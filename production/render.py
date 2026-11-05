"""2D animation renderer: layered vector character over AI backgrounds, camera moves, effects, subtitles.
Usage: render.py --stills 3,10,20 | render.py --full"""
import json
import math
import random
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import skia

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 30
BG_W, BG_H = 1536, 864
BASE = W / BG_W
TL = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
BGS = {p.stem: skia.Image.open(str(p)) for p in (ROOT / "assets" / "bg").glob("*.png")}
SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
INK = 0xFF0B0B0D
SKIN, SHADE = 0xFFF5F3EC, 0xFFD5D6D4
HAIR, JACKET, JACKET_DARK, SHIRT = 0xFF4A2C20, 0xFF9A5A3C, 0xFF7A4530, 0xFFD8D4C6
SUB_FONT = skia.Font(skia.Typeface.MakeFromFile("C:/Windows/Fonts/comicbd.ttf"), 38)
BOARD_FONT = skia.Font(skia.Typeface.MakeFromFile("C:/Windows/Fonts/comicbd.ttf"), 33)
CAPTION_FONT = skia.Font(skia.Typeface.MakeFromFile("C:/Windows/Fonts/comicbd.ttf"), 64)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def stroke(width, color=INK):
    return skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=color,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def poly(points, close=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def limb(c, a, b, width=9):
    c.drawLine(*a, *b, stroke(width))


def arm(c, shoulder, angle, bend, side, holding=False):
    """Two-segment arm; angle is measured from straight down, positive toward the character's front."""
    upper, lower = 48, 46
    ex = shoulder[0] + math.sin(angle) * upper * side
    ey = shoulder[1] + math.cos(angle) * upper
    fa = angle + bend
    hx = ex + math.sin(fa) * lower * side
    hy = ey + math.cos(fa) * lower
    limb(c, shoulder, (ex, ey))
    limb(c, (ex, ey), (hx, hy))
    c.drawCircle(hx, hy, 8, fill(INK))
    if holding:
        c.save()
        c.translate(hx, hy)
        c.rotate(90 - math.degrees(fa) if side > 0 else math.degrees(fa) - 90)
        c.drawRoundRect(skia.Rect.MakeXYWH(-6, -7, 34, 14), 4, 4, fill(0xFF3A3F44))
        c.drawRoundRect(skia.Rect.MakeXYWH(-6, -7, 34, 14), 4, 4, stroke(3))
        c.drawRect(skia.Rect.MakeXYWH(28, -10, 8, 20), fill(0xFFF3E7A8))
        c.drawRect(skia.Rect.MakeXYWH(28, -10, 8, 20), stroke(3))
        c.restore()
    return hx, hy


def head(c, cx, cy, s):
    """Layered head: s holds look, blink, mouth, brows, tilt and facing (-1..1 profile bias)."""
    r = 66
    c.save()
    c.translate(cx, cy)
    c.rotate(s.get("tilt", 0))
    face = s.get("face", 0)
    c.drawCircle(0, 0, r, fill(SKIN))
    clip = skia.Path()
    clip.addCircle(0, 0, r)
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    c.drawCircle(-face * 18 - 16, -8, r + 3, fill(SHADE))
    c.drawCircle(-face * 18 - 8, -6, r - 4, fill(SKIN))
    c.restore()
    # hair: jagged fringe, drawn over the skull
    spikes = [(-r - 2, -14)]
    for i in range(7):
        x = lerp(-r + 6, r - 6, i / 6) + face * 6
        spikes += [(x - 8, -36 - (i % 2) * 7), (x + 4, -20 + (i % 3) * 3)]
    spikes += [(r + 2, -14), (r - 8, -46), (40, -70), (6, -78), (-34, -72), (-r + 6, -48)]
    c.drawPath(poly(spikes), fill(HAIR))
    c.drawPath(poly(spikes), stroke(6))
    if s.get("helmet"):
        c.drawArc(skia.Rect.MakeXYWH(-r - 8, -r - 22, 2 * r + 16, 2 * r + 10), 180, 180, True, fill(0xFFC9A23A))
        c.drawArc(skia.Rect.MakeXYWH(-r - 8, -r - 22, 2 * r + 16, 2 * r + 10), 180, 180, True, stroke(6))
        c.drawLine(-r - 18, -28, r + 18, -28, stroke(10))
    if s.get("back"):  # seen from behind: only hair
        c.drawCircle(0, -6, r + 1, fill(HAIR))
        c.drawCircle(0, -6, r + 1, stroke(6))
        c.restore()
        return
    # face
    fx = face * 22
    lx, ly = s.get("look", (0, 0))
    wide = s.get("eye", 1.0)
    blink = s.get("blink", 0.0)
    for ex in (-22 + fx - abs(face) * 2, 22 + fx + abs(face) * 2):
        eye = skia.Rect.MakeXYWH(ex + lx * 7 - 6.5 * wide, 2 + ly * 5 - 8 * wide * (1 - blink), 13 * wide, max(2.5, 16 * wide * (1 - blink)))
        c.drawOval(eye, fill(INK))
    brow = s.get("brow", 0)  # negative worried, positive angry
    c.drawLine(-34 + fx, -14 - brow * 6, -14 + fx, -14 + brow * 6, stroke(4.5))
    c.drawLine(14 + fx, -14 + brow * 6, 34 + fx, -14 - brow * 6, stroke(4.5))
    mouth = s.get("mouth", "flat")
    mx, my = fx + lx * 3, 34
    if mouth == "flat":
        c.drawLine(mx - 13, my, mx + 13, my, stroke(4.5))
    elif mouth == "worry":
        p = skia.Path()
        p.moveTo(mx - 15, my + 5)
        p.quadTo(mx, my - 7, mx + 15, my + 5)
        c.drawPath(p, stroke(4.5))
    else:
        size = {"o": 12, "talk1": 6, "talk2": 13, "gasp": 16}.get(mouth, 8)
        rect = skia.Rect.MakeXYWH(mx - size * .75, my - size * .7, size * 1.5, size * 1.4)
        c.drawOval(rect, fill(0xFF3A1416))
        c.drawOval(rect, stroke(4))
    if s.get("sweat"):
        drop = (s["t"] * 26) % 34
        c.drawCircle(r * .82, -r * .1 + drop, 6, fill(0xFF9FD3E8))
        c.drawCircle(r * .82, -r * .1 + drop, 6, stroke(2.5))
    c.restore()


def character(c, s):
    """Character rig. Origin between the feet; s['walk'] is a phase in radians, None when standing."""
    c.save()
    c.translate(s["x"], s["y"])
    c.scale(s["scale"] * s.get("dir", 1), s["scale"])
    c.rotate(s.get("lean", 0))
    walk = s.get("walk")
    breath = math.sin(s["t"] * s.get("breath_rate", 1.7)) * s.get("breath_amp", 2)
    bob = abs(math.sin(walk)) * 7 if walk is not None else 0
    sit = s.get("sit")
    hip = (0, (-46 if sit else -112 - bob) + breath * .3)
    shoulder_y = (-126 if sit else -192 - bob) + breath
    jacket, jacket_dark = s.get("jacket", (JACKET, JACKET_DARK))
    swing = math.sin(walk) * .55 if walk is not None else 0
    for side, sw in (() if sit else ((-1, swing), (1, -swing))):
        knee = (hip[0] + side * 10 + math.sin(sw) * 54, hip[1] + math.cos(sw) * 54)
        lift = max(0, math.sin(sw * 4)) * 8 if walk is not None else 0
        foot = (knee[0] + math.sin(sw * .4) * 54, -4 - lift)
        limb(c, (hip[0] + side * 10, hip[1]), knee)
        limb(c, knee, foot)
        c.drawLine(foot[0] - 2, foot[1], foot[0] + 18, foot[1], stroke(11))
    left, right = (-24, shoulder_y + 8), (24, shoulder_y + 8)
    arm_back = s.get("arm_l", (-.1, .1))
    arm(c, left, arm_back[0] + (swing if walk is not None else 0), arm_back[1], -1)
    # gown
    gown = skia.Path()
    gown.moveTo(-26, shoulder_y)
    gown.quadTo(0, shoulder_y - 9, 26, shoulder_y)
    hem = 4 if sit else 38
    gown.lineTo(46, hip[1] + hem)
    gown.quadTo(0, hip[1] + hem + 11, -46, hip[1] + hem)
    gown.close()
    c.drawPath(gown, fill(jacket))
    c.save()
    c.clipPath(gown, doAntiAlias=True)
    c.drawRect(skia.Rect.MakeLTRB(-60, shoulder_y, -10, hip[1] + 60), fill(jacket_dark))
    if not s.get("back"):
        c.drawLine(0, shoulder_y + 12, 0, hip[1] + 60, stroke(3))
    c.restore()
    c.drawPath(gown, stroke(6))
    if not s.get("back"):
        c.drawPath(poly([(-13, shoulder_y - 4), (0, shoulder_y + 15), (13, shoulder_y - 4)]), fill(SHIRT))
        c.drawPath(poly([(-13, shoulder_y - 4), (0, shoulder_y + 15), (13, shoulder_y - 4)]), stroke(4.5))
    if sit:  # knees drawn up in front of the body
        for side in (-1, 1):
            knee, foot = (side * 30, hip[1] - 66), (side * 50, -4)
            for width, color in ((34, INK), (24, 0xFF2F3A44)):
                c.drawLine(side * 16, hip[1] + 6, *knee, stroke(width, color))
                c.drawLine(*knee, *foot, stroke(width, color))
            c.drawLine(foot[0] - 4 * side, foot[1], foot[0] + 22 * side, foot[1], stroke(16))
    arm_front = s.get("arm_r", (.1, .1))
    s["hand"] = arm(c, right, arm_front[0] - (swing * .25 if walk is not None else 0), arm_front[1], 1, holding=s.get("flashlight", False))
    if s.get("phone"):
        hx, hy = s["hand"]
        c.drawRoundRect(skia.Rect.MakeXYWH(hx - 12, hy - 40, 26, 46), 5, 5, fill(0xFF1C2226))
        c.drawRoundRect(skia.Rect.MakeXYWH(hx - 12, hy - 40, 26, 46), 5, 5, stroke(4))
        c.drawRect(skia.Rect.MakeXYWH(hx - 7, hy - 34, 16, 32), fill(0xFFB9E4EC))
    head(c, 0 + s.get("head_dx", 0), shoulder_y - 56, s)
    c.restore()


class Cam:
    def __init__(self, a, b, t):
        k = ease(t)
        self.x, self.y, self.z = lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)

    def apply(self, c, shake=(0, 0)):
        scale = BASE * self.z
        half_w, half_h = W / 2 / scale, H / 2 / scale
        self.x = min(max(self.x, half_w), BG_W - half_w)
        self.y = min(max(self.y, half_h), BG_H - half_h)
        c.translate(W / 2 + shake[0], H / 2 + shake[1])
        c.scale(scale, scale)
        c.translate(-self.x, -self.y)


