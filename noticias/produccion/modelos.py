"""Detailed illustrated models for the news explainer: a map built from real coastline coordinates of the Persian Gulf and the
Strait of Hormuz, and shaded drawings of an oil tanker, a fighter jet, a missile and an oil barrel."""
import math
import random

import skia

INK = 0xFF15110F


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def line(width, color=INK):
    return skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=color,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def glow(color, blur):
    return skia.Paint(AntiAlias=True, Color=color, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))


def gradient(p0, p1, colors):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], colors))
    return p


def path(points, close=True, smooth=False):
    p = skia.Path()
    p.moveTo(*points[0])
    if smooth:  # rounded coast: quadratic curves through midpoints
        for a, b in zip(points[1:], points[2:] + points[:1] if close else points[2:]):
            p.quadTo(*a, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    else:
        for q in points[1:]:
            p.lineTo(*q)
    if close:
        p.close()
    return p


# ---------------------------------------------------------------- map from real coordinates (lon, lat)
def proj(lon, lat):
    """Equirectangular projection to map units: 100 units per degree, origin at 47E 31N."""
    return (lon - 47) * 100, (31 - lat) * 100


IRAN = [(44, 34), (48.0, 30.4), (48.6, 30.0), (50.3, 29.3), (50.84, 28.97), (51.4, 28.0), (52.6, 27.4), (53.7, 26.9), (54.5, 26.6),
        (55.3, 26.55), (55.9, 26.95), (56.27, 27.18), (56.9, 27.0), (57.3, 26.0), (57.77, 25.64), (59.0, 25.4), (61.0, 25.2), (64, 25), (64, 34)]
ARABIA = [(44, 22), (44, 29.6), (48.0, 29.4), (48.6, 28.0), (49.6, 27.0), (50.1, 26.5), (50.8, 25.6), (51.0, 26.1), (51.2, 26.15),
          (51.6, 25.9), (51.6, 25.0), (51.4, 24.6), (52.5, 24.2), (54.0, 24.2), (55.3, 25.27), (55.95, 25.8), (56.1, 26.1), (56.38, 26.38),
          (56.4, 25.9), (56.33, 25.12), (56.6, 24.5), (57.8, 23.7), (58.6, 23.6), (59.8, 22.5), (64, 22)]
QESHM = [(55.28, 26.62), (55.7, 26.8), (56.1, 26.97), (56.3, 26.93), (55.9, 26.72), (55.5, 26.58)]
CITIES = {"BANDAR ABBAS": (56.27, 27.18), "DUBÁI": (55.3, 25.27), "MASCATE": (58.6, 23.6)}
PLACES = {"qeshm": (55.85, 26.8), "ormuz": (56.45, 26.6), "golfo": (52.0, 27.0), "oman_mar": (58.2, 24.6)}


def gulf_map(c, center, zoom, t, W=1280, H=720, labels=True, font=None):
    """Draws the region so that `center` (lon, lat) is in the middle of the screen; zoom = pixels per map unit."""
    cx, cy = proj(*center)
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)
    c.drawRect(skia.Rect.MakeLTRB(-1000, -1000, 3000, 2000), gradient((0, 200), (0, 900), [0xFF2F82B4, 0xFF1A527E]))
    land = [path([proj(*p) for p in shape], smooth=True) for shape in (IRAN, ARABIA, QESHM)]
    for p in land:  # turquoise shallows along every coast
        c.drawPath(p, line(36 / zoom ** .3, 0x5560D4E0))
        c.drawPath(p, line(16 / zoom ** .3, 0x6688E6EC))
    for i in range(40):  # drifting light on the water
        y = (i * 47 + t * 12) % 1300 - 200
        c.drawLine(-1000, y, 3000, y + 60, line(2.5 / zoom ** .2, 0x14FFFFFF))
    rnd = random.Random(5)
    for p, base, dark in zip(land, (0xFFD7B47F, 0xFFE4C894, 0xFFC9A066), (0x30704010, 0x28704010, 0x30704010)):
        c.drawPath(p, fill(base))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        for _ in range(140):  # mountains and dunes
            x, y = rnd.uniform(-300, 2000), rnd.uniform(-400, 1000)
            s = rnd.uniform(20, 70)
            c.drawPath(path([(x - s, y), (x, y - s * .7), (x + s, y)]), fill(dark))
        c.drawRect(skia.Rect.MakeLTRB(-1000, -1000, 3000, 2000), gradient((0, -300), (0, 900), [0x00000000, 0x22000000]))
        c.restore()
        foam = .5 + .5 * math.sin(t * 2)
        c.drawPath(p, line(7 / zoom ** .5, skia.ColorSetARGB(int(150 + 70 * foam), 255, 255, 255)))
        c.drawPath(p, line(4 / zoom ** .5))
    if labels and font:
        for name, (lon, lat) in CITIES.items():
            x, y = proj(lon, lat)
            c.drawCircle(x, y, 6 / zoom ** .5, fill(0xFFFFFFFF))
            c.drawCircle(x, y, 6 / zoom ** .5, line(3 / zoom ** .5))
            f = skia.Font(font, 20 / zoom)
            c.drawString(name, x + 10 / zoom, y - 8 / zoom, f, line(5 / zoom))
            c.drawString(name, x + 10 / zoom, y - 8 / zoom, f, fill(0xFFFFFFFF))
    c.restore()
    return lambda lon, lat: (W / 2 + (proj(lon, lat)[0] - cx) * zoom, H / 2 + (proj(lon, lat)[1] - cy) * zoom)


