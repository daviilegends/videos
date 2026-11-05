"""Original teacher character for the League academy, in the Sticks style (round head, ink dot eyes, stick limbs).
profesora(c, x, y, scale, t, pose, look): origin between the feet. pose keys: expr (see EXPRS), hand_l / hand_r
(local targets), point_l / point_r, pointer_l / pointer_r, bend_r, front_l, talk (0..1), blink (0..1), tilt, lean, look."""
import math

import skia

INK = 0xFF1E2228
SKIN, SHADE, BLUSH = 0xFFF6D2B8, 0xFFE6B89C, 0x55F07A7A
LIPS, LIPS_D = 0xFFD62839, 0xFF9E1626
BOLD = "C:/Windows/Fonts/segoeuib.ttf"

LOOKS = {
    "A": dict(hair=0xFF4A2E22, hair_d=0xFF33201A, style="bun", blazer=0xFF27406B, blazer_d=0xFF1C3052, blouse=0xFFF7F3EA,
              skirt=0xFF7A1E2E, shoes=0xFFD62839, frames=0xFF1E2228),
    "B": dict(hair=0xFFB4472A, hair_d=0xFF84321D, style="long", blazer=0xFF1F5E5B, blazer_d=0xFF164644, blouse=0xFFF7F3EA,
              skirt=0xFF1E2430, shoes=0xFF1E2430, frames=0xFFC0283A),
    "C": dict(hair=0xFF1A1A22, hair_d=0xFF3A3A48, style="pony", blazer=0xFF6B2340, blazer_d=0xFF511A30, blouse=0xFFFFF4D6,
              skirt=0xFF22283A, shoes=0xFFD62839, frames=0xFFE0B040),
}

EXPRS = {  # eye size, top lid, brow raise (left, right), mouth, extras
    "neutral": dict(eye=1.0, lid=0, brows=(0, 0), mouth="smile", smile=.6),
    "explica": dict(eye=1.0, lid=0, brows=(.3, .3), mouth="smile", smile=.8),
    "guino": dict(eye=1.0, lid=0, brows=(.5, -.2), mouth="smirk", smile=1, wink=True, fx="brillo"),
    "piensa": dict(eye=.9, lid=.3, brows=(.7, -.3), mouth="pout", look=(-.6, -.8), fx="burbuja"),
    "asombro": dict(eye=1.45, lid=0, brows=(1.4, 1.4), mouth="O", fx="exclama"),
    "feliz": dict(eye=1.0, lid=0, brows=(.6, .6), mouth="grin", happy=True, fx="corazon"),
    "picara": dict(eye=1.0, lid=.45, brows=(-.2, .9), mouth="smirk", smile=.9),
}


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def stroke(w, color=INK):
    return skia.Paint(AntiAlias=True, Color=color, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def poly(points, close=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def shape(c, p, color, w=6):
    c.drawPath(p, fill(color))
    c.drawPath(p, stroke(w))


_FONTS = {}


def bold(size):
    if size not in _FONTS:
        _FONTS[size] = skia.Font(skia.Typeface.MakeFromFile(BOLD), size)
    return _FONTS[size]


def ik(sh, target, l1, l2, bend):
    dx, dy = target[0] - sh[0], target[1] - sh[1]
    d = max(1e-3, min(l1 + l2 - .5, math.hypot(dx, dy)))
    a = math.atan2(dy, dx)
    b = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))) * bend
    return (sh[0] + l1 * math.cos(a + b), sh[1] + l1 * math.sin(a + b)), (sh[0] + d * math.cos(a), sh[1] + d * math.sin(a))


def arm(c, sh, target, bend, look, point=False, pointer=False):
    el, hd = ik(sh, target, 50, 48, bend)
    c.drawLine(*sh, *el, stroke(15, INK))  # blazer sleeve on the upper arm
    c.drawLine(*sh, *el, stroke(8, look["blazer"]))
    c.drawLine(*el, *hd, stroke(9))
    ang = math.atan2(hd[1] - el[1], hd[0] - el[0])
    if pointer:
        tip = (hd[0] + math.cos(ang) * 120, hd[1] + math.sin(ang) * 120)
        c.drawLine(*hd, *tip, stroke(9, INK))
        c.drawLine(*hd, *tip, stroke(4, 0xFFC08A4A))
        c.drawCircle(*tip, 5, fill(0xFFF3EFE2))
    if point:
        c.drawLine(*hd, hd[0] + math.cos(ang) * 16, hd[1] + math.sin(ang) * 16, stroke(6))
    c.drawCircle(*hd, 8, fill(INK))
    return hd


