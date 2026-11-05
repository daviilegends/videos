"""Shared props for the teacher's LoL classes (episodes 10+): jungle monsters, turret plates, coins, XP bar,
level badge, cooldown clock, stamp. Everything draws in the current canvas coordinates (world or HUD)."""
import math

import skia

import motor as M
from motor import BLUE, GOLD, INK, RED, back, clamp, ease, fill, path, stroke, text

ORO = 0xFFFFD34D
PURPLE = 0xFF9B6CF0
G = M.G
LANE_Y = {k: G.lane_y(k, 6000) for k in ("superior", "central", "inferior")}


def eyes(c, x, y, r, look=0.0, angry=False):
    for sx in (-1, 1):
        c.drawCircle(x + sx * r * 1.3, y, r, fill(0xFFFFF4C8))
        c.drawCircle(x + sx * r * 1.3 + look * r * .4, y + r * .15, r * .5, fill(INK))
        if angry:
            c.drawLine(x + sx * r * 2.2, y - r * 1.4, x + sx * r * .5, y - r * .8, stroke(r * .45))


KIND_SPRITE = {"crab": "cangrejo", "bug": "larva", "herald": "heraldo", "baron": "baron"}


def monster(c, x, y, s, t, body, belly=None, kind="blob", k=1.0, hp=1.0, label=None, angry=False, flash=0.0,
            sprite=None, flip=False):
    """Jungle monster: official render (sprite name, or by kind: crab/bug/herald/baron); cartoon blob fallback."""
    if k <= 0:
        return
    name = sprite or KIND_SPRITE.get(kind)
    if name:
        top = M.sprite(c, name, x, y, s, t, k, flash, flip)
        if hp < 1:
            M.bar(c, x, top - 20, 150 * s, hp)
        if label:
            M.badge(c, label, x, y + 130 * s, 30, body, 0xFFFFFFFF)
        return
    bob = math.sin(t * 3) * 6
    c.save()
    c.translate(x, y + bob)
    c.scale(s * back(min(1, k)), s * back(min(1, k)))
    col = body if flash <= 0 else 0xFFFFFFFF
    c.drawOval(skia.Rect.MakeXYWH(-90, 60, 180, 36), fill(0x55000000))
    if kind == "crab":
        for sx in (-1, 1):
            for j in range(3):
                c.drawLine(sx * 50, 30, sx * (95 + j * 10), 40 + j * 18 + math.sin(t * 12 + j) * 6, stroke(9))
            claw = path([(sx * 60, -10), (sx * 120, -50), (sx * 140, -20), (sx * 110, -5)])
            c.drawPath(claw, fill(col))
            c.drawPath(claw, stroke(6))
        c.drawOval(skia.Rect.MakeXYWH(-80, -40, 160, 90), fill(col))
        c.drawOval(skia.Rect.MakeXYWH(-80, -40, 160, 90), stroke(7))
        for sx in (-1, 1):
            c.drawLine(sx * 22, -36, sx * 30, -70, stroke(6))
            c.drawCircle(sx * 30, -78, 13, fill(0xFFFFF4C8))
            c.drawCircle(sx * 30, -76, 6, fill(INK))
    elif kind == "bug":
        for j in range(3):
            seg = skia.Rect.MakeXYWH(-40 + j * 30, -30 - j * 6, 70, 60)
            c.drawOval(seg, fill(col))
            c.drawOval(seg, stroke(6))
        for sx in (-1, 1):
            c.drawLine(40 + sx * 10, -60, 60 + sx * 30, -100 + math.sin(t * 8) * 8, stroke(5))
        eyes(c, 60, -44, 9, .5, angry)
    elif kind in ("herald", "baron"):
        big = 1.5 if kind == "baron" else 1.1
        c.scale(big, big)
        body_p = path([(-90, 50), (-110, -40), (-60, -120), (0, -150), (60, -120), (110, -40), (90, 50)])
        c.drawPath(body_p, fill(col))
        c.drawPath(body_p, stroke(7))
        if kind == "baron":
            for sx in (-1, 1):
                c.drawPath(path([(sx * 50, -130), (sx * 90, -200), (sx * 70, -120)]), fill(0xFFE8E0F8))
                c.drawPath(path([(sx * 50, -130), (sx * 90, -200), (sx * 70, -120)]), stroke(5))
            c.drawRoundRect(skia.Rect.MakeXYWH(-60, -20, 120, 40), 16, 16, fill(0xFF2A1A3A))
            for j in range(5):
                c.drawPath(path([(-50 + j * 25, -20), (-38 + j * 25, 6), (-26 + j * 25, -20)]), fill(0xFFFFFFFF))
        else:
            c.drawCircle(0, -70, 34, fill(0xFFE8E0F8))
            c.drawCircle(0, -70, 34, stroke(6))
            c.drawCircle(0, -70, 16, fill(PURPLE))
        eyes(c, 0, -60 if kind == "baron" else -110, 12, 0, True)
    else:  # blob (buff monsters)
        b = path([(-80, 50), (-100, -20), (-60, -90), (0, -110), (60, -90), (100, -20), (80, 50)])
        c.drawPath(b, fill(col))
        c.drawPath(b, stroke(7))
        if belly:
            c.drawOval(skia.Rect.MakeXYWH(-45, -30, 90, 70), fill(belly))
        eyes(c, 0, -55, 12, 0, angry)
        c.drawArc(skia.Rect.MakeXYWH(-20, -30, 40, 24), 20, 140, False, stroke(5))
    c.restore()
    if hp < 1:
        w = 150 * s
        c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y - 190 * s, w, 16), 8, 8, fill(0xFF0A1424))
        c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y - 190 * s, w * clamp(hp), 16), 8, 8, fill(0xFFB06CF0))
        c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y - 190 * s, w, 16), 8, 8, stroke(3, GOLD))
    if label:
        M.badge(c, label, x, y + 130 * s, 30, body, 0xFFFFFFFF)


