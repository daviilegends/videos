"""Engine for the teacher's LoL classes. An episode = guion.json + narration (narrar.py) + render.py with its scenes.

In the episode's render.py:
    import motor as M
    M.setup(__file__, lane="inferior", clase=1)
    @M.escena("hook", "aula", prof=[(0, "asombro"), ("rival", "piensa")], sfx=lambda b: [("tiza", 0)])
    def hook(c, lt, b): ...
    if __name__ == "__main__": M.main()

Scene kinds: "aula" (classroom + chalkboard) and "mapa" (2D lane; c arrives in WORLD coordinates,
use `with b.hud(c):` to draw in screen coordinates). b.at("word") = local time of that word.
Usage: render_env/Scripts/python.exe render.py [--stills 1.0,4.0 | --hoja] [--full]
"""
import json
import math
import multiprocessing as mp
import re
import subprocess
import sys
import unicodedata
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import skia
import soundfile as sf

LEAGUE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LEAGUE / "personaje"))
sys.path.insert(0, str(LEAGUE / "escenarios"))
import grieta as G  # noqa: E402
from profesora import LOOKS, POSES, profesora  # noqa: E402

W, H, FPS = 1080, 1920, 30
FONTS = "C:/Windows/Fonts/"
INK = 0xFF1E2228
CHALK, CHALK_Y, CHALK_R, CHALK_B = 0xFFF2F0E6, 0xFFF2D35A, 0xFFF08A8A, 0xFF9AD0F5
BLUE, RED, GOLD = 0xFF3FA9F5, 0xFFE84855, 0xFFE8C26A
LOOK = LOOKS["C"]
UNIT = .6  # pixels per game unit on the lane map
FOCUS = (540, 820)  # where the camera centre lands on screen

# ---------- basic helpers ----------
_fonts = {}


def font(file, size):
    k = (file, size)
    if k not in _fonts:
        _fonts[k] = skia.Font(skia.Typeface.MakeFromFile(FONTS + file), size)
    return _fonts[k]


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def stroke(w, color=INK):
    return skia.Paint(AntiAlias=True, Color=color, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def alpha(color, a):
    return (int(max(0, min(1, a)) * ((color >> 24) & 255)) << 24) | (color & 0xFFFFFF)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back(x, s=1.7):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)


def lerp(a, b, k):
    return a + (b - a) * k


def mix(p, q, k):
    return (lerp(p[0], q[0], k), lerp(p[1], q[1], k))


def pulse(lt, at, decay=6.0):
    """1 at the instant `at`, decaying afterwards."""
    return math.exp(-(lt - at) * decay) if lt >= at else 0.0


def keys(lt, frames, fn=ease):
    """Interpolates (time, value) keyframes; values may be numbers or tuples."""
    if lt <= frames[0][0]:
        return frames[0][1]
    for (t0, v0), (t1, v1) in zip(frames, frames[1:]):
        if lt < t1:
            k = fn((lt - t0) / max(1e-6, t1 - t0))
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, k) for a, b in zip(v0, v1))
            return lerp(v0, v1, k)
    return frames[-1][1]


def path(points, close=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def text(c, s, x, y, f, color, outline=0, outline_color=INK, align="c"):
    w = f.measureText(s)
    x0 = x - w / 2 if align == "c" else x
    if outline:
        c.drawString(s, x0, y, f, stroke(outline, outline_color))
    c.drawString(s, x0, y, f, fill(color))
    return w


def badge(c, s, x, y, size, bg, fg=INK, k=1.0, rot=0):
    if k <= 0:
        return
    f = font("segoeuib.ttf", size)
    w = f.measureText(s)
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    sc = back(k)
    c.scale(sc, sc)
    r = skia.Rect.MakeXYWH(-w / 2 - size * .55, -size * .95, w + size * 1.1, size * 1.35)
    c.drawRoundRect(r, size * .6, size * .6, fill(bg))
    c.drawRoundRect(r, size * .6, size * .6, stroke(max(3, size * .12)))
    c.drawString(s, -w / 2, 0, f, fill(fg))
    c.restore()


# ---------- classroom ----------
def classroom(c):
    g = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [0xFF9FD3C6, 0xFFE8CFAE])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=g))
    c.drawRect(skia.Rect.MakeXYWH(0, 1480, W, 440), fill(0xFFB57D4E))
    for j in range(6):
        c.drawLine(0, 1520 + j * 70, W, 1520 + j * 70, stroke(4, 0xFF9A6538))
    c.drawRect(skia.Rect.MakeXYWH(0, 1470, W, 22), fill(0xFF8A5A34))
    board = skia.Rect.MakeLTRB(70, 250, 1010, 1060)
    c.drawRoundRect(board.makeOutset(26, 26), 14, 14, fill(0xFF8A5A34))
    c.drawRoundRect(board.makeOutset(26, 26), 14, 14, stroke(7))
    c.drawRect(board, fill(0xFF2F5E47))
    c.drawRect(board, stroke(6))
    for x, y, r in ((240, 420, 120), (820, 900, 160), (600, 600, 90)):
        c.drawCircle(x, y, r, fill(0x10FFFFFF))
    c.drawRoundRect(skia.Rect.MakeXYWH(200, 1076, 680, 22), 8, 8, fill(0xFF8A5A34))
    c.drawRoundRect(skia.Rect.MakeXYWH(200, 1076, 680, 22), 8, 8, stroke(5))
    c.drawRoundRect(skia.Rect.MakeXYWH(300, 1066, 60, 14), 6, 6, fill(CHALK))


def chalk_line(c, s, x, y, size, k, color=CHALK, maxw=880, align="c"):
    """Chalk text written left to right (k 0..1); shrinks to fit maxw."""
    if k <= 0:
        return
    f = font("segoeprb.ttf", size)
    w = f.measureText(s)
    if w > maxw:
        f = font("segoeprb.ttf", int(size * maxw / w))
        w = f.measureText(s)
    x0 = x - w / 2 if align == "c" else x
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(x0 - 10, y - size * 1.4, x0 + w * min(1, k) + 10, y + size * .6))
    c.drawString(s, x0, y, f, fill(color))
    c.restore()


def chalk_stroke(c, pts, k, color=CHALK, w=8):
    """Draws a polyline progressively (k 0..1), like a chalk stroke."""
    if k <= 0:
        return
    p = path(pts, close=False)
    meas = skia.PathMeasure(p, False)
    out = skia.Path()
    meas.getSegment(0, meas.getLength() * min(1, k), out, True)
    c.drawPath(out, stroke(w, color))


def chalk_circle(c, x, y, r, k, color=CHALK, w=8):
    if k <= 0:
        return
    pts = [(x + math.cos(a) * r * (1 + .03 * math.sin(a * 3)), y + math.sin(a) * r) for a in np.linspace(-1.9, -1.9 + 2 * math.pi * 1.05, 50)]
    chalk_stroke(c, pts, k, color, w)


def chalk_minion(c, x, y, s, color=CHALK, k=1.0):
    if k <= 0:
        return
    p = stroke(7, alpha(color, k))
    c.drawCircle(x, y, 32 * s, p)
    c.drawPath(path([(x - 28 * s, y - 14 * s), (x, y - 62 * s), (x + 28 * s, y - 14 * s)], close=False), p)
    c.drawCircle(x - 10 * s, y + 2 * s, 4 * s, fill(alpha(color, k)))
    c.drawCircle(x + 12 * s, y + 2 * s, 4 * s, fill(alpha(color, k)))


def chalk_arrow(c, a, b, k, color=CHALK, w=8):
    chalk_stroke(c, [a, b], k, color, w)
    if k >= 1:
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for d in (2.6, -2.6):
            c.drawLine(*b, b[0] + math.cos(ang + d) * 30, b[1] + math.sin(ang + d) * 30, stroke(w, color))


