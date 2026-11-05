"""motor3d: shared Blender engine for 3dpartes. An episode script does `from motor3d import *` and only describes
its own layers, machines, actions and camera moves. Run the episode, not this file:

    blender -b --python escena_<tema>.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar]

What it gives: timeline helpers (F, L, SC, beat), mesh and animation helpers (box, prim, key, show, pop, cut ...),
a flat low-poly palette, sky and light, sweep_path (layers along a path with shape keys), the section cutter,
the landscape (soil block, plain, trees, houses, fields, hills, mountains, clouds), machines and vehicles,
rain, falling gravel, steam, spray, the camera (shot, follow) and terminar() (beats.json + render).
Blender 5 note: an object and its data share one action, so key() only changes the interpolation of the curve it keys."""
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

EP = Path(sys.argv[sys.argv.index("--") + 1])
UNTIL = float(sys.argv[sys.argv.index("--") + 2])
FPS = 30
TL = json.loads((EP / "timeline.json").read_text(encoding="utf-8"))
SC = {s["id"]: s for s in TL["scenes"]}


def F(seconds):
    return 1 + round(seconds * FPS)


def L(sid, i=0):
    return SC[sid]["lines"][i]


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
random.seed(11)
BEATS = {}


def beat(name, value):
    BEATS[name] = value


# ------------------------------------------------------------------ helpers
def material(name, rgb, rough=.9, alpha=1.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    rgb = tuple(c ** 2.2 for c in rgb)
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


def link(ob):
    sc.collection.objects.link(ob)
    return ob


def mesh_object(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = link(bpy.data.objects.new(name, me))
    if mat:
        ob.data.materials.append(mat)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat, origin=None):
    """Axis-aligned box. With origin, the mesh is built around that point so scaling grows from it."""
    ox, oy, oz = origin or (0, 0, 0)
    v = [(x - ox, y - oy, z - oz) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    ob = mesh_object(name, v, f, mat)
    ob.location = (ox, oy, oz)
    return ob


def prim(kind, name, loc, scale, mat, parent=None, rot=(0, 0, 0), **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(location=(0, 0, 0), **kw)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    ob.rotation_euler = rot
    if parent:
        ob.parent = parent
    ob.location = loc
    if mat:
        ob.data.materials.append(mat)
    return ob


def empty(name, loc=(0, 0, 0)):
    ob = link(bpy.data.objects.new(name, None))
    ob.location = loc
    return ob


def _fcurves(action):
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    out = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out += list(bag.fcurves)
    return out


fcurves = _fcurves  # public name, since `import *` skips names that start with _


def key(ob, path, frame, value, index=-1, interp=None):
    target, attr = ob, path
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
        holder = target.id_data if hasattr(target, "id_data") else ob
        ad = holder.animation_data
        for fc in _fcurves(ad.action):
            if fc.data_path.split(".")[-1] != attr:  # object and data can share one action in Blender 5
                continue
            for kp in fc.keyframe_points:
                if int(round(kp.co[0])) == frame:
                    kp.interpolation = interp


def show(ob, t_on=None, t_off=None):
    """Hidden outside [t_on, t_off). Uses render visibility, so booleans and shape keys are untouched.
    Applies to every child too, because a hidden parent does not hide its children."""
    for child in ob.children_recursive:
        if not child.display_type == "WIRE":
            _show(child, t_on, t_off)
    _show(ob, t_on, t_off)


def _show(ob, t_on, t_off):
    if ob.animation_data and ob.animation_data.action:  # a second call adds a new window instead of replacing
        fcs = [fc for fc in _fcurves(ob.animation_data.action) if fc.data_path == "hide_render"]
        if fcs:
            if t_on is not None:
                ob.hide_render = False
                ob.keyframe_insert("hide_render", frame=F(t_on))
            if t_off is not None:
                ob.hide_render = True
                ob.keyframe_insert("hide_render", frame=F(t_off))
            for fc in fcs:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
            return
    ob.hide_render = t_on is not None
    ob.keyframe_insert("hide_render", frame=1)
    if t_on is not None:
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=F(t_on))
    if t_off is not None:
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=F(t_off))
    for fc in _fcurves(ob.animation_data.action):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def pop(ob, t, dur=.25, final=None):
    final = final or tuple(ob.scale)
    f = F(t)
    key(ob, "scale", 1, (0, 0, 0), interp="CONSTANT")
    key(ob, "scale", f - 1, (0, 0, 0), interp="CONSTANT")
    key(ob, "scale", f + round(dur * FPS), tuple(s * 1.15 for s in final))
    key(ob, "scale", f + round(dur * FPS) + 4, final)


def unpop(ob, t, dur=.2):
    key(ob, "scale", F(t), tuple(ob.scale))
    key(ob, "scale", F(t + dur), (0, 0, 0))


def cut(ob, cutter, apply=False):
    mod = ob.modifiers.new(f"corte_{cutter.name}", "BOOLEAN")
    mod.object = cutter
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    if apply:
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier=mod.name)


def cutter(ob):
    ob.hide_render = True
    ob.display_type = "WIRE"
    return ob