def blink(t, seed=0.0):
    phase = (t + seed) % 3.7
    return 1.0 if phase < .09 else 0.0


def talk(t):
    return ["talk1", "talk2", "o", "talk2", "talk1"][int(t * 9) % 5]


def beam(c, x, y, angle, length=560, spread=13, alpha=72):
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    paint = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    paint.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(length, 0)],
                                                   [skia.ColorSetARGB(alpha, 245, 230, 170), skia.ColorSetARGB(0, 245, 230, 170)]))
    half = math.tan(math.radians(spread)) * length
    c.drawPath(poly([(0, -6), (length, -half), (length, half), (0, 6)]), paint)
    c.restore()


def steam(c, x, y, t):
    for i in range(3):
        p = skia.Path()
        ox = x + (i - 1) * 16
        p.moveTo(ox, y)
        for j in range(1, 5):
            p.quadTo(ox + math.sin(t * 2 + i + j) * 15, y - j * 21 + 10, ox + math.sin(t * 2 + i + j + 1) * 7, y - j * 21)
        paint = stroke(5, skia.ColorSetARGB(int(95 + 40 * math.sin(t + i)), 225, 230, 225))
        c.drawPath(p, paint)


def cup(c, x, y, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = skia.Path()
    body.moveTo(-34, -46)
    body.lineTo(34, -46)
    body.lineTo(26, 16)
    body.quadTo(0, 25, -26, 16)
    body.close()
    handle = skia.Rect.MakeXYWH(26, -32, 34, 32)
    c.drawOval(handle, stroke(9))
    c.drawPath(body, fill(0xFFD8D4C6))
    c.drawPath(body, stroke(6))
    c.drawOval(skia.Rect.MakeXYWH(-34, -55, 68, 19), fill(0xFF3A2317))
    c.drawOval(skia.Rect.MakeXYWH(-34, -55, 68, 19), stroke(6))
    c.drawOval(skia.Rect.MakeXYWH(-52, 12, 104, 22), stroke(5, 0xAA201A15))
    c.restore()


def chalk_text(c, board, progress):
    x, y, w, h = board
    lines = ["NO ABRAS", "LA ÚLTIMA", "PUERTA"]
    total = sum(len(l) for l in lines)
    shown = int(progress * total)
    for i, line in enumerate(lines):
        part = line[:max(0, shown)]
        shown -= len(line)
        if not part:
            break
        width = BOARD_FONT.measureText(line)
        c.drawString(part, x + (w - width) / 2, y + h * (.34 + i * .2), BOARD_FONT, fill(0xF2ECE6D0))


# ---------------------------------------------------------------- scene coordinates, in background pixels
from layout import LAYOUT, beats  # noqa: E402  tuned per generated background

BT = beats(TL)
LINES = BT["lines"]


def door_gap(k):
    """The cabin behind the lobby doors: a plain dark inside lit from above."""
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT["lobby"]["doors"]
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [0xFF4E7A68, 0xFF10201C]))
        c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), p)
    return draw