def chalk_check(c, x, y, k, color=0xFF8EE08E, s=1.0):
    chalk_stroke(c, [(x - 26 * s, y), (x - 6 * s, y + 22 * s), (x + 32 * s, y - 30 * s)], k, color, 10)


def chalk_cross(c, x, y, k, color=CHALK_R, s=1.0):
    chalk_stroke(c, [(x - 30 * s, y - 30 * s), (x + 30 * s, y + 30 * s)], k * 2, color, 10)
    chalk_stroke(c, [(x + 30 * s, y - 30 * s), (x - 30 * s, y + 30 * s)], k * 2 - 1, color, 10)


# ---------- lane actors (world coordinates) ----------
_icons = {}


def icon(name):
    if name not in _icons:
        _icons[name] = skia.Image.open(str(LEAGUE / "assets" / "campeones" / f"{name}.png"))
    return _icons[name]


def champ(c, x, y, name, team, label=None, k=1.0, flash=0.0, hp=1.0, dead=0.0, s=1.0, a=1.0):
    """Champion: official icon in a circle with team ring, label (TÚ/RIVAL), name and health bar. a < 1 = hidden (brush)."""
    if k <= 0 or a <= 0:
        return
    color = BLUE if team == "azul" else RED
    if a < 1:
        c.saveLayerAlpha(None, int(255 * a))
    c.save()
    c.translate(x, y)
    sc = back(k) * s
    c.scale(sc, sc)
    c.drawOval(skia.Rect.MakeXYWH(-62, 52, 124, 34), fill(0x55000000))
    c.drawCircle(0, 0, 68, fill(0xFF13284A))
    c.save()
    c.clipPath(skia.Path.Circle(0, 0, 64), doAntiAlias=True)
    c.drawImageRect(icon(name), skia.Rect.MakeXYWH(-70, -70, 140, 140), skia.SamplingOptions(skia.FilterMode.kLinear))
    if dead > 0:
        c.drawRect(skia.Rect.MakeXYWH(-70, -70, 140, 140), fill(alpha(0xFF303030, dead * .75)))
    c.restore()
    c.drawCircle(0, 0, 68, stroke(10, color))
    c.drawCircle(0, 0, 76, stroke(4, GOLD))
    if flash > 0:
        c.drawCircle(0, 0, 66, fill(alpha(0xFFFFFFFF, flash * .8)))
    if label:
        badge(c, label, 0, 112, 30, color, 0xFFFFFFFF)
    text(c, name.upper(), 0, 156 if label else 112, font("segoeuib.ttf", 26), GOLD, 8)
    c.drawRoundRect(skia.Rect.MakeXYWH(-60, -104, 120, 14), 7, 7, fill(0xFF0A1424))
    if hp > 0:
        c.drawRoundRect(skia.Rect.MakeXYWH(-60, -104, 120 * clamp(hp), 14), 7, 7, fill(0xFF4CD07A if team == "azul" else RED))
    c.drawRoundRect(skia.Rect.MakeXYWH(-60, -104, 120, 14), 7, 7, stroke(3, GOLD))
    c.restore()
    if a < 1:
        c.restore()


def minion(c, x, y, team, face=1.0, t=0.0, kind="melee", flash=0.0, pop=0.0, s=1.0, swing=0.0):
    """Minion; face -1..1 = gaze direction; pop 0..1 = death animation; swing 0..1 = attack lunge."""
    if pop >= 1:
        return
    body, dark = (0xFF4A8FE0, 0xFF27508A) if team == "azul" else (0xFFE5484D, 0xFF8E2A33)
    if flash > 0:
        body = 0xFFFFD0D0
    c.save()
    c.translate(x + face * swing * 18, y + math.sin(t * 8 + x * .01) * 3)
    sc = s * (1 + pop * .5) * {"canon": 1.25, "super": 1.6}.get(kind, 1.0)
    c.scale(sc, sc)
    a = 1 - pop
    c.drawOval(skia.Rect.MakeXYWH(-34, 30, 68, 16), fill(alpha(0x55000000, a)))
    c.drawPath(skia.Path.Oval(skia.Rect.MakeXYWH(-32, -30, 64, 66)), fill(alpha(body, a)))
    c.drawPath(skia.Path.Oval(skia.Rect.MakeXYWH(-32, -30, 64, 66)), stroke(6, alpha(INK, a)))
    if kind == "mago":
        hat = path([(-34, -14), (0, -66), (34, -14)])
        c.drawPath(hat, fill(alpha(dark, a)))
        c.drawPath(hat, stroke(6, alpha(INK, a)))
        c.drawCircle(0, -70, 9, fill(alpha(0xFFFFE27A, a)))
    elif kind == "super":
        horns = path([(-34, -6), (-44, -50), (-14, -26), (0, -60), (14, -26), (44, -50), (34, -6)])
        c.drawPath(horns, fill(alpha(0xFF6A3AA8 if team == "rojo" else 0xFF2A9A8A, a)))
        c.drawPath(horns, stroke(6, alpha(INK, a)))
    elif kind == "canon":
        c.drawRoundRect(skia.Rect.MakeXYWH(face * 10 - 10 + (face > 0) * 6, -6, 46 * (1 if face >= 0 else -1), 22), 8, 8, fill(alpha(0xFF555A60, a)))
        c.drawRoundRect(skia.Rect.MakeXYWH(-26, -46, 52, 26), 10, 10, fill(alpha(dark, a)))
        c.drawRoundRect(skia.Rect.MakeXYWH(-26, -46, 52, 26), 10, 10, stroke(6, alpha(INK, a)))
    else:
        helm = path([(-30, -8), (0, -58), (30, -8)])
        c.drawPath(helm, fill(alpha(dark, a)))
        c.drawPath(helm, stroke(6, alpha(INK, a)))
    for sx in (-1, 1):
        ex = face * 12 + sx * 11
        c.drawCircle(ex, 4, 7, fill(alpha(0xFFFFF4C8, a)))
        c.drawCircle(ex + face * 2, 5, 3.5, fill(alpha(INK, a)))
    c.restore()
    if pop > 0:  # sparks
        for j in range(8):
            ang = j * math.pi / 4 + .3
            r = 30 + pop * 70
            c.drawCircle(x + math.cos(ang) * r, y + math.sin(ang) * r, 9 * (1 - pop), fill(alpha(body, 1 - pop)))