def ease(k):
    k = min(1, max(0, k))
    return k * k * (3 - 2 * k)


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ materials
GRASS = material("pasto", (.36, .64, .20))
GRASS2 = material("pasto2", (.46, .70, .24))
FIELD = material("cultivo", (.80, .70, .30))
FIELD2 = material("cultivo2", (.30, .52, .16))
TOP = material("tierra", (.47, .29, .14))
SUB = material("subsuelo", (.60, .40, .22))
ROCKL = material("roca", (.42, .34, .30))
DIRT = material("camino", (.50, .34, .18), rough=.5)
MUD = material("lodo", (.30, .20, .11), rough=.15)
SUBGRADE = material("subrasante", (.86, .66, .40))
SUBBASE = material("subbase", (.44, .43, .42))
BASE = material("base", (.80, .78, .72))
PRIME = material("riego", (.24, .15, .08), rough=.2)
ASPHALT = material("asfalto", (.17, .17, .19), rough=.6)
WHITE = material("blanco", (.97, .97, .95), emit=.15)
YELLOWL = material("amarillo", (1.0, .80, .10), emit=.2)
WATER = material("agua", (.25, .58, .90), rough=.05, alpha=.75)
RAIN = material("lluvia", (.80, .90, 1.0), alpha=.45, emit=.6)
PUDDLE = material("charco", (.36, .62, .90), rough=.02, alpha=.8)
WOOD = material("madera", (.55, .36, .18))
ORANGE = material("naranja", (1.0, .45, .05), emit=.3)
MACHINE = material("maquina", (.98, .74, .08))
DARK = material("oscuro", (.10, .10, .11))
STEEL = material("acero", (.72, .74, .78), rough=.3)
CONCRETE = material("concreto", (.70, .70, .68))
LEAF = material("hoja", (.20, .50, .20))
LEAF2 = material("hoja2", (.32, .60, .22))
LEAF3 = material("hoja3", (.42, .62, .18))
TRUNK = material("tronco", (.40, .26, .14))
CLOUD = material("nube", (1, 1, 1), emit=.5)
HILL = material("colina", (.40, .62, .26))
HILL2 = material("colina2", (.34, .56, .24))
MOUNT = material("montana", (.52, .62, .74))
SNOW = material("nieve", (.95, .97, 1.0), emit=.2)
WALLS = [material(f"muro{i}", c) for i, c in enumerate([(.95, .90, .78), (.95, .80, .62), (.88, .92, .95), (.98, .85, .85)])]
ROOF = material("techo", (.72, .30, .20))
RED = material("coche_rojo", (.88, .14, .12), rough=.35)
BLUE = material("coche_azul", (.15, .40, .88), rough=.35)
GLASS = material("vidrio", (.55, .75, .90), rough=.1)
STEAM = material("vapor", (.95, .95, .95), alpha=.5, emit=.3)
DUST = material("polvo", (.70, .58, .42), alpha=.6)
CRACKM = material("grieta", (.05, .05, .05))


def variar(mat, escala=.35, fuerza=.18):
    """Breaks up a flat colour with soft noise (lighter and darker patches), so soil and grass don't look like plastic."""
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = tuple(bsdf.inputs["Base Color"].default_value)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = escala
    noise.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = tuple(c * (1 - fuerza) for c in base[:3]) + (1,)
    ramp.color_ramp.elements[1].color = tuple(min(1, c * (1 + fuerza)) for c in base[:3]) + (1,)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])


for _m, _e in ((GRASS, .25), (GRASS2, .08), (TOP, .9), (SUB, .6), (ROCKL, .5)):
    variar(_m, _e)


def biselar(ob, ancho=.05):
    """Rounds the edges a little so boxes catch the light instead of looking like flat cards."""
    mod = ob.modifiers.new("bisel", "BEVEL")
    mod.width = ancho
    mod.segments = 2
    mod.limit_method = "ANGLE"
    return ob

# ------------------------------------------------------------------ world, light, render
world = bpy.data.worlds.new("cielo")
sc.world = world
world.use_nodes = True
nodes, links = world.node_tree.nodes, world.node_tree.links
sky = tuple(c ** 2.2 for c in (.50, .76, 1.0)) + (1,)
nodes["Background"].inputs["Color"].default_value = sky
ambient = nodes.new("ShaderNodeBackground")
ambient.inputs["Color"].default_value = sky
ambient.inputs["Strength"].default_value = .5
ray = nodes.new("ShaderNodeLightPath")
mixs = nodes.new("ShaderNodeMixShader")
links.new(ray.outputs["Is Camera Ray"], mixs.inputs[0])
links.new(ambient.outputs[0], mixs.inputs[1])
links.new(nodes["Background"].outputs[0], mixs.inputs[2])
links.new(mixs.outputs[0], nodes["World Output"].inputs["Surface"])
sun = link(bpy.data.objects.new("sol", bpy.data.lights.new("sol", "SUN")))
sun.data.energy = 3.4
sun.data.angle = math.radians(5)
sun.rotation_euler = (math.radians(50), 0, math.radians(-35))

sc.render.engine = "BLENDER_EEVEE"
RAPIDO = "--rapido" in sys.argv   # quick review stills: low samples, no ray tracing
sc.eevee.taa_render_samples = 12 if RAPIDO else 48
for attr, value in (("use_raytracing", not RAPIDO), ("use_shadows", True), ("shadow_ray_count", 2), ("shadow_step_count", 8)):
    try:
        setattr(sc.eevee, attr, value)
    except (AttributeError, TypeError):
        pass
try:
    sc.eevee.ray_tracing_options.resolution_scale = "2"
except (AttributeError, TypeError):
    pass
sc.render.use_motion_blur = not RAPIDO
sc.render.motion_blur_shutter = .4
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = FPS
sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "JPEG"
sc.render.image_settings.quality = 92
sc.render.filepath = str(EP / "frames" / "f_")
sc.frame_start, sc.frame_end = 1, F(UNTIL)


