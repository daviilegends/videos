"""Summoner's Rift with the REAL shape (sketch v2, from the user's references).
Square map, game coordinates 0..15000 with y UP (blue base bottom-left, red base top-right), drawn with y flipped.
Top lane along the left + top edges, bot lane along the bottom + right edges, mid on the diagonal.
The river crosses the other diagonal (top-left -> bottom-right). Upper pit = Baron / Herald / Void Grubs,
lower pit = Dragons. Jungle = walls of trees with walkable paths and camp clearings between them.
The red half is the point reflection of the blue half (x, y) -> (14800 - x, 14800 - y), like the real map.
Coordinates are approximate (from the real minimap), adjusted by eye with the user."""
import math
import random

import skia

from mapa import brush, fill, polyline, stroke
from grieta import BLUE, RED, INK, LANE_C, JUNGLE, JUNGLE_L, JUNGLE_D, TREE, TREE_D, WATER, WATER_L, WATER_D, BASE_C, VOID, blob, thick, turret

S = 15000          # world size (square)
W = H = S
C = 14800          # reflection constant: red = (C - x, C - y)
LANE_W, RIVER_W, PATH_W = 820, 1100, 620
FLOOR = 0xFF3E7350          # walkable jungle floor
WALL = 0xFF1A3A25           # jungle walls (tree mass)


def P(x, y):
    """Game coordinates (y up) -> screen/world coordinates (y down)."""
    return (x, S - y)


def mirror(pts):
    return [(C - x, C - y) for x, y in pts]


# ---------------- lanes (game coords)
TOP = [(1150, 3300), (1050, 11300), (1350, 12900), (2100, 13600), (3600, 13850), (11500, 13750)]
MID = [(3500, 3500), (11300, 11300)]
BOT = mirror(TOP)[::-1]
LANES = {"superior": TOP, "central": MID, "inferior": BOT}

# ---------------- river: top-left -> bottom-right through the centre
RIVER = [(1750, 13050), (2900, 12300), (3900, 11300), (5300, 9900), (6500, 8350), (7400, 7400), (8300, 6450), (9500, 4900), (10900, 3500), (11900, 2500), (13050, 1750)]
PIT_R = 620
_N = 1 / math.sqrt(2)
_PIT_OFF = RIVER_W / 2 + 40               # centre right at the bank: the pit is a half-circle that ends at the water
BARON = (4600 + _PIT_OFF * _N, 10600 + _PIT_OFF * _N)   # red side of the river (towards top), tucked into the jungle
DRAGON = (C - BARON[0], C - BARON[1])                    # blue side of the river (towards bot)

# ---------------- bases
BLUE_BASE = (300, 300)
RED_BASE = (C - 300, C - 300)
BASE_R = 4000
NEXUS = {"azul": (1550, 1550), "rojo": (C - 1550, C - 1550)}

# ---------------- structures (blue; red is mirrored)
_T_BLUE = {
    "superior": [(1000, 10450), (1500, 6700), (1170, 4290)],
    "central": [(5850, 6400), (5050, 4800), (3650, 3700)],
    "inferior": [(10500, 1030), (6900, 1500), (4280, 1250)],
}
TIERS = ["exterior", "interior", "inhibidor"]
_INHIB_BLUE = {"superior": (1170, 3570), "central": (3200, 3200), "inferior": (3450, 1250)}
_NEXUS_T_BLUE = [(1750, 2270), (2180, 1800)]


def named_turret(name):
    team, lane, tier = name.split("_")
    x, y = _T_BLUE[lane][TIERS.index(tier)]
    if team == "rojo":
        # the red top lane mirrors the blue BOT lane (point reflection swaps lanes)
        other = {"superior": "inferior", "inferior": "superior", "central": "central"}[lane]
        x, y = _T_BLUE[other][TIERS.index(tier)]
        x, y = C - x, C - y
    return P(x, y)


TURRETS = [(*named_turret(f"{team}_{lane}_{tier}"), BLUE if team == "azul" else RED)
           for team in ("azul", "rojo") for lane in _T_BLUE for tier in TIERS]