def shot(c, a, b, k, kind="bala", color=BLUE):
    """Projectile from a to b, k 0..1 (not drawn outside that range)."""
    if not 0 <= k < 1:
        return
    p = mix(a, b, k)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    if kind == "hacha":  # spinning axe
        c.save()
        c.translate(*p)
        c.rotate(k * 900)
        c.drawLine(-30, 0, 30, 0, stroke(10, 0xFF6B4A2B))
        blade = path([(16, -6), (40, -30), (48, 0), (40, 30), (16, 6)])
        c.drawPath(blade, fill(0xFFE84855))
        c.drawPath(blade, stroke(5))
        c.restore()
        return
    if kind == "torre":
        glow = skia.Paint(AntiAlias=True, Color=alpha(color, .6), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
        q = mix(a, b, max(0, k - .25))
        c.drawLine(*q, *p, stroke(26, alpha(color, .45)))
        c.drawCircle(*p, 34, glow)
        c.drawCircle(*p, 22, fill(0xFFFFF4E0))
        c.drawCircle(*p, 22, stroke(6, color))
        return
    if kind == "flecha":
        c.save()
        c.translate(*p)
        c.rotate(math.degrees(ang))
        c.drawLine(-50, 0, 20, 0, stroke(8, 0xFFBFE8FF))
        c.drawPath(path([(20, -14), (44, 0), (20, 14)]), fill(0xFF8FD0EA))
        c.drawPath(path([(20, -14), (44, 0), (20, 14)]), stroke(4))
        c.restore()
        return
    big = kind == "habilidad"
    q = mix(a, b, max(0, k - (.3 if big else .18)))
    c.drawLine(*q, *p, stroke(30 if big else 16, alpha(color, .5)))
    c.drawCircle(*p, 26 if big else 16, fill(0xFFF4FBFF))
    c.drawCircle(*p, 26 if big else 16, stroke(5, color))


def burst(c, p, k, color=0xFFFFE27A, r=80):
    """Impact star; k = remaining intensity (1 -> 0)."""
    if k <= .02:
        return
    for j in range(8):
        a = j * math.pi / 4 + .2
        r0, r1 = r + (1 - k) * 40, r + 30 + (1 - k) * 60
        c.drawLine(p[0] + math.cos(a) * r0, p[1] + math.sin(a) * r0, p[0] + math.cos(a) * r1, p[1] + math.sin(a) * r1,
                   stroke(8, alpha(color, k)))


def ring(c, p, r, k, color=RED, label=None, t=0.0, label_dy=None):
    if k <= 0:
        return
    pp = stroke(6, alpha(color, k))
    pp.setPathEffect(skia.DashPathEffect.Make([22, 14], t * 40))
    c.drawCircle(*p, r * back(k), fill(alpha((color & 0xFFFFFF) | 0x30000000, k)))
    c.drawCircle(*p, r * back(k), pp)
    if label:
        badge(c, label, p[0], p[1] - r - 20 if label_dy is None else p[1] + label_dy, 34, color, 0xFFFFFFFF, k)


def target_line(c, a, b, k, color=RED, t=0.0):
    if k <= 0:
        return
    end = mix(a, b, k)
    pp = stroke(7, alpha(color, .9))
    pp.setPathEffect(skia.DashPathEffect.Make([18, 12], -t * 60))
    c.drawLine(*a, *end, pp)
    c.drawCircle(*end, 12, fill(color))


def lock(c, x, y, k):
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(back(k), back(k))
    c.drawPath(path([(-14, -10), (-14, -26), (14, -26), (14, -10)], close=False), stroke(7))
    c.drawRoundRect(skia.Rect.MakeXYWH(-22, -12, 44, 34), 6, 6, fill(GOLD))
    c.drawRoundRect(skia.Rect.MakeXYWH(-22, -12, 44, 34), 6, 6, stroke(5))
    c.restore()


def turret_heat(c, x, y, level, k):
    """Heat meter above a turret: level 0..3 (+0%..+150%)."""
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(back(k), back(k))
    for j in range(4):
        on = j <= level
        col = [0xFFFFE27A, 0xFFFFB14A, 0xFFFF7A3A, 0xFFE8343A][j]
        r = skia.Rect.MakeXYWH(-110 + j * 56, -20, 50, 40)
        c.drawRoundRect(r, 8, 8, fill(col if on else 0xFF3A3F48))
        c.drawRoundRect(r, 8, 8, stroke(5))
    c.restore()


# ---------- HUD ----------
def sign(c, t, k, l1, l2):
    """Hanging wooden sign with chalk lettering."""
    if k <= 0:
        return
    c.save()
    c.translate(540, -60 + 110 * back(k))
    c.rotate(math.sin(t * 2) * 1.5 * (1 - ease(k)) + math.sin(t * 1.3) * .6)
    for sx in (-1, 1):
        c.drawLine(sx * 250, -80, sx * 250, 40, stroke(8, 0xFF5A3A22))
    board = skia.Rect.MakeXYWH(-330, 30, 660, 190)
    c.drawRoundRect(board.makeOutset(16, 16), 18, 18, fill(0xFF8A5A34))
    c.drawRoundRect(board.makeOutset(16, 16), 18, 18, stroke(7))
    c.drawRect(board, fill(0xFF2F5E47))
    c.drawRect(board, stroke(5))
    for s_, y, col in ((l1, 110, CHALK), (l2, 190, CHALK_Y)):
        f = font("segoeprb.ttf", 66)
        if f.measureText(s_) > 600:
            f = font("segoeprb.ttf", int(66 * 600 / f.measureText(s_)))
        text(c, s_, 0, y, f, col)
    c.restore()


def caption(c, s_, k, color=0xFFFFFFFF, y=1300, size=56):
    if k <= 0:
        return
    f = font("segoeuib.ttf", size)
    w = f.measureText(s_)
    if w > 960:
        f = font("segoeuib.ttf", int(size * 960 / w))
        w = f.measureText(s_)
    c.save()
    c.translate(540, y)
    sc = back(k)
    c.scale(sc, sc)
    r = skia.Rect.MakeXYWH(-w / 2 - 28, -size, w + 56, size * 1.36)
    c.drawRoundRect(r, 38, 38, fill(0xDD14181C))
    c.drawRoundRect(r, 38, 38, stroke(4, color))
    c.drawString(s_, -w / 2, 0, f, fill(color))
    c.restore()


def big_number(c, s_, x, y, k, color=GOLD, size=170, rot=-6):
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    sc = back(k, 2.4)
    c.scale(sc, sc)
    text(c, s_, 0, 0, font("segoeuib.ttf", size), color, 22)
    c.restore()


def minion_hp(c, x, y, hp, s=1.0, team="rojo"):
    """Small health bar over a minion."""
    w = 80 * s
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y - 90 * s, w, 12), 6, 6, fill(0xFF0A1424))
    if hp > 0:
        c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y - 90 * s, w * clamp(hp), 12), 6, 6, fill(RED if team == "rojo" else 0xFF4CD07A))
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y - 90 * s, w, 12), 6, 6, stroke(3, GOLD))


def ward(c, x, y, k, t=0.0, team="azul", reveal=0.0):
    """Ward totem; reveal > 0 draws its sight circle."""
    if k <= 0:
        return
    col = 0xFFF2D35A if team == "azul" else 0xFFE84855
    if reveal > 0:
        c.drawCircle(x, y, 380 * ease(reveal), fill(alpha(0x33FFF2B0, reveal)))
        pp = stroke(5, alpha(0xFFF2D35A, reveal))
        pp.setPathEffect(skia.DashPathEffect.Make([18, 12], t * 30))
        c.drawCircle(x, y, 380 * ease(reveal), pp)
    c.save()
    c.translate(x, y - (1 - back(k)) * 120)
    c.drawOval(skia.Rect.MakeXYWH(-30, 18, 60, 18), fill(0x55000000))
    c.drawRoundRect(skia.Rect.MakeXYWH(-10, -40, 20, 64), 8, 8, fill(0xFF6B4A2B))
    c.drawRoundRect(skia.Rect.MakeXYWH(-10, -40, 20, 64), 8, 8, stroke(5))
    glow = .6 + .4 * math.sin(t * 4)
    p = skia.Paint(AntiAlias=True, Color=alpha(col, .6 * glow), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    c.drawCircle(0, -58, 30, p)
    c.drawOval(skia.Rect.MakeXYWH(-26, -76, 52, 36), fill(0xFFFFFFFF))
    c.drawOval(skia.Rect.MakeXYWH(-26, -76, 52, 36), stroke(5))
    c.drawCircle(0, -58, 11, fill(col))
    c.drawCircle(0, -58, 5, fill(INK))
    c.restore()


def recall_fx(c, x, y, k, t=0.0, cancel=0.0):
    """Recall channel: blue rings + progress bar (k 0..1); cancel > 0 = it breaks (red)."""
    if k <= 0 and cancel <= 0:
        return
    if cancel <= 0:
        for j in range(3):
            ph = (t * .8 + j / 3) % 1
            c.drawCircle(x, y, 90 + ph * 60, stroke(6, alpha(0xFF6FC3FF, (1 - ph) * .9)))
        p = skia.Paint(AntiAlias=True, Color=alpha(0xFF6FC3FF, .35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30))
        c.drawCircle(x, y, 120, p)
    w = 220
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y + 190, w, 26), 13, 13, fill(0xEE0A1424))
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y + 190, w * clamp(k), 26), 13, 13, fill(0xFF6FC3FF if cancel <= 0 else RED))
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y + 190, w, 26), 13, 13, stroke(4, GOLD))
    text(c, "RECALL", x, y + 250, font("segoeuib.ttf", 30), 0xFFFFFFFF, 8)
    if cancel > 0:
        burst(c, (x, y), 1 - cancel, RED, 90)


