"""Simplified Summoner's Rift (the user's sketch): blue base on the LEFT, red on the RIGHT.
Mid straight across the middle; top and bot slightly curved above and below; the river ONE straight vertical line
from top to bot (cut only by the lanes); Baron/Herald/Grubs pit upper-right of the river, Dragon pit lower-left.
Clean style (khaki lanes, green jungle, blue river) with ink outlines. Everything vector, drawn per frame.
World: 12000 x 6000 px. API: draw(c, t, view), minimap(c, x, y, w, view, t), lane_y(lane, x), named_turret(name)."""
import math
import random

import skia

from mapa import brush, fill, polyline, stroke

W, H = 12000, 6000
BLUE, RED = 0xFF3FA9F5, 0xFFE84855
INK = 0xFF1E2228
LANE_C, LANE_E = 0xFFD2C893, 0xFFB9AE78
JUNGLE, JUNGLE_L, JUNGLE_D = 0xFF2F5C3E, 0xFF386B49, 0xFF264D33
TREE, TREE_D = 0xFF1F4A2E, 0xFF173B24
WATER, WATER_L, WATER_D = 0xFF3AA0D2, 0xFF9AD6F0, 0xFF2A7FAE
BASE_C = 0xFFA9BCC4
VOID = 0xFF141D17
LANE_W, RIVER_W = 560, 520
X0, X1 = 900, W - 900  # lanes run from base to base


def lane_y(lane, x):
    u = min(1, max(0, (x - X0) / (X1 - X0)))
    if lane == "central":
        return H / 2
    bow = 430 * math.sin(math.pi * u)
    return 1450 - bow if lane == "superior" else H - 1450 + bow


def lane_path(lane):
    p = skia.Path()
    xs = [X0 - 600 + k * 100 for k in range(int((X1 - X0 + 1200) / 100) + 1)]
    p.moveTo(xs[0], lane_y(lane, xs[0]))
    for x in xs[1:]:
        p.lineTo(x, lane_y(lane, x))
    return p


# The river: ONE straight line, perpendicular to mid (the real map turned so the blue base is on the left).
# It runs from the top lane to the bottom lane and is only "cut" by the three lanes drawn over it.
# Kept as two collinear halves (top -> mid, mid -> bot) so the old code reading RIVERS[0] / RIVERS[1] still works.
RIVER_X = W / 2
RIVER_TOP = (RIVER_X, lane_y("superior", RIVER_X))  # ends under the lane (no overhang)
RIVER_BOT = (RIVER_X, lane_y("inferior", RIVER_X))
RIVERS = [(RIVER_TOP, (RIVER_X, H / 2)), ((RIVER_X, H / 2), RIVER_BOT)]

# Epic monster pits, attached to the river like on the real map:
# upper pit = Baron Nashor, Rift Herald and the Void Grubs (red side of the river, right);
# lower pit = the dragons (blue side of the river, left).
BARON = (RIVER_X + 470, 2060)
DRAGON = (RIVER_X - 470, H - 2060)
PIT_R = 330

# turrets: x per lane (blue = left half, red = mirrored)
_TX = {"superior": [3900, 2500, 1500], "central": [4500, 3300, 1900], "inferior": [3900, 2500, 1500]}
TIERS = ["exterior", "interior", "inhibidor"]


def named_turret(name):
    """'rojo_inferior_exterior', 'azul_central_interior', ..."""
    team, lane, tier = name.split("_")
    x = _TX[lane][TIERS.index(tier)]
    if team == "rojo":
        x = W - x
    return (x, lane_y(lane, x))


TURRETS = [(*named_turret(f"{team}_{lane}_{tier}"), BLUE if team == "azul" else RED)
           for team in ("azul", "rojo") for lane in _TX for tier in TIERS]

