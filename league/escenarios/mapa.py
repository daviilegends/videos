"""Original 2D top-down cartoon map of a lane (jungle, stone lane, rock walls, brush, river, turrets).
mapa(c, W, H, t, lane) draws the full frame. The static layer is cached per lane; brush, river and turret glow animate.
Lanes: "inferior" (river at the top-left corner), "superior" (mirrored), "central" (river crossing the middle)."""
import math
import random

import skia

INK = 0xFF1E2228
JUNGLE, JUNGLE_L, JUNGLE_D = 0xFF2C5A3A, 0xFF3A6E48, 0xFF234A30
LANE, LANE_D, LANE_L = 0xFFC8AE78, 0xFFAE9462, 0xFFD9C394
ROCK, ROCK_D, ROCK_L = 0xFF6E7268, 0xFF555950, 0xFF8A8E82
BRUSH, BRUSH_L, BRUSH_D = 0xFF2F7F4E, 0xFF55A86C, 0xFF1F5E38
WATER, WATER_L = 0xFF3A8FB7, 0xFF8FD0EA
BLUE, RED = 0xFF3FA9F5, 0xFFE84855

LAYOUTS = {
    # lane: centre line (points), brushes (x, y, rx, ry), river polygon, turrets (x, y, team), label
    "inferior": dict(path=[(-80, 1820), (300, 1300), (620, 900), (1160, 260)],
                     brushes=[(150, 1020, 120, 70), (930, 1080, 120, 72), (330, 620, 110, 60)],
                     river=[(-40, 330), (380, -40), (640, -40), (-40, 620)],
                     turrets=[(150, 1640, BLUE), (960, 360, RED)], label="LÍNEA INFERIOR"),
    "central": dict(path=[(540, 1960), (540, -40)],
                    brushes=[(200, 900, 110, 70), (880, 980, 110, 70)],
                    river=[(-40, 1050), (1120, 650), (1120, 900), (-40, 1300)],
                    turrets=[(540, 1700, BLUE), (540, 220, RED)], label="LÍNEA CENTRAL"),
}
LAYOUTS["superior"] = dict(LAYOUTS["inferior"], label="LÍNEA SUPERIOR")

