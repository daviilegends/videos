"""Immersed-tube tunnel under the sea (06-tunel-bajo-el-mar) on top of motor3d.
The strait runs along y between two shores (land for |x| > 60); the tunnel crosses it along x. The cutaway at y = 0
shows the water column, the seabed, the trench and the inside of the tunnel elements.

    blender -b --python escena_tunel.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar] [--rapido]"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motor3d import *  # noqa: E402,F401,F403

S = {k: SC[f"b{k}"] for k in range(1, 16)}
SAND = material("arena", (.86, .76, .52))
variar(SAND, .4)
SEAWATER = material("agua_mar", (.18, .48, .80), rough=.05, alpha=.55)
agua_animada(SEAWATER, 60)
DOCKWATER = material("agua_dique", (.25, .58, .90), rough=.05, alpha=.6)
GRAVEL = material("grava", (.62, .60, .56))
variar(GRAVEL, .6)
RUBBER = material("hule", (.10, .10, .11), rough=.6)
TANKW = material("agua_lastre", (.20, .60, 1.0), alpha=.75, emit=.4)
LIGHT = material("luz_tunel", (1.0, .92, .65), emit=6.0)
HULLR = material("casco_rojo", (.75, .16, .12))
HULLW = material("casco_blanco", (.95, .95, .92))
ARROWM = material("flecha", (1.0, .85, .15), emit=1.5)

section = seccion()
front = corte_frente()
SEA_X = 60.0
SEABED = -12.0
TRENCH_Z = -21.0
BED_TOP = -20.3
EL_LEN, EL_W, EL_H = 23.0, 7.0, 7.0
SLOTS = [-46.4, -23.2, 0.0, 23.2, 46.4]
DOCK_X = -92.0
YO = 3.5  # the tunnel is shifted so the cut runs through the middle of the near bore (you see inside it)

# ------------------------------------------------------------------ land, seabed and sea
dock_pit = cutter(box("corte_dique", -112, -58, -11, 11, -8.5, 6, None))
dock_pit.location = (0, 0, 0)
trench_cut = cutter(box("corte_zanja", -58, 58, -9.5 + YO, 9.5 + YO, TRENCH_Z, SEABED + .6, None, origin=(-58, 0, 0)))
key(trench_cut, "scale", 1, (.001, 1, 1), interp="CONSTANT")
bore_cut = cutter(box("corte_tunel_playa", 48, 78, -4, 4, -19, -13, None, origin=(78, 0, 0)))
bore_cut.location = (500, 0, 0)

for name, x0, x1 in (("tierra_izq", -400, -SEA_X), ("tierra_der", SEA_X, 400)):
    for lname, z1, z0, mat in (("pasto", 1.5, 1.2, GRASS), ("tierra", 1.2, -3, TOP), ("arena", -3, -14, SAND), ("roca", -14, -250, ROCKL)):
        ob = box(f"{name}_{lname}", x0, x1, -400, 600, z0, z1, mat)
        cut(ob, section)
        if name == "tierra_izq":
            cut(ob, dock_pit)
        else:
            cut(ob, bore_cut)
for lname, z1, z0, mat in (("lecho_arena", SEABED, SEABED - 3, SAND), ("lecho_roca", SEABED - 3, -250, ROCKL)):
    ob = box(lname, -SEA_X, SEA_X, -400, 600, z0, z1, mat)
    cut(ob, section)
    cut(ob, trench_cut)
    cut(ob, bore_cut)
sea = box("mar", -SEA_X, SEA_X, -400, 600, SEABED, 0, SEAWATER)
cut(sea, section)
for i in range(30):  # stones on the cut face of the seabed
    x, z = random.uniform(-55, 55), random.uniform(-38, -13)
    s = random.uniform(.2, .6)
    st = prim("ico_sphere", f"piedra{i}", (x, random.uniform(-.1, .1), z), (s, s * .7, s * .8), ROCKL, subdivisions=1)
    cut(st, section)


def libre(x, y):
    return y > 6 and abs(x) > 70 and not (-115 < x < -55 and -16 < y < 16) and not (x > 60 and abs(y) < 14)


paisaje(libre, arboles=240, zona=(-300, 300, -120, 320), centro=(0, 150),
        casas=[(random.choice((-1, 1)) * random.uniform(75, 150), random.uniform(25, 140)) for _ in range(16)])


# ------------------------------------------------------------------ boats
def barco(name, length, hull_mat, cabin=True):
    p = empty(name)
    prim("cube", f"{name}_casco", (0, 0, .4), (length / 2, length / 7, 1.2), hull_mat, parent=p)
    prim("cube", f"{name}_cubierta", (0, 0, 1.65), (length / 2 - .3, length / 7 - .2, .06), WOOD, parent=p)
    if cabin:
        prim("cube", f"{name}_cabina", (-length / 4, 0, 2.6), (length / 9, length / 9, 1.0), HULLW, parent=p)
        prim("cube", f"{name}_ventanas", (-length / 4 + length / 9 + .02, 0, 2.9), (.02, length / 10, .3), GLASS, parent=p)
    for ch in p.children:
        ch["frente_ok"] = True
    return p


# b1: giant ships cross the strait (along y), a bridge would block them
b1 = S[1]
for k, (x, col, ln) in enumerate(((-15, HULLR, 34), (22, BLUE, 26))):
    sh = barco(f"carguero{k}", ln, col)
    sh.rotation_euler.z = math.radians(90)
    for j in range(4):
        cont = prim("cube", f"carguero{k}_cont{j}", (ln / 2 - 5 - j * 4.2, 0, 2.6), (1.9, ln / 8, 1.0),
                    random.choice((ORANGE, RED, BLUE, MACHINE)), parent=sh)
        cont["frente_ok"] = True
    y0 = -160 if k == 0 else 220
    key(sh, "location", 1, (x, y0, 0), interp="LINEAR")
    key(sh, "location", F(S[2]["start"]), (x, y0 + (110 if k == 0 else -110), 0), interp="LINEAR")
    show(sh, None, S[2]["start"])
bridge = empty("puente_fantasma")
deck = box("puente_tablero", -70, 70, -3, 3, 9, 10, material("fantasma", (1.0, .3, .25), alpha=.35, emit=.6), )
deck.parent = bridge
deck["frente_ok"] = True
for x in (-30, 0, 30):
    pl = box(f"puente_pila{x}", x - 1, x + 1, -1, 1, -12, 9, deck.data.materials[0])
    pl.parent = bridge
    pl["frente_ok"] = True
pop(bridge, L("b1", 0)["start"] + 2.4, dur=.2, final=(1, 1, 1))
unpop(bridge, L("b1", 0)["start"] + 3.6, .25)
beat("barcos", b1["start"] + .3)
beat("puente", [L("b1", 0)["start"] + 2.4, L("b1", 0)["start"] + 3.6])

# b2: digging from the beach, the sea pours in
b2 = S[2]
dig0, dig1 = b2["start"] + .3, L("b2", 1)["start"]
key(bore_cut, "location", F(dig0) - 1, (500, 0, 0), interp="CONSTANT")
key(bore_cut, "location", F(dig0), (78, 0, 0), interp="LINEAR")
key(bore_cut, "scale", F(dig0), (.05, 1, 1), interp="LINEAR")
key(bore_cut, "scale", F(dig1), (1.0, 1, 1), interp="LINEAR")  # grows from x=78 towards the sea
key(bore_cut, "location", F(S[3]["start"]) - 1, (78, 0, 0), interp="CONSTANT")
key(bore_cut, "location", F(S[3]["start"]), (500, 0, 0), interp="CONSTANT")
flood = box("inundacion", 48, 78, -4, 4, -19, -13, SEAWATER, origin=(48, 0, -19))
cut(flood, front)
key(flood, "scale", 1, (1, 1, .001), interp="CONSTANT")
key(flood, "scale", F(L("b2", 1)["start"] + .6), (1, 1, .001))
key(flood, "scale", F(L("b2", 1)["start"] + 2.0), (1, 1, 1))
show(flood, L("b2", 1)["start"] + .5, S[3]["start"])
flujo("chorro", [(56, 0, -11), (58, 0, -14), (64, 0, -16), (74, 0, -17)], L("b2", 1)["start"] + .5, S[3]["start"] - .2, 30, SEAWATER,
      size=(.45, .45, .45), period=.8, jitter=1.0)
for ob in sc.objects:
    if ob.name.startswith("chorro"):
        ob["frente_ok"] = True
miner = empty("excavadora_tunel", (80, 0, -16))
prim("cylinder", "tbm_cuerpo", (0, 0, 0), (2.6, 2.6, 4), MACHINE, parent=miner, rot=(0, math.radians(90), 0), vertices=16)
prim("cylinder", "tbm_cabeza", (-4.2, 0, 0), (2.8, 2.8, .3), DARK, parent=miner, rot=(0, math.radians(90), 0), vertices=16)
for ch in miner.children:
    cut(ch, section)
key(miner, "location", F(dig0), (80, 0, -16), interp="LINEAR")
key(miner, "location", F(dig1), (54, 0, -16), interp="LINEAR")
key(miner, "location", F(dig1 + 1.5), (60, 0, -16), interp="LINEAR")
show(miner, dig0, S[3]["start"])
beat("cavar_playa", [dig0, dig1])
beat("se_inunda", L("b2", 1)["start"] + .5)

# ------------------------------------------------------------------ b3: dredger digs the trench on the seabed
b3 = S[3]
dr0, dr1 = L("b3", 0)["start"] + 1.4, b3["end"] - .3
key(trench_cut, "scale", F(dr0), (.001, 1, 1))
key(trench_cut, "scale", F(dr1), (1, 1, 1), interp="LINEAR")
dredger = barco("draga", 16, MACHINE)
arm = empty("draga_brazo", (6, 0, 2))
arm.parent = dredger
prim("cylinder", "draga_pluma", (0, 0, 4), (.25, .25, 4), STEEL, parent=arm, vertices=8)
bucket = prim("cube", "draga_cuchara", (6, 0, -6), (1.0, 1.2, .8), DARK)
bucket["frente_ok"] = True
cable = prim("cylinder", "draga_cable", (6, 0, -2), (.06, .06, 4), DARK)
cable["frente_ok"] = True
for ob in (bucket, cable):
    ob.parent = dredger
for ch in arm.children:
    ch["frente_ok"] = True
key(dredger, "location", 1, (-70, 0, 0), interp="CONSTANT")
key(dredger, "location", F(b3["start"]), (-70, 0, 0))
key(dredger, "location", F(dr0), (-58 - 6, 0, 0))
key(dredger, "location", F(dr1), (58 - 6, 0, 0), interp="LINEAR")
key(dredger, "location", F(b3["end"] + 1), (75, 0, 0))
scoop_t = []
n_scoops = int((dr1 - dr0) / .9)
for j in range(n_scoops):
    t = dr0 + j * .9
    key(bucket, "location", F(t), (6, 0, 1.5), interp="LINEAR")
    key(bucket, "location", F(t + .45), (6, 0, TRENCH_Z + 1.2 - .0), interp="LINEAR")
    key(cable, "scale", F(t), (1, 1, .1), interp="LINEAR")
    key(cable, "scale", F(t + .45), (1, 1, 2.6), interp="LINEAR")
    key(cable, "location", F(t), (6, 0, 1.8), interp="LINEAR")
    key(cable, "location", F(t + .45), (6, 0, -8.5), interp="LINEAR")
    scoop_t.append(round(t + .45, 3))
show(dredger, b3["start"], S[4]["start"] + 1)
beat("draga", b3["start"])
beat("cucharadas", scoop_t)

# ------------------------------------------------------------------ b4: gravel bed
b4 = S[4]
bed = box("cama_grava", -58, 58, -8.6 + YO, 8.6 + YO, TRENCH_Z, BED_TOP, GRAVEL, origin=(-58, 0, TRENCH_Z))
cut(bed, front)
key(bed, "scale", 1, (.001, 1, 1), interp="CONSTANT")
key(bed, "scale", F(b4["start"] + .3), (.001, 1, 1))
key(bed, "scale", F(b4["end"] - .3), (1, 1, 1), interp="LINEAR")
for k in range(5):
    gravel_rain(f"grava{k}", b4["start"] + .3 + k * (b4["dur"] if "dur" in b4 else (b4["end"] - b4["start"])) / 6,
                b4["start"] + .3 + (k + 1) * (b4["end"] - b4["start"]) / 6, BED_TOP, GRAVEL, (.25, .45), 12,
                xs=(-58 + k * 23, -58 + (k + 1) * 23), ys=(.3, 6))
beat("grava", [b4["start"] + .3, b4["end"] - .3])


# ------------------------------------------------------------------ tunnel elements
def elemento(name, gasket=True):
    """Hollow concrete box (two road bores), built around the origin; returns its empty and its bulkheads."""
    p = empty(name)
    h, w, ln = EL_H, EL_W, EL_LEN / 2
    yo = YO
    parts = [box(f"{name}_piso", -ln, ln, -w + yo, w + yo, 0, 1, CONCRETE), box(f"{name}_techo", -ln, ln, -w + yo, w + yo, h - 1, h, CONCRETE),
             box(f"{name}_pared_s", -ln, ln, -w + yo, -w + 1 + yo, 1, h - 1, CONCRETE), box(f"{name}_pared_n", -ln, ln, w - 1 + yo, w + yo, 1, h - 1, CONCRETE),
             box(f"{name}_pared_c", -ln, ln, -.5 + yo, .5 + yo, 1, h - 1, CONCRETE)]
    heads = [box(f"{name}_mampara{s}", s * ln - .15, s * ln + .15, -w + yo, w + yo, 0, h, STEEL) for s in (-1, 1)]
    tanks = [box(f"{name}_tanque{k}", x - 2, x + 2, 1.3 + yo, 5.6 + yo, 1, 2.6, TANKW, origin=(x, 3.4 + yo, 1)) for k, x in enumerate((-6, 6))]
    seals = []
    if gasket:
        for k, (a, b_, c, d) in enumerate(((-w, w, -.25, .55), (-w, w, h - .55, h + .25), (-w - .25, -w + .55, 0, h), (w - .55, w + .25, 0, h))):
            seals.append(box(f"{name}_junta{k}", ln, ln + .7, a + yo, b_ + yo, c, d, RUBBER, origin=(ln, 0, 0)))
    for ob in parts + heads + tanks + seals:
        ob.parent = p
        cut(ob, front)
    p["heads"] = [o.name for o in heads]
    return p, heads, tanks, seals


# b5: the dry dock; b6: casting the element inside it
b5, b6, b7, b8 = S[5], S[6], S[7], S[8]
dam = box("presa_dique", -62, -58, -11, 11, -8.5, 1.5, CONCRETE, origin=(-60, 0, -8.5))
cut(dam, section)
dock_floor = box("piso_dique", -112, -58, -11, 11, -8.8, -8.5, CONCRETE)
cut(dock_floor, section)
for k, (a, b_, c, d) in enumerate(((-112, -58, 10.6, 11), (-112, -111.6, -11, 11))):
    wl = box(f"muro_dique{k}", a, b_, c, d, -8.5, 1.5, CONCRETE)
    cut(wl, section)
beat("dique", b5["start"] + .3)
EL, HEADS, TANKS, SEALS = elemento("elemento0")
FLOAT_Z = -EL_H + .6  # floating: only the roof sticks out of the water
key(EL, "location", 1, (DOCK_X, 0, -8.5), interp="CONSTANT")
cast0 = b6["start"] + .2
for ob in EL.children:
    if ob.name.startswith("elemento0_mampara") or "junta" in ob.name or "tanque" in ob.name:
        continue
    key(ob, "scale", 1, (1, 1, .001), interp="CONSTANT")
    key(ob, "scale", F(cast0) - 1, (1, 1, .001), interp="CONSTANT")
    key(ob, "scale", F(cast0 + 1.6), (1, 1, 1))
show(EL, cast0)
for ob in HEADS:
    pop(ob, b7["start"] + .3 + HEADS.index(ob) * .5, dur=.2, final=tuple(ob.scale))
for ob in TANKS + SEALS:
    show(ob, b7["start"] + .2)
crane = empty("grua_dique", (DOCK_X + 16, 12, 1.5))
prim("cube", "grua_torre", (0, 0, 9), (.6, .6, 9), MACHINE, parent=crane)
prim("cube", "grua_pluma", (-8, 0, 18), (10, .4, .4), MACHINE, parent=crane)
hook = prim("cube", "grua_gancho", (-14, 0, 8), (.5, .5, .6), DARK, parent=crane)
key(hook, "location", F(cast0), (-14, 0, 14), interp="LINEAR")
key(hook, "location", F(cast0 + 1.2), (-14, 0, 2), interp="LINEAR")
show(crane, b5["start"], b9_start := S[9]["start"])
gravel_rain("colado", cast0, cast0 + 1.6, -1.6, CONCRETE, (.15, .25), 30, xs=(DOCK_X - 10, DOCK_X + 10), ys=(.3, 6))
beat("colar", cast0)
beat("mamparas", [b7["start"] + .3, b7["start"] + .8])

# b8: flood the dock: water rises, the dam drops, the element floats up
fl0, fl1 = b8["start"] + .2, b8["start"] + 2.6
dock_water = box("agua_dique", -112, -58, -11, 11, -8.5, 0, DOCKWATER, origin=(-85, 0, -8.5))
cut(dock_water, section)
key(dock_water, "scale", 1, (1, 1, .001), interp="CONSTANT")
key(dock_water, "scale", F(fl0), (1, 1, .001))
key(dock_water, "scale", F(fl1), (1, 1, 1), interp="LINEAR")
show(dock_water, fl0)
key(dam, "scale", F(fl1), (1, 1, 1))
key(dam, "scale", F(fl1 + .6), (1, 1, .001))
float_t = L("b8", 0)["start"] + 3.2
key(EL, "location", F(float_t), (DOCK_X, 0, -8.5))
key(EL, "location", F(float_t + 1.2), (DOCK_X, 0, FLOAT_Z))
for f in range(F(float_t + 1.2), F(S[9]["start"]), 3):  # bobbing
    key(EL, "location", f, (DOCK_X, 0, FLOAT_Z + .15 * math.sin(f * .2)), interp="LINEAR")
beat("inundar", fl0)
beat("flota", float_t)

# b9: tugboats tow it above the trench
b9 = S[9]
tw0, tw1 = b9["start"] + .3, b9["end"] - .2
key(EL, "location", F(tw0), (DOCK_X, 0, FLOAT_Z))
key(EL, "location", F(tw1), (SLOTS[0], 0, FLOAT_Z), interp="LINEAR")
tugs = []
for k, dy in enumerate((-5.5, 5.5)):
    tg = barco(f"remolcador{k}", 7, RED if k == 0 else ORANGE)
    rope = prim("cylinder", f"cabo{k}", (-6, 0, 1.6), (.05, .05, 3), DARK, parent=tg, rot=(0, math.radians(90), 0))
    rope["frente_ok"] = True
    key(tg, "location", F(tw0), (DOCK_X + EL_LEN / 2 + 9, dy, .2))
    key(tg, "location", F(tw1), (SLOTS[0] + EL_LEN / 2 + 9, dy, .2), interp="LINEAR")
    show(tg, tw0 - .2, S[10]["start"] + 1.5)
    vapor(tg, tw0, (-3, -1), (-.5, .5), count=6, mat=STEAM, tam=.6)
    tugs.append(tg)
beat("remolque", [tw0, tw1])

# b10: ballast tanks fill, it sinks onto the gravel bed
b10 = S[10]
fill0 = b10["start"] + .3
for tk in TANKS:
    key(tk, "scale", 1, (1, 1, .05), interp="CONSTANT")
    key(tk, "scale", F(fill0), (1, 1, .05))
    key(tk, "scale", F(fill0 + 1.5), (1, 1, 1), interp="LINEAR")
sink0, sink1 = fill0 + 1.2, b10["end"] - .2
key(EL, "location", F(sink0), (SLOTS[0], 0, FLOAT_Z))
key(EL, "location", F(sink1), (SLOTS[0], 0, BED_TOP), interp="LINEAR")
for k, tg in enumerate(tugs):
    unpop(tg, b10["end"] + .3, .25)
beat("lastre", fill0)
beat("hundir", [sink0, sink1])

# b11-b12: second element, pulled tight; water between them pumped out; the sea pushes
b11, b12 = S[11], S[12]
EL2, HEADS2, TANKS2, SEALS2 = elemento("elemento1")
pull0, pull1 = L("b11", 0)["start"] + 1.6, b11["end"] - .3
gap = 2.0
x2 = SLOTS[1]
key(EL2, "location", 1, (x2, 0, BED_TOP + 30), interp="CONSTANT")
key(EL2, "location", F(b11["start"]), (x2 - gap, 0, BED_TOP + 6))
key(EL2, "location", F(pull0), (x2 - gap, 0, BED_TOP))
key(EL2, "location", F(pull1), (x2 - .7, 0, BED_TOP), interp="LINEAR")
show(EL2, b11["start"])
for sl in SEALS:  # the seal on element 0's end squeezes when the sea presses
    key(sl, "scale", F(L("b12", 0)["start"] + 2.2), (1, 1, 1))
    key(sl, "scale", F(L("b12", 0)["start"] + 3.2), (.35, 1, 1))
key(EL2, "location", F(L("b12", 0)["start"] + 2.2), (x2 - .7, 0, BED_TOP))
key(EL2, "location", F(L("b12", 0)["start"] + 3.2), (x2 - .25, 0, BED_TOP))
trapped = box("agua_atrapada", SLOTS[0] + EL_LEN / 2, SLOTS[0] + EL_LEN / 2 + .5, -6.8 + YO, 6.8 + YO, BED_TOP + .2, BED_TOP + EL_H - .2, TANKW,
              origin=(SLOTS[0] + EL_LEN / 2, 0, BED_TOP + .2))
cut(trapped, front)
show(trapped, pull1, L("b12", 0)["start"] + 2.4)
key(trapped, "scale", F(L("b12", 0)["start"] + .6), (1, 1, 1))
key(trapped, "scale", F(L("b12", 0)["start"] + 2.2), (1, 1, .02), interp="LINEAR")
arrows = []
for k in range(3):  # the whole sea pushing on the far end
    ar = prim("cone", f"flecha_mar{k}", (x2 + EL_LEN / 2 + 3.5, -2, BED_TOP + 1.5 + k * 2.2), (.7, .7, 1.4), ARROWM,
              rot=(0, math.radians(-90), 0), vertices=10)
    ar["frente_ok"] = True
    pop(ar, L("b12", 0)["start"] + 2.0 + k * .12, final=(.7, .7, 1.4))
    unpop(ar, S[13]["start"] + .2)
    for f in range(F(L("b12", 0)["start"] + 2.2), F(S[13]["start"]), 4):
        key(ar, "location", f, (x2 + EL_LEN / 2 + 3.5 - .6 * abs(math.sin(f * .25)), -2, BED_TOP + 1.5 + k * 2.2), interp="LINEAR")
beat("tirar", [pull0, pull1])
beat("bombear", [L("b12", 0)["start"] + .6, L("b12", 0)["start"] + 2.2])
beat("presion", L("b12", 0)["start"] + 2.2)

# b13: piece after piece across the strait
b13 = S[13]
rest = []
for k, x in enumerate(SLOTS[2:]):
    e, hh, tt, ss = elemento(f"elemento{k + 2}")
    t = b13["start"] + .2 + k * (b13["end"] - b13["start"] - .4) / 3
    key(e, "location", 1, (x, 0, FLOAT_Z), interp="CONSTANT")
    key(e, "location", F(t), (x, 0, FLOAT_Z))
    key(e, "location", F(t + .9), (x, 0, BED_TOP))
    show(e, t)
    rest.append((e, hh))
beat("piezas", [round(b13["start"] + .2 + k * (b13["end"] - b13["start"] - .4) / 3 + .9, 3) for k in range(3)])

# b14: rock backfill over the tunnel
b14 = S[14]
for j, (y0, y1, z0) in enumerate(((-9.4 + YO, 9.4 + YO, BED_TOP + EL_H), (EL_W + YO, 9.4 + YO, BED_TOP))):
    fill = box(f"relleno_roca{j}", -58, 58, y0, y1, z0, SEABED - .2, ROCKL, origin=(0, 0, z0))  # roof and far side only
    cut(fill, front)
    key(fill, "scale", 1, (1, 1, .001), interp="CONSTANT")
    key(fill, "scale", F(b14["start"] + .4), (1, 1, .001))
    key(fill, "scale", F(b14["end"] - .3), (1, 1, 1), interp="LINEAR")
    show(fill, b14["start"] + .4)
for k in range(5):
    gravel_rain(f"roca{k}", b14["start"] + .3, b14["end"] - .5, SEABED - .3, ROCKL, (.4, .8), 10, xs=(-58 + k * 23, -35 + k * 23), ys=(.5, 7))
beat("relleno", [b14["start"] + .4, b14["end"] - .3])

# b15: bulkheads out, road, lights, cars
b15 = S[15]
k0 = b15["start"] + .2
all_heads = HEADS + HEADS2 + [h for _, hh in rest for h in hh]
for j, h in enumerate(all_heads):
    unpop(h, k0 + j * .05, .15)
for k, x in enumerate(SLOTS):
    rd = box(f"carretera{k}", x - EL_LEN / 2, x + EL_LEN / 2, -2.5 + YO, -.5 + YO, BED_TOP + 1.0, BED_TOP + 1.12, ASPHALT)
    cut(rd, front)
    show(rd, k0 + .7 + k * .08)
    for j in range(5):
        lt = box(f"luz{k}_{j}", x - 10 + j * 5, x - 9 + j * 5, -2.0 + YO, -1.0 + YO, BED_TOP + EL_H - 1.15, BED_TOP + EL_H - 1.0, LIGHT)
        show(lt, L("b15", 0)["start"] + 2.6 + k * .1)
cars_t = L("b15", 0)["start"] + 2.6
for i in range(6):
    cr = car(f"coche{i}", random.choice((RED, BLUE, WALLS[0], MACHINE)))
    cr.rotation_euler.z = math.radians(90)
    lane_y = 1.6
    t0 = cars_t + i * .5
    key(cr, "location", F(t0), (-30, lane_y, BED_TOP + 1.12), interp="LINEAR")
    key(cr, "location", F(t0 + 5), (60, lane_y, BED_TOP + 1.12), interp="LINEAR")
    show(cr, t0, t0 + 5)
beat("mamparas_fuera", k0)
beat("camino", k0 + .7)
beat("luces", L("b15", 0)["start"] + 2.6)
beat("coches", cars_t)

# ------------------------------------------------------------------ camera
camara()
shot(0, S[2]["start"], (-30, -150, 55), (-10, -130, 45), (0, 30, -2), (0, 30, -4), False)
shot(S[2]["start"], S[3]["start"], (82, -46, 6), (76, -40, 4), (62, 0, -12), (60, 0, -13), True)
shot(S[3]["start"], S[4]["start"], (-50, -62, 8), (40, -62, 8), (-45, 0, -12), (40, 0, -12), True)
shot(S[4]["start"], S[5]["start"], (-10, -46, -6), (20, -46, -7), (-10, 0, -19), (20, 0, -19), True)
shot(S[5]["start"], S[6]["start"], (-70, -70, 28), (-74, -60, 22), (-85, 0, -4), (-86, 0, -5), True)
shot(S[6]["start"], S[7]["start"], (-74, -40, 6), (-78, -36, 4), (-90, 0, -4), (-92, 0, -4), True)
shot(S[7]["start"], S[8]["start"], (-70, -26, 0), (-72, -24, -1), (-80, 0, -4), (-80, 0, -4), True)
shot(S[8]["start"], S[9]["start"], (-74, -58, 14), (-76, -54, 12), (-88, 0, -3), (-90, 0, -2), True)
shot(S[9]["start"], S[10]["start"], (-95, -70, 22), (-50, -70, 20), (-88, 0, -2), (-48, 0, -3), True)
shot(S[10]["start"], S[11]["start"], (-40, -52, -3), (-42, -48, -6), (-46, 0, -12), (-46, 0, -16), True)
shot(S[11]["start"], S[12]["start"], (-26, -26, -13), (-28, -24, -14), (-34, 0, -17), (-35, 0, -17), True)
shot(S[12]["start"], S[13]["start"], (-14, -44, -10), (-16, -40, -11), (-26, 0, -17), (-24, 0, -17), True)
shot(S[13]["start"], S[14]["start"], (0, -120, 6), (0, -110, 2), (0, 0, -15), (0, 0, -16), True)
shot(S[14]["start"], S[15]["start"], (15, -66, 0), (10, -60, -2), (0, 0, -15), (0, 0, -15), True)
shot(S[15]["start"], L("b15", 0)["start"] + 6.0, (-30, -14, -17.5), (10, -14, -17.5), (-20, 1.5, -18.2), (20, 1.5, -18.2), True, lens=20)
shot(L("b15", 0)["start"] + 6.0, UNTIL + 1, (0, -90, 10), (0, -150, 50), (0, 0, -12), (0, 40, -4), True, lens=24)

terminar()
