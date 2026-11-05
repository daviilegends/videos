"""Full 2D map in the style of Summoner's Rift (our cartoon art), with the real orientation:
blue base bottom-left, red top-right; top lane up the left and across the top, bot lane across the bottom
and up the right; mid on the diagonal; river from top-left to bottom-right with Baron (above) and Dragon (below).
World: 9000 x 9000 px (0.6 px per game unit -> about 15000 units). Static content is rendered in cached tiles.
API: draw(c, t, view_rect) draws the visible world; minimap(c, x, y, size, view_rect, t) draws the minimap."""
import math
import random

import skia

from mapa import (BRUSH, BRUSH_D, BRUSH_L, INK, JUNGLE, JUNGLE_D, JUNGLE_L, LANE, LANE_D, LANE_L, ROCK, ROCK_D, ROCK_L,  # noqa: F401
                  WATER, WATER_L, blob, brush, fill, polyline, stroke, turret)

S = 9000
BLUE, RED = 0xFF3FA9F5, 0xFFE84855
LANE_W = 560
RIVER_W = 620
TILE, RES = 1024, 1.5
VOID = 0xFF16241C


def F(x, y):
    return (x * S, y * S)


def rot(p):  # 180-degree symmetry of the map
    return (S - p[0], S - p[1])


# ---------------- geometry ----------------
def lane_paths():
    top = skia.Path()
    top.moveTo(*F(.065, .80))
    top.lineTo(*F(.065, .17))
    top.quadTo(*F(.065, .065), *F(.17, .065))
    top.lineTo(*F(.80, .065))
    bot = skia.Path()
    bot.moveTo(*F(.20, .935))
    bot.lineTo(*F(.83, .935))
    bot.quadTo(*F(.935, .935), *F(.935, .83))
    bot.lineTo(*F(.935, .20))
    mid = skia.Path()
    mid.moveTo(*F(.20, .80))
    mid.lineTo(*F(.80, .20))
    return dict(superior=top, inferior=bot, central=mid)


RIVER_PTS = [F(.115, .135), F(.20, .225), F(.30, .31), F(.40, .415), F(.50, .50), F(.60, .585), F(.70, .69), F(.80, .775), F(.885, .865)]
BARON, DRAGON = F(.335, .265), F(.665, .735)
PIT_R = 400

WALLS_W = [  # west jungle (blue side, top half); the east jungle is its 180-degree rotation
    [(.095, .317), (.108, .381), (.151, .413)],
    [(.198, .357), (.262, .389), (.286, .444), (.262, .484)],
    [(.116, .468), (.111, .532), (.127, .587)],
    [(.190, .444), (.175, .500), (.198, .563), (.254, .571)],
    [(.294, .500), (.325, .548), (.305, .611)],
    [(.159, .640), (.230, .650)],
    [(.357, .420), (.389, .465)],
    [(.095, .222), (.119, .278)],
    [(.240, .300), (.250, .330)],
]
WALLS_S = [  # south jungle (blue side, bottom half); the north jungle is its rotation
    [(.357, .690), (.346, .754), (.381, .817)],
    [(.444, .667), (.484, .683), (.500, .730), (.468, .762), (.437, .738)],
    [(.413, .849), (.484, .873)],
    [(.532, .762), (.563, .802), (.548, .857)],
    [(.619, .873), (.698, .865)],
    [(.500, .600), (.532, .635)],
    [(.640, .610), (.659, .651)],
    [(.603, .698), (.667, .730), (.698, .794)],
    [(.300, .860), (.320, .890)],
    [(.735, .800), (.770, .842)],
]
WALL_W = 340

BRUSHES = [(.68, .893, 230, 70), (.60, .893, 200, 65), (.825, .870, 150, 110), (.86, .80, 120, 90),  # bot (blue half)
           (.42, .53, 120, 90), (.30, .395, 120, 80), (.14, .70, 110, 80), (.56, .70, 110, 80)]
BRUSHES = BRUSHES + [(1 - x, 1 - y, rx, ry) for x, y, rx, ry in BRUSHES]

# blue turrets (x, y) and the red ones by symmetry
TURRETS_B = [F(.065, .29), F(.075, .50), (585, 6364),  # top: outer, inner, inhibitor
             F(.42, .58), F(.36, .64), (1909, 7091),  # mid
             F(.71, .935), F(.50, .935), (2636, 8415),  # bot
             (900, 7500), (1500, 8100)]  # nexus