def door_panels(k):
    """The doors are cut from the background itself and slide apart, so they keep its drawing."""
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT["lobby"]["doors"]
        mid = (x0 + x1) / 2
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1))
        shift = ease(k) * (mid - x0)
        c.drawImageRect(BGS["lobby"], skia.Rect.MakeLTRB(x0, y0, mid, y1), skia.Rect.MakeLTRB(x0 - shift, y0, mid - shift, y1), SAMPLING, paint)
        c.drawImageRect(BGS["lobby"], skia.Rect.MakeLTRB(mid, y0, x1, y1), skia.Rect.MakeLTRB(mid + shift, y0, x1 + shift, y1), SAMPLING, paint)
        c.restore()
    return draw


def shaft_light(pos):
    """Light from the landing doors sliding down the shaft walls, so the car reads as moving."""
    def draw(c, t, paint):
        for j in range(4):
            y = (pos * 240 + j * 260) % 1040 - 120
            g = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
            g.setColor(skia.ColorSetARGB(52, 200, 225, 190))
            c.drawRect(skia.Rect.MakeXYWH(0, y, BG_W, 46), g)
    return draw


def doors_open(name, k, rescuer=None):
    """Closed doors cut from the background slide apart; light and, optionally, a rescuer appear behind them."""
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT[name]["doors"]
        mid = (x0 + x1) / 2
        if k <= 0:
            return
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [0xFFE6E2C8, 0xFF8A9C8C]))
        c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), p)
        if rescuer:
            c.save()
            c.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1))
            character(c, rescuer)
            c.restore()
        c.save()
        c.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1))
        shift = ease(k) * (mid - x0)
        c.drawImageRect(BGS[name], skia.Rect.MakeLTRB(x0, y0, mid, y1), skia.Rect.MakeLTRB(x0 - shift, y0, mid - shift, y1), SAMPLING, paint)
        c.drawImageRect(BGS[name], skia.Rect.MakeLTRB(mid, y0, x1, y1), skia.Rect.MakeLTRB(mid + shift, y0, x1 + shift, y1), SAMPLING, paint)
        c.restore()
    return draw