def flash_fx(c, a, b, k):
    """Flash: puff where you leave, puff where you arrive (k = seconds after the cast)."""
    spell_pop(c, "SummonerFlash", b[0], b[1] - 190, k, 100)
    if not 0 <= k < 1.2:
        return
    for p, kk in ((a, k), (b, k - .05)):
        if kk > 0:
            f = 1 - min(1, kk / .6)
            for j in range(10):
                ang = j * math.pi / 5
                r = 40 + (1 - f) * 90
                c.drawCircle(p[0] + math.cos(ang) * r, p[1] + math.sin(ang) * r, 12 * f + 1, fill(alpha(0xFFFFF3A0, f)))
            c.drawCircle(*p, 70 * (1 - f) + 20, stroke(8, alpha(0xFFFFF3A0, f)))
    f = 1 - min(1, k / .4)
    if f > 0:
        c.drawLine(*a, *b, stroke(14, alpha(0x99FFF3A0, f)))


# ---------- official monster renders (assets/monstruos, from the LoL wiki; allowed by Riot's Legal Jibber Jabber) ----------
_sprites = {}
# target height in px at s=1 (keeps the old footprint of the cartoon monsters)
SPRITE_H = {"baron": 620, "heraldo": 300, "larva": 190, "cangrejo": 280, "azul": 260, "rojo": 240, "gromp": 220,
            "lobo": 250, "lobo_chico": 170, "ave": 210, "krug": 230}
DRAGON_COLORS = {0xFFFF8A3A: "dragon_infernal", 0xFF3FA9C5: "dragon_oceano", 0xFFB9A6E8: "dragon_ancestral"}


def sprite_img(name):
    if name not in _sprites:
        _sprites[name] = skia.Image.open(str(LEAGUE / "assets" / "monstruos" / f"{name}.png"))
    return _sprites[name]


def sprite(c, name, x, y, s, t, k=1.0, flash=0.0, flip=False, h=None):
    """Official render standing with its feet at (x, y + 60*s): pops in with back(k), breathes (squash), bobs,
    flashes white when hit. Returns the screen y of the top of the image (for health bars)."""
    if k <= 0:
        return y
    s *= max(1.0, .85 / S.get("zoom", 1.0))   # wide shots: keep monsters readable
    img = sprite_img(name)
    if h is None:
        h = SPRITE_H.get(name, 200 if not name.startswith("dragon") else 330)
    sc = s * back(min(1, k)) * h / img.height()
    if name.startswith("dragon") and img.width() / img.height() > 1.6:   # very wide drakes: limit by width
        sc = min(sc, s * back(min(1, k)) * 520 / img.width())
    w, hh = img.width() * sc, img.height() * sc
    flying = name.startswith("dragon")
    bob = math.sin(t * (2.2 if flying else 3)) * (10 if flying else 4) * s
    breath = 1 + math.sin(t * 3.1) * .025
    foot = y + 60 * s
    c.drawOval(skia.Rect.MakeXYWH(x - w * .38, foot - 14 * s + (30 * s if flying else 0), w * .76, 30 * s), fill(0x55000000))
    c.save()
    c.translate(x, foot + bob - (40 * s if flying else 0))
    c.scale(-1 if flip else 1, 1)
    c.scale(1 / breath, breath)
    p = skia.Paint(AntiAlias=True)
    if flash > 0:
        cf = skia.ColorFilters.Blend(skia.ColorSetARGB(int(255 * min(1, flash)), 255, 255, 255), skia.BlendMode.kSrcATop)
        if cf is not None:
            p.setColorFilter(cf)
    c.drawImageRect(img, skia.Rect.MakeXYWH(-w / 2, -hh, w, hh), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)
    c.restore()
    return foot + bob - (40 * s if flying else 0) - hh


def dragon(c, x, y, s, t, color=0xFFFF8A3A, k=1.0, hp=1.0, label=None, sprite_name=None):
    """Drake: official render (by sprite_name, or guessed from the colour); cartoon fallback if unknown."""
    if k <= 0:
        return
    name = sprite_name or DRAGON_COLORS.get(color)
    if name:
        top = sprite(c, name, x, y, s, t, k)
        if hp < 1:
            bar(c, x, top - 20, 180 * s, hp)
        if label:
            badge(c, label, x, y + 150 * s, 30, color, 0xFFFFFFFF)
        return
    flap = math.sin(t * 7) * 18
    c.save()
    c.translate(x, y + math.sin(t * 2) * 8)
    c.scale(s * back(k), s * back(k))
    c.drawOval(skia.Rect.MakeXYWH(-90, 70, 180, 40), fill(0x55000000))
    for sx in (-1, 1):
        wing = path([(sx * 30, -10), (sx * 150, -70 - flap), (sx * 130, 10 - flap * .3), (sx * 95, -5), (sx * 70, 30)])
        c.drawPath(wing, fill(color))
        c.drawPath(wing, stroke(6))
    c.drawOval(skia.Rect.MakeXYWH(-55, -40, 110, 120), fill(color))
    c.drawOval(skia.Rect.MakeXYWH(-55, -40, 110, 120), stroke(7))
    c.drawOval(skia.Rect.MakeXYWH(-30, 0, 60, 70), fill(0xFFFFE2B0))
    c.drawOval(skia.Rect.MakeXYWH(-45, -105, 90, 80), fill(color))
    c.drawOval(skia.Rect.MakeXYWH(-45, -105, 90, 80), stroke(7))
    for sx in (-1, 1):
        c.drawPath(path([(sx * 20, -98), (sx * 32, -140), (sx * 40, -94)]), fill(0xFFFFF4C8))
        c.drawPath(path([(sx * 20, -98), (sx * 32, -140), (sx * 40, -94)]), stroke(5))
        c.drawCircle(sx * 18, -70, 10, fill(0xFFFFFFFF))
        c.drawCircle(sx * 18, -68, 5, fill(INK))
    c.restore()
    if hp < 1:
        c.drawRoundRect(skia.Rect.MakeXYWH(x - 90 * s, y - 175 * s, 180 * s, 16), 8, 8, fill(0xFF0A1424))
        c.drawRoundRect(skia.Rect.MakeXYWH(x - 90 * s, y - 175 * s, 180 * s * clamp(hp), 16), 8, 8, fill(0xFFB06CF0))
        c.drawRoundRect(skia.Rect.MakeXYWH(x - 90 * s, y - 175 * s, 180 * s, 16), 8, 8, stroke(3, GOLD))
    if label:
        badge(c, label, x, y + 150 * s, 30, color, 0xFFFFFFFF)


ICON_COLORS = {0xFFFF8A3A: "monstruos/dragon_infernal", 0xFF3FA9C5: "monstruos/dragon_ocean", 0xFFB9A6E8: "monstruos/dragon_elder"}


def icono(c, rel, x, y, size, k=1.0, alpha=1.0):
    """Official icon from assets/iconos/<rel>.png centred at (x, y), popping in with back(k)."""
    if k <= 0:
        return
    key = "ico:" + rel
    if key not in _sprites:
        _sprites[key] = skia.Image.open(str(LEAGUE / "assets" / "iconos" / f"{rel}.png"))
    img = _sprites[key]
    sz = size * back(min(1, k))
    p = skia.Paint(AntiAlias=True)
    if alpha < 1:
        p.setAlphaf(alpha)
    c.drawImageRect(img, skia.Rect.MakeXYWH(x - sz / 2, y - sz / 2, sz, sz), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)


