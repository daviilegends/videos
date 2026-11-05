"""Ice rink episode (03-pista-de-hielo) on top of motor3d. A rink is built in a hot town with palm trees:
sand with heating pipes, insulation, brine pipes in a concrete slab, a chiller, painted ice, boards, dehumidifiers
and a resurfacer. The cutaway at y=0 slices the floor so the layers show in front.

    blender -b --python escena_hielo.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar]"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motor3d import *  # noqa: E402,F401,F403

S = {k: SC[f"b{k}"] for k in range(1, 17)}
DRY = material("pasto_seco", (.62, .66, .30))
SAND = material("arena", (.86, .74, .48))
PINK = material("aislante", (.98, .62, .70))
HEAT = material("calor", (1.0, .35, .12), emit=1.5)
BRINEM = material("salmuera", (.30, .75, 1.0), emit=.4)
ICE = material("hielo", (.80, .92, 1.0), rough=.05, alpha=.55)
FROST = material("escarcha", (.92, .97, 1.0), emit=.2)
FROSTSOIL = material("suelo_congelado", (.78, .88, .96))
PAINTW = material("pintura", (.97, .98, 1.0))
LINER = material("linea_roja", (.85, .12, .12))
LINEB = material("linea_azul", (.12, .30, .85))
MUDDY = material("charco_lodo", (.42, .32, .18), rough=.1, alpha=.85)
GLASSP = material("vidrio_valla", (.80, .92, 1.0), rough=.05, alpha=.25)
WET = material("pelicula", (.75, .90, 1.0), rough=.0, alpha=.35)
PALM = material("palma", (.22, .55, .20))
MERCURY = material("mercurio", (.95, .10, .10), emit=.8)
section = seccion()
X, Y0, Y1 = 14.2, -4.2, 24.2        # inner edge of the boards


# ------------------------------------------------------------------ ground, pit and a hot town around it
pit = cutter(box("corte_pista", -15, 15, -5, 25, -1.6, 3, None))
pit.location.z = 4
frost_lens = prim("ico_sphere", "lente_hielo", (0, 3, -2.5), (.01, .01, .01), FROSTSOIL, subdivisions=2)
cut(frost_lens, section)
suelo([("pasto", 0, -.15, DRY), ("tierra", -.15, -.65, TOP), ("subsuelo", -.65, -6, SUB), ("roca", -6, -40, ROCKL)],
      {"pasto": [(pit, False)], "tierra": [(pit, False)], "subsuelo": [(pit, False), (frost_lens, False)]})


def palm(i, x, y):
    h = random.uniform(6, 9)
    lean = random.uniform(-.15, .15)
    prim("cylinder", f"palma_tronco{i}", (x + lean * h / 2, y, h / 2), (.25, .25, h / 2), TRUNK, rot=(0, lean, 0), vertices=6)
    for k in range(7):
        a = k * 2 * math.pi / 7
        prim("cube", f"palma_hoja{i}_{k}", (x + lean * h + math.cos(a) * 1.4, y + math.sin(a) * 1.4, h - .2), (1.6, .35, .05), PALM,
             rot=(0, math.radians(25), a))


def libre(x, y):
    return not (-30 < x < 40 and -16 < y < 42) and not (y < 2 and abs(x) < 60)


paisaje(libre, arboles=120, casas=[(random.choice((-1, 1)) * random.uniform(45, 90), random.uniform(-10, 90)) for _ in range(16)])
n = 0
while n < 70:
    x, y = random.uniform(-120, 160), random.uniform(-60, 200)
    if libre(x, y):
        palm(n, x, y)
        n += 1
sun.data.energy = 4.2

# ------------------------------------------------------------------ b1: it never gets cold
th = empty("termometro", (-16, 3, 0))
prim("cylinder", "termo_poste", (0, 0, 1.5), (.12, .12, 1.5), STEEL, parent=th, vertices=8)
prim("cylinder", "termo_tubo", (0, 0, 4.2), (.35, .35, 1.4), WHITE, parent=th, vertices=10)
prim("ico_sphere", "termo_bulbo", (0, -.05, 2.9), (.55, .55, .55), MERCURY, parent=th, subdivisions=2)
merc = prim("cube", "termo_rojo", (0, -.3, 3.0), (.16, .05, 1.0), MERCURY, parent=th)
pop(th, S[1]["start"] + .2, final=(1.4, 1.4, 1.4))
key(merc, "scale", F(S[1]["start"] + .6), (.16, .05, .05))
key(merc, "location", F(S[1]["start"] + .6), (0, -.3, 3.0))
key(merc, "scale", F(S[1]["end"] - .3), (.16, .05, 1.25))
key(merc, "location", F(S[1]["end"] - .3), (0, -.3, 4.25))
show(th, None, S[3]["start"])
beat("termometro", S[1]["start"] + .6)

# ------------------------------------------------------------------ b2: water on the ground makes a warm puddle
hose_t = S[2]["start"] + .2
nozzle = (0, 6, 1.6)
hose = prim("cylinder", "manguera", (-3, 4, .8), (.08, .08, 3.4), GREEN_P, rot=(math.radians(-60), 0, math.radians(-50)), vertices=6)
pop(hose, hose_t, dur=.15)
for i in range(30):
    d = prim("ico_sphere", f"chorro{i}", nozzle, (.08, .08, .12), WATER, subdivisions=1)
    period = .45
    fa = F(hose_t + .2 - random.uniform(0, period))
    key(d, "location", fa, (random.uniform(-.1, .1), 6.2, 1.5), interp="LINEAR")
    key(d, "location", fa + round(period * FPS), (random.uniform(-.8, .8), 9 + random.uniform(-.6, .6), 0), interp="LINEAR")
    for fc in fcurves(d.animation_data.action):
        fc.modifiers.new("CYCLES")
    show(d, hose_t + .2, S[2]["end"] - .6)
puddle = prim("cylinder", "charco", (0, 10, .02), (.01, .01, .02), MUDDY, vertices=16)
key(puddle, "scale", F(hose_t + .3), (.01, .01, .02))
key(puddle, "scale", F(S[2]["end"] - .4), (4.5, 3.6, .02))
show(puddle, hose_t + .3, S[3]["start"] + .3)
show(hose, None, S[3]["start"])
wisp = empty("vapor_charco", (0, 10, 0))
vapor(wisp, hose_t + 1.5, (-3, 3), (-2, 2), count=8)
show(wisp, hose_t + 1.5, S[3]["start"])
beat("agua", [hose_t + .2, S[2]["end"] - .6])

# ------------------------------------------------------------------ b3: level the ground, sand bed
b3 = S[3]
d0, d1 = b3["start"] + .2, b3["start"] + 2.6
key(pit, "location", 1, (0, 0, 4), interp="CONSTANT")
key(pit, "location", F(d0), (0, 0, 4))
key(pit, "location", F(d1), (0, 0, 0))
dz = dozer("topadora")
aparecer(dz, d0, (1.2, 1.2, 1.2))
for f in range(F(d0), F(d1) + 1, 3):
    k = (f - F(d0)) / (F(d1) - F(d0))
    key(dz, "location", f, (lerp(-8, 8, k), 3 + 16 * k, -1.6 + 1.6 * (1 - k)), interp="LINEAR")
unpop(dz, d1 + .05, .05)
sand = box("arena", -15, 15, -5, 25, -1.6, -1.2, SAND, origin=(0, 0, -1.6))
cut(sand, section)
key(sand, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(sand, "scale", F(d1), (1, 1, .01))
key(sand, "scale", F(b3["end"] - .2), (1, 1, 1))
show(sand, d1)
gravel_rain("granos", d1, b3["end"] - .6, -1.3, SAND, (.08, .14), 40, xs=(-12, 12), ys=(.3, 20))
beat("nivelar", [d0, d1])
beat("arena", [d1, b3["end"] - .2])

# ------------------------------------------------------------------ b4: frozen soil heaves and cracks a test floor
b4 = S[4]
test = losa("losa_prueba", -15, 15, -5, 25, -1.2, -.85, CONCRETE, lambda x, y: 1.1 * math.exp(-(x * x) / 30 - ((y - 3) ** 2) / 40), nx=21, ny=21)
cut(test, section)
t_cold, t_heave = b4["start"] + .3, b4["start"] + 2.8
show(test, b4["start"], S[5]["start"])
frost = box("escarcha_prueba", -15, 15, -5, 25, -.85, -.82, FROST)
cut(frost, section)
show(frost, t_cold, t_heave - .2)
key(frost_lens, "scale", F(t_cold + .6), (.01, .01, .01))
key(frost_lens, "scale", F(t_heave + .8), (8, 7, .8))
key(frost_lens, "scale", F(S[5]["start"] - .05), (8, 7, .8))
key(frost_lens, "scale", F(S[5]["start"]), (.01, .01, .01), interp="CONSTANT")
shape_key(test, "deform", F(t_heave), 0)
shape_key(test, "deform", F(b4["end"] - .4), 1)
for i, (x, y, r) in enumerate([(-3, 2, 30), (2.5, 4, -40), (-1, 6, 70), (4, 1.5, 10), (0, 1.0, -25)]):
    z = -.85 + 1.1 * math.exp(-(x * x) / 30 - ((y - 3) ** 2) / 40) + .02
    cr = prim("cube", f"grieta{i}", (x, y, z), (1.6, .07, .03), CRACKM, rot=(0, 0, math.radians(r)))
    pop(cr, b4["end"] - .9 + i * .1, dur=.1)
    show(cr, None, S[5]["start"])
beat("frio", t_cold)
beat("hinchar", t_heave)
beat("grietas", b4["end"] - .9)

# ------------------------------------------------------------------ b5: subsoil heating pipes
b5 = S[5]
heat_t = []
for i, x in enumerate([-13 + 2 * k for k in range(14)]):
    p = prim("cylinder", f"calefaccion{i}", (x, 10, -1.07), (.13, .13, 15), HEAT, rot=(math.radians(90), 0, 0), vertices=10)
    cut(p, section)
    t = b5["start"] + .2 + i * .17
    pop(p, t, dur=.12)
    heat_t.append(round(t, 3))
beat("calefaccion", heat_t)

# ------------------------------------------------------------------ b6: insulation boards
b6 = S[6]
ins_t = []
for i in range(12):
    x0 = -15 + i * 2.5
    bd = box(f"aislante{i}", x0 + .03, x0 + 2.47, -5, 25, -1.2, -.95, PINK, origin=(x0 + 1.25, 10, -1.2))
    cut(bd, section)
    t = b6["start"] + .2 + i * .26
    pop(bd, t, dur=.15, final=(1, 1, 1))
    ins_t.append(round(t, 3))
beat("aislante", ins_t)

# ------------------------------------------------------------------ b7: brine pipes
b7 = S[7]
brine_t = []
xs = [-14.5 + .6 * k for k in range(49)]
for i, x in enumerate(xs):
    p = prim("cylinder", f"salmuera{i}", (x, 10, -.78), (.09, .09, 14.6), BRINEM, rot=(math.radians(90), 0, 0), vertices=8)
    cut(p, section)
    t = b7["start"] + .15 + i * (2.2 / len(xs))
    pop(p, t, dur=.1)
    if i % 4 == 0:
        brine_t.append(round(t, 3))
headers = []
for j, x0 in enumerate((-14.6, .2)):
    hd = box(f"cabezal{j}", x0, x0 + 14.4, 24.6, 25.0, -.85, -.6, BRINEM)
    pop(hd, L("b7", 1)["start"] + j * .2, final=(1, 1, 1))
    headers.append(hd)
beat("salmuera", brine_t)

# ------------------------------------------------------------------ b8: concrete slab poured from a mixer truck
b8 = S[8]
mixer = truck("revolvedora", WALLS[2], STEEL)
drum = prim("cylinder", "olla", (0, -1.0, 2.6), (1.1, 1.1, 2.2), ORANGE, parent=mixer, rot=(math.radians(90), 0, 0), vertices=12)
chute = prim("cube", "canaleta", (0, -4.6, 1.8), (.25, 1.2, .08), STEEL, parent=mixer, rot=(math.radians(-25), 0, 0))
mixer.location = (17, 16, 0)
mixer.rotation_euler = (0, 0, math.radians(-90))
aparecer(mixer, b8["start"], (1.2, 1.2, 1.2))
for f in range(F(b8["start"]), F(S[9]["start"]) + 1, 3):
    key(drum, "rotation_euler", f, (math.radians(90), 0, f * .25), interp="LINEAR")
unpop(mixer, S[9]["start"] + .05, .05)
slab = box("losa", -15, 15, -5, 25, -.95, -.5, CONCRETE, origin=(0, 0, -.95))
cut(slab, section)
key(slab, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(slab, "scale", F(b8["start"] + .3), (1, 1, .01))
key(slab, "scale", F(L("b8", 0)["end"] + .3), (1, 1, 1))
show(slab, b8["start"] + .3)
for i in range(24):
    c = prim("ico_sphere", f"concreto{i}", (12, 16, 1.6), (.22, .22, .22), CONCRETE, subdivisions=1)
    period = .5
    fa = F(b8["start"] + .2 - random.uniform(0, period))
    key(c, "location", fa, (12.4, 16 + random.uniform(-.3, .3), 1.5), interp="LINEAR")
    key(c, "location", fa + round(period * FPS), (10 + random.uniform(-1, 1), 16 + random.uniform(-1, 1), -.6), interp="LINEAR")
    for fc in fcurves(c.animation_data.action):
        fc.modifiers.new("CYCLES")
    show(c, b8["start"] + .2, L("b8", 0)["end"] + .3)
beat("concreto", [b8["start"] + .2, L("b8", 0)["end"] + .3])

# ------------------------------------------------------------------ b9: the chiller pulls the heat out
b9 = S[9]
ch = empty("enfriador", (22, 30, 0))
prim("cube", "enf_cuerpo", (0, 0, 1.6), (3.5, 2.2, 1.6), WALLS[2], parent=ch)
fans = [prim("cylinder", f"enf_ventilador{k}", (-1.8 + 1.8 * k, 0, 3.25), (.8, .8, .06), DARK, parent=ch, vertices=12) for k in range(3)]
pop(ch, b9["start"] + .1, final=(1, 1, 1))
for k, fn in enumerate(fans):
    for f in range(F(b9["start"] + .3), F(UNTIL) + 1, 3):
        key(fn, "rotation_euler", f, (0, 0, f * .6 + k), interp="LINEAR")
link1 = prim("cylinder", "tubo_enfriador", (18, 27.5, .3), (.3, .3, 6.2), BRINEM, rot=(0, math.radians(90), math.radians(35)), vertices=10)
pop(link1, b9["start"] + .6, dur=.15)
for i in range(16):  # cold brine goes in, heat comes out of the fans
    d = prim("ico_sphere", f"flujo_frio{i}", (22, 30, .3), (.18, .18, .18), BRINEM, subdivisions=1)
    fa = F(b9["start"] + 1.0 + i * .1)
    key(d, "location", fa, (20, 29, .5), interp="LINEAR")
    key(d, "location", fa + 24, (13, 24.8, -.4), interp="LINEAR")
    for fc in fcurves(d.animation_data.action):
        fc.modifiers.new("CYCLES")
    show(d, b9["start"] + 1.0 + i * .1, S[10]["start"])
heat_out = empty("calor_sale", (22, 30, 3.4))
vapor(heat_out, b9["start"] + 1.3, (-2.5, 2.5), (-1, 1), count=10, mat=HEAT)
show(heat_out, b9["start"] + 1.3, S[10]["start"])
frost_top = box("escarcha", -15, 15, -5, 25, -.5, -.49, FROST)
cut(frost_top, section)
show(frost_top, b9["start"] + 2.6, S[10]["start"] + .6)
cold = empty("frio_losa", (0, 10, -.6))
vapor(cold, b9["start"] + 2.8, (-12, 12), (1, 20), count=14)
show(cold, b9["start"] + 2.8, S[10]["start"])
beat("enfriador", b9["start"] + .1)
beat("flujo", b9["start"] + 1.0)
beat("escarcha", b9["start"] + 2.6)

# ------------------------------------------------------------------ b10: thin layers of water make flat ice
b10 = S[10]
ice = box("hielo", -15, 15, -5, 25, -.5, -.44, ICE, origin=(0, 0, -.5))
cut(ice, section)
cart = empty("rociador_carro", (0, 0, -.5))
prim("cube", "carro_cuerpo", (0, 0, .5), (.8, .6, .4), MACHINE, parent=cart)
prim("cube", "carro_barra", (0, -.8, .25), (6, .06, .06), STEEL, parent=cart)
rociador(cart, -.8, b10["start"], count=30, mat=WATER, ancho=6)
aparecer(cart, b10["start"])
passes = [(-8, 1, 23), (0, 23, 1), (8, 1, 23)]
span = (b10["end"] - .3 - b10["start"]) / 3
show(ice, b10["start"] + .3)
key(ice, "scale", 1, (1, 1, .01), interp="CONSTANT")
for k, (x, ya, yb) in enumerate(passes):
    a = b10["start"] + k * span
    for f in range(F(a), F(a + span) + 1, 2):
        u = (f - F(a)) / max(1, F(a + span) - F(a))
        key(cart, "location", f, (x, lerp(ya, yb, u), -.5), interp="LINEAR")
    key(ice, "scale", F(a + span), (1, 1, (k + 1) / 3))
unpop(cart, b10["end"] - .2, .05)
beat("rociar", [b10["start"], b10["end"] - .3])

# ------------------------------------------------------------------ b12: paint, lines and the clear seal coat
b12 = S[12]
paint = box("pintura", -15, 15, -5, 25, -.44, -.43, PAINTW, origin=(0, -5, -.44))
cut(paint, section)
p0, p1 = b12["start"] + .1, b12["start"] + 1.6
key(paint, "scale", 1, (1, .001, 1), interp="CONSTANT")
key(paint, "scale", F(p0), (1, .001, 1))
key(paint, "scale", F(p1), (1, 1, 1))
show(paint, p0)
painter = empty("pintor", (0, -5, -.43))
prim("cube", "pintor_cuerpo", (0, 0, .4), (1.2, .5, .35), MACHINE, parent=painter)
prim("cube", "pintor_barra", (0, -.6, .1), (14.5, .05, .05), WHITE, parent=painter)
aparecer(painter, p0)
key(painter, "location", F(p0), (0, -4.2, -.43), interp="LINEAR")
key(painter, "location", F(p1), (0, 24.6, -.43), interp="LINEAR")
unpop(painter, p1 + .05, .05)
line_t = b12["start"] + 1.8
lines = [box("linea_centro", -14.2, 14.2, 9.6, 10.4, -.43, -.425, LINER), box("linea_azul1", -14.2, 14.2, 3.6, 4.2, -.43, -.425, LINEB),
         box("linea_azul2", -14.2, 14.2, 15.8, 16.4, -.43, -.425, LINEB)]
for x, y in ((-8, 0), (8, 0), (-8, 20), (8, 20), (0, 10)):
    ring = prim("cylinder", f"circulo{x}_{y}", (x, y if y else 1.2, -.428), (2.4, 2.4, .003), LINER, vertices=24)
    inner = prim("cylinder", f"circulo_int{x}_{y}", (x, y if y else 1.2, -.426), (2.2, 2.2, .003), PAINTW, vertices=24)
    lines += [ring, inner]
for i, ob in enumerate(lines):
    cut(ob, section)
    show(ob, line_t + i * .08)
seal = box("sello", -15, 15, -5, 25, -.425, -.33, ICE, origin=(0, 0, -.425))
cut(seal, section)
key(seal, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(seal, "scale", F(b12["end"] - 1.6), (1, 1, .01))
key(seal, "scale", F(b12["end"] - .2), (1, 1, 1))
show(seal, b12["end"] - 1.6)
ICE_TOP = -.33
beat("pintar", [p0, p1])
beat("lineas", line_t)
beat("sellar", b12["end"] - 1.6)

# ------------------------------------------------------------------ b13: pucks hit the crowd, then boards and glass
b13 = S[13]
crowd = []
for side in (-1, 1):
    for r in range(3):
        bench = box(f"grada{side}{r}", side * (16.5 + r * 1.3) - .65, side * (16.5 + r * 1.3) + .65, 1, 21, 0, .5 + r * .6, CONCRETE)
        show(bench, b13["start"])
        for k in range(6):
            y = 2.5 + k * 3.2 + random.uniform(-.5, .5)
            ps = persona(f"publico{side}{r}{k}", (side * (16.5 + r * 1.3), y, .5 + r * .6), sentada=True)
            ps.rotation_euler.z = math.radians(90 if side > 0 else -90)
            pop(ps, b13["start"] + random.uniform(0, .4), final=(1, 1, 1))
            crowd.append(ps)
puck = prim("cylinder", "disco", (0, 10, ICE_TOP + .04), (.14, .14, .04), DARK, vertices=12)
hit = next(p for p in crowd if p.name == "publico110" or p.name.startswith("publico11"))
t_shot, t_hit = b13["start"] + .4, b13["start"] + 1.3
aparecer(puck, t_shot - .1, tuple(puck.scale))
key(puck, "location", F(t_shot), (0, 10, ICE_TOP + .04), interp="LINEAR")
key(puck, "location", F(t_shot + .45), (10, tuple(hit.location)[1] - 1, ICE_TOP + .3))
key(puck, "location", F(t_hit), (hit.location.x - .3, hit.location.y, hit.location.z + 1.1))
key(puck, "location", F(t_hit + .5), (hit.location.x + 1.0, hit.location.y + .5, hit.location.z))
unpop(puck, t_hit + .6)
key(hit, "scale", F(t_hit), (1, 1, 1))
key(hit, "scale", F(t_hit + .15), (1, 1, .62))
key(hit, "scale", F(t_hit + .9), (1, 1, .62))
key(hit, "scale", F(t_hit + 1.3), (1, 1, 1))
board_t = []
segs = []
for i in range(14):  # long sides
    y = Y0 + i * 2.03
    segs += [(X, X + .15, y, y + 2.03), (-X - .15, -X, y, y + 2.03)]
for i in range(14):  # short sides
    x = -X + i * 2.03
    segs += [(x, x + 2.03, Y0 - .15, Y0), (x, x + 2.03, Y1, Y1 + .15)]
t_b0 = L("b13", 1)["start"] + .1
for i, (a, b, c, d) in enumerate(segs):
    wall = box(f"valla{i}", a, b, c, d, ICE_TOP, ICE_TOP + 1.1, WHITE, origin=((a + b) / 2, (c + d) / 2, ICE_TOP))
    kick = box(f"zoclo{i}", a - .01, b + .01, c - .01, d + .01, ICE_TOP, ICE_TOP + .25, YELLOWL, origin=((a + b) / 2, (c + d) / 2, ICE_TOP))
    glass = box(f"vidrio{i}", a + .04, b - .04, c + .04, d - .04, ICE_TOP + 1.1, ICE_TOP + 2.6, GLASSP, origin=((a + b) / 2, (c + d) / 2, ICE_TOP + 1.1))
    t = t_b0 + (i // 2) * (1.6 / (len(segs) // 2))
    for ob in (wall, kick, glass):
        cut(ob, section)
        pop(ob, t + (.25 if ob is glass else 0), dur=.12, final=(1, 1, 1))
    if i % 6 == 0:
        board_t.append(round(t, 3))
puck2 = prim("cylinder", "disco2", (0, 10, ICE_TOP + .04), (.14, .14, .04), DARK, vertices=12)
t2 = b13["end"] - 1.0
aparecer(puck2, t2 - .1, tuple(puck2.scale))
key(puck2, "location", F(t2), (0, 10, ICE_TOP + .04), interp="LINEAR")
key(puck2, "location", F(t2 + .35), (X - .3, 12, ICE_TOP + .5))
key(puck2, "location", F(t2 + .8), (4, 14, ICE_TOP + .04))
unpop(puck2, S[14]["start"] + .5)
beat("disco", t_shot)
beat("golpe_publico", t_hit)
beat("vallas", board_t)
beat("rebote", t2 + .35)

# ------------------------------------------------------------------ b14: fog, drips, dehumidifiers
b14 = S[14]
fog = []
for i in range(16):
    fg = prim("ico_sphere", f"niebla{i}", (random.uniform(-11, 11), random.uniform(2, 22), random.uniform(1.0, 2.6)), (.01, .01, .01), STEAM, subdivisions=2)
    fg["frente_ok"] = True
    final = (random.uniform(3, 5), random.uniform(3, 5), random.uniform(.8, 1.4))
    key(fg, "scale", F(b14["start"] + .2), (.01, .01, .01))
    key(fg, "scale", F(b14["start"] + 1.6), final)
    key(fg, "scale", F(L("b14", 1)["start"] + 1.4), final)
    key(fg, "scale", F(L("b14", 1)["end"] - .2), (.01, .01, .01))
    fog.append(fg)
rain("goteo", 0, 12, 10, 9, b14["start"] + 1.2, L("b14", 1)["start"] + 1.4, 70)
for o in bpy.data.objects:
    if o.name.startswith("goteo"):
        o.data.materials[0] = WATER
dh_t = []
for i, (x, y) in enumerate([(-16.4, 1.5), (16.4, 1.5), (-16.4, 22.5), (16.4, 22.5)]):
    u = empty(f"deshumidificador{i}", (x, y, 0))
    prim("cylinder", f"dh_poste{i}", (0, 0, 2), (.12, .12, 2), STEEL, parent=u, vertices=6)
    prim("cube", f"dh_caja{i}", (0, 0, 4.4), (.9, .7, .6), WALLS[2], parent=u)
    prim("cylinder", f"dh_rejilla{i}", (-.92 if x > 0 else .92, 0, 4.4), (.45, .45, .03), DARK, parent=u, rot=(0, math.radians(90), 0), vertices=12)
    t = L("b14", 1)["start"] + .2 + i * .25
    pop(u, t, final=(1, 1, 1))
    dh_t.append(round(t, 3))
beat("niebla", b14["start"] + .2)
beat("goteo", b14["start"] + 1.2)
beat("deshumidificadores", dh_t)

# ------------------------------------------------------------------ b15: skaters scratch it, the resurfacer fixes it
b15 = S[15]
skaters = []
for i in range(7):
    sk = persona(f"patinador{i}", (0, 10, ICE_TOP), mat=random.choice([RED, BLUE, GREEN_P, ORANGE]))
    skaters.append(sk)
    ph = i / 7 * 2 * math.pi


def skate(sk, ph, t0, t1, rx=9, ry=7):
    for f in range(F(t0), F(t1) + 1, 3):
        a = ph + f / FPS * .9
        key(sk, "location", f, (rx * math.cos(a), 10 + ry * math.sin(a), ICE_TOP), interp="LINEAR")
        key(sk, "rotation_euler", f, (0, math.radians(-12), a + math.pi), interp="LINEAR")


for i, sk in enumerate(skaters):
    pop(sk, b15["start"] + i * .08, final=(1, 1, 1))
    skate(sk, i / 7 * 2 * math.pi, b15["start"], L("b15", 1)["start"] + .2, 9 - (i % 3), 7 - (i % 2))
    unpop(sk, L("b15", 1)["start"] + .2)
scratches = []
for i in range(46):
    a = random.uniform(0, 2 * math.pi)
    rr = random.uniform(5, 10)
    x, y = rr * math.cos(a), 10 + rr * .75 * math.sin(a)
    sc_ob = prim("cube", f"rayon{i}", (x, y, ICE_TOP + .006), (random.uniform(.5, 1.2), .03, .004), WHITE, rot=(0, 0, a + math.pi / 2 + random.uniform(-.3, .3)))
    pop(sc_ob, b15["start"] + .3 + random.uniform(0, 1.5), dur=.08)
    scratches.append(sc_ob)
rs = empty("pulidora", (0, 0, ICE_TOP))
prim("cube", "pul_cuerpo", (0, 0, .9), (1.2, 1.9, .7), WHITE, parent=rs)
prim("cube", "pul_franja", (0, 0, .75), (1.22, 1.92, .12), LINEB, parent=rs)
prim("cube", "pul_tolva", (0, .6, 1.9), (1.0, .9, .35), LINEB, parent=rs)
prim("cube", "pul_cuchilla", (0, -2.0, .25), (1.3, .2, .2), STEEL, parent=rs)
persona("pul_chofer", (0, -1.0, .6), mat=DARK).parent = rs
wheels(rs, (-1.15, 1.15), (1.2, -1.2), r=.4, w=.3)
lanes = [(-8.5, 1, 23), (0, 23, 1), (8.5, 1, 23)]
r0 = L("b15", 1)["start"]
lane_span = (L("b15", 1)["end"] - r0) / 3
aparecer(rs, r0)
for k, (x, ya, yb) in enumerate(lanes):
    a = r0 + k * lane_span
    for f in range(F(a), F(a + lane_span) + 1, 2):
        u = (f - F(a)) / max(1, F(a + lane_span) - F(a))
        key(rs, "location", f, (x, lerp(ya, yb, u), ICE_TOP), interp="LINEAR")
        key(rs, "rotation_euler", f, (0, 0, 0 if yb > ya else math.pi), interp="CONSTANT")
    film = box(f"pelicula{k}", x - 4.3, x + 4.3, 0, abs(yb - ya), ICE_TOP + .001, ICE_TOP + .012, WET, origin=(x, ya, ICE_TOP))
    if yb < ya:
        film.rotation_euler.z = math.pi
    key(film, "scale", 1, (1, .001, 1), interp="CONSTANT")
    key(film, "scale", F(a), (1, .001, 1))
    key(film, "scale", F(a + lane_span), (1, 1, 1))
    show(film, a, S[16]["start"] + .5)
    for sc_ob in scratches:
        if abs(sc_ob.location.x - x) < 4.3:
            u = (sc_ob.location.y - ya) / (yb - ya)
            unpop(sc_ob, a + max(0, min(1, u)) * lane_span, .06)
unpop(rs, L("b15", 1)["end"] + .1, .05)
beat("patinar", [b15["start"], L("b15", 1)["start"]])
beat("pulidora", [r0, L("b15", 1)["end"]])

# ------------------------------------------------------------------ b16: benches, music, skaters
b16 = S[16]
for i, (x, y) in enumerate([(-22, 4), (-22, 12), (22, 4), (22, 12)]):
    bn = empty(f"banca{i}", (x, y, 0))
    prim("cube", f"banca_a{i}", (0, 0, .45), (.25, 1.1, .05), WOOD, parent=bn)
    prim("cube", f"banca_r{i}", (.22 if x > 0 else -.22, 0, .75), (.04, 1.1, .25), WOOD, parent=bn)
    pop(bn, b16["start"] + .1 + i * .1, final=(1, 1, 1))
for i, (x, y) in enumerate([(-15.5, 24.5), (15.5, 24.5)]):
    spk = empty(f"bocina{i}", (x, y, 0))
    prim("cylinder", f"bocina_poste{i}", (0, 0, 2), (.1, .1, 2), STEEL, parent=spk, vertices=6)
    prim("cube", f"bocina_caja{i}", (0, 0, 4.3), (.5, .4, .7), DARK, parent=spk)
    pop(spk, b16["start"] + .6 + i * .1, final=(1, 1, 1))
    for k in range(5):
        nt_ = empty(f"nota{i}_{k}", (x, y - .5, 4.5))
        prim("ico_sphere", f"nota_c{i}_{k}", (0, 0, 0), (.22, .1, .17), DARK, parent=nt_, subdivisions=1)
        prim("cube", f"nota_p{i}_{k}", (.2, 0, .45), (.03, .03, .45), DARK, parent=nt_)
        fa = F(b16["start"] + 1.0 + k * .35)
        key(nt_, "location", fa, (x, y - .5, 4.6), interp="LINEAR")
        key(nt_, "location", fa + 45, (x + random.uniform(-1.5, 1.5), y - 1.5, 7.5), interp="LINEAR")
        for fc in fcurves(nt_.animation_data.action):
            fc.modifiers.new("CYCLES")
        show(nt_, b16["start"] + 1.0 + k * .35)
for i, sk in enumerate(skaters):
    key(sk, "scale", F(b16["start"] + 1.4 + i * .08) - 1, (0, 0, 0))
    key(sk, "scale", F(b16["start"] + 1.4 + i * .08) + 6, (1, 1, 1))
    skate(sk, i / 7 * 2 * math.pi, b16["start"] + 1.4, UNTIL, 9 - (i % 3), 7 - (i % 2))
beat("bancas", b16["start"] + .1)
beat("musica", b16["start"] + .6)

# ------------------------------------------------------------------ camera
camara()
shot(0, S[2]["start"], (-23, -9, 5.5), (-21.5, -7.5, 5), (-16, 3, 4), (-15, 4, 3.8), False)
shot(S[2]["start"], S[3]["start"], (7, -3, 4.5), (6.5, -1.5, 4), (0, 9, 0), (0, 10, 0), False)
shot(S[3]["start"], S[4]["start"], (24, -18, 14), (22, -16, 12), (0, 10, -1.5), (0, 10, -1.5), True)
shot(S[4]["start"], S[5]["start"], (6, -12, 1.6), (4, -11, 1.3), (1, 6, -1.6), (0, 6, -1.6), True)
shot(S[5]["start"], S[6]["start"], (-6, -11, 1.5), (-4.5, -10, 1.2), (-2, 6, -1.5), (-1, 6, -1.5), True)
shot(S[6]["start"], S[7]["start"], (16, -12, 7), (14, -11, 6), (0, 8, -1.2), (0, 9, -1.2), True)
shot(S[7]["start"], L("b7", 1)["start"], (11, -9, 7), (10, -8, 6.5), (0, 10, -.9), (0, 10, -.9), True)
shot(L("b7", 1)["start"], S[8]["start"], (3.5, -5.5, 1.0), (2.8, -5, .9), (0, 4, -.8), (0, 4, -.8), True)
shot(S[8]["start"], L("b8", 1)["start"], (26, -10, 8), (24, -9, 7), (8, 12, -.6), (8, 12, -.6), True)
shot(L("b8", 1)["start"], S[9]["start"], (-4, -7.5, 1.2), (-3.5, -7, 1.0), (0, 4, -.8), (0, 4, -.8), True)
shot(S[9]["start"], L("b9", 1)["start"], (36, -12, 13), (33, -10, 12), (12, 18, 0), (12, 18, 0), True)
shot(L("b9", 1)["start"], S[10]["start"], (-4, -7.5, 1.3), (-3.5, -7, 1.1), (0, 4, -.7), (0, 4, -.7), True)
shot(S[10]["start"], S[11]["start"], (13, -7, 3), (11, -6, 2.6), (0, 10, -.5), (0, 11, -.5), True)
shot(S[11]["start"], S[12]["start"], (3, 3, 2.6), (2.5, 3.5, 2.2), (0, 7, -.5), (0, 7.5, -.5), False)
shot(S[12]["start"], S[13]["start"], (0, -16, 17), (0, -14, 16), (0, 10, -.4), (0, 10, -.4), False)
shot(S[13]["start"], L("b13", 1)["start"], (6, -6, 3.5), (8, -4, 3.2), (12, 11, .8), (14, 11, 1.0), False)
shot(L("b13", 1)["start"], S[14]["start"], (26, -20, 14), (23, -18, 12), (0, 10, 0), (0, 10, 0), False)
shot(S[14]["start"], S[15]["start"], (16, -10, 5), (14, -9, 4.6), (0, 10, 1.4), (0, 10, 1.2), False)
shot(S[15]["start"], S[16]["start"], (18, -12, 8), (16, -11, 7), (0, 10, -.3), (0, 10, -.3), False)
shot(S[16]["start"], UNTIL + 1, (20, -16, 9), (70, -80, 55), (0, 10, 0), (0, 30, 0), False, lens=26)

terminar()
