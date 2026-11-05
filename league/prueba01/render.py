"""Profesor Jaime Enrique, test 01 (10 s): minion aggro. Vertical 1080x1920, everything drawn in code (skia).
Usage: render_env/Scripts/python.exe render.py [--stills 1.0,4.0] [--full]"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import skia
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "personaje"))
from profesora import LOOKS, POSES, profesora  # noqa: E402

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "campeones"
ICONS = {n: skia.Image.open(str(ASSETS / f"{n}.png")) for n in ("Caitlyn", "Draven")}
LOOK = LOOKS["C"]


def teacher(c, x, y, s, t, base, **kw):
    pose = dict(POSES[base])
    pose.update(kw)
    pose.setdefault("talk", amp(t))
    pose.setdefault("blink", blink_at(t))
    profesora(c, x, y, s, t, pose, LOOK)

HERE = Path(__file__).resolve().parent
W, H, FPS, DUR = 1080, 1920, 30, 10.0
FONTS = "C:/Windows/Fonts/"
INK = 0xFF1E2228

# ---------- timing ----------
SCRIPT = [l["text"] for l in json.loads((HERE / "lineas.json").read_text(encoding="utf-8"))]
ASR = json.loads((HERE / "palabras_asr.json").read_text(encoding="utf-8"))
WORDS = [dict(w=w, s=a["s"], e=a["e"]) for w, a in zip(" ".join(SCRIPT).split(), ASR)]
T = {w["w"].strip("¿?,.").lower(): w["s"] for w in WORDS}  # first occurrence of each word
T_AB, T_BC = T["porque"] - .14, WORDS[-1]["e"] + .35
T_GOLPE = T["golpeas"] + .1      # projectile leaves
T_HIT = T_GOLPE + .3
T_BASICO = T["ataque"]
T_CERCA = T["cercanos"]
T_GIRAN = T["giran"]
T_PEGAN = T_GIRAN + .55

audio, SR = sf.read(HERE / "narracion.wav")
audio = audio if audio.ndim == 1 else audio.mean(1)


def amp(t):
    i = int(t * SR)
    seg = audio[max(0, i - 600):i + 600]
    return 0.0 if len(seg) == 0 else min(1.0, float(np.sqrt(np.mean(seg ** 2))) * 9)


# ---------- helpers ----------
def font(file, size):
    return skia.Font(skia.Typeface.MakeFromFile(FONTS + file), size)


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def stroke(w, color=INK):
    return skia.Paint(AntiAlias=True, Color=color, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def alpha(color, a):
    return (int(max(0, min(1, a)) * ((color >> 24) & 255)) << 24) | (color & 0xFFFFFF)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def back(x, s=1.7):
    """Ease-out with overshoot (follow-through)."""
    x = max(0.0, min(1.0, x)) - 1
    return 1 + x * x * ((s + 1) * x + s)


def lerp(a, b, k):
    return a + (b - a) * k


def mix(p, q, k):
    return (lerp(p[0], q[0], k), lerp(p[1], q[1], k))


def path(points, close=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def blob(cx, cy, rx, ry, n, bump, phase=0.0):
    """Fluffy closed shape: n rounded lobes around an ellipse."""
    p = skia.Path()
    pts = [(cx + rx * math.cos(2 * math.pi * j / n + phase), cy + ry * math.sin(2 * math.pi * j / n + phase)) for j in range(n)]
    p.moveTo(*pts[0])
    for j in range(n):
        a, b = pts[j], pts[(j + 1) % n]
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        out = (m[0] - cx, m[1] - cy)
        d = math.hypot(*out) or 1
        p.quadTo(m[0] + out[0] / d * bump, m[1] + out[1] / d * bump, *b)
    p.close()
    return p


def shape(c, p, color, w=6):
    c.drawPath(p, fill(color))
    c.drawPath(p, stroke(w))


def text(c, s, x, y, f, color, outline=0, align="c", outline_color=INK):
    w = f.measureText(s)
    x0 = x - w / 2 if align == "c" else x
    if outline:
        c.drawString(s, x0, y, f, stroke(outline, outline_color))
    c.drawString(s, x0, y, f, fill(color))
    return w


def ik(sh, target, l1, l2, bend):
    """Two-bone IK: returns the elbow and the reachable hand position."""
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    d = max(1e-3, min(l1 + l2 - 1, math.hypot(dx, dy)))
    a = math.atan2(dy, dx)
    cos_b = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1, min(1, cos_b))) * bend
    elbow = (sh[0] + l1 * math.cos(a + b), sh[1] + l1 * math.sin(a + b))
    return elbow, (sh[0] + d * math.cos(a), sh[1] + d * math.sin(a))


# ---------- the professor ----------
HAIR, HAIR_D = 0xFFF0C64E, 0xFFC9962E
SKIN, EAR_IN = 0xFFE9B595, 0xFFD88E78
WHITE, WHITE_D = 0xFFF6F3EC, 0xFFD6D0C4
GOG, LENS = 0xFFDB4A2C, 0xFF7CC4F0
COAT, COAT_D, SLEEVE, GLOVE = 0xFF3C6E8E, 0xFF2D5670, 0xFF6AA6C6, 0xFF4E5E6A


def spiky(cx, cy, rx, ry, n, spike, t, phase=0.0):
    """Flame-like spiky hair mass: curved spikes around an ellipse, swaying a little."""
    p = skia.Path()
    a0 = math.pi * .92 + phase * .1
    span = math.pi * 1.16
    base = lambda a, r: (cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r)  # noqa: E731
    p.moveTo(*base(a0, .9))
    for j in range(n):
        a1 = a0 + span * (j + .5) / n
        a2 = a0 + span * (j + 1) / n
        up = 1 + (spike / rx) * (1.15 if j % 3 == 1 else .85) + math.sin(t * 2 + j) * .015
        tip = (cx + math.cos(a1 + .12) * (rx * up), cy + math.sin(a1 + .12) * (ry * up) - spike * .25)
        ctrl = base(a1 - .05, 1.12)
        p.quadTo(*ctrl, *tip)
        p.quadTo(*base(a2 - .02, 1.05), *base(a2, .92))
    p.quadTo(cx, cy + ry * 1.0, *base(a0, .9))
    p.close()
    return p


def arm(c, sh, hand, bend, point=False, pointer=False):
    l1, l2 = 82, 78
    el, hd = ik(sh, hand, l1, l2, bend)
    for w, col in ((40, INK), (30, SLEEVE)):
        c.drawPath(path([sh, el, hd], close=False), stroke(w, col))
    ang = math.atan2(hd[1] - el[1], hd[0] - el[0])
    if pointer:  # wooden pointer stick held in the hand
        tip = (hd[0] + math.cos(ang) * 230, hd[1] + math.sin(ang) * 230)
        c.drawLine(*hd, *tip, stroke(14, INK))
        c.drawLine(*hd, *tip, stroke(8, 0xFFB98247))
        c.drawCircle(*tip, 9, fill(0xFFF3EFE2))
        c.drawCircle(*tip, 9, stroke(4))
    if point:  # index finger
        tip = (hd[0] + math.cos(ang) * 46, hd[1] + math.sin(ang) * 46)
        c.drawLine(*hd, *tip, stroke(24, INK))
        c.drawLine(*hd, *tip, stroke(14, GLOVE))
    c.drawCircle(*hd, 25, fill(GLOVE))
    c.drawCircle(*hd, 25, stroke(6))
    return hd


def professor(c, x, y, s, t, pose):
    """pose: hand_l / hand_r targets (local coords), finger flags, tilt (deg), talk (0..1), lean, wink."""
    c.save()
    breath = math.sin(t * 2.2) * .012
    c.translate(x, y)
    c.scale(s, s)
    c.rotate(pose.get("lean", 0))
    # legs and boots
    for sx in (-1, 1):
        c.drawRoundRect(skia.Rect.MakeXYWH(sx * 42 - 20, -95, 40, 85), 12, 12, fill(0xFF2A2F3A))
        c.drawRoundRect(skia.Rect.MakeXYWH(sx * 42 - 20, -95, 40, 85), 12, 12, stroke(6))
        shape(c, skia.Path.Oval(skia.Rect.MakeXYWH(sx * 46 - 34, -26, 68, 30)), 0xFF2A2F3A)
    c.save()
    c.scale(1, 1 + breath)
    # coat
    coat = skia.Path()
    coat.moveTo(-82, -300)
    coat.quadTo(0, -318, 82, -300)
    coat.lineTo(118, -88)
    coat.quadTo(0, -64, -118, -88)
    coat.close()
    shape(c, coat, COAT)
    c.drawLine(0, -300, 0, -80, stroke(5, COAT_D))
    c.drawPath(path([(-112, -96), (0, -78), (112, -96)], close=False), stroke(8, 0xFFE4C064))
    c.drawRect(skia.Rect.MakeXYWH(-104, -175, 208, 30), fill(0xFF7A4E30))
    c.drawRect(skia.Rect.MakeXYWH(-104, -175, 208, 30), stroke(5))
    c.drawRoundRect(skia.Rect.MakeXYWH(-30, -182, 60, 44), 6, 6, fill(0xFFF0CC5A))
    c.drawRoundRect(skia.Rect.MakeXYWH(-30, -182, 60, 44), 6, 6, stroke(5))
    c.restore()
    sh_l, sh_r = (-80, -282), (80, -282)
    hand_l, hand_r = pose.get("hand_l", (-120, -120)), pose.get("hand_r", (120, -120))
    if not pose.get("front_l"):
        arm(c, sh_l, hand_l, 1, pose.get("point_l"), pose.get("pointer_l"))
    if not pose.get("front_r"):
        arm(c, sh_r, hand_r, -1, pose.get("point_r"), pose.get("pointer_r"))
    # head (pivot at the neck)
    talk = pose.get("talk", 0)
    c.save()
    c.translate(0, -300)
    c.rotate(pose.get("tilt", 0) + math.sin(t * 1.7) * 2)
    c.translate(0, -talk * 4)
    hy = -170
    for sx in (-1, 1):  # yordle ears
        ear = path([(sx * 92, hy - 20), (sx * 205, hy - 78), (sx * 120, hy + 40)])
        shape(c, ear, SKIN)
        c.drawPath(path([(sx * 108, hy - 10), (sx * 178, hy - 58), (sx * 120, hy + 22)]), fill(EAR_IN))
    shape(c, spiky(0, hy - 90, 150, 112, 13, 75, t), HAIR, 7)
    c.drawPath(spiky(0, hy - 80, 105, 80, 9, 40, t, .4), fill(HAIR_D))
    shape(c, skia.Path.Oval(skia.Rect.MakeXYWH(-100, hy - 95, 200, 190)), SKIN)
    # beard and sideburns (white cloud around the lower face)
    beard = blob(0, hy + 55, 125, 72, 9, 22, .2)
    shape(c, beard, WHITE)
    c.drawPath(blob(0, hy + 70, 80, 40, 7, 12), fill(WHITE_D))
    # mouth under the mustache
    mo = 4 + 26 * talk
    c.drawOval(skia.Rect.MakeXYWH(-17, hy + 52, 34, mo), fill(0xFF5A2A2A))
    # goggles
    blink = pose.get("blink", 0)
    for sx in (-1, 1):
        r = skia.Rect.MakeXYWH(sx * 56 - 46, hy - 32, 92, 64)
        c.drawRoundRect(r, 18, 18, fill(GOG))
        c.drawRoundRect(r, 18, 18, stroke(7))
        lens = skia.Rect.MakeXYWH(sx * 56 - 33, hy - 20, 66, 40)
        c.drawRoundRect(lens, 12, 12, fill(LENS))
        lid = max(blink, .38 if not (pose.get("wink") and sx == 1) else 1.0)  # sleepy half lids, like the reference
        c.drawRoundRect(skia.Rect.MakeXYWH(sx * 56 - 33, hy - 20, 66, 40 * lid), 12, 12, fill(0xFF4E8FBF))
        c.drawLine(sx * 56 - 30, hy - 20 + 40 * lid, sx * 56 + 30, hy - 20 + 40 * lid, stroke(5))
        c.drawLine(sx * 56 + 10, hy - 14, sx * 56 + 24, hy - 14, stroke(5, 0xCCFFFFFF))
    c.drawLine(-10, hy - 4, 10, hy - 4, stroke(10, GOG))
    c.drawOval(skia.Rect.MakeXYWH(-12, hy + 12, 24, 16), fill(0xFFC9806A))  # nose
    # big mustache
    for sx in (-1, 1):
        m = skia.Path()
        m.moveTo(0, hy + 30)
        m.cubicTo(sx * 40, hy + 18, sx * 90, hy + 28, sx * 112, hy + 66)
        m.cubicTo(sx * 80, hy + 58, sx * 40, hy + 62, 0, hy + 46)
        m.close()
        shape(c, m, WHITE, 6)
    # front hair spikes over the forehead
    zig = [(-122, hy - 62), (-95, hy - 18), (-70, hy - 70), (-40, hy - 32), (-10, hy - 86), (25, hy - 36), (55, hy - 80), (85, hy - 28),
           (126, hy - 64)]
    c.drawPath(path(zig + [(112, hy - 140), (-112, hy - 140)]), fill(HAIR))
    c.drawPath(path(zig, close=False), stroke(6))
    for q in ((-55, hy - 120), (40, hy - 128)):
        c.drawPath(path([(q[0] - 22, q[1] + 26), q, (q[0] + 20, q[1] + 30)], close=False), stroke(6, HAIR_D))
    # magnifier clipped in the hair
    c.drawLine(118, hy - 70, 132, hy - 128, stroke(12, INK))
    c.drawLine(118, hy - 70, 132, hy - 128, stroke(6, 0xFFB0B8C0))
    c.drawCircle(140, hy - 150, 30, fill(GOG))
    c.drawCircle(140, hy - 150, 30, stroke(6))
    c.drawCircle(140, hy - 150, 18, fill(LENS))
    c.restore()
    if pose.get("front_l"):
        arm(c, sh_l, hand_l, 1, pose.get("point_l"), pose.get("pointer_l"))
    if pose.get("front_r"):
        arm(c, sh_r, hand_r, -1, pose.get("point_r"), pose.get("pointer_r"))
    c.restore()


def blink_at(t):
    for b in (1.3, 4.2, 6.9, 9.1):
        if b <= t < b + .14:
            return 1.0
    return 0.0


# ---------- scenes ----------
CHALK, CHALK_Y = 0xFFF2F0E6, 0xFFF2D35A


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
    for j, (x, y, r) in enumerate(((240, 420, 120), (820, 900, 160), (600, 600, 90))):
        c.drawCircle(x, y, r, fill(0x10FFFFFF))
    c.drawRoundRect(skia.Rect.MakeXYWH(200, 1076, 680, 22), 8, 8, fill(0xFF8A5A34))
    c.drawRoundRect(skia.Rect.MakeXYWH(200, 1076, 680, 22), 8, 8, stroke(5))
    c.drawRoundRect(skia.Rect.MakeXYWH(300, 1066, 60, 14), 6, 6, fill(CHALK))


def chalk_line(c, s, x, y, size, k, color=CHALK):
    """Chalk text written left to right; k in 0..1."""
    if k <= 0:
        return
    f = font("segoeprb.ttf", size)
    w = f.measureText(s)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(x - w / 2 - 10, y - size * 1.3, x - w / 2 + w * min(1, k) + 10, y + size * .5))
    c.drawString(s, x - w / 2, y, f, fill(color))
    c.restore()


def badge(c, s, x, y, size, bg, fg=INK, k=1.0):
    if k <= 0:
        return
    f = font("segoeuib.ttf", size)
    w = f.measureText(s)
    c.save()
    c.translate(x, y)
    sc = back(k)
    c.scale(sc, sc)
    r = skia.Rect.MakeXYWH(-w / 2 - 22, -size * .95, w + 44, size * 1.35)
    c.drawRoundRect(r, size * .6, size * .6, fill(bg))
    c.drawRoundRect(r, size * .6, size * .6, stroke(5))
    c.drawString(s, -w / 2, 0, f, fill(fg))
    c.restore()


def minion(c, x, y, face, s=1.0, flash=0.0):
    """Small red minion seen from above-front; face = direction (-1 left .. 1 right)."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = 0xFFE5484D if flash <= 0 else 0xFFFF9090
    c.drawOval(skia.Rect.MakeXYWH(-34, 30, 68, 16), fill(0x55000000))
    shape(c, skia.Path.Oval(skia.Rect.MakeXYWH(-32, -30, 64, 66)), body, 6)
    helmet = path([(-30, -8), (0, -58), (30, -8)])
    shape(c, helmet, 0xFF8E2A33, 6)
    for sx in (-1, 1):
        ex = face * 12 + sx * 11
        c.drawCircle(ex, 4, 7, fill(0xFFFFF4C8))
        c.drawCircle(ex + face * 2, 5, 3.5, fill(INK))
    c.restore()


