"""Retaining wall episode (04-muro-de-contencion) on top of motor3d. A house sits at the foot of a hill (the hill
rises toward -x). The wall runs along y at x=0, so the cutaway at y=0 shows its profile: hill, wall, house.

    blender -b --python escena_muro.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar]"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motor3d import *  # noqa: E402,F401,F403

S = {k: SC[f"b{k}"] for k in range(1, 17)}
RUST = material("varilla", (.62, .30, .16), rough=.5)
FORM = material("cimbra", (.78, .56, .30))
WETC = material("concreto_mojado", (.42, .44, .46), rough=.15, alpha=.7)
ARROWR = material("flecha_roja", (1.0, .22, .15), emit=1.2)
ARROWY = material("flecha_amarilla", (1.0, .85, .15), emit=1.2)
ARROWB = material("flecha_azul", (.25, .60, 1.0), emit=1.2)
CORE = [material(f"nucleo{i}", c) for i, c in enumerate([(.40, .62, .22), (.47, .29, .14), (.62, .44, .26), (.72, .60, .40)])]
WY0, WY1 = -6.0, 26.0
section = seccion()


def zh(x):
    """Natural ground height of the hill at x (it rises toward -x)."""
    if x >= 6:
        return 0.0
    if x >= -6:
        return (6 - x) / 3
    if x >= -20:
        return 4 + (-6 - x) / 14 * .5
    if x >= -60:
        return 4.5 + (-20 - x) / 40 * 9.5
    return 14.0


def prism(name, poly, mat, y0=-40, y1=80):
    """Closed (x, z) outline extruded along y."""
    return sweep_path(name, [(x, z, "") for x, z in poly], [y0, y1], lambda s, o, z: (o, s, z), mat)


def arrow(name, a, b, mat, r=.12):
    """Glowing arrow from a to b, drawn in front of the cut face."""
    p = empty(name, a)
    d = [b[i] - a[i] for i in range(3)]
    ln = math.sqrt(sum(c * c for c in d))
    rot = (0, math.atan2(math.hypot(d[0], d[1]), d[2]), math.atan2(d[1], d[0]))
    p.rotation_euler = rot
    for ob in (prim("cylinder", f"{name}_asta", (0, 0, ln * .38), (r, r, ln * .38), mat, parent=p, vertices=8),
               prim("cone", f"{name}_punta", (0, 0, ln * .86), (r * 2.4, r * 2.4, ln * .14), mat, parent=p, vertices=8)):
        ob["frente_ok"] = True
    return p


# ------------------------------------------------------------------ ground and hill
cutA = cutter(box("corte_excavacion", -5, 1.5, -45, 85, -1.2, 25, None))
cutB = cutter(box("corte_talud", 1.5, 10.5, -45, 85, 0, 25, None))
ditch = cutter(sweep_path("corte_contracuneta", [(-14 + o, z, "") for o, z in ((-1.3, 1.2), (1.3, 1.2), (0, -.8))], [-45, 85],
                          lambda s, o, z: (o, s, z + zh(-14)), None))
key_b = box("dentellon", -1.0, -.4, WY0, WY1, -2.2, -1.2, CONCRETE, origin=(0, 0, -1.2))
cutA.location = cutB.location = (500, 0, 30)
ditch.location = (500, 0, 3)
layers = suelo([("pasto", 0, -.15, GRASS), ("tierra", -.15, -.65, TOP), ("subsuelo", -.65, -6, SUB), ("roca", -6, -40, ROCKL)],
               {"pasto": [(cutA, False)], "tierra": [(cutA, False)], "subsuelo": [(cutA, False), (key_b, False)]})
top = [(x, zh(x)) for x in (6, -6, -20, -60)] + [(-160, 14)]  # starts at the toe: no edge folding back on the base
hill = prism("cerro", top + [(-160, 0)], TOP)  # no repeated point: a zero-length edge breaks the booleans
skin = prism("cerro_pasto", [(x, z + .12) for x, z in top] + [(x, z) for x, z in reversed(top)], GRASS)
for ob in (hill, skin):
    for c in (cutA, cutB, ditch, section):
        cut(ob, c)


def libre(x, y):
    return (x > 26 or abs(y - 10) > 55) and x > -2


paisaje(libre, arboles=160, zona=(-160, 200, -120, 300), casas=[(30 + random.uniform(0, 60), random.uniform(-30, 80)) for _ in range(8)])
for i in range(40):  # trees on the hillside
    x, y = random.uniform(-90, -8), random.uniform(-30, 80)
    if abs(x + 14) < 3 or (y < 2 and x > -40):
        continue
    h = random.uniform(3, 5.5)
    t = empty(f"arbol_cerro{i}", (x, y, zh(x) + .05))
    prim("cylinder", f"ac_tronco{i}", (0, 0, h * .2), (.2, .2, h * .2), TRUNK, parent=t, vertices=6)
    prim("cone", f"ac_copa{i}", (0, 0, h * .7), (h * .32, h * .32, h * .45), random.choice((LEAF, LEAF2)), parent=t, vertices=7)
casa(90, 13.5, 10, w=7, d=8, h=4.5)
for i in range(2):
    persona(f"familia{i}", (10 + i * 1.2, 2.5, 0))

# ------------------------------------------------------------------ b1: rain, the slope creeps toward the house
b1 = S[1]
rain("lluviaA", 3, 10, 14, 16, 0, b1["end"] + .2, 280)
slide = prism("deslave", [(4.6, .45), (-1.2, 2.4), (.6, 2.8), (3.5, 1.6)], TOP, 2, 18)
key(slide, "location", F(b1["start"] + 1.0), (0, 0, 0))
key(slide, "location", F(b1["end"] - .3), (3.6, 0, -1.2))
show(slide, None, S[3]["start"])
beat("lluvia1", [0, b1["end"] + .2])
beat("deslave", b1["start"] + 1.0)

# ------------------------------------------------------------------ b2: soil study, the hill pushes
b2 = S[2]
rig = truck("perforadora", MACHINE, DARK)
rig.location = (-12, 6, zh(-12))
rig.rotation_euler.z = math.radians(90)
mast = prim("cube", "torre_perf", (0, -2.2, 3.6), (.15, .15, 2.4), STEEL, parent=rig)
aparecer(rig, b2["start"])
core = empty("nucleo", (-12.6, 2.2, zh(-12) - 4))
for i, m in enumerate(CORE):
    prim("cylinder", f"nucleo_capa{i}", (0, 0, 3.4 - i * .9), (.22, .22, .45), m, parent=core, vertices=10)
key(core, "location", F(b2["start"] + .6), (-12.6, 2.2, zh(-12) - 4))
key(core, "location", F(b2["start"] + 2.2), (-12.6, 2.2, zh(-12) + 1.5))
show(core, b2["start"] + .6, S[3]["start"])
push = []
for i, z in enumerate((1.0, 2.2, 3.2)):
    a = arrow(f"empuje{i}", (-4.5 + i * 1.6, -.4, z), (-1.2 + i * 1.6, -.4, z - .2), ARROWR)
    pop(a, b2["start"] + 2.4 + i * .15, final=(1, 1, 1))
    unpop(a, S[3]["start"])
unpop(rig, S[3]["start"])
beat("perforar", [b2["start"] + .2, b2["start"] + 2.2])
beat("flechas", b2["start"] + 2.4)

# ------------------------------------------------------------------ b3: dig, a thin wall topples
b3 = S[3]
dig0, dig1 = b3["start"] + .05, b3["start"] + .9
for c in (cutA, cutB):  # parked far away until the dig: a cutter that touches nothing can flip the cut faces
    key(c, "location", 1, (500, 0, 30), interp="CONSTANT")
    key(c, "location", F(dig0) - 1, (500, 0, 30), interp="CONSTANT")
    key(c, "location", F(dig0), (0, 0, 30))
    key(c, "location", F(dig1), (0, 0, 0))
thin = box("muro_delgado", -.25, 0, WY0, WY1, -1.2, 3.7, CONCRETE, origin=(0, 10, -1.2))
cut(thin, section)
test_soil = box("relleno_prueba", -5, -.25, WY0, WY1, -1.2, 3.7, TOP, origin=(-2.6, 10, -1.2))
cut(test_soil, section)
t_wall, t_soil, t_fall = dig1 + .1, dig1 + .5, b3["start"] + 2.0
pop(thin, t_wall, final=(1, 1, 1))
key(test_soil, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(test_soil, "scale", F(t_soil), (1, 1, .01))
key(test_soil, "scale", F(t_soil + .5), (1, 1, 1))
key(thin, "rotation_euler", F(t_fall), (0, 0, 0))
key(thin, "rotation_euler", F(t_fall + .7), (0, math.radians(78), 0))
key(test_soil, "location", F(t_fall), (-2.6, 10, -1.2))
key(test_soil, "location", F(t_fall + .9), (-.4, 10, -1.2))
key(test_soil, "scale", F(t_fall), (1, 1, 1))
key(test_soil, "scale", F(t_fall + .9), (1.15, 1, .55))
show(thin, t_wall, S[4]["start"])
show(test_soil, t_soil, S[4]["start"])
beat("excavar", [dig0, dig1])
beat("muro_cae", t_fall + .6)

# ------------------------------------------------------------------ b4-b6: footing, sliding, shear key
b4, b5, b6 = S[4], S[5], S[6]
wall = empty("muro", (0, 0, 0))
foot = box("zapata", -4, 1.2, WY0, WY1, -1.2, -.4, CONCRETE)
stem = box("pantalla", -.4, 0, WY0, WY1, -.4, 4.2, CONCRETE)
soil2 = box("relleno_talon", -5, -.4, WY0, WY1, -.4, 3.7, TOP)
soil2b = box("relleno_talon_b", -5, -4, WY0, WY1, -1.2, -.4, TOP)
for ob in (foot, stem, soil2, soil2b):
    ob.parent = wall
    cut(ob, section)
for ob in (foot, stem):
    show(ob, b4["start"] + .1, S[7]["start"])
for ob in (soil2, soil2b):
    show(ob, b4["start"] + 1.0, S[7]["start"])
key(soil2, "location", F(b4["start"] + 1.0), (0, 0, 4))
key(soil2, "location", F(b4["start"] + 1.5), (0, 0, 0))
for i, x in enumerate((-3.4, -2.4, -1.4)):
    a = arrow(f"peso{i}", (x, -.4, 3.4), (x, -.4, -.2), ARROWY)
    pop(a, L("b4", 0)["start"] + 2.0 + i * .12, final=(1, 1, 1))
    unpop(a, b5["start"])
s0, s1 = b5["start"] + .8, b5["end"] - .5
key(wall, "location", F(s0), (0, 0, 0))
key(wall, "location", F(s1), (1.4, 0, 0))
key(wall, "location", F(b6["start"]) - 1, (1.4, 0, 0))
key(wall, "location", F(b6["start"]), (0, 0, 0), interp="CONSTANT")
for i, z in enumerate((.6, 1.8, 3.0)):
    a = arrow(f"empuje_b{i}", (-4.6, -.4, z), (-1.0, -.4, z), ARROWR)
    pop(a, b5["start"] + .3 + i * .1, final=(1, 1, 1))
    key(a, "location", F(s0), (-4.6, -.4, z))
    key(a, "location", F(s1), (-3.2, -.4, z))
    key(a, "location", F(b6["start"]), (-4.6, -.4, z), interp="CONSTANT")
    unpop(a, S[7]["start"])
dust = empty("polvo_desliz", (1.4, 1, -1.0))
vapor(dust, s0, (-.5, .5), (0, 18), count=8, mat=DUST)
show(dust, s0, s1 + .3)
k0 = b6["start"] + .6
key(key_b, "scale", 1, (1, 1, .001), interp="CONSTANT")
key(key_b, "scale", F(k0), (1, 1, .001))
key(key_b, "scale", F(k0 + .9), (1, 1, 1))
cut(key_b, section)
show(key_b, k0, S[7]["start"])
key(wall, "location", F(L("b6", 1)["start"]), (0, 0, 0))
key(wall, "location", F(L("b6", 1)["start"]) + 3, (.06, 0, 0))
key(wall, "location", F(L("b6", 1)["start"]) + 6, (0, 0, 0))
beat("zapata", b4["start"] + .1)
beat("relleno", b4["start"] + 1.0)
beat("desliza", [s0, s1])
beat("dentellon", k0)

# ------------------------------------------------------------------ b7: rebar
b7 = S[7]
rebar_t = []
ys = [.4 + .6 * k for k in range(43)]
for k, y in enumerate(ys):
    t = b7["start"] + .2 + k * (4.2 / len(ys))
    for x in (-.32, -.08):
        bar = box(f"varilla_v{k}{x}", x - .03, x + .03, y - .03, y + .03, -1.0, 4.0, RUST)
        pop(bar, t, dur=.1, final=(1, 1, 1))
    bar = box(f"varilla_z{k}", -3.8, 1.0, y - .03, y + .03, -.95, -.9, RUST)
    pop(bar, t + .05, dur=.1, final=(1, 1, 1))
    if k % 6 == 0:
        rebar_t.append(round(t, 3))
for j, (x, z) in enumerate([(-.32, .5), (-.08, .5), (-.32, 2.0), (-.08, 2.0), (-.32, 3.5), (-.08, 3.5), (-2, -.92), (0, -.92)]):
    bar = box(f"varilla_l{j}", x - .03, x + .03, .05, WY1, z - .03, z + .03, RUST)
    pop(bar, b7["start"] + 1.0 + j * .1, dur=.1, final=(1, 1, 1))
beat("varillas", rebar_t)

# ------------------------------------------------------------------ b8: forms, pour, vibrate
b8 = S[8]
forms = [box("cimbra_frente", 0, .08, .05, WY1, -.4, 4.25, FORM), box("cimbra_atras", -.48, -.4, .05, WY1, -.4, 4.25, FORM),
         box("cimbra_zapata1", 1.2, 1.28, .05, WY1, -1.2, -.4, FORM), box("cimbra_zapata2", -4.08, -4, .05, WY1, -1.2, -.4, FORM)]
for i, ob in enumerate(forms):
    pop(ob, b8["start"] + .1 + i * .15, final=(1, 1, 1))
    unpop(ob, S[9]["start"] + .3)
foot2 = box("zapata_real", -4, 1.2, WY0, WY1, -1.2, -.4, CONCRETE, origin=(0, 0, -1.2))
stem2 = box("pantalla_real", -.4, 0, WY0, WY1, -.4, 4.2, CONCRETE, origin=(0, 0, -.4))
key2 = box("dentellon_real", -1.0, -.4, WY0, WY1, -2.2, -1.2, CONCRETE)
cut(layers[2], key2)
c0, c1, c2 = b8["start"] + .8, b8["start"] + 1.6, b8["end"] - .8
for ob, a, b in ((foot2, c0, c1), (stem2, c1, c2)):
    cut(ob, section)
    key(ob, "scale", 1, (1, 1, .001), interp="CONSTANT")
    key(ob, "scale", F(a), (1, 1, .001))
    key(ob, "scale", F(b), (1, 1, 1))
    show(ob, a)
cut(key2, section)
show(key2, c0)
bucket = empty("cubeta", (-.2, 2, 7))
prim("cone", "cubeta_cono", (0, 0, 0), (.8, .8, .9), STEEL, parent=bucket, rot=(math.pi, 0, 0), vertices=10)
aparecer(bucket, c0 - .2)
for f in range(F(c0 - .2), F(c2) + 1, 3):
    u = (f - F(c0 - .2)) / max(1, F(c2) - F(c0 - .2))
    key(bucket, "location", f, (-.2, lerp(2, 24, u), 6.5), interp="LINEAR")
unpop(bucket, c2 + .1)
for i in range(16):
    d = prim("ico_sphere", f"colado{i}", (0, 0, 0), (.16, .16, .16), CONCRETE, parent=bucket, subdivisions=1)
    fa = F(c0 - random.uniform(0, .45))
    key(d, "location", fa, (random.uniform(-.15, .15), random.uniform(-.2, .2), -.6), interp="LINEAR")
    key(d, "location", fa + 13, (random.uniform(-.15, .15), random.uniform(-.2, .2), -6.0), interp="LINEAR")
    for fc in fcurves(d.animation_data.action):
        fc.modifiers.new("CYCLES")
vib = prim("cylinder", "vibrador", (-.2, 3, 4.6), (.06, .06, 1.2), STEEL, vertices=8)
aparecer(vib, c1, tuple(vib.scale))
for f in range(F(c1), F(b8["end"]) + 1, 2):
    u = (f - F(c1)) / max(1, F(b8["end"]) - F(c1))
    key(vib, "location", f, (-.2 + (.04 if (f // 2) % 2 else -.04), lerp(3, 20, u), 4.6), interp="LINEAR")
unpop(vib, b8["end"])
beat("cimbra", [b8["start"] + .1, b8["start"] + .6])
beat("colar", [c0, c2])
beat("vibrar", [c1, b8["end"]])

# ------------------------------------------------------------------ b9: curing
b9 = S[9]
wet = [box("mojado_frente", .0, .02, .05, WY1, -.4, 4.2, WETC), box("mojado_atras", -.42, -.4, .05, WY1, -.4, 4.2, WETC)]
for ob in wet:
    show(ob, b9["start"] + .6, S[10]["start"] + .5)
spr = empty("manguera_curado", (-.2, 2, 5.0))
rociador(spr, 0, b9["start"] + .3, count=26, mat=WATER, ancho=.8)
aparecer(spr, b9["start"] + .3)
for f in range(F(b9["start"] + .3), F(b9["end"]) + 1, 3):
    u = (f - F(b9["start"] + .3)) / max(1, F(b9["end"]) - F(b9["start"] + .3))
    key(spr, "location", f, (-.2, lerp(2, 22, u), 5.0), interp="LINEAR")
unpop(spr, b9["end"])
beat("curado", [b9["start"] + .3, b9["end"]])

# ------------------------------------------------------------------ b10-b11: water behind the wall, weep holes
b10, b11 = S[10], S[11]
rain("lluviaB", -2, 10, 6, 14, b10["start"], b11["start"] + .5, 220)
water = box("agua_atras", -5, -.4, WY0, WY1, -.4, 2.8, WATER, origin=(0, 0, -.4))
cut(water, section)
show(water, b10["start"] + .3, S[12]["start"] + .6)
key(water, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(water, "scale", F(b10["start"] + .3), (1, 1, .01))
key(water, "scale", F(b10["end"] - .4), (1, 1, 1))
for i, z in enumerate((.3, 1.2, 2.1)):
    a = arrow(f"empuje_agua{i}", (-3.6, -.4, z), (-.7, -.4, z), ARROWB)
    pop(a, b10["start"] + 2.0 + i * .12, final=(1, 1, 1))
    unpop(a, L("b11", 0)["start"] + 1.2)
holes_t = b11["start"] + .3
for i, y in enumerate([0.0] + [2.2 + 2.4 * k for k in range(10)]):
    hp = prim("cylinder", f"lloradero{i}", (-.2, y, .05), (.1, .1, .3), PIPEW if "PIPEW" in globals() else WHITE, rot=(0, math.radians(90), 0), vertices=10)
    cut(hp, section)
    pop(hp, holes_t + i * .06, dur=.1)
    if i:
        for k in range(5):
            d = prim("ico_sphere", f"chorrito{i}_{k}", (.1, y, .05), (.07, .07, .07), WATER, subdivisions=1)
            fa = F(holes_t + .5 - random.uniform(0, .5))
            key(d, "location", fa, (.15, y, .05), interp="LINEAR")
            key(d, "location", fa + 15, (1.4, y, -.0), interp="LINEAR")
            for fc in fcurves(d.animation_data.action):
                fc.modifiers.new("CYCLES")
            show(d, holes_t + .5, S[13]["start"])
key(water, "scale", F(holes_t + .5), (1, 1, 1))
key(water, "scale", F(b11["end"]), (1, 1, .15))
beat("lluvia2", [b10["start"], b11["start"] + .5])
beat("agua_sube", b10["start"] + .3)
beat("lloraderos", holes_t)
beat("chorritos", [holes_t + .5, S[13]["start"]])

# ------------------------------------------------------------------ b12: gravel drain and perforated pipe
b12 = S[12]
gravel = box("grava_dren", -1.2, -.4, WY0, WY1, -.4, 3.7, GRAVEL if "GRAVEL" in globals() else SUBBASE, origin=(0, 0, -.4))
cut(gravel, section)
key(gravel, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(gravel, "scale", F(b12["start"] + .3), (1, 1, .01))
key(gravel, "scale", F(b12["start"] + 1.6), (1, 1, 1))
show(gravel, b12["start"] + .3)
gravel_rain("piedrita", b12["start"] + .2, b12["start"] + 1.3, 1.5, SUBBASE, (.08, .14), 40, xs=(-1.15, -.45), ys=(.2, 10))
dpipe = prim("cylinder", "tubo_dren", (-.8, 10, -.2), (.16, .16, 16), WHITE, rot=(math.radians(90), 0, 0), vertices=12)
cut(dpipe, section)
pop(dpipe, b12["start"] + 1.7, dur=.15)
for i in range(10):
    d = prim("ico_sphere", f"escurre{i}", (-.8, -.15, 3), (.08, .05, .1), WATER, subdivisions=1)
    d["frente_ok"] = True
    fa = F(b12["start"] + 2.1 - random.uniform(0, .9))
    key(d, "location", fa, (random.uniform(-1.1, -.5), -.15, 3.4), interp="LINEAR")
    key(d, "location", fa + 27, (-.8, -.15, -.15), interp="LINEAR")
    for fc in fcurves(d.animation_data.action):
        fc.modifiers.new("CYCLES")
    show(d, b12["start"] + 2.1, S[13]["start"] + .5)
beat("grava", [b12["start"] + .2, b12["start"] + 1.3])
beat("tubo", b12["start"] + 1.7)
beat("escurre", b12["start"] + 2.1)

# ------------------------------------------------------------------ b13: backfill in compacted layers
b13 = S[13]
fill_t = []
fill_layers = [box("relleno_fondo", -5, -4, WY0, WY1, -1.2, -.4, TOP)]
zs = [-.4, .62, 1.65, 2.67, 3.7]
for i in range(4):
    fill_layers.append(box(f"relleno{i}", -5, -1.2, WY0, WY1, zs[i], zs[i + 1], TOP, origin=(0, 0, zs[i])))
for i, ob in enumerate(fill_layers):
    cut(ob, section)
    t = b13["start"] + .1 + max(0, i - 1) * .7
    key(ob, "scale", 1, (1, 1, .01), interp="CONSTANT")
    key(ob, "scale", F(t), (1, 1, .01))
    key(ob, "scale", F(t + .35), (1, 1, 1))
    show(ob, t)
    fill_t.append(round(t, 3))
plate = compactadora("compactadora")
aparecer(plate, b13["start"] + .5, (1.6, 1.6, 1.6))
for f in range(F(b13["start"] + .5), F(b13["end"]) + 1, 2):
    u = (f - F(b13["start"] + .5)) / max(1, F(b13["end"]) - F(b13["start"] + .5))
    lvl = min(3, int(u * 4))
    key(plate, "location", f, (lerp(-4.4, -1.8, (u * 4) % 1), 2.6, zs[lvl + 1] + (.06 if (f // 2) % 2 else 0)), interp="LINEAR")
unpop(plate, b13["end"])
for nm, x0, x1, z0, z1 in (("relleno_frente", 0, 1.5, -.4, 0), ("relleno_frente_b", 1.2, 1.5, -1.2, -.4)):
    ob = box(nm, x0, x1, WY0, WY1, z0, z1, TOP)
    cut(ob, section)
    show(ob, b13["end"] - .3)
beat("rellenar", fill_t)
beat("compactar", [b13["start"] + .5, b13["end"]])

# ------------------------------------------------------------------ b14: interceptor ditch up the hill
b14 = S[14]
key(ditch, "location", 1, (500, 0, 3), interp="CONSTANT")
key(ditch, "location", F(b14["start"] + .2) - 1, (500, 0, 3), interp="CONSTANT")
key(ditch, "location", F(b14["start"] + .2), (0, 0, 3))
key(ditch, "location", F(b14["start"] + 1.4), (0, 0, 0))
rain("lluviaC", -14, 10, 10, 14, b14["start"] + 1.2, b14["end"] + .3, 220)
dw = prism("agua_contracuneta", [(-14.35, zh(-14) - .55), (-13.65, zh(-14) - .55), (-13.75, zh(-14) - .35), (-14.25, zh(-14) - .35)], WATER, .05, 80)
show(dw, b14["start"] + 1.6)
dz = dozer("excavadora_cerro")
dz.location = (-14, -2, zh(-14))
aparecer(dz, b14["start"] + .1, (1.1, 1.1, 1.1))
key(dz, "location", F(b14["start"] + .1), (-14, 1, zh(-14)))
key(dz, "location", F(b14["start"] + 1.5), (-14, 18, zh(-14)))
unpop(dz, b14["start"] + 1.6)
beat("cuneta", [b14["start"] + .2, b14["start"] + 1.4])
beat("lluvia3", [b14["start"] + 1.2, b14["end"] + .3])

# ------------------------------------------------------------------ b15: plants and roots
b15 = S[15]
lawn = box("pasto_relleno", -5, -.4, WY0, WY1, 3.7, 3.82, GRASS)
cut(lawn, section)
show(lawn, b15["start"] + .1)
plant_t = []
for i in range(30):
    x = random.uniform(-19, -1)
    y = random.uniform(1.5, 24) if i > 5 else random.uniform(1.1, 1.4)
    z = 3.82 if x > -5 else zh(x) + .1
    s = random.uniform(.5, 1.0)
    pl = prim("ico_sphere", f"planta{i}", (x, y, z + s * .5), (s, s, s * .8), random.choice((LEAF2, LEAF3)), subdivisions=1)
    t = b15["start"] + .2 + i * .06
    pop(pl, t, dur=.15)
    if i <= 5:
        for k in range(3):
            rt = prim("cylinder", f"raiz{i}_{k}", (x + random.uniform(-.3, .3), -.12, z - .7), (.03, .03, .7), TRUNK,
                      rot=(0, random.uniform(-.4, .4), 0), vertices=5)
            rt["frente_ok"] = True
            pop(rt, t + .3 + k * .1, dur=.2)
    if i % 6 == 0:
        plant_t.append(round(t, 3))
beat("plantas", plant_t)

# ------------------------------------------------------------------ camera
camara()
shot(0, S[2]["start"], (30, -22, 12), (27, -19, 10), (0, 10, 3), (0, 10, 2.5), False)
shot(S[2]["start"], S[3]["start"], (-3, -17, 7), (-4, -15.5, 6.5), (-9, 6, 2.5), (-9, 6, 2.5), True)
shot(S[3]["start"], S[4]["start"], (3, -17, 3.5), (2.5, -16, 3.3), (-1, 6, 1), (-1, 6, 1), True)
shot(S[4]["start"], S[6]["start"], (2.5, -16, 3.3), (2, -15, 3.1), (-1, 6, 1), (-.5, 6, 1), True)
shot(S[6]["start"], S[7]["start"], (1.5, -12, 1.6), (1.2, -11, 1.4), (-1, 6, -.8), (-1, 6, -.9), True)
shot(S[7]["start"], S[8]["start"], (8, -9, 7), (7, -8, 6.5), (-1, 8, 1), (-1, 10, 1), True)
shot(S[8]["start"], S[9]["start"], (9, -8, 6), (8, -7, 5.5), (-1, 10, 1.5), (-1, 11, 1.5), True)
shot(S[9]["start"], S[10]["start"], (7, -6, 4), (6.5, -5.5, 3.8), (-.5, 8, 2), (-.5, 9, 2), True)
shot(S[10]["start"], S[11]["start"], (2, -16, 3.5), (1.8, -15, 3.3), (-2, 6, 1.2), (-2, 6, 1.2), True)
shot(S[11]["start"], S[12]["start"], (5, -10, 2), (4.5, -9.5, 1.8), (-1, 5, .5), (-1, 5, .5), True)
shot(S[12]["start"], S[13]["start"], (2, -14, 3), (1.8, -13, 2.8), (-1.5, 5, 1), (-1.5, 5, 1), True)
shot(S[13]["start"], S[14]["start"], (1, -17, 4), (.5, -16, 3.8), (-2, 6, 1.5), (-2, 6, 1.5), True)
shot(S[14]["start"], S[15]["start"], (6, -20, 15), (5, -18, 14), (-12, 10, 4), (-12, 10, 4), True)
shot(S[15]["start"], S[16]["start"], (8, -16, 8), (7, -15, 7.5), (-6, 8, 3), (-6, 8, 3), True)
shot(S[16]["start"], UNTIL + 1, (24, -18, 9), (70, -70, 45), (0, 10, 2), (-10, 20, 4), False, lens=26)

terminar()