TURRETS += [(*P(x, y), BLUE) for x, y in _NEXUS_T_BLUE] + [(*P(C - x, C - y), RED) for x, y in _NEXUS_T_BLUE]
INHIBS = [(*P(*p), BLUE) for p in _INHIB_BLUE.values()] + [(*P(C - p[0], C - p[1]), RED) for p in _INHIB_BLUE.values()]

# ---------------- jungle camps (blue side; red mirrored)
CAMPS_BLUE = {"Gromp": (2100, 8450), "Azul": (3850, 7950), "Lobos": (3800, 6500),
              "Aves": (7000, 5450), "Rojo": (7750, 4100), "Krugs": (8400, 2700)}
CAMPS = {f"{k} azul": v for k, v in CAMPS_BLUE.items()}
CAMPS.update({f"{k} rojo": (C - v[0], C - v[1]) for k, v in CAMPS_BLUE.items()})
SCUTTLE = [(4400, 9650), (10400, 5150)]

# walkable jungle paths (blue side, game coords); red side is mirrored
PATHS_BLUE = [
    [(1050, 8000), (2100, 8450), (3850, 7950), (4700, 8900), (5300, 9900)],      # top-lane -> gromp -> blue -> river
    [(3850, 7950), (3800, 6500), (4900, 6000), (5850, 6400)],                    # blue -> wolves -> mid
    [(3800, 6500), (2700, 5600), (2300, 4400)],                                 # wolves -> base
    [(1050, 9800), (2300, 9750), (3300, 9900), (4400, 9650)],                    # top tri-brush -> top river
    [(2300, 9750), (2100, 8450)],
    [(4200, 2300), (5600, 3100), (7750, 4100), (8800, 4900), (9850, 4400)],     # base -> red buff -> dragon
    [(7750, 4100), (8400, 2700), (9300, 1300)],                                  # red -> krugs -> bot lane
    [(7750, 4100), (7000, 5450), (6300, 6300)],                                  # red -> raptors -> mid
    [(7000, 5450), (8000, 6100), (8300, 6450)],                                  # raptors -> river
    [(5000, 4400), (6100, 4900), (7000, 5450)],
    [(10500, 1100), (10600, 2700), (11200, 3300), (10900, 3500)],                # bot tri-brush -> river
    [(5850, 6400), (6500, 8350)],                                                # mid -> river (top side)
]
PATHS = PATHS_BLUE + [mirror(p) for p in PATHS_BLUE]

# brushes (blue side; mirrored for red): (x, y, rx, ry)
# brushes (blue side; mirrored for red): (x, y, rx, ry, angle)
BRUSH_BLUE = [
    (2450, 14170, 430, 140, 4), (1400, 13330, 300, 130, -45), (880, 12250, 300, 130, 88),   # top-lane corner, outer side
    (7080, 7790, 380, 120, -45),                                                          # mid: in the river, along the lane's upper edge
    (2300, 9750, 300, 200, 0), (1700, 9300, 180, 130, 0),                                 # top tri-brush
    (3200, 7300, 240, 150, 0), (4500, 7500, 200, 140, 0),                                 # blue buff
    (5500, 5100, 220, 140, 0), (6800, 6200, 200, 130, 0),                                 # mid side brush, raptors
    (8000, 3500, 240, 150, 0),                                                            # red buff
    (10500, 2900, 300, 200, 0), (11300, 2300, 200, 140, 0),                               # bot tri-brush
]
# the two river-bank brushes next to mid, exactly where the user drew them (not mirrored)
BRUSH_FIXED = [(6100, 7900, 380, 110, 70), (9350, 5900, 380, 110, 60)]
BRUSHES = BRUSH_BLUE + [(C - x, C - y, rx, ry, a) for x, y, rx, ry, a in BRUSH_BLUE] + BRUSH_FIXED


def _scr(pts):
    return [P(x, y) for x, y in pts]


def lane_path(lane):
    return polyline(_scr(LANES[lane]))


def _union(paths):
    out = paths[0]
    for p in paths[1:]:
        r = skia.Op(out, p, skia.PathOp.kUnion_PathOp)
        out = r if r is not None else out
    return out


_G = {}