def spell_pop(c, rel, x, y, k, size=110, dur=1.3):
    """Official spell icon popping above a caster (k = seconds since the cast), gold frame, rises and fades."""
    if not 0 <= k < dur:
        return
    a = 1 - max(0, k - dur + .35) / .35
    yy = y - 30 * ease(min(1, k / .4))
    sz = size * back(min(1, k / .25))
    c.drawRoundRect(skia.Rect.MakeXYWH(x - sz / 2 - 6, yy - sz / 2 - 6, sz + 12, sz + 12), 14, 14, fill(alpha(0xFF0A1424, a)))
    icono(c, rel, x, yy, sz, 1, a)
    c.drawRoundRect(skia.Rect.MakeXYWH(x - sz / 2 - 6, yy - sz / 2 - 6, sz + 12, sz + 12), 14, 14, stroke(5, alpha(GOLD, a)))


def spell_cd(c, rel, x, y, size, frac, k=1.0, secs=None):
    """In-game style cooldown: official icon, dark sweep over the remaining fraction (clockwise from 12), seconds
    left in the centre, gold frame; glows when ready (frac 0)."""
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    sc = back(min(1, k))
    c.scale(sc, sc)
    h = size / 2
    c.drawRoundRect(skia.Rect.MakeXYWH(-h - 8, -h - 8, size + 16, size + 16), 18, 18, fill(0xEE0A1424))
    icono(c, rel, 0, 0, size)
    frac = clamp(frac)
    if frac > 0:
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(-h, -h, size, size))
        p = skia.Path()
        p.moveTo(0, 0)
        p.arcTo(skia.Rect.MakeXYWH(-size, -size, 2 * size, 2 * size), -90, -360 * frac, False)
        p.close()
        c.drawPath(p, fill(0xB0000000))
        c.restore()
        if secs is not None:
            text(c, f"{secs}", 0, size * .17, font("segoeuib.ttf", int(size * .42)), 0xFFFFFFFF, 10)
    else:
        glow = skia.Paint(AntiAlias=True, Color=0x88FFE27A, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
        c.drawRoundRect(skia.Rect.MakeXYWH(-h - 8, -h - 8, size + 16, size + 16), 18, 18, glow)
        icono(c, rel, 0, 0, size)
    c.drawRoundRect(skia.Rect.MakeXYWH(-h - 8, -h - 8, size + 16, size + 16), 18, 18, stroke(6, GOLD))
    c.restore()


def bar(c, x, y, w, hp):
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y, w, 16), 8, 8, fill(0xFF0A1424))
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y, w * clamp(hp), 16), 8, 8, fill(0xFFB06CF0))
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y, w, 16), 8, 8, stroke(3, GOLD))


def pizarra(id_, lineas, prof=None, extra=None, sfx_extra=None, sub_y=None):
    """Data-driven classroom scene. lineas: (text, x, y, size, color, when[, dur, align]); `when` = local time or a
    word of the line. Each line gets a chalk sound. extra(c, lt, b) draws more on top."""
    def fn(c, lt, b):
        for L in lineas:
            txt, x, y, size, col, when = L[:6]
            dur = L[6] if len(L) > 6 else .5
            align = L[7] if len(L) > 7 else "c"
            chalk_line(c, txt, x, y, size, (lt - _resolve(b, when)) / dur, col, 880 if align == "c" else 960 - x, align)
        if extra:
            extra(c, lt, b)

    def sfx(b):
        return [("tiza", _resolve(b, L[5]), .7) for L in lineas] + (sfx_extra(b) if sfx_extra else [])
    escena(id_, "aula", prof=prof, sfx=sfx, sub_y=sub_y)(fn)
    return fn


# ---------- comedy gags ----------
def fist(c, x, y, s=1.0, rot=0.0, color=0xFFF2C29B):
    """Cartoon fist (glove) pointing right."""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    c.drawRoundRect(skia.Rect.MakeXYWH(-120, -26, 90, 52), 16, 16, fill(0xFF6B2340))
    c.drawRoundRect(skia.Rect.MakeXYWH(-120, -26, 90, 52), 16, 16, stroke(6))
    c.drawRoundRect(skia.Rect.MakeXYWH(-40, -48, 96, 96), 34, 34, fill(color))
    c.drawRoundRect(skia.Rect.MakeXYWH(-40, -48, 96, 96), 34, 34, stroke(7))
    for j in range(3):
        c.drawLine(20, -26 + j * 24, 50, -26 + j * 24, stroke(5))
    c.drawRoundRect(skia.Rect.MakeXYWH(-26, -66, 46, 30), 12, 12, fill(color))
    c.drawRoundRect(skia.Rect.MakeXYWH(-26, -66, 46, 30), 12, 12, stroke(6))
    c.restore()


def dizzy(c, x, y, k, t, r=70):
    """Stars circling over a head."""
    if k <= 0:
        return
    for j in range(4):
        a = t * 5 + j * math.pi / 2
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * .35
        star = skia.Path()
        for q in range(10):
            rr = 20 if q % 2 == 0 else 9
            aa = q * math.pi / 5 - math.pi / 2
            (star.moveTo if q == 0 else star.lineTo)(px + math.cos(aa) * rr * k, py + math.sin(aa) * rr * k)
        star.close()
        c.drawPath(star, fill(0xFFFFE27A))
        c.drawPath(star, stroke(4))


def tamal(c, x, y, s, k, t=0.0):
    if k <= 0:
        return
    c.save()
    c.translate(x, y + math.sin(t * 6) * 6)
    c.scale(s * back(k), s * back(k))
    husk = skia.Path()
    husk.moveTo(-70, 10)
    husk.quadTo(-80, -40, -20, -55)
    husk.lineTo(60, -30)
    husk.quadTo(90, 0, 60, 30)
    husk.lineTo(-20, 50)
    husk.quadTo(-70, 50, -70, 10)
    husk.close()
    c.drawPath(husk, fill(0xFFE9D08A))
    c.drawPath(husk, stroke(6))
    c.drawRoundRect(skia.Rect.MakeXYWH(-45, -28, 85, 56), 24, 24, fill(0xFFF5C451))
    c.drawRoundRect(skia.Rect.MakeXYWH(-45, -28, 85, 56), 24, 24, stroke(5))
    for j in range(3):
        c.drawLine(-50 + j * 30, -40, -40 + j * 30, 40, stroke(3, 0x66806030))
    c.restore()


def heart(c, x, y, r, k):
    if k <= 0:
        return
    p = skia.Path()
    p.moveTo(x, y + r * .9)
    p.cubicTo(x - r * 1.6, y - r * .2, x - r * .6, y - r * 1.4, x, y - r * .4)
    p.cubicTo(x + r * .6, y - r * 1.4, x + r * 1.6, y - r * .2, x, y + r * .9)
    c.drawPath(p, fill(alpha(0xFFFF5A7A, k)))
    c.drawPath(p, stroke(4, alpha(INK, k)))


def steam(c, x, y, k, t):
    if k <= 0:
        return
    for j in range(3):
        ph = (t * .8 + j / 3) % 1
        a = alpha(0xFFFFFFFF, k * (1 - ph) * .9)
        c.drawCircle(x + math.sin(t * 3 + j * 2) * 30 + (j - 1) * 40, y - ph * 160, 26 + ph * 30, fill(a))