TURRETS = [(x, y, BLUE) for x, y in TURRETS_B] + [(S - x, S - y, RED) for x, y in TURRETS_B]
INHIBS_B = [(585, 6672), (1697, 7303), (2328, 8415)]
NEXUS_B = (1080, 7920)
FOUNTAIN_B = (430, 8570)
BASE_R = 2350


def named_turret(name):
    """'rojo_inferior_exterior' etc. Returns (x, y) of the turret base."""
    team, lane, tier = name.split("_")
    idx = {"superior": 0, "central": 3, "inferior": 6}[lane] + {"exterior": 0, "interior": 1, "inhibidor": 2}[tier]
    x, y = TURRETS_B[idx]
    return (x, y) if team == "azul" else (S - x, S - y)


# ---------------- static primitives ----------------
def stroke_path(points, w):
    p = polyline(points)
    out = skia.Path()
    skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeJoin=skia.Paint.kRound_Join,
               StrokeCap=skia.Paint.kRound_Cap).getFillPath(p, out)
    return out


def smooth(points):
    p = skia.Path()
    p.moveTo(*points[0])
    for a, b in zip(points[1:-1], points[2:]):
        p.quadTo(*a, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    p.lineTo(*points[-1])
    return p


def thick(path, w):
    out = skia.Path()
    skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeJoin=skia.Paint.kRound_Join,
               StrokeCap=skia.Paint.kRound_Cap).getFillPath(path, out)
    return out


class Prim:
    __slots__ = ("r", "fn")

    def __init__(self, r, fn):
        self.r, self.fn = r, fn