def hair_back(c, look, r, t):
    st = look["style"]
    if st == "long":
        p = skia.Path()
        p.moveTo(-r - 4, -10)
        p.cubicTo(-r - 20, 60, -r - 6, 100, -r + 10, 128)
        for j in range(5):
            x0 = -r + 10 + j * (2 * r - 20) / 4
            p.quadTo(x0 + 12, 148 + math.sin(t * 2 + j) * 3, x0 + (2 * r - 20) / 8, 128)
        p.lineTo(r - 10, 128)
        p.cubicTo(r + 6, 100, r + 20, 60, r + 4, -10)
        p.close()
        shape(c, p, look["hair"])
    if st == "pony":  # high ponytail swinging behind
        sw = math.sin(t * 2.4) * 6
        p = skia.Path()
        p.moveTo(r - 30, -r + 8)
        p.cubicTo(r + 40, -r - 10, r + 70 + sw, 20, r + 30 + sw, 90)
        p.cubicTo(r + 40 + sw, 30, r + 10, -20, r - 18, -r + 30)
        p.close()
        shape(c, p, look["hair"])
        c.drawPath(poly([(r + 10, -r + 10), (r + 46 + sw * .5, 0), (r + 40 + sw, 60)], close=False), stroke(3.5, look["hair_d"]))


def star(c, x, y, r, color):
    pts = []
    for j in range(8):
        rr = r if j % 2 == 0 else r * .35
        a = math.pi / 4 * j - math.pi / 2
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    shape(c, poly(pts), color, 3)


def heart(c, x, y, r, color):
    p = skia.Path()
    p.moveTo(x, y + r)
    p.cubicTo(x - r * 2, y - r * .2, x - r * .8, y - r * 1.6, x, y - r * .5)
    p.cubicTo(x + r * .8, y - r * 1.6, x + r * 2, y - r * .2, x, y + r)
    shape(c, p, color, 3.5)


def mouth(c, e, talk):
    my = 36
    kind = e["mouth"]
    if talk > .1 or kind == "O":
        # open mouth follows the voice: taller and a bit wider when louder; "O" (surprise) stays round
        h = 6 + 30 * talk if kind != "O" else 18 + 14 * talk
        w = 22 + 10 * talk if kind != "O" else 20 + 4 * talk
        r = skia.Rect.MakeXYWH(-w / 2, my - h * .4, w, h)
        c.drawOval(r, fill(0xFF5A1418))
        c.save()
        c.clipPath(skia.Path.Oval(r), doAntiAlias=True)
        c.drawRect(skia.Rect.MakeXYWH(-w / 2, my - h * .4, w, min(6, h * .25)), fill(0xFFFFFFFF))  # upper teeth
        c.drawOval(skia.Rect.MakeXYWH(-w * .35, my + h * .3, w * .7, h * .45), fill(0xFFD8606A))  # tongue
        c.restore()
        c.drawOval(r, stroke(5, LIPS))
        return
    if kind == "grin":
        p = skia.Path()
        p.moveTo(-18, my - 4)
        p.quadTo(0, my - 1, 18, my - 4)
        p.quadTo(0, my + 22, -18, my - 4)
        p.close()
        c.drawPath(p, fill(0xFF5A1418))
        c.save()
        c.clipPath(p, doAntiAlias=True)
        c.drawRect(skia.Rect.MakeXYWH(-16, my - 6, 32, 8), fill(0xFFFFFFFF))
        c.restore()
        c.drawPath(p, stroke(5, LIPS))
        return
    c.save()
    if kind == "pout":
        c.translate(-6, 2)
        c.scale(.72, .9)
    elif kind == "smirk":
        c.translate(0, my)
        c.rotate(-9)
        c.translate(0, -my)
    smile = e.get("smile", .5)
    up = skia.Path()
    up.moveTo(-15, my + 1 - smile * 3)
    up.quadTo(-8, my - 7, 0, my - 3)
    up.quadTo(8, my - 7, 15, my + 1 - smile * 3)
    up.quadTo(0, my + 3, -15, my + 1 - smile * 3)
    lo = skia.Path()
    lo.moveTo(-14, my + 1 - smile * 3)
    lo.quadTo(0, my + 3, 14, my + 1 - smile * 3)
    lo.quadTo(0, my + 14 + smile * 2, -14, my + 1 - smile * 3)
    for pth in (lo, up):
        c.drawPath(pth, fill(LIPS))
        c.drawPath(pth, stroke(2.5, LIPS_D))
    c.restore()