# brushes: river mouths on each lane (both sides of the river), plus jungle-edge brushes on the side lanes
BRUSHES = [(RIVER_X - 520, "superior", 1, 170, 85), (RIVER_X + 520, "superior", 1, 170, 85),
           (RIVER_X - 520, "central", -1, 170, 85), (RIVER_X + 520, "central", 1, 170, 85),
           (RIVER_X - 520, "inferior", -1, 170, 85), (RIVER_X + 520, "inferior", -1, 170, 85),
           (3300, "superior", -1, 240, 75), (W - 3300, "superior", -1, 240, 75),
           (3300, "inferior", 1, 240, 75), (W - 3300, "inferior", 1, 240, 75)]


def _brush_pos(x, lane, side):
    return x, lane_y(lane, x) + side * (LANE_W / 2 + 40)


def thick(path, w):
    out = skia.Path()
    skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeJoin=skia.Paint.kRound_Join,
               StrokeCap=skia.Paint.kRound_Cap).getFillPath(path, out)
    return out


def blob(cx, cy, rx, ry, n, rnd, bump=.2):
    pts = []
    for j in range(n):
        a = 2 * math.pi * j / n
        k = 1 + (rnd.random() - .5) * bump * 2
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    p = skia.Path()
    p.moveTo((pts[-1][0] + pts[0][0]) / 2, (pts[-1][1] + pts[0][1]) / 2)
    for j in range(n):
        a, b = pts[j], pts[(j + 1) % n]
        p.quadTo(*a, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    p.close()
    return p


_G = {}


def geo():
    if _G:
        return _G
    rnd = random.Random(21)
    lanes = {k: thick(lane_path(k), LANE_W) for k in ("superior", "central", "inferior")}
    rivers = [thick(polyline([RIVER_TOP, RIVER_BOT]), RIVER_W)]  # one continuous piece, no seams
    banks = [thick(polyline([RIVER_TOP, RIVER_BOT]), RIVER_W + 50)]
    base_b = skia.Path.Circle(-700, H / 2, 2050)
    base_r = skia.Path.Circle(W + 700, H / 2, 2050)
    blocked = list(lanes.values()) + rivers + [base_b, base_r, skia.Path.Circle(*BARON, PIT_R + 120), skia.Path.Circle(*DRAGON, PIT_R + 120)]

    def free(x, y, m=0):
        return not any(p.contains(x, y) for p in blocked) and (m <= 0 or all(
            not any(p.contains(x + dx, y + dy) for p in blocked) for dx, dy in ((m, 0), (-m, 0), (0, m), (0, -m))))
    mottles = []
    for _ in range(700):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        mottles.append((blob(x, y, rnd.uniform(80, 220), rnd.uniform(50, 140), 7, rnd), JUNGLE_L if rnd.random() < .5 else JUNGLE_D))
    trees = []
    for _ in range(900):  # tree clusters in the jungle, away from lanes and river
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        if free(x, y, 170):
            r = rnd.uniform(70, 120)
            trees.append((x, y, r, blob(x, y, r, r * .9, 8, rnd, .25), TREE if rnd.random() < .6 else TREE_D))
    trees.sort(key=lambda q: q[1])
    ripples = []
    for (a, b) in RIVERS:
        for _ in range(26):
            k = rnd.random()
            ripples.append((a[0] + (b[0] - a[0]) * k + rnd.uniform(-150, 150), a[1] + (b[1] - a[1]) * k, rnd.random()))
    _G.update(lanes=lanes, rivers=rivers, banks=banks, base_b=base_b, base_r=base_r, mottles=mottles, trees=trees, ripples=ripples)
    return _G


def turret(c, x, y, team, t, s=1.0):
    """Turret icon in our style; crystal at (x, y - 190*s)."""
    body = 0xFF5FB8F5 if team == BLUE else 0xFFF06A72
    dark = 0xFF2C6E9E if team == BLUE else 0xFF9E2C35
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawOval(skia.Rect.MakeXYWH(-80, -26, 160, 56), fill(0x55000000))
    base = skia.Rect.MakeXYWH(-70, -32, 140, 50)
    c.drawRoundRect(base, 18, 18, fill(dark))
    c.drawRoundRect(base, 18, 18, stroke(7))
    tower = polyline([(-46, -14), (-34, -130), (34, -130), (46, -14)])
    tower.close()
    c.drawPath(tower, fill(body))
    c.drawPath(tower, stroke(7))
    c.drawLine(-22, -110, -28, -30, stroke(7, 0x88FFFFFF))
    crown = polyline([(-50, -126), (-50, -160), (-28, -160), (-28, -146), (-10, -146), (-10, -160), (10, -160), (10, -146), (28, -146),
                      (28, -160), (50, -160), (50, -126)])
    crown.close()
    c.drawPath(crown, fill(dark))
    c.drawPath(crown, stroke(7))
    glow = .6 + .4 * math.sin(t * 3)
    p = skia.Paint(AntiAlias=True, Color=(int(140 * glow) << 24) | (team & 0xFFFFFF), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20))
    c.drawCircle(0, -190, 42, p)
    gem = polyline([(0, -232), (22, -192), (0, -164), (-22, -192)])
    gem.close()
    c.drawPath(gem, fill(0xFFFFFFFF))
    c.drawPath(gem, stroke(6))
    c.drawPath(polyline([(0, -222), (12, -192), (0, -174)]), fill(team))
    c.restore()


