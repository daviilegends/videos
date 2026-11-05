"""Road episode (01-carretera) on top of motor3d: the road runs north, bends right and goes on to a village.
The ground is a wide landscape of soil layers, so the cutaway shots slice a real place.

    blender -b --python escena_carretera.py -- <carpeta_episodio> <segundos_hasta> [--cuadros 2,10.5 | --guardar]"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motor3d import *  # noqa: E402,F401,F403

# ------------------------------------------------------------------ road path
S1, R = 190.0, 35.0                    # straight from y=-150 to y=40, then a right curve of radius 35
S2 = S1 + R * math.pi / 2
END = S2 + 265.0                       # second straight runs east past the village
TAN_BANK = math.tan(math.radians(5))
HW_TOP = 5.6                           # half-width of the subbase top; crown and bank are measured from it
CROWN = .15
CREEK_Y = 18.0


def path(s):
    if s <= S1:
        return (0.0, -150 + s), (0.0, 1.0)
    if s <= S2:
        p = (s - S1) / R
        return (R - R * math.cos(p), 40 + R * math.sin(p)), (math.sin(p), math.cos(p))
    return (R + (s - S2), 40 + R), (1.0, 0.0)


def bank_w(s):
    if s < S1 - 15 or s > S2 + 15:
        return 0.0
    if s < S1:
        return (s - S1 + 15) / 15
    if s > S2:
        return 1 - (s - S2) / 15
    return 1.0


def crown_dz(o):
    return CROWN * max(0.0, 1 - abs(o) / HW_TOP)


def bank_dz(o, s):
    return (HW_TOP - o) * TAN_BANK * bank_w(s)


def world_pt(s, o, z):
    (x, y), (tx, ty) = path(s)
    return (x + o * ty, y - o * tx, z)


def samples(s0, s1):
    out, s = [], s0
    while s < s1 - 1e-6:
        out.append(s)
        s += 8 if s < S1 - 18 else (10 if s > S2 + 18 else 1.5)
    return out + [s1]


def sweep(name, profile, s0, s1, mat, keys=False, static=None, zorigin=0.0):
    """Road layer along the path. flags: c follows the crown, b follows the bank. keys=True animates both as shape keys;
    static=(crown, bank) bakes them in."""
    deform = {"bombeo": lambda o, s, fl: crown_dz(o) * ("c" in fl), "peralte": lambda o, s, fl: bank_dz(o, s) * ("b" in fl)}
    baked = None
    if static:
        baked = {"bombeo": lambda o, s, fl: static[0] * crown_dz(o) * ("c" in fl), "peralte": lambda o, s, fl: static[1] * bank_dz(o, s) * ("b" in fl)}
    return sweep_path(name, profile, samples(s0, s1), world_pt, mat, deforms=deform if keys else None, static=baked, zorigin=zorigin)


# ------------------------------------------------------------------ section cutter (y < 0 in cutaway shots)
section = seccion()

# ------------------------------------------------------------------ static cutters
X0, X1, Y0, Y1 = -400, 400, -400, 600
creek_cut = cutter(mesh_object("corte_arroyo", [(x, y, z) for x in (X0 - 5, X1 + 5) for (y, z) in
                                                ((CREEK_Y - 1.2, -1.6), (CREEK_Y + 1.2, -1.6), (CREEK_Y + 1.9, .6), (CREEK_Y - 1.9, .6))],
                               [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], None))
zone_prof = [(-6.45, -.92, ""), (6.45, -.92, ""), (6.45, -.62, ""), (-6.45, -.62, "")]
zone_cut = cutter(sweep("corte_zona_subrasante", zone_prof, 0, END, None))
strip_prof = [(-6.45, -.62, ""), (6.45, -.62, ""), (7.3, .6, ""), (-7.3, .6, "")]
strip_rest = cutter(sweep("corte_despalme_resto", strip_prof, S1 - 6, END, None))
strip_rest.location.z = -50                                   # parked underground until the dozer has gone
strip_main = cutter(box("corte_despalme", -7.3, 7.3, -150, S1 - 150, -.62, .6, None, origin=(0, -150, 0)))
ditch_prof = [(o, z, "") for o, z in ((-1.1, .4), (1.1, .4), (0, -.85))]
ditches = []
for side in (-1, 1):
    d = cutter(sweep(f"corte_cuneta{side}", [(side * 8.3 + o, z, f) for o, z, f in ditch_prof], 0, END, None))
    d.location.z = 1.4
    ditches.append(d)

# ------------------------------------------------------------------ ground: soil layers inside a large landscape
ground = []
for name, z1, z0, mat in (("pasto", 0, -.15, GRASS), ("tierra", -.15, -.65, TOP), ("subsuelo", -.65, -3.0, SUB), ("roca", -3.0, -40, ROCKL)):
    ob = box(f"capa_{name}", X0, X1, Y0, Y1, z0, z1, mat)
    if name != "roca":
        cut(ob, creek_cut, apply=True)
    if name in ("tierra", "subsuelo"):
        cut(ob, zone_cut, apply=True)
    if name in ("pasto", "tierra"):
        cut(ob, strip_main)
        cut(ob, strip_rest)
    if name != "roca":
        for d in ditches:
            cut(ob, d)
    cut(ob, section)
    ground.append(ob)
for i, (a, b, c, d) in enumerate([(-5000, 5000, Y1, 5000), (-5000, 5000, -5000, Y0), (-5000, X0, Y0, Y1), (X1, 5000, Y0, Y1)]):
    cut(box(f"llanura{i}", a, b, c, d, -1.0, -.03, GRASS2), section)  # the plain around the soil block, never inside it
for i in range(40):  # stones in the cut face
    x, z = random.uniform(-12, 12), random.uniform(-8, -1.1)
    s = random.uniform(.1, .25)
    st = prim("ico_sphere", f"piedra{i}", (x, random.uniform(-.1, .1), z), (s, s * .7, s * .8), ROCKL, subdivisions=1)
    cut(st, section)

# creek: water box that rises with the flood, with a moving texture so it flows
agua_animada(WATER)
creek_water = box("arroyo", X0, X1, CREEK_Y - 1.25, CREEK_Y + 1.25, -1.6, -1.32, WATER, origin=(0, 0, -1.6))
vado = box("vado", -7.2, 7.2, CREEK_Y - 1.95, CREEK_Y + 1.95, -1.7, -.92, SUB)
vado_tubo = box("vado_tubo", -7.2, 7.2, CREEK_Y - 1.95, CREEK_Y + 1.95, -1.7, -.92, SUB)

# ------------------------------------------------------------------ road layers
dirt = sweep("camino_tierra", [(-3.0, -.12, ""), (3.0, -.12, ""), (2.7, .02, ""), (-2.7, .02, "")], 0, END, DIRT)
for c in (creek_cut, strip_main, strip_rest, section):
    cut(dirt, c)

washout = cutter(box("corte_deslave", -7, 7, CREEK_Y - 1.95, CREEK_Y + 1.95, -.95, -.61, None))
washout.location.z = -50
SUBG_RAW = material("subrasante_suelta", (.60, .40, .22))
subg_raw = box("subrasante_suelta", -6.45, 6.45, -150, S1 - 150, -.92, -.62, SUBG_RAW, origin=(0, S1 - 150, 0))
subg_main = box("subrasante", -6.45, 6.45, -150, S1 - 150, -.92, -.62, SUBGRADE, origin=(0, -150, 0))
subg_rest = sweep("subrasante_resto", zone_prof, S1, END, SUBGRADE)
subg_patch = box("subrasante_parche", -6.45, 6.45, CREEK_Y - 1.95, CREEK_Y + 1.95, -.92, -.62, SUBGRADE)
for ob in (subg_raw, subg_main):
    cut(ob, washout)
for ob in (subg_raw, subg_main, subg_rest, subg_patch, vado, vado_tubo):
    cut(ob, section)

subbase = sweep("subbase", [(-5.9, -.62, ""), (5.9, -.62, ""), (5.6, -.17, "cb"), (0, -.17, "cb"), (-5.6, -.17, "cb")], 0, END, SUBBASE, keys=True, zorigin=-.62)
base = sweep("base", [(-5.6, -.17, "cb"), (0, -.17, "cb"), (5.6, -.17, "cb"), (5.3, .13, "cb"), (0, .13, "cb"), (-5.3, .13, "cb")], 0, END, BASE, keys=True, zorigin=-.17)
prime_p = [(-5.3, .13, "cb"), (0, .13, "cb"), (5.3, .13, "cb"), (5.3, .165, "cb"), (0, .165, "cb"), (-5.3, .165, "cb")]
asph_p = [(-5.3, .165, "cb"), (0, .165, "cb"), (5.3, .165, "cb"), (5.0, .38, "cb"), (0, .38, "cb"), (-5.0, .38, "cb")]
prime_main, prime_rest = sweep("riego", prime_p, 0, S1, PRIME, keys=True), sweep("riego_resto", prime_p, S1, END, PRIME, keys=True)
asph_main, asph_rest = sweep("asfalto", asph_p, 0, S1, ASPHALT, keys=True), sweep("asfalto_resto", asph_p, S1, END, ASPHALT, keys=True)
prime_cut = cutter(box("corte_riego", -8, 8, 0, 400, -1, 2, None))
asph_cut = cutter(box("corte_asfalto", -8, 8, 0, 400, -1, 2, None))
cut(prime_main, prime_cut)
cut(asph_main, asph_cut)
road_layers = [subbase, base, prime_main, prime_rest, asph_main, asph_rest]
for ob in road_layers:
    cut(ob, section)


def road_key(name, ob, frame, value):
    kb = ob.data.shape_keys.key_blocks[name]
    kb.value = value
    kb.keyframe_insert("value", frame=frame)


def surface(o, s, crown=1.0, bank=1.0, top=.38):
    return top + crown * crown_dz(o) + bank * bank_dz(o, s)


# ------------------------------------------------------------------ landscape context
path_pts = [path(s)[0] for s in range(0, int(END), 4)]


def far_from_road(x, y, d):
    return all((x - px) ** 2 + (y - py) ** 2 > d * d for px, py in path_pts)


def libre(x, y):
    return (not (y < 2 and abs(x) < 30) and abs(y - CREEK_Y) >= 3 and far_from_road(x, y, 13)
            and not (90 < x < 230 and 55 < y < 100) and not (18 < x < 90 and -70 < y < 12))


paisaje(libre, casas=[(95 + i * 10 + random.uniform(-2, 2), 75 + random.choice((-1, 1)) * random.uniform(15, 24)) for i in range(13)],
        campos=[(20, 52, -68, -30), (56, 88, -68, -30), (20, 52, -26, 10), (56, 88, -26, 10)])
for i in range(26):  # creek-side bushes
    x = random.choice((-1, 1)) * random.uniform(10, 60)
    prim("ico_sphere", f"arbusto{i}", (x, CREEK_Y + random.choice((-2.6, 2.6)), .4), (.9, .9, .7), LEAF3, subdivisions=1)
box("torre", 160, 166, 100, 106, 0, 16, WALLS[0])
prim("cone", "torre_techo", (163, 103, 18), (4.5, 4.5, 2.5), ROOF, vertices=4, rot=(0, 0, math.radians(45)))

# ------------------------------------------------------------------ vehicles on the road
def drive(ob, s0, s1, t0, t1, o, bank_at, crown=1.0, top=.38, step=2):
    """Moves a vehicle along the road between two arc lengths, sitting on the surface and leaning with the bank.
    When s1 < s0 the vehicle drives the other way and faces backwards along the road."""
    back = s1 < s0
    f0, f1 = F(t0), F(t1)
    for f in list(range(f0, f1, step)) + [f1]:
        k = (f - f0) / max(1, f1 - f0)
        s = lerp(s0, s1, k)
        x, y, _ = world_pt(s, o, 0)
        _, (tx, ty) = path(s)
        b = bank_at((f - 1) / FPS)
        z = surface(o, s, crown, b, top)
        roll = math.atan(TAN_BANK) * bank_w(s) * b
        yaw = math.atan2(-tx, ty) + (math.pi if back else 0)
        key(ob, "location", f, (x, y, z), interp="LINEAR")
        key(ob, "rotation_euler", f, (0, -roll if back else roll, yaw), interp="LINEAR")


# ------------------------------------------------------------------ b1: rain on the muddy dirt road
rain("lluviaA", 0, 6, 16, 22, 0, SC["b1"]["end"] + .3, 320)
puddles = []
for i in range(14):
    y = random.uniform(-6, 36)
    if abs(y - CREEK_Y) < 3:
        continue
    pd = prim("cylinder", f"charco{i}", (random.uniform(-1.8, 1.8), y, .03), (random.uniform(.6, 1.1), random.uniform(.9, 1.6), .015), MUD, vertices=12)
    pd.scale = (pd.scale[0], pd.scale[1], .015)
    t = .5 + random.uniform(0, 2.2)
    key(pd, "scale", 1, (0, 0, .015), interp="CONSTANT")
    key(pd, "scale", F(t), (0, 0, .015))
    key(pd, "scale", F(t + .8), tuple(pd.scale))
    puddles.append(pd)
beat("lluvia1", [0, SC["b1"]["end"] + .3])

# ------------------------------------------------------------------ b2: survey and stakes
b2 = SC["b2"]
tripod = teodolito("tripode", (8.5, 1.5, 0))
pop(tripod, b2["start"] + .05, final=(1, 1, 1))
stakes, stake_times = [], []
ys = [2, 8, 14, 22, 28, 34]
for j, y in enumerate(ys):
    for side in (-1, 1):
        st = estaca(f"estaca{j}{side}", (side * 6.5, y, 0))
        t = b2["start"] + .35 + (j * 2 + (side > 0)) * .19
        pop(st, t, dur=.18, final=(1, 1, 1))
        stakes.append(st)
        stake_times.append(round(t, 3))
lines_t = b2["start"] + .35 + 12 * .19
for side in (-1, 1):
    r = prim("cube", f"hilo{side}", (side * 6.5, 18, 1.0), (.02, 16, .02), ORANGE)
    key(r, "scale", 1, (0, 0, 0), interp="CONSTANT")
    key(r, "scale", F(lines_t) - 1, (1, 0, 1))
    key(r, "location", F(lines_t) - 1, (side * 6.5, 2, 1.0))
    key(r, "scale", F(lines_t + .6), (1, 1, 1))
    key(r, "location", F(lines_t + .6), (side * 6.5, 18, 1.0))
    stakes.append(r)
beat("estacas", stake_times)
beat("tripode", b2["start"] + .05)

# ------------------------------------------------------------------ b3: dozer strips the topsoil
b3 = SC["b3"]
dz = dozer("topadora")
d0, d1 = F(b3["start"]), F(b3["end"] - .2)
key(dz, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(dz, "scale", d0 - 1, (0, 0, 0), interp="CONSTANT")
key(dz, "scale", d0, (1, 1, 1))
y_start, y_end = -3.0, 38.0
pile = prim("ico_sphere", "monton", (0, 3.6, .3), (1.8, .9, .7), TOP, parent=dz, subdivisions=1)
for f in range(d0, d1 + 1, 2):
    k = (f - d0) / (d1 - d0)
    y = lerp(y_start, y_end, k)
    key(dz, "location", f, (0, y, -.62 + .02 * math.sin(f)), interp="LINEAR")
    key(strip_main, "scale", f, (1, max(.001, (y + 2.4 + 150) / S1), 1), interp="LINEAR")
    key(pile, "scale", f, (1.8 * (.4 + .6 * k), .9, .7 * (.4 + .6 * k)), interp="LINEAR")
key(strip_main, "scale", 1, (1, .001, 1), interp="CONSTANT")
key(strip_main, "scale", d0 - 1, (1, (y_start + 2.4 + 150) / S1, 1), interp="CONSTANT")
key(strip_main, "scale", F(SC["b4"]["start"]), (1, 1, 1), interp="CONSTANT")
key(strip_rest, "location", 1, (0, 0, -50), interp="CONSTANT")
key(strip_rest, "location", F(SC["b4"]["start"]), (0, 0, 0), interp="CONSTANT")
unpop(dz, SC["b4"]["start"] - .05, .05)
for ob in stakes + puddles:  # stakes and puddles go when the blade reaches them; the strings go first
    if ob.name.startswith(("estaca", "charco")):
        t = b3["start"] + (ob.location.y - 2.4 - y_start) / (y_end - y_start) * (b3["end"] - .2 - b3["start"])
        t = max(b3["start"] + .05, t)
    else:
        t = b3["start"] + .2
    unpop(ob, t, .12)
unpop(tripod, b3["start"] + .2)
beat("topadora", [b3["start"], b3["end"] - .2])

# ------------------------------------------------------------------ b4: roller compacts the subgrade
b4 = SC["b4"]
rl = roller("rodillo")
r0, r1 = F(b4["start"] + .1), F(b4["end"] - .1)
key(rl, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(rl, "scale", r0 - 1, (0, 0, 0), interp="CONSTANT")
key(rl, "scale", r0, (1, 1, 1))
key(subg_main, "scale", 1, (1, .001, 1), interp="CONSTANT")
key(subg_raw, "scale", 1, (1, 1, 1), interp="CONSTANT")
for f in range(r0, r1 + 1, 2):
    k = (f - r0) / (r1 - r0)
    y = lerp(-1.0, 30.0, k)
    key(rl, "location", f, (0, y, -.62 + (.04 if (f // 2) % 2 else 0)), interp="LINEAR")
    key(subg_main, "scale", f, (1, max(.001, (y + 1.0 + 150) / S1), 1), interp="LINEAR")
    key(subg_raw, "scale", f, (1, max(.001, (S1 - 150 - y - 1.0) / S1), 1), interp="LINEAR")
key(subg_main, "scale", F(SC["b5"]["start"]), (1, 1, 1), interp="CONSTANT")
key(subg_raw, "scale", F(SC["b5"]["start"]), (1, .001, 1), interp="CONSTANT")
show(subg_rest, b4["start"])
show(subg_raw, None, SC["b5"]["start"])
unpop(rl, SC["b5"]["start"] - .05, .05)
beat("rodillo1", [b4["start"] + .1, b4["end"] - .1])

# ------------------------------------------------------------------ b5: the creek floods the crossing
b5, b6 = SC["b5"], SC["b6"]
t_rise0, t_rise1 = b5["start"] + .2, b5["start"] + 1.6
key(creek_water, "scale", 1, (1, 1, 1))
key(creek_water, "scale", F(t_rise0), (1, 1, 1))
key(creek_water, "scale", F(t_rise1), (1, 1, 4.0))
t_wash = b5["start"] + 1.7
key(washout, "location", 1, (0, 0, -50), interp="CONSTANT")
key(washout, "location", F(t_wash), (0, 0, 0), interp="CONSTANT")
for i in range(8):
    x = random.uniform(-5, 5)
    s = random.uniform(.35, .6)
    ch = prim("ico_sphere", f"terron{i}", (x, CREEK_Y + random.uniform(-1, 1), -.75), (s, s, s * .7), SUBGRADE, subdivisions=1)
    f0 = F(t_wash + i * .04)
    key(ch, "scale", 1, (0, 0, 0), interp="CONSTANT")
    key(ch, "scale", f0 - 1, (0, 0, 0), interp="CONSTANT")
    key(ch, "scale", f0, (s, s, s * .7))
    key(ch, "location", f0, tuple(ch.location))
    key(ch, "location", F(b5["end"] + .3), (x + random.uniform(9, 14), ch.location.y + random.uniform(-.4, .4), -.75))
    key(ch, "rotation_euler", f0, (0, 0, 0))
    key(ch, "rotation_euler", F(b5["end"] + .3), (random.uniform(2, 4), random.uniform(1, 3), 0))
    unpop(ch, b5["end"] + .2)
beat("crecida", t_rise0)
beat("deslave", t_wash)

# ------------------------------------------------------------------ b6: culvert pipe
pipe = empty("alcantarilla", (0, CREEK_Y, -1.25))
outer_p = prim("cylinder", "tubo", (0, 0, 0), (.42, .42, 8.2), CONCRETE, parent=pipe, rot=(0, math.radians(90), 0), vertices=20)
inner_p = prim("cylinder", "tubo_hueco", (0, 0, 0), (.33, .33, 8.6), None, parent=pipe, rot=(0, math.radians(90), 0), vertices=20)
inner_p.hide_render = True
inner_p.display_type = "WIRE"
cut(outer_p, inner_p)
cut(vado_tubo, inner_p)
t_drop, t_land = b6["start"] + .45, b6["start"] + 1.05
key(pipe, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(pipe, "scale", F(t_drop) - 1, (0, 0, 0), interp="CONSTANT")
key(pipe, "scale", F(t_drop), (1, 1, 1))
key(pipe, "location", F(t_drop), (0, CREEK_Y, 5))
key(pipe, "location", F(t_land), (0, CREEK_Y, -1.25))
key(pipe, "location", F(t_land + .12), (0, CREEK_Y, -1.13))
key(pipe, "location", F(t_land + .25), (0, CREEK_Y, -1.25))
t_fill = b6["start"] + 1.75
show(vado, None, t_wash)
show(vado_tubo, t_fill)
pop(subg_patch, t_fill, dur=.2, final=(1, 1, 1))
key(creek_water, "scale", F(b6["start"]), (1, 1, 4.0))
key(creek_water, "scale", F(b6["start"] + .6), (1, 1, 1))
beat("tubo", t_land)
beat("relleno", t_fill)

# ------------------------------------------------------------------ b7: asphalt straight on soil sinks under a truck
b7 = SC["b7"]
nx, ny = 15, 26
slab_v, slab_f = [], []
for zz in (-.62, -.42):
    for j in range(ny):
        for i in range(nx):
            slab_v.append((lerp(-5.0, 5.0, i / (nx - 1)), lerp(-.5, 14, j / (ny - 1)), zz))
off = nx * ny


def vid(i, j, top):
    return top * off + j * nx + i


for j in range(ny - 1):
    for i in range(nx - 1):
        slab_f.append((vid(i, j, 1), vid(i + 1, j, 1), vid(i + 1, j + 1, 1), vid(i, j + 1, 1)))
        slab_f.append((vid(i, j, 0), vid(i, j + 1, 0), vid(i + 1, j + 1, 0), vid(i + 1, j, 0)))
for i in range(nx - 1):
    for j in (0, ny - 1):
        slab_f.append((vid(i, j, 0), vid(i + 1, j, 0), vid(i + 1, j, 1), vid(i, j, 1)))
for j in range(ny - 1):
    for i in (0, nx - 1):
        slab_f.append((vid(i, j, 0), vid(i, j + 1, 0), vid(i, j + 1, 1), vid(i, j, 1)))
slab = mesh_object("asfalto_prueba", slab_v, slab_f, ASPHALT)
slab.shape_key_add(name="Basis")
sink = slab.shape_key_add(name="hundido", from_mix=False)
for v in sink.data:
    v.co.z -= .45 * math.exp(-(v.co.x ** 2) / 10 - (v.co.y - 4.5) ** 2 / 14)
cut(slab, section)
t_slab = b7["start"] + .05
key(slab, "location", 1, (0, 0, 3), interp="CONSTANT")
key(slab, "location", F(t_slab) - 1, (0, 0, 3))
key(slab, "location", F(t_slab + .35), (0, 0, 0))
show(slab, t_slab, SC["b8"]["start"] + .25)
tk = truck("camion", RED, MACHINE)
t_arrive, t_sink0, t_sink1 = b7["start"] + 1.6, b7["start"] + 2.0, b7["start"] + 3.1
key(tk, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(tk, "scale", F(b7["start"] + .3) - 1, (0, 0, 0), interp="CONSTANT")
key(tk, "scale", F(b7["start"] + .3), (1, 1, 1))
key(tk, "rotation_euler", 1, (0, 0, math.pi))
key(tk, "location", F(b7["start"] + .3), (0, 34, -.42), interp="LINEAR")
key(tk, "location", F(t_arrive), (0, 5.5, -.42))
key(tk, "location", F(t_sink0), (0, 5.0, -.42))
key(tk, "location", F(t_sink1), (0, 5.0, -.82))
key(tk, "rotation_euler", F(t_sink0), (0, 0, math.pi))
key(tk, "rotation_euler", F(t_sink1), (math.radians(-3), math.radians(4), math.pi))
kb = slab.data.shape_keys.key_blocks["hundido"]
kb.value = 0
kb.keyframe_insert("value", frame=F(t_sink0))
kb.value = 1
kb.keyframe_insert("value", frame=F(t_sink1))
for i, (x, y, rot, ln) in enumerate([(-2.6, 2.2, 30, 1.4), (2.4, 2.8, -40, 1.2), (-1.5, 8.0, -20, 1.5), (2.8, 7.4, 35, 1.1), (0, 1.0, 80, 1.0)]):
    cr = prim("cube", f"grieta{i}", (x, y, -.42 - .45 * math.exp(-(x ** 2) / 10 - (y - 4.5) ** 2 / 14) + .012), (ln, .05, .02), CRACKM,
              rot=(0, 0, math.radians(rot)))
    pop(cr, t_sink0 + .5 + i * .1, dur=.15)
    show(cr, None, SC["b8"]["start"] + .25)
show(tk, None, SC["b8"]["start"] + .25)
beat("camion", [b7["start"] + .3, t_arrive])
beat("hundimiento", t_sink0)
beat("grietas", t_sink0 + .5)

# ------------------------------------------------------------------ b8: subbase of coarse gravel, plate compactor
b8 = SC["b8"]


g0, g1 = b8["start"] + .3, b8["start"] + 1.6
gravel_rain("grava", g0, g1 - .4, -.3, SUBBASE, (.08, .16))
key(subbase, "scale", 1, (1, 1, .001), interp="CONSTANT")
key(subbase, "scale", F(g0), (1, 1, .001))
key(subbase, "scale", F(g1), (1, 1, 1))
show(subbase, g0)
plate = compactadora("compactadora")
c0, c1 = F(g1 - .1), F(b8["end"])
key(plate, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(plate, "scale", c0 - 1, (0, 0, 0), interp="CONSTANT")
key(plate, "scale", c0, (1.4, 1.4, 1.4))
for f in range(c0, c1, 2):
    k = (f - c0) / max(1, c1 - c0)
    key(plate, "location", f, (lerp(-4, 4, k), 1.6, -.17 + crown_dz(0) * 0 + (.07 if (f // 2) % 2 else 0)), interp="LINEAR")
unpop(plate, b8["end"])
beat("grava_gruesa", [g0, g1])
beat("compactadora", [(c0 - 1) / FPS, (c1 - 1) / FPS])

# ------------------------------------------------------------------ b9: base of fine gravel, roller
b9 = SC["b9"]
h0, h1 = b9["start"] + .1, b9["start"] + 1.3
gravel_rain("gravilla", h0, h1 - .4, .1, BASE, (.04, .08), 50)
key(base, "scale", 1, (1, 1, .001), interp="CONSTANT")
key(base, "scale", F(h0), (1, 1, .001))
key(base, "scale", F(h1), (1, 1, 1))
show(base, h0)
rl2 = roller("rodillo2")
q0, q1 = F(h1), F(b9["end"])
key(rl2, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(rl2, "scale", q0 - 1, (0, 0, 0), interp="CONSTANT")
key(rl2, "scale", q0, (1, 1, 1))
key(rl2, "rotation_euler", 1, (0, 0, math.pi))
for f in range(q0, q1 + 1, 2):
    k = (f - q0) / max(1, q1 - q0)
    key(rl2, "location", f, (1.5, lerp(24, 4.5, ease(k)), .13 + (.03 if (f // 2) % 2 else 0)), interp="LINEAR")
unpop(rl2, b9["end"] + .05, .05)
beat("grava_fina", [h0, h1])
beat("rodillo2", [h1, b9["end"]])

# ------------------------------------------------------------------ b10: prime coat sprayed by a distributor truck
b10 = SC["b10"]
sp = truck("petrolizadora", WALLS[2], DARK)
bar = prim("cube", "barra", (0, -4.6, .5), (1.6, .06, .06), DARK, parent=sp)
rociador(sp, -4.6, b10["start"])
p0, p1 = F(b10["start"] + .15), F(b10["end"] - .7)
key(sp, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(sp, "scale", p0 - 1, (0, 0, 0), interp="CONSTANT")
key(sp, "scale", p0, (1, 1, 1))
key(prime_cut, "location", 1, (0, -.5, 0), interp="CONSTANT")
for f in range(p0, p1 + 1, 2):
    k = (f - p0) / max(1, p1 - p0)
    y = lerp(4.0, 34.0, k)
    key(sp, "location", f, (0, y, .13), interp="LINEAR")
    key(prime_cut, "location", f, (0, y - 4.6, 0), interp="LINEAR")
key(prime_cut, "location", F(SC["b11"]["start"]), (0, 500, 0), interp="CONSTANT")
show(prime_main, b10["start"])
show(prime_rest, SC["b11"]["start"])
unpop(sp, SC["b11"]["start"] - .05, .05)
beat("riego", [(p0 - 1) / FPS, (p1 - 1) / FPS])

# ------------------------------------------------------------------ b11: rain stands on the flat surface
b11, b12 = SC["b11"], SC["b12"]
rain("lluviaB", 0, 6, 9, 10, b11["start"] - .1, b12["start"] + 1.0, 260)
puddles2 = []
for i in range(12):
    x, y = random.uniform(-3.8, 3.8), random.uniform(.8, 14)
    pd = prim("cylinder", f"charcoB{i}", (x, y, .175), (random.uniform(.5, 1.0), random.uniform(.6, 1.2), .012), PUDDLE, vertices=12)
    final = tuple(pd.scale)
    t = b11["start"] + .4 + random.uniform(0, 1.8)
    key(pd, "scale", 1, (0, 0, .012), interp="CONSTANT")
    key(pd, "scale", F(t), (0, 0, .012))
    key(pd, "scale", F(t + 1.0), final)
    # b12: the crown sheds the water to the sides
    side = 1 if x >= 0 else -1
    key(pd, "location", F(b12["start"] + .2), (x, y, .175))
    key(pd, "location", F(b12["start"] + 1.5), (side * 5.6, y, .02))
    key(pd, "scale", F(b12["start"] + 1.0), final)
    key(pd, "scale", F(b12["start"] + 1.6), (0, 0, .012))
    puddles2.append(pd)
beat("lluvia2", [b11["start"] - .1, b12["start"] + 1.0])
beat("charcos", b11["start"] + .4)

# ------------------------------------------------------------------ b12: crown and ditches
k0, k1 = F(b12["start"] + .2), F(b12["start"] + 1.4)
for ob in road_layers:
    road_key("bombeo", ob, 1, 0)
    road_key("bombeo", ob, k0, 0)
    road_key("bombeo", ob, k1, 1)
    road_key("peralte", ob, 1, 0)
for d in ditches:
    key(d, "location", 1, (0, 0, 1.4))
    key(d, "location", F(b12["start"] + 1.2), (0, 0, 1.4))
    key(d, "location", F(b12["start"] + 2.6), (0, 0, 0))
ditch_water = []
for side in (-1, 1):
    w = sweep(f"agua_cuneta{side}", [(side * 8.3 + o, z, "") for o, z in ((-.35, -.8), (.35, -.8), (.3, -.6), (-.3, -.6))], 0, END, WATER)
    cut(w, section)
    show(w, b12["start"] + 2.3)
    ditch_water.append(w)
beat("bombeo", (k0 - 1) / FPS)
beat("cunetas", [b12["start"] + 1.2, b12["start"] + 2.6])
beat("escurre", b12["start"] + .3)

# ------------------------------------------------------------------ b13: paver lays hot asphalt, roller follows
b13 = SC["b13"]
pv = pavimentadora("pavimentadora", b13["start"])
a0, a1 = F(b13["start"] + .05), F(L("b13", 0)["end"] + .1)
key(pv, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(pv, "scale", a0 - 1, (0, 0, 0), interp="CONSTANT")
key(pv, "scale", a0, (1, 1, 1))
key(asph_cut, "location", 1, (0, -.5, 0), interp="CONSTANT")
rl3 = roller("rodillo3")
for f in range(a0, a1 + 1, 2):
    k = (f - a0) / max(1, a1 - a0)
    y = lerp(3.0, 26.0, k)
    key(pv, "location", f, (0, y, .165), interp="LINEAR")
    key(asph_cut, "location", f, (0, y - 2.3, 0), interp="LINEAR")
    key(rl3, "location", f, (0, y - 9.5, surface(0, 150, 1, 0) + (.03 if (f // 2) % 2 else 0)), interp="LINEAR")
key(rl3, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(rl3, "scale", a0 + 15, (0, 0, 0), interp="CONSTANT")
key(rl3, "scale", a0 + 16, (1, 1, 1))
show(asph_main, b13["start"])
show(asph_rest, SC["b14"]["start"])
key(asph_cut, "location", F(SC["b14"]["start"]), (0, 500, 0), interp="CONSTANT")
for ob in (pv, rl3):
    unpop(ob, SC["b14"]["start"] - .05, .05)
beat("pavimentadora", [(a0 - 1) / FPS, (a1 - 1) / FPS])

# ------------------------------------------------------------------ b14: a car slides off the flat curve
b14, b15 = SC["b14"], SC["b15"]
car1 = car("coche1", RED)
c_t0, c_t1 = b14["start"] + .05, b14["end"] - .1
cf0, cf1 = F(c_t0), F(c_t1)
key(car1, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(car1, "scale", cf0 - 1, (0, 0, 0), interp="CONSTANT")
key(car1, "scale", cf0, (1, 1, 1))
y_skid = 46.0
y_stop = 40 + math.sqrt((R + 8.3) ** 2 - (R - 1.8) ** 2)
for f in range(cf0, cf1 + 1, 2):
    k = (f - cf0) / max(1, cf1 - cf0)
    y = lerp(8, y_stop, 1 - (1 - k) ** 1.6)
    yaw = 0 if y < y_skid else -math.radians(75) * ease((y - y_skid) / (y_stop - y_skid))
    dist = math.hypot(1.8 - R, y - 40)
    on_road = dist > R - 5.0 and y < 40 or dist > R - 5.0 and dist < R + 5.0
    z = surface(1.8, 150, 1, 0) if (y < 40 or dist < R + 5.0) else (-.7 if dist > R + 7.4 else .0)
    roll = 0 if dist < R + 7.4 else math.radians(18)
    key(car1, "location", f, (1.8, y, z), interp="LINEAR")
    key(car1, "rotation_euler", f, (0, roll, yaw), interp="LINEAR")
show(car1, None, b15["start"])
t_skid = c_t0 + (cf1 - cf0) / FPS * (1 - (1 - (y_skid - 8) / (y_stop - 8)) ** (1 / 1.6))
beat("coche_pasa", c_t0)
beat("derrape", t_skid)
beat("choque", c_t1)

# ------------------------------------------------------------------ b15: superelevation, a car takes the curve
bk0, bk1 = b15["start"] + .1, b15["start"] + 1.2
for ob in road_layers:
    road_key("peralte", ob, F(bk0), 0)
    road_key("peralte", ob, F(bk1), 1)


def bank_at(t):
    return ease((t - bk0) / (bk1 - bk0))


car2 = car("coche2", BLUE)
key(car2, "scale", 1, (0, 0, 0), interp="CONSTANT")
key(car2, "scale", F(b15["start"] + .9) - 1, (0, 0, 0), interp="CONSTANT")
key(car2, "scale", F(b15["start"] + .9), (1, 1, 1))
drive(car2, S1 - 32, S1 + 40, b15["start"] + .9, b15["end"], 1.8, bank_at)
drive(car2, S1 + 40, S2 + 120, b15["end"], SC["b17"]["end"] + 3, 1.8, bank_at, step=3)
show(car2, b15["start"] + .9, SC["b16"]["start"])
show(car2, SC["b17"]["start"])
beat("peralte", bk0)
beat("coche_curva", b15["start"] + .9)

# ------------------------------------------------------------------ b16: guardrails, signs, painted lines
b16 = SC["b16"]
gs = [S1 - 22 + 4 * i for i in range(int((S2 + 22 - (S1 - 22)) / 4) + 1)]
rail_times = []
for i, s in enumerate(gs):
    o = -4.75
    x, y, _ = world_pt(s, o, 0)
    z = surface(o, s, 1, 1)
    post = prim("cylinder", f"poste{i}", (x, y, z + .45), (.06, .06, .45), STEEL, vertices=6)
    t = b16["start"] + .1 + i * (1.7 / len(gs))
    pop(post, t, dur=.1)
    rail_times.append(round(t, 3))
    if i:
        seg = sweep(f"barrera{i}", [(-4.83, .95, "cb"), (-4.69, .95, "cb"), (-4.69, 1.25, "cb"), (-4.83, 1.25, "cb")],
                    gs[i - 1], s, STEEL, static=(1, 1))
        show(seg, t)
beat("barreras", rail_times)
signs = []
for j, (s, kind) in enumerate([(S1 - 34, "curva"), (S1 - 55, "velocidad")]):
    x, y, _ = world_pt(s, 6.8, 0)
    sg = empty(f"senal{j}", (x, y, 0))
    prim("cylinder", f"senal_poste{j}", (0, 0, 1.2), (.06, .06, 1.2), STEEL, parent=sg, vertices=6)
    if kind == "curva":
        prim("cube", f"senal_placa{j}", (0, -.05, 2.6), (.55, .03, .55), YELLOWL, parent=sg, rot=(0, math.radians(45), 0))
        prim("cube", f"senal_flecha{j}", (0, -.09, 2.6), (.08, .02, .32), DARK, parent=sg)
        prim("cube", f"senal_punta{j}", (.12, -.09, 2.86), (.16, .02, .06), DARK, parent=sg, rot=(0, math.radians(-30), 0))
    else:
        prim("cylinder", f"senal_placa{j}", (0, -.05, 2.6), (.55, .55, .03), WHITE, parent=sg, rot=(math.radians(90), 0, 0), vertices=20)
        prim("cylinder", f"senal_borde{j}", (0, -.03, 2.6), (.62, .62, .025), RED, parent=sg, rot=(math.radians(90), 0, 0), vertices=20)
    t = b16["start"] + 1.6 + j * .35
    pop(sg, t, final=(1, 1, 1))
    signs.append(t)
beat("senales", signs)
paint_t0, paint_t1 = b16["start"] + 2.2, b16["end"] + .6
p_from, p_to = S1 - 40, S2 + 40
paint_times = []
s = 0.0
i = 0
while s < END - 3:
    seg_len = 3.0
    for o, m, dashed in ((0, YELLOWL, True), (-4.0, WHITE, False), (4.0, WHITE, False)):
        if dashed and int(s / 3) % 2:
            continue
        ln = sweep(f"linea{i}_{o}", [(o - .09, .382, "cb"), (o + .09, .382, "cb"), (o + .09, .392, "cb"), (o - .09, .392, "cb")], s, s + seg_len, m, static=(1, 1))
        t = paint_t0 if s < p_from else (paint_t1 if s > p_to else lerp(paint_t0, paint_t1, (s - p_from) / (p_to - p_from)))
        show(ln, t)
    if p_from <= s <= p_to and i % 4 == 0:
        paint_times.append(round(lerp(paint_t0, paint_t1, (s - p_from) / (p_to - p_from)), 3))
    s += seg_len
    i += 1
beat("pintura", [paint_t0, paint_t1])

# ------------------------------------------------------------------ b17: finished road with traffic
b17 = SC["b17"]
car3 = car("coche3", RED)
drive(car3, S2 + 90, S1 - 60, b17["start"] - .3, b17["end"] + 3, -1.8, lambda t: 1.0, step=3)
show(car3, b17["start"])
tk2 = truck("camion2", WALLS[1], WALLS[2])
drive(tk2, S1 - 90, S1 + 10, b17["start"] - .2, b17["end"] + 3, 1.8, lambda t: 1.0, step=3)
show(tk2, b17["start"])
beat("trafico", b17["start"])

# ------------------------------------------------------------------ camera
camara()
shot(0, b2["start"], (16, -44, 24), (11, -34, 19), (0, 30, 0), (0, 26, 0), False, lens=26)
shot(b2["start"], b3["start"], (15, -7, 7.5), (13, -4, 6.5), (0, 14, 0), (0, 15, 0), False)
follow(b3["start"], b4["start"], dz, (10, -11, 6), (0, 4, 0), False)
shot(b4["start"], b5["start"], (2.5, -10, 1.6), (.5, -9, 1.3), (0, 6, -.7), (0, 8, -.7), True)
shot(b5["start"], b6["start"], (10, 9, 3.6), (9, 10, 3.2), (-1, CREEK_Y + 1, -.9), (-1, CREEK_Y + 1, -.9), False)
shot(b6["start"], t_fill + .2, (10, 9, 3.6), (9.5, 9.5, 3.4), (-1, CREEK_Y + 1, -.9), (-1, CREEK_Y + 1, -1.0), False)
shot(t_fill + .2, b7["start"], (15.5, CREEK_Y - .3, -.3), (14, CREEK_Y - .2, -.45), (6, CREEK_Y, -1.25), (6, CREEK_Y, -1.3), False, lens=22)
shot(b7["start"], b8["start"], (4, -13, 2.6), (1.5, -11, 1.8), (0, 7, -.2), (0, 5, -.4), True)
shot(b8["start"], b9["start"], (-1, -8.5, .7), (1, -8, .6), (0, 3, -.5), (0, 3, -.4), True)
shot(b9["start"], b10["start"], (1, -8.5, 1.0), (-1, -8.8, 1.2), (0, 4, -.2), (0, 5, -.1), True)
shot(b10["start"], b11["start"], (8, -8, 4.5), (6, -7, 4), (0, 8, 0), (0, 14, 0), True)
shot(b11["start"], b12["start"], (6.5, -5.5, 3.8), (5.5, -4.8, 3.4), (0, 7, 0), (0, 7, 0), True)
shot(b12["start"], b13["start"], (0, -14, 1.6), (0, -13, 1.4), (0, 4, -.3), (0, 4, -.3), True)
shot(b13["start"], L("b13", 1)["start"], (9, -7, 4.5), (8, -3, 4), (0, 8, .3), (0, 14, .3), True)
shot(L("b13", 1)["start"], b14["start"], (0, -11, 1.4), (0, -10.4, 1.3), (0, 4, -.2), (0, 4, -.2), True)
shot(b14["start"], b15["start"], (-34, 22, 24), (-31, 26, 22), (8, 52, 0), (6, 56, 0), False)
shot(b15["start"], b16["start"], world_pt(S1 - 4, -10, 3.2), world_pt(S1 + 2, -10.5, 3.0), world_pt(S1 + 32, 0, .6), world_pt(S1 + 36, 0, .6), False)
shot(b16["start"], b17["start"], (-20, 26, 15), (-9, 42, 12), (12, 58, 0), (16, 66, 0), False)
shot(b17["start"], UNTIL + 1, (-14, 22, 12), (-70, -40, 70), (14, 60, 0), (40, 90, 0), False, lens=26)


terminar()