def face(c, look, s, t):
    e = dict(EXPRS[s.get("expr", "neutral")])
    e.update({k: s[k] for k in ("look", "smile") if k in s})
    lx, ly = e.get("look", (0, 0))
    blink = s.get("blink", 0)
    for sx in (-1, 1):
        c.drawOval(skia.Rect.MakeXYWH(sx * 34 - 12, 14, 24, 13), fill(0x88F07A7A if e.get("happy") else BLUSH))
    for j, ex in enumerate((-23, 23)):
        side = -1 if j == 0 else 1
        cx, cy = ex + lx * 6, -2 + ly * 4
        sz = e["eye"]
        closed = 1.0 if (e.get("wink") and j == 1) else blink
        if e.get("happy"):
            p = skia.Path()
            p.moveTo(cx - 10, cy + 4)
            p.quadTo(cx, cy - 10, cx + 10, cy + 4)
            c.drawPath(p, stroke(5))
            top = cy - 4
        elif closed > .6:
            p = skia.Path()
            p.moveTo(cx - 10, cy)
            p.quadTo(cx, cy + 8, cx + 10, cy)
            c.drawPath(p, stroke(5))
            top = cy + 1
        else:
            h = 18 * sz * (1 - closed) * (1 - e["lid"] * .45)
            rect = skia.Rect.MakeXYWH(cx - 6.5 * sz, cy + 9 * sz - h, 13 * sz, max(3, h))
            if sz > 1.2:  # surprised: whites around a small pupil
                big = rect.makeOutset(4, 4)
                c.drawOval(big, fill(0xFFFFFFFF))
                c.drawOval(big, stroke(3.5))
                c.drawCircle(rect.centerX(), rect.centerY(), 5.5, fill(INK))
                top = big.top()
            else:
                c.drawOval(rect, fill(INK))
                c.drawCircle(cx + 2, rect.top() + 5, 2.5, fill(0xFFFFFFFF))
                if e["lid"] > 0:
                    c.drawLine(cx - 9, rect.top(), cx + 9, rect.top(), stroke(4.5))
                top = rect.top()
        for k in range(3):  # lashes flick outward
            a = math.radians(-60 - k * 22) if side > 0 else math.radians(-120 + k * 22)
            bx = cx + side * (4 + k * 2.5)
            c.drawLine(bx, top + 1, bx + math.cos(a) * 10, top + 1 + math.sin(a) * 10, stroke(3))
    bl, br = e["brows"]
    c.drawLine(-36, -26 - bl * 7, -14, -29 - bl * 9, stroke(4))
    c.drawLine(14, -29 - br * 9, 36, -26 - br * 7, stroke(4))
    fr = look["frames"]
    for sx in (-1, 1):  # cat-eye glasses
        g = skia.Path()
        cx = sx * 23
        g.moveTo(cx - sx * 18, -12)
        g.quadTo(cx - sx * 20, 14, cx, 15)
        g.quadTo(cx + sx * 20, 14, cx + sx * 22, -6)
        g.lineTo(cx + sx * 27, -20)
        g.quadTo(cx, -18, cx - sx * 18, -12)
        g.close()
        c.drawPath(g, fill(0x33BFE4FF))
        c.drawPath(g, stroke(9, INK))
        c.drawPath(g, stroke(5, fr))
    c.drawLine(-6, -10, 6, -10, stroke(5, fr))
    mouth(c, e, s.get("talk", 0))
    fx = e.get("fx")
    if fx == "brillo":
        k = 1 + .2 * math.sin(t * 8)
        star(c, 62, -40, 13 * k, 0xFFF2D35A)
        star(c, 78, -12, 7 * k, 0xFFFFFFFF)
    elif fx == "burbuja":
        bob = math.sin(t * 2) * 4
        for bx, by, rr in ((58, -58, 6), (72, -76, 9)):
            c.drawCircle(bx, by + bob, rr, fill(0xFFFFFFFF))
            c.drawCircle(bx, by + bob, rr, stroke(3.5))
        r = skia.Rect.MakeXYWH(66, -150 + bob, 84, 64)
        c.drawOval(r, fill(0xFFFFFFFF))
        c.drawOval(r, stroke(4.5))
        c.drawString("?", 95, -100 + bob, bold(46), fill(INK))
    elif fx == "exclama":
        c.drawString("!", 74, -66, bold(64), stroke(8))
        c.drawString("!", 74, -66, bold(64), fill(0xFFF2D35A))
        for a in (-150, -125, -55, -30):
            r0 = 84 + 4 * math.sin(t * 20)
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            c.drawLine(ca * r0, sa * r0, ca * (r0 + 22), sa * (r0 + 22), stroke(5))
    elif fx == "corazon":
        heart(c, 72, -66 + math.sin(t * 3) * 4, 14, 0xFFE8475A)


