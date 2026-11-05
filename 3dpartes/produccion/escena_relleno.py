"""Landfill episode (02-relleno-sanitario) on top of motor3d. A lined pit is built in open country far from the city,
filled with cells of trash, drained, vented and finally capped as a park. A bad open dump at x=-40 shows the problem.

    blender -b --python escena_relleno.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar]"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motor3d import *  # noqa: E402,F401,F403

S = {k: SC[f"b{k}"] for k in range(1, 19)}
AQUA = material("acuifero", (.42, .62, .82))
PLUME = material("contaminacion", (.42, .40, .14))
CLAY = material("arcilla", (.70, .36, .24))
MEMBRANE = material("geomembrana", (.08, .08, .09), rough=.25)
FELT = material("geotextil", (.92, .92, .88))
GRAVELM = material("grava_drenaje", (.58, .56, .52))
LEACH = material("lixiviado", (.48, .36, .10), rough=.1, alpha=.85)
PIPEW = material("tubo_blanco", (.95, .95, .95))
GASM = material("metano", (.55, .95, .45), alpha=.45, emit=.8)
FIRE = material("fuego", (1.0, .55, .10), emit=4.0)
BOLT = material("rayo", (1.0, .92, .20), emit=3.0)
SPARK = material("chispa", (1.0, .75, .30), emit=5.0)
GREEN = material("camion_verde", (.18, .55, .28))
CAPCLAY = material("arcilla_tapa", (.62, .34, .22))
TRASH = material("basura", (.5, .5, .5))
nt = TRASH.node_tree
vor = nt.nodes.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 3.0
trash_ramp = nt.nodes.new("ShaderNodeValToRGB")
trash_ramp.color_ramp.interpolation = "CONSTANT"
els = trash_ramp.color_ramp.elements
for pos, c in ((0, (.30, .26, .20)), (.2, (.18, .18, .19)), (.4, (.42, .46, .30)), (.6, (.62, .58, .48)), (.8, (.28, .36, .48))):
    e = els[0] if pos == 0 else (els[1] if pos == .2 else els.new(pos))
    e.position = pos
    e.color = tuple(v ** 2.2 for v in c) + (1,)
nt.links.new(vor.outputs["Distance"], trash_ramp.inputs["Fac"])
nt.links.new(trash_ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])

section = seccion()


# ------------------------------------------------------------------ pit geometry: a 45-degree pit 4 m deep
def E(d, z):
    """Half-width and y range of the pit surface pushed inward by d metres, at height z."""
    g = (z + 4) - d * 1.414
    return 10 + g, -6 - g, 26 + g


def frustum(name, za, zb, ea, eb, mat, origin_z=None):
    """Solid between two horizontal rectangles ea=(hx, y0, y1) at za and eb at zb."""
    oz = za if origin_z is None else origin_z
    v = []
    for z, (hx, y0, y1) in ((za, ea), (zb, eb)):
        v += [(-hx, y0, z - oz), (hx, y0, z - oz), (-hx, y1, z - oz), (hx, y1, z - oz)]
    ob = mesh_object(name, v, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)], mat)
    ob.location.z = oz
    return ob


def shell(name, d0, d1, mat, ztop=0.0):
    """Liner between the pit surface pushed in by d0 (outside) and d1 (inside), up to the rim."""
    rings = []
    for d in (d0, d1):
        zb = -4 + d
        hb, ht = E(d, zb), E(d, ztop)
        rings.append([(-hb[0], hb[1], zb), (hb[0], hb[1], zb), (hb[0], hb[2], zb), (-hb[0], hb[2], zb),
                      (-ht[0], ht[1], ztop), (ht[0], ht[1], ztop), (ht[0], ht[2], ztop), (-ht[0], ht[2], ztop)])
    v = rings[0] + rings[1]
    f = []
    for o in (0, 8):
        f.append((o + 0, o + 1, o + 2, o + 3))
        for i in range(4):
            j = (i + 1) % 4
            f.append((o + i, o + j, o + 4 + j, o + 4 + i))
    for i in range(4):
        j = (i + 1) % 4
        f.append((4 + i, 4 + j, 12 + j, 12 + i))
    ob = mesh_object(name, v, f, mat)
    cut(ob, section)
    return ob


def reveal(ob, t0, t1, y0=-12, y1=32, follower=None, z=None):
    """Lays a liner from y0 to y1 between t0 and t1 with a cutter that removes everything beyond the front edge."""
    c = cutter(box(f"corte_{ob.name}", -60, 60, 0, 120, -20, 20, None))
    cut(ob, c)
    show(ob, t0)
    f0, f1 = F(t0), F(t1)
    key(c, "location", 1, (0, y0, 0), interp="CONSTANT")
    for f in range(f0, f1 + 1, 2):
        y = lerp(y0, y1, (f - f0) / max(1, f1 - f0))
        key(c, "location", f, (0, y, 0), interp="LINEAR")
        if follower:
            key(follower, "location", f, (0, y, z), interp="LINEAR")
    key(c, "location", f1 + 2, (0, 500, 0), interp="CONSTANT")


CELL0 = -4 + 1.32
TRASH_H, COVER_H, NCELL = 1.0, .25, 5


def ext(z):
    hx, y0, y1 = E(1.32, min(z, 0))
    k = 2 * max(0.0, z)
    return hx - k, y0 + k, y1 - k


# ------------------------------------------------------------------ cutters, ground, landscape
pit_cut = cutter(frustum("corte_hoyo", -4, 3, E(0, -4), E(0, 3), None, origin_z=0))
pit_cut.location.z = 4.5
dump_cut = cutter(frustum("corte_tiradero", -2.5, 2, (3, -2, 6), (7.5, -6.5, 10.5), None, origin_z=0))
dump_cut.location = (-40, 0, 50)
plume = prim("ico_sphere", "pluma", (-40, 2, -7.4), (.01, .01, .01), PLUME, subdivisions=2)
pond_cut = cutter(frustum("corte_laguna", -1.4, 1, (4, 17.5, 26.5), (6.4, 15.1, 28.9), None))
pond_cut.location.x = 25
river_cut = cutter(box("corte_rio", -172, -160, -400, 600, -1.5, 1, None))
chan_cuts = []
for i, (a, b, c, d) in enumerate([(-16.9, -15.5, -12, 32), (15.5, 16.9, -12, 32), (-16.9, 16.9, -12, -10.6), (-16.9, 16.9, 30.6, 32)]):
    cc = cutter(box(f"corte_canal{i}", a, b, c, d, -.8, 1, None))
    cc.location.z = 2
    chan_cuts.append(cc)
top_cuts = [(river_cut, True), (pit_cut, False), (dump_cut, False), (pond_cut, False)] + [(c, False) for c in chan_cuts]
ground = suelo([("pasto", 0, -.15, GRASS), ("tierra", -.15, -.65, TOP), ("subsuelo", -.65, -6, SUB), ("acuifero", -6, -9, AQUA), ("roca", -9, -40, ROCKL)],
               {"pasto": top_cuts, "tierra": top_cuts, "subsuelo": [(river_cut, True), (pit_cut, False), (dump_cut, False), (pond_cut, False)],
                "acuifero": [(plume, False)]})
cut(plume, section)
cut(box("rio", -172, -160, -400, 600, -1.5, -.6, WATER), section)
agua_animada(WATER)


def libre(x, y):
    return not (-26 < x < 40 and -18 < y < 44) and not (-52 < x < -28 and -10 < y < 14) and not (-178 < x < -154) and not (y > 230) and not (y < 2 and abs(x) < 60)


paisaje(libre, arboles=300, campos=[(44, 80, -40, -4), (44, 80, 0, 36), (-110, -70, 20, 60)])
for i in range(40):  # the city far away on the horizon
    x, y = random.uniform(-260, 300), random.uniform(760, 860)
    w, h = random.uniform(12, 24), random.uniform(16, 60)
    box(f"edificio{i}", x - w / 2, x + w / 2, y - w / 2, y + w / 2, 0, h, random.choice(WALLS + [GLASS, CONCRETE]))


def bag(name, loc, s):
    p = empty(name, loc)
    prim("ico_sphere", f"{name}_b", (0, 0, s * .8), (s, s * .9, s * .8), random.choice((DARK, GREEN, BLUE, WHITE, DARK)), parent=p, subdivisions=1)
    prim("cone", f"{name}_n", (0, 0, s * 1.7), (s * .3, s * .3, s * .35), DARK, parent=p, vertices=5)
    return p


# ------------------------------------------------------------------ b1: trash piles up / b2: the bad dump poisons the water
bags = []
for i in range(46):
    r, a = random.uniform(0, 4.5) ** .8, random.uniform(0, 2 * math.pi)
    x, y = -40 + r * math.cos(a), 2 + r * math.sin(a)
    s = random.uniform(.4, .65)
    b = bag(f"bolsa{i}", (x, y, 6), s)
    t = S[1]["start"] + .2 + i * .075
    aparecer(b, t)
    key(b, "location", F(t), (x, y, 6))
    key(b, "location", F(t + .3), (x, y, max(0, 1.2 - r * .25) + random.uniform(0, .5)))
    bags.append((b, x, y))
beat("bolsas", [round(S[1]["start"] + .2 + i * .075 * 4, 3) for i in range(12)])
t_hole = S[2]["start"] + .2
key(dump_cut, "location", 1, (-40, 0, 50), interp="CONSTANT")
key(dump_cut, "location", F(t_hole), (-40, 0, 2.5))
key(dump_cut, "location", F(t_hole + .6), (-40, 0, 0))
key(dump_cut, "location", F(S[3]["start"]) - 1, (-40, 0, 0))
key(dump_cut, "location", F(S[3]["start"]), (-40, 0, 50), interp="CONSTANT")
for b, x, y in bags:
    key(b, "location", F(t_hole + .1), tuple(b.location))
    key(b, "location", F(t_hole + .7), (x, y, -2.5 + random.uniform(0, 1.6)))
    show(b, None, S[3]["start"])
for i in range(30):  # garbage juice seeping down in front of the cut face
    d = prim("ico_sphere", f"jugo{i}", (-40 + random.uniform(-3, 3), -.15, 0), (.09, .05, .14), PLUME, subdivisions=1)
    period = random.uniform(.8, 1.1)
    fa = F(S[2]["start"] + 1.0 - random.uniform(0, period))
    key(d, "location", fa, (d.location.x, -.15, -2.4), interp="LINEAR")
    key(d, "location", fa + round(period * FPS), (d.location.x, -.15, -6.6), interp="LINEAR")
    for fc in fcurves(d.animation_data.action):
        fc.modifiers.new("CYCLES")
    show(d, S[2]["start"] + 1.0, S[3]["start"])
key(plume, "scale", F(S[2]["start"] + 1.6), (.01, .01, .01))
key(plume, "scale", F(S[2]["end"]), (7, 4, 1.3))
show(plume, None, S[3]["start"])
beat("hoyo", t_hole)
beat("filtracion", S[2]["start"] + 1.0)

# ------------------------------------------------------------------ b3: choosing the site
tri = teodolito("tripode", (19, -4, 0))
pop(tri, S[3]["start"] + .4, final=(1.6, 1.6, 1.6))
stake_t = []
for i, (x, y) in enumerate([(-14, -10), (14, -10), (14, 30), (-14, 30), (0, -10), (0, 30), (-14, 10), (14, 10)]):
    st = estaca(f"estaca{i}", (x, y, 0))
    t = S[3]["start"] + .9 + i * .25
    pop(st, t, final=(3, 3, 3))
    unpop(st, S[4]["start"] + .2)
    stake_t.append(round(t, 3))
unpop(tri, S[4]["start"] + .2)
beat("estacas", stake_t)

# ------------------------------------------------------------------ b4: dig the pit, compact the clay liner
dig0, dig1 = S[4]["start"] + .1, S[4]["start"] + 2.3
key(pit_cut, "location", 1, (0, 0, 4.5), interp="CONSTANT")
key(pit_cut, "location", F(dig0), (0, 0, 4.5))
key(pit_cut, "location", F(dig1), (0, 0, 0))
dz = dozer("excavadora")
aparecer(dz, dig0, (1.3, 1.3, 1.3))
for f in range(F(dig0), F(dig1) + 1, 3):
    k = (f - F(dig0)) / (F(dig1) - F(dig0))
    key(dz, "location", (f), (lerp(-4, 4, k), 10 + 9 * math.sin(k * 7), -4 + 4.5 * (1 - k) if k < .98 else -4), interp="LINEAR")
unpop(dz, dig1 + .05, .05)
pile = prim("cone", "monton", (-24, 10, 0), (5, 5, 3), TOP, vertices=9)
key(pile, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(pile, "scale", F(dig0), (0, 0, 0))
key(pile, "scale", F(dig1), (5, 5, 3))
clay = shell("arcilla", 0, .6, CLAY)
rl = roller("rodillo")
aparecer(rl, dig1 + .05, (1.2, 1.2, 1.2))
reveal(clay, dig1 + .05, S[4]["end"] - .1, follower=rl, z=-3.4)
unpop(rl, S[5]["start"] + .05, .05)
beat("excavar", [dig0, dig1])
beat("rodillo", [dig1 + .05, S[4]["end"] - .1])

# ------------------------------------------------------------------ b5: geomembrane rolled out and welded
mem = shell("geomembrana", .6, .72, MEMBRANE)
roll = prim("cylinder", "rollo", (0, -12, -3.0), (.5, .5, 11), MEMBRANE, rot=(0, math.radians(90), 0), vertices=14)
aparecer(roll, S[5]["start"])
m0, m1 = S[5]["start"] + .1, L("b5", 0)["end"] - .5
reveal(mem, m0, m1, follower=roll, z=-2.75)
unpop(roll, m1 + .1)
spark_t = []
for i in range(36):
    x = random.choice((-4.5, 0, 4.5))
    y = random.uniform(-5, 25)
    sp = prim("ico_sphere", f"chispa{i}", (x, y, -3.25), (.16, .16, .16), SPARK, subdivisions=1)
    t = m0 + .4 + (y + 5) / 30 * (m1 - m0) + random.uniform(0, .3)
    pop(sp, t, dur=.06)
    unpop(sp, t + .25, .06)
    spark_t.append(t)
beat("rollo_membrana", [m0, m1])
beat("soldadura", [min(spark_t), max(spark_t)])

# ------------------------------------------------------------------ b6: a sharp rock
rock = prim("cone", "piedra_filosa", (6, 1.2, 4), (.55, .55, .8), ROCKL, vertices=5, rot=(math.radians(180), 0, 0))
t_rock = S[6]["start"] + .3
aparecer(rock, t_rock, tuple(rock.scale))
key(rock, "location", F(t_rock), (6, 1.2, 4))
key(rock, "location", F(t_rock + .45), (6, 1.2, -2.95))
hole = prim("cylinder", "perforacion", (6, 1.2, -3.27), (.35, .35, .02), CRACKM, vertices=10)
pop(hole, t_rock + .45, dur=.1)
unpop(rock, S[7]["start"] + .1)
unpop(hole, S[7]["start"] + .1)
beat("piedra", t_rock + .45)

# ------------------------------------------------------------------ b7: geotextile
felt = shell("geotextil", .72, .87, FELT)
roll2 = prim("cylinder", "rollo2", (0, -12, -2.9), (.55, .55, 11), FELT, rot=(0, math.radians(90), 0), vertices=14)
aparecer(roll2, S[7]["start"])
g0, g1 = S[7]["start"] + .1, L("b7", 0)["end"]
reveal(felt, g0, g1, follower=roll2, z=-2.55)
unpop(roll2, g1 + .1)
beat("rollo_tela", [g0, g1])

# ------------------------------------------------------------------ b8: leachate pools at the bottom
z_l = -4 + .87
leach = frustum("lixiviado", z_l, z_l + .45, E(.87, z_l), E(.87, z_l + .45), LEACH)
cut(leach, section)
key(leach, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(leach, "scale", F(S[8]["start"] + .3), (1, 1, .01))
key(leach, "scale", F(S[8]["start"] + 2.2), (1, 1, 1))
show(leach, S[8]["start"] + .3)
rain("goteo", 0, 10, 8, 14, S[8]["start"], S[8]["end"], 90)
for o in bpy.data.objects:
    if o.name.startswith("goteo"):
        o.data.materials[0] = LEACH
beat("lixiviado", S[8]["start"] + .3)

# ------------------------------------------------------------------ b9: drainage gravel and pipes to a pond
gr = shell("grava", .87, 1.32, GRAVELM)
show(gr, S[9]["start"] + .9)
gravel_rain("guijarro", S[9]["start"] + .1, S[9]["start"] + .8, z_l + .3, GRAVELM, (.1, .18), 45, xs=(-9, 9), ys=(.1, 8))
pipes = []
for i, x in enumerate((-5, 0, 5)):
    p = prim("cylinder", f"dren{i}", (x, 10, -2.9), (.22, .22, 17), PIPEW, rot=(math.radians(90), 0, 0), vertices=10)
    cut(p, section)
    pop(p, S[9]["start"] + .5 + i * .15, dur=.15)
    pipes.append(p)
key(leach, "scale", F(S[9]["start"] + 1.2), (1, 1, 1))
key(leach, "scale", F(S[9]["end"]), (1, 1, .01))
show(leach, None, S[10]["start"])
pond = box("laguna_fondo", -6.5, 6.5, 15, 29, -1.45, -1.38, MEMBRANE)
pond.location.x = 25
pond_l = box("laguna", -6.2, 6.2, 15.3, 28.7, -1.4, -.3, LEACH, origin=(0, 0, -1.4))
pond_l.location.x = 25
key(pond_l, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(pond_l, "scale", F(S[9]["start"] + 1.6), (1, 1, .01))
key(pond_l, "scale", F(S[9]["end"]), (1, 1, 1))
link_pipe = prim("cylinder", "tubo_laguna", (16.5, 20, .25), (.25, .25, 2.5), PIPEW, rot=(0, math.radians(90), 0), vertices=10)
pop(link_pipe, S[9]["start"] + 1.0)
for i in range(10):
    d = prim("ico_sphere", f"flujo{i}", (14, 20, .25), (.15, .15, .15), LEACH, subdivisions=1)
    fa = F(S[9]["start"] + 1.3 + i * .12)
    key(d, "location", fa, (14, 20, .3), interp="LINEAR")
    key(d, "location", fa + 18, (19.5, 20, -.4), interp="LINEAR")
    for fc in fcurves(d.animation_data.action):
        fc.modifiers.new("CYCLES")
    show(d, S[9]["start"] + 1.3 + i * .12, S[10]["start"] + .5)
beat("grava", [S[9]["start"] + .1, S[9]["start"] + .8])
beat("tubos", S[9]["start"] + .5)
beat("drenaje", [S[9]["start"] + 1.2, S[9]["end"]])

# ------------------------------------------------------------------ b10: the first cell; b11: cells stacked
tk = truck("camion_basura", GREEN, GREEN)
bed = bpy.data.objects["camion_basura_caja"]
t_truck0, t_dump = S[10]["start"] + .05, S[10]["start"] + 1.0
aparecer(tk, t_truck0, (1.3, 1.3, 1.3))
key(tk, "location", F(t_truck0), (0, 46, 0))
key(tk, "location", F(t_dump), (0, 35.5, 0))
key(bed, "rotation_euler", F(t_dump), (0, 0, 0))
key(bed, "rotation_euler", F(t_dump + .5), (math.radians(32), 0, 0))
key(bed, "location", F(t_dump), tuple(bed.location))
key(bed, "location", F(t_dump + .5), (0, -1.0, 2.9))
unpop(tk, L("b10", 1)["start"])
for i in range(30):
    x, y = random.uniform(-7, 7), random.uniform(16, 26)
    b = bag(f"bolsaC{i}", (0, 31, 2), random.uniform(.45, .7))
    t = t_dump + .3 + i * .03
    aparecer(b, t)
    key(b, "location", F(t), (random.uniform(-1.5, 1.5), 31, 2.5))
    key(b, "location", F(t + .5), (x, y, CELL0 + random.uniform(0, .5)))
    unpop(b, t_dump + 1.6)
cells = []
for k in range(NCELL):
    za = CELL0 + k * (TRASH_H + COVER_H)
    tr = frustum(f"celda{k}", za, za + TRASH_H, ext(za), ext(za + TRASH_H), TRASH)
    cv = frustum(f"cubierta{k}", za + TRASH_H, za + TRASH_H + COVER_H, ext(za + TRASH_H), ext(za + TRASH_H + COVER_H), TOP)
    for ob in (tr, cv):
        cut(ob, section)
    cells.append((tr, cv))
c_fill, c_crush, c_cover = t_dump + 1.1, t_dump + 1.7, L("b10", 0)["end"] - .4
tr0, cv0 = cells[0]
key(tr0, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(tr0, "scale", F(c_fill), (1, 1, .01))
key(tr0, "scale", F(c_fill + .5), (1, 1, 1.35))
key(tr0, "scale", F(c_crush), (1, 1, 1.35))
key(tr0, "scale", F(c_cover - .2), (1, 1, 1))
show(tr0, c_fill)
crusher = roller("compactadora")
aparecer(crusher, c_crush - .1, (1.2, 1.2, 1.2))
for f in range(F(c_crush - .1), F(c_cover - .2) + 1, 2):
    k = (f - F(c_crush - .1)) / max(1, F(c_cover - .2) - F(c_crush - .1))
    zt = CELL0 + TRASH_H * lerp(1.35, 1.0, k)
    key(crusher, "location", f, (lerp(-6, 6, k), lerp(22, 2, k), zt + (.05 if (f // 2) % 2 else 0)), interp="LINEAR")
unpop(crusher, c_cover - .1, .05)
key(cv0, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(cv0, "scale", F(c_cover), (1, 1, .01))
key(cv0, "scale", F(c_cover + .4), (1, 1, 1))
show(cv0, c_cover)
cell_t = []
for k in range(1, NCELL):
    t = S[11]["start"] + .1 + (k - 1) * .55
    tr, cv = cells[k]
    for ob, a in ((tr, t), (cv, t + .3)):
        key(ob, "scale", 1, (1, 1, .01), interp="CONSTANT")
        key(ob, "scale", F(a), (1, 1, .01))
        key(ob, "scale", F(a + .25), (1, 1, 1))
        show(ob, a)
    cell_t.append(round(t, 3))
TOPZ = CELL0 + NCELL * (TRASH_H + COVER_H)
beat("camion", [t_truck0, t_dump])
beat("descarga", t_dump + .3)
beat("compactar", [c_crush - .1, c_cover - .2])
beat("cubrir", c_cover)
beat("celdas", cell_t)

# ------------------------------------------------------------------ b12: rain becomes leachate; b13: stormwater channels
rain("lluvia", 0, 10, 22, 26, S[12]["start"] - .1, S[13]["end"], 320)
for i in range(26):
    d = prim("ico_sphere", f"filtra{i}", (random.uniform(-7, 7), -.15, 0), (.09, .05, .14), LEACH, subdivisions=1)
    period = random.uniform(1.0, 1.4)
    fa = F(S[12]["start"] + .6 - random.uniform(0, period))
    key(d, "location", fa, (d.location.x, -.15, TOPZ - .2), interp="LINEAR")
    key(d, "location", fa + round(period * FPS), (d.location.x, -.15, CELL0 + .1), interp="LINEAR")
    for fc in fcurves(d.animation_data.action):
        fc.modifiers.new("CYCLES")
    show(d, S[12]["start"] + .6, S[13]["start"])
ch0, ch1 = S[13]["start"] + .2, S[13]["start"] + 1.8
for c in chan_cuts:
    key(c, "location", 1, (0, 0, 2))
    key(c, "location", F(ch0), (0, 0, 2))
    key(c, "location", F(ch1), (0, 0, 0))
for i, (a, b, c, d) in enumerate([(-16.7, -15.7, -11.8, 31.8), (15.7, 16.7, -11.8, 31.8), (-16.7, 16.7, -11.8, -10.8), (-16.7, 16.7, 30.8, 31.8)]):
    w = box(f"canal_agua{i}", a, b, c, d, -.75, -.45, WATER)
    cut(w, section)
    show(w, ch1 + .2)
beat("canales", [ch0, ch1])
beat("agua_canal", ch1 + .2)

# ------------------------------------------------------------------ b14: methane bubbles and a flash
gas_t0 = S[14]["start"] + .3
for i in range(40):
    x = random.uniform(-9, 9)
    bub = prim("ico_sphere", f"burbuja{i}", (x, -.2, 0), (.22, .1, .22), GASM, subdivisions=1)
    period = random.uniform(1.2, 1.8)
    fa = F(gas_t0 - random.uniform(0, period))
    key(bub, "location", fa, (x, -.2, CELL0 + .2), interp="LINEAR")
    key(bub, "location", fa + round(period * FPS), (x * .6, -.2, TOPZ + .6), interp="LINEAR")
    for fc in fcurves(bub.animation_data.action):
        fc.modifiers.new("CYCLES")
    show(bub, gas_t0, S[16]["start"])
flash = prim("ico_sphere", "destello", (0, 4, TOPZ + .5), (.1, .1, .1), FIRE, subdivisions=2)
t_flash = S[14]["end"] - 1.1
key(flash, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(flash, "scale", F(t_flash), (.1, .1, .1))
key(flash, "scale", F(t_flash + .25), (4, 4, 3))
key(flash, "scale", F(t_flash + .6), (0, 0, 0))
beat("burbujas", gas_t0)
beat("explosion", t_flash)

# ------------------------------------------------------------------ b15: gas wells, flare and generator
well_t = []
for i, (x, y) in enumerate([(-3, .05), (3, 6), (-3, 12), (3, 17), (0, 2)]):
    w = box(f"pozo_gas{i}", x - .25, x + .25, y - .25, y + .25, CELL0 + .3, TOPZ + 1.4, STEEL, origin=(0, 0, TOPZ + 1.4))
    w.location = (0, 0, TOPZ + 1.4)
    cut(w, section)
    t = S[15]["start"] + .2 + i * .3
    key(w, "scale", 1, (1, 1, 0), interp="CONSTANT")
    key(w, "scale", F(t), (1, 1, 0))
    key(w, "scale", F(t + .5), (1, 1, 1))
    show(w, t)
    well_t.append(round(t, 3))
    hp = prim("cylinder", f"manifold{i}", ((x + 26) / 2, (y + 4) / 2, TOPZ + 1.3), (.12, .12, math.hypot(26 - x, 4 - y) / 2), STEEL,
              rot=(0, math.radians(90), math.atan2(4 - y, 26 - x)), vertices=6)
    show(hp, t + .6)
stack = prim("cylinder", "quemador", (26, 4, 4), (.5, .5, 4), STEEL, vertices=10)
pop(stack, S[15]["start"] + 1.6)
flame = prim("cone", "llama", (26, 4, 9), (.8, .8, 1.3), FIRE, vertices=8)
t_fire = S[15]["start"] + 2.1
key(flame, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(flame, "scale", F(t_fire) - 1, (0, 0, 0), interp="CONSTANT")
for f in range(F(t_fire), F(UNTIL) + 1, 3):
    key(flame, "scale", f, (.8 + random.uniform(-.15, .15), .8 + random.uniform(-.15, .15), 1.3 + random.uniform(-.35, .35)), interp="LINEAR")
gen = box("generador", 30, 35, 7, 11, 0, 3, CONCRETE)
pop(gen, L("b15", 0)["end"] - 1.2, final=(1, 1, 1))
for j, (dx, dz, rot) in enumerate(((0, .5, 25), (.35, 0, -25), (0, -.5, 25))):
    bolt = prim("cube", f"rayo{j}", (32.5 + dx, 6.95, 1.6 + dz), (.12, .03, .4), BOLT, rot=(0, math.radians(rot), 0))
    pop(bolt, L("b15", 0)["end"] - .8 + j * .06, dur=.1)
for k in range(3):  # power line going away
    pole = prim("cylinder", f"poste_luz{k}", (40 + k * 14, 9, 4), (.15, .15, 4), WOOD, vertices=6)
    pop(pole, L("b15", 0)["end"] - .6 + k * .1)
beat("perforar_gas", well_t)
beat("quemador", t_fire)
beat("electricidad", L("b15", 0)["end"] - .8)

# ------------------------------------------------------------------ b16: monitoring wells down to the aquifer
mon_t = []
for i, (x, y) in enumerate([(19.5, .05), (-19.5, .05), (19.5, 31), (-19.5, 31)]):
    w = box(f"pozo_monitoreo{i}", x - .18, x + .18, y - .18, y + .18, -7.5, .9, PIPEW, origin=(0, 0, .9))
    w.location = (0, 0, .9)
    cut(w, section)
    capm = prim("cylinder", f"tapa_monitoreo{i}", (x, y, 1.0), (.3, .3, .12), BLUE, vertices=8)
    t = S[16]["start"] + .2 + i * .35
    key(w, "scale", 1, (1, 1, 0), interp="CONSTANT")
    key(w, "scale", F(t), (1, 1, 0))
    key(w, "scale", F(t + .9), (1, 1, 1))
    show(w, t)
    pop(capm, t + .9)
    mon_t.append(round(t, 3))
sample = prim("ico_sphere", "muestra", (19.5, -.25, -7.2), (.2, .1, .2), AQUA, subdivisions=1)
key(sample, "location", F(L("b16", 0)["end"] - .6), (19.5, -.25, -7.2))
key(sample, "location", F(L("b16", 1)["end"]), (19.5, -.25, .8))
show(sample, L("b16", 0)["end"] - .6, S[17]["start"])
beat("perforar_monitoreo", mon_t)

# ------------------------------------------------------------------ b17: cap and park
cap = []
z = TOPZ
for k, (name, th, mat) in enumerate((("tapa_arcilla", .3, CAPCLAY), ("tapa_tierra", .35, TOP), ("tapa_pasto", .14, GRASS))):
    e0 = E(0, 0)
    grow = .3 + k * .3
    ob = frustum(name, 0, z + th, (e0[0] + grow, e0[1] - grow, e0[2] + grow), tuple(v for v in (ext(TOPZ)[0] + grow * .5, ext(TOPZ)[1] - grow * .5, ext(TOPZ)[2] + grow * .5)), mat)
    t = S[17]["start"] + .2 + k * .55
    key(ob, "scale", 1, (1, 1, .01), interp="CONSTANT")
    key(ob, "scale", F(t), (1, 1, .01))
    key(ob, "scale", F(t + .4), (1, 1, 1))
    show(ob, t)
    cap.append(t)
    z += th
PARKZ = z
park_t = S[17]["start"] + 2.0
hx, y0, y1 = ext(TOPZ)
for i in range(14):
    x, y = random.uniform(-hx + .5, hx - .5), random.uniform(y0 + .5, y1 - .5)
    h = random.uniform(2.5, 4)
    tr = empty(f"parque_arbol{i}", (x, y, PARKZ))
    prim("cylinder", f"pa_tronco{i}", (0, 0, h * .2), (.2, .2, h * .2), TRUNK, parent=tr, vertices=6)
    prim("ico_sphere", f"pa_copa{i}", (0, 0, h * .6), (h * .3, h * .3, h * .28), random.choice((LEAF2, LEAF3)), parent=tr, subdivisions=1)
    pop(tr, park_t + i * .08, final=(1, 1, 1))
for i, (x, y) in enumerate([(-2, 3), (2.5, 9), (-1.5, 15)]):
    bn = empty(f"banca{i}", (x, y, PARKZ))
    prim("cube", f"banca_asiento{i}", (0, 0, .45), (.9, .25, .05), WOOD, parent=bn)
    prim("cube", f"banca_respaldo{i}", (0, .22, .75), (.9, .04, .25), WOOD, parent=bn)
    pop(bn, park_t + 1.0 + i * .12, final=(1, 1, 1))
path_p = box("sendero", -.8, .8, max(.2, y0 + .3), y1 - .3, PARKZ - .02, PARKZ + .02, BASE)
show(path_p, park_t + .2)
kite = empty("papalote", (2, 6, PARKZ + 7))
prim("cube", "papalote_tela", (0, 0, 0), (.6, .05, .8), RED, parent=kite, rot=(0, math.radians(45), 0))
aparecer(kite, park_t + 1.4)
for f in range(F(park_t + 1.4), F(UNTIL) + 1, 6):
    key(kite, "location", f, (2 + math.sin(f * .07) * 1.2, 6, PARKZ + 7 + math.sin(f * .11) * .6), interp="LINEAR")
beat("tapa", cap)
beat("parque", park_t)

# ------------------------------------------------------------------ camera
camara()
shot(0, S[2]["start"], (-31, -24, 9), (-33, -19, 8), (-40, 4, 1), (-40, 8, 1.5), False)
shot(S[2]["start"], S[3]["start"], (-36, -15, 1.2), (-37, -13.5, 0.4), (-40, 2, -3.6), (-40, 2, -4.2), True)
shot(S[3]["start"], S[4]["start"], (30, -30, 20), (27, -27, 17), (0, 10, 0), (0, 10, 0), False)
shot(S[4]["start"], S[5]["start"], (30, -26, 16), (26, -24, 13), (0, 10, -2), (0, 10, -2.5), True)
shot(S[5]["start"], S[6]["start"], (14, -9, 1.2), (12, -8.5, .6), (5, 9, -3.6), (5, 11, -3.6), True)
shot(S[6]["start"], S[7]["start"], (10.5, -5.5, -.8), (10, -5, -1.2), (6, 2, -3.2), (6, 2, -3.3), True)
shot(S[7]["start"], S[8]["start"], (14, -9, 1.2), (12, -8.5, .6), (5, 9, -3.4), (5, 11, -3.4), True)
shot(S[8]["start"], S[9]["start"], (0, -14, 1.0), (0, -13, .4), (0, 6, -3.0), (0, 6, -3.0), True)
shot(S[9]["start"], S[10]["start"], (34, -18, 11), (32, -16, 10), (12, 10, -2.5), (14, 12, -2), True)
shot(S[10]["start"], S[11]["start"], (26, -14, 12), (23, -12, 10), (0, 18, -1.5), (0, 16, -1), True)
shot(S[11]["start"], S[12]["start"], (0, -34, 3), (0, -38, 5), (0, 10, -.5), (0, 10, 0), True)
shot(S[12]["start"], S[13]["start"], (6, -27, 4), (4, -25, 3.5), (0, 8, 0), (0, 8, 0), True)
shot(S[13]["start"], S[14]["start"], (-32, -34, 28), (-28, -30, 25), (0, 12, 0), (0, 12, 0), False)
shot(S[14]["start"], S[15]["start"], (0, -26, 3), (0, -24, 3.2), (0, 8, 1), (0, 8, 1.2), True)
shot(S[15]["start"], S[16]["start"], (34, -24, 13), (31, -22, 12), (8, 10, 2.5), (10, 10, 3), True)
shot(S[16]["start"], S[17]["start"], (27, -17, 0), (26, -16, -.5), (18, 3, -3.6), (18, 3, -3.8), True)
shot(S[17]["start"], S[18]["start"], (32, -30, 16), (27, -26, 13), (0, 12, 2), (0, 12, 3), False)
shot(S[18]["start"], UNTIL + 1, (24, -22, 11), (60, -90, 60), (0, 12, 3), (0, 80, 0), False, lens=26)

terminar()