def champ(c, x, y, label, color, k=1.0, flash=0.0, hp=1.0, icon=None, name=""):
    c.save()
    c.translate(x, y)
    sc = back(k)
    c.scale(sc, sc)
    c.drawCircle(0, 0, 68, fill(0xFF13284A))
    if icon is not None:
        c.save()
        c.clipPath(skia.Path.Circle(0, 0, 64), doAntiAlias=True)
        c.drawImageRect(ICONS[icon], skia.Rect.MakeXYWH(-70, -70, 140, 140), skia.SamplingOptions(skia.FilterMode.kLinear))
        c.restore()
    c.drawCircle(0, 0, 68, stroke(10, color))
    c.drawCircle(0, 0, 68 + 8, stroke(4, 0xFFE8C26A))
    if flash > 0:
        c.drawCircle(0, 0, 66, fill(alpha(0xFFFFFFFF, flash * .8)))
    if icon is None:
        text(c, label, 0, 14, font("segoeuib.ttf", 40), 0xFFFFFFFF)
    else:
        badge(c, label, 0, 112, 30, color, 0xFFFFFFFF)
        text(c, name.upper(), 0, 156, font("segoeuib.ttf", 26), 0xFFE8C26A, 8)
    c.drawRoundRect(skia.Rect.MakeXYWH(-60, -104, 120, 14), 7, 7, fill(0xFF0A1424))
    c.drawRoundRect(skia.Rect.MakeXYWH(-60, -104, 120 * hp, 14), 7, 7, fill(0xFF4CD07A if color != 0xFFE84855 else 0xFFE84855))
    c.drawRoundRect(skia.Rect.MakeXYWH(-60, -104, 120, 14), 7, 7, stroke(3, 0xFFE8C26A))
    c.restore()