def _structures(c, t, vo):
    for team, sx in ((BLUE, 1), (RED, -1)):
        cx = 300 if sx == 1 else W - 300
        if vo.contains(cx, H / 2):
            bob = math.sin(t * 2) * 10
            p = skia.Paint(AntiAlias=True, Color=(0x99 << 24) | (team & 0xFFFFFF), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40))
            c.drawOval(skia.Rect.MakeXYWH(cx - 220, H / 2 - 70, 440, 170), fill(0xFF6E7A86))
            c.drawOval(skia.Rect.MakeXYWH(cx - 220, H / 2 - 70, 440, 170), stroke(9))
            c.drawCircle(cx, H / 2 - 150 + bob, 130, p)
            gem = polyline([(cx, H / 2 - 320 + bob), (cx + 100, H / 2 - 150 + bob), (cx, H / 2 - 20 + bob), (cx - 100, H / 2 - 150 + bob)])
            gem.close()
            c.drawPath(gem, fill(team))
            c.drawPath(gem, stroke(8))
        for lane in ("superior", "central", "inferior"):
            ix = 1100 if sx == 1 else W - 1100
            iy = lane_y(lane, ix)
            if vo.contains(ix, iy):
                c.drawCircle(ix, iy, 95, fill(0xFF6E7A86))
                c.drawCircle(ix, iy, 95, stroke(8))
                c.drawCircle(ix, iy, 60, fill(team))
                c.drawCircle(ix, iy, 60, stroke(6))
                gem = polyline([(ix, iy - 32), (ix + 22, iy), (ix, iy + 32), (ix - 22, iy)])
                gem.close()
                c.drawPath(gem, fill(0xFFFFFFFF))
                c.drawPath(gem, stroke(5))