def build():
    rnd = random.Random(11)
    prims = []
    add = lambda r, fn: prims.append(Prim(r, fn))  # noqa: E731
    lanes = lane_paths()
    lane_fill = {k: thick(p, LANE_W) for k, p in lanes.items()}
    river = thick(smooth(RIVER_PTS), RIVER_W)
    for pc in (BARON, DRAGON):
        pass
    base_b = skia.Path.Circle(0, S, BASE_R)
    base_r = skia.Path.Circle(S, 0, BASE_R)

    def in_any(x, y, paths):
        return any(p.contains(x, y) for p in paths)

    # mottled jungle floor
    for _ in range(2600):
        x, y = rnd.uniform(0, S), rnd.uniform(0, S)
        b = blob(x, y, rnd.uniform(60, 180), rnd.uniform(40, 120), 7, rnd)
        col = JUNGLE_L if rnd.random() < .5 else JUNGLE_D
        add(b.getBounds(), lambda c, b=b, col=col: c.drawPath(b, fill(col)))
    # jungle walls: rocky ridges with tree canopy
    for walls, rotate in ((WALLS_W, False), (WALLS_S, False), (WALLS_W, True), (WALLS_S, True)):
        for pts in walls:
            P = [F(*q) for q in pts]
            if rotate:
                P = [rot(q) for q in P]
            sp = smooth(P)
            outer = thick(sp, WALL_W)
            inner = thick(sp, WALL_W * .62)

            def wall(c, outer=outer, inner=inner, sp=sp):
                c.drawPath(outer, fill(ROCK_D))
                c.drawPath(outer, stroke(10))
                c.drawPath(inner, fill(0xFF1F4A2E))
            add(outer.getBounds().makeOutset(20, 20), wall)
            meas = skia.PathMeasure(sp, False)
            d, L = 0, meas.getLength()
            while d <= L:  # tree crowns on top of the ridge
                (x, y), _ = meas.getPosTan(d)
                r = rnd.uniform(55, 80)
                b = blob(x + rnd.uniform(-20, 20), y + rnd.uniform(-20, 20), r, r * .9, 8, rnd, .25)
                col = BRUSH_D if rnd.random() < .5 else 0xFF2A6B42

                def crown(c, b=b, col=col):
                    c.drawPath(b, fill(col))
                    c.drawPath(b, stroke(5))
                add(b.getBounds(), crown)
                d += rnd.uniform(70, 100)
    # river with banks
    bank = thick(smooth(RIVER_PTS), RIVER_W + 60)
    add(bank.getBounds(), lambda c: c.drawPath(bank, fill(0xFF2A6A88)))
    add(river.getBounds(), lambda c: c.drawPath(river, fill(WATER)))
    for _ in range(260):  # lighter shallows
        x, y = rnd.uniform(0, S), rnd.uniform(0, S)
        if river.contains(x, y):
            b = blob(x, y, rnd.uniform(40, 110), rnd.uniform(25, 60), 7, rnd)
            add(b.getBounds(), lambda c, b=b: c.drawPath(b, fill(0xFF4A9FC6)))
    # epic monster pits
    for (px, py), glow in ((BARON, 0xFF9B6CF0), (DRAGON, 0xFFFF9A4A)):
        def pit(c, px=px, py=py, glow=glow):
            c.drawCircle(px, py, PIT_R + 70, fill(ROCK_D))
            c.drawCircle(px, py, PIT_R, fill(0xFF5B4A3A))
            c.drawCircle(px, py, PIT_R * .7, fill(0xFF6E5B47))
            p = skia.Paint(AntiAlias=True, Color=(0x66 << 24) | (glow & 0xFFFFFF),
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 60))
            c.drawCircle(px, py, PIT_R * .45, p)
            c.drawCircle(px, py, PIT_R + 70, stroke(10))
            c.drawCircle(px, py, PIT_R, stroke(7))
        add(skia.Rect.MakeXYWH(px - PIT_R - 80, py - PIT_R - 80, 2 * PIT_R + 160, 2 * PIT_R + 160), pit)
    # bases (stone platforms)
    for base, team, center in ((base_b, BLUE, (0, S)), (base_r, RED, (S, 0))):
        def plat(c, base=base, team=team, center=center):
            c.drawPath(base, fill(0xFF8C98A2))
            c.save()
            c.clipPath(base, doAntiAlias=True)
            for r in range(500, BASE_R, 380):
                c.drawCircle(*center, r, stroke(14, 0xFF77838E))
            for j in range(9):
                a = j * math.pi / 16
                sx = 1 if center[0] == 0 else -1
                sy = -1 if center[1] == S else 1
                c.drawLine(*center, center[0] + sx * math.cos(a) * BASE_R, center[1] + sy * math.sin(a) * BASE_R, stroke(10, 0xFF77838E))
            c.restore()
            c.drawPath(base, stroke(16))
        add(base.getBounds(), plat)
    # rocks along the lanes (with gaps for jungle entrances)
    for name, lp in lanes.items():
        meas = skia.PathMeasure(lp, False)
        L = meas.getLength()
        d = 0
        while d < L:
            (x, y), (tx, ty) = meas.getPosTan(d)
            for side in (-1, 1):
                if rnd.random() < .22:
                    continue
                nx, ny = -ty * side, tx * side
                off = LANE_W / 2 + 60 + rnd.uniform(-10, 25)
                rx, ry = x + nx * off, y + ny * off
                if in_any(rx, ry, [river, base_b, base_r]) or not (0 < rx < S and 0 < ry < S):
                    continue
                rr = rnd.uniform(45, 75)
                rock = blob(rx, ry, rr, rr * .8, 8, rnd, .25)

                def rk(c, rock=rock, rx=rx, ry=ry, rr=rr):
                    c.drawPath(rock, fill(ROCK))
                    c.save()
                    c.clipPath(rock, doAntiAlias=True)
                    c.drawCircle(rx - rr * .3, ry - rr * .35, rr * .7, fill(ROCK_L))
                    c.drawCircle(rx + rr * .4, ry + rr * .5, rr * .8, fill(ROCK_D))
                    c.restore()
                    c.drawPath(rock, stroke(5))
                add(rock.getBounds().makeOutset(6, 6), rk)
            d += 75
    # stone lanes with cobbles
    for name, lf in lane_fill.items():
        add(lf.getBounds(), lambda c, lf=lf: c.drawPath(lf, fill(LANE)))
        b = lf.getBounds()
        n = int(b.width() * b.height() / 5200)
        for _ in range(n):
            x, y = rnd.uniform(b.left(), b.right()), rnd.uniform(b.top(), b.bottom())
            if not lf.contains(x, y) or in_any(x, y, [base_b, base_r]):
                continue
            r = skia.Rect.MakeXYWH(x, y, rnd.uniform(30, 60), rnd.uniform(20, 38))
            col = LANE_D if rnd.random() < .5 else LANE_L

            def cob(c, r=r, col=col):
                c.drawRoundRect(r, 8, 8, fill(col))
                c.drawRoundRect(r, 8, 8, stroke(2, 0x55000000))
            add(r.makeOutset(3, 3), cob)
        add(lf.getBounds(), lambda c, lf=lf: c.drawPath(lf, stroke(7)))
    # map outer edge: dark cliffs outside a rounded square
    edge = skia.Path()
    edge.addRect(skia.Rect.MakeXYWH(-3000, -3000, S + 6000, S + 6000))
    inner = skia.Path()
    inner.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(120, 120, S - 240, S - 240), 900, 900))
    cliff = skia.Path()
    cliff = skia.Op(edge, inner, skia.PathOp.kDifference_PathOp)
    add(cliff.getBounds(), lambda c: (c.drawPath(cliff, fill(VOID)), c.drawPath(inner, stroke(14))))
    # base structures: fountains, inhibitors, nexus
    for team, sign_ in ((BLUE, 1), (RED, -1)):
        tr = (lambda p: p) if sign_ == 1 else rot
        fx, fy = tr(FOUNTAIN_B)

        def fountain(c, fx=fx, fy=fy, team=team):
            c.drawCircle(fx, fy, 260, fill(0xFF6E7A86))
            c.drawCircle(fx, fy, 260, stroke(10))
            p = skia.Paint(AntiAlias=True, Color=(0x99 << 24) | (team & 0xFFFFFF), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 50))
            c.drawCircle(fx, fy, 170, p)
            c.drawCircle(fx, fy, 120, fill(team))
            c.drawCircle(fx, fy, 120, stroke(8))
        add(skia.Rect.MakeXYWH(fx - 300, fy - 300, 600, 600), fountain)
        for ix, iy in [tr(q) for q in INHIBS_B]:
            def inhib(c, ix=ix, iy=iy, team=team):
                c.drawCircle(ix, iy, 110, fill(0xFF6E7A86))
                c.drawCircle(ix, iy, 110, stroke(8))
                c.drawCircle(ix, iy, 60, fill(team))
                c.drawCircle(ix, iy, 60, stroke(6))
            add(skia.Rect.MakeXYWH(ix - 130, iy - 130, 260, 260), inhib)
        nx, ny = tr(NEXUS_B)

        def nexus(c, nx=nx, ny=ny, team=team):
            c.drawOval(skia.Rect.MakeXYWH(nx - 230, ny - 90, 460, 200), fill(0xFF6E7A86))
            c.drawOval(skia.Rect.MakeXYWH(nx - 230, ny - 90, 460, 200), stroke(10))
            gem = polyline([(nx, ny - 330), (nx + 110, ny - 120), (nx, ny + 20), (nx - 110, ny - 120)])
            gem.close()
            c.drawPath(gem, fill(team))
            c.drawPath(gem, stroke(9))
            c.drawLine(nx - 30, ny - 270, nx - 55, ny - 130, stroke(9, 0xAAFFFFFF))
        add(skia.Rect.MakeXYWH(nx - 260, ny - 360, 520, 500), nexus)
    return prims, river