def card_bg(c, t):
    g = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [0xFF0B1E3D, 0xFF071226])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=g))
    for j in range(-4, 14):
        x0 = j * 150 + (t * 20) % 150
        c.drawLine(x0, 0, x0 + 700, H, stroke(2, 0x14FFFFFF))
    for x, y, r, col in ((180, 1500, 120, 0x223FA9F5), (900, 300, 160, 0x22E8C26A), (850, 1700, 100, 0x224CD07A)):
        p = skia.Paint(AntiAlias=True, Color=col, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 60))
        c.drawCircle(x, y, r, p)


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "escenarios"))
from mapa import mapa  # noqa: E402

YOU, RIVAL = (380, 1200), (700, 805)
MINIONS = [(545, 965), (605, 1015), (500, 1015)]       # red, near the rival
ALLIES = [(445, 1120), (488, 1172), (400, 1080)]     # blue, near you


def ally_minion(c, x, y, t, j):
    c.save()
    c.translate(x, y + math.sin(t * 8 + j) * 3)
    c.scale(1.05, 1.05)
    c.drawOval(skia.Rect.MakeXYWH(-34, 30, 68, 16), fill(0x55000000))
    c.drawPath(skia.Path.Oval(skia.Rect.MakeXYWH(-32, -30, 64, 66)), fill(0xFF4A8FE0))
    c.drawPath(skia.Path.Oval(skia.Rect.MakeXYWH(-32, -30, 64, 66)), stroke(6))
    helm = path([(-30, -8), (0, -58), (30, -8)])
    c.drawPath(helm, fill(0xFF27508A))
    c.drawPath(helm, stroke(6))
    for sx in (-1, 1):
        c.drawCircle(12 + sx * 11, 4, 7, fill(0xFFFFF4C8))
        c.drawCircle(14 + sx * 11, 5, 3.5, fill(INK))
    c.restore()


