"""'¿Cómo se hace?' episode 02 (botella de plástico) on top of motor3d. The line runs along +x inside a factory hall:
pellets, dryer, extruder, injection mold, preform, infrared oven, stretch-blow mold, inspection, filler, labeler, packing,
recycling. Light rules learned on episode 01: pieces fully behind the cut are not sliced, moving particles travel
behind the cut plane (y > 0) instead of being sliced, and the cutter stays static.

    blender -b --python escena_botella.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar] [--rapido]"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motor3d import *  # noqa: E402,F401,F403

random.seed(2)
S = {k: SC[f"b{k}"] for k in range(1, 15)}
PELLET = material("pet_bolitas", (.80, .90, .97), rough=.15, alpha=.8)
PET = material("pet", (.78, .90, .98), rough=.04, alpha=.32)
PREF = material("preforma", (.55, .78, .95), rough=.05, alpha=.6)
PREF_HOT = material("preforma_caliente", (1.0, .62, .35), rough=.1, alpha=.7, emit=.8)
MELT = material("pet_fundido", (1.0, .70, .25), rough=.1, alpha=.85, emit=1.6)
HOT = material("calor", (1.0, .40, .10), emit=3.0)
IR = material("infrarrojo", (1.0, .25, .08), emit=4.0)
COOL = material("frio", (.35, .70, 1.0), emit=1.2)
SS = material("inoxidable", (.80, .82, .85), rough=.25)
BLUEM = material("motor", (.15, .35, .70), rough=.4)
GOLD = material("tornillo_dorado", (.95, .72, .25), rough=.25)
DRINK = material("bebida", (.95, .55, .15), rough=.05, alpha=.7)
CAP = material("tapa", (.10, .45, .85), rough=.4)
LABEL = material("etiqueta", (.90, .20, .18), rough=.5)
GREEN = material("escaner", (.2, 1.0, .35), emit=4.0, alpha=.5)
REDL = material("rechazo", (1.0, .12, .10), emit=4.0)
RECYC = material("reciclaje", (.20, .60, .30))
CARD = material("carton", (.72, .55, .35))
HOLO = material("holograma", (.6, .85, 1.0), alpha=.25, emit=1.0)
section = seccion()
nave(-52, 62)
Z = 2.5  # extruder axis height

# preform and bottle profiles, (radius, z) with the neck ring at z=0: the neck never changes, the body grows below it
PREFORM = [(0, -1.0), (.12, -.98), (.17, -.92), (.18, -.8), (.18, -.6), (.18, -.4), (.18, -.2), (.18, -.1), (.19, -.05),
           (.25, -.03), (.25, 0), (.19, .02), (.19, .25), (0, .25)]
STRETCHED = [(0, -2.5), (.1, -2.48), (.14, -2.4), (.15, -2.1), (.15, -1.6), (.15, -1.1), (.16, -.6), (.17, -.25), (.19, -.05),
             (.25, -.03), (.25, 0), (.19, .02), (.19, .25), (0, .25)]
BOTTLE = [(0, -2.6), (.38, -2.57), (.48, -2.45), (.5, -2.2), (.5, -1.6), (.5, -1.0), (.42, -.6), (.26, -.25), (.19, -.05),
          (.25, -.03), (.25, 0), (.19, .02), (.19, .25), (0, .25)]


def threads(parent, mat=None):
    """Three thread rings on the neck, so the cap has somewhere to go."""
    for k in range(3):
        prim("cylinder", f"{parent.name}_rosca{k}", (0, 0, .07 + k * .06), (.21, .21, .015), mat or parent.active_material, parent=parent, vertices=20)


def preform(name, loc, mat=PREF, formas=None):
    ob = torno(name, PREFORM, mat, loc, formas=formas)
    threads(ob)
    return ob


def bottle(name, loc, mat=PET, cap=False):
    ob = torno(name, BOTTLE, mat, loc, segs=28)
    threads(ob)
    if cap:
        prim("cylinder", f"{name}_tapa", (0, 0, .2), (.23, .23, .1), CAP, parent=ob, vertices=20)
    return ob


# ------------------------------------------------------------------ b1-b2: a pile of PET pellets, the bottle we want
b1, b2 = S[1], S[2]
crate = box("caja_bolitas", -47, -42, .5, 4.5, .05, 1.6, CARD)
cut(crate, cutter(box("caja_hueco", -46.8, -42.2, .7, 4.3, .3, 2, None)))
pile = prim("ico_sphere", "monton_bolitas", (-44.5, 2.5, 1.3), (2.3, 1.7, .6), PELLET, subdivisions=3)
for i in range(70):
    prim("cylinder", f"bolita{i}", (-44.5 + random.uniform(-2.2, 2.2), random.uniform(.8, 4), random.uniform(1.4, 1.9)), (.09, .09, .07), PELLET,
         rot=(random.uniform(0, 3), random.uniform(0, 3), 0), vertices=8)
holo = bottle("botella_sueno", (-44.5, 2.5, 6.2), HOLO)
pop(holo, b1["start"] + .4, final=(1, 1, 1))
girar(holo, 2, 1.2, b1["start"], S[2]["start"] + .5)
unpop(holo, L("b1", 0)["end"] - 1.4)
hand_scoop = empty("pala", (-41, .6, 2.2))
prim("cylinder", "pala_cuenco", (0, 0, 0), (.6, .6, .12), STEEL, parent=hand_scoop, vertices=16)
for i in range(14):
    prim("cylinder", f"pala_bolita{i}", (random.uniform(-.4, .4), random.uniform(-.4, .4), .14), (.09, .09, .07), PELLET, parent=hand_scoop,
         rot=(random.uniform(0, 3), random.uniform(0, 3), 0), vertices=8)
aparecer(hand_scoop, b2["start"] + .1)
key(hand_scoop, "location", F(b2["start"] + .1), (-41, .6, 2.2))
key(hand_scoop, "location", F(b2["end"] - .2), (-41, .6, 2.8))
unpop(hand_scoop, S[3]["start"] + .1)
beat("bolitas", b2["start"] + .1)

# ------------------------------------------------------------------ b3: moisture makes it brittle; the dryer
b3 = S[3]
for i in range(12):  # droplets cling to the pellets in the scoop
    d = prim("ico_sphere", f"gota{i}", (-41 + random.uniform(-.45, .45), .6 + random.uniform(-.45, .45), 2.95), (.05, .05, .06), WATER, subdivisions=1)
    d["frente_ok"] = True
    pop(d, b3["start"] + .3 + i * .08, dur=.15)
    unpop(d, L("b3", 1)["start"])
test = empty("pieza_fragil", (-38.6, .2, 1.2))
halves = []
for k, s_ in enumerate((-1, 1)):
    h = box(f"fragil{k}", -.04 * s_ - (.35 if s_ < 0 else 0), (.35 if s_ > 0 else 0) - .04 * s_, -.12, .12, 0, .9, material("pet_amarillo", (.85, .78, .55), alpha=.8))
    h.parent = test
    halves.append(h)
stand = box("pedestal_fragil", -39.2, -38, -.2, .6, .05, 1.2, DARK)
aparecer(test, b3["start"] + 1.2)
t_snap = L("b3", 0)["end"] - .5
for k, h in enumerate(halves):
    key(h, "location", F(t_snap), (0, 0, 0))
    key(h, "rotation_euler", F(t_snap), (0, 0, 0))
    key(h, "location", F(t_snap + .35), ((-.25, .25)[k], 0, -.2))
    key(h, "rotation_euler", F(t_snap + .35), (0, (.5, -.5)[k], 0))
unpop(test, L("b3", 1)["start"] + .2)
dryer = prim("cylinder", "secador", (-34, 0, 4.6), (1.6, 1.6, 2.8), SS, vertices=32)
dryer_in = cutter(prim("cylinder", "secador_hueco", (-34, 0, 4.8), (1.45, 1.45, 2.8), None, vertices=32))
cut(dryer, dryer_in)
cut(dryer, section)
dcone = prim("cone", "secador_cono", (-34, 0, 1.3), (1.6, 1.6, .55), SS, rot=(math.pi, 0, 0), vertices=32)
cut(dcone, section)
fill_d = prim("cylinder", "secador_relleno", (-34, 0, 4.0), (1.42, 1.42, 2.0), PELLET, vertices=32)
cut(fill_d, section)
heater = box("secador_resistencia", -35.2, -32.8, 0, 1.3, 2.0, 2.3, HOT)
show(heater, L("b3", 1)["start"] + .2)
soporte("secador", -35.3, -32.7, .9, 1.3)
for o in flujo("aire_caliente", [(-34, .5, 2.2), (-34, .5, 6.8)], L("b3", 1)["start"] + .3, S[4]["start"] + .5, 22,
               material("aire", (1.0, .55, .25), alpha=.35, emit=1.2), (.14, .14, .14), period=1.2, jitter=1.0):
    o["frente_ok"] = True
steam_d = empty("vapor_secador", (-34, .4, 7.5))
vapor(steam_d, L("b3", 1)["start"] + 1.0, (-.5, .5), (-.3, .3), count=10, tam=.4)
show(steam_d, L("b3", 1)["start"] + 1.0, S[4]["start"] + 1)
for o in flujo("tubo_bolitas", [(-44.5, .5, 1.9), (-40, .5, 6), (-34, .5, 7.2), (-34, .5, 5.8)], b2["end"], S[4]["start"], 18, PELLET,
               (.09, .09, .07), period=1.6, kind="cylinder", jitter=.1):
    o["frente_ok"] = True
beat("gotas", b3["start"] + .3)
beat("cruje", t_snap)
beat("secador", [L("b3", 1)["start"] + .2, S[4]["start"]])

# ------------------------------------------------------------------ b4: extruder melts it into thick honey
b4 = S[4]
X0, X1 = -29, -17
barrel = prim("cylinder", "barril", ((X0 + X1) / 2, 0, Z), (.9, .9, (X1 - X0) / 2), SS, rot=(0, math.radians(90), 0), vertices=32)
bore = cutter(prim("cylinder", "barril_hueco", ((X0 + X1) / 2, 0, Z), (.74, .74, (X1 - X0) / 2 + .2), None, rot=(0, math.radians(90), 0), vertices=32))
cut(barrel, bore)
cut(barrel, section)
for k in range(4):
    band = prim("cylinder", f"banda_calor{k}", (X0 + 2.5 + k * 3, 0, Z), (.96, .96, .35), HOT, rot=(0, math.radians(90), 0), vertices=32)
    cut(band, bore)
    cut(band, section)
    show(band, b4["start"] + .6)
motor = box("motor_extrusor", X0 - 4, X0 - .4, -1.4, 1.4, 1.0, 4.0, BLUEM)
cut(motor, section)
soporte("extrusor", X0 + .5, X1 - .5, .7, Z - .9)
feed = prim("cone", "extrusor_tolva", (X0 + 1.5, 0, Z + 2.2), (1.1, 1.1, .9), SS, rot=(math.pi, 0, 0), vertices=16)
cut(feed, section)
screw = empty("tornillo", (X0 + .3, 0, Z))
prim("cylinder", "tornillo_eje", ((X1 - X0) / 2, 0, 0), (.22, .22, (X1 - X0) / 2 - .2), GOLD, parent=screw, rot=(0, math.radians(90), 0), vertices=12)
for k in range(48):  # whole screw inside the sliced barrel, the way cutaway drawings show it: no boolean on moving parts
    fl = prim("cube", f"helice{k}", (.3 + k * (X1 - X0 - .8) / 48, 0, 0), (.05, .66, .09), GOLD, parent=screw, rot=(k * .55, 0, 0))
    fl["frente_ok"] = True
for ch in screw.children:
    ch["frente_ok"] = True
girar(screw, 0, -6, b4["start"], S[6]["start"])
for o in flujo("bolitas_barril", [(X0 + .8, .4, Z + .2), ((X0 + X1) / 2, .4, Z + .1)], b4["start"] + .3, S[6]["start"], 24, PELLET, (.09, .09, .07),
               period=1.8, kind="cylinder", jitter=.15):
    o["frente_ok"] = True
for o in flujo("miel", [((X0 + X1) / 2, .4, Z), (X1 - .2, .4, Z)], b4["start"] + .8, S[6]["start"], 20, MELT, (.2, .2, .2), period=1.8,
               grow=(.6, 1.2), jitter=.15):
    o["frente_ok"] = True
beat("extrusor", [b4["start"], S[5]["start"]])

# ------------------------------------------------------------------ b5-b6: injection mold makes preforms
b5, b6 = S[5], S[6]
MX = -12
runner = prim("cylinder", "canal", ((X1 + MX - 2) / 2, .4, Z), (.18, .18, (MX - 2 - X1) / 2), STEEL, rot=(0, math.radians(90), 0), vertices=10)
mold_low = box("molde_abajo", MX - 2.4, MX + 2.4, -1.2, 1.4, .9, 2.6, STEEL)
cut(mold_low, cutter(box("molde_cavidades", MX - 2.2, MX + 2.2, -1.4, 1.0, 1.1, 2.8, None)))  # open row of cavities
cut(mold_low, section)
mold_top = empty("molde_arriba", (MX, 0, 2.6))
top_block = box("molde_arriba_bloque", MX - 2.4, MX + 2.4, -1.2, 1.4, 2.6, 3.4, MACHINE, origin=(MX, 0, 2.6))
top_block.parent = mold_top
top_block.location = (0, 0, 0)
cut(top_block, section)
soporte("molde", MX - 2.2, MX + 2.2, 1.2, .9)
t_shot = b5["start"] + 1.2
t_open = L("b5", 1)["start"] + .2
key(mold_top, "location", F(t_open), (MX, 0, 2.6))
key(mold_top, "location", F(t_open + .5), (MX, 0, 4.6))
hot_pre, cold_pre = [], []
for k in range(4):  # four cavities in a row, behind the cut plane so they stay whole
    x = MX - 1.65 + k * 1.1
    hp = torno(f"preforma_fundida{k}", [(r, z + 1.0) for r, z in PREFORM], MELT, (x, .45, 1.15))
    key(hp, "scale", F(t_shot + k * .05), (1, 1, .02))
    key(hp, "scale", F(t_shot + .6 + k * .05), (1, 1, 1))
    show(hp, t_shot, t_open)
    cp = preform(f"preforma_molde{k}", (x, .45, 2.15))
    show(cp, t_open)
    key(cp, "location", F(t_open + .4), (x, .45, 2.15))
    key(cp, "location", F(t_open + .9), (x, .45, 3.6))
    key(cp, "location", F(L("b5", 1)["end"]), (x, .45, 3.6))
    key(cp, "location", F(L("b5", 1)["end"] + .6), (-5 + k * .02, .3 + k * .15, 1.3 + k * .3))
    unpop(cp, S[6]["start"] + .2)
    hot_pre.append(hp)
    cold_pre.append(cp)
beat("inyectar", t_shot)
beat("abrir_molde", t_open)

hero = preform("preforma_estrella", (-5, .3, 2.0))  # b6: close-up on a pedestal, turning, the thread catching the light
box("pedestal_preforma", -5.6, -4.4, -.3, .9, .05, 1.0, DARK)
pop(hero, b6["start"] + .1, final=(1, 1, 1))
girar(hero, 2, 1.5, b6["start"], S[8]["start"])
ring = prim("cylinder", "brillo_rosca", (-5, .3, 2.13), (.24, .24, .1), material("rosca_brillo", (1, .9, .3), alpha=.4, emit=2.0), vertices=24)
ring["frente_ok"] = True
show(ring, L("b6", 1)["start"] + 1.2, L("b6", 1)["end"])
beat("preforma", b6["start"] + .1)

# ------------------------------------------------------------------ b7: too thick and small to drink from
b7 = S[7]
ghost = bottle("botella_fantasma", (-3.2, .3, 3.6), HOLO)
pop(ghost, b7["start"] + .3, final=(1, 1, 1))
unpop(ghost, S[8]["start"])
unpop(hero, S[8]["start"] + .1)
beat("comparar", b7["start"] + .3)

# ------------------------------------------------------------------ b8: infrared oven, the neck stays cool
b8 = S[8]
OX0, OX1 = 1, 11
oven = box("horno_ir", OX0, OX1, -1.2, 1.6, .9, 3.6, SS)
cut(oven, cutter(box("horno_ir_hueco", OX0 - .5, OX1 + .5, -1.0, 1.4, 1.1, 3.4, None)))
cut(oven, section)
for k in range(5):
    lamp = box(f"lampara_ir{k}", OX0 + .3, OX1 - .3, 1.15, 1.3, 1.3 + k * .3, 1.42 + k * .3, IR)
    show(lamp, b8["start"] + .4)
coolp = box("placa_fria", OX0 + .3, OX1 - .3, .2, 1.1, 3.0, 3.1, COOL)
show(coolp, L("b8", 1)["start"])
chain = box("cadena", OX0 - 2, OX1 + 3, .2, .7, 3.25, 3.35, DARK)
soporte("horno_ir", OX0 + .4, OX1 - .4, 1.4, .9)
oven_pre = []
for k in range(9):
    p = preform(f"preforma_horno{k}", (OX0 - 1, .45, 2.9), PREF_HOT)
    oven_pre.append(p)
    girar(p, 2, 9, b8["start"], S[9]["start"] + 1)
desfile(oven_pre, [(OX0 - 1.5, .45, 2.9), (OX1 + 2.5, .45, 2.9)], b8["start"], S[9]["start"] + .5, period=6)
beat("horno_ir", [b8["start"] + .4, S[9]["start"]])

# ------------------------------------------------------------------ b9-b10: stretch-blow mold
b9, b10 = S[9], S[10]
BX = 16
t_in = b9["start"] + .3
t_stretch = L("b9", 1)["start"] + .3
t_blow = t_stretch + .9
t_cool = b10["start"] + .4
t_out = b10["end"] - 1.0
blow = torno("preforma_soplado", PREFORM, PREF_HOT, (BX, 0, 4.1), segs=32, formas={"estirada": STRETCHED, "botella": BOTTLE})
threads(blow)
cut(blow, section)
show(blow, t_in)
key(blow, "location", F(t_in), (BX - 2.5, 0, 4.1))
key(blow, "location", F(t_in + .6), (BX, 0, 4.1))
for nm, f, v in (("estirada", t_stretch, 0), ("estirada", t_stretch + .7, 1), ("estirada", t_blow, 1), ("estirada", t_blow + .35, 0),
                 ("botella", t_blow, 0), ("botella", t_blow + .35, 1)):
    shape_key(blow, nm, F(f), v)
blow.data.materials.append(PET)
cool_sw = prim("cylinder", "botella_enfriada", (BX, 0, 2.8), (.505, .505, 1.27), PET, vertices=28)  # stands in after cooling
cool_sw.hide_render = True
halves = []
for k, (a, b) in enumerate(((BX - 1.6, BX), (BX, BX + 1.6))):
    h = empty(f"molde_soplado{k}", ((a + b) / 2, 0, 2.8))
    blk = box(f"molde_soplado_bloque{k}", a, b, -1.0, 1.0, 1.2, 4.3, STEEL, origin=((a + b) / 2, 0, 2.8))
    blk.parent = h
    blk.location = (0, 0, 0)
    cav = cutter(torno(f"cavidad{k}", [(r + .01 if r else 0, z) for r, z in BOTTLE], None, (BX - (a + b) / 2, 0, 1.3), segs=32, parent=h))
    cut(blk, cav)
    cut(blk, section)
    side = -1 if k == 0 else 1
    key(h, "location", F(t_in + .6), ((a + b) / 2 + side * 1.2, 0, 2.8))
    key(h, "location", F(t_in + 1.0), ((a + b) / 2, 0, 2.8))
    key(h, "location", F(t_out), ((a + b) / 2, 0, 2.8))
    key(h, "location", F(t_out + .4), ((a + b) / 2 + side * 1.2, 0, 2.8))
    halves.append(h)
rod = prim("cylinder", "varilla", (BX, .02, 6.0), (.05, .05, 1.6), STEEL, vertices=8)
rod["frente_ok"] = True
key(rod, "location", F(t_stretch), (BX, .02, 6.0))
key(rod, "location", F(t_stretch + .7), (BX, .02, 4.4))
key(rod, "location", F(t_blow + .5), (BX, .02, 4.4))
key(rod, "location", F(t_blow + 1.0), (BX, .02, 6.0))
for o in flujo("aire_soplado", [(BX, .15, 3.9), (BX, .15, 1.8)], t_blow - .1, t_blow + .4, 10, material("aire_frio", (.9, .95, 1), alpha=.5, emit=1.5),
               (.06, .06, .12), period=.25, jitter=.25):
    o["frente_ok"] = True
frost = box("molde_frio", BX - 1.62, BX + 1.62, .0, .05, 1.2, 4.3, material("escarcha", (.5, .8, 1.0), alpha=.25, emit=1.0))
frost["frente_ok"] = True
show(frost, t_cool, t_out)
beat("entra_preforma", t_in + .6)
beat("estirar", t_stretch)
beat("soplar", t_blow)
beat("enfriar", t_cool)
beat("abrir_soplado", t_out)

# the finished bottle leaves the mold for the belt (a clean copy behind the cut, so the sliced one can vanish)
done = bottle("botella_lista", (BX, .5, 4.1))
show(done, t_out + .3)
show(blow, t_in, t_out + .3)
key(done, "location", F(t_out + .3), (BX, .5, 4.1))
key(done, "location", F(t_out + 1.0), (BX + 3.5, .5, 3.9))
unpop(done, S[11]["start"] + .2)

# ------------------------------------------------------------------ b11: inspection: cameras and an air jet
b11 = S[11]
IX0, IX1 = 19, 31
belt = box("banda_inspeccion", IX0, IX1 + 8, -.6, 1.4, 1.1, 1.3, DARK)
soporte("banda", IX0 + .5, IX1 + 7.5, 1.2, 1.1)
cam_box = box("camara_inspeccion", 24, 26, -.4, 1.6, 4.2, 5.0, MACHINE)
cut(cam_box, section)
lens = prim("cylinder", "lente_inspeccion", (25, .5, 4.1), (.3, .3, .15), DARK, vertices=16)
scan = box("escaneo", 24.6, 25.4, -.3, 1.3, 1.3, 4.1, GREEN)
scan["frente_ok"] = True
for j in range(6):
    show_t = b11["start"] + .6 + j * .9
    key(scan, "scale", F(show_t), (1, 1, 1))
show(scan, b11["start"] + .5, S[12]["start"])
line_b = [bottle(f"botella_banda{k}", (IX0, .5, 3.95)) for k in range(7)]
desfile(line_b, [(IX0, .5, 3.95), (IX1 + 6, .5, 3.95)], b11["start"], S[12]["start"] + 1.5, period=7)
bad = bottle("botella_mala", (23.8, .5, 3.95))
spot = prim("ico_sphere", "mancha", (0, -.42, -1.4), (.12, .05, .12), DARK, parent=bad, subdivisions=1)
t_reject = L("b11", 1)["start"] + .4
show(bad, b11["start"] + 1.0, S[12]["start"])
key(bad, "location", F(b11["start"] + 1.0), (21, .5, 3.95))
key(bad, "location", F(t_reject - .6), (25, .5, 3.95))
key(bad, "location", F(t_reject), (27.5, .5, 3.95))
key(bad, "location", F(t_reject + .5), (27.8, 2.6, 2.4))
key(bad, "rotation_euler", F(t_reject), (0, 0, 0))
key(bad, "rotation_euler", F(t_reject + .5), (math.radians(-70), 0, 0))
alarm = prim("ico_sphere", "luz_rechazo", (25, -.2, 5.2), (.18, .18, .18), REDL, subdivisions=1)
alarm["frente_ok"] = True
show(alarm, t_reject - .6, t_reject + .8)
nozzle = prim("cylinder", "boquilla_aire", (27.5, -.4, 3.4), (.12, .12, .4), STEEL, rot=(math.radians(90), 0, 0), vertices=8)
nozzle["frente_ok"] = True
for o in flujo("soplido", [(27.5, -.2, 3.4), (27.5, 1.8, 3.4)], t_reject - .1, t_reject + .4, 10, material("aire_chorro", (.95, .97, 1), alpha=.5, emit=1.5),
               (.05, .05, .05), period=.2, jitter=.2):
    o["frente_ok"] = True
bin_r = box("contenedor_rechazo", 26.8, 29, 2.0, 3.6, .05, 1.4, DARK)
beat("escaner", b11["start"] + .6)
beat("rechazo", t_reject)

# ------------------------------------------------------------------ b12: filler and capper
b12 = S[12]
FX = 34
frame_f = box("llenadora", FX - 3, FX + 3, -.4, 1.8, 5.0, 5.8, SS)
cut(frame_f, section)
for x in (FX - 3, FX + 3):
    box(f"llenadora_pilar{x}", x - .2, x + .2, 1.3, 1.7, .05, 5.0, SS)
t_fill = b12["start"] + .6
t_cap = L("b12", 0)["start"] + (L("b12", 0)["end"] - L("b12", 0)["start"]) * .62
for k in range(4):
    x = FX - 1.8 + k * 1.2
    b_ = bottle(f"botella_llenar{k}", (x, .5, 3.95))
    show(b_, b12["start"], S[13]["start"] + .3)
    liq = prim("cylinder", f"bebida{k}", (x, .5, 1.42), (.47, .47, .02), DRINK, vertices=24)
    liq["frente_ok"] = True
    key(liq, "scale", F(t_fill + k * .1), (.47, .47, .02))
    key(liq, "location", F(t_fill + k * .1), (x, .5, 1.42))
    key(liq, "scale", F(t_fill + 1.6 + k * .1), (.47, .47, 1.05))
    key(liq, "location", F(t_fill + 1.6 + k * .1), (x, .5, 2.45))
    show(liq, t_fill, S[13]["start"] + .3)
    nz = prim("cylinder", f"boquilla{k}", (x, .5, 4.9), (.1, .1, .35), STEEL, vertices=8)
    stream = prim("cylinder", f"chorro{k}", (x, .5, 3.1), (.05, .05, 1.5), DRINK, vertices=8)
    stream["frente_ok"] = True
    show(stream, t_fill + k * .1, t_fill + 1.6 + k * .1)
    cap = prim("cylinder", f"tapa{k}", (x, .5, 5.2), (.23, .23, .1), CAP, vertices=20)
    cap["frente_ok"] = True
    show(cap, t_cap - .4, S[13]["start"] + .3)
    key(cap, "location", F(t_cap - .3 + k * .08), (x, .5, 4.9))
    key(cap, "location", F(t_cap + .2 + k * .08), (x, .5, 4.15))
    key(cap, "rotation_euler", F(t_cap + .2 + k * .08), (0, 0, 0))
    key(cap, "rotation_euler", F(t_cap + .7 + k * .08), (0, 0, math.radians(540)))
beat("llenar", [t_fill, t_fill + 1.8])
beat("tapar", [t_cap + .2 + k * .08 for k in range(4)])

# ------------------------------------------------------------------ b13: label and pack; b14: recycle back to pellets
b13, b14 = S[13], S[14]
PX = 42
labeled, labels = [], []
for k in range(6):
    x, y = PX - .6 + (k % 3) * 1.05, .5 + (k // 3) * 1.05
    b_ = bottle(f"botella_final{k}", (x, y, 3.95), cap=True)
    lab = prim("cylinder", f"etiqueta{k}", (0, 0, -1.6), (.515, .515, .35), LABEL, parent=b_, vertices=28)
    key(lab, "scale", F(b13["start"] + .2 + k * .08), (.515, .515, .001))
    key(lab, "scale", F(b13["start"] + .6 + k * .08), (.515, .515, .35))
    show(b_, b13["start"])
    labeled.append(b_)
table = box("mesa_empaque", PX - 1.6, PX + 3, -.2, 2.6, 1.0, 1.3, DARK)
pack = box("empaque", PX - 1.2, PX + 2.7, .0, 2.1, 1.3, 1.31, material("plastico_empaque", (.9, .95, 1), alpha=.3), origin=(PX + .75, 1.05, 1.3))
pack["frente_ok"] = True
t_pack = L("b13", 0)["start"] + (L("b13", 0)["end"] - L("b13", 0)["start"]) * .55
key(pack, "scale", F(t_pack), (1, 1, 1))
key(pack, "scale", F(t_pack + .5), (1, 1, 280))  # the 1 cm sheet wraps up to 2.8 m of bottles
show(pack, t_pack)
beat("etiqueta", b13["start"] + .2)
beat("empacar", t_pack)

RX = 50
binr = box("bote_reciclaje", RX - 1, RX + 1, .3, 2.3, .05, 2.4, RECYC)
cut(binr, cutter(box("bote_hueco", RX - .85, RX + .85, .45, 2.15, .3, 2.6, None)))
used = bottle("botella_usada", (RX - 3, 1.3, 4.5), cap=True)
show(used, b14["start"])
key(used, "location", F(b14["start"] + .3), (RX - 3, 1.3, 4.5))
key(used, "location", F(b14["start"] + 1.1), (RX, 1.3, 2.6))
key(used, "rotation_euler", F(b14["start"] + .3), (0, 0, 0))
key(used, "rotation_euler", F(b14["start"] + 1.1), (0, math.radians(160), 0))
unpop(used, b14["start"] + 1.4)
shredder = box("trituradora", RX + 2, RX + 5, .3, 2.3, .05, 3.0, MACHINE)
for o in flujo("bolitas_recicladas", [(RX + 5.2, 1.3, 1.6), (RX + 6.5, 1.3, .4), (RX + 9, 1.3, .2)], b14["start"] + 1.8, UNTIL + 1, 30, PELLET,
               (.09, .09, .07), period=1.5, kind="cylinder", jitter=.3):
    o["frente_ok"] = True
beat("reciclar", b14["start"] + 1.1)
beat("bolitas_nuevas", b14["start"] + 1.8)

# ------------------------------------------------------------------ camera
camara()
shot(0, S[2]["start"], (-40, -8, 4.5), (-41, -7, 4.2), (-44.5, 2, 3.5), (-44.5, 2, 3.0), True)
shot(S[2]["start"], S[3]["start"], (-38.5, -4, 3.4), (-39, -3.5, 3.6), (-41, .6, 2.3), (-41, .6, 2.7), True)
shot(S[3]["start"], L("b3", 1)["start"], (-37.5, -4.5, 3.2), (-38, -4, 3.0), (-40, .4, 2.0), (-39, .3, 1.7), True)
shot(L("b3", 1)["start"], S[4]["start"], (-29, -11, 5.5), (-30, -10, 6), (-34, 0, 4.2), (-34, 0, 4.6), True)
shot(S[4]["start"], S[5]["start"], (-20, -12, 5), (-22, -11, 4.5), (-24, 0, 2.5), (-23, 0, 2.5), True)
shot(S[5]["start"], S[6]["start"], (-8.5, -8.5, 4.6), (-9, -8, 4.4), (-12, 0, 2.6), (-12, 0, 2.8), True)
shot(S[6]["start"], S[7]["start"], (-3.2, -3.4, 2.6), (-3.4, -3.0, 2.4), (-5, .3, 1.9), (-5, .3, 2.0), True)
shot(S[7]["start"], S[8]["start"], (-2.6, -6.5, 3.6), (-2.8, -6, 3.4), (-4.1, .3, 2.6), (-4.1, .3, 2.6), True)
shot(S[8]["start"], L("b8", 1)["start"], (9, -9, 4.6), (7, -8.5, 4.2), (5, 0, 2.5), (6, 0, 2.6), True)
shot(L("b8", 1)["start"], S[9]["start"], (5.5, -3.6, 4.2), (6.5, -3.4, 4.1), (6, .4, 3.1), (7, .4, 3.1), True)
shot(S[9]["start"], S[10]["start"], (19, -7.5, 4.0), (18.5, -6.8, 3.6), (16, 0, 2.9), (16, 0, 2.8), True)
shot(S[10]["start"], S[11]["start"], (18.4, -6.2, 3.4), (19.5, -7, 3.8), (16, 0, 2.8), (17.5, 0, 3.0), True)
shot(S[11]["start"], S[12]["start"], (29, -10, 5.6), (29.5, -9.5, 5.4), (25.5, .5, 3.4), (26.5, .5, 3.2), True)
shot(S[12]["start"], S[13]["start"], (37, -8.5, 5.2), (36.5, -8, 5.0), (34, .5, 3.6), (34, .5, 3.8), True)
shot(S[13]["start"], S[14]["start"], (46.5, -8, 5.5), (46, -7.5, 5.3), (43, 1, 3.0), (43, 1, 3.0), True)
shot(S[14]["start"], UNTIL + 1, (54, -8, 4.5), (6, -66, 38), (51, 1, 2), (0, 4, 3), True, lens=26)

terminar()