def head(c, look, s, t):
    r = 66
    c.save()
    c.rotate(s.get("tilt", 0) + math.sin(t * 1.6) * 1.5)
    if look["style"] == "bun":
        c.drawLine(-44, -r - 46, 44, -r - 6, stroke(13, INK))
        c.drawLine(-44, -r - 46, 44, -r - 6, stroke(7, 0xFFF2C440))
        shape(c, skia.Path.Circle(0, -r - 18, 32), look["hair"])
    for sx in (-1, 1):  # small gold earrings
        c.drawCircle(sx * (r - 4), 22, 6, fill(0xFFF0C64E))
        c.drawCircle(sx * (r - 4), 22, 6, stroke(3))
    c.drawCircle(0, 0, r, fill(SKIN))
    c.save()
    c.clipPath(skia.Path.Circle(0, 0, r), doAntiAlias=True)
    c.drawCircle(-16, -8, r + 3, fill(SHADE))
    c.drawCircle(-8, -6, r - 4, fill(SKIN))
    c.restore()
    c.drawCircle(0, 0, r, stroke(6))
    bang = skia.Path()  # side-swept bangs
    bang.moveTo(-r - 3, 4)
    bang.cubicTo(-r - 6, -60, -20, -r - 14, 20, -r - 4)
    bang.cubicTo(52, -r + 6, r + 6, -40, r + 3, 6)
    bang.cubicTo(r - 10, -24, 40, -40, 6, -30)
    bang.cubicTo(-14, -26, -40, -28, -52, -6)
    bang.cubicTo(-58, 4, -62, 10, -r - 3, 4)
    bang.close()
    shape(c, bang, look["hair"])
    c.drawPath(poly([(-30, -46), (4, -56), (34, -44)], close=False), stroke(4, look["hair_d"]))
    face(c, look, s, t)
    c.restore()