def draw(c, t, view):
    g = geo()
    vo = view.makeOutset(250, 250)
    c.drawRect(view.makeOutset(60, 60), fill(VOID))
    c.drawRoundRect(skia.Rect.MakeXYWH(-200, 150, W + 400, H - 300), 700, 700, fill(JUNGLE))
    for p, col in g["mottles"]:
        if skia.Rect.Intersects(p.getBounds(), vo):
            c.drawPath(p, fill(col))
    for k in ("base_b", "base_r"):
        b = g[k]
        if skia.Rect.Intersects(b.getBounds(), vo):
            c.drawPath(b, fill(BASE_C))
            c.save()
            c.clipPath(b, doAntiAlias=True)
            cx = -700 if k == "base_b" else W + 700
            for r in range(700, 2050, 340):
                c.drawCircle(cx, H / 2, r, stroke(12, 0xFF93A8B1))
            c.restore()
            c.drawPath(b, stroke(12))
    for bank, river in zip(g["banks"], g["rivers"]):
        c.drawPath(bank, fill(WATER_D))
        c.drawPath(river, fill(WATER))
    c.save()
    for river in g["rivers"]:
        c.save()
        c.clipPath(river, doAntiAlias=True)
        for x, y, ph in g["ripples"]:
            k = (t * .3 + ph) % 1
            px, py = x + 200 * k * .3, y + 200 * k
            if vo.contains(px, py):
                a = int(255 * math.sin(k * math.pi))
                c.drawPath(polyline([(px - 34, py), (px, py - 12), (px + 34, py)]), stroke(7, (a << 24) | (WATER_L & 0xFFFFFF)))
        c.restore()
    c.restore()
    for bank in g["banks"]:
        c.drawPath(bank, stroke(8))
    for (px, py), glow in ((BARON, 0xFF9B6CF0), (DRAGON, 0xFFFF9A4A)):
        if vo.intersects(skia.Rect.MakeXYWH(px - PIT_R - 80, py - PIT_R - 80, 2 * PIT_R + 160, 2 * PIT_R + 160)):
            c.drawCircle(px, py, PIT_R + 60, fill(0xFF555950))
            c.drawCircle(px, py, PIT_R + 60, stroke(9))
            c.drawCircle(px, py, PIT_R, fill(0xFF6E5B47))
            c.drawCircle(px, py, PIT_R * .65, fill(0xFF7A664F))
            p = skia.Paint(AntiAlias=True, Color=(0x55 << 24) | (glow & 0xFFFFFF), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 50))
            c.drawCircle(px, py, PIT_R * .5, p)
            c.drawCircle(px, py, PIT_R, stroke(6))
    for k, lane in g["lanes"].items():
        c.drawPath(lane, fill(LANE_C))
        c.save()
        c.clipPath(lane, doAntiAlias=True)
        c.drawPath(lane_path(k), stroke(LANE_W - 70, 0xFFDAD19F))
        c.restore()
        c.drawPath(lane, stroke(9))
    for x, y, r, p, col in g["trees"]:
        if vo.contains(x, y):
            c.drawOval(skia.Rect.MakeXYWH(x - r * .9, y + r * .45, r * 1.8, r * .6), fill(0x44000000))
            c.drawPath(p, fill(col))
            c.drawPath(p, stroke(6))
            c.drawCircle(x - r * .3, y - r * .3, r * .3, fill(0x22FFFFFF))
    _structures(c, t, vo)
    for j, (x, lane, side, rx, ry) in enumerate(BRUSHES):
        bx, by = _brush_pos(x, lane, side)
        if vo.contains(bx, by):
            brush(c, bx, by, rx, ry, t, j)
    for x, y, team in TURRETS:
        if vo.contains(x, y):
            turret(c, x, y, team, t)


def minimap(c, x, y, w, view, t):
    h = w * H / W
    sc = w / W
    c.save()
    c.translate(x, y)
    r = skia.Rect.MakeWH(w, h)
    c.drawRoundRect(r.makeOutset(8, 8), 14, 14, fill(0xFF0E1418))
    c.clipRect(r)
    c.drawRect(r, fill(JUNGLE))
    c.scale(sc, sc)
    g = geo()
    for b in (g["base_b"], g["base_r"]):
        c.drawPath(b, fill(BASE_C))
    for river in g["rivers"]:
        c.drawPath(river, fill(WATER))
    for lane in g["lanes"].values():
        c.drawPath(lane, fill(LANE_C))
    for tx, ty, team in TURRETS:
        c.drawCircle(tx, ty, 110, fill(team))
    c.drawRect(skia.Rect.MakeLTRB(max(0, view.left()), max(0, view.top()), min(W, view.right()), min(H, view.bottom())), stroke(60, 0xFFFFFFFF))
    c.restore()
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h).makeOutset(8, 8), 14, 14, stroke(6, 0xFFE8C26A))
