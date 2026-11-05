"""'¿Cómo se hace?' episode 01 (frituras de maíz inflado) on top of motor3d. A production line runs along +x inside
a factory hall: mill, mixer, extruder, dryer, seasoning drum, multihead weigher and bagger. Every machine is
centred on y=0, so the cutaway shows inside it.

    blender -b --python escena_frituras.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar] [--rapido]"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motor3d import *  # noqa: E402,F401,F403

S = {k: SC[f"b{k}"] for k in range(1, 15)}
CORN = material("maiz", (1.0, .78, .12), rough=.4)
MEAL = material("semola", (.98, .88, .55))
DOUGH = material("masa", (.96, .80, .38), rough=.6)
PUFF = material("fritura", (.98, .86, .52), rough=.8)
PUFFC = material("fritura_queso", (1.0, .50, .08), rough=.8)
CHEESE = material("polvo_queso", (1.0, .55, .10), emit=.3)
OIL = material("aceite", (1.0, .80, .25), alpha=.6, emit=.3)
HOT = material("calor_horno", (1.0, .45, .10), emit=3.0)
BAND = material("resistencia", (.85, .15, .08), emit=1.5)
FLOOR = material("piso_fabrica", (.62, .64, .66), rough=.5)
variar(FLOOR, .15, .08)
WALLF = material("muro_fabrica", (.86, .88, .90))
SS = material("inoxidable", (.80, .82, .85), rough=.25)
BLUEM = material("motor", (.15, .35, .70), rough=.4)
FOIL = material("bolsa", (.95, .45, .10), rough=.3)
N2 = material("nitrogeno", (.55, .80, 1.0), alpha=.4, emit=.8)
STALE = material("rancia", (.55, .45, .30))
NEEDLE = material("aguja", (.95, .10, .10), emit=1.0)
section = seccion()
front = corte_frente()
Z = 2.5          # height of the extruder axis

# ------------------------------------------------------------------ ground, factory hall, landscape outside
hall = cutter(box("corte_nave", -52, 62, -14, 24, -.31, 1, None))
suelo([("pasto", 0, -.15, GRASS), ("tierra", -.15, -.65, TOP), ("subsuelo", -.65, -6, SUB), ("roca", -6, -40, ROCKL)],
      {"pasto": [(hall, True)], "tierra": [(hall, True)]})
floor = box("piso", -52, 62, -14, 24, -.3, .05, FLOOR)
cut(floor, section)
for nm, a, b, c, d in (("fondo", -52, 62, 22, 22.6), ("izq", -52, -51.4, -14, 22.6), ("der", 61.4, 62, -14, 22.6)):
    w = box(f"muro_{nm}", a, b, c, d, .05, 13, WALLF)
    cut(w, section)
for k in range(10):  # big windows in the back wall show the countryside outside
    x = -46 + k * 11
    box(f"ventanal{k}", x, x + 7, 21.9, 22.7, 4, 10, GLASS)
roof = box("techo_nave", -52, 62, -14, 22.6, 13.2, 13.5, WALLF)
cut(roof, section)
for k in range(9):  # big soft lights under the roof
    lt = link(bpy.data.objects.new(f"luz_nave{k}", bpy.data.lights.new(f"luz_nave{k}", "AREA")))
    lt.data.energy = 2200
    lt.data.size = 12
    lt.data.color = (1.0, .96, .9)
    lt.location = (-45 + k * 12.5, 3, 12.3)
for k in range(12):  # roof trusses and hanging lamps
    x = -48 + k * 10
    tr = box(f"viga{k}", x - .2, x + .2, -14, 22.6, 12.6, 13.2, STEEL)
    cut(tr, section)
    for y in (4, 14):
        lamp = prim("cone", f"lampara{k}_{y}", (x + 5, y, 11.2), (.7, .7, .4), DARK, vertices=10)
        bulb = prim("ico_sphere", f"foco{k}_{y}", (x + 5, y, 10.85), (.25, .25, .25), material(f"luz{k}{y}", (1, .95, .8), emit=4.0), subdivisions=1)
paisaje(lambda x, y: (y > 30 or x < -60 or x > 70) and not (y < 2 and abs(x) < 120), arboles=220,
        campos=[(-120, -70, 40, 90), (-60, 0, 40, 90), (10, 70, 40, 90), (80, 130, 40, 90)])


def soporte(name, x0, x1, y0, y1, h):
    """Four steel legs and a frame under a machine."""
    for x in (x0, x1):
        for y in (y0, y1):
            leg = box(f"{name}_pata{x}{y}", x - .12, x + .12, y - .12, y + .12, .05, h, STEEL)
            if y < 0:
                cut(leg, section)


# ------------------------------------------------------------------ b1: corn as hard as a rock
b1 = S[1]
pile = prim("ico_sphere", "monton_maiz", (-44, 3, 0), (4, 3, 1.6), CORN, subdivisions=2)
for i in range(40):
    prim("ico_sphere", f"grano{i}", (-44 + random.uniform(-3.5, 3.5), 3 + random.uniform(-2.5, 1), random.uniform(.3, 1.4)), (.18, .14, .22), CORN, subdivisions=1)
kern = prim("ico_sphere", "grano_prueba", (-41.5, .6, 1.25), (.32, .26, .38), CORN, subdivisions=1)
stand = box("yunque", -42.2, -40.8, .1, 1.1, .05, 1.0, STEEL)
hammer = empty("martillo", (-41.5, .6, 1.6))
prim("cube", "martillo_cabeza", (0, 0, .25), (.45, .22, .22), DARK, parent=hammer)
prim("cylinder", "martillo_mango", (.9, 0, .25), (.06, .06, .7), WOOD, parent=hammer, rot=(0, math.radians(90), 0), vertices=6)
t_hit = b1["start"] + 3.6
for f0, ang in ((F(b1["start"] + 2.6), 0), (F(t_hit - .35), -60), (F(t_hit), 0), (F(t_hit + .3), -25), (F(t_hit + .6), 0)):
    key(hammer, "rotation_euler", f0, (0, math.radians(ang), 0))
aparecer(hammer, b1["start"] + 2.5)
spark = prim("ico_sphere", "chispa_maiz", (-41.5, .2, 1.5), (.01, .01, .01), material("chispa", (1, .9, .4), emit=6), subdivisions=1)
key(spark, "scale", F(t_hit), (.01, .01, .01))
key(spark, "scale", F(t_hit + .08), (.5, .5, .5))
key(spark, "scale", F(t_hit + .3), (.01, .01, .01))
unpop(hammer, S[2]["start"] + .3)
beat("martillazo", t_hit)

# ------------------------------------------------------------------ b2: roller mill
b2 = S[2]
mill = empty("molino", (-38, 0, 0))
mill_body = box("molino_cuerpo", -40, -36, -1.4, 1.4, 1.5, 4.5, MACHINE)
mill_hole = cutter(box("molino_hueco", -39.3, -36.7, -1.6, 1.6, 2.4, 4.6, None))
cut(mill_body, mill_hole)
cut(mill_body, section)
hop = prim("cone", "molino_tolva", (-38, 0, 5.6), (1.8, 1.8, 1.1), SS, rot=(math.pi, 0, 0), vertices=10)
rolls = []
for k, x in enumerate((-38.55, -37.45)):
    r = prim("cylinder", f"rodillo_molino{k}", (x, 0, 3.4), (.5, .5, 1.3), STEEL, rot=(math.radians(90), 0, 0), vertices=18)
    cut(r, section)
    rolls.append(r)
    girar(r, 1, 12 if k == 0 else -12, b2["start"], S[4]["start"])
cut(hop, section)
soporte("molino", -39.8, -36.2, -1.2, 1.2, 1.5)
flujo("grano_cae", [(-38, -.1, 5.3), (-38, -.1, 3.9)], b2["start"] + .2, S[3]["start"] + .5, 18, CORN, (.12, .09, .14), period=.5, jitter=.25)
for o in [o for o in bpy.data.objects if o.name.startswith("grano_cae")]:
    o["frente_ok"] = True
flujo("semola_cae", [(-38, -.1, 2.9), (-38, -.1, 1.7), (-34, -.1, 1.7)], b2["start"] + .5, S[3]["start"] + .8, 30, MEAL, (.06, .06, .06), period=.8, jitter=.3)
for o in [o for o in bpy.data.objects if o.name.startswith("semola_cae")]:
    o["frente_ok"] = True
beat("molino", [b2["start"], S[3]["start"]])

# ------------------------------------------------------------------ b3: mixer with water
b3 = S[3]
tank = prim("cylinder", "mezcladora", (-30, 0, 3), (1.7, 1.7, 1.6), SS, vertices=24)
inner = prim("cylinder", "mezcladora_hueco", (-30, 0, 3.2), (1.55, 1.55, 1.6), None, vertices=24)
cutter(inner)
cut(tank, inner)
cut(tank, section)
soporte("mezcladora", -31.4, -28.6, -1.2, 1.2, 1.4)
shaft = empty("aspas", (-30, .3, 3))
prim("cylinder", "aspas_eje", (0, 0, .4), (.08, .08, 1.4), STEEL, parent=shaft, vertices=8)
for k in range(3):
    cut(prim("cube", f"aspa{k}", (0, 0, -.4 + k * .5), (1.2, .08, .12), STEEL, parent=shaft, rot=(0, 0, k * 1.0)), section)
girar(shaft, 2, 8, b3["start"], S[5]["start"])
dough_t = prim("cylinder", "masa_tanque", (-30, 0, 1.6), (1.5, 1.5, .01), DOUGH, vertices=24)
cut(dough_t, section)
key(dough_t, "scale", F(b3["start"] + .5), (1.5, 1.5, .01))
key(dough_t, "location", F(b3["start"] + .5), (-30, 0, 1.6))
key(dough_t, "scale", F(b3["end"] - .3), (1.5, 1.5, 1.1))
key(dough_t, "location", F(b3["end"] - .3), (-30, 0, 2.7))
show(dough_t, b3["start"] + .5)
pipe_w = prim("cylinder", "tubo_agua", (-30.8, 1.2, 5.4), (.12, .12, .9), STEEL, rot=(math.radians(90), 0, 0), vertices=8)
flujo("agua_cae", [(-30.8, -.1, 5.2), (-30.8, -.1, 3.2)], b3["start"] + .7, b3["end"] - .4, 14, WATER, (.07, .07, .11), period=.45, jitter=.05)
for o in [o for o in bpy.data.objects if o.name.startswith("agua_cae")]:
    o["frente_ok"] = True
beat("mezclar", [b3["start"], S[4]["start"]])
beat("agua", b3["start"] + .7)

# ------------------------------------------------------------------ b4: baked as it is: a hard flat cracker
b4 = S[4]
oven = box("horno_prueba", -25, -22.6, .4, 2.2, .05, 2.4, DARK)
door = box("horno_puerta", -25, -22.6, .3, .4, .4, 2.0, GLASS)
glow = box("horno_brillo", -24.8, -22.8, .5, 2.0, .3, 2.2, HOT)
show(glow, b4["start"] + .5, b4["start"] + 2.2)
tray = empty("charola", (-23.8, -1.0, 1.2))
prim("cube", "charola_base", (0, 0, 0), (.7, .5, .03), STEEL, parent=tray)
disc = prim("cylinder", "galleta", (0, 0, .08), (.45, .45, .05), DOUGH, parent=tray, vertices=16)
aparecer(tray, b4["start"] + .1)
key(tray, "location", F(b4["start"] + .2), (-23.8, -1.0, 1.2))
key(tray, "location", F(b4["start"] + .6), (-23.8, 1.2, 1.2))
key(tray, "location", F(b4["start"] + 2.2), (-23.8, 1.2, 1.2))
key(tray, "location", F(b4["start"] + 2.6), (-23.8, .7, 1.2))
burnt = material("galleta_dura", (.62, .42, .20))
disc.data.materials.append(burnt)
disc.active_material_index = 0
for f, v in ((1, 0), (F(b4["start"] + 2.1), 0), (F(b4["start"] + 2.2), 1)):
    disc.data.materials[0] = DOUGH
cracker = prim("cylinder", "galleta_dura", (0, 0, .08), (.45, .45, .04), burnt, parent=tray, vertices=16)
show(cracker, b4["start"] + 2.2, S[5]["start"])
show(disc, b4["start"] + .1, b4["start"] + 2.2)
unpop(tray, S[5]["start"])
beat("horno_prueba", [b4["start"] + .5, b4["start"] + 2.2])
beat("galleta", b4["start"] + 2.9)

# ------------------------------------------------------------------ b5-b8: the extruder
b5, b6, b7, b8 = S[5], S[6], S[7], S[8]
X0, X1 = -16, 2            # barrel from x0 to the die at x1
barrel = prim("cylinder", "barril", ((X0 + X1) / 2, 0, Z), (1.0, 1.0, (X1 - X0) / 2), SS, rot=(0, math.radians(90), 0), vertices=28)
bore = prim("cylinder", "barril_hueco", ((X0 + X1) / 2, 0, Z), (.82, .82, (X1 - X0) / 2 + .2), None, rot=(0, math.radians(90), 0), vertices=28)
cutter(bore)
cut(barrel, bore)
cut(barrel, section)
for k in range(5):
    band = prim("cylinder", f"banda{k}", (X0 + 2.5 + k * 3, 0, Z), (1.06, 1.06, .35), BAND, rot=(0, math.radians(90), 0), vertices=28)
    cut(band, bore)
    cut(band, section)
gear = box("motor_extrusor", X0 - 4, X0 - .4, -1.4, 1.4, 1.0, 4.0, BLUEM)
cut(gear, section)
soporte("extrusor", X0 + .5, X1 - .5, -.8, .8, Z - 1.0)
hop2 = prim("cone", "extrusor_tolva", (X0 + 1.5, 0, Z + 2.4), (1.2, 1.2, 1.0), SS, rot=(math.pi, 0, 0), vertices=12)
cut(hop2, section)
GOLD = material("tornillo_dorado", (.95, .72, .25), rough=.25)
screw = empty("tornillo", (X0 + .3, 0, Z))
prim("cylinder", "tornillo_eje", ((X1 - X0) / 2, 0, 0), (.25, .25, (X1 - X0) / 2 - .2), GOLD, parent=screw, rot=(0, math.radians(90), 0), vertices=12)
n_fl = 70
for k in range(n_fl):
    x = .3 + k * (X1 - X0 - .8) / n_fl
    fl = prim("cube", f"helice{k}", (x, 0, 0), (.05, .74, .1), GOLD, parent=screw, rot=(k * .55, 0, 0))
for ch in screw.children:
    cut(ch, section)
girar(screw, 0, -6, b5["start"], UNTIL + 1)
for o in flujo("masa_tubo", [(X0 + .8, -.05, Z), (X1 - .4, -.05, Z)], b5["start"] + .6, S[9]["start"], 46, DOUGH, (.26, .26, .26), period=2.6, grow=(1.2, .65), jitter=.45):
    cut(o, section)
die = prim("cylinder", "dado", (X1 + .1, 0, Z), (1.0, 1.0, .12), STEEL, rot=(0, math.radians(90), 0), vertices=28)
cut(die, section)
gauge = empty("manometro", (X1 - 2.5, 0, Z + 1.0))
prim("cylinder", "mano_tubo", (0, 0, .35), (.06, .06, .35), STEEL, parent=gauge, vertices=6)
prim("cylinder", "mano_caratula", (0, -.05, .95), (.42, .42, .06), WHITE, parent=gauge, rot=(math.radians(90), 0, 0), vertices=20)
needle = prim("cube", "mano_aguja", (0, -.13, .95), (.03, .02, .3), NEEDLE, parent=gauge)
for ch in gauge.children:
    ch["frente_ok"] = True
needle.rotation_euler.y = math.radians(-70)
key(needle, "rotation_euler", F(b6["start"] + .3), (0, math.radians(-70), 0))
key(needle, "rotation_euler", F(b6["start"] + 2.8), (0, math.radians(75), 0))
for f in range(F(b6["start"] + 2.8), F(b7["start"] + 1.2), 3):
    key(needle, "rotation_euler", f, (0, math.radians(75 + random.uniform(-3, 3)), 0))
key(needle, "rotation_euler", F(L("b7", 0)["end"] - .2), (0, math.radians(75), 0))
key(needle, "rotation_euler", F(L("b7", 0)["end"] + .2), (0, math.radians(-60), 0))
press = box("brillo_presion", X1 - 2.6, X1 - .2, -.02, 0, Z - .55, Z + .55, material("presion", (1, .25, .1), alpha=.22, emit=1.2))
press["frente_ok"] = True
show(press, b6["start"] + 1.2, L("b7", 0)["end"] - .1)
knife = empty("cuchilla", (X1 + .3, 0, Z))
for k in range(2):
    cut(prim("cube", f"cuchilla_hoja{k}", (0, 0, 0), (.05, 1.05, .08), STEEL, parent=knife, rot=(k * math.pi / 2, 0, 0)), section)
girar(knife, 0, 40, b5["start"], UNTIL + 1)
t_puff = L("b7", 0)["end"] - .3
belt1 = box("banda1", X1 + .6, 12, -.9, .9, 1.0, 1.15, DARK)
cut(belt1, section)
soporte("banda1", X1 + 1, 11.5, -.8, .8, 1.0)
for o in flujo("inflado", [(X1 + .35, -.2, Z), (X1 + 1.4, -.2, Z - .4), (X1 + 2.2, -.2, 1.35), (12, -.2, 1.35)], t_puff, S[10]["start"], 34, PUFF, (.17, .17, .34), period=2.4, grow=(.35, 1.0), jitter=.5):
    o["frente_ok"] = True
steam = empty("vapor_dado", (X1 + .6, 0, Z))
vapor(steam, t_puff, (0, .8), (-.6, .6), count=12, tam=.35)
show(steam, t_puff, S[10]["start"])
beat("extrusor", b5["start"])
beat("presion", b6["start"] + .3)
beat("expansion", t_puff)
beat("cuchilla", b8["start"] + .2)

# ------------------------------------------------------------------ b9: drying oven
b9 = S[9]
OV0, OV1 = 13, 27
oven2 = box("horno_secado", OV0, OV1, -1.8, 1.8, .9, 3.4, SS)
hollow = cutter(box("horno_hueco", OV0 - .5, OV1 + .5, -1.6, 1.6, 1.1, 3.2, None))
cut(oven2, hollow)
cut(oven2, section)
glow2 = box("horno_resistencias", OV0 + .2, OV1 - .2, -1.5, 1.5, 3.0, 3.15, HOT)
cut(glow2, section)
show(glow2, b9["start"] + .4)
belt2 = box("banda2", 12, OV1 + 1.5, -1.0, 1.0, 1.2, 1.32, DARK)
cut(belt2, section)
soporte("horno", OV0 + .5, OV1 - .5, -1.6, 1.6, .9)
for k in range(3):
    ch_ = prim("cylinder", f"chimenea{k}", (OV0 + 3 + k * 4, .5, 4.4), (.3, .3, 1.0), SS, vertices=10)
    v = empty(f"vapor_chimenea{k}", (OV0 + 3 + k * 4, .5, 5.0))
    vapor(v, b9["start"] + 1.0, (-.3, .3), (-.3, .3), count=6, tam=.4)
    show(v, b9["start"] + 1.0)
for o in flujo("secando", [(12, -.25, 1.5), (OV1 + 1.4, -.25, 1.5)], b9["start"] + .1, S[11]["start"] + 1.0, 60, PUFF, (.17, .17, .34), period=4.5, jitter=.7):
    o["frente_ok"] = True
beat("horno", [b9["start"] + .4, b9["end"]])

# ------------------------------------------------------------------ b10: powder alone slides off
b10 = S[10]
plate = empty("plato_prueba", (29.6, -.6, 1.4))
prim("cylinder", "plato", (0, 0, 0), (.9, .9, .04), WHITE, parent=plate, vertices=20)
for k in range(5):
    prim("ico_sphere", f"plato_fritura{k}", (random.uniform(-.5, .5), random.uniform(-.4, .4), .18), (.16, .16, .32), PUFF, parent=plate,
         rot=(0, math.radians(80), random.uniform(0, 3)), subdivisions=1)
pop(plate, b10["start"] + .2, final=(1, 1, 1))
for o in flujo("queso_resbala", [(29.6, -.7, 2.6), (29.6, -.7, 1.6), (30.3, -.7, 1.4), (30.6, -.7, .1)], b10["start"] + 1.6, S[11]["start"] + .3, 30, CHEESE, (.05, .05, .05), period=1.1, jitter=.4):
    o["frente_ok"] = True
heap = prim("cone", "polvo_piso", (30.6, -.4, .05), (.01, .01, .01), CHEESE, vertices=10)
key(heap, "scale", F(b10["start"] + 2.4), (.01, .01, .01))
key(heap, "scale", F(b10["end"]), (.5, .5, .15))
unpop(plate, S[11]["start"] + .3)
unpop(heap, S[11]["start"] + .3)
beat("queso_cae", b10["start"] + 1.6)

# ------------------------------------------------------------------ b11: seasoning drum
b11 = S[11]
DR0, DR1 = 30, 37
drum = prim("cylinder", "tambor", ((DR0 + DR1) / 2, 0, 2.6), (1.6, 1.6, (DR1 - DR0) / 2), SS, rot=(0, math.radians(92), 0), vertices=28)
dbore = prim("cylinder", "tambor_hueco", ((DR0 + DR1) / 2, 0, 2.6), (1.45, 1.45, (DR1 - DR0) / 2 + .3), None, rot=(0, math.radians(92), 0), vertices=28)
cutter(dbore)
cut(drum, dbore)
cut(drum, section)
girar(drum, 0, 2.5, 0, UNTIL + 1)
for x in (DR0 + .8, DR1 - .8):
    for y in (-1.2, 1.2):
        r = prim("cylinder", f"tambor_rueda{x}{y}", (x, y, 1.0), (.3, .3, .2), DARK, rot=(0, math.radians(90), 0), vertices=10)
        if y < 0:
            cut(r, section)
soporte("tambor", DR0 + .8, DR1 - .8, -1.2, 1.2, .9)
tumble = []
for i in range(34):  # puffs tumbling inside the turning drum
    p = prim("ico_sphere", f"volteo{i}", (DR0 + 1, .3, 2), (.17, .17, .34), PUFF, subdivisions=1)
    p["frente_ok"] = True
    a0, x = random.uniform(0, 6.28), random.uniform(DR0 + .8, DR1 - .8)
    for f in range(F(b11["start"]), F(S[12]["start"]) + 1, 3):
        t = (f - 1) / FPS
        a = a0 + t * 2.5
        r = .9 + .3 * math.sin(a * 1.7 + i)
        key(p, "location", f, (x + (t - b11["start"]) * .25 % 1.0, -.25, 2.6 - abs(r * math.cos(a)) * .9), interp="LINEAR")
        key(p, "rotation_euler", f, (a * 2, a, 0), interp="LINEAR")
    show(p, b11["start"], S[12]["start"])
    tumble.append(p)
t_oil, t_cheese = b11["start"] + 1.0, b11["start"] + 3.0
nozzle = box("rociador_aceite", DR0 + .5, DR1 - .5, -.1, .1, 3.5, 3.65, STEEL)
cut(nozzle, section)
for o in flujo("aceite", [(DR0 + 3, -.3, 3.4), (DR0 + 3, -.3, 2.2)], t_oil, t_cheese + .6, 20, OIL, (.05, .05, .09), period=.4, jitter=2.0):
    o["frente_ok"] = True
hop3 = prim("cone", "tolva_queso", (DR0 + 3.5, 0, 5.2), (1.0, 1.0, .9), FOIL, rot=(math.pi, 0, 0), vertices=10)
cut(hop3, section)
for o in flujo("lluvia_queso", [(DR0 + 3.5, -.3, 4.4), (DR0 + 3.5, -.3, 2.0)], t_cheese, S[12]["start"], 50, CHEESE, (.05, .05, .05), period=.6, jitter=1.6):
    o["frente_ok"] = True
orange_mix = [(f, 0.0) for f in (1, F(t_cheese + .4))] + [(F(t_cheese + 2.0), 1.0)]
mixn = PUFF.node_tree.nodes.new("ShaderNodeMix")
mixn.data_type = "RGBA"
mixn.inputs["A"].default_value = tuple(PUFF.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value)
mixn.inputs["B"].default_value = tuple(PUFFC.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value)
PUFF.node_tree.links.new(mixn.outputs["Result"], PUFF.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
for f, v in orange_mix:  # every puff turns orange as the cheese sticks (none of the plain ones are on screen after)
    mixn.inputs["Factor"].default_value = v
    mixn.inputs["Factor"].keyframe_insert("default_value", frame=f)
belt3 = box("banda3", DR1 + .5, 41, -.9, .9, 1.0, 1.12, DARK)
cut(belt3, section)
for o in flujo("sazonadas", [(DR1 + .6, -.2, 1.3), (41, -.2, 1.3), (42, -.2, 6.4)], t_cheese + 1.2, S[13]["start"] + 1.0, 30, PUFFC, (.17, .17, .34), period=2.2, jitter=.4):
    o["frente_ok"] = True
beat("tambor", b11["start"])
beat("aceite", t_oil)
beat("queso", t_cheese)

# ------------------------------------------------------------------ b12: multihead weigher; b13: nitrogen bag
b12, b13 = S[12], S[13]
WX = 44
tower = box("bascula_torre", WX - 2.2, WX + 2.2, -2.2, 2.2, .05, 4.2, MACHINE)
cut(tower, section)
cone = prim("cone", "bascula_cono", (WX, 0, 7.4), (1.2, 1.2, .6), SS, vertices=14)
cut(cone, section)
buckets = []
for k in range(10):
    a = k * 2 * math.pi / 10
    bk = empty(f"cubeta{k}", (WX + 2.0 * math.cos(a), 2.0 * math.sin(a), 6.2))
    bk.rotation_euler.z = a
    prim("cube", f"cubeta_caja{k}", (0, 0, 0), (.45, .38, .45), SS, parent=bk)
    flap = prim("cube", f"cubeta_tapa{k}", (-.45, 0, -.45), (.05, .38, .3), STEEL, parent=bk)
    if bk.location.y < .6:
        for ch in bk.children:
            cut(ch, section)
    buckets.append((bk, flap))
chosen = [0, 3, 6, 8]
for j, k in enumerate(chosen):
    bk, flap = buckets[k]
    t = b12["start"] + 2.0 + j * .1
    key(flap, "rotation_euler", F(t), (0, 0, 0))
    key(flap, "rotation_euler", F(t + .15), (0, math.radians(-70), 0))
    key(flap, "rotation_euler", F(t + .9), (0, math.radians(-70), 0))
    key(flap, "rotation_euler", F(t + 1.1), (0, 0, 0))
    glowb = prim("cube", f"cubeta_luz{k}", tuple(bk.location + Vector((0, 0, .6))), (.2, .2, .05), material(f"verde{k}", (.2, 1, .3), emit=3), )
    show(glowb, b12["start"] + 1.3, t + 1.0)
for o in flujo("porcion", [(WX, -.2, 5.6), (WX, -.2, 3.4)], b12["start"] + 2.1, S[13]["start"] + .5, 26, PUFFC, (.15, .15, .3), period=.5, jitter=.5):
    o["frente_ok"] = True
bag = empty("bolsa", (WX, -.3, 2.2))
bag_body = prim("cube", "bolsa_cuerpo", (0, 0, 0), (.75, .25, .9), FOIL, parent=bag)
bag["frente_ok"] = True
bag_body["frente_ok"] = True
key(bag, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(bag, "scale", F(b12["start"] + 2.0) - 1, (0, 0, 0), interp="CONSTANT")
key(bag, "scale", F(b12["start"] + 2.0), (1, .35, 1))
key(bag, "scale", F(b12["end"]), (1, .35, 1))
stale_bag = empty("bolsa_aplastada", (WX + 4.5, -.8, 1.2))
sb = prim("cube", "bolsa_aplastada_cuerpo", (0, 0, 0), (.75, .2, .9), FOIL, parent=stale_bag)
for k in range(4):
    prim("ico_sphere", f"rancia{k}", (random.uniform(-.4, .4), -.25, random.uniform(-.5, .5)), (.15, .15, .28), STALE, parent=stale_bag, subdivisions=1)
weight = box("pesa", WX + 3.7, WX + 5.3, -1.1, -.5, 4, 4.8, DARK, origin=(WX + 4.5, -.8, 4))
for ch in stale_bag.children:
    ch["frente_ok"] = True
weight["frente_ok"] = True
t_crush = b13["start"] + 1.6
aparecer(stale_bag, b13["start"] + .1)
aparecer(weight, b13["start"] + .9)
key(weight, "location", F(t_crush - .3), (WX + 4.5, -.8, 4))
key(weight, "location", F(t_crush), (WX + 4.5, -.8, 1.6))
key(stale_bag, "scale", F(t_crush), (1, 1, 1))
key(stale_bag, "scale", F(t_crush + .15), (1.3, 1, .35))
unpop(stale_bag, L("b13", 1)["start"])
unpop(weight, L("b13", 1)["start"])
tank2 = prim("cylinder", "tanque_n2", (WX + 3, 1.2, 1.6), (.5, .5, 1.6), material("tanque_verde", (.2, .55, .35)), vertices=14)
t_n2 = L("b13", 1)["start"] + .3
for o in flujo("n2", [(WX + 2.6, -.4, 2.6), (WX + .4, -.4, 2.4)], t_n2, S[14]["start"], 16, N2, (.16, .16, .16), period=.6, jitter=.15):
    o["frente_ok"] = True
key(bag, "scale", F(t_n2), (1, .35, 1))
key(bag, "scale", F(t_n2 + 1.6), (1, 1.15, 1))
seal = box("sello", WX - .9, WX + .9, -.75, -.6, 3.05, 3.2, STEEL)
seal["frente_ok"] = True
show(seal, t_n2 + 1.7, S[14]["start"] + .5)
key(bag, "location", F(S[14]["start"] - .2), (WX, -.3, 2.2))
key(bag, "location", F(S[14]["start"] + .6), (WX + 6, -.3, 1.6))
belt4 = box("banda4", WX + 1, WX + 12, -.9, .9, .9, 1.02, DARK)
cut(belt4, section)
beat("bascula", b12["start"] + 2.0)
beat("aplastar", t_crush)
beat("nitrogeno", t_n2)
beat("sellar", t_n2 + 1.7)

# ------------------------------------------------------------------ b14: orange fingers
b14 = S[14]
eater = persona("comensal", (WX + 8, 1.2, .05))
eater.rotation_euler.z = math.radians(200)
hand = prim("ico_sphere", "mano_naranja", (WX + 7.8, .9, 1.55), (.13, .13, .13), CHEESE, subdivisions=1)
hand["frente_ok"] = True
pop(eater, b14["start"] + .2, final=(1, 1, 1))
pop(hand, b14["start"] + 1.2, dur=.15)
for f in range(F(b14["start"] + 1.4), F(UNTIL) + 1, 6):
    key(hand, "location", f, (WX + 7.8, .9, 1.55 + .2 * math.sin(f * .3)), interp="LINEAR")
beat("dedos", b14["start"] + 1.2)

# ------------------------------------------------------------------ camera
camara()
shot(0, S[2]["start"], (-36, -9, 3.6), (-37.5, -7, 2.8), (-42, 2, 1.4), (-41.5, 1, 1.3), True)
shot(S[2]["start"], S[3]["start"], (-33, -9, 4.6), (-34, -8, 4.2), (-38, 0, 3.4), (-38, 0, 3.2), True)
shot(S[3]["start"], S[4]["start"], (-25.5, -8.5, 4.6), (-26.5, -8, 4.2), (-30, 0, 2.8), (-30, 0, 2.8), True)
shot(S[4]["start"], S[5]["start"], (-20.5, -5.5, 2.6), (-21, -5, 2.4), (-23.8, 0, 1.4), (-23.8, 0, 1.4), True)
shot(S[5]["start"], S[6]["start"], (-2, -15, 5), (-4, -14, 4.6), (-7, 0, 2.5), (-6, 0, 2.5), True)
shot(S[6]["start"], S[7]["start"], (1.5, -6.5, 3.8), (1, -6, 3.6), (-1.5, 0, 2.8), (-1.2, 0, 2.8), True)
shot(S[7]["start"], S[8]["start"], (6, -5.5, 3.2), (5.4, -5, 3.0), (2.8, 0, 2.3), (3.2, 0, 2.0), True)
shot(S[8]["start"], S[9]["start"], (4.6, -3.6, 2.9), (4.4, -3.4, 2.8), (2.4, 0, 2.5), (2.4, 0, 2.5), True)
shot(S[9]["start"], S[10]["start"], (14, -13, 6), (24, -12, 5.5), (16, 0, 2), (25, 0, 2), True)
shot(S[10]["start"], S[11]["start"], (31.8, -5.2, 2.8), (31.4, -4.8, 2.6), (29.8, 0, 1.5), (29.8, 0, 1.4), True)
shot(S[11]["start"], S[12]["start"], (37, -10.5, 4.6), (36, -10, 4.4), (33.5, 0, 2.6), (33.5, 0, 2.6), True)
shot(S[12]["start"], S[13]["start"], (49, -14, 8), (48, -13, 7.6), (44, 0, 5), (44, 0, 5), True)
shot(S[13]["start"], S[14]["start"], (48.5, -7.5, 2.8), (48, -7, 2.7), (45.5, 0, 1.9), (45.5, 0, 1.9), True)
shot(S[14]["start"], UNTIL + 1, (54, -7, 3), (12, -64, 38), (51, 0, 1.6), (0, 4, 3), True, lens=26)

terminar()