def geo():
    if _G:
        return _G
    rnd = random.Random(7)
    lanes = {k: thick(lane_path(k), LANE_W) for k in LANES}
    river = thick(polyline(_scr(RIVER)), RIVER_W)
    pits = [skia.Path.Circle(*P(*BARON), PIT_R), skia.Path.Circle(*P(*DRAGON), PIT_R)]
    water = river
    bases = [skia.Path.Circle(*P(*BLUE_BASE), BASE_R), skia.Path.Circle(*P(*RED_BASE), BASE_R)]
    paths = [thick(polyline(_scr(p)), PATH_W) for p in PATHS]
    clearings = [skia.Path.Circle(*P(*v), 560) for v in CAMPS.values()] + [skia.Path.Circle(*P(*v), 420) for v in SCUTTLE]
    walk = _union(list(lanes.values()) + [water] + pits + bases + paths + clearings)
    border = skia.Path()
    border.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(300, 300, S - 300, S - 300), 900, 900))
    walk = skia.Op(walk, border, skia.PathOp.kIntersect_PathOp) or walk
    trees = []
    for _ in range(4200):
        x, y = rnd.uniform(0, S), rnd.uniform(0, S)
        if not walk.contains(x, y):
            r = rnd.uniform(110, 190)
            trees.append((x, y, r, blob(x, y, r, r * .9, 8, rnd, .25), TREE if rnd.random() < .55 else TREE_D))
    trees.sort(key=lambda q: q[1])
    mottles = [(blob(rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(150, 380), rnd.uniform(90, 240), 7, rnd), JUNGLE_L if rnd.random() < .5 else JUNGLE_D)
               for _ in range(900)]
    ripples = []
    for _ in range(140):
        k = rnd.uniform(0, len(RIVER) - 1.001)
        j = int(k)
        a, b = RIVER[j], RIVER[j + 1]
        f = k - j
        ripples.append((*P(a[0] + (b[0] - a[0]) * f + rnd.uniform(-300, 300), a[1] + (b[1] - a[1]) * f + rnd.uniform(-300, 300)), rnd.random()))
    _G.update(pits=pits, lanes=lanes, water=water, river=river, bases=bases, walk=walk, trees=trees, mottles=mottles, ripples=ripples)
    return _G


def pit(c, x, y, glow, t, away):
    """Pit beside the river: round floor cut by the water, stone wall only on the jungle side (open towards the river).
    away = screen-space unit vector pointing from the river to the pit."""
    g = geo()
    circle = skia.Path.Circle(x, y, PIT_R)
    floor = skia.Op(circle, g["water"], skia.PathOp.kDifference_PathOp) or circle
    c.drawPath(floor, fill(0xFF4E6A66 if glow == 0xFFFF9A4A else 0xFF4A4466))
    c.save()
    c.clipPath(floor, doAntiAlias=True)
    for r in range(160, PIT_R, 150):
        c.drawCircle(x, y, r, stroke(8, 0x33FFFFFF))
    p = skia.Paint(AntiAlias=True, Color=(0x66 << 24) | (glow & 0xFFFFFF), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 90))
    c.drawCircle(x, y, PIT_R * .45, p)
    c.restore()
    base = math.atan2(away[1], away[0])
    arc = skia.Path()
    arc.addArc(skia.Rect.MakeXYWH(x - PIT_R, y - PIT_R, 2 * PIT_R, 2 * PIT_R), math.degrees(base) - 110, 220)
    c.drawPath(arc, stroke(70, 0xFF5C6158))
    c.drawPath(arc, stroke(10))
    for j in range(11):  # stone blocks along the wall
        ang = base + math.radians(-105 + j * 21)
        bx, by = x + math.cos(ang) * PIT_R, y + math.sin(ang) * PIT_R
        c.drawRoundRect(skia.Rect.MakeXYWH(bx - 60, by - 95, 120, 130), 28, 28, fill(0xFF7D847A))
        c.drawRoundRect(skia.Rect.MakeXYWH(bx - 60, by - 95, 120, 130), 28, 28, stroke(8))


