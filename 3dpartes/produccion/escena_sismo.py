"""Earthquake-proof building episode (05-edificio-antisismico) on top of motor3d. The whole world shakes during
the quakes (everything on the ground is parented to the empty 'mundo'); the isolated building stays still above
its rubber pads. The cutaway at y=0 runs through the building's middle row of columns.

    blender -b --python escena_sismo.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar] [--rapido]"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motor3d import *  # noqa: E402,F401,F403

S = {k: SC[f"b{k}"] for k in range(1, 13)}
MUD = material("lodo", (.52, .40, .30))
variar(MUD, .5)
WAVE = material("onda", (1.0, .55, .15), alpha=.6, emit=2.0)
GLASSB = material("vidrio_edificio", (.55, .78, .95), rough=.05, alpha=.35)
COLC = material("concreto_columna", (.70, .70, .68), alpha=1.0)
RUBBER = material("hule", (.12, .12, .13), rough=.6)
LEAD = material("plomo", (.95, .55, .20), emit=.4)
DAMPM = material("amortiguador", (.95, .30, .10), emit=0.0)
RUST = material("varilla", (.62, .30, .16), rough=.5)
GAPM = material("junta", (1.0, .85, .15), emit=1.5)
section = seccion()
front = corte_frente()
COLS = [-5.5, 0.0, 5.5]

# ------------------------------------------------------------------ the shaking world
mundo = empty("mundo")
pit = cutter(box("corte_fosa", -8, 8, -8, 8, -2.6, 8, None))
pit.location = (500, 0, 0)
layers = suelo([("pasto", 0, -.15, GRASS), ("tierra", -.15, -.65, TOP), ("lodo", -.65, -14, MUD), ("roca", -14, -40, ROCKL)],
               {"pasto": [(pit, False)], "tierra": [(pit, False)], "lodo": [(pit, False)]})


def libre(x, y):
    return not (-20 < x < 22 and -14 < y < 20) and not (y < 2 and abs(x) < 60)


paisaje(libre, arboles=200, casas=[(random.choice((-1, 1)) * random.uniform(26, 60), random.uniform(4, 60)) for _ in range(14)])
for ob in list(sc.objects):  # everything on the ground shakes with it
    if ob.parent is None and ob not in (section, mundo, pit) and ob.type in ("MESH", "EMPTY") and ob.name != "sol":
        ob.parent = mundo
pit.parent = mundo
fault = box("falla", -400, 400, -60.4, -60, -.05, .02, CRACKM)
fault.rotation_euler.z = math.radians(25)
fault.parent = mundo
QUAKES = [(S[1]["start"] + .8, S[1]["end"] - .2, .22), (L("b2", 0)["start"] + 2.4, L("b2", 1)["end"], .55),
          (S[6]["start"] + 2.6, S[6]["end"] - .3, .32), (S[11]["start"] + .2, S[11]["end"] - .3, .6)]


def g(t):
    """Ground displacement in x at time t."""
    for a, b, amp in QUAKES:
        if a <= t <= b:
            env = min(1, (t - a) / .6) * min(1, (b - t) / .6)
            return amp * env * (math.sin(2 * math.pi * 1.7 * (t - a)) + .45 * math.sin(2 * math.pi * 3.3 * (t - a) + 1))
    return 0.0


for f in range(1, F(UNTIL) + 1, 2):
    key(mundo, "location", f, (g((f - 1) / FPS), 0, 0), interp="LINEAR")
quake_beats = [[round(a, 2), round(b, 2)] for a, b, _ in QUAKES]

# b1: seismic waves spreading from the epicentre
for wave in range(3):  # thin rings that appear one after another, moving outward from the epicentre
    for i in range(8):
        r = 6 + i * 7
        ring = prim("torus", f"onda{wave}_{i}", (-60, -40, .15), (1, 1, 1), WAVE, major_radius=r, minor_radius=.35, major_segments=64)
        ring["frente_ok"] = True
        t0 = S[1]["start"] + .4 + wave * .9 + i * .12
        show(ring, t0, t0 + .35)
beat("onda", S[1]["start"] + .5)


# ------------------------------------------------------------------ buildings
def edificio(prefix, levels, glass=True, col_mat=CONCRETE):
    """Slabs at each level and column segments between them, all cut by the section. Returns (slabs, columns)."""
    slabs, cols = [], []
    for i, z in enumerate(levels):
        sl = biselar(box(f"{prefix}_losa{i}", -6.6, 6.6, -6.6, 6.6, z - .3, z, CONCRETE, origin=(0, 0, z)), .04)
        cut(sl, section)
        slabs.append(sl)
    for i in range(len(levels) - 1):
        z0, z1 = levels[i], levels[i + 1] - .3
        row = []
        for x in COLS:
            for y in COLS:
                c = biselar(box(f"{prefix}_col{i}_{x}_{y}", x - .35, x + .35, y - .35, y + .35, z0, z1, col_mat, origin=(x, y, (z0 + z1) / 2)), .03)
                cut(c, section)
                row.append(c)
        cols.append(row)
        if glass:
            for nm, a, b, c_, d in (("n", -6.6, 6.6, 6.5, 6.6), ("e", 6.5, 6.6, -6.6, 6.6), ("o", -6.6, -6.5, -6.6, 6.6)):
                gl = box(f"{prefix}_vidrio{i}{nm}", a, b, c_, d, z0, z1, GLASSB)
                cut(gl, section)
                slabs[i + 1].children  # noqa: B018  (glass hangs from the slab above)
                gl.parent = slabs[i + 1]
                gl.location = (0, 0, -levels[i + 1])
    return slabs, cols


def move_building(slabs, cols, levels, f, drift, drop=None):
    """Keys every slab at x = drift(i) and tilts the column segments between them. drop(i) lowers slabs (collapse)."""
    xs = [drift(i) for i in range(len(levels))]
    dz = [drop(i) if drop else 0 for i in range(len(levels))]
    for i, sl in enumerate(slabs):
        key(sl, "location", f, (xs[i], 0, levels[i] + dz[i]), interp="LINEAR")
    for i, row in enumerate(cols):
        h = (levels[i + 1] - .3 + dz[i + 1]) - (levels[i] + dz[i])
        h0 = levels[i + 1] - .3 - levels[i]
        tilt = math.atan2(xs[i + 1] - xs[i], max(h, .2))
        for c, (x, y) in zip(row, [(x, y) for x in COLS for y in COLS]):
            key(c, "location", f, (x + (xs[i] + xs[i + 1]) / 2, y, levels[i] + dz[i] + h / 2), interp="LINEAR")
            key(c, "rotation_euler", f, (0, tilt, 0), interp="LINEAR")
            key(c, "scale", f, (1, 1, max(.05, h / h0)), interp="LINEAR")


# b2: a normal building whips and its ground floor snaps
b2 = S[2]
LV1 = [0, 3, 6, 9, 12, 15, 18]
s1, c1 = edificio("normal", LV1)
t_show, t_snap = b2["start"] + .2, L("b2", 1)["start"] + 1.4
for ob in s1 + [c for r in c1 for c in r]:
    pop(ob, t_show + (ob.location.z / 18) * .8, dur=.12, final=tuple(ob.scale))
    show(ob, None, S[3]["start"])
for f in range(F(t_show + 1.2), F(S[3]["start"]), 2):
    t = (f - 1) / FPS
    lag = [g(t)] + [g(t) - 3.2 * (i / 6) ** 1.3 * g(t - .28) for i in range(1, 7)]
    collapse = max(0.0, min(1.0, (t - t_snap) / .45))
    move_building(s1, c1, LV1, f, lambda i: lag[i] + (collapse * 3.4 * (i / 6) ** 1.5 if i else 0),
                  (lambda i: -2.55 * collapse if i >= 1 else 0))
for k, (x, z, r) in enumerate([(-5.5, 1.2, 30), (0, 1.8, -40), (5.5, 1.0, 60), (-5.5, 2.2, -20), (5.5, 2.0, 15)]):
    cr = prim("cube", f"grieta_col{k}", (x + .36, -.36, z), (.02, .4, .04), CRACKM, rot=(math.radians(r), 0, 0))
    cr["frente_ok"] = True
    pop(cr, t_snap - .5 + k * .08, dur=.08)
    show(cr, None, t_snap + .1)
dust = empty("polvo_colapso", (0, 0, 0))
vapor(dust, t_snap + .2, (-8, 8), (-6, 6), count=16, mat=DUST)
show(dust, t_snap + .2, S[3]["start"])
beat("edificio_normal", t_show)
beat("colapso", t_snap)

# ------------------------------------------------------------------ b3: pit and piles to rock
b3 = S[3]
d0, d1 = b3["start"] + .1, b3["start"] + .9
key(pit, "location", 1, (500, 0, 0), interp="CONSTANT")
key(pit, "location", F(d0) - 1, (500, 0, 0), interp="CONSTANT")
key(pit, "location", F(d0), (0, 0, 8))
key(pit, "location", F(d1), (0, 0, 0))
piles, pile_t = [], []
rig = empty("piloteadora", (0, 0, -2.6))  # sits behind each pile (+y) so it never pokes out in front of the cut
prim("cube", "pil_base", (0, 0, .6), (1.4, 1.5, .6), MACHINE, parent=rig)
prim("cube", "pil_mastil", (-1.5, -1.3, 7), (.25, .25, 7), MACHINE, parent=rig)
hammer = prim("cube", "pil_martillo", (-1.5, -1.8, 12), (.45, .45, .8), DARK, parent=rig)
cut(hammer, section)
aparecer(rig, d1)
order = [(x, y) for y in COLS for x in COLS]
span = (b3["end"] - .3 - d1) / len(order)
for k, (x, y) in enumerate(order):
    p = biselar(box(f"pilote{k}", x - .32, x + .32, y - .32, y + .32, -15.5, -2.6, CONCRETE, origin=(x, y, -2.6)), .03)
    p.parent = mundo
    cut(p, front)
    t = d1 + k * span
    key(p, "location", F(t), (x, y, 10.0))
    for j in range(3):
        key(p, "location", F(t + span * (j + 1) / 3), (x, y, -2.6 + 12.6 * (1 - (j + 1) / 3)), interp="LINEAR")
    show(p, t)
    key(rig, "location", F(t), (x + 1.5, y + 1.8 if y >= 0 else 60, -2.6), interp="CONSTANT")
    for j in range(3):
        key(hammer, "location", F(t + span * j / 3), (-1.5, -1.8, 11), interp="LINEAR")
        key(hammer, "location", F(t + span * (j + .7) / 3), (-1.5, -1.8, 13.5), interp="LINEAR")
    pile_t += [round(t + span * (j + 1) / 3, 3) for j in range(3)]
    piles.append(p)
unpop(rig, b3["end"] - .1, .05)
beat("excavar", [d0, d1])
beat("pilotes", pile_t)

# ------------------------------------------------------------------ b4: foundation mat
b4 = S[4]
mat_ = biselar(box("losa_cimentacion", -6.8, 6.8, -6.8, 6.8, -2.6, -1.6, CONCRETE, origin=(0, 0, -2.6)), .04)
mat_.parent = mundo
cut(mat_, section)
key(mat_, "scale", 1, (1, 1, .01), interp="CONSTANT")
key(mat_, "scale", F(b4["start"] + .3), (1, 1, .01))
key(mat_, "scale", F(b4["end"] - .6), (1, 1, 1))
show(mat_, b4["start"] + .3)
gravel_rain("colado", b4["start"] + .2, b4["end"] - 1.2, -1.8, CONCRETE, (.15, .25), 40, xs=(-6, 6), ys=(.2, 6))
beat("losa", [b4["start"] + .3, b4["end"] - .6])

# ------------------------------------------------------------------ b5: the real building floats above the mat
b5, b6 = S[5], S[6]
LV = [-.6, 2.4, 5.4, 8.4, 11.4, 14.4, 18.9]
s2, c2 = edificio("real", LV, glass=False, col_mat=COLC)
base = biselar(box("losa_base", -6.6, 6.6, -6.6, 6.6, -1.0, -.6, CONCRETE), .04)
cut(base, section)
t_b = b5["start"] + .1
for ob in s2 + [c for r in c2 for c in r] + [base]:
    pop(ob, t_b + (ob.location.z + 1) / 20 * 1.2, dur=.12, final=tuple(ob.scale))
gap_line = box("hueco_brillo", -6.8, 6.8, -.05, .0, -1.55, -1.05, GAPM)
gap_line["frente_ok"] = True
show(gap_line, b5["start"] + 1.6, b6["start"] + .4)
beat("edificio_real", t_b)

# ------------------------------------------------------------------ b6: base isolators (bend, building stays)
isolators, iso_t = [], []
for k, (x, y) in enumerate(order):
    iso = empty(f"aislador{k}", (x, y, -1.3))
    for j in range(5):
        prim("cylinder", f"ais_hule{k}_{j}", (0, 0, -.27 + j * .12), (.62, .62, .05), RUBBER, parent=iso, vertices=20)
        prim("cylinder", f"ais_placa{k}_{j}", (0, 0, -.21 + j * .12), (.64, .64, .012), STEEL, parent=iso, vertices=20)
    core = prim("cylinder", f"ais_plomo{k}", (0, 0, 0), (.16, .16, .29), LEAD, parent=iso, vertices=12)
    iso["capas"] = [c.name for c in iso.children if c is not core]
    for ch in iso.children:
        cut(ch, section)
    t = b6["start"] + .2 + k * .15
    pop(iso, t, dur=.12, final=(1, 1, 1))
    iso_t.append(round(t, 3))
    isolators.append((iso, x, y))


def isolator_keys(t0, t1):
    """Shear, not tilt: the bottom layer moves with the ground, the top stays with the building, layers step in between."""
    for f in range(F(t0), F(t1) + 1, 2):
        d = g((f - 1) / FPS)
        for iso, x, y in isolators:
            for ch in iso.children:
                z = ch.location.z
                u = (z + .29) / .58          # 0 at the bottom, 1 at the top
                if ch.name.startswith("ais_plomo"):
                    key(ch, "location", f, (d / 2, 0, 0), interp="LINEAR")
                    key(ch, "rotation_euler", f, (0, math.atan2(-d, .58), 0), interp="LINEAR")
                else:
                    key(ch, "location", f, (d * (1 - u), 0, z), interp="LINEAR")


isolator_keys(QUAKES[2][0] - .1, QUAKES[2][1] + .1)
beat("aisladores", iso_t)
beat("sismo_prueba", [QUAKES[2][0], QUAKES[2][1]])

# ------------------------------------------------------------------ b7: seismic gap around the base
b7 = S[7]
walls = []
for k, (a, b_, c, d) in enumerate([(-8, -7.6, -8, 8), (7.6, 8, -8, 8), (-8, 8, -8, -7.6), (-8, 8, 7.6, 8)]):
    w = biselar(box(f"muro_junta{k}", a, b_, c, d, -2.6, 0, CONCRETE, origin=((a + b_) / 2, (c + d) / 2, -2.6)), .03)
    w.parent = mundo
    cut(w, section)
    key(w, "scale", 1, (1, 1, .01), interp="CONSTANT")
    key(w, "scale", F(b7["start"] + .2 + k * .2), (1, 1, .01))
    key(w, "scale", F(b7["start"] + .7 + k * .2), (1, 1, 1))
    show(w, b7["start"] + .2 + k * .2)
gap_t = b7["start"] + 1.6
for k, (a, b_, c, d) in enumerate([(-7.6, -6.6, -7.6, 7.6), (6.6, 7.6, -7.6, 7.6), (-7.6, 7.6, 6.6, 7.6)]):
    gl = box(f"junta_brillo{k}", a, b_, c, d, -.05, .01, GAPM)
    gl.parent = mundo
    cut(gl, section)
    show(gl, gap_t + k * .15, S[8]["start"] + .3)
for k, x in enumerate((-7.1, 7.1)):
    a = empty(f"flecha_junta{k}", (x, -.5, .8))
    prim("cone", f"fj_a{k}", (-.3, 0, 0), (.2, .2, .3), GAPM, parent=a, rot=(0, math.radians(-90), 0), vertices=8)
    prim("cone", f"fj_b{k}", (.3, 0, 0), (.2, .2, .3), GAPM, parent=a, rot=(0, math.radians(90), 0), vertices=8)
    for ch in a.children:
        ch["frente_ok"] = True
    pop(a, gap_t + .3, final=(1, 1, 1))
    unpop(a, S[8]["start"] + .3)
beat("muros_junta", b7["start"] + .2)
beat("junta", gap_t)

# ------------------------------------------------------------------ b8: confinement ties inside a column (x-ray)
b8 = S[8]
xa, xb = b8["start"] + .1, b8["start"] + .6
alpha = COLC.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
try:
    COLC.surface_render_method = "BLENDED"
except AttributeError:
    COLC.blend_method = "BLEND"
for f, v in ((1, 1.0), (F(xa), 1.0), (F(xb), .18), (F(S[9]["start"] - .3), .18), (F(S[9]["start"] + .2), 1.0)):
    alpha.default_value = v
    alpha.keyframe_insert("default_value", frame=f)
tie_t = []
for x, y in ((0, 5.5), (5.5, 5.5), (-5.5, 5.5), (0, 0.0), (5.5, 0.0), (-5.5, 0.0)):
    for dx in (-.22, .22):
        for dy in (-.22, .22):
            bar = box(f"barra{x}{y}{dx}{dy}", x + dx - .03, x + dx + .03, y + dy - .03, y + dy + .03, -.6, 2.1, RUST)
            cut(bar, section)
            show(bar, xb - .1, S[9]["start"] + .2)
    for j in range(11):
        tie = prim("torus", f"estribo{x}{y}{j}", (x, y, -.4 + j * .24), (1, 1, 1), RUST, major_radius=.3, minor_radius=.025)
        tie.rotation_euler.z = math.radians(45)
        cut(tie, section)
        t = xb + .1 + j * .2
        pop(tie, t, dur=.08)
        show(tie, None, S[9]["start"] + .2)
        if x == 0 and y == 0 and j % 3 == 0:
            tie_t.append(round(t, 3))
beat("rayos_x", xa)
beat("estribos", tie_t)

# ------------------------------------------------------------------ b9: braces with dampers on the east face
b9 = S[9]
damp_t = []
for i in range(6):
    z0, z1 = LV[i], LV[i + 1] - .3
    for k, (ya, yb) in enumerate(((0.4, 5.1), (-5.1, -0.4))):
        if ya < 0:
            continue
        y_lo, y_hi = (ya, yb) if i % 2 == 0 else (yb, ya)
        mid = ((y_lo + y_hi) / 2, (z0 + z1) / 2)
        ln = math.hypot(y_hi - y_lo, z1 - z0)
        ang = math.atan2(y_hi - y_lo, z1 - z0)
        br = empty(f"riostra{i}{k}", (6.75, mid[0], mid[1]))
        br.rotation_euler.x = -ang
        prim("cylinder", f"riostra_barra{i}{k}", (0, 0, 0), (.09, .09, ln / 2), STEEL, parent=br, vertices=8)
        prim("cylinder", f"riostra_amort{i}{k}", (0, 0, 0), (.22, .22, ln * .16), DAMPM, parent=br, vertices=12)
        t = b9["start"] + .2 + i * .35
        pop(br, t, final=(1, 1, 1))
        damp_t.append(round(t, 3))
emis = DAMPM.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
DAMPM.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, .35, .05, 1)
emis.default_value = 0
emis.keyframe_insert("default_value", frame=1)
for f in range(F(S[11]["start"]), F(S[11]["end"]), 3):
    emis.default_value = 6 * min(1, abs(g((f - 1) / FPS)) / .4)
    emis.keyframe_insert("default_value", frame=f)
emis.default_value = 0
emis.keyframe_insert("default_value", frame=F(S[11]["end"]) + 6)
beat("amortiguadores", damp_t)

# ------------------------------------------------------------------ b10: tuned mass damper at the top
b10, b11 = S[10], S[11]
pivot = empty("pendulo", (0, 0, LV[6] - .3))
ball = prim("ico_sphere", "bola", (0, 0, -3.0), (1.5, 1.5, 1.5), STEEL, parent=pivot, subdivisions=3)
cut(ball, section)
for k, (cx, cy) in enumerate(((-.8, .6), (.8, .6), (-.8, 2.0), (.8, 2.0))):
    cab = prim("cylinder", f"cable{k}", (cx * .6, cy * .6, -1.0), (.03, .03, 1.0), DARK, parent=pivot, vertices=6)
t_ball = b10["start"] + .2
pop(pivot, t_ball, final=(1, 1, 1))
sway0, sway1 = b10["start"] + 2.4, b10["end"] - .2


def top_drift(t):
    if sway0 <= t <= sway1:
        env = min(1, (t - sway0) / .8) * min(1, (sway1 - t) / .8)
        return .35 * env * math.sin(2 * math.pi * .55 * (t - sway0))
    if b11["start"] <= t <= b11["end"]:
        return .06 * math.sin(2 * math.pi * .9 * (t - b11["start"]))
    return 0.0


for f in list(range(F(sway0) - 2, F(sway1) + 3, 2)) + list(range(F(b11["start"]) - 2, F(b11["end"]) + 3, 2)):
    t = (f - 1) / FPS
    d = top_drift(t)
    move_building(s2, c2, LV, f, lambda i: d * (i / 6) ** 1.2)
    key(pivot, "location", f, (d, 0, LV[6] - .3), interp="LINEAR")
    key(pivot, "rotation_euler", f, (0, math.radians(14) * (-d / .35) if sway0 <= t <= sway1 else math.radians(9) * math.sin(2 * math.pi * .9 * (t - b11["start"]) + math.pi), 0), interp="LINEAR")
beat("bola", t_ball)
beat("vaiven", [sway0, sway1])

# ------------------------------------------------------------------ b11: the big quake: ground moves, building stays
isolator_keys(QUAKES[3][0] - .1, QUAKES[3][1] + .1)
beat("sismo_final", [QUAKES[3][0], QUAKES[3][1]])

# ------------------------------------------------------------------ b12: windows, elevator, neighbours
b12 = S[12]
win_t = b12["start"] + .2
for i in range(6):
    z0, z1 = LV[i], LV[i + 1] - .3
    for nm, a, b_, c, d in (("n", -6.6, 6.6, 6.5, 6.6), ("e", 6.85, 6.95, -6.6, 6.6), ("o", -6.6, -6.5, -6.6, 6.6)):
        gl = box(f"ventana{i}{nm}", a, b_, c, d, z0, z1, GLASSB)
        cut(gl, section)
        show(gl, win_t + i * .12)
shaft = box("cubo_elevador", 2.2, 3.8, 2.2, 3.8, -.6, LV[6] - .3, GLASSB)
show(shaft, win_t + .8)
car = biselar(box("elevador", 2.3, 3.7, 2.3, 3.7, 0, 2.4, MACHINE, origin=(3, 3, 0)), .04)
car.location = (3, 3, -.6)
aparecer(car, win_t + .8)
for f in range(F(win_t + .8), F(UNTIL) + 1, 3):
    u = ((f - F(win_t + .8)) / FPS) % 6
    z = -.6 + (LV[5] - LV[0]) * (u / 3 if u < 3 else (6 - u) / 3)
    key(car, "location", f, (3, 3, z), interp="LINEAR")
people_t = b12["start"] + 1.4
for i in range(14):
    lvl = random.randint(0, 5)
    x, y = random.uniform(-5, 5), random.uniform(.8, 5.5)
    pp = persona(f"vecino{i}", (x, y, LV[lvl]))
    pop(pp, people_t + i * .08, final=(1, 1, 1))
    for f in range(F(people_t), F(UNTIL) + 1, 6):
        key(pp, "rotation_euler", f, (0, 0, math.sin(f * .05 + i) * .8), interp="LINEAR")
beat("ventanas", win_t)
beat("vecinos", people_t)
beat("sismos", quake_beats)

# ------------------------------------------------------------------ camera
camara()
shot(0, S[2]["start"], (44, -40, 22), (40, -36, 19), (-10, 0, 2), (0, 5, 3), False)
shot(S[2]["start"], S[3]["start"], (3, -34, 10), (2, -31, 9.5), (0, 0, 8.5), (0, 0, 7.5), False)
shot(S[3]["start"], S[4]["start"], (10, -32, 3), (8, -30, 2.5), (0, 5, -7), (0, 5, -7), True)
shot(S[4]["start"], S[5]["start"], (7, -22, 3), (6, -20, 2.5), (0, 4, -2.5), (0, 4, -2.5), True)
shot(S[5]["start"], S[6]["start"], (22, -26, 10), (20, -24, 9), (0, 3, 6), (0, 3, 5), True)
shot(S[6]["start"], S[7]["start"], (6, -12, 1.0), (5, -11, .95), (.5, 4, -1.6), (.5, 4, -1.6), True, lens=32)
shot(S[7]["start"], S[8]["start"], (18, -18, 15), (16, -16, 13), (0, 0, -.5), (0, 0, -.5), True)
shot(S[8]["start"], S[9]["start"], (3, -6, 1.8), (2.6, -5.4, 1.6), (0, 2, .8), (0, 2, .8), True)
shot(S[9]["start"], S[10]["start"], (24, -9, 9), (22, -8, 8.5), (5.5, 3, 7), (5.5, 3, 8), True)
shot(S[10]["start"], S[11]["start"], (10, -20, 20), (9, -18, 19), (0, 2, 16.5), (0, 2, 16.5), True)
shot(S[11]["start"], S[12]["start"], (15, -38, 9), (14, -36, 8.5), (0, 4, 5), (0, 4, 5), True)
shot(S[12]["start"], UNTIL + 1, (26, -30, 12), (70, -80, 45), (0, 0, 8), (0, 20, 8), False, lens=26)

terminar()