def phone_hand(x, y, k):
    """Close-up of the phone in the character's hand: no signal bars."""
    def draw(c, t, paint):
        hy = lerp(y + 260, y, ease(k * 3))
        c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Blend(LAYOUT["cabina"]["light"], skia.BlendMode.kModulate)))
        c.drawLine(x + 40, hy + 120, x + 300, hy + 600, stroke(96))
        c.drawLine(x + 40, hy + 120, x + 300, hy + 600, stroke(84, JACKET))
        phone = skia.Rect.MakeXYWH(x - 90, hy - 170, 180, 320)
        c.drawRoundRect(phone, 24, 24, fill(0xFF1C2226))
        c.drawRoundRect(phone, 24, 24, stroke(7))
        c.drawRect(skia.Rect.MakeXYWH(x - 72, hy - 145, 144, 260), fill(0xFF9FCFD8))
        for b in range(4):
            bar = skia.Rect.MakeXYWH(x - 44 + b * 22, hy - 40 - b * 16, 14, 18 + b * 16)
            c.drawRect(bar, stroke(3.5, 0xFF2E4A50))
        if int(t * 2.4) % 2:
            c.drawLine(x - 50, hy - 105, x + 46, hy - 10, stroke(9, 0xFFB4382C))
            c.drawLine(x + 46, hy - 105, x - 50, hy - 10, stroke(9, 0xFFB4382C))
        for side in (-1, 1):
            c.drawCircle(x + side * 96, hy + 40, 38, fill(SKIN))
            c.drawCircle(x + side * 96, hy + 40, 38, stroke(6))
        c.restore()
    return draw


def car_at(dy):
    """Moves the car, cut from the background, along the black shaft."""
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT["hueco"]["car"]
        c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(0xFF000000))
        c.drawImageRect(BGS["hueco"], skia.Rect.MakeLTRB(x0, y0, x1, y1), skia.Rect.MakeLTRB(x0, y0 + dy, x1, y1 + dy), SAMPLING, paint)
    return draw


def button_glow(x, y, level):
    def draw(c, t, paint):
        if level > 0:
            c.drawCircle(x, y, 36, skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen, Color=skia.ColorSetARGB(int(190 * level), 240, 200, 110),
                                              MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 13)))
    return draw


def pressing_hand(x, y, reach):
    """The character's arm entering the close-up, drawn with the rig's sleeve and outline."""
    def draw(c, t, paint):
        hx, hy = lerp(x + 340, x + 18, reach), lerp(y + 430, y + 44, reach)
        ex, ey = hx + 520, hy + 500
        c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Blend(LAYOUT["panel"]["light"], skia.BlendMode.kModulate)))
        c.drawLine(hx + 34, hy + 34, ex, ey, stroke(96))
        c.drawLine(hx + 34, hy + 34, ex, ey, stroke(84, JACKET))
        c.save()
        c.translate(hx, hy)
        c.rotate(-44)
        finger = skia.Rect.MakeXYWH(-13, -66, 26, 72)
        c.drawRoundRect(finger, 13, 13, fill(SKIN))
        c.drawRoundRect(finger, 13, 13, stroke(6))
        c.restore()
        c.drawCircle(hx + 14, hy + 16, 36, fill(SKIN))
        c.drawCircle(hx + 14, hy + 16, 36, stroke(6))
        c.restore()
    return draw


def air(k):
    """Dust carried by the air coming through the grille."""
    def draw(c, t, paint):
        for i in range(46):
            r = random.Random(i)
            life = (t * r.uniform(.25, .5) + r.random()) % 1
            x = r.uniform(390, 1160) + math.sin(t * 1.3 + i) * 12 + life * 50
            y = r.uniform(215, 560) + life * r.uniform(90, 230)
            c.drawCircle(x, y, r.uniform(1.6, 3.6), fill(skia.ColorSetARGB(int(150 * math.sin(life * math.pi)), 205, 225, 215)))
    return draw