def draw(c, t, view):
    g = geo()
    vo = view.makeOutset(400, 400)
    c.drawRect(view.makeOutset(60, 60), fill(VOID))
    c.drawRoundRect(skia.Rect.MakeLTRB(150, 150, S - 150, S - 150), 1000, 1000, fill(WALL))
    for x, y, r, p, col in g["trees"]:
        if vo.contains(x, y):
            c.drawPath(p, fill(col))
            c.drawPath(p, stroke(7, 0xFF0F2416))
            c.drawCircle(x - r * .3, y - r * .3, r * .28, fill(0x1FFFFFFF))
    c.drawPath(g["walk"], fill(FLOOR))
    c.save()
    c.clipPath(g["walk"], doAntiAlias=True)
    for p, col in g["mottles"]:
        if skia.Rect.Intersects(p.getBounds(), vo):
            c.drawPath(p, fill((0x55 << 24) | (col & 0xFFFFFF)))
    for b, team in zip(g["bases"], (BLUE, RED)):
        c.drawPath(b, fill(BASE_C))
        cx, cy = P(*(BLUE_BASE if team == BLUE else RED_BASE))
        for r in range(1200, BASE_R, 700):
            c.drawCircle(cx, cy, r, stroke(14, 0xFF93A8B1))
    c.drawPath(g["water"], fill(WATER_D))
    c.drawPath(thick(polyline(_scr(RIVER)), RIVER_W - 140), fill(WATER))
    for x, y, ph in g["ripples"]:
        k = (t * .3 + ph) % 1
        a = int(255 * math.sin(k * math.pi))
        px, py = x + 160 * k, y + 160 * k
        c.drawPath(polyline([(px - 50, py), (px, py - 18), (px + 50, py)]), stroke(9, (a << 24) | (WATER_L & 0xFFFFFF)))
    for k, lane in g["lanes"].items():
        c.drawPath(lane, fill(LANE_C))
        c.drawPath(lane_path(k), stroke(LANE_W - 120, 0xFFDAD19F))
    c.restore()
    c.drawPath(g["walk"], stroke(12, 0xFF0F2416))
    pit(c, *P(*BARON), 0xFF9B6CF0, t, (_N, -_N))      # screen: up-right, away from the river
    pit(c, *P(*DRAGON), 0xFFFF9A4A, t, (-_N, _N))     # screen: down-left
    for j, (x, y, rx, ry, ang) in enumerate(BRUSHES):
        bx, by = P(x, y)
        if vo.contains(bx, by):
            c.save()
            c.translate(bx, by)
            c.rotate(ang)
            brush(c, 0, 0, rx, ry, t, j)
            c.restore()
    for x, y, team in INHIBS:
        c.drawCircle(x, y, 150, fill(0xFF6E7A86))
        c.drawCircle(x, y, 150, stroke(10))
        c.drawCircle(x, y, 95, fill(team))
        c.drawCircle(x, y, 95, stroke(8))
    for team, (nx, ny) in NEXUS.items():
        x, y = P(nx, ny)
        col = BLUE if team == "azul" else RED
        c.drawCircle(x, y, 330, fill(0xFF6E7A86))
        c.drawCircle(x, y, 330, stroke(12))
        gem = polyline([(x, y - 420), (x + 190, y - 120), (x, y + 120), (x - 190, y - 120)])
        gem.close()
        c.drawPath(gem, fill(col))
        c.drawPath(gem, stroke(12))
    for x, y, team in sorted(TURRETS, key=lambda q: q[1]):
        if vo.contains(x, y):
            turret(c, x, y, team, t, 1.7)


def minimap(c, x, y, w, view, t):
    sc = w / S
    c.save()
    c.translate(x, y)
    r = skia.Rect.MakeWH(w, w)
    c.drawRoundRect(r.makeOutset(8, 8), 14, 14, fill(0xFF0E1418))
    c.clipRect(r)
    c.drawRect(r, fill(WALL))
    c.scale(sc, sc)
    g = geo()
    c.drawPath(g["walk"], fill(FLOOR))
    for b in g["bases"]:
        c.drawPath(b, fill(BASE_C))
    c.drawPath(g["water"], fill(WATER))
    for lane in g["lanes"].values():
        c.drawPath(lane, fill(LANE_C))
    for tx, ty, team in TURRETS:
        c.drawCircle(tx, ty, 220, fill(team))
    c.drawRect(skia.Rect.MakeLTRB(max(0, view.left()), max(0, view.top()), min(S, view.right()), min(S, view.bottom())), stroke(120, 0xFFFFFFFF))
    c.restore()
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, w).makeOutset(8, 8), 14, 14, stroke(6, 0xFFE8C26A))