# ------------------------------------------------------------------ sweeps along a path
def sweep_path(name, profile, ss, point, mat, deforms=None, static=None, zorigin=0.0):
    """Extrudes a closed cross-section along a path and caps both ends.
    profile = [(offset, z, flags)]; ss = arc lengths to sample; point(s, offset, z) -> world (x, y, z).
    deforms = {shape_key_name: fn(offset, s, flags) -> dz} adds shape keys; static = {same} bakes them in.
    Local z is measured from zorigin, so scaling z grows the layer upward from its bottom."""
    k = len(profile)
    verts, faces = [], []
    for s in ss:
        for o, z, fl in profile:
            if static:
                z += sum(fn(o, s, fl) for fn in static.values())
            x, y, _ = point(s, o, z)
            verts.append((x, y, z - zorigin))
    for i in range(len(ss) - 1):
        for j in range(k):
            a, b = i * k + j, i * k + (j + 1) % k
            faces.append((a, b, b + k, a + k))
    faces.append(tuple(range(k)))
    faces.append(tuple(range((len(ss) - 1) * k, len(ss) * k)))
    ob = mesh_object(name, verts, faces, mat)
    ob.location.z = zorigin
    if deforms:
        ob.shape_key_add(name="Basis")
        for kname, fn in deforms.items():
            kb = ob.shape_key_add(name=kname, from_mix=False)
            for i, s in enumerate(ss):
                for j, (o, z, fl) in enumerate(profile):
                    kb.data[i * k + j].co.z += fn(o, s, fl)
    return ob


def shape_key(ob, name, frame, value):
    kb = ob.data.shape_keys.key_blocks[name]
    kb.value = value
    kb.keyframe_insert("value", frame=frame)


# ------------------------------------------------------------------ section cutter: removes y < y0 in cutaway shots
SECTION = None
SECTION_OFF = -5000.0


def seccion(y0=0.0):
    """Creates the cutter that slices the scene at y = y0. Pass it to cut() on every object that should be sliced."""
    global SECTION
    SECTION = cutter(box("corte_seccion", -1000, 1000, -2000 + y0, y0, -200, 200, None))
    return SECTION


# ------------------------------------------------------------------ soil block inside a wide landscape
def suelo(capas, cortes_por_capa=None, block=(-400, 400, -400, 600)):
    """Soil layers as boxes [(name, z_top, z_bottom, material)] over a block, plus the plain around it (never inside it,
    or it would show through every hole). cortes_por_capa = {name: [(cutter, apply)]}. Returns the layer objects."""
    x0, x1, y0, y1 = block
    out = []
    for name, z1, z0, mat in capas:
        ob = box(f"capa_{name}", x0, x1, y0, y1, z0, z1, mat)
        for c, apply in (cortes_por_capa or {}).get(name, []):
            cut(ob, c, apply=apply)
        if SECTION:
            cut(ob, SECTION)
        out.append(ob)
    for i, (a, b, c, d) in enumerate([(-5000, 5000, y1, 5000), (-5000, 5000, -5000, y0), (-5000, x0, y0, y1), (x1, 5000, y0, y1)]):
        pl = box(f"llanura{i}", a, b, c, d, -1.0, -.03, GRASS2)
        if SECTION:
            cut(pl, SECTION)
    for i in range(40):  # stones in the cut face
        x, z = random.uniform(-12, 12), random.uniform(-8, -1.1)
        s = random.uniform(.1, .25)
        st = prim("ico_sphere", f"piedra{i}", (x, random.uniform(-.1, .1), z), (s, s * .7, s * .8), ROCKL, subdivisions=1)
        if SECTION:
            cut(st, SECTION)
    return out


def tree(i, x, y, h=None):
    h = h or random.uniform(3, 6)
    prim("cylinder", f"tronco{i}", (x, y, h * .2), (.22, .22, h * .2), TRUNK, vertices=6)
    if random.random() < .5:
        prim("cone", f"copa{i}", (x, y, h * .4 + h * .35), (h * .34, h * .34, h * .5), random.choice((LEAF, LEAF2)), vertices=7)
    else:
        r = h * .32
        prim("ico_sphere", f"copa{i}", (x, y, h * .55 + r * .6), (r, r, r * .9), random.choice((LEAF2, LEAF3)), subdivisions=1)


def casa(i, x, y, w=None, d=None, h=None):
    w, d, h = w or random.uniform(5, 8), d or random.uniform(5, 7), h or random.uniform(3.5, 6)
    box(f"casa{i}", x - w / 2, x + w / 2, y - d / 2, y + d / 2, 0, h, random.choice(WALLS))
    mesh_object(f"techo{i}", [(x - w / 2 - .4, y - d / 2 - .4, h), (x + w / 2 + .4, y - d / 2 - .4, h), (x + w / 2 + .4, y + d / 2 + .4, h),
                              (x - w / 2 - .4, y + d / 2 + .4, h), (x - w / 2 - .4, y, h + 2.4), (x + w / 2 + .4, y, h + 2.4)],
                [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)], ROOF)


def campo(i, x0, x1, y0, y1, mat):
    box(f"cultivo{i}", x0, x1, y0, y1, -.05, .06, mat)
    for k in range(int((x1 - x0) / 3)):  # furrows
        box(f"surco{i}_{k}", x0 + k * 3 + .3, x0 + k * 3 + 1.2, y0 + .5, y1 - .5, .06, .16, mat)