def shots(t):
    """Every sentence has its own action. Returns background, camera, draw lists and light settings for time t."""
    sc = next((s for s in TL["scenes"] if t < s["end"]), TL["scenes"][-1])
    i = max((j for j, l in enumerate(LINES) if t >= l["start"]), default=0)
    start = LINES[i]["start"] if i else 0.0
    stop = LINES[i + 1]["start"] if i + 1 < len(LINES) else TL["duration"]
    lt = t - start
    k = min(1.0, lt / max(.1, stop - start))
    base = dict(t=t, blink=blink(t))
    out = dict(bg="cabina", shake=(0, 0), dark=.0, over=[], flicker=.25)

    def at(name):
        out["bg"], out["tint"] = name, LAYOUT[name]["tint"]

    at("cabina")
    if i == 0:  # Son las ocho de la noche: arrives at the lobby
        at("lobby")
        out["cam"] = Cam((768, 432, 1.0), (700, 440, 1.08), k)
        out["char"] = dict(base, x=lerp(40, 560, k), y=800, scale=.95, walk=t * 6, face=.55, look=(.8, -.2), mouth="flat")
    elif t < BT["press"]:  # Entras al elevador: the doors open and the character walks in
        at("lobby")
        opening = ease((t - BT["door_open"]) / .55)
        kw = (t - BT["door_open"]) / (BT["press"] - BT["door_open"])
        out["cam"] = Cam((700, 440, 1.08), (770, 430, 1.3), kw)
        out["over"] = [door_gap(opening)]
        inside = kw > .86
        out["char"] = dict(base, x=lerp(560, 770, ease(kw)), y=lerp(800, 625, ease(kw)), scale=lerp(.95, .66, ease(kw)), walk=t * 6,
                           back=kw > .45, face=.3 if kw <= .45 else 0, mouth="flat")
        out["over"].append(door_panels(opening))
        if inside:
            out["front"] = [door_panels(1 - ease((kw - .86) / .14))]
    elif t < BT["rise"]:  # presionas el botón de tu piso
        at("panel")
        x, y = LAYOUT["panel"]["buttons"][0]
        kp = (t - BT["press"]) / (BT["rise"] - BT["press"])
        reach = ease(kp / .35) if kp < .6 else 1 - ease((kp - .6) / .4)
        lit = 1.0 if t >= BT["press_hit"] else 0.0
        out["cam"] = Cam((790, 410, 1.45), (840, 440, 1.75), kp)
        out["over"] = [button_glow(x, y, lit)]
        out["front"] = [pressing_hand(x, y, reach)]
    elif t < LINES[2]["start"]:  # y comienzas a subir: the car rises in the shaft
        at("hueco")
        cx, cy = LAYOUT["hueco"]["car"]
        kr = (t - BT["rise"]) / (LINES[2]["start"] - BT["rise"])
        out["cam"] = Cam((cx, cy + 40, 1.7), (cx, cy, 1.8), kr)
        out["over"] = [shaft_light(t - BT["rise"])]
        out["shake"] = (math.sin(t * 40) * .8, 0)
    elif i == 2:  # Pero de repente: waits, calm, watching the ceiling
        out["cam"] = Cam((768, 500, 1.35), (768, 480, 1.55), k)
        look = math.sin(t * .9)
        out["char"] = dict(base, x=768, y=835, scale=1.15, face=look * .15, look=(look * .6, -.7), mouth="flat", arm_l=(.1, .15), arm_r=(.1, .15))
    elif i == 3:  # Un golpe
        hit = math.exp(-lt * 3.6)
        r = random.Random(int(t * FPS))
        out["shake"] = (r.uniform(-1, 1) * hit * 34, r.uniform(-1, 1) * hit * 28)
        out["dark"] = .95 if lt < .09 else hit * .28
        out["cam"] = Cam((768, 480, 1.7), (768, 500, 1.7), k)
        out["char"] = dict(base, x=768, y=835 + hit * 14, scale=1.15, lean=hit * 7, eye=1.35, brow=-1, mouth="gasp", look=(0, -.2), arm_l=(.9, .4), arm_r=(.9, .4), blink=0)
    elif t < BT["halt"]:  # Las luces parpadean: the tube goes on and off
        at("techo")
        kl = (t - LINES[4]["start"]) / (BT["halt"] - LINES[4]["start"])
        pulse = random.Random(int(t * 11)).random()
        out["cam"] = Cam((768, 380, 1.15), (768, 330, 1.45), kl)
        out["dark"] = .82 if pulse < .45 else 0
        out["flicker"] = 0
    elif i == 4:  # y el elevador se detiene: the car bounces and stays still
        at("hueco")
        dt = t - BT["halt"]
        cx, cy = LAYOUT["hueco"]["car"]
        out["cam"] = Cam((cx, cy, 2.0), (cx, cy, 2.2), k)
        out["over"] = [shaft_light(BT["hit"] - BT["rise"])]
        out["shake"] = (0, math.sin(dt * 13) * math.exp(-dt * 3.2) * 10)
        out["flicker"] = 1.2
    elif i == 5:  # Presionas los botones: hits several, none lights up
        at("panel")
        which = min(2, sum(t >= p for p in BT["presses"]))
        phase = min((abs(t - p) for p in BT["presses"]), default=1)
        x, y = LAYOUT["panel"]["buttons"][which + 1]
        out["cam"] = Cam((790, 400, 1.45), (760, 400, 1.55), k)
        out["front"] = [pressing_hand(x, y, max(.72, 1 - phase * 1.2))]
    elif i == 6:  # Nada: the character's blank face
        out["cam"] = Cam((768, 500, 2.3), (768, 495, 2.55), k)
        out["char"] = dict(base, x=768, y=835, scale=1.15, look=(0, 0), brow=-.9, mouth="flat", blink=1.0 if .35 < lt < .47 else 0)
        out["dark"] = .14
    elif i == 7:  # Intentas abrir las puertas: from behind, pushing with both arms
        at("puertas")
        strain = abs(math.sin(lt * 5.5))
        out["cam"] = Cam((768, 500, 1.15), (768, 480, 1.42), k)
        out["char"] = dict(base, x=768 + math.sin(lt * 13) * 3 * strain, y=835, scale=1.4, back=True, lean=-2 + strain * 4,
                           arm_l=(1.65, .25), arm_r=(1.65, .25), breath_rate=9, breath_amp=4)
        out["shake"] = (math.sin(t * 31) * strain * 1.4, 0)
    elif i == 8:  # Estás atrapado: the camera leaves the car, a tiny box in the dark
        at("hueco")
        cx, cy = LAYOUT["hueco"]["car"]
        out["cam"] = Cam((cx, cy, 3.2), (768, 432, 1.0), k)
        out["over"] = [shaft_light(BT["hit"] - BT["rise"])]
        out["flicker"] = 0
    elif i == 9:  # Lo primero que debes saber... sin oxigeno: panic, then slower breathing
        calm = ease((k - .62) / .3)
        if .38 <= k < .62:  # un elevador detenido
            at("hueco")
            cx, cy = LAYOUT["hueco"]["car"]
            out["cam"] = Cam((cx, cy, 2.4), (cx, cy, 2.6), (k - .38) / .24)
            out["over"] = [shaft_light(BT["hit"] - BT["rise"])]
        else:
            out["cam"] = Cam((768, 500, 1.75), (768, 520, 2.1), k)
            out["char"] = dict(base, x=768, y=835, scale=1.15, brow=lerp(-1, -.3, calm), eye=lerp(1.25, 1, calm), mouth="o" if calm < .5 else "flat", look=(0, -.1),
                               arm_r=(.8, 2.0), arm_l=(.1, .15), breath_rate=lerp(10, 2.2, calm), breath_amp=lerp(4, 6, calm))
    elif i == 10 and k < .56:  # Los elevadores tienen sistemas de ventilacion
        at("rejilla")
        out["cam"] = Cam((768, 400, 1.05), (768, 400, 1.32), k / .56)
        out["over"] = [air(k)]
        out["flicker"] = 0
    elif i == 10:  # y no son cajas hermeticas: looks up at the vent, calmer
        kc = (k - .56) / .44
        out["cam"] = Cam((768, 470, 1.6), (768, 440, 1.3), kc)
        out["char"] = dict(base, x=768, y=835, scale=1.15, look=(.1, -1), face=.05, brow=-.2, mouth="flat", arm_r=(.15, .15), arm_l=(.15, .15), breath_rate=2.2, breath_amp=3)
    elif i == 11:  # pasan las horas: sitting against the back wall while the light changes
        out["cam"] = Cam((768, 560, 1.35), (768, 600, 1.6), k)
        out["char"] = dict(base, x=768, y=835, scale=1.15, sit=True, look=(.2, -.2), brow=-.5, mouth="flat", arm_l=(.6, .9), arm_r=(.6, .9))
        out["dark"] = .22 + .18 * math.sin(lt * 3)
    elif i == 12:  # el espacio se vuelve cada vez mas pequeno
        out["cam"] = Cam((768, 640, 1.6), (768, 660, 2.4), k)
        out["squeeze"] = ease(k)
        out["char"] = dict(base, x=768, y=835, scale=1.15, sit=True, eye=1.2, brow=-1, mouth="worry", breath_rate=9, breath_amp=3, look=(math.sin(t * 3) * .8, 0), arm_l=(.6, .9), arm_r=(.6, .9))
    elif i == 13:  # el cansancio, la sed
        out["cam"] = Cam((768, 640, 2.3), (768, 650, 2.5), k)
        out["char"] = dict(base, x=768, y=835, scale=1.15, sit=True, eye=.85, brow=-.6, mouth="o", sweat=True, blink=1.0 if (t % 2.2) < .25 else 0, arm_l=(.6, .9), arm_r=(.6, .9))
        out["dark"] = .2
    elif i == 14:  # Intentas llamar a alguien, pero no tienes senal
        if k < .4:
            out["cam"] = Cam((768, 540, 1.7), (768, 520, 1.85), k / .4)
            out["char"] = dict(base, x=768, y=835, scale=1.15, phone=True, arm_r=(2.5, .9), look=(.7, -.3), face=.2, brow=-.6, mouth="flat")
        else:
            out["cam"] = Cam((768, 432, 1.15), (768, 432, 1.25), (k - .4) / .6)
            out["dark"] = .35
            out["front"] = [phone_hand(768, 430, (k - .4) / .6)]
    elif i == 15:  # Golpeas la puerta y gritas
        if k < .55:
            at("puertas")
            swing = max(0.0, math.sin(lt * 12))
            hit = max((math.exp(-(t - h) * 9) for h in BT["knocks"] if t >= h), default=0)
            out["cam"] = Cam((768, 500, 1.3), (768, 490, 1.45), k / .55)
            out["char"] = dict(base, x=768, y=835, scale=1.4, back=True, arm_r=(1.3 + swing * .9, .3), arm_l=(1.4, .3), lean=hit * 3)
            out["shake"] = (math.sin(t * 50) * hit * 6, 0)
        else:
            out["cam"] = Cam((768, 520, 2.2), (768, 515, 2.4), (k - .55) / .45)
            out["char"] = dict(base, x=768, y=835, scale=1.15, mouth="gasp" if int(t * 5) % 2 else "o", eye=1.25, brow=.6, look=(0, -.4), arm_l=(2.5, .6), arm_r=(2.5, .6))
            out["shake"] = (math.sin(t * 37) * 1.5, 0)
    elif i in (16, 17):  # Pasan dos horas. Despues cinco.
        out["caption"] = "2 HORAS" if i == 16 else "5 HORAS"
        out["cam"] = Cam((768, 600, 1.5 if i == 16 else 1.9), (768, 610, 1.6 if i == 16 else 2.05), k)
        out["char"] = dict(base, x=768, y=835, scale=1.15, sit=True, eye=.8 if i == 17 else .95, brow=-.4, mouth="flat", look=(0, .3), arm_l=(1.1, .9), arm_r=(1.1, .9), blink=.6 if i == 17 else base["blink"])
        out["dark"] = (.25 if i == 16 else .4) + .25 * abs(math.sin(lt * 8))
    elif i == 18:  # La temperatura... ventilacion, el edificio y el fallo
        if k < .42:
            out["cam"] = Cam((768, 640, 2.0), (768, 640, 2.2), k / .42)
            out["char"] = dict(base, x=768, y=835, scale=1.15, sit=True, sweat=True, eye=.9, brow=-.6, mouth="o", arm_l=(.6, .9), arm_r=(.6, .9))
        elif k < .64:
            at("rejilla")
            out["cam"] = Cam((768, 400, 1.15), (768, 400, 1.3), (k - .42) / .22)
            out["over"] = [air(k)]
        elif k < .82:
            at("hueco")
            out["cam"] = Cam((768, 432, 1.0), (768, 432, 1.08), (k - .64) / .18)
            out["over"] = [shaft_light(BT["hit"] - BT["rise"])]
        else:
            at("techo")
            out["cam"] = Cam((768, 330, 1.45), (768, 330, 1.55), (k - .82) / .18)
            out["dark"] = .8 if random.Random(int(t * 9)).random() < .35 else .15
        out["flicker"] = 0
    elif i == 19:  # Y entonces llega la madrugada: nobody in the lobby
        at("lobby")
        out["cam"] = Cam((768, 430, 1.0), (768, 400, 1.2), k)
        out["dark"] = .45
        out["flicker"] = 0
    elif i == 20:  # Lo mas dificil ya no es solamente estar encerrado
        out["cam"] = Cam((768, 650, 2.4), (768, 650, 2.6), k)
        out["char"] = dict(base, x=768, y=835, scale=1.15, sit=True, eye=.7, brow=-.7, mouth="flat", look=(0, .4), arm_l=(1.1, .9), arm_r=(1.1, .9))
        out["dark"] = .3
    elif i == 21:  # Es no saber cuando alguien va a encontrarte
        at("hueco")
        cx, cy = LAYOUT["hueco"]["car"]
        out["cam"] = Cam((cx, cy, 2.2), (768, 432, 1.0), k)
        out["over"] = [shaft_light(BT["hit"] - BT["rise"])]
        out["flicker"] = 0
    elif i == 22:  # boton de alarma, pedir ayuda y esperar al personal de rescate
        if k < .38:
            at("panel")
            x, y = LAYOUT["panel"]["buttons"][3]
            kp = k / .38
            out["cam"] = Cam((700, 400, 1.45), (650, 390, 1.6), kp)
            out["over"] = [button_glow(x, y, 1.0 if t >= BT["alarm"] else 0)]
            out["front"] = [pressing_hand(x, y, ease(kp / .4) if kp < .7 else 1 - ease((kp - .7) / .3))]
        elif k < .62:
            out["cam"] = Cam((768, 520, 1.9), (768, 520, 2.1), (k - .38) / .24)
            out["char"] = dict(base, x=768, y=835, scale=1.15, face=.6, look=(1, -.3), mouth=talk(t), brow=-.3, arm_r=(1.0, .5))
        else:
            at("puertas")
            ko = ease((t - BT["doors"]) / 1.2)
            helper = dict(t=t, x=768, y=700, scale=1.0, helmet=True, jacket=(0xFFB8862E, 0xFF8E6522), look=(0, 0), mouth="flat",
                          flashlight=True, arm_r=(1.0, .2), blink=blink(t, 1.3))
            out["cam"] = Cam((768, 470, 1.1), (768, 450, 1.25), (k - .62) / .38)
            out["over"] = [doors_open("puertas", ko, helper)]
            out["char"] = dict(base, x=560, y=835, scale=1.3, back=True, arm_l=(.2, .2), arm_r=(.2, .2))
            out["flicker"] = 0
    elif i == 23:  # Nunca intentar salir por tu cuenta
        out["cam"] = Cam((768, 470, 1.4), (768, 500, 1.6), k)
        shake_no = math.sin(lt * 7) * (1 - ease(k)) if k > .35 else 0
        out["char"] = dict(base, x=768, y=835, scale=1.15, look=(shake_no, -1 if k < .35 else 0), face=shake_no * .5, brow=-.3, mouth="flat")
    else:  # emergencia mucho mas peligrosa: down into the dark shaft
        at("hueco")
        cx, cy = LAYOUT["hueco"]["car"]
        out["cam"] = Cam((cx, cy, 1.8), (cx, 760, 1.6), k)
        out["over"] = [shaft_light(BT["hit"] - BT["rise"])]
        out["dark"] = .5 * ease(k)
        out["flicker"] = 0
    return out, sc