LANE_W = 420


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def stroke(w, color=INK):
    return skia.Paint(AntiAlias=True, Color=color, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def polyline(points):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    return p


def blob(cx, cy, rx, ry, n, rnd, bump=.18):
    pts = []
    for j in range(n):
        a = 2 * math.pi * j / n
        k = 1 + (rnd.random() - .5) * bump * 2
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    p = skia.Path()
    m0 = ((pts[-1][0] + pts[0][0]) / 2, (pts[-1][1] + pts[0][1]) / 2)
    p.moveTo(*m0)
    for j in range(n):
        a, b = pts[j], pts[(j + 1) % n]
        p.quadTo(*a, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    p.close()
    return p


def lane_path(points, w):
    p = polyline(points)
    out = skia.Path()
    stroker = skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeJoin=skia.Paint.kRound_Join,
                         StrokeCap=skia.Paint.kRound_Cap)
    stroker.getFillPath(p, out)
    return out


def static_layer(W, H, lay):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    rnd = random.Random(7)
    c.drawRect(skia.Rect.MakeWH(W, H), fill(JUNGLE))
    for _ in range(70):  # mottled jungle floor
        c.drawPath(blob(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(30, 90), rnd.uniform(20, 60), 7, rnd),
                   fill(JUNGLE_L if rnd.random() < .5 else JUNGLE_D))
    # river
    river = polyline(lay["river"])
    river.close()
    c.drawPath(river, fill(WATER))
    c.drawPath(river, stroke(8, 0xFF2A6A88))
    # rock walls hugging the lane
    lane = lane_path(lay["path"], LANE_W)
    walls = lane_path(lay["path"], LANE_W + 120)
    pts = []
    meas = skia.PathMeasure(polyline(lay["path"]), False)
    L = meas.getLength()
    d = 0
    while d < L:
        (x, y), (tx, ty) = meas.getPosTan(d)
        for side in (-1, 1):
            nx, ny = -ty * side, tx * side
            off = LANE_W / 2 + 70 + rnd.uniform(-10, 20)
            pts.append((x + nx * off, y + ny * off))
        d += 70
    for (x, y) in pts:
        rr = rnd.uniform(40, 70)
        rock = blob(x, y, rr, rr * .8, 8, rnd, .25)
        c.drawPath(rock, fill(ROCK))
        c.save()
        c.clipPath(rock, doAntiAlias=True)
        c.drawCircle(x - rr * .3, y - rr * .35, rr * .7, fill(ROCK_L))
        c.drawCircle(x + rr * .4, y + rr * .5, rr * .8, fill(ROCK_D))
        c.restore()
        c.drawPath(rock, stroke(5))
    del walls
    # stone lane with cobbles
    c.drawPath(lane, fill(LANE))
    c.save()
    c.clipPath(lane, doAntiAlias=True)
    for _ in range(420):
        x, y = rnd.uniform(-50, W + 50), rnd.uniform(-50, H + 50)
        r = skia.Rect.MakeXYWH(x, y, rnd.uniform(26, 52), rnd.uniform(18, 34))
        c.drawRoundRect(r, 8, 8, fill(LANE_D if rnd.random() < .5 else LANE_L))
        c.drawRoundRect(r, 8, 8, stroke(2, 0x55000000))
    c.restore()
    c.drawPath(lane, stroke(7))
    return surf.makeImageSnapshot()


_CACHE = {}


def brush(c, x, y, rx, ry, t, seed):
    rnd = random.Random(seed)
    c.drawOval(skia.Rect.MakeXYWH(x - rx, y - ry * .6, rx * 2, ry * 1.4), fill(0x66000000))
    blades = []
    for _ in range(int(rx * ry / 120)):
        a = rnd.uniform(0, 2 * math.pi)
        r = math.sqrt(rnd.random())
        blades.append((x + math.cos(a) * rx * r, y + math.sin(a) * ry * r, rnd.uniform(26, 48), rnd.uniform(-.3, .3)))
    blades.sort(key=lambda b: b[1])
    for bx, by, h, lean in blades:
        sway = math.sin(t * 2.2 + bx * .05) * .18 + lean
        tip = (bx + math.sin(sway) * h, by - math.cos(sway) * h)
        blade = skia.Path()
        blade.moveTo(bx - 8, by)
        blade.quadTo(bx - 2, by - h * .5, *tip)
        blade.quadTo(bx + 4, by - h * .5, bx + 8, by)
        blade.close()
        c.drawPath(blade, fill(BRUSH if by % 3 < 1.5 else BRUSH_D))
        c.drawPath(blade, stroke(3))
        c.drawLine(bx, by - h * .3, tip[0] * .7 + bx * .3, tip[1] * .7 + by * .3, stroke(2.5, BRUSH_L))


def turret(c, x, y, team, t):
    glow = .6 + .4 * math.sin(t * 3)
    c.drawOval(skia.Rect.MakeXYWH(x - 70, y - 24, 140, 54), fill(0x66000000))
    base = skia.Rect.MakeXYWH(x - 62, y - 30, 124, 52)
    c.drawOval(base, fill(0xFF8C8F86))
    c.drawOval(base, stroke(6))
    body = skia.Path()
    body.moveTo(x - 40, y - 4)
    body.lineTo(x - 28, y - 150)
    body.lineTo(x + 28, y - 150)
    body.lineTo(x + 40, y - 4)
    body.close()
    c.drawPath(body, fill(0xFFB4B6AA))
    c.drawPath(body, stroke(6))
    c.drawLine(x - 34, y - 60, x + 34, y - 60, stroke(4))
    c.drawLine(x - 30, y - 110, x + 30, y - 110, stroke(4))
    p = skia.Paint(AntiAlias=True, Color=(int(150 * glow) << 24) | (team & 0xFFFFFF),
                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
    c.drawCircle(x, y - 190, 46, p)
    gem = polyline([(x, y - 245), (x + 26, y - 190), (x, y - 150), (x - 26, y - 190)])
    gem.close()
    c.drawPath(gem, fill(team))
    c.drawPath(gem, stroke(5))
    c.drawLine(x - 8, y - 225, x - 14, y - 195, stroke(4, 0xAAFFFFFF))


def mapa(c, W, H, t, lane="inferior"):
    lay = LAYOUTS[lane]
    if lane not in _CACHE:
        _CACHE[lane] = static_layer(W, H, lay)
    c.drawImage(_CACHE[lane], 0, 0)
    # animated river ripples
    river = polyline(lay["river"])
    river.close()
    c.save()
    c.clipPath(river, doAntiAlias=True)
    for j in range(14):
        x = (j * 97 + t * 40) % (W + 200) - 100
        y = (j * 151) % 700
        c.drawPath(polyline([(x, y), (x + 30, y - 8), (x + 60, y)]), stroke(5, WATER_L))
    c.restore()
    for j, (x, y, rx, ry) in enumerate(lay["brushes"]):
        brush(c, x, y, rx, ry, t, j)
    for x, y, team in lay["turrets"]:
        turret(c, x, y, team, t)