_STATE = {}


def _state():
    if not _STATE:
        prims, river = build()
        _STATE.update(prims=prims, river=river, tiles={}, ripples=[])
        meas = skia.PathMeasure(smooth(RIVER_PTS), False)
        rnd = random.Random(5)
        L = meas.getLength()
        for j in range(160):
            (x, y), (tx, ty) = meas.getPosTan(rnd.uniform(0, L))
            o = rnd.uniform(-RIVER_W * .4, RIVER_W * .4)
            _STATE["ripples"].append((x - ty * o, y + tx * o, tx, ty, rnd.uniform(0, 1)))
    return _STATE


def _tile(i, j):
    st = _state()
    key = (i, j)
    if key not in st["tiles"]:
        n = int(TILE * RES)
        surf = skia.Surface(n, n)
        c = surf.getCanvas()
        c.scale(RES, RES)
        c.translate(-i * TILE, -j * TILE)
        c.drawRect(skia.Rect.MakeXYWH(i * TILE, j * TILE, TILE, TILE), fill(JUNGLE))
        tr = skia.Rect.MakeXYWH(i * TILE - 4, j * TILE - 4, TILE + 8, TILE + 8)
        for p in st["prims"]:
            if skia.Rect.Intersects(p.r, tr):
                p.fn(c)
        st["tiles"][key] = surf.makeImageSnapshot()
    return st["tiles"][key]