def paisaje(libre, arboles=320, zona=(-160, 260, -120, 320), centro=(60, 120), casas=(), campos=()):
    """Context around the work site so it never floats in the void: trees where libre(x, y) is True,
    houses [(x, y)], fields [(x0, x1, y0, y1)], rolling hills, mountains on the horizon and clouds."""
    n = 0
    while n < arboles:
        x, y = random.uniform(zona[0], zona[1]), random.uniform(zona[2], zona[3])
        if libre(x, y):
            tree(n, x, y)
            n += 1
    for i, (x, y) in enumerate(casas):
        casa(i, x, y)
    for i, rect in enumerate(campos):
        campo(i, *rect, FIELD if i % 2 == 0 else FIELD2)
    cx, cy = centro
    for i in range(30):
        a, d = random.uniform(0, 2 * math.pi), random.uniform(330, 650)
        r = random.uniform(70, 150)
        prim("ico_sphere", f"colina{i}", (cx + d * math.cos(a), cy + d * math.sin(a), -r * .55), (r, r, r * .7), random.choice((HILL, HILL2)), subdivisions=2)
    for i in range(16):
        a, d, h = math.radians(random.uniform(20, 160)), random.uniform(1300, 1700), random.uniform(220, 420)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        prim("cone", f"monte{i}", (x, y, h / 2 - 20), (h * .9, h * .9, h / 2), MOUNT, vertices=6, rot=(0, 0, random.uniform(0, 3)))
        prim("cone", f"nieve{i}", (x, y, h * .86 - 20), (h * .26, h * .26, h * .14 + .5), SNOW, vertices=6)
    for i in range(10):
        x, y, z = random.uniform(-200, 300), random.uniform(80, 500), random.uniform(55, 90)
        for j in range(4):
            r = random.uniform(6, 11)
            prim("ico_sphere", f"nube{i}_{j}", (x + j * 7, y + random.uniform(-3, 3), z + random.uniform(-2, 2)), (r, r * .8, r * .6), CLOUD, subdivisions=1)