def plated_bar(c, x, y, w, plates_left, k=1.0, flash=-1):
    """Turret health bar split in 5 plates."""
    if k <= 0:
        return
    h = 28
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y, w, h), 8, 8, fill(0xFF0A1424))
    pw = w / 5
    for j in range(5):
        on = j < plates_left
        col = RED if on else 0xFF3A3F48
        if j == flash:
            col = 0xFFFFFFFF
        c.drawRect(skia.Rect.MakeXYWH(x - w / 2 + j * pw + 2, y + 3, pw - 4, h - 6), fill(col))
    for j in range(1, 5):
        c.drawLine(x - w / 2 + j * pw, y, x - w / 2 + j * pw, y + h, stroke(4))
    c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2, y, w, h), 8, 8, stroke(4, GOLD))


def coin_pop(c, x, y, k, amount=None):
    """Gold coin rising and fading (k = seconds since it was earned)."""
    if k <= 0 or k > 1.6:
        return
    a = 1 - max(0, (k - 1) / .6)
    yy = y - 80 * ease(min(1, k))
    c.drawCircle(x, yy, 26, fill(M.alpha(ORO, a)))
    c.drawCircle(x, yy, 26, stroke(5, M.alpha(INK, a)))
    if amount:
        text(c, f"+{amount}", x + 70, yy + 12, M.font("segoeuib.ttf", 40), M.alpha(ORO, a), 8, M.alpha(INK, a))


def xp_bar(c, x, y, w, frac, k=1.0, label=None, color=0xFF9B6CF0):
    if k <= 0:
        return
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, 34), 14, 14, fill(0xEE0A1424))
    c.drawRoundRect(skia.Rect.MakeXYWH(x + 4, y + 4, (w - 8) * clamp(frac), 26), 12, 12, fill(color))
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, 34), 14, 14, stroke(4, GOLD))
    if label:
        text(c, label, x + w / 2, y + 26, M.font("segoeuib.ttf", 24), 0xFFFFFFFF, 6)


def level_badge(c, x, y, lvl, k=1.0, color=GOLD, size=46):
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(back(min(1, k)), back(min(1, k)))
    c.drawCircle(0, 0, size, fill(0xFF1A2230))
    c.drawCircle(0, 0, size, stroke(6, color))
    text(c, str(lvl), 0, size * .38, M.font("segoeuib.ttf", int(size * 1.05)), 0xFFFFFFFF, 6)
    c.restore()


def cd_clock(c, x, y, frac, k=1.0, letter="F", color=0x99FFE27A):
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(back(min(1, k)), back(min(1, k)))
    c.drawCircle(0, 0, 70, fill(0xEE0E1418))
    p = skia.Path()
    p.moveTo(0, 0)
    p.arcTo(skia.Rect.MakeXYWH(-60, -60, 120, 120), -90, 360 * clamp(frac), False)
    p.close()
    c.drawPath(p, fill(color))
    c.drawCircle(0, 0, 70, stroke(6, GOLD))
    text(c, letter, 0, 22, M.font("segoeuib.ttf", 60), 0xFFFFFFFF, 8)
    c.restore()


def stamp(c, s_, k, color=RED, x=540, y=700, size=120):
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(-10)
    sc = 1 + 1.5 * (1 - ease(min(1, k / .6)))
    c.scale(sc, sc)
    a = min(1, k * 2)
    f = M.font("segoeuib.ttf", size)
    w = f.measureText(s_)
    r = skia.Rect.MakeXYWH(-w / 2 - 30, -size * .92, w + 60, size * 1.15)
    c.drawRoundRect(r, 18, 18, stroke(14, M.alpha(color, a)))
    c.drawString(s_, -w / 2, 0, f, fill(M.alpha(color, a)))
    c.restore()


def pizza(c, x, y, r, slices, k=1.0, t=0.0):
    """Chalk-style pizza cut in `slices` (HUD/board)."""
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(back(min(1, k)), back(min(1, k)))
    c.drawCircle(0, 0, r, fill(0xFFF2C062))
    c.drawCircle(0, 0, r * .86, fill(0xFFE8763A))
    for j in range(7):
        a = j * 2.3
        c.drawCircle(math.cos(a) * r * .5, math.sin(a) * r * .5, r * .1, fill(0xFFB02A20))
    for j in range(slices):
        a = j * 2 * math.pi / slices - math.pi / 2
        c.drawLine(0, 0, math.cos(a) * r, math.sin(a) * r, stroke(6))
    c.drawCircle(0, 0, r, stroke(6))
    c.restore()


def map_cam(x, y, z=1.15):
    return (x, y, z)


def cierre_teemo(recap1, recap2, badge_text, extra=None, gag_key="teemo"):
    """Closing classroom scene shared by every class: recap in chalk, the like badge and Teemo getting punched."""
    def fn(c, lt, b):
        M.chalk_line(c, recap1, 540, 400, 64, lt / .5)
        M.chalk_line(c, recap2, 540, 500, 56, (lt - .6) / .5, M.CHALK_Y)
        M.badge(c, badge_text, 540, 650, 40, GOLD, INK, (lt - b.at("like")) / .35, rot=-3)
        if extra:
            extra(c, lt, b)
        M.teemo_punch(c, lt, [b.at(gag_key) + .1], 740, 880, ease((lt - b.at("like")) / .4), b.t0 + lt)
    M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), (gag_key, "feliz")],
             sfx=lambda b: [("tiza", 0), ("tiza", .6), ("ding", b.at("like")), ("puno", b.at(gag_key)), ("teemo_muere", b.at(gag_key) + .3)])(fn)