def draw(c, t, view):
    """view: skia.Rect in world coordinates that is visible."""
    st = _state()
    c.drawRect(view.makeOutset(50, 50), fill(VOID))
    i0, i1 = math.floor(view.left() / TILE), math.floor(view.right() / TILE)
    j0, j1 = math.floor(view.top() / TILE), math.floor(view.bottom() / TILE)
    samp = skia.SamplingOptions(skia.FilterMode.kLinear)
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            if -3 <= i <= S // TILE + 3 and -3 <= j <= S // TILE + 3:
                c.drawImageRect(_tile(i, j), skia.Rect.MakeXYWH(i * TILE, j * TILE, TILE, TILE), samp)
    vo = view.makeOutset(150, 150)
    # river ripples
    c.save()
    c.clipPath(st["river"], doAntiAlias=True)
    for x, y, tx, ty, ph in st["ripples"]:
        k = (t * .25 + ph) % 1
        px, py = x + tx * k * 300, y + ty * k * 300
        if vo.contains(px, py):
            a = int(255 * math.sin(k * math.pi))
            c.drawPath(polyline([(px - 30, py), (px, py - 10), (px + 30, py)]), stroke(6, (a << 24) | (WATER_L & 0xFFFFFF)))
    c.restore()
    for j, (x, y, rx, ry) in enumerate(BRUSHES):
        X, Y = F(x, y)
        if vo.intersects(skia.Rect.MakeXYWH(X - rx, Y - ry, 2 * rx, 2 * ry)):
            brush(c, X, Y, rx, ry, t, j)
    for x, y, team in TURRETS:
        if vo.intersects(skia.Rect.MakeXYWH(x - 100, y - 300, 200, 350)):
            turret(c, x, y, team, t)


_MINI = {}


def minimap(c, x, y, size, view, t):
    if size not in _MINI:
        surf = skia.Surface(size, size)
        m = surf.getCanvas()
        sc = size / S
        m.scale(sc, sc)
        m.drawRect(skia.Rect.MakeWH(S, S), fill(0xFF234A30))
        lanes = lane_paths()
        for p in lanes.values():
            m.drawPath(p, stroke(LANE_W, 0xFFB9A574))
        m.drawPath(smooth(RIVER_PTS), stroke(RIVER_W, WATER))
        for walls, r_ in ((WALLS_W, False), (WALLS_S, False), (WALLS_W, True), (WALLS_S, True)):
            for pts in walls:
                P = [F(*q) for q in pts]
                m.drawPath(smooth([rot(q) for q in P] if r_ else P), stroke(WALL_W, 0xFF14301E))
        m.drawCircle(0, S, BASE_R, fill(0xFF7E8C98))
        m.drawCircle(S, 0, BASE_R, fill(0xFF7E8C98))
        for tx, ty, team in TURRETS:
            m.drawCircle(tx, ty, 150, fill(team))
            m.drawCircle(tx, ty, 150, stroke(50))
        _MINI[size] = surf.makeImageSnapshot()
    c.save()
    c.translate(x, y)
    r = skia.Rect.MakeWH(size, size)
    c.drawRoundRect(r.makeOutset(8, 8), 14, 14, fill(0xFF0E1418))
    c.drawImage(_MINI[size], 0, 0)
    c.drawRoundRect(r.makeOutset(8, 8), 14, 14, stroke(6, 0xFFE8C26A))
    sc = size / S
    v = skia.Rect.MakeLTRB(max(0, view.left() * sc), max(0, view.top() * sc), min(size, view.right() * sc), min(size, view.bottom() * sc))
    c.drawRect(v, stroke(4, 0xFFFFFFFF))
    c.drawCircle(v.centerX(), v.centerY(), 7 + 3 * math.sin(t * 6), fill(0xFFFFE27A))
    c.restore()