def agua_animada(mat, velocidad=90):
    """Gives a water material a flowing noise pattern (moves along -x over the whole video)."""
    nt = mat.node_tree
    noise, mapn, coord, ramp = (nt.nodes.new(t) for t in ("ShaderNodeTexNoise", "ShaderNodeMapping", "ShaderNodeTexCoord", "ShaderNodeValToRGB"))
    noise.inputs["Scale"].default_value = 1.6
    ramp.color_ramp.elements[0].color = tuple(c ** 2.2 for c in (.20, .50, .85)) + (1,)
    ramp.color_ramp.elements[1].color = tuple(c ** 2.2 for c in (.62, .84, 1.0)) + (1,)
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = .45, .7
    nt.links.new(coord.outputs["Object"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    loc = mapn.inputs["Location"]
    loc.default_value[0] = 0
    loc.keyframe_insert("default_value", index=0, frame=1)
    loc.default_value[0] = -velocidad
    loc.keyframe_insert("default_value", index=0, frame=F(80))
    for fc in _fcurves(nt.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


# ------------------------------------------------------------------ machines and vehicles
def wheels(parent, xs, ys, r=.45, w=.3):
    for x in xs:
        for y in ys:
            prim("cylinder", f"{parent.name}_rueda{x}{y}", (x, y, r), (r, r, w / 2), DARK, parent=parent, rot=(0, math.radians(90), 0), vertices=10)


def dozer(name):
    p = empty(name)
    prim("cube", f"{name}_cuerpo", (0, 0, 1.2), (1.3, 1.9, .7), MACHINE, parent=p)
    prim("cube", f"{name}_cabina", (0, -.6, 2.4), (1.0, .9, .6), GLASS, parent=p)
    prim("cube", f"{name}_techo", (0, -.6, 3.05), (1.1, 1.0, .06), MACHINE, parent=p)
    for x in (-1.45, 1.45):
        prim("cube", f"{name}_oruga{x}", (x, 0, .45), (.35, 2.1, .45), DARK, parent=p)
    prim("cube", f"{name}_cuchilla", (0, 2.6, .7), (2.1, .15, .7), MACHINE, parent=p, rot=(math.radians(-12), 0, 0))
    prim("cylinder", f"{name}_escape", (.7, .6, 2.4), (.1, .1, .6), DARK, parent=p, vertices=6)
    return p


def roller(name):
    p = empty(name)
    prim("cylinder", f"{name}_rodillo", (0, 2.0, .8), (.8, .8, 1.15), STEEL, parent=p, rot=(0, math.radians(90), 0), vertices=14)
    prim("cube", f"{name}_marco", (0, 2.0, 1.15), (1.3, .5, .25), MACHINE, parent=p)
    prim("cube", f"{name}_cuerpo", (0, -.4, 1.2), (1.1, 1.6, .75), MACHINE, parent=p)
    prim("cube", f"{name}_cabina", (0, -.5, 2.5), (.8, .7, .55), GLASS, parent=p)
    wheels(p, (-1.1, 1.1), (-1.2,), r=.6, w=.5)
    return p


def truck(name, mat, bed=MACHINE):
    p = empty(name)
    prim("cube", f"{name}_cabina", (0, 3.2, 1.7), (1.25, 1.0, 1.1), mat, parent=p)
    prim("cube", f"{name}_parabrisas", (0, 4.22, 2.1), (1.05, .03, .5), GLASS, parent=p)
    prim("cube", f"{name}_chasis", (0, 0, .85), (1.2, 4.2, .2), DARK, parent=p)
    prim("cube", f"{name}_caja", (0, -1.0, 1.9), (1.3, 2.8, .9), bed, parent=p)
    wheels(p, (-1.15, 1.15), (3.0, -.8, -2.6), r=.55, w=.4)
    return p


def car(name, mat):
    p = empty(name)
    prim("cube", f"{name}_cuerpo", (0, 0, .62), (.95, 2.1, .38), mat, parent=p)
    prim("cube", f"{name}_cabina", (0, -.2, 1.25), (.82, 1.15, .32), GLASS, parent=p)
    prim("cube", f"{name}_techo", (0, -.2, 1.6), (.84, 1.05, .04), mat, parent=p)
    wheels(p, (-.92, .92), (1.35, -1.35), r=.36, w=.25)
    return p



def pavimentadora(name, t0=0.0):
    p = empty(name)
    prim("cube", f"{name}_cuerpo", (0, 0, 1.1), (1.8, 1.7, .7), MACHINE, parent=p)
    prim("cube", f"{name}_tolva", (0, 2.0, 1.3), (1.7, .6, .5), DARK, parent=p)
    prim("cube", f"{name}_regla", (0, -2.1, .35), (2.6, .3, .3), MACHINE, parent=p)
    prim("cube", f"{name}_cabina", (0, -.6, 2.3), (.9, .6, .5), GLASS, parent=p)
    prim("cube", f"{name}_techo", (0, -.6, 2.95), (1.6, 1.2, .06), MACHINE, parent=p)
    for x in (-1.6, 1.6):
        prim("cube", f"{name}_oruga{x}", (x, 0, .35), (.3, 1.6, .35), DARK, parent=p)
    vapor(p, t0, (-3, 3), (-8, -3))
    return p


def vapor(parent, t0, xs, ys, count=10, mat=None, tam=1.0):
    """Puffs that rise and grow in a loop, parented so they follow the machine (steam, dust)."""
    for i in range(count):
        pf = prim("ico_sphere", f"{parent.name}_vapor{i}", (random.uniform(*xs), random.uniform(*ys), .6), (.5, .5, .4), mat or STEAM, parent=parent, subdivisions=1)
        pf["frente_ok"] = True  # puffs of air may float in front of the cut
        period = random.uniform(.9, 1.3)
        fa = F(t0 - random.uniform(0, period))
        key(pf, "location", fa, (pf.location.x, pf.location.y, .45), interp="LINEAR")
        key(pf, "location", fa + round(period * FPS), (pf.location.x, pf.location.y, 2.4), interp="LINEAR")
        key(pf, "scale", fa, (.2 * tam, .2 * tam, .2 * tam), interp="LINEAR")
        key(pf, "scale", fa + round(period * FPS), (.9 * tam, .9 * tam, .7 * tam), interp="LINEAR")
        for fc in _fcurves(pf.animation_data.action):
            fc.modifiers.new("CYCLES")


def compactadora(name):
    p = empty(name)
    prim("cube", f"{name}_placa", (0, 0, .12), (.45, .4, .12), MACHINE, parent=p)
    prim("cube", f"{name}_motor", (0, 0, .42), (.3, .28, .2), DARK, parent=p)
    prim("cylinder", f"{name}_manija", (0, -.8, .95), (.04, .04, .7), DARK, parent=p, rot=(math.radians(-50), 0, 0), vertices=6)
    return p


def teodolito(name, loc):
    p = empty(name, loc)
    for a in range(3):
        ang = a * 2.1
        leg = prim("cylinder", f"{name}_pata{a}", (.45 * math.cos(ang), .45 * math.sin(ang), .75), (.04, .04, .78), WOOD, parent=p, vertices=6)
        leg.rotation_euler = (math.radians(-17) * math.sin(ang), math.radians(17) * math.cos(ang), 0)
    prim("cube", f"{name}_cuerpo", (0, 0, 1.65), (.2, .25, .22), MACHINE, parent=p)
    prim("cylinder", f"{name}_lente", (0, -.32, 1.7), (.08, .08, .12), DARK, parent=p, rot=(math.radians(90), 0, 0), vertices=8)
    return p


def estaca(name, loc):
    p = empty(name, loc)
    prim("cylinder", f"{name}_palo", (0, 0, .55), (.06, .06, .55), WOOD, parent=p, vertices=6)
    prim("cube", f"{name}_cinta", (0, 0, 1.05), (.1, .1, .08), ORANGE, parent=p)
    return p


def rociador(parent, y, t0, count=26, mat=None, ancho=1.5):
    """Liquid drops falling in a loop from a spray bar at local y (asphalt distributor, irrigation)."""
    for i in range(count):
        d = prim("ico_sphere", f"{parent.name}_gota{i}", (random.uniform(-ancho, ancho), y, .4), (.05, .05, .09), mat or PRIME, parent=parent, subdivisions=1)
        period = random.uniform(.25, .35)
        fa = F(t0 - random.uniform(0, period))
        key(d, "location", fa, (d.location.x, y, .45), interp="LINEAR")
        key(d, "location", fa + round(period * FPS), (d.location.x, y - .15, -.15), interp="LINEAR")
        for fc in _fcurves(d.animation_data.action):
            fc.modifiers.new("CYCLES")


def aparecer(ob, t, final=(1, 1, 1)):
    """Instant appearance of a parented group at time t (a vehicle entering the shot)."""
    key(ob, "scale", 1, (0, 0, 0), interp="CONSTANT")
    key(ob, "scale", F(t) - 1, (0, 0, 0), interp="CONSTANT")
    key(ob, "scale", F(t), final)


# ------------------------------------------------------------------ camera
_CAM = {}


def camara(lens=24):
    target = empty("mira")
    cam = link(bpy.data.objects.new("camara", bpy.data.cameras.new("camara")))
    cam.data.lens = lens
    cam.data.clip_start = .05
    cam.data.clip_end = 6000
    sc.camera = cam
    cam.constraints.new("TRACK_TO").target = target
    _CAM.update(cam=cam, target=target)
    return cam


_SLICED = set()


def _section_key(f0, sliced):
    if SECTION:
        _SLICED.add(bool(sliced))
        key(SECTION, "location", f0, (0, 0 if sliced else SECTION_OFF, 0), interp="CONSTANT")


def _fijar_corte():
    """When every shot uses the same cut, the cutter is made static: an animated cutter (even with constant keys)
    makes Blender re-evaluate every boolean that uses it on every frame, which was most of the render time."""
    if SECTION and len(_SLICED) == 1 and SECTION.animation_data:
        SECTION.animation_data_clear()
        SECTION.location = (0, 0 if True in _SLICED else SECTION_OFF, 0)


def shot(t0, t1, cam_a, cam_b, aim_a, aim_b, sliced=False, lens=24, smooth=True):
    """One camera move from cam_a to cam_b looking from aim_a to aim_b; sliced shows the cutaway."""
    cam, target = _CAM["cam"], _CAM["target"]
    f0, f1 = F(t0), max(F(t0) + 1, F(t1) - 1)
    for ob, a, b in ((cam, cam_a, cam_b), (target, aim_a, aim_b)):
        key(ob, "location", f0, a, interp="BEZIER" if smooth else "LINEAR")
        key(ob, "location", f1, b, interp="LINEAR")
    key(cam, "data.lens", f0, lens, interp="CONSTANT")
    _section_key(f0, sliced)


def follow(t0, t1, ob, cam_off, aim_off, sliced=False, lens=24):
    """Camera that travels with an object, keeping the given offsets."""
    cam, target = _CAM["cam"], _CAM["target"]
    f0, f1 = F(t0), F(t1) - 1
    for f in range(f0, f1 + 1, 3):
        sc.frame_set(f)
        p = ob.matrix_world.translation
        key(cam, "location", f, tuple(p[i] + cam_off[i] for i in range(3)), interp="LINEAR")
        key(target, "location", f, tuple(p[i] + aim_off[i] for i in range(3)), interp="LINEAR")
    key(cam, "data.lens", f0, lens, interp="CONSTANT")
    _section_key(f0, sliced)


def revisar(t):
    """Problems a viewer would notice at time t: pieces sticking out in front of the cut that are not sliced
    (they float), and a camera at or below ground level (it sees the cut face edge-on or from inside the soil).
    Objects meant to sit in front of the face (rain, drops, bubbles) carry ob["frente_ok"] = True."""
    out = []
    cam = _CAM.get("cam")
    sliced = SECTION is not None and abs(SECTION.matrix_world.translation.y) < 1
    if cam and cam.matrix_world.translation.z < (.8 if sliced else .3):
        out.append(f"t={t}: camara a {cam.matrix_world.translation.z:.2f} m, casi a ras del suelo")
    if not sliced:
        return out
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in sc.objects:
        if ob.type != "MESH" or ob.display_type == "WIRE" or ob.hide_render or ob.get("frente_ok"):
            continue
        if any(m.type == "BOOLEAN" and m.object is not None and (m.object == SECTION or m.object.parent == SECTION) for m in ob.modifiers):
            continue
        e = ob.evaluated_get(dg)
        if abs(e.matrix_world.determinant()) < 1e-9:
            continue  # scaled to nothing: not on screen
        pts = [e.matrix_world @ Vector(c) for c in e.bound_box]
        ys = [p.y for p in pts]
        front = [p for p in pts if p.y < -.05]
        seen = any(0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0 for v in (world_to_camera_view(sc, cam, p) for p in front))
        if front and seen:
            out.append(f"t={t}: {ob.name} asoma delante del corte sin cortarse (y min {min(ys):.2f})")
    return out


def terminar():
    """Writes beats.json and renders: --cuadros t1,t2 (review stills), --guardar (.blend) or the full animation."""
    (EP / "beats.json").write_text(json.dumps(BEATS, indent=1), encoding="utf-8")
    (EP / "frames").mkdir(exist_ok=True)
    _fijar_corte()
    if "--cuadros" in sys.argv:
        for t in sys.argv[sys.argv.index("--cuadros") + 1].split(","):
            sc.frame_set(F(float(t)))
            for warning in revisar(float(t)):
                print("AVISO", warning, flush=True)
            sc.render.filepath = str(EP / "frames" / f"revision_{float(t):05.1f}.jpg")
            bpy.ops.render.render(write_still=True)
    elif "--guardar" in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(EP / "escena.blend"))
    else:
        bpy.ops.render.render(animation=True)


# ------------------------------------------------------------------ weather and materials falling
def rain(prefix, cx, cy, spread_x, spread_y, t0, t1, count=260):
    for i in range(count):
        x, y = cx + random.uniform(-spread_x, spread_x), cy + random.uniform(-spread_y, spread_y)
        d = prim("cube", f"{prefix}{i}", (x, y, 0), (.015, .015, .28), RAIN)
        d["frente_ok"] = True
        period = random.uniform(.45, .6)
        phase = random.uniform(0, period)
        top, bottom = random.uniform(9, 14), 0
        fa = F(t0 - phase)
        key(d, "location", fa, (x, y, top), interp="LINEAR")
        key(d, "location", fa + round(period * FPS), (x, y, bottom), interp="LINEAR")
        for fc in _fcurves(d.animation_data.action):
            if fc.data_path == "location":
                fc.modifiers.new("CYCLES")
        show(d, max(0, t0), t1)



def gravel_rain(prefix, t0, t1, ztop, mat, size, count=40, xs=(-5, 5), ys=(.1, 6)):
    """Stones that fall onto a surface at ztop and vanish, while a layer grows under them."""
    for i in range(count):
        x, y = random.uniform(*xs), random.uniform(*ys)
        s = random.uniform(*size)
        pb = prim("ico_sphere", f"{prefix}{i}", (x, y, ztop + 4), (s, s, s), mat, subdivisions=1)
        t = random.uniform(t0, t1)
        key(pb, "scale", 1, (0, 0, 0), interp="CONSTANT")
        key(pb, "scale", F(t) - 1, (0, 0, 0), interp="CONSTANT")
        key(pb, "scale", F(t), (s, s, s))
        key(pb, "location", F(t), (x, y, ztop + 3.5))
        key(pb, "location", F(t + .35), (x, y, ztop))
        unpop(pb, t + .5, .15)




# ------------------------------------------------------------------ deformable slab (sinks, bulges, cracks)
def losa(name, x0, x1, y0, y1, z0, z1, mat, deform, nx=15, ny=26):
    """Grid slab with a shape key 'deform' where each vertex moves by deform(x, y) in z. Animate it with
    shape_key(ob, "deform", frame, value)."""
    v, f = [], []
    for zz in (z0, z1):
        for j in range(ny):
            for i in range(nx):
                v.append((lerp(x0, x1, i / (nx - 1)), lerp(y0, y1, j / (ny - 1)), zz))
    off = nx * ny

    def vid(i, j, top):
        return top * off + j * nx + i

    for j in range(ny - 1):
        for i in range(nx - 1):
            f.append((vid(i, j, 1), vid(i + 1, j, 1), vid(i + 1, j + 1, 1), vid(i, j + 1, 1)))
            f.append((vid(i, j, 0), vid(i, j + 1, 0), vid(i + 1, j + 1, 0), vid(i + 1, j, 0)))
    for i in range(nx - 1):
        for j in (0, ny - 1):
            f.append((vid(i, j, 0), vid(i + 1, j, 0), vid(i + 1, j, 1), vid(i, j, 1)))
    for j in range(ny - 1):
        for i in (0, nx - 1):
            f.append((vid(i, j, 0), vid(i, j + 1, 0), vid(i, j + 1, 1), vid(i, j, 1)))
    ob = mesh_object(name, v, f, mat)
    ob.shape_key_add(name="Basis")
    kb = ob.shape_key_add(name="deform", from_mix=False)
    for p in kb.data:
        p.co.z += deform(p.co.x, p.co.y)
    return ob


def persona(name, loc, mat=None, sentada=False):
    """Simple low-poly person: body, head and legs, standing or sitting."""
    p = empty(name, loc)
    mat = mat or random.choice([RED, BLUE, GREEN_P, ORANGE, WALLS[1]])
    h = .45 if sentada else .8
    prim("cylinder", f"{name}_cuerpo", (0, 0, h + .35), (.22, .18, .35), mat, parent=p, vertices=8)
    prim("ico_sphere", f"{name}_cabeza", (0, 0, h + .88), (.17, .17, .19), SKIN, parent=p, subdivisions=1)
    for s in (-.1, .1):
        prim("cylinder", f"{name}_pierna{s}", (s, -.15 if sentada else 0, h / 2), (.07, .07, h / 2), DARK, parent=p, vertices=6)
    return p


GREEN_P = material("ropa_verde", (.20, .60, .30))
SKIN = material("piel", (.92, .72, .55))


def corte_frente(d=.03):
    """A second section cutter d metres in front of the main one, for objects buried in the soil (piles, pipes, roots):
    their cut face then sits just in front of the soil's cut face instead of fighting with it (z-fighting)."""
    c = cutter(box("corte_seccion_frente", -1000, 1000, -2000, -d, -200, 200, None))
    c.parent = SECTION
    return c


# ------------------------------------------------------------------ factory helpers: things that travel and spin
def flujo(prefix, pts, t0, t1, count, mat, size=(.2, .2, .2), period=2.0, grow=None, kind="ico_sphere", jitter=.15):
    """count objects travelling in a loop along the polyline pts (world points) between t0 and t1, evenly spread.
    grow=(a, b) scales them from a to b along the way (dough that puffs up, drops that shrink)."""
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(segs)
    obs = []
    for i in range(count):
        ob = prim(kind, f"{prefix}{i}", pts[0], size, mat, subdivisions=1) if kind == "ico_sphere" else prim(kind, f"{prefix}{i}", pts[0], size, mat)
        ob.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
        off = (random.uniform(-jitter, jitter), random.uniform(-jitter, jitter), random.uniform(-jitter * .5, jitter * .5))
        fa = F(t0) - round(period * FPS * i / count)
        acc = 0.0
        for k, p in enumerate(pts):
            u = acc / total
            f = fa + round(u * period * FPS)
            key(ob, "location", f, tuple(p[j] + off[j] for j in range(3)), interp="LINEAR")
            if grow:
                sc_ = lerp(grow[0], grow[1], u)
                key(ob, "scale", f, tuple(s * sc_ for s in size), interp="LINEAR")
            if k < len(segs):
                acc += segs[k]
        for fc in fcurves(ob.animation_data.action):
            fc.modifiers.new("CYCLES")
        show(ob, t0, t1)
        obs.append(ob)
    return obs


def girar(ob, eje, vel, t0=0.0, t1=None):
    """Spins ob about axis 0/1/2 at vel rad/s between t0 and t1 (keeps its other angles)."""
    t1 = UNTIL + 1 if t1 is None else t1
    base = list(ob.rotation_euler)
    a = base.copy()
    key(ob, "rotation_euler", F(t0), tuple(a), interp="LINEAR")
    a[eje] = base[eje] + vel * (t1 - t0)
    key(ob, "rotation_euler", F(t1), tuple(a), interp="LINEAR")


# ------------------------------------------------------------------ factory pieces shared by "¿Cómo se hace?"
def torno(name, perfil, mat, loc=(0, 0, 0), segs=24, formas=None, parent=None):
    """Solid of revolution around z from a profile [(r, z), ...] (first and last points with r=0 close it).
    formas={'nombre': perfil2} adds shape keys with the same number of points (a preform that stretches and inflates)."""
    def ring_verts(prof):
        vs = []
        for r, z in prof:
            if r == 0:  # pole: a single vertex closes the end without degenerate faces
                vs.append((0.0, 0.0, z))
                continue
            for k in range(segs):
                a = 2 * math.pi * k / segs
                vs.append((r * math.cos(a), r * math.sin(a), z))
        return vs
    starts, idx = [], 0
    for r, _ in perfil:
        starts.append(idx)
        idx += 1 if r == 0 else segs
    faces = []
    for i in range(len(perfil) - 1):
        a, b = starts[i], starts[i + 1]
        pa, pb = perfil[i][0] == 0, perfil[i + 1][0] == 0
        for k in range(segs):
            k1 = (k + 1) % segs
            if pa and not pb:
                faces.append((a, b + k1, b + k))
            elif pb and not pa:
                faces.append((a + k, a + k1, b))
            elif not pa and not pb:
                faces.append((a + k, a + k1, b + k1, b + k))
    ob = mesh_object(name, ring_verts(perfil), faces, mat)
    for poly_ in ob.data.polygons:
        poly_.use_smooth = True
    if formas:
        ob.shape_key_add(name="base")
        for nm, prof in formas.items():
            kb = ob.shape_key_add(name=nm)
            for v, co in zip(kb.data, ring_verts(prof)):
                v.co = co
    ob.location = loc
    if parent:
        ob.parent = parent
    return ob


def desfile(obs, pts, t0, t1, period, hold=None):
    """Moves existing objects in a loop along the polyline pts between t0 and t1, evenly spread (bottles on a belt)."""
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(segs)
    for i, ob in enumerate(obs):
        fa = F(t0) - round(period * FPS * i / len(obs))
        acc = 0.0
        for k, p in enumerate(pts):
            key(ob, "location", fa + round(acc / total * period * FPS), p, interp="LINEAR")
            if k < len(segs):
                acc += segs[k]
        for fc in fcurves(ob.animation_data.action):
            if fc.data_path == "location":
                fc.modifiers.new("CYCLES")
        show(ob, t0, t1)


def nave(x0, x1, y0=-14, y1=24, alto=13, luces=4, energia=5000, ventanas=True):
    """Factory hall with floor, walls, roof, trusses, hanging lamps and big windows onto the countryside.
    Four large area lights instead of many small ones: the picture is nearly the same and the render much lighter."""
    floor_m = material("piso_fabrica", (.62, .64, .66), rough=.5)
    variar(floor_m, .15, .08)
    wall_m = material("muro_fabrica", (.86, .88, .90))
    hall = cutter(box("corte_nave", x0, x1, y0, y1 + 2, -.31, 1, None))
    suelo([("pasto", 0, -.15, GRASS), ("tierra", -.15, -.65, TOP), ("subsuelo", -.65, -6, SUB), ("roca", -6, -40, ROCKL)],
          {"pasto": [(hall, True)], "tierra": [(hall, True)]})
    cut(box("piso", x0, x1, y0, y1 + 2, -.3, .05, floor_m), SECTION)
    box("muro_fondo", x0, x1, y1 - 2, y1 - 1.4, .05, alto, wall_m)
    for nm, a, b in (("izq", x0, x0 + .6), ("der", x1 - .6, x1)):
        cut(box(f"muro_{nm}", a, b, y0, y1 - 1.4, .05, alto, wall_m), SECTION)
    if ventanas:
        n = int((x1 - x0 - 6) // 11)
        for k in range(n):
            x = x0 + 6 + k * 11
            box(f"ventanal{k}", x, x + 7, y1 - 2.1, y1 - 1.3, 4, 10, GLASS)
    box("techo_nave", x0, x1, 0, y1 - 1.4, alto + .2, alto + .5, wall_m)  # behind the cut only: nothing to slice
    for k in range(luces):
        lt = link(bpy.data.objects.new(f"luz_nave{k}", bpy.data.lights.new(f"luz_nave{k}", "AREA")))
        lt.data.energy = energia
        lt.data.size = (x1 - x0) / luces
        lt.data.color = (1.0, .96, .9)
        lt.location = (x0 + (k + .5) * (x1 - x0) / luces, 3, alto - .7)
    for k in range(int((x1 - x0) // 10)):
        x = x0 + 4 + k * 10
        box(f"viga{k}", x - .2, x + .2, 0, y1 - 1.4, alto - .4, alto + .2, STEEL)
        for y in (4, 14):
            prim("cone", f"lampara{k}_{y}", (x + 5, y, alto - 1.8), (.7, .7, .4), DARK, vertices=10)
            prim("ico_sphere", f"foco{k}_{y}", (x + 5, y, alto - 2.15), (.25, .25, .25), material(f"luz{k}{y}", (1, .95, .8), emit=4.0), subdivisions=1)
    paisaje(lambda x, y: (y > y1 + 6 or x < x0 - 8 or x > x1 + 8) and not (y < 2 and abs(x) < 120), arboles=220,
            campos=[(-120, -70, 40, 90), (-60, 0, 40, 90), (10, 70, 40, 90), (80, 130, 40, 90)])


def soporte(name, x0, x1, y1, h):
    """Back legs of a machine (the front ones would be cut away entirely in the cutaway)."""
    for x in (x0, x1):
        box(f"{name}_pata{x}", x - .12, x + .12, y1 - .12, y1 + .12, .05, h, STEEL)