DUST = [(random.Random(i).uniform(0, W), random.Random(i + 900).uniform(0, H), random.Random(i + 77).uniform(.4, 1.4)) for i in range(55)]


def frame(canvas, t):
    s, sc = shots(t)
    cam = s["cam"]
    canvas.clear(skia.ColorBLACK)
    canvas.save()
    cam.apply(canvas, s["shake"])
    bg_paint = skia.Paint(ColorFilter=skia.ColorFilters.Blend(s["tint"], skia.BlendMode.kModulate))
    canvas.drawImage(BGS[s["bg"]], 0, 0, SAMPLING, bg_paint)
    for item in s["over"]:
        item(canvas, t, bg_paint)
    ch = s.get("char")
    if ch:
        canvas.drawOval(skia.Rect.MakeXYWH(ch["x"] - 74 * ch["scale"], ch["y"] - 12 * ch["scale"], 148 * ch["scale"], 26 * ch["scale"]),
                        skia.Paint(AntiAlias=True, Color=0x9A000000, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9)))
        canvas.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Blend(LAYOUT[s["bg"]]["light"], skia.BlendMode.kModulate)))
        character(canvas, ch)
        canvas.restore()
    for item in s.get("front", []):
        item(canvas, t, bg_paint)
    canvas.restore()
    # ambient light flicker, dust, darkening, vignette
    noise = math.sin(t * 37) * math.sin(t * 11.3) * math.sin(t * 5.1)
    level = s["dark"] + max(0, noise) * .2 * s["flicker"]
    if level > 0:
        canvas.drawRect(skia.Rect.MakeWH(W, H), fill(skia.ColorSetARGB(int(min(1, level) * 255), 0, 0, 0)))
    for i, (x, y, z) in enumerate(DUST):
        px = (x + math.sin(t * .3 + i) * 26 + t * 6 * z) % W
        py = (y + math.cos(t * .23 + i) * 18 - t * 3 * z) % H
        canvas.drawCircle(px, py, 1.3 * z, fill(skia.ColorSetARGB(int(42 * z), 225, 235, 225)))
    vig = skia.Paint()
    vig.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * .68, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(200, 0, 0, 0)], [.5, 1.0]))
    canvas.drawRect(skia.Rect.MakeWH(W, H), vig)
    if s.get("squeeze"):
        q = s["squeeze"]
        for side in (0, 1):
            g = skia.Paint()
            x0 = 0 if side == 0 else W
            g.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, 0), skia.Point(abs(x0 - W * .42 * q), 0)],
                                                       [skia.ColorSetARGB(250, 0, 0, 0), skia.ColorSetARGB(0, 0, 0, 0)]))
            canvas.drawRect(skia.Rect.MakeWH(W, H), g)
    if s.get("caption"):
        x = (W - CAPTION_FONT.measureText(s["caption"])) / 2
        canvas.drawString(s["caption"], x, 110, CAPTION_FONT, stroke(12))
        canvas.drawString(s["caption"], x, 110, CAPTION_FONT, fill(0xFFF2E6B8))
    fade = max(s.get("fade", 0), 1 - ease(t / .45), ease((t - (TL["duration"] - .5)) / .45))
    if fade > 0:
        canvas.drawRect(skia.Rect.MakeWH(W, H), fill(skia.ColorSetARGB(int(fade * 255), 0, 0, 0)))
    subtitle(canvas, t, sc)