def sign(c, t, k):
    """Wooden sign with chalk lettering, swinging slightly as it drops in."""
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
    f = font("segoeprb.ttf", 66)
    text(c, "EL AGRO", 0, 110, f, CHALK)
    text(c, "DE SÚBDITOS", 0, 190, f, CHALK_Y)
    c.restore()


def caption(c, s_, y, color, k):
    if k <= 0:
        return
    f = font("segoeuib.ttf", 56)
    w = f.measureText(s_)
    c.save()
    c.translate(540, y)
    sc = back(k)
    c.scale(sc, sc)
    r = skia.Rect.MakeXYWH(-w / 2 - 28, -56, w + 56, 76)
    c.drawRoundRect(r, 38, 38, fill(0xCC14181C))
    c.drawRoundRect(r, 38, 38, stroke(4, color))
    c.drawString(s_, -w / 2, 0, f, fill(color))
    c.restore()


def scene_lane(c, t):
    lt = t - T_AB
    zoom = lerp(1.12, 1.0, ease(lt / .6))  # camera settles onto the lane
    c.save()
    c.translate(540, 960)
    c.scale(zoom, zoom)
    c.translate(-540, -960)
    mapa(c, W, H, t, "inferior")
    kr = ease((t - T_CERCA) / .4)
    if kr > 0:  # "nearby": the rival's call-for-help area
        p = stroke(6, alpha(0xFFE84855, kr))
        p.setPathEffect(skia.DashPathEffect.Make([22, 14], t * 40))
        c.drawCircle(*RIVAL, 300 * back(kr), fill(alpha(0x33E84855, kr)))
        c.drawCircle(*RIVAL, 300 * back(kr), p)
        badge(c, "CERCANOS", RIVAL[0] + 150, RIVAL[1] - 250, 32, 0xFFE84855, 0xFFFFFFFF, kr)
    for j, (x, y) in enumerate(ALLIES):
        ally_minion(c, x, y, t, j)
    kt = ease((t - T_GIRAN) / .25)
    km = ease((t - T_GIRAN - .25) / .55)
    for j, (mx, my) in enumerate(MINIONS):
        tx, ty = YOU[0] + 120 + j * 30, YOU[1] - 40 + (j - 1) * 60
        x, y = lerp(mx, tx, km * .75), lerp(my, ty, km * .75)
        face = lerp(-.8, -1, kt)
        hop = -abs(math.sin((t - T_GIRAN) * 14 + j)) * 14 if 0 < km < 1 else 0
        minion(c, x, y + math.sin(t * 8 + j) * 3 + hop, face, 1.05)
        if kt > 0:
            badge(c, "!", x, y - 70, 40, 0xFFE84855, 0xFFFFFFFF, kt)
    if T_GOLPE <= t < T_HIT:  # Caitlyn's basic attack
        k = (t - T_GOLPE) / (T_HIT - T_GOLPE)
        p_ = mix(YOU, RIVAL, k)
        q = mix(YOU, RIVAL, max(0, k - .18))
        c.drawLine(*q, *p_, stroke(16, 0x883FA9F5))
        c.drawCircle(*p_, 16, fill(0xFFBFE8FF))
        c.drawCircle(*p_, 16, stroke(4, 0xFF3FA9F5))
    hit = math.exp(-(t - T_HIT) * 6) if t >= T_HIT else 0
    pegan = math.exp(-(t - T_PEGAN) * 7) if t >= T_PEGAN else 0
    champ(c, *YOU, "TÚ", 0xFF3FA9F5, ease((lt - .1) / .4), pegan, 1 - .35 * ease((t - T_PEGAN) / .6), "Caitlyn", "Caitlyn")
    sx = math.sin(t * 60) * 8 * hit
    champ(c, RIVAL[0] + sx, RIVAL[1], "RIVAL", 0xFFE84855, ease((lt - .2) / .4), hit, 1 - .12 * ease((t - T_HIT) / .3),
          "Draven", "Draven")
    if hit > 0:
        for j in range(8):
            a = j * math.pi / 4
            r0, r1 = 80 + (1 - hit) * 40, 110 + (1 - hit) * 60
            c.drawLine(RIVAL[0] + math.cos(a) * r0, RIVAL[1] + math.sin(a) * r0, RIVAL[0] + math.cos(a) * r1,
                       RIVAL[1] + math.sin(a) * r1, stroke(8, alpha(0xFFFFE27A, hit)))
    badge(c, "ATAQUE BÁSICO", 330, 930, 38, 0xFF3FA9F5, 0xFFFFFFFF, ease((t - T_BASICO) / .3))
    c.restore()
    sign(c, t, (lt - .05) / .5)
    badge(c, "LÍNEA INFERIOR", 540, 345, 30, 0xFFF3E7C8, INK, ease((lt - .4) / .3))
    caption(c, "GOLPEAS AL RIVAL…", 1300, 0xFFFFFFFF, (t - T_HIT) / .3 if t < T_GIRAN else 0)
    caption(c, "…Y SUS SÚBDITOS VAN POR TI", 1300, 0xFFFF6B74, (t - T_GIRAN) / .3) if t >= T_GIRAN else None
    k_up = back((lt - .15) / .45)
    hand = mix((46, -112), (112, -236), k_up)
    expr = "asombro" if t >= T_GIRAN else "explica"
    teacher(c, 900, 1895 + (1 - ease(lt / .3)) * 450, 1.25, t, "puntero", expr=expr, dir=-1, hand_r=hand, bend_r=1, tilt=-4)