# ---------------------------------------------------------------- vehicles and objects
def tanker(c, x, y, s, t, heading=0.0):
    """Crude oil tanker seen from above-side: red underwater hull, dark hull, deck pipes, white bridge, bow wave, wake."""
    c.save()
    c.translate(x, y)
    c.rotate(heading)
    c.scale(s, s)
    for i in range(6):  # wake
        a = (t * 1.5 + i / 6) % 1
        c.drawOval(skia.Rect.MakeXYWH(-95 - a * 90, 2 - 8 * a, 40 + 30 * a, 10 + 14 * a), line(3, skia.ColorSetARGB(int(160 * (1 - a)), 255, 255, 255)))
    c.drawPath(path([(66, -2), (82, 6), (66, 14)]), fill(0xAAFFFFFF))  # bow wave
    c.drawPath(path([(-80, 4), (70, 4), (60, 16), (-74, 16)]), fill(0xFFB0342A))
    hull = path([(-84, -14), (64, -14), (80, 2), (64, 8), (-80, 8)])
    c.drawPath(hull, gradient((0, -14), (0, 8), [0xFF3A3F47, 0xFF20242A]))
    c.drawPath(hull, line(3))
    c.drawLine(-70, -8, 56, -8, line(2.5, 0xFF8A2A22))
    for i in range(5):  # deck pipes and tank hatches
        c.drawCircle(-50 + i * 22, -17, 4.5, fill(0xFF9AA0A6))
        c.drawCircle(-50 + i * 22, -17, 4.5, line(1.5))
    c.drawLine(-60, -19, 44, -19, line(2, 0xFF6E747A))
    bridge = skia.Rect.MakeXYWH(-80, -42, 26, 28)
    c.drawRect(bridge, gradient((-80, 0), (-54, 0), [0xFFFFFFFF, 0xFFD6DADE]))
    c.drawRect(bridge, line(2.5))
    for i in range(3):
        c.drawRect(skia.Rect.MakeXYWH(-77 + i * 8, -37, 5, 5), fill(0xFF2E4B66))
    c.drawRect(skia.Rect.MakeXYWH(-72, -52, 8, 10), fill(0xFFB0342A))
    c.drawRect(skia.Rect.MakeXYWH(-72, -52, 8, 10), line(2))
    c.restore()