CUES = json.loads((ROOT / "cues.json").read_text(encoding="utf-8"))


def subtitle(canvas, t, sc):
    for cue in CUES:
        if cue["start"] <= t < cue["end"] + .12:
            clean = cue["text"].rstrip(".,;")
            x = (W - SUB_FONT.measureText(clean)) / 2
            canvas.drawString(clean, x, H - 44, SUB_FONT, stroke(9))
            canvas.drawString(clean, x, H - 44, SUB_FONT, fill(0xFFFFFFFF))
            return


def main():
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    surface = skia.Surface(pixels, colorType=skia.kRGBA_8888_ColorType)
    canvas = surface.getCanvas()
    if "--stills" in sys.argv:
        out = ROOT / "stills"
        out.mkdir(exist_ok=True)
        from PIL import Image
        for value in sys.argv[sys.argv.index("--stills") + 1].split(","):
            frame(canvas, float(value))
            Image.fromarray(pixels[:, :, :3].copy()).save(out / f"t{float(value):05.1f}.png")
        return
    total = int(TL["duration"] * FPS)
    target = ROOT / "output" / "video_mudo.mp4"
    target.parent.mkdir(exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(target)], stdin=subprocess.PIPE)
    for i in range(total):
        frame(canvas, i / FPS)
        ff.stdin.write(pixels.tobytes())
        if i % 300 == 0:
            print(i, total, flush=True)
    ff.stdin.close()
    ff.wait()
    print("ok", target)


main()