def scene_hook(c, t):
    classroom(c)
    chalk_line(c, "¿POR QUÉ", 540, 470, 92, (t - .1) / .45)
    chalk_line(c, "TE PEGAN LOS", 540, 600, 92, (t - .55) / .6)
    chalk_line(c, "SÚBDITOS?", 540, 740, 110, (t - 1.15) / .5, CHALK_Y)
    # chalk doodle: minion arrow
    k = ease((t - 1.6) / .5)
    if k > 0:
        p = stroke(8, alpha(CHALK, .85))
        c.drawPath(path([(330, 860), (330 + 420 * k, 860)], close=False), p)
        if k >= 1:
            c.drawPath(path([(720, 830), (755, 860), (720, 890)], close=False), p)
        c.drawCircle(270, 860, 40, p)
        c.drawPath(path([(242, 840), (270, 792), (298, 840)], close=False), p)
        c.drawCircle(830, 860, 46, stroke(8, alpha(CHALK_Y, k)))
        chalk_line(c, "TÚ", 830, 878, 46, 1, alpha(CHALK_Y, k))
    badge(c, "PROF. JAIME ENRIQUE", 260, 150, 34, 0xFFE8C26A)
    # thinking pose: hand on the chin, then a raised finger on "rival"
    enter = back(t / .4)
    teacher(c, 540, 1880 + (1 - enter) * 600, 2.0, t, "piensa")