def slap(c, x, y, k, rot=0.0):
    """Open hand (slap) arriving from the left; k 0..1."""
    if k <= 0:
        return
    c.save()
    c.translate(x - (1 - ease(k)) * 200, y)
    c.rotate(rot)
    palm = skia.Rect.MakeXYWH(-40, -50, 80, 100)
    for j in range(4):
        c.drawRoundRect(skia.Rect.MakeXYWH(-36 + j * 20, -110, 18, 70), 9, 9, fill(0xFFF2C29B))
        c.drawRoundRect(skia.Rect.MakeXYWH(-36 + j * 20, -110, 18, 70), 9, 9, stroke(5))
    c.drawRoundRect(palm, 28, 28, fill(0xFFF2C29B))
    c.drawRoundRect(palm, 28, 28, stroke(6))
    c.drawRoundRect(skia.Rect.MakeXYWH(-80, -30, 50, 26), 12, 12, fill(0xFFF2C29B))
    c.drawRoundRect(skia.Rect.MakeXYWH(-80, -30, 50, 26), 12, 12, stroke(5))
    c.restore()


def pow_text(c, s_, x, y, k, color=0xFFFFE27A, size=90, rot=-8):
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    sc = back(k, 2.6)
    c.scale(sc, sc)
    burst_p = skia.Path()
    for q in range(16):
        rr = size * (1.15 if q % 2 == 0 else .8)
        a = q * math.pi / 8
        (burst_p.moveTo if q == 0 else burst_p.lineTo)(math.cos(a) * rr * 1.5, math.sin(a) * rr)
    burst_p.close()
    c.drawPath(burst_p, fill(0xFFE84855))
    c.drawPath(burst_p, stroke(7))
    text(c, s_, 0, size * .32, font("segoeuib.ttf", size), color, 14)
    c.restore()


def teemo_punch(c, lt, hits, x=740, y=1240, k_in=1.0, t=0.0):
    """HUD gag: Teemo's icon gets punched at each time in `hits` (local times)."""
    if k_in <= 0:
        return
    last = max([h for h in hits if lt >= h], default=None)
    sq = pulse(lt, last, 7) if last is not None else 0
    dead = lt >= hits[-1] + .4
    c.save()
    c.translate(x + sq * 40, y)
    c.rotate(sq * 25 + (12 if dead else 0) * ease((lt - hits[-1] - .4) / .3))
    c.scale(back(k_in) * (1 + sq * .15), back(k_in) * (1 - sq * .25))
    c.drawCircle(0, 0, 105, fill(0xFF13284A))
    c.save()
    c.clipPath(skia.Path.Circle(0, 0, 98), doAntiAlias=True)
    c.drawImageRect(icon("Teemo"), skia.Rect.MakeXYWH(-105, -105, 210, 210), skia.SamplingOptions(skia.FilterMode.kLinear))
    c.restore()
    c.drawCircle(0, 0, 105, stroke(12, RED))
    c.drawCircle(0, 0, 116, stroke(5, GOLD))
    c.restore()
    text(c, "TEEMO", x, y + 170, font("segoeuib.ttf", 40), GOLD, 10)
    for h in hits:  # each punch: fist flies in from the left
        k = (lt - h + .22) / .22
        if 0 < k < 1.6:
            px = lerp(x - 520, x - 150, ease(min(1, k)))
            fist(c, px, y + 10, 1.5, 0)
        pow_text(c, "¡PUM!", x - 40, y - 190, clamp((lt - h) / .2) * (1 if lt - h < 1.0 else max(0, 1 - (lt - h - 1.0) / .3)))
    if dead:
        dizzy(c, x, y - 120, 1, t)


# ---------- episode state ----------
class Beat:
    def __init__(self, idx, line, words, spec):
        self.idx, self.id = idx, line["id"]
        self.t0, self.end_abs = line["start"], line["end"]
        self.words = [dict(w=w["w"], s=w["s"] - self.t0, e=w["e"] - self.t0) for w in words]
        self.kind = spec["kind"]
        self.fn, self.spec = spec["fn"], spec
        self.dur = None  # local time until the next line starts
        self.end = self.end_abs - self.t0

    def at(self, key, n=0, end=False):
        key = norm(key)
        hits = [w for w in self.words if norm(w["w"]).startswith(key)]
        if len(hits) <= n:
            raise KeyError(f"'{key}' is not in line '{self.id}': {[w['w'] for w in self.words]}")
        return hits[n]["e" if end else "s"]

    @contextmanager
    def hud(self, c):
        c.save()
        c.resetMatrix()
        try:
            yield c
        finally:
            c.restore()


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9ñ]", "", "".join(ch for ch in s if unicodedata.category(ch) != "Mn"))


S = dict(specs={}, beats=[], ep=None)


def setup(file, lane="inferior", clase=1):
    ep = Path(file).resolve().parent
    S.update(ep=ep, lane=lane, clase=clase)
    S["guion"] = json.loads((ep / "guion.json").read_text(encoding="utf-8"))
    lineas = ep / "lineas.json"
    if lineas.exists():
        S["lineas"] = json.loads(lineas.read_text(encoding="utf-8"))
        S["palabras"] = {p["id"]: p["words"] for p in json.loads((ep / "palabras.json").read_text(encoding="utf-8"))}
        audio, sr = sf.read(ep / "narracion.wav")
        S["audio"], S["sr"] = (audio if audio.ndim == 1 else audio.mean(1)), sr


def escena(id_, kind="aula", prof=None, sfx=None, cam=None, sub_y=None, teacher=True):
    def deco(fn):
        S["specs"][id_] = dict(kind=kind, fn=fn, prof=prof, sfx=sfx, cam=cam, sub_y=sub_y, teacher=teacher)
        return fn
    return deco


def amp(t):
    """Mouth opening 0..1 from the narration: RMS over ~50 ms with a noise floor, so the mouth closes in pauses."""
    a, sr = S["audio"], S["sr"]
    i = int(t * sr)
    w = int(sr * .025)
    seg = a[max(0, i - w):i + w]
    if len(seg) == 0:
        return 0.0
    rms = float(np.sqrt(np.mean(seg ** 2)))
    return max(0.0, min(1.0, (rms - .012) * 11))


def blink_at(t):
    ph = (t * 1000) % 3700 / 1000
    return 1.0 if ph < .13 else 0.0


def _resolve(b, when):
    return b.at(when) if isinstance(when, str) else when


def build():
    specs = S["specs"]
    missing = [ln["id"] for ln in S["lineas"] if ln["id"] not in specs]
    if missing:
        raise SystemExit(f"scenes missing for: {missing}")
    beats = [Beat(i, ln, S["palabras"][ln["id"]], specs[ln["id"]]) for i, ln in enumerate(S["lineas"])]
    for b, nxt in zip(beats, beats[1:]):
        b.dur = nxt.t0 - b.t0
    beats[-1].dur = beats[-1].end + 2.2
    S["beats"] = beats
    S["DUR"] = beats[-1].t0 + beats[-1].dur
    # teacher keyframes on a global clock (continuous between scenes of the same kind)
    gk = []
    for b in beats:
        prof = b.spec["prof"] or ([(0, "explica")] if b.kind == "aula" else [(0, "puntero")])
        prof = prof(b) if callable(prof) else prof
        for item in prof:
            when, base = item[0], item[1]
            kw = item[2] if len(item) > 2 else {}
            pose = dict(POSES[base])
            if b.kind == "mapa" and base != "puntero":
                pose.setdefault("dir", -1)
            pose.update(kw)
            gk.append((b.t0 + _resolve(b, when), b.idx, pose))
        cams = b.spec["cam"]
        if b.kind == "mapa":
            cams = cams(b) if callable(cams) else (cams or [(0, (540, 960, 1.0))])
            if isinstance(cams, tuple):
                cams = [(0, cams)]
            b.cams = [(b.t0 + _resolve(b, w), v) for w, v in cams]
    S["gk"] = gk
    # subtitles: chunks of up to 3 words, cut at punctuation
    subs = []
    for b in beats:
        cur = []
        for w in b.words:
            cur.append(dict(w=w["w"], s=w["s"] + b.t0, e=w["e"] + b.t0))
            if len(cur) == 3 or w["w"][-1] in ",.?:!":
                subs.append(cur)
                cur = []
        if cur:
            subs.append(cur)
    S["subs"] = subs