def profesora(c, x, y, scale, t, pose, look):
    c.save()
    c.translate(x, y)
    c.scale(scale * pose.get("dir", 1), scale)
    c.rotate(pose.get("lean", 0))
    breath = math.sin(t * 1.8) * 1.5
    sway = math.sin(t * 1.1) * 2  # weight shift on the hips
    hem, waist, sh_y = -58, -150 + breath * .2, -194 + breath
    c.save()  # hair that hangs behind the body
    c.translate(0, sh_y - 64)
    c.rotate(pose.get("tilt", 0) + math.sin(t * 1.6) * 1.5)
    hair_back(c, look, 66, t)
    c.restore()
    for side, kx in ((-1, 2), (1, -4)):  # legs and heels, relaxed contrapposto
        hip = (side * 14 + sway, hem + 2)
        foot = (side * 17 + (6 if side > 0 else 0), -10)
        knee = (hip[0] + kx, (hip[1] + foot[1]) / 2)
        c.drawLine(*hip, *knee, stroke(9))
        c.drawLine(*knee, *foot, stroke(9))
        shoe = poly([(foot[0] - 6, foot[1] - 4), (foot[0] + 20, foot[1] + 6), (foot[0] + 20, foot[1] + 10), (foot[0] - 2, foot[1] + 10)])
        shape(c, shoe, look["shoes"], 4)
        c.drawLine(foot[0] - 4, foot[1] + 2, foot[0] - 6, foot[1] + 12, stroke(5))
    sk = skia.Path()  # pencil skirt: round hips from a narrow waist, tapering to the knee
    sk.moveTo(-17 + sway * .3, waist)
    sk.cubicTo(-40 + sway, waist + 12, -52 + sway, waist + 40, -46 + sway, waist + 58)
    sk.cubicTo(-42 + sway, hem - 14, -36 + sway, hem - 4, -32 + sway, hem)
    sk.lineTo(32 + sway, hem)
    sk.cubicTo(36 + sway, hem - 4, 42 + sway, hem - 14, 46 + sway, waist + 58)
    sk.cubicTo(52 + sway, waist + 40, 40 + sway, waist + 12, 17 + sway * .3, waist)
    sk.close()
    shape(c, sk, look["skirt"])
    c.drawLine(12 + sway, hem - 18, 14 + sway, hem, stroke(3))
    sh_l, sh_r = (-27, sh_y + 6), (27, sh_y + 6)
    hl, hr = pose.get("hand_l", (-44, -112)), pose.get("hand_r", (44, -112))
    if not pose.get("front_l"):
        arm(c, sh_l, hl, pose.get("bend_l", 1), look, pose.get("point_l"), pose.get("pointer_l"))
    bz = skia.Path()  # fitted blazer: fuller bust line, cinched waist, peplum over the hips
    bz.moveTo(-28, sh_y)
    bz.quadTo(0, sh_y - 8, 28, sh_y)
    bz.cubicTo(40, sh_y + 14, 40, sh_y + 34, 30, sh_y + 40)
    bz.cubicTo(20, waist - 14, 15, waist - 4, 16, waist)
    bz.quadTo(24, waist + 8, 26, waist + 14)
    bz.quadTo(0, waist + 20, -26, waist + 14)
    bz.quadTo(-24, waist + 8, -16, waist)
    bz.cubicTo(-15, waist - 4, -20, waist - 14, -30, sh_y + 40)
    bz.cubicTo(-40, sh_y + 34, -40, sh_y + 14, -28, sh_y)
    bz.close()
    c.drawPath(bz, fill(look["blazer"]))
    c.save()
    c.clipPath(bz, doAntiAlias=True)
    c.drawRect(skia.Rect.MakeLTRB(-60, sh_y - 10, -14, waist + 40), fill(look["blazer_d"]))
    c.restore()
    c.drawPath(bz, stroke(6))
    v = poly([(-14, sh_y - 3), (0, sh_y + 30), (14, sh_y - 3)])  # blouse V and lapels
    shape(c, v, look["blouse"], 4)
    for sx in (-1, 1):
        c.drawPath(poly([(sx * 14, sh_y - 3), (sx * 24, sh_y + 16), (sx * 4, sh_y + 34)], close=False), stroke(4))
    c.drawLine(-16, waist, 16, waist, stroke(5))  # thin belt
    c.drawCircle(0, waist + 8, 4, fill(0xFFF0C64E))
    c.drawLine(0, sh_y - 12, 0, sh_y - 2, stroke(9))  # neck
    if pose.get("front_l"):
        arm(c, sh_l, hl, pose.get("bend_l", 1), look, pose.get("point_l"), pose.get("pointer_l"))
    c.save()
    c.translate(0, sh_y - 64)
    head(c, look, pose, t)
    c.restore()
    arm(c, sh_r, hr, pose.get("bend_r", -1), look, pose.get("point_r"), pose.get("pointer_r"))
    c.restore()


POSES = {
    "neutral": dict(expr="neutral", hand_l=(-46, -112), hand_r=(46, -112)),
    "explica": dict(expr="explica", hand_l=(-46, -112), hand_r=(116, -236), bend_r=1, point_r=True, talk=.7, tilt=-5),
    "guino": dict(expr="guino", hand_l=(-46, -112), hand_r=(96, -262), bend_r=1, point_r=True, tilt=-6, lean=-2),
    "piensa": dict(expr="piensa", hand_l=(-30, -150), hand_r=(12, -196), front_l=True, tilt=8),
    "asombro": dict(expr="asombro", hand_l=(-92, -240), hand_r=(92, -240), bend_l=-1, bend_r=1),
    "feliz": dict(expr="feliz", hand_l=(-100, -262), hand_r=(100, -262), bend_l=-1, bend_r=1, tilt=4),
    "picara": dict(expr="picara", hand_l=(-46, -112), hand_r=(112, -150), bend_r=1, pointer_r=True, lean=-3, tilt=-4),
    "puntero": dict(expr="explica", hand_l=(-46, -112), hand_r=(112, -150), bend_r=1, pointer_r=True, talk=.4),
}

if __name__ == "__main__":
    import sys
    W, H = 1600, 1080
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(0xFFEFE6D8)
    for j, (name, pose) in enumerate(POSES.items()):
        x, y = 200 + (j % 4) * 400, 500 + (j // 4) * 530
        profesora(c, x, y, 1.3, 0.4 + j, pose, LOOKS["C"])
        c.drawString(name, x - bold(30).measureText(name) / 2, y + 42, bold(30), fill(0xFF555555))
    surf.makeImageSnapshot().save(sys.argv[1])