def scene_end(c, t):
    classroom(c)
    lt = t - T_BC
    chalk_line(c, "GOLPEAS AL RIVAL", 540, 450, 80, lt / .4)
    k = ease((lt - .35) / .3)
    if k > 0:
        c.drawPath(path([(540, 500), (540, 500 + 90 * k)], close=False), stroke(9, CHALK))
        if k >= 1:
            c.drawPath(path([(510, 560), (540, 595), (570, 560)], close=False), stroke(9, CHALK))
    chalk_line(c, "SUS SÚBDITOS", 540, 700, 92, (lt - .6) / .35, CHALK_Y)
    chalk_line(c, "TE ATACAN", 540, 820, 92, (lt - .9) / .35, CHALK_Y)
    badge(c, "¿LO SABÍAS?", 540, 990, 70, 0xFFE8C26A, INK, (lt - 1.35) / .35)
    badge(c, "PROF. JAIME ENRIQUE", 260, 150, 34, 0xFFE8C26A)
    up = back((lt - .1) / .4)
    bounce = abs(math.sin(lt * 3)) * 10 * math.exp(-lt)
    expr = "guino" if lt > 1.35 else "explica"
    teacher(c, 540, 1880 - bounce, 2.0, t, "guino", expr=expr, hand_r=mix((46, -112), (96, -262), up), tilt=lerp(0, -6, up))