def segment_of(i):
    """First and last beat index of the run of same-kind scenes containing i."""
    beats = S["beats"]
    a = i
    while a > 0 and beats[a - 1].kind == beats[i].kind:
        a -= 1
    z = i
    while z < len(beats) - 1 and beats[z + 1].kind == beats[i].kind:
        z += 1
    return a, z


NUM = ("hand_l", "hand_r", "tilt", "lean")


def teacher_pose(t, i):
    a, z = segment_of(i)
    ks = [k for k in S["gk"] if a <= k[1] <= z]
    cur = [k for k in ks if k[0] <= t]
    if not cur:
        return dict(ks[0][2])
    k1 = cur[-1]
    prev = cur[-2] if len(cur) > 1 else None
    if prev is None:
        return dict(k1[2])
    f = back((t - k1[0]) / .38)
    pose = dict(k1[2] if f > .5 else prev[2])
    for n in NUM:
        p0, p1 = prev[2].get(n), k1[2].get(n)
        if p0 is None or p1 is None:
            continue
        pose[n] = tuple(lerp(u, v, f) for u, v in zip(p0, p1)) if isinstance(p0, tuple) else lerp(p0, p1, f)
    if (prev[2].get("dir", 1) != k1[2].get("dir", 1)):
        pose["dir"] = k1[2].get("dir", 1)
    return pose


def draw_teacher(c, t, b):
    a, _ = segment_of(b.idx)
    enter = t - S["beats"][a].t0 + .12
    pose = teacher_pose(t, b.idx)
    pose["talk"] = amp(t)  # always the real voice: the poses' fixed talk values must not freeze the mouth
    pose.setdefault("blink", blink_at(t))
    if b.kind == "aula":
        profesora(c, 540, 1950 + (1 - back(enter / .45)) * 650, 2.0, t, pose, LOOK)
    else:
        if pose.get("dir", 1) == 1 and "pointer_r" in pose:
            pose["dir"] = -1
        profesora(c, 900, 1895 + (1 - ease(enter / .35)) * 480, 1.25, t, pose, LOOK)


def camera(t, i):
    a, z = segment_of(i)
    ks = [k for b in S["beats"][a:z + 1] for k in b.cams]
    cur = [k for k in ks if k[0] <= t] or ks[:1]
    k1 = cur[-1]
    prev = cur[-2] if len(cur) > 1 else None
    if prev is None:
        return k1[1]
    f = ease((t - k1[0]) / .8)
    return tuple(lerp(u, v, f) for u, v in zip(prev[1], k1[1]))


def subtitles(c, t, y):
    subs = S["subs"]
    for n, ch in enumerate(subs):
        end = subs[n + 1][0]["s"] - .05 if n + 1 < len(subs) else ch[-1]["e"] + .4
        end = min(end, ch[-1]["e"] + .7)
        if ch[0]["s"] - .05 <= t < end:
            f = font("segoeuib.ttf", 66)
            words = [w["w"].upper() for w in ch]
            total = sum(f.measureText(s) for s in words) + f.measureText(" ") * (len(words) - 1)
            if total > 980:
                f = font("segoeuib.ttf", int(66 * 980 / total))
                total = 980
            k = back((t - ch[0]["s"] + .05) / .18)
            c.save()
            c.translate(540, y)
            c.scale(k, k)
            x = -total / 2
            for w, s in zip(ch, words):
                col = CHALK_Y if w["s"] <= t < w["e"] + .1 else 0xFFFFFFFF
                c.drawString(s, x, 0, f, stroke(14))
                c.drawString(s, x, 0, f, fill(col))
                x += f.measureText(s + " ")
            c.restore()


def beat_at(t):
    beats = S["beats"]
    for b in reversed(beats):
        if t >= b.t0 - .12:
            return b
    return beats[0]


# ---------- patterned base background (replaces the map in "mapa" scenes when a fondo is set) ----------
FONDO_COLORES = {"marino": 0xFF1C2E4A, "verde": 0xFF1E3B2C, "morado": 0xFF2E2346, "vino": 0xFF3E1E2A, "petroleo": 0xFF163A40}
FONDO_PATRONES = ("rombos", "hex", "puntos", "diagonal")


def fondo_cfg():
    """('patron', color) from env LOL_FONDO="patron:color" or guion.json "fondo": {"patron", "color"}; None = map."""
    env = __import__("os").environ.get("LOL_FONDO")
    if env:
        pat, col = (env.split(":") + ["marino"])[:2]
    else:
        f = S.get("guion", {}).get("fondo", {})   # default style since class 07: navy diamonds; "fondo": "mapa" = old map
        if f == "mapa":
            return None
        pat, col = f.get("patron", "rombos"), f.get("color", "marino")
    col = FONDO_COLORES.get(col, None) or int(col, 16) | 0xFF000000
    return pat, col


def _shade(col, f):
    r, g, b = (col >> 16) & 255, (col >> 8) & 255, col & 255
    if f >= 0:
        r, g, b = r + (255 - r) * f, g + (255 - g) * f, b + (255 - b) * f
    else:
        r, g, b = r * (1 + f), g * (1 + f), b * (1 + f)
    return 0xFF000000 | (int(r) << 16) | (int(g) << 8) | int(b)