def fighter(c, x, y, s, angle, t, flame=True):
    """Stealth fighter seen from above: shaded fuselage, swept wings, twin tails, canopy with highlight, afterburner."""
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.scale(s, s)
    if flame:
        f = 1 + .15 * math.sin(t * 40)
        c.drawOval(skia.Rect.MakeXYWH(-104 * f, -9, 46 * f, 18), glow(0xCCFF8A2A, 8))
        c.drawOval(skia.Rect.MakeXYWH(-86, -5, 26, 10), glow(0xFFFFE6A0, 4))
    wings = path([(-20, 0), (6, -10), (-34, -64), (-50, -64), (-44, -10), (-44, 10), (-50, 64), (-34, 64), (6, 10)])
    c.drawPath(wings, gradient((0, -64), (0, 64), [0xFF7C8894, 0xFF5A6570]))
    c.drawPath(wings, line(3))
    for side in (-1, 1):
        tail = path([(-58, side * 6), (-82, side * 30), (-74, side * 32), (-46, side * 10)])
        c.drawPath(tail, fill(0xFF56616B))
        c.drawPath(tail, line(3))
    body = path([(-64, -8), (30, -11), (78, 0), (30, 11), (-64, 8)])
    c.drawPath(body, gradient((0, -11), (0, 11), [0xFF9BA6B0, 0xFF6A7580]))
    c.drawPath(body, line(3))
    c.drawLine(-50, 0, 60, 0, line(1.5, 0x44000000))
    c.drawOval(skia.Rect.MakeXYWH(18, -6, 30, 12), gradient((18, -6), (48, 6), [0xFFE0B04A, 0xFF8A5A10]))
    c.drawOval(skia.Rect.MakeXYWH(18, -6, 30, 12), line(2))
    c.drawOval(skia.Rect.MakeXYWH(26, -4, 10, 3), fill(0xCCFFFFFF))
    c.restore()


def missile(c, x, y, s, angle, t):
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    c.scale(s, s)
    f = 1 + .2 * math.sin(t * 50)
    c.drawOval(skia.Rect.MakeXYWH(-64 * f, -8, 34 * f, 16), glow(0xDDFF9A3A, 7))
    for side in (-1, 1):
        c.drawPath(path([(-30, side * 6), (-42, side * 18), (-24, side * 6)]), fill(0xFF6A7178))
        c.drawPath(path([(-30, side * 6), (-42, side * 18), (-24, side * 6)]), line(2))
    body = path([(-34, -7), (28, -7), (44, 0), (28, 7), (-34, 7)])
    c.drawPath(body, gradient((0, -7), (0, 7), [0xFFF2F2F2, 0xFFB8BEC4]))
    c.drawPath(body, line(2.5))
    c.drawPath(path([(28, -7), (44, 0), (28, 7)]), fill(0xFFC63A2E))
    c.restore()


def smoke_trail(c, pts, k, scale=1.0):
    n = max(2, int(len(pts) * min(1, k)))
    for i in range(n - 1):
        a = i / max(1, n)
        c.drawCircle(*pts[i], (8 + 14 * (1 - a)) * scale, glow(skia.ColorSetARGB(int(90 + 90 * a), 235, 235, 235), 7))


def barrel(c, x, y, s, level, t):
    """Shaded oil barrel; `level` 0..1 is how full it looks through a cut window, with a sloshing surface."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = skia.Rect.MakeXYWH(-80, -120, 160, 240)
    c.drawRoundRect(body.makeOffset(8, 8), 20, 20, fill(0x55000000))
    c.drawRoundRect(body, 20, 20, gradient((-80, 0), (80, 0), [0xFF1D4E8A, 0xFF3F7CC4, 0xFF1A426F]))
    window = skia.Rect.MakeXYWH(-42, -95, 84, 190)
    c.drawRoundRect(window, 12, 12, fill(0xFF0E1A26))
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(window, 12, 12), doAntiAlias=True)
    top = 95 - 190 * level
    wave = skia.Path()
    wave.moveTo(-42, 95)
    wave.lineTo(-42, top)
    for i in range(9):
        wave.lineTo(-42 + i * 10.5, top + math.sin(t * 4 + i) * 3)
    wave.lineTo(42, 95)
    wave.close()
    c.drawPath(wave, gradient((0, top), (0, 95), [0xFF3A2A1A, 0xFF120C08]))
    c.drawLine(-42, top, 42, top, line(3, 0xFFD9A441))
    c.restore()
    c.drawRoundRect(window, 12, 12, line(4))
    for yy in (-70, 70):
        c.drawLine(-80, yy, 80, yy, line(7, 0xFF16365E))
    c.drawRoundRect(body, 20, 20, line(6))
    c.drawRect(skia.Rect.MakeXYWH(-70, -112, 26, 160), fill(0x22FFFFFF))
    c.restore()