SUB_CHUNKS = []
_cur = []
for w in WORDS:
    _cur.append(w)
    if len(_cur) == 3 or w["w"][-1] in ",.?":
        SUB_CHUNKS.append(_cur)
        _cur = []
if _cur:
    SUB_CHUNKS.append(_cur)


def subtitles(c, t, y):
    for ch in SUB_CHUNKS:
        nxt = SUB_CHUNKS.index(ch) + 1
        end = SUB_CHUNKS[nxt][0]["s"] - .05 if nxt < len(SUB_CHUNKS) else ch[-1]["e"] + .4
        if ch[0]["s"] - .05 <= t < end:
            f = font("segoeuib.ttf", 66)
            words = [w["w"].upper() for w in ch]
            total = sum(f.measureText(s) for s in words) + f.measureText(" ") * (len(words) - 1)
            k = back((t - ch[0]["s"] + .05) / .18)
            c.save(); c.translate(540, y); c.scale(k, k)
            x = -total / 2
            for w, s in zip(ch, words):
                col = 0xFFF2D35A if w["s"] <= t < w["e"] + .1 else 0xFFFFFFFF
                c.drawString(s, x, 0, f, stroke(14))
                c.drawString(s, x, 0, f, fill(col))
                x += f.measureText(s + " ")
            c.restore()