def draw_fondo(c, t, view, pat, col):
    """World-space pattern (it slides with the camera, so moves still read as motion) + turrets of the lanes."""
    vo = view.makeOutset(300, 300)
    c.drawRect(vo, fill(col))
    line = stroke(5, _shade(col, .10))
    soft = fill(_shade(col, .06))
    step = 220
    x0, y0 = math.floor(vo.left() / step) * step, math.floor(vo.top() / step) * step
    if pat == "rombos":
        for gx in range(int(x0), int(vo.right()) + step, step):
            for gy in range(int(y0), int(vo.bottom()) + step, step):
                d = path([(gx, gy - step / 2 + 18), (gx + step / 2 - 18, gy), (gx, gy + step / 2 - 18), (gx - step / 2 + 18, gy)])
                c.drawPath(d, soft if (gx // step + gy // step) % 2 else line)
    elif pat == "hex":
        r = step / 1.9
        hx, hy = r * 1.732, r * 1.5
        for j, gy in enumerate(range(int(y0 // hy) - 1, int(vo.bottom() // hy) + 2)):
            for gx in range(int(vo.left() // hx) - 1, int(vo.right() // hx) + 2):
                cx_, cy_ = gx * hx + (hx / 2 if gy % 2 else 0), gy * hy
                c.drawPath(path([(cx_ + r * .9 * math.cos(math.radians(30 + 60 * a)), cy_ + r * .9 * math.sin(math.radians(30 + 60 * a))) for a in range(6)]), line)
    elif pat == "puntos":
        for gx in range(int(x0), int(vo.right()) + step, step // 2):
            for gy in range(int(y0), int(vo.bottom()) + step, step // 2):
                off = step // 4 if (gy // (step // 2)) % 2 else 0
                c.drawCircle(gx + off, gy, 14, soft)
    else:  # diagonal
        h = vo.height()
        for gx in range(int(x0 - h), int(vo.right()) + step, step):
            c.drawPath(path([(gx, vo.bottom()), (gx + 80, vo.bottom()), (gx + 80 + h, vo.top()), (gx + h, vo.top())]), soft)
    for j, (x, lane, side, rx, ry) in enumerate(G.BRUSHES):   # brushes and turrets are gameplay, keep them
        bx, by = G._brush_pos(x, lane, side)
        if vo.contains(bx, by):
            G.brush(c, bx, by, rx, ry, t, j)
    for x, y, team in G.TURRETS:
        if vo.contains(x, y):
            G.turret(c, x, y, team, t)


def vignette(c, col):
    p = skia.Paint(Shader=skia.GradientShader.MakeRadial((W / 2, H / 2), H * .75, [0x00000000, 0x00000000, (0x99 << 24) | (_shade(col, -.6) & 0xFFFFFF)], [0, .55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def frame(t):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    b = beat_at(t)
    lt = t - b.t0
    if b.kind == "aula":
        classroom(c)
        badge(c, f"CLASE #{S['clase']:02d}", 175, 150, 34, GOLD)
        b.fn(c, lt, b)
        if b.spec["teacher"]:
            draw_teacher(c, t, b)
        sub_y = b.spec["sub_y"] or 1170
    else:
        cx, cy, z = camera(t, b.idx)
        fc = fondo_cfg()
        if fc:
            z *= float(S["guion"].get("fondo", {}).get("zoom", 1.0))
        S["zoom"] = z
        view = skia.Rect.MakeXYWH(cx - FOCUS[0] / z, cy - FOCUS[1] / z, W / z, H / z)
        c.clear(0xFF141D17)
        c.save()
        c.translate(*FOCUS)
        c.scale(z, z)
        c.translate(-cx, -cy)
        if fc:
            draw_fondo(c, t, view, *fc)
        else:
            G.draw(c, t, view)
        b.fn(c, lt, b)
        c.restore()
        if fc:
            vignette(c, fc[1])
        elif b.spec.get("minimapa", True):
            G.minimap(c, 26, 1745, 300, view, t)
        if b.spec["teacher"]:
            draw_teacher(c, t, b)
        sub_y = b.spec["sub_y"] or 1450
    # transition between kinds: white flash
    beats = S["beats"]
    for nb in beats[1:]:
        if beats[nb.idx - 1].kind != nb.kind:
            fl = max(0, 1 - abs(t - (nb.t0 - .12)) / .12)
            if fl > 0:
                c.drawRect(skia.Rect.MakeWH(W, H), fill(alpha(0xFFFFFFFF, fl * .7)))
    subtitles(c, t, sub_y)
    return surf


# ---------- audio ----------
_sfx_index = {}


def sfx_files(slot):
    """List of wav files for a slot (real LoL variants if available) and its config."""
    cfg = json.loads((Path(__file__).with_name("sonidos.json")).read_text(encoding="utf-8"))[slot]
    real = LEAGUE / "assets" / "sfx" / f"{slot}.wav"
    if real.exists():
        return [real], cfg
    if "lol" in cfg:
        files = sorted((LEAGUE / "assets" / "sonidos_lol" / "wav").glob(cfg["lol"]))
        if files:
            return files, cfg
        print(f"  ! slot {slot}: no files for {cfg['lol']}")
    if not _sfx_index:
        lib = LEAGUE.parent / "sfx" / "library"
        cat = json.loads((LEAGUE.parent / "sfx" / "catalog.json").read_text(encoding="utf-8"))
        for it in cat:
            p = lib / it["path"]
            _sfx_index[p.name] = p
    p = _sfx_index.get(cfg["archivo"])
    if p is None or not p.exists():
        p = next((LEAGUE.parent / "sfx" / "library").rglob(cfg["archivo"]))
    return [p], cfg


def build_audio():
    sr = 48000
    nar = np.interp(np.arange(0, len(S["audio"]) / S["sr"], 1 / sr), np.arange(len(S["audio"])) / S["sr"], S["audio"])
    out = np.zeros(int(S["DUR"] * sr) + sr)
    out[:len(nar)] += nar
    cues = []
    beats = S["beats"]
    for b in beats:
        if b.idx and beats[b.idx - 1].kind != b.kind:
            cues.append(("whoosh", b.t0 - .3, 1.0))
        if b.spec["sfx"]:
            for item in b.spec["sfx"](b):
                slot, when = item[0], _resolve(b, item[1])
                cues.append((slot, b.t0 + when, item[2] if len(item) > 2 else 1.0))
    cache, turn = {}, {}
    for slot, at, vm in cues:
        if slot not in cache:
            files, cfg = sfx_files(slot)
            variants = []
            for p in files:
                x, xsr = sf.read(p, frames=int(48000 * 4 * 4), always_2d=True)
                x = x.mean(1)
                x = np.interp(np.arange(0, len(x) / xsr, 1 / sr), np.arange(len(x)) / xsr, x)
                x = x[:int(cfg["largo"] * sr)].copy()
                fade = min(len(x), int(.25 * sr))
                x[len(x) - fade:] *= np.linspace(1, 0, fade)
                variants.append(x / (np.abs(x).max() or 1) * cfg["vol"])
            cache[slot] = variants
        turn[slot] = turn.get(slot, -1) + 1
        variants = cache[slot]
        x0 = variants[turn[slot] % len(variants)]
        x = x0 * vm
        i = int(at * sr)
        if i < 0:
            x, i = x[-i:], 0
        out[i:i + len(x)] += x[:len(out) - i]
    out = out[:int(S["DUR"] * sr)]
    path_ = S["ep"] / "mezcla.wav"
    sf.write(path_, np.clip(out, -1, 1), sr)
    print(f"audio: {len(cues)} sound cues", flush=True)
    return path_


# ---------- render ----------
def _render_range(args):
    n0, n1, out = args
    build()
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", str(out)],
                          stdin=subprocess.PIPE)
    for n in range(n0, n1):
        ff.stdin.write(frame(n / FPS).makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
    ff.stdin.close()
    ff.wait()
    return out


def main():
    build()
    ep = S["ep"]
    slug = ep.name
    if "--stills" in sys.argv or "--hoja" in sys.argv:
        out = ep / "stills"
        out.mkdir(exist_ok=True)
        if "--hoja" in sys.argv:  # contact sheet: 2 frames per scene
            ts = []
            for b in S["beats"]:
                ts += [b.t0 + b.dur * .3, b.t0 + b.dur * .85]
        else:
            ts = [float(v) for v in sys.argv[sys.argv.index("--stills") + 1].split(",")]
        imgs = []
        for t in ts:
            img = frame(t).makeImageSnapshot()
            img.save(str(out / f"t{t:06.2f}.png"))
            imgs.append((t, img))
        if "--hoja" in sys.argv:
            cols, tw, th = 8, 270, 480
            rows = math.ceil(len(imgs) / cols)
            sheet = skia.Surface(cols * tw, rows * (th + 30))
            sc = sheet.getCanvas()
            sc.clear(0xFF202020)
            for j, (t, img) in enumerate(imgs):
                x, y = (j % cols) * tw, (j // cols) * (th + 30)
                sc.drawImageRect(img, skia.Rect.MakeXYWH(x, y, tw, th), skia.SamplingOptions(skia.FilterMode.kLinear))
                b = beat_at(t)
                sc.drawString(f"{t:.1f}s {b.id}", x + 6, y + th + 22, font("segoeuib.ttf", 20), fill(0xFFFFFFFF))
            sheet.makeImageSnapshot().save(str(ep / "hoja.png"))
            print("sheet", ep / "hoja.png")
        print("stills", out, f"duration {S['DUR']:.1f}s")
    if "--full" in sys.argv:
        mix_wav = build_audio()
        total = int(S["DUR"] * FPS)
        nproc = 4
        cuts = [round(total * j / nproc) for j in range(nproc + 1)]
        parts = [(cuts[j], cuts[j + 1], ep / f"_parte{j}.mp4") for j in range(nproc)]
        with mp.Pool(nproc) as pool:
            pool.map(_render_range, parts)
        lst = ep / "_partes.txt"
        lst.write_text("".join(f"file '{p[2].as_posix()}'\n" for p in parts), encoding="utf-8")
        out = ep / f"{slug}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(mix_wav),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                        "-c:a", "aac", "-b:a", "192k", "-t", f"{S['DUR']:.3f}", str(out)], check=True)
        for p in parts:
            p[2].unlink()
        lst.unlink()
        print("ok", out, f"{S['DUR']:.1f}s")
