"""News explainer, production version: illustrated backgrounds with camera moves, the Sticks character rig, a detailed
animated map of the Strait of Hormuz, effects (missile trails, explosions, counters), news graphics and whip transitions.
    render_env\\Scripts\\python.exe noticia2.py [--stills 1,5,9] [--hasta 30]"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import numpy as np
import skia
import soundfile as sf

import modelos as M
import rig_sticks as R

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 30
TL = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
CUES = json.loads((ROOT / "cues.json").read_text(encoding="utf-8"))
LINES = [l for s in TL["scenes"] for l in s["lines"]]
LENGTH = float(sys.argv[sys.argv.index("--hasta") + 1]) if "--hasta" in sys.argv else TL["duration"]
BGS = {p.stem: skia.Image.open(str(p)) for p in (ROOT / "assets" / "bg").glob("*.png")}
SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
INK, WHITE, RED, BLUE, GREEN, YELLOW = 0xFF15110F, 0xFFFFFFFF, 0xFFD8352B, 0xFF27407A, 0xFF239A52, 0xFFF4C430
BOLD = skia.Typeface.MakeFromFile("C:/Windows/Fonts/ariblk.ttf")
SUBF = skia.Font(skia.Typeface.MakeFromFile("C:/Windows/Fonts/comicbd.ttf"), 36)


def font(size):
    return skia.Font(BOLD, size)


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def line(width, color=INK):
    return skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=color,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def glow(color, blur):
    return skia.Paint(AntiAlias=True, Color=color, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def back(k):
    """Ease with a small overshoot, for things that pop in."""
    k = max(0.0, min(1.0, k))
    s = 1.7
    k -= 1
    return k * k * ((s + 1) * k + s) + 1


def poly(points):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    p.close()
    return p


def shake(t, amount):
    r = random.Random(int(t * FPS))
    return r.uniform(-1, 1) * amount, r.uniform(-1, 1) * amount


# ---------------------------------------------------------------- building blocks
def bg(c, name, zoom, cx=.5, cy=.5, tint=None):
    """Illustrated background with a slow camera; (cx, cy) is the image point at the screen centre."""
    img = BGS.get(name)
    if img is None:
        c.drawRect(skia.Rect.MakeWH(W, H), fill(0xFF33475B))
        return
    sc = W / img.width() * zoom
    half_w, half_h = W / 2 / sc, H / 2 / sc
    x = min(max(cx * img.width(), half_w), img.width() - half_w)
    y = min(max(cy * img.height(), half_h), img.height() - half_h)
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(sc, sc)
    c.translate(-x, -y)
    paint = skia.Paint(ColorFilter=skia.ColorFilters.Blend(tint, skia.BlendMode.kModulate)) if tint else None
    c.drawImage(img, 0, 0, SAMPLING, paint)
    c.restore()


def person(c, x, y, scale, t, mouth=None, look=(0, 0), face=0.0, arm_r=(.1, .1), arm_l=(-.1, .1), brow=0.0, jacket=None,
           hair=None, tie=None, walk=None, eye=1.0):
    s = dict(t=t, x=x, y=y, scale=scale, blink=1.0 if (t + x * .01) % 3.6 < .1 else 0.0, look=look, face=face, arm_r=arm_r, arm_l=arm_l,
             brow=brow, mouth=mouth or "flat", walk=walk, eye=eye)
    if jacket:
        s["jacket"] = jacket
    if hair:
        s["hair_color"] = hair
    shadow = skia.Rect.MakeXYWH(x - 70 * scale, y - 12 * scale, 140 * scale, 24 * scale)
    c.drawOval(shadow, glow(0x66000000, 8))
    R.character(c, s)
    if tie:  # a tie drawn over the shirt opening
        c.save()
        c.translate(x, y)
        c.scale(scale, scale)
        top = -188 + math.sin(t * 1.7) * 2
        c.drawPath(poly([(-6, top), (6, top), (9, top + 52), (0, top + 64), (-9, top + 52)]), fill(tie))
        c.drawPath(poly([(-6, top), (6, top), (9, top + 52), (0, top + 64), (-9, top + 52)]), line(3))
        c.restore()


def talk(t, speaking=True):
    return ["talk1", "talk2", "o", "talk2", "talk1"][int(t * 9) % 5] if speaking else "flat"


def banner(c, text, k, y=60, color=RED, size=40):
    """News strap sliding in from the left."""
    f = font(size)
    w = f.measureText(text) + 60
    x = -w + (w + 40) * back(k * 2.2)
    c.drawRoundRect(skia.Rect.MakeXYWH(x + 6, y + 6, w, size * 1.5), 8, 8, fill(0x55000000))
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, size * 1.5), 8, 8, fill(color))
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, size * 1.5), 8, 8, line(4))
    c.drawString(text, x + 30, y + size * 1.1, f, fill(WHITE))


def chip(c, text, x, y, k, size=30, color=WHITE, ink=INK):
    s = back(k * 2.5)
    if s <= 0:
        return
    f = font(size)
    w = f.measureText(text)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    r = skia.Rect.MakeXYWH(-w / 2 - 18, -size * 1.05, w + 36, size * 1.45)
    c.drawRoundRect(r.makeOffset(4, 4), 10, 10, fill(0x55000000))
    c.drawRoundRect(r, 10, 10, fill(color))
    c.drawRoundRect(r, 10, 10, line(4))
    c.drawString(text, -w / 2, 0, f, fill(ink))
    c.restore()


def explosion(c, x, y, k, size=150, seed=1):
    if not 0 < k < 1.2:
        return
    ring = size * 1.8 * ease(k * 1.5)
    c.drawCircle(x, y, ring, line(10 * (1 - min(1, k)), (0x00FFFFFF & 0xFFF2E6) | (int(200 * max(0, 1 - k)) << 24)))
    r = size * ease(k * 2.2) * (1.15 - .4 * max(0, k - .5))
    for i, col in enumerate((0xFF9C2A16, 0xFFF2702A, YELLOW, 0xFFFFF6D8)):
        rr = r * (1 - i * .22)
        pts = [(x + math.cos(j * math.pi / 9 + k * 2) * rr * (1 if j % 2 else .6), y + math.sin(j * math.pi / 9 + k * 2) * rr * (1 if j % 2 else .6))
               for j in range(18)]
        c.drawPath(poly(pts), fill((col & 0x00FFFFFF) | (int(255 * max(0, 1 - k) ** .5) << 24)))
    rnd = random.Random(seed)
    for _ in range(14):  # debris
        a, v = rnd.uniform(0, math.tau), rnd.uniform(.6, 1.3) * size * 2
        px, py = x + math.cos(a) * v * k, y + math.sin(a) * v * k + 200 * k * k
        c.drawRect(skia.Rect.MakeXYWH(px, py, 8, 8), fill(skia.ColorSetARGB(int(255 * max(0, 1 - k)), 40, 30, 25)))
    for i in range(6):  # smoke rising after the blast
        sk = max(0, k - .3)
        c.drawCircle(x + (i - 2.5) * size * .25, y - sk * size * (1 + i * .1), size * (.3 + sk * .5), glow(skia.ColorSetARGB(int(150 * max(0, 1 - sk * 1.2)), 60, 55, 50), 14))


def jet(c, x, y, s, angle, fire=True, t=0.0):
    M.fighter(c, x, y, s, angle, t, flame=fire)

def missile_trail(c, pts, k, t=0.0):
    """A missile following pts with a smoke trail behind it; k is progress 0..1."""
    M.smoke_trail(c, pts, k)
    n = max(2, int(len(pts) * min(1, k)))
    if k < 1:
        (x0, y0), (x, y) = pts[max(0, n - 2)], pts[n - 1]
        M.missile(c, x, y, 1.1, math.degrees(math.atan2(y - y0, x - x0)), t)

def counter(c, value, x, y, size, color=WHITE, prefix="", suffix=""):
    text = f"{prefix}{value:,.0f}{suffix}".replace(",", ".")
    f = font(size)
    w = f.measureText(text)
    c.drawString(text, x - w / 2 + 4, y + 4, f, fill(0x88000000))
    c.drawString(text, x - w / 2, y, f, line(size * .16))
    c.drawString(text, x - w / 2, y, f, fill(color))


# ---------------------------------------------------------------- map of the strait (map units 0..1000 x 0..600)
IRAN = [(-300, -300), (1300, -300), (1300, 250), (1000, 248), (880, 262), (800, 242), (730, 222), (650, 228), (560, 200), (450, 172),
        (350, 150), (250, 120), (150, 92), (-300, 60)]
ARABIA = [(-300, 900), (-300, 290), (150, 332), (300, 392), (420, 432), (520, 442), (600, 402), (640, 334), (688, 284), (708, 262),
          (732, 300), (762, 382), (822, 440), (1000, 470), (1300, 480), (1300, 900)]
QESHM = (640, 246)


def gulf(c, cx, cy, zoom, t):
    """Illustrated map: depth-shaded sea, textured land with hills, foam along the coasts, Qeshm island."""
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(zoom * 1.28, zoom * 1.28)
    c.translate(-cx, -cy)
    sea = skia.Paint()
    sea.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 150), skia.Point(0, 500)], [0xFF2E7FB0, 0xFF1E5C8C]))
    c.drawRect(skia.Rect.MakeLTRB(-300, -300, 1300, 900), sea)
    for shape in (IRAN, ARABIA):  # light shallow water along the coasts
        c.drawPath(poly(shape), line(26, 0x6656C6D6))
    for i in range(30):
        y = (i * 31 + t * 8) % 700 - 50
        c.drawLine(-300, y, 1300, y + 40, line(1.5, 0x18FFFFFF))
    rnd = random.Random(3)
    for shape, base in ((IRAN, 0xFFD9B98A), (ARABIA, 0xFFE2C79A)):
        p = poly(shape)
        c.drawPath(p, fill(base))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        for _ in range(60):  # hills and texture
            x, y = rnd.uniform(-300, 1300), rnd.uniform(-300, 900)
            c.drawOval(skia.Rect.MakeXYWH(x, y, rnd.uniform(40, 120), rnd.uniform(14, 40)), fill(0x22603E1A))
        c.restore()
        foam = .5 + .5 * math.sin(t * 2)
        c.drawPath(p, line(5, skia.ColorSetARGB(int(140 + 80 * foam), 255, 255, 255)))
        c.drawPath(p, line(3.5))
    c.save()
    c.translate(*QESHM)
    c.rotate(-14)
    c.drawOval(skia.Rect.MakeXYWH(-50, -10, 100, 20), fill(0xFFCDAA74))
    c.drawOval(skia.Rect.MakeXYWH(-50, -10, 100, 20), line(3))
    c.restore()
    c.restore()


def m2s(mx, my, cx, cy, zoom):
    return W / 2 + (mx - cx) * zoom * 1.28, H / 2 + (my - cy) * zoom * 1.28


def pin(c, x, y, t, color=RED):
    pulse = (t * 1.2) % 1
    c.drawCircle(x, y, 14 + 40 * pulse, line(4, (color & 0x00FFFFFF) | (int(220 * (1 - pulse)) << 24)))
    c.drawCircle(x, y, 12, fill(color))
    c.drawCircle(x, y, 12, line(4))


def tanker(c, x, y, s, t, heading=0.0):
    M.tanker(c, x, y, s, t, heading)

def intro(c, t, k):  # cold open: night sea, breaking-news strap, title slam
    bg(c, "golfo_noche", 1.05 + k * .1, .5, .5)
    c.drawRect(skia.Rect.MakeWH(W, H), fill(0x44000010))
    jet(c, -200 + 1700 * ease(k * 1.3), 220 - 60 * k, 1.4, -6, t=t)
    banner(c, "ÚLTIMA HORA", k, 70)
    s = back((k - .35) * 2.5)
    if s > 0:
        c.save()
        c.translate(W / 2, 380)
        c.scale(s, s)
        for txt, y, col in (("EE.UU. ATACA", -10, WHITE), ("UNA ISLA DE IRÁN", 80, YELLOW)):
            f = font(72)
            w = f.measureText(txt)
            c.drawString(txt, -w / 2, y, f, line(14))
            c.drawString(txt, -w / 2, y, f, fill(col))
        c.restore()


def l0_flags(c, t, k):  # "Estados Unidos volvió a atacar a Irán."
    dx, dy = shake(t, 10 * max(0, 1 - abs(k - .55) * 5))
    c.translate(dx, dy)
    bg(c, "cielo_combate", 1.1 + k * .1, .5, .45)
    for i, side in enumerate((-1, 1)):
        x = W / 2 + side * (520 - 260 * ease(k * 2))
        c.drawCircle(x, 330, 150, glow(0x66000000, 20))
        c.drawCircle(x, 330, 140, fill(WHITE))
        c.save()
        clip = skia.Path()
        clip.addCircle(x, 330, 135)
        c.clipPath(clip, doAntiAlias=True)
        if side < 0:
            for j in range(7):
                c.drawRect(skia.Rect.MakeXYWH(x - 140, 195 + j * 39 + math.sin(t * 3 + j) * 3, 280, 20), fill(RED))
            c.drawRect(skia.Rect.MakeXYWH(x - 140, 195, 130, 140), fill(BLUE))
        else:
            for j, col in enumerate((GREEN, WHITE, RED)):
                c.drawRect(skia.Rect.MakeXYWH(x - 140, 195 + j * 90 + math.sin(t * 3 + j) * 3, 280, 92), fill(col))
            c.drawCircle(x, 330, 26, line(7, RED))
        c.restore()
        c.drawCircle(x, 330, 140, line(8))
    explosion(c, W / 2, 330, (k - .5) / .5, 130)
    chip(c, "OTRA VEZ", W / 2, 600, (k - .6) * 2, 44, YELLOW)


def l1_anchor(c, t, k):  # "¿Qué está pasando, y qué podría venir después?": the region from high above
    to = M.gulf_map(c, (54.5, 26.5), .7 + .15 * k, t, labels=True, font=BOLD)
    for i, place in enumerate(("qeshm", "ormuz")):
        x, y = to(*M.PLACES[place])
        s = back((k - .2 - i * .25) * 2.5)
        if s > 0:
            c.save()
            c.translate(x, y - 70 + math.sin(t * 3 + i) * 8)
            c.scale(s, s)
            f = font(110)
            c.drawString("?", -32, 40, f, line(14))
            c.drawString("?", -32, 40, f, fill(YELLOW))
            c.restore()
    chip(c, "¿QUÉ ESTÁ PASANDO?", W / 2, 100, k * 3, 44, YELLOW)

def l2_strike(c, t, k):  # the strike on Qeshm, on the real map
    hit = (k - .72) / .28
    dx, dy = shake(t, 9 * max(0, 1 - hit * 2) if hit > 0 else 0)
    c.translate(dx, dy)
    zoom = .75 + 1.9 * ease(k * 1.15)
    center = (54.5 + 1.35 * ease(k), 26.4 + .4 * ease(k))
    to = M.gulf_map(c, center, zoom, t, labels=zoom < 1.6, font=BOLD)
    qx, qy = to(*M.PLACES["qeshm"])
    jet(c, -200 + 1700 * ease((k - .2) / .45), 140 + 30 * math.sin(k * 4), 1.5, 8, t=t)
    mk = (k - .5) / .22
    if mk > 0:
        pts = [(qx - 460 + 460 * u, qy - 330 + 330 * u - 130 * math.sin(u * math.pi)) for u in [i / 40 for i in range(41)]]
        missile_trail(c, pts, mk, t)
    explosion(c, qx, qy, hit, 120, seed=2)
    pin(c, qx, qy, t)
    chip(c, "ISLA DE QESHM", qx, qy + 80, (k - .1) * 2, 30)
    chip(c, "IRÁN", W / 2, 120, (k - .05) * 2, 40, YELLOW)
    banner(c, "LUNES 2 DE NOVIEMBRE", k, 30, BLUE, 30)
    chip(c, "SEGÚN THE WALL STREET JOURNAL", W - 300, H - 120, (k - .2) * 2, 22, WHITE)

def l3_hormuz(c, t, k):  # the strait and the oil
    to = M.gulf_map(c, (56.3 - .2 * k, 26.45), 3.2 + .3 * k, t, labels=True, font=BOLD)
    route = [(54.6, 26.0), (55.6, 26.25), (56.25, 26.5), (56.55, 26.45), (56.9, 26.1), (57.6, 25.4)]
    for i in range(5):
        u = (k * .5 + i * .2) % 1
        seg = u * (len(route) - 1)
        j = min(len(route) - 2, int(seg))
        f = seg - j
        lon = route[j][0] + (route[j + 1][0] - route[j][0]) * f
        lat = route[j][1] + (route[j + 1][1] - route[j][1]) * f
        x0, y0 = to(*route[j])
        x1, y1 = to(*route[j + 1])
        tanker(c, *to(lon, lat), .55, t, math.degrees(math.atan2(y1 - y0, x1 - x0)))
    pin(c, *to(*M.PLACES["qeshm"]), t)
    chip(c, "ESTRECHO DE ORMUZ", W / 2, 90, k * 2, 40, YELLOW)
    s = back((k - .45) * 2.2)
    if s > 0:
        c.save()
        c.translate(1100, 400)
        c.scale(s * .9, s * .9)
        M.barrel(c, 0, 0, 1.0, .2 * ease((k - .5) * 3), t)
        c.restore()
        chip(c, "1 DE CADA 5 BARRILES", 1100, 600, (k - .55) * 2, 26, WHITE)

def l4_island(c, t, k):  # what is on the island: three markers on the illustration
    bg(c, "isla", 1.15 + .1 * k, .5 - .1 * k, .5)
    for i, (txt, x, y) in enumerate((("MISILES BAJO TIERRA", 360, 470), ("BASE NAVAL", 760, 520), ("DESALINIZADORA", 980, 330))):
        kk = (k - .1 - i * .25) * 2.2
        if kk > 0:
            pin(c, x, y, t, [RED, BLUE, 0xFF2A9FD6][i])
            chip(c, txt, x, y - 50, kk, 26)


def l5_official(c, t, k):  # officials: "defensive", answer to a hit aircraft
    if k < .62:
        bg(c, "sala_prensa", 1.2 + .1 * k, .5, .55)
        person(c, 640, 760, 1.55, t, mouth=talk(t), arm_r=(1.3 + math.sin(t * 2.4) * .25, .8), jacket=(0xFF3A3F4A, 0xFF2A2E36), tie=BLUE,
               hair=0xFF6B6B6B)
        s = back((k - .12) * 3)
        if s > 0:
            c.save()
            c.translate(290, 260)
            c.scale(s, s)
            shield = poly([(-80, -95), (80, -95), (80, 15), (0, 100), (-80, 15)])
            c.drawPath(shield, glow(0x66000000, 10))
            c.drawPath(shield, fill(0xFF3C82C4))
            c.drawPath(shield, line(7))
            c.drawPath(poly([(-40, 0), (-12, 30), (45, -40), (50, -30), (-12, 50), (-50, 10)]), fill(WHITE))
            c.restore()
            chip(c, "\"ATAQUE DEFENSIVO\"", 290, 420, (k - .2) * 3, 30)
    else:
        kk = (k - .62) / .38
        bg(c, "cielo_combate", 1.25, .4 + .2 * kk, .5)
        x, y = 200 + 800 * kk, 260 + 140 * kk
        for i in range(10):
            a = (t * 2 + i / 10) % 1
            c.drawCircle(x - 60 - a * 220, y - 20 - a * 70, 14 + 30 * a, glow(skia.ColorSetARGB(int(170 * (1 - a)), 50, 50, 50), 10))
        jet(c, x, y, 1.7, 22 + math.sin(t * 9) * 4, t=t)
        c.drawCircle(x - 20, y, 22, glow(0xCCFF8030, 12))
        chip(c, "AERONAVE DE EE.UU. ALCANZADA", W / 2, 110, kk * 3, 32, YELLOW)


def l6_centcom(c, t, k):  # Central Command: no official announcement
    bg(c, "oficina_militar", 1.15 + .08 * k, .5, .5)
    doc = skia.Rect.MakeXYWH(470, 140, 340, 420)
    c.save()
    c.rotate(-3, 640, 350)
    c.drawRect(doc.makeOffset(8, 8), fill(0x66000000))
    c.drawRect(doc, fill(0xFFF8F4EA))
    c.drawRect(doc, line(6))
    c.drawString("COMANDO CENTRAL", 500, 200, font(26), fill(INK))
    for i in range(7):
        c.drawLine(500, 250 + i * 40, 780 - (i % 3) * 50, 250 + i * 40, line(7, 0xFFC9C0B0))
    c.restore()
    s = back((k - .25) * 3)
    if s > 0:
        c.save()
        c.translate(640, 420)
        c.rotate(-14)
        c.scale(1.6 - .6 * s, 1.6 - .6 * s)
        c.drawRoundRect(skia.Rect.MakeXYWH(-250, -50, 500, 80), 10, 10, line(8, RED))
        f = font(40)
        c.drawString("SIN ANUNCIO OFICIAL", -f.measureText("SIN ANUNCIO OFICIAL") / 2, 6, f, fill(RED))
        c.restore()


def l7_election(c, t, k):  # one night before the midterm elections
    bg(c, "casilla", 1.12 + .08 * k, .5, .55)
    cal = skia.Rect.MakeXYWH(140, 140, 220, 240)
    c.drawRect(cal.makeOffset(6, 6), fill(0x66000000))
    c.drawRect(cal, fill(WHITE))
    c.drawRect(skia.Rect.MakeXYWH(140, 140, 220, 60), fill(RED))
    c.drawRect(cal, line(6))
    c.drawString("NOV", 200, 185, font(36), fill(WHITE))
    flip = ease((k - .3) * 3)
    f = font(110)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(140, 200, 220, 180))
    for day, dy in (("2", -170 * flip), ("3", 170 * (1 - flip))):
        c.drawString(day, 250 - f.measureText(day) / 2, 340 + dy, f, fill(INK))
    c.restore()
    ballot_y = 200 + 260 * ease((k - .45) * 2.5)
    c.save()
    c.translate(900, ballot_y)
    c.rotate(10 * (1 - ease((k - .45) * 2.5)))
    c.drawRect(skia.Rect.MakeXYWH(-50, -65, 100, 130), fill(WHITE))
    c.drawRect(skia.Rect.MakeXYWH(-50, -65, 100, 130), line(5))
    c.drawLine(-25, 0, -5, 25, line(8, GREEN))
    c.drawLine(-5, 25, 30, -25, line(8, GREEN))
    c.restore()
    chip(c, "ELECCIONES DE MEDIO MANDATO", W / 2, 640, (k - .2) * 2, 30, YELLOW)


TRUMP = dict(jacket=(0xFF223459, 0xFF182644), hair=0xFFF0C766, tie=RED)


def l8_trump(c, t, k):  # Trump: "we already won", "it can't even be called a war"
    bg(c, "casa_blanca", 1.15 + .08 * k, .5, .6)
    c.drawRect(skia.Rect.MakeXYWH(520, 520, 240, 220), fill(0xFF5A3A26))
    c.drawRect(skia.Rect.MakeXYWH(520, 520, 240, 220), line(6))
    person(c, 640, 640, 1.7, t, mouth=talk(t), arm_r=(1.4 + math.sin(t * 2.2) * .3, .5), arm_l=(-.6, .4), brow=.3, **TRUMP)
    if k < .5:
        s = back((k - .1) * 3)
        if s > 0:
            c.save()
            c.translate(270, 260)
            c.scale(s, s)
            cup = poly([(-60, -80), (60, -80), (40, 20), (-40, 20)])
            c.drawPath(cup, fill(YELLOW))
            c.drawPath(cup, line(6))
            c.drawRect(skia.Rect.MakeXYWH(-14, 20, 28, 40), fill(YELLOW))
            c.drawRect(skia.Rect.MakeXYWH(-50, 60, 100, 24), fill(0xFF8A5A2A))
            c.drawRect(skia.Rect.MakeXYWH(-50, 60, 100, 24), line(5))
            c.restore()
            chip(c, "\"YA GANAMOS\"", 270, 420, (k - .15) * 3, 32)
    else:
        kk = (k - .5) * 2
        for i in range(4):
            month = ["JUL", "AGO", "SEP", "OCT"][i]
            chip(c, month, 180 + i * 0 + (i % 2) * 120, 160 + i * 80, (kk - i * .15) * 3, 30, WHITE)
        chip(c, "\"MESES SIN COMBATIR\"", 270, 520, (kk - .5) * 3, 30, YELLOW)


def l9_pentagon(c, t, k):  # the Pentagon reinforces the region and prepares options
    if k < .45:
        bg(c, "pentagono", 1.1 + .25 * k, .5, .5)
        chip(c, "PENTÁGONO", W / 2, 110, k * 3, 40, YELLOW)
    else:
        kk = (k - .45) / .55
        to = M.gulf_map(c, (56.5, 25.8), 1.6, t, labels=True, font=BOLD)
        for i in range(5):  # forces arriving from the Gulf of Oman
            u = ease((kk - i * .08) * 1.6)
            lon, lat = 59.5 - 3.0 * u, 23.6 + 1.6 * u + i * .12
            sx, sy = to(lon, lat)
            if i < 3:
                M.tanker(c, sx, sy, .5, t, -35)
            else:
                jet(c, sx, sy - 120, .8, 210, t=t)
        for i, txt in enumerate(("OPCIÓN A", "OPCIÓN B", "OPCIÓN C")):
            chip(c, txt, 230, 200 + i * 90, (kk - .3 - i * .12) * 3, 30, WHITE)
        chip(c, "MÁS FUERZAS EN LA REGIÓN", W / 2, 90, kk * 3, 34, YELLOW)


def l10_timeline(c, t, k):  # the war began in late February (US and Israel)
    bg(c, "oficina_militar", 1.2, .5, .5, tint=0xFF8890A0)
    c.drawRect(skia.Rect.MakeWH(W, H), fill(0x66000000))
    months = ["FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV"]
    x0, x1, y = 120, 1160, 380
    prog = ease(k * 1.2)
    c.drawLine(x0, y, x1, y, line(12, 0xFF555555))
    c.drawLine(x0, y, x0 + (x1 - x0) * prog, y, line(12, RED))
    for i, m in enumerate(months):
        x = x0 + (x1 - x0) * i / (len(months) - 1)
        on = prog >= i / (len(months) - 1)
        c.drawCircle(x, y, 16, fill(RED if on else 0xFF777777))
        c.drawCircle(x, y, 16, line(4))
        f = font(24)
        c.drawString(m, x - f.measureText(m) / 2, y + 60, f, fill(WHITE))
    chip(c, "EE.UU. + ISRAEL ATACAN IRÁN", 330, 250, (k - .05) * 3, 30, YELLOW)
    explosion(c, x0, y, (k - .02) / .35, 70, seed=4)


def l11_cost(c, t, k):  # the cost so far: 47,100 million dollars
    bg(c, "capitolio", 1.1 + .1 * k, .5, .5, tint=0xFFB0B0B0)
    c.drawRect(skia.Rect.MakeWH(W, H), fill(0x55000000))
    value = 47100 * ease(k * 1.6)
    for i in range(int(18 * ease(k * 1.6))):  # money stacks growing
        x = 140 + (i % 6) * 70
        yb = 640 - (i // 6) * 34
        c.drawRect(skia.Rect.MakeXYWH(x, yb, 60, 30), fill(0xFF5DA65A))
        c.drawRect(skia.Rect.MakeXYWH(x, yb, 60, 30), line(4))
        c.drawCircle(x + 30, yb + 15, 8, line(3, 0xFF2E6B2E))
    counter(c, value, 820, 330, 96, YELLOW, "$", "")
    c.drawString("MILLONES DE DÓLARES", 600, 400, font(34), fill(WHITE))
    chip(c, "HASTA EL 16 DE OCTUBRE", 820, 470, (k - .3) * 3, 28)
    for i in range(3):  # taxpayers
        person(c, 800 + i * 120, 720, .7, t + i, look=(0, -.3), eye=1.2, brow=-.6)


def l12_question(c, t, k):  # "¿Qué podría pasar ahora?": three roads branch out of the strait
    to = M.gulf_map(c, (56.2, 26.4), 2.4, t, labels=False)
    ox, oy = to(*M.PLACES["ormuz"])
    for i, (dx, dy, col) in enumerate(((-380, -200, RED), (380, -170, YELLOW), (0, 230, 0xFF3FA9F5))):
        kk = ease((k - i * .15) * 2.2)
        c.drawLine(ox, oy, ox + dx * kk, oy + dy * kk, line(16, col))
        if kk > .95:
            c.drawCircle(ox + dx, oy + dy, 26, fill(col))
            c.drawCircle(ox + dx, oy + dy, 26, line(5))
    pin(c, ox, oy, t)
    chip(c, "¿QUÉ PODRÍA PASAR?", W / 2, 110, k * 3, 50, YELLOW)

def l13_truce(c, t, k):  # the truce could break
    bg(c, "mesa_negociacion", 1.15 + .05 * k, .5, .5)
    tear = ease((k - .4) * 2.5)
    for side in (-1, 1):
        c.save()
        c.translate(640 + side * 120 * tear, 360 + 20 * tear)
        c.rotate(side * 12 * tear)
        half = poly([(0, -160), (side * 200, -160), (side * 200, 160), (0, 160)] if side > 0 else [(0, -160), (-200, -160), (-200, 160), (0, 160)])
        c.drawPath(half, fill(0xFFF8F4EA))
        c.drawPath(half, line(6))
        c.restore()
    f = font(56)
    if tear < .3:
        c.drawString("TREGUA", 640 - f.measureText("TREGUA") / 2, 380, f, fill(INK))
    explosion(c, 640, 360, (k - .55) / .45, 110, seed=6)
    chip(c, "SI IRÁN RESPONDE…", W / 2, 100, k * 3, 40, YELLOW)


def l14_oil(c, t, k):  # oil and gasoline prices could jump
    bg(c, "gasolinera", 1.12 + .08 * k, .5, .55)
    rise = ease((k - .2) * 1.8)
    c.drawRoundRect(skia.Rect.MakeXYWH(820, 150, 340, 170), 14, 14, fill(0xFF1A1A1A))
    c.drawRoundRect(skia.Rect.MakeXYWH(820, 150, 340, 170), 14, 14, line(6))
    c.drawString("GASOLINA", 860, 200, font(28), fill(WHITE))
    if rise > 0:
        ax = 1100
        c.drawPath(poly([(ax, 290 - 70 * rise), (ax - 26, 290 - 40 * rise), (ax + 26, 290 - 40 * rise)]), fill(0xFFFF6A3A))
        c.drawLine(ax, 290, ax, 290 - 45 * rise, line(14, 0xFFFF6A3A))
        c.drawString("SUBE", 860, 285, font(56), fill(0xFFFF6A3A))
    chart = [(140 + i * 60, 520 - 25 * i * ease((k - .1) * 1.5) - 30 * math.sin(i * 1.7) * .3) for i in range(9)]
    p = skia.Path()
    p.moveTo(*chart[0])
    for q in chart[1:]:
        p.lineTo(*q)
    c.drawPath(p, line(12, RED))
    tip = chart[-1]
    c.drawPath(poly([(tip[0] + 30, tip[1] - 10), (tip[0] - 10, tip[1] - 30), (tip[0] - 5, tip[1] + 15)]), fill(RED))
    chip(c, "PETRÓLEO ↑", 320, 200, (k - .1) * 3, 36, WHITE)


def l15_campaign(c, t, k):  # in the US the war's cost is a campaign issue
    bg(c, "capitolio", 1.12 + .1 * k, .5, .45)
    for i in range(int(14 * ease(k * 1.5))):  # campaign signs popping up
        r = random.Random(i)
        x, y = r.uniform(120, 1160), r.uniform(430, 640)
        c.save()
        c.translate(x, y)
        c.rotate(r.uniform(-8, 8))
        col = BLUE if i % 2 else RED
        c.drawLine(0, 0, 0, 70, line(6, 0xFF6A4A2A))
        c.drawRect(skia.Rect.MakeXYWH(-45, -50, 90, 55), fill(col))
        c.drawRect(skia.Rect.MakeXYWH(-45, -50, 90, 55), line(4))
        c.drawString("$", -10, -12, font(30), fill(WHITE))
        c.restore()
    chip(c, "$47.100 MILLONES", 640, 140, (k - .2) * 3, 40, YELLOW)
    chip(c, "TEMA DE CAMPAÑA", 640, 230, (k - .4) * 3, 30, WHITE)

def l16_results(c, t, k):  # the election results could shape what comes next
    bg(c, "casilla", 1.15, .5, .5)
    c.drawRect(skia.Rect.MakeWH(W, H), fill(0x44000000))
    c.drawLine(640, 150, 640, 260, line(10))
    tilt = math.sin(t * 2) * 10 * (1 - ease(k))
    c.save()
    c.translate(640, 260)
    c.rotate(tilt)
    c.drawLine(-260, 0, 260, 0, line(12))
    for side, col in ((-1, BLUE), (1, RED)):
        c.drawLine(side * 260, 0, side * 260, 120, line(5))
        c.drawRoundRect(skia.Rect.MakeXYWH(side * 260 - 90, 120, 180, 50), 10, 10, fill(col))
        c.drawRoundRect(skia.Rect.MakeXYWH(side * 260 - 90, 120, 180, 50), 10, 10, line(5))
    c.restore()
    chip(c, "¿QUÉ DECIDIRÁN LOS VOTANTES?", W / 2, 620, (k - .2) * 3, 32, YELLOW)


def l17_deal(c, t, k):  # Trump says he prefers a deal with Tehran
    bg(c, "mesa_negociacion", 1.12 + .06 * k, .5, .55)
    person(c, 420, 720, 1.4, t, mouth=talk(t), arm_r=(1.5, .3), **TRUMP)
    c.drawRect(skia.Rect.MakeXYWH(820, 470, 240, 300), fill(0x22000000))
    s = back((k - .3) * 3)
    if s > 0:
        c.save()
        c.translate(900, 300)
        c.scale(s, s)
        c.drawRect(skia.Rect.MakeXYWH(-110, -140, 220, 280), fill(0xFFF8F4EA))
        c.drawRect(skia.Rect.MakeXYWH(-110, -140, 220, 280), line(6))
        c.drawString("ACUERDO", -90, -90, font(36), fill(INK))
        for i in range(4):
            c.drawLine(-80, -40 + i * 40, 80, -40 + i * 40, line(6, 0xFFC9C0B0))
        c.restore()
    chip(c, "¿ACUERDO CON TEHERÁN?", W / 2, 110, (k - .1) * 3, 38, YELLOW)


def l18_options(c, t, k):  # but the military options remain on the table
    bg(c, "oficina_militar", 1.15 + .1 * k, .5, .55)
    c.drawRect(skia.Rect.MakeXYWH(140, 470, 1000, 40), fill(0xFF5A3A26))
    c.drawRect(skia.Rect.MakeXYWH(140, 470, 1000, 40), line(6))
    for i in range(3):
        s = back((k - .1 - i * .15) * 3)
        if s > 0:
            c.save()
            c.translate(360 + i * 280, 430)
            c.scale(s, s)
            jet(c, 0, 0, 1.2, -8, fire=False, t=t)
            c.restore()
    chip(c, "OPCIONES MILITARES: SOBRE LA MESA", W / 2, 120, (k - .2) * 3, 34, YELLOW)


def outro(c, t, k):
    bg(c, "estudio", 1.2, .5, .5)
    c.drawRect(skia.Rect.MakeWH(W, H), fill(0x88000000))
    chip(c, "SÍGUENOS PARA MÁS NOTICIAS", W / 2, 360, k * 3, 46, YELLOW)


SHOTS = [intro, l0_flags, l1_anchor, l2_strike, l3_hormuz, l4_island, l5_official, l6_centcom, l7_election, l8_trump, l9_pentagon,
         l10_timeline, l11_cost, l12_question, l13_truce, l14_oil, l15_campaign, l16_results, l17_deal, l18_options, outro]
STARTS = [0.0] + [l["start"] - .35 for l in LINES] + [LINES[-1]["end"] + .4]
WHIP = .22  # seconds of whip-pan transition around each cut


def draw_shot(c, i, t):
    start = STARTS[i]
    stop = STARTS[i + 1] if i + 1 < len(STARTS) else TL["duration"]
    c.save()
    SHOTS[i](c, t, (t - start) / max(.1, stop - start))
    c.restore()


def frame(c, t):
    i = max(j for j, s in enumerate(STARTS) if t >= s)
    c.clear(0xFF000000)
    draw_shot(c, i, t)
    # whip pan: a quick sideways streak right after each cut
    since = t - STARTS[i]
    if 0 < i and since < WHIP:
        k = since / WHIP
        streak = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(220 * (1 - k)), 255, 255, 255),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30))
        for j in range(8):
            yy = 60 + j * 85
            c.drawRect(skia.Rect.MakeXYWH(-200 + 1700 * k - j * 40, yy, 600, 18), streak)
        c.drawRect(skia.Rect.MakeWH(W, H), fill(skia.ColorSetARGB(int(120 * (1 - k)), 255, 255, 255)))
    vig = skia.Paint()
    vig.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * .75, [0x00000000, 0x77000000], [.55, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), vig)
    fade = max(1 - t / .4, (t - (LENGTH - .8)) / .8)
    if fade > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill(skia.ColorSetARGB(int(255 * min(1, fade)), 0, 0, 0)))
    for cue in CUES:
        if cue["start"] <= t < cue["end"] + .1:
            text = cue["text"].rstrip(".,;")
            x = (W - SUBF.measureText(text)) / 2
            c.drawString(text, x, H - 28, SUBF, line(9))
            c.drawString(text, x, H - 28, SUBF, fill(WHITE))
            break


def audio(path):
    voice, sr = sf.read(ROOT / "audio" / "narracion.wav", dtype="float32")
    voice = voice if voice.ndim == 1 else voice.mean(1)
    n = int(LENGTH * sr)
    mix = np.zeros(n, dtype=np.float32)
    v = voice[:n] / max(np.abs(voice).max(), 1e-6)
    mix[:len(v)] += v * .9
    catalog = {PureWindowsPath(i["path"]).name: i["path"] for i in json.loads(Path(r"C:\videos-youtube\sfx\catalog.json").read_text(encoding="utf-8"))}

    def clip(name, dur=None):
        cmd = ["ffmpeg", "-v", "error"] + (["-t", str(dur)] if dur else []) + ["-i", str(Path(r"C:\videos-youtube\sfx\library") / catalog[name]),
               "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
        x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)
        return x / max(np.abs(x).max(), 1e-6)

    def place(x, at, gain):
        i = int(at * sr)
        if 0 <= i < n:
            mix[i:min(n, i + len(x))] += x[:min(n, i + len(x)) - i] * gain

    bed = clip("Drone, Pulsating, Metallic_01.wav")
    while len(bed) < n:
        bed = np.concatenate([bed, bed])
    mix += bed[:n] * .05
    whoosh = clip("Whooshes_059.wav", .8)
    for s in STARTS[1:]:
        if s < LENGTH:
            place(whoosh, s - .05, .12)
    boom, hit = clip("Bluezone-BC0214-explosion-whooshe-003.wav"), clip("Bluezone-BC0226-hit-impact-004.wav")

    def at(i, frac):
        return STARTS[i] + (STARTS[i + 1] - STARTS[i]) * frac

    place(boom, at(1, .5), .45)
    place(hit, at(3, .72), .55)
    place(clip("Whooshes_135.wav", 1.5), at(3, .25), .25)
    place(boom, at(14, .55), .35)
    place(clip("Bluezone-BC0226-whoosh-impact-012.wav", 1.5), 0.6, .3)
    ticks = clip("Pressing Buttons 6.wav", .15)
    for j in range(12):
        place(ticks, at(12, .05 + j * .05), .08)
    edge = np.minimum(1, np.arange(n) / (sr * .3)) * np.minimum(1, (n - np.arange(n)) / (sr * .8))
    sf.write(path, np.stack([np.tanh(mix * edge * 1.05) * .95] * 2, 1), sr)


def main():
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    surface = skia.Surface(pixels, colorType=skia.kRGBA_8888_ColorType)
    c = surface.getCanvas()
    if "--stills" in sys.argv:
        from PIL import Image
        out = ROOT / "cuadros"
        out.mkdir(exist_ok=True)
        for v in sys.argv[sys.argv.index("--stills") + 1].split(","):
            frame(c, float(v))
            Image.fromarray(pixels[:, :, :3].copy()).save(out / f"t{float(v):06.1f}.png")
        return
    silent, mixed, final = ROOT / "noticia2_mudo.mp4", ROOT / "noticia2_audio.wav", ROOT / "noticia_iran.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for i in range(int(LENGTH * FPS)):
        frame(c, i / FPS)
        ff.stdin.write(pixels.tobytes())
    ff.stdin.close()
    ff.wait()
    audio(mixed)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(mixed), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", str(final)], check=True)
    print("ok", final)


if __name__ == "__main__":
    main()