def frame(t):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    if t < T_AB:
        scene_hook(c, t)
        sub_y = 1010
        z = ease((t - (T_AB - .25)) / .25)  # push into the board before the cut
        if z > 0:
            img = surf.makeImageSnapshot()
            c.clear(0xFF000000)
            c.save(); c.translate(540, 640); c.scale(1 + z * .5, 1 + z * .5); c.translate(-540, -640)
            c.drawImage(img, 0, 0)
            c.restore()
    elif t < T_BC:
        scene_lane(c, t)
        sub_y = 1420
    else:
        scene_end(c, t)
        sub_y = 1165
    flash = max(0, 1 - abs(t - T_AB) / .12) + max(0, 1 - abs(t - T_BC) / .12)
    if flash > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill(alpha(0xFFFFFFFF, flash * .7)))
    subtitles(c, t, sub_y)
    return surf


SFX = Path("C:/videos-youtube/sfx")


def build_audio():
    find = lambda k: str(next(SFX.rglob(f"{k}.wav")))  # noqa: E731
    cues = [("068_Cable_Whoosh", T_AB - .25, .35), ("068_Cable_Whoosh", T_BC - .2, .3),
            ("Bluezone-BC0226-hit-impact-004", T_HIT, .22), ("Notification_Bridge Operation 01", T_BASICO, .25),
            ("Notification_Bridge Operation 01", T_GIRAN, .3), ("Bluezone-BC0226-hit-impact-004", T_PEGAN, .12),
            ("Notification_Bridge Operation 01", T_BC + 1.35, .3)]
    args, filt = ["-i", str(HERE / "narracion.wav")], []
    for j, (k, at, vol) in enumerate(cues):
        args += ["-i", find(k)]
        filt.append(f"[{j + 1}:a]atrim=0:1.6,afade=t=out:st=1.2:d=0.4,volume={vol},adelay={int(at * 1000)}:all=1[s{j}]")
    mixin = "".join(f"[s{j}]" for j in range(len(cues)))
    filt.append(f"[0:a]{mixin}amix=inputs={len(cues) + 1}:normalize=0:duration=longest,apad=pad_dur=12,atrim=0:{DUR}[a]")
    out = HERE / "mezcla.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", *args, "-filter_complex", ";".join(filt), "-map", "[a]", "-ar", "48000", str(out)], check=True)
    return out


if __name__ == "__main__":
    if "--stills" in sys.argv:
        out = HERE / "stills"
        out.mkdir(exist_ok=True)
        for v in sys.argv[sys.argv.index("--stills") + 1].split(","):
            frame(float(v)).makeImageSnapshot().save(str(out / f"t{float(v):05.2f}.png"))
        print("stills", out)
    if "--full" in sys.argv:
        mix_wav = build_audio()
        out = HERE / "prueba01_profesor.mp4"
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-i", str(mix_wav), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
                               "-c:a", "aac", "-b:a", "192k", "-t", str(DUR), str(out)], stdin=subprocess.PIPE)
        for n in range(int(DUR * FPS)):
            img = frame(n / FPS).makeImageSnapshot()
            ff.stdin.write(img.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        ff.stdin.close()
        ff.wait()
        print("ok", out)
