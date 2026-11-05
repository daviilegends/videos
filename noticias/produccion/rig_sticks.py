"""Sticks character rig, extracted from production\render.py so other series can draw the same characters."""
import math

import skia

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
    c.drawPath(poly(spikes), fill(s.get("hair_color", HAIR)))
    c.drawPath(poly(spikes), stroke(6))
    if s.get("helmet"):
        c.drawArc(skia.Rect.MakeXYWH(-r - 8, -r - 22, 2 * r + 16, 2 * r + 10), 180, 180, True, fill(0xFFC9A23A))
        c.drawArc(skia.Rect.MakeXYWH(-r - 8, -r - 22, 2 * r + 16, 2 * r + 10), 180, 180, True, stroke(6))
        c.drawLine(-r - 18, -28, r + 18, -28, stroke(10))
    if s.get("back"):  # seen from behind: only hair
        c.drawCircle(0, -6, r + 1, fill(s.get("hair_color", HAIR)))
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


