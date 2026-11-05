"""Builds and animates the pool episode in Blender, synced to the narration, and renders JPEG frames.

    blender -b --python escena.py -- <carpeta_episodio> <segundos_hasta>

The ground is a block of soil layers. A second cutter slices it along the pool's centre line in the section
shots, so the viewer sees the hole from the side; in the wide shots the block is whole."""
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix

EP = Path(sys.argv[sys.argv.index("--") + 1])
UNTIL = float(sys.argv[sys.argv.index("--") + 2])
FPS = 30
TL = json.loads((EP / "timeline.json").read_text(encoding="utf-8"))
LINES = [l for s in TL["scenes"] for l in s["lines"]]
SCENE = {s["id"]: s for s in TL["scenes"]}


def F(seconds):
    return 1 + round(seconds * FPS)


def line(prefix):
    return next(l for l in LINES if l["text"].startswith(prefix))


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
random.seed(4)


# ------------------------------------------------------------------ helpers
def material(name, rgb, rough=.9, alpha=1.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    rgb = tuple(c ** 2.2 for c in rgb)  # colours are written as screen (sRGB) values; Blender wants linear
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except AttributeError:
            m.blend_method = "BLEND"
    if emit:
        p.inputs["Emission Color"].default_value = (*rgb, 1)
        p.inputs["Emission Strength"].default_value = emit
    return m


def mesh_object(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()  # consistent outward normals, which the boolean cuts need
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return mesh_object(name, v, f, mat)


def prim(kind, name, loc, scale, mat, **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(location=loc, **kw)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(mat)
    return ob


def key(ob, path, frame, value, index=-1, interp=None):
    target = ob
    attr = path
    if "." in path:
        *chain, attr = path.split(".")
        for part in chain:
            target = getattr(target, part)
    if index >= 0:
        getattr(target, attr)[index] = value
    else:
        setattr(target, attr, value)
    target.keyframe_insert(attr, index=index, frame=frame)
    if interp:
        action = (ob.animation_data or ob.data.shape_keys.animation_data).action
        for fc in _fcurves(action):
            for kp in fc.keyframe_points:
                if int(kp.co[0]) == frame:
                    kp.interpolation = interp


def _fcurves(action):
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    out = []  # Blender 5 layered actions
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += list(bag.fcurves)
    return out


def pop(ob, frame, dur=8, final=None):
    """Scales an object up from nothing with a small overshoot."""
    final = final or tuple(ob.scale)
    key(ob, "scale", frame - 1, (0, 0, 0))
    key(ob, "scale", frame + dur, tuple(s * 1.12 for s in final))
    key(ob, "scale", frame + dur + 4, final)


def hide_until(ob, frame):
    key(ob, "scale", 1, (0, 0, 0), interp="CONSTANT")
    key(ob, "scale", frame, tuple(ob.scale) if any(ob.scale) else (1, 1, 1))


# ------------------------------------------------------------------ materials
GRASS = material("pasto", (.30, .62, .18))
TOP = material("tierra", (.47, .28, .13))
SUB = material("subsuelo", (.38, .21, .10))
SAND = material("arena", (.80, .64, .38))
ROCK = material("piedra", (.42, .37, .33))
GRAVEL = material("grava", (.62, .60, .55))
CONCRETE = material("concreto", (.66, .66, .64))
WATER = material("agua", (.25, .62, .95), rough=.05, alpha=.62)
WOOD = material("madera", (.55, .36, .18))
ROPE = material("cuerda", (1.0, .55, .05), emit=.3)
LEAF = material("hoja", (.22, .52, .20))
LEAF2 = material("hoja2", (.35, .62, .22))
TRUNK = material("tronco", (.40, .26, .14))
CLOUD = material("nube", (1, 1, 1), emit=.4)
WALL = material("casa", (.93, .88, .76))
ROOF = material("techo", (.70, .30, .20))
ORANGE = material("maquina", (.95, .52, .08))
CRACK = material("grieta", (.08, .07, .07))

# ------------------------------------------------------------------ world, light, render
world = bpy.data.worlds.new("cielo")
sc.world = world
world.use_nodes = True
# bright sky for the camera, softer light on the scene
nodes, links = world.node_tree.nodes, world.node_tree.links
sky = tuple(c ** 2.2 for c in (.45, .74, 1.0)) + (1,)
nodes["Background"].inputs["Color"].default_value = sky
ambient = nodes.new("ShaderNodeBackground")
ambient.inputs["Color"].default_value = sky
ambient.inputs["Strength"].default_value = .45
ray = nodes.new("ShaderNodeLightPath")
mix = nodes.new("ShaderNodeMixShader")
links.new(ray.outputs["Is Camera Ray"], mix.inputs[0])
links.new(ambient.outputs[0], mix.inputs[1])
links.new(nodes["Background"].outputs[0], mix.inputs[2])
links.new(mix.outputs[0], nodes["World Output"].inputs["Surface"])
sun = bpy.data.objects.new("sol", bpy.data.lights.new("sol", "SUN"))
sun.data.energy = 3.6
sun.data.angle = math.radians(6)
sun.rotation_euler = (math.radians(52), 0, math.radians(32))
sc.collection.objects.link(sun)

for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = engine
        break
    except TypeError:
        pass
sc.eevee.taa_render_samples = 24
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = FPS
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "JPEG"
sc.render.image_settings.quality = 92
sc.render.filepath = str(EP / "frames" / "f_")
sc.frame_start, sc.frame_end = 1, F(UNTIL)

# ------------------------------------------------------------------ soil block and cutters
POOL_X, POOL_Y, DEPTH, SLOPE = 4.0, 2.0, 2.2, .9
BLOCK = (-14, 14, -6, 24)

pool_cut = box("corte_alberca", -POOL_X, POOL_X, -POOL_Y, POOL_Y, -DEPTH, .6, None)
pool_cut.hide_render = True
pool_cut.display_type = "WIRE"
pool_cut.shape_key_add(name="recto")
talud = pool_cut.shape_key_add(name="talud")
grow = SLOPE * (DEPTH + .6) / DEPTH
for v in talud.data:
    if v.co.z > 0:
        v.co.x *= (POOL_X + grow) / POOL_X
        v.co.y *= (POOL_Y + grow) / POOL_Y

section = box("corte_seccion", -40, 40, -60, 0, -20, 20, None)
section.hide_render = True
section.display_type = "WIRE"


def cut(ob, pool=True):
    for cutter in ([pool_cut] if pool else []) + [section]:
        mod = ob.modifiers.new("corte", "BOOLEAN")
        mod.object = cutter
        mod.operation = "DIFFERENCE"


BEDROCK = material("roca", (.50, .44, .38))
layers = [("pasto", 0, -.25, GRASS), ("tierra", -.25, -1.2, TOP), ("subsuelo", -1.2, -2.7, SUB), ("arena", -2.7, -4.2, SAND),
          ("roca", -4.2, -9.0, BEDROCK)]  # deep enough that close section shots never show the sky below the block
for name, z1, z0, mat in layers:
    cut(box(f"capa_{name}", *BLOCK, z0, z1, mat))
for i in range(70):  # stones showing in the cut face
    x = random.uniform(-13.5, 13.5)
    z = random.uniform(-8.5, -.5)
    if abs(x) < POOL_X + grow + .6 and z > -DEPTH - .5:
        continue
    s = random.uniform(.08, .2)
    stone = prim("ico_sphere", f"piedra{i}", (x, random.uniform(-.05, .05), z), (s, s * .7, s * .8), ROCK, subdivisions=1)
    cut(stone, pool=False)

# ------------------------------------------------------------------ yard: house, trees, clouds, fence
box("casa", -6, 6, 13, 20, 0, 4.5, WALL)
roof = mesh_object("techo", [(-6.6, 12.4, 4.5), (6.6, 12.4, 4.5), (6.6, 20.6, 4.5), (-6.6, 20.6, 4.5), (-6.6, 16.5, 7), (6.6, 16.5, 7)],
                   [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)], ROOF)
box("puerta", -.8, .8, 12.95, 13.0, 0, 2.2, WOOD)
for x in (-4, 3):
    box(f"ventana{x}", x, x + 1.6, 12.95, 13.0, 1.8, 3.2, WATER)
for i in range(45):
    while True:
        x, y = random.uniform(-13, 13), random.uniform(-5, 23)
        if not (abs(x) < 9 and -4 < y < 21):
            break
    h = random.uniform(2.2, 4)
    prim("cylinder", f"tronco{i}", (x, y, h * .2), (.18, .18, h * .2), TRUNK, vertices=6)
    prim("cone", f"copa{i}", (x, y, h * .4 + h * .35), (h * .32, h * .32, h * .45), random.choice((LEAF, LEAF2)), vertices=7)
for i in range(7):
    cx, cy, cz = random.uniform(-25, 25), random.uniform(25, 60), random.uniform(14, 22)
    for j in range(4):
        r = random.uniform(1.4, 2.6)
        prim("ico_sphere", f"nube{i}_{j}", (cx + j * 1.6, cy + random.uniform(-.6, .6), cz + random.uniform(-.4, .5)), (r, r * .8, r * .7), CLOUD, subdivisions=1)

# ------------------------------------------------------------------ construction pieces
b2 = SCENE["b2"]
corners = [(-POOL_X, -POOL_Y), (POOL_X, -POOL_Y), (POOL_X, POOL_Y), (-POOL_X, POOL_Y)]
stakes = []
for i, (x, y) in enumerate(corners):
    st = prim("cylinder", f"estaca{i}", (x, y, .45), (.07, .07, .45), WOOD, vertices=6)
    pop(st, F(b2["start"] + .3 + i * .35))
    stakes.append(st)
rope_start = F(b2["start"] + 2.0)
for i in range(4):
    (x0, y0), (x1, y1) = corners[i], corners[(i + 1) % 4]
    length = math.hypot(x1 - x0, y1 - y0)
    r = prim("cube", f"cuerda{i}", ((x0 + x1) / 2, (y0 + y1) / 2, .55), (length / 2, .025, .025), ROPE)
    r.rotation_euler.z = math.atan2(y1 - y0, x1 - x0)
    pop(r, rope_start + i * 10, dur=10)
    stakes.append(r)

# excavation: the cutter goes down while the dirt pile grows
dig = line("Luego excavas")
walls = line("Pero si cavas")
dig_end = F(walls["start"] + (walls["end"] - walls["start"]) * .45)
key(pool_cut, "location", 1, 3.0, index=2)
key(pool_cut, "location", F(dig["start"]), 3.0, index=2)
key(pool_cut, "location", dig_end, 0.0, index=2)
for ob in stakes:  # stakes and rope leave when digging starts
    key(ob, "scale", F(dig["start"]) + 6, tuple(ob.scale))
    key(ob, "scale", F(dig["start"]) + 14, (0, 0, 0))
pile = prim("cone", "monton", (9.5, 6, 0), (2.4, 2.4, 1.3), TOP, vertices=9)
key(pile, "scale", F(dig["start"]) - 1, (0, 0, 0))
key(pile, "scale", dig_end, (2.4, 2.4, 1.3))

# straight walls collapse
fall = walls["start"] + (walls["end"] - walls["start"]) * .74
chunks = []
for i in range(9):
    x = random.uniform(-3.4, 3.4)
    s = random.uniform(.22, .4)
    ch = prim("ico_sphere", f"terron{i}", (x, POOL_Y - .25, -.35), (s, s, s * .8), TOP if i % 2 else SUB, subdivisions=1)
    t0 = F(fall + i * .06)
    key(ch, "scale", 1, (0, 0, 0), interp="CONSTANT")
    key(ch, "scale", t0, (s, s, s * .8))
    key(ch, "location", t0, (x, POOL_Y - .25, -.35))
    key(ch, "location", t0 + 14, (x + random.uniform(-.3, .3), POOL_Y - 1.1, -DEPTH + s * .6))
    key(ch, "rotation_euler", t0, (0, 0, 0))
    key(ch, "rotation_euler", t0 + 14, (random.uniform(1, 3), random.uniform(1, 3), 0))
    chunks.append(ch)

# talud: walls lean back, the fallen soil is cleared
b4 = SCENE["b4"]
kb = pool_cut.data.shape_keys.key_blocks["talud"]
kb.value = 0
kb.keyframe_insert("value", frame=F(b4["start"] + .4))
kb.value = 1
kb.keyframe_insert("value", frame=F(b4["start"] + 2.6))
for ch in chunks:
    key(ch, "scale", F(b4["start"] + .3), tuple(ch.scale))
    key(ch, "scale", F(b4["start"] + .9), (0, 0, 0))

# gravel base, falling stones and the compactor
b5 = SCENE["b5"]
span5 = b5["end"] - b5["start"]
grav = box("grava", -POOL_X, POOL_X, -POOL_Y, POOL_Y, -DEPTH, -DEPTH + .28, GRAVEL)
cut(grav, pool=False)
key(grav, "scale", 1, (0, 0, 0), interp="CONSTANT")
grav.data.transform(Matrix.Translation((0, 0, DEPTH)))
grav.location.z = -DEPTH
key(grav, "scale", F(b5["start"]), (1, 1, .02))
key(grav, "scale", F(b5["start"] + span5 * .4), (1, 1, 1))
for i in range(36):
    x, y = random.uniform(-3.8, 3.8), random.uniform(.1, 1.9)
    s = random.uniform(.06, .12)
    pb = prim("ico_sphere", f"guijarro{i}", (x, y, 2.5), (s, s, s), GRAVEL, subdivisions=1)
    t0 = F(b5["start"] + random.uniform(0, span5 * .35))
    key(pb, "scale", 1, (0, 0, 0), interp="CONSTANT")
    key(pb, "scale", t0, (s, s, s))
    key(pb, "location", t0, (x, y, 1.5))
    key(pb, "location", t0 + 12, (x, y, -DEPTH + .3))
comp = prim("cube", "compactadora", (-3.3, .9, -DEPTH + .5), (.35, .3, .2), ORANGE)
handle = prim("cylinder", "manija", (0, 0, 0), (.04, .04, .5), CRACK, vertices=6)
handle.parent = comp
handle.location = (-1.3, 0, 2.2)
handle.rotation_euler.y = math.radians(-40)
c0, c1 = F(b5["start"] + span5 * .4), F(b5["end"])
key(comp, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(comp, "scale", c0, (.35, .3, .2))
for f in range(c0, c1, 3):
    k = (f - c0) / max(1, c1 - c0)
    key(comp, "location", f, (-3.3 + 6.6 * k, .9, -DEPTH + .5 + (.08 if (f // 3) % 2 else 0)))
key(comp, "scale", c1, (.35, .3, .2))
key(comp, "scale", c1 + 6, (0, 0, 0))

# plain concrete shell cracks under the water's weight
b6 = SCENE["b6"]
span6 = b6["end"] - b6["start"]
inner = (POOL_X - .25, POOL_Y - .25)
top_x, top_y = POOL_X + SLOPE - .2, POOL_Y + SLOPE - .2
zb = -DEPTH + .28
shell = mesh_object("cascaron", [(-inner[0], -inner[1], zb), (inner[0], -inner[1], zb), (inner[0], inner[1], zb), (-inner[0], inner[1], zb),
                                  (-top_x, -top_y, 0), (top_x, -top_y, 0), (top_x, top_y, 0), (-top_x, top_y, 0)],
                    [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], CONCRETE)
solid = shell.modifiers.new("grosor", "SOLIDIFY")
solid.thickness = .22
cut(shell, pool=False)
hide_until(shell, F(b6["start"] + .2))
water = box("agua_prueba", -inner[0], inner[0], -inner[1], inner[1], zb, zb + 1.6, WATER)
cut(water, pool=False)
water.data.transform(Matrix.Translation((0, 0, -zb)))
water.location.z = zb
key(water, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(water, "scale", F(b6["start"] + span6 * .2), (1, 1, .01))
key(water, "scale", F(b6["start"] + span6 * .55), (1, 1, 1))
key(water, "scale", F(b6["start"] + span6 * .78), (1, 1, 1))
key(water, "scale", F(b6["end"]), (1, 1, .01))
for i, (x, z, rot, ln) in enumerate([(-1.5, -1.3, 60, .9), (-1.1, -.8, -35, .7), (1.2, -1.5, 75, 1.0), (1.6, -.9, -50, .6), (.2, -1.8, 10, .8)]):
    y = POOL_Y - .24 + (z - zb) / (0 - zb) * (top_y - inner[1]) - .02
    cr = prim("cube", f"grieta{i}", (x, y, z), (ln * .7, .04, .06), CRACK)
    cr.rotation_euler = (math.radians(-35), math.radians(rot), 0)
    key(cr, "scale", 1, (0, 0, 0), interp="CONSTANT")
    key(cr, "scale", F(b6["start"] + span6 * (.55 + i * .04)), (0, .04, .06))
    key(cr, "scale", F(b6["start"] + span6 * (.62 + i * .04)), (ln * .7, .04, .06))

# ------------------------------------------------------------------ camera
target = bpy.data.objects.new("mira", None)
sc.collection.objects.link(target)
cam = bpy.data.objects.new("camara", bpy.data.cameras.new("camara"))
cam.data.lens = 24
cam.data.clip_start = .05
sc.collection.objects.link(cam)
sc.camera = cam
track = cam.constraints.new("TRACK_TO")
track.target = target
SECTION_ON, SECTION_OFF = 0.0, -8.0


def shot(t0, t1, cam_a, cam_b, aim_a, aim_b, sliced):
    f0, f1 = F(t0), F(t1) - 1
    for ob, a, b in ((cam, cam_a, cam_b), (target, aim_a, aim_b)):
        key(ob, "location", f0, a, interp="LINEAR")
        key(ob, "location", f1, b, interp="LINEAR")
    y = SECTION_ON if sliced else SECTION_OFF
    key(section, "location", f0, (0, y, 0), interp="CONSTANT")


b1, b3 = SCENE["b1"], SCENE["b3"]
mid3 = walls["start"] + (walls["end"] - walls["start"]) * .5
shot(0, b2["start"], (24, -30, 19), (12, -33, 14), (0, 6, -1), (0, 4, -1), False)
shot(b2["start"], b3["start"], (3, -14, 12), (1, -12, 9.5), (0, 0, 0), (0, .5, 0), False)
shot(b3["start"], mid3, (13, -16, 9), (11, -14, 7.5), (0, 0, -1), (0, .5, -1.2), False)
shot(mid3, b4["start"], (0, -9.5, .6), (0, -8.6, .2), (0, 1, -1.2), (0, 1, -1.3), True)
shot(b4["start"], b5["start"], (0, -9.5, .3), (1.5, -9.2, .5), (0, 1, -1.1), (.3, 1, -1.1), True)
shot(b5["start"], b6["start"], (-1, -6.8, -.6), (1.2, -6.4, -.8), (0, 1, -1.9), (.5, 1, -1.9), True)
shot(b6["start"], max(b6["end"], UNTIL) + 1, (0, -9.4, .4), (0, -8.8, .2), (0, 1.5, -1.2), (0, 1.5, -1.3), True)

beats = dict(estacas=[b2["start"] + .3 + i * .35 for i in range(4)], excavar=[dig["start"], (dig_end - 1) / FPS], derrumbe=fall,
             talud=b4["start"] + .4, grava=b5["start"], compactar=[(c0 - 1) / FPS, (c1 - 1) / FPS],
             agua=[b6["start"] + span6 * .2, b6["start"] + span6 * .55], grietas=b6["start"] + span6 * .55, fuga=b6["start"] + span6 * .78)
(EP / "beats.json").write_text(json.dumps(beats, indent=1), encoding="utf-8")
(EP / "frames").mkdir(exist_ok=True)
if "--cuadros" in sys.argv:  # review: render only these seconds
    for t in sys.argv[sys.argv.index("--cuadros") + 1].split(","):
        sc.frame_set(F(float(t)))
        sc.render.filepath = str(EP / "frames" / f"revision_{float(t):05.1f}.jpg")
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
