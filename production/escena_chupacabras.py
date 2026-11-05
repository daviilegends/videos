"""Sticks, Archivo México: El Chupacabras. One visible action per sentence; positions are in background pixels.
Usage: render_env/Scripts/python.exe escena_chupacabras.py <episode folder> [--stills ...] [--full] [--audio] [--short]"""
from palitos import *

LAYOUT = {
    "granja": dict(light=0xFFB8C4E0, ground=800, house_door=(330, 640), corral=(1050, 700)),
    "corral": dict(light=0xFFD4DCE6, ground=790),
    "plaza": dict(light=0xFFF0D8B4, ground=805),
    "sala": dict(light=0xFFC8D4E8, ground=812, couch=(420, 760), tv=(1040, 380, 1290, 560), window=None),
    "tv": dict(screen=(250, 120, 1150, 720)),
    "monte": dict(light=0xFFAEBCD8, ground=800, thicket=(768, 600)),
    "laboratorio": dict(light=0xFFE6E8EE, ground=810, table=(768, 610), wall_y=330),
}
LAYOUT.update(json.loads((EP / "layout.json").read_text(encoding="utf-8")) if (EP / "layout.json").exists() else {})

FARMER = dict(sombrero=True, jacket=(0xFFE6E0D0, 0xFFBDB6A4), hair=0xFF2A1C14)
WOMAN = dict(jacket=(0xFFB4485A, 0xFF8A3444), hair=0xFF1E1410)
MAN2 = dict(jacket=(0xFF4E6A8C, 0xFF3A5068), hair=0xFF3A2A1E)
KID = dict(jacket=(0xFF6E9A4A, 0xFF557838), hair=0xFF2C1E16)
DOCTOR = dict(jacket=(0xFFF0F0EC, 0xFFCACAC4), hair=0xFF6A6A68)
RED = 0xFFE0302A


# ---------------------------------------------------------------- props drawn on top of the backgrounds
def glow(c, x, y, rx, ry, color, alpha):
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, rx * .9))
    p.setColor(skia.ColorSetARGB(int(alpha * 200), (color >> 16) & 255, (color >> 8) & 255, color & 255))
    c.drawOval(skia.Rect.MakeXYWH(x - rx * 2, y - ry * 2, rx * 4, ry * 4), p)


def eyes(x, y, size=1.0, level=1.0, gap=34):
    """Two red almond eyes glowing in the dark."""
    def draw(c, t, paint):
        if level <= 0:
            return
        blink_k = .15 if (t * .7) % 3.1 < .08 else 1.0
        for side in (-1, 1):
            ex = x + side * gap * size
            glow(c, ex, y, 16 * size, 10 * size, RED, level)
            c.save()
            c.translate(ex, y)
            c.rotate(side * 14)
            c.drawOval(skia.Rect.MakeXYWH(-13 * size, -7 * size * blink_k, 26 * size, 14 * size * blink_k),
                       fill(skia.ColorSetARGB(int(255 * level), 255, 70, 50)))
            c.restore()
    return draw


def goat(c, x, y, s=1.0, lying=False, d=1, marks=False, t=0.0):
    """Cartoon goat. Lying goats rest with closed eyes; `marks` shows the two small dots on the neck."""
    c.save()
    c.translate(x, y)
    c.scale(s * d, s)
    coat, dark = 0xFFE8E2D6, 0xFF9C9284
    if lying:
        body = skia.Rect.MakeXYWH(-85, -62, 170, 62)
        for dx in (-50, -15, 30):
            c.drawLine(dx, -10, dx + 34, -4, stroke(11))
        c.drawOval(body, fill(coat))
        c.drawOval(skia.Rect.MakeXYWH(-40, -58, 50, 26), fill(dark))
        c.drawOval(body, stroke(6))
        hx, hy = 102, -22
        c.drawLine(62, -38, hx - 10, hy - 4, stroke(26))
        c.drawLine(62, -38, hx - 10, hy - 4, stroke(16, coat))
        c.save()
        c.translate(hx, hy)
        c.rotate(18)
        c.drawOval(skia.Rect.MakeXYWH(-26, -17, 58, 32), fill(coat))
        c.drawOval(skia.Rect.MakeXYWH(-26, -17, 58, 32), stroke(5))
        c.drawLine(-4, -4, 10, -6, stroke(4))  # closed eye
        c.drawArc(skia.Rect.MakeXYWH(-22, -44, 26, 34), 200, 120, False, stroke(6, 0xFF5A4E40))
        c.restore()
        if marks:
            for k in (0, 1):
                c.drawCircle(78 + k * 10, -30 + k * 3, 3.2, fill(0xFF8A1E1A))
    else:
        for dx in (-55, -30, 35, 58):
            c.drawLine(dx, -40, dx + math.sin(t * 3 + dx) * 3, 0, stroke(9))
        body = skia.Rect.MakeXYWH(-80, -98, 160, 66)
        c.drawOval(body, fill(coat))
        c.drawOval(body, stroke(6))
        c.drawLine(62, -84, 92, -124, stroke(26))
        c.drawLine(62, -84, 92, -124, stroke(16, coat))
        c.drawOval(skia.Rect.MakeXYWH(80, -148, 56, 34), fill(coat))
        c.drawOval(skia.Rect.MakeXYWH(80, -148, 56, 34), stroke(5))
        c.drawCircle(110, -136, 4, fill(INK))
        c.drawArc(skia.Rect.MakeXYWH(84, -176, 26, 36), 200, 120, False, stroke(6, 0xFF5A4E40))
        c.drawLine(122, -118, 120, -102, stroke(4))  # beard
    c.restore()


def creature(c, x, y, s=1.0, level=1.0, t=0.0):
    """Hunched silhouette with spikes on the back and glowing eyes, the way the reports described it."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    breathe = math.sin(t * 2.2) * 3
    body = poly([(-30, 0), (-44, -60), (-70, -96), (-58, -150 + breathe), (-20, -196 + breathe), (30, -206 + breathe), (62, -180 + breathe),
                 (58, -140), (36, -110), (40, -60), (26, 0), (10, 0), (6, -50), (-12, -48), (-14, 0)])
    paint = fill(skia.ColorSetARGB(int(255 * level), 22, 18, 26))
    c.drawPath(body, paint)
    for k in range(7):  # spikes along the back
        bx, by = lerp(-66, -10, k / 6), lerp(-110, -200, k / 6) + breathe
        c.drawPath(poly([(bx - 10, by + 8), (bx - 26 - k * 2, by - 26), (bx + 8, by)]), paint)
    for side in (-1, 1):  # thin arms with claws
        sx, sy = 40, -150 + breathe
        hx, hy = sx + 40 + side * 6, sy + 50 + side * 10
        c.drawLine(sx, sy, hx, hy, stroke(9, skia.ColorSetARGB(int(255 * level), 22, 18, 26)))
        for k in range(3):
            c.drawLine(hx, hy, hx + 14 + k * 4, hy + 10 - k * 9, stroke(4, skia.ColorSetARGB(int(255 * level), 22, 18, 26)))
    head = skia.Rect.MakeXYWH(14, -262 + breathe, 70, 74)
    c.drawOval(head, paint)
    c.restore()
    eyes(x + 52 * s, y + (-228 + breathe) * s, .8 * s, level, gap=16)(c, t, None)


def coyote(c, x, y, s=1.0, d=1, t=0.0):
    """A thin coyote with mange lying on its side: patches of bare grey-pink skin and a hairless tail."""
    c.save()
    c.translate(x, y)
    c.scale(s * d, s)
    fur, skin = 0xFF8C6E4E, 0xFFC4A098
    breath = 1 + math.sin(t * 2.4) * .02
    for dx in (-70, -40, 50, 80):
        c.drawLine(dx, -20, dx + 40, -2, stroke(8))
    c.drawPath(poly([(-120, -40), (-190, -36), (-200, -30), (-120, -30)]), fill(skin))
    c.drawPath(poly([(-120, -40), (-190, -36), (-200, -30), (-120, -30)]), stroke(4))
    body = skia.Rect.MakeXYWH(-130, -78 * breath, 250, 64 * breath)
    c.drawOval(body, fill(skin))
    c.save()
    c.clipRect(body)
    for px, py, r in ((-90, -60, 26), (-20, -70, 22), (40, -42, 30), (90, -66, 18)):
        c.drawCircle(px, py, r, fill(fur))
    for k in range(18):  # sparse hair
        hx = -110 + k * 13
        c.drawLine(hx, -72, hx + 4, -60, stroke(2, 0xFF5A4430))
    c.restore()
    c.drawOval(body, stroke(6))
    c.drawPath(poly([(110, -66), (196, -48), (208, -38), (150, -30), (106, -34)]), fill(skin))
    c.drawPath(poly([(110, -66), (196, -48), (208, -38), (150, -30), (106, -34)]), stroke(5))
    for ex in (118, 140):
        c.drawPath(poly([(ex, -64), (ex + 8, -102), (ex + 20, -62)]), fill(skin))
        c.drawPath(poly([(ex, -64), (ex + 8, -102), (ex + 20, -62)]), stroke(4))
    c.drawLine(150, -50, 164, -50, stroke(4))  # closed eye
    c.drawCircle(206, -40, 5, fill(INK))
    c.restore()


def bubble(x, y, icon, level=1.0, w=120, h=96):
    """Speech bubble; the icon is '?', '!', 'monstruo', 'matraz' or 'ovni'."""
    def draw(c, t, paint):
        if level <= 0:
            return
        c.save()
        c.translate(x, y)
        c.scale(lerp(.4, 1, ease(level)), lerp(.4, 1, ease(level)))
        a = int(255 * min(1, level * 1.4))
        rect = skia.Rect.MakeXYWH(-w / 2, -h, w, h * .8)
        c.drawPath(poly([(-14, -h * .22), (0, 0), (16, -h * .22)]), fill(skia.ColorSetARGB(a, 250, 248, 240)))
        c.drawRoundRect(rect, 26, 26, fill(skia.ColorSetARGB(a, 250, 248, 240)))
        c.drawRoundRect(rect, 26, 26, stroke(5, skia.ColorSetARGB(a, 11, 11, 13)))
        cx, cy = 0, -h * .6
        if icon in ("?", "!"):
            f = font(58)
            c.drawString(icon, cx - f.measureText(icon) / 2, cy + 22, f, fill(skia.ColorSetARGB(a, 11, 11, 13)))
        elif icon == "monstruo":
            creature(c, cx - 12, cy + 30, .2, level, t)
        elif icon == "matraz":
            c.drawPath(poly([(-10, cy - 28), (10, cy - 28), (10, cy - 8), (28, cy + 24), (-28, cy + 24), (-10, cy - 8)]), fill(0xFF7ED0A8))
            c.drawPath(poly([(-10, cy - 28), (10, cy - 28), (10, cy - 8), (28, cy + 24), (-28, cy + 24), (-10, cy - 8)]), stroke(4))
        elif icon == "ovni":
            c.drawOval(skia.Rect.MakeXYWH(cx - 40, cy - 6, 80, 22), fill(0xFF9AA8B8))
            c.drawOval(skia.Rect.MakeXYWH(cx - 40, cy - 6, 80, 22), stroke(4))
            c.drawArc(skia.Rect.MakeXYWH(cx - 20, cy - 26, 40, 40), 180, 180, True, fill(0xFFB8E4F0))
            c.drawArc(skia.Rect.MakeXYWH(cx - 20, cy - 26, 40, 40), 180, 180, True, stroke(4))
        c.restore()
    return draw


MEXICO = [(.04, .16), (.30, .13), (.40, .24), (.48, .30), (.56, .30), (.60, .46), (.66, .60), (.76, .64), (.84, .56), (.86, .64),
          (.78, .80), (.66, .84), (.56, .78), (.42, .70), (.30, .58), (.22, .44), (.15, .30), (.10, .26), (.14, .48), (.10, .50), (.04, .24)]


def tv_content(kind, k, t):
    """What the television shows, drawn inside the screen rectangle of the 'tv' background."""
    def draw(c, tt, paint):
        x0, y0, x1, y1 = LAYOUT["tv"]["screen"]
        w, h = x1 - x0, y1 - y0
        c.save()
        clip = skia.Path()
        clip.addRoundRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), 40, 40)
        c.clipPath(clip, doAntiAlias=True)
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [0xFF20406A, 0xFF0C1A2E]))
        c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), g)
        P = lambda u, v: (x0 + u * w, y0 + v * h)  # noqa: E731
        if kind == "mapa":
            sea = 0xFF1C3A5E
            c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(sea))
            land = poly([P(u * .82 + .02, v * .8 + .1) for u, v in MEXICO])
            c.drawPath(land, fill(0xFF6E9A5A))
            c.drawPath(land, stroke(5))
            pr = P(.92, .74)
            pulse = .5 + .5 * math.sin(tt * 6)
            c.drawOval(skia.Rect.MakeXYWH(pr[0] - 34, pr[1] - 12, 68, 24), fill(0xFF6E9A5A))
            c.drawOval(skia.Rect.MakeXYWH(pr[0] - 34, pr[1] - 12, 68, 24), stroke(4))
            glow(c, pr[0], pr[1], 30, 20, RED, .6 + .4 * pulse)
            f = font(34)
            c.drawString("PUERTO RICO · 1995", P(.58, .92)[0], P(.58, .92)[1], f, fill(0xFFFFFFFF))
            if k > 0:  # the story travels west
                target = P(.42, .55)
                n = int(ease(k) * 14)
                for j in range(n):
                    q = j / 13
                    px, py = lerp(pr[0], target[0], q), lerp(pr[1], target[1], q) - math.sin(q * math.pi) * 120
                    c.drawCircle(px, py, 6, fill(0xFFF2E21E))
                if k > .6:
                    glow(c, target[0], target[1], 40, 30, RED, .8)
                    c.drawString("MÉXICO · 1996", P(.24, .12)[0], P(.24, .12)[1] + 30, f, fill(0xFFF2E21E))
                if k > .8:
                    for u, v in ((.3, .1), (.88, .3), (.75, .9)):
                        glow(c, *P(u, v), 22, 16, RED, (k - .8) * 5 * (.6 + .4 * math.sin(tt * 5 + u * 9)))
        elif kind == "noticia":
            c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(0xFF14243A))
            creature(c, x0 + w * .5, y0 + h * .82, h / 380, 1.0, tt)
            c.drawRect(skia.Rect.MakeLTRB(x0, y0 + h * .78, x1, y1), fill(0xFFB02420))
            f = font(46)
            c.drawString("ÚLTIMA HORA", x0 + 30, y0 + h * .78 + 56, f, fill(0xFFFFFFFF))
            ticker = "   AVISTAMIENTOS EN TODO EL PAÍS   •   ¿QUÉ ATACA AL GANADO?   •   EL CHUPACABRAS   •"
            fs = font(30)
            off = (tt * 140) % fs.measureText(ticker)
            c.drawRect(skia.Rect.MakeLTRB(x0, y1 - 52, x1, y1), fill(0xFF0B0B0D))
            for rep in range(3):
                c.drawString(ticker, x0 - off + rep * fs.measureText(ticker), y1 - 16, fs, fill(0xFFF2E21E))
        elif kind == "leyenda":
            c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(0xFF2A1840))
            for j in range(16):
                r = random.Random(j)
                sx, sy = x0 + r.random() * w, y0 + r.random() * h
                tw = .5 + .5 * math.sin(tt * 3 + j)
                c.drawCircle(sx, sy, 3 + 3 * tw, fill(skia.ColorSetARGB(int(200 * tw), 242, 226, 30)))
            creature(c, x0 + w * .46, y0 + h * .9, h / 330, 1.0, tt)
        for j in range(0, int(h), 6):  # scanlines
            c.drawLine(x0, y0 + j, x1, y0 + j, stroke(1.5, 0x22000000))
        c.restore()
        glass = skia.Paint(AntiAlias=True)
        glass.setShader(skia.GradientShader.MakeRadial(skia.Point(x0 + w * .3, y0 + h * .25), w * .7,
                                                       [skia.ColorSetARGB(40, 255, 255, 255), skia.ColorSetARGB(0, 255, 255, 255)], [0, 1]))
        c.drawRoundRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), 40, 40, glass)
    return draw


def tv_glow(level):
    """Bluish flicker thrown by the television over the room."""
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT["sala"]["tv"]
        f = .7 + .3 * math.sin(t * 13) * math.sin(t * 7.3)
        glow(c, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * .9, (y1 - y0) * .9, 0xFF6FA8FF, level * f)
        c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(skia.ColorSetARGB(int(110 * level * f), 160, 200, 255)))
    return draw


def newspaper(k):
    """A newspaper spins in toward the camera with the headline of the day."""
    def draw(c, t, paint):
        if k <= 0:
            return
        c.save()
        c.translate(W / 2, H / 2 - 20)
        c.rotate((1 - ease(k)) * 720)
        sc = lerp(.05, 1, ease(k))
        c.scale(sc, sc)
        page = skia.Rect.MakeXYWH(-300, -220, 600, 420)
        c.drawRect(skia.Rect.MakeXYWH(-292, -212, 600, 420), fill(0x66000000))
        c.drawRect(page, fill(0xFFEDE6D2))
        c.drawRect(page, stroke(6))
        c.drawString("EL DIARIO", -110, -175, font(40), fill(INK))
        c.drawLine(-280, -160, 280, -160, stroke(4))
        head = "¿EL CHUPACABRAS?"
        f = font(62)
        c.drawString(head, -f.measureText(head) / 2, -95, f, fill(INK))
        c.drawRect(skia.Rect.MakeXYWH(-270, -70, 250, 230), fill(0xFF3A3A40))
        creature(c, -150, 150, .62, 1.0, 0)
        for j in range(9):
            c.drawLine(10, -50 + j * 24, 270 - (j % 3) * 30, -50 + j * 24, stroke(7, 0xFF8A857A))
        c.restore()
    return draw


def shadow_on_wall(k_monster, x, y):
    """The table lamp throws a monster's shadow on the wall; as the lamp swings it turns into a dog's shadow."""
    def draw(c, t, paint):
        a = k_monster
        c.save()
        c.translate(x, y)
        c.scale(1.4, 1.4)
        p = skia.Paint(AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4))
        if a > 0:
            c.saveLayer(None, skia.Paint(Alphaf=a * .75))
            creature(c, 0, 0, .9, 1.0, t)
            c.restore()
        if a < 1:
            p.setColor(skia.ColorSetARGB(int((1 - a) * 160), 0, 0, 0))
            c.drawOval(skia.Rect.MakeXYWH(-110, -70, 200, 60), p)
            c.drawPath(poly([(80, -66), (150, -50), (156, -40), (80, -30)]), p)
            for ex in (86, 104):
                c.drawPath(poly([(ex, -64), (ex + 7, -96), (ex + 16, -62)]), p)
        c.restore()
    return draw


# ---------------------------------------------------------------- beats
B = {}
B["muertos"] = beat("muertos", cue_start("muertos"))
B["agujeros"] = beat("agujeros", cue_start("agujeros"))
B["sombra"] = beat("sombra", LINES[1]["start"] + (LINES[1]["end"] - LINES[1]["start"]) * .3)
B["ojos_corral"] = beat("ojos_corral", LINES[3]["start"] + 1.2)
B["burbujas"] = beat("burbujas", [LINES[4]["start"] + d for d in (.3, .9, 1.5)])
B["nombre"] = beat("nombre", LINES[5]["start"])
B["flechas"] = beat("flechas", LINES[7]["start"] + .3)
B["criatura"] = beat("criatura", LINES[8]["start"] + .2)
B["ojos_monte"] = beat("ojos_monte", cue_start("ojos"))
B["periodico"] = beat("periodico", LINES[10]["start"] + (LINES[10]["end"] - LINES[10]["start"]) * .45)
B["flashes"] = beat("flashes", [LINES[10]["start"] + (LINES[10]["end"] - LINES[10]["start"]) * f for f in (.25, .32, .38)])
B["noticia"] = beat("noticia", LINES[11]["start"])
B["luz_lab"] = beat("luz_lab", LINES[14]["start"] + .5)
B["revela"] = beat("revela", LINES[15]["start"] + (LINES[15]["end"] - LINES[15]["start"]) * .45)
B["ojos_final"] = beat("ojos_final", LINES[20]["start"] + (LINES[20]["end"] - LINES[20]["start"]) * .6)


def person(base, appearance, **kw):
    d = dict(base)
    d.update(appearance)
    d.update(kw)
    return d


def shots(t):
    i, lt, k = linea(t)
    base = dict(t=t, blink=blink(t))
    g = LAYOUT
    out = dict(bg="granja")
    if i == 0:
        if t < B["muertos"]:  # sale al corral
            out["bg"] = "granja"
            kk = (t - 0) / max(.1, B["muertos"])
            x0, y0 = g["granja"]["house_door"]
            out["cam"] = Cam((600, 470, 1.25), (820, 500, 1.4), kk)
            out["char"] = person(base, FARMER, x=lerp(x0, 900, ease(kk)), y=g["granja"]["ground"], scale=.9, walk=t * 6, face=.5, look=(.8, 0))
        elif t < B["agujeros"]:  # los animales en el suelo
            out["bg"] = "corral"
            kk = (t - B["muertos"]) / max(.1, B["agujeros"] - B["muertos"])
            out["cam"] = Cam((768, 560, 1.2), (768, 600, 1.45), kk)
            out["over"] = [lambda c, tt, p: [goat(c, 560 + j * 230, g["corral"]["ground"] - 10 + (j % 2) * 18, .9, True, 1 if j % 2 else -1) for j in range(3)]]
            out["char"] = person(base, FARMER, x=1180, y=g["corral"]["ground"] + 20, scale=1.0, face=-.6, look=(-.8, .4), eye=1.3, brow=-1, mouth="gasp", arm_l=(.8, .6), arm_r=(.8, .6))
        else:  # close-up: two small marks on the neck
            out["bg"] = "corral"
            kk = (t - B["agujeros"]) / max(.1, LINES[1]["start"] - B["agujeros"])
            gx, gy = 790, g["corral"]["ground"] - 10
            out["cam"] = Cam((gx + 70, gy - 40, 2.6), (gx + 80, gy - 36, 3.2), kk)
            out["over"] = [lambda c, tt, p: goat(c, gx, gy, .9, True, 1, marks=True)]
            out["dark"] = .1
    elif i == 1:  # noventa... ciencia ficción: a shape crosses the moonlit farm
        out["bg"] = "granja"
        out["cam"] = Cam((768, 470, 1.35), (768, 432, 1.0), k)
        out["dark"] = .25
        ks = (t - B["sombra"]) / 2.2
        if 0 <= ks <= 1:
            out["over"] = [lambda c, tt, p: creature(c, lerp(1500, 60, ks), g["granja"]["ground"] - 90 - math.sin(ks * math.pi) * 40, .55, .95, tt)]
    elif i == 2:  # en distintas comunidades: neighbors around the animals at dawn
        out["bg"] = "corral"
        out["cam"] = Cam((620, 560, 1.15), (900, 560, 1.25), k)
        out["over"] = [lambda c, tt, p: [goat(c, 520 + j * 260, g["corral"]["ground"] - 8 + (j % 2) * 20, .85, True, 1 if j % 2 else -1) for j in range(3)]]
        gy = g["corral"]["ground"] + 26
        out["chars"] = [person(base, FARMER, x=420, y=gy, scale=1.0, face=.5, look=(.7, .5), brow=-.8, mouth="worry"),
                        person(base, WOMAN, x=1180, y=gy + 6, scale=.98, face=-.5, look=(-.6, .5), brow=-.8, mouth="flat", arm_r=(2.1, .9), blink=blink(t, .7)),
                        person(base, MAN2, x=1360, y=gy - 4, scale=.95, face=-.6, look=(-.9, .3), brow=-.5, mouth="o", blink=blink(t, 1.9))]
    elif i == 3:  # heridas extrañas, algo los atacó de noche: eyes behind the fence
        out["bg"] = "corral"
        out["cam"] = Cam((768, 520, 1.3), (768, 500, 1.6), k)
        out["dark"] = .55
        out["flicker"] = 0
        level = ease((t - B["ojos_corral"]) / .6) * (1 - ease((k - .85) / .15))
        out["over"] = [lambda c, tt, p: goat(c, 520, g["corral"]["ground"] - 20, .8, False, 1, t=tt),
                       lambda c, tt, p: goat(c, 1000, g["corral"]["ground"] - 10, .8, False, -1, t=tt + 1),
                       eyes(768, 450, 1.1, level)]
    elif i == 4:  # un nombre que todos repetían: whispers across the square
        out["bg"] = "plaza"
        out["cam"] = Cam((768, 520, 1.15), (768, 560, 1.4), k)
        gy = g["plaza"]["ground"]
        xs = (460, 680, 880, 1090)
        looks = (FARMER, WOMAN, MAN2, KID)
        out["chars"] = [person(base, looks[j], x=xs[j], y=gy, scale=.9 if j < 3 else .7, face=(.5 if j % 2 == 0 else -.5), look=((.7 if j % 2 == 0 else -.7), 0),
                               mouth=talk(t + j) if int(t * 2 + j) % 3 == 0 else "flat", blink=blink(t, j * .8)) for j in range(4)]
        out["over"] = [bubble(xs[j] + (40 if j % 2 == 0 else -40), gy - 300, "?" if j != 2 else "!", ease((t - B["burbujas"][min(j, 2)]) / .35)) for j in range(3)]
    elif i == 5:  # El Chupacabras.
        out["bg"] = "plaza"
        hit = math.exp(-(t - B["nombre"]) * 3)
        out["cam"] = Cam((768, 560, 1.4), (768, 560, 1.7), k)
        out["shake"] = (random.Random(int(t * FPS)).uniform(-1, 1) * hit * 18, random.Random(int(t * FPS) + 9).uniform(-1, 1) * hit * 12)
        out["dark"] = .9 if lt < .07 else .25
        gy = g["plaza"]["ground"]
        out["chars"] = [person(base, look, x=x, y=gy, scale=.9, eye=1.35, brow=-1, mouth="gasp", look=(0, -.3), arm_l=(1.2, .6), arm_r=(1.2, .6), blink=0)
                        for x, look in ((560, FARMER), (768, WOMAN), (980, MAN2))]
        out["caption"] = "EL CHUPACABRAS"
    elif i in (6, 7):  # Puerto Rico, then México and other countries, on the TV map
        out["bg"] = "tv"
        out["cam"] = Cam((750, 470, 1.0), (750, 470, 1.12), k)
        out["over"] = [tv_content("mapa", 0 if i == 6 else min(1, (t - B["flechas"]) / 2.2), t)]
    elif i in (8, 9):  # the description: the silhouette rises from the thicket
        out["bg"] = "monte"
        tx, ty = g["monte"]["thicket"]
        rise = ease((t - B["criatura"]) / 1.6)
        out["cam"] = Cam((tx, ty - 60, 1.4), (tx, ty - 120, 1.9), (t - LINES[8]["start"]) / (LINES[10]["start"] - LINES[8]["start"]))
        out["dark"] = .3
        out["flicker"] = 0
        out["over"] = [lambda c, tt, p: creature(c, tx, ty + lerp(220, 0, rise), 1.0, 1.0, tt)]
        if i == 9:
            out["dark"] = .45
    elif i == 10:  # TV and newspapers: the family watches, flashes, then the paper spins in
        out["bg"] = "sala"
        cx, cy = g["sala"]["couch"]
        out["cam"] = Cam((560, 470, 1.1), (640, 460, 1.22), k)
        out["dark"] = .2
        out["over"] = [tv_glow(1.0)]
        out["chars"] = [person(base, MAN2, x=cx - 60, y=cy, scale=.85, sit=True, face=.6, look=(1, -.2), mouth="o", eye=1.15),
                        person(base, KID, x=cx + 90, y=cy + 6, scale=.7, sit=True, face=.6, look=(1, -.3), mouth="gasp", eye=1.3, blink=blink(t, 1.1))]
        flash = max((math.exp(-(t - f) * 14) for f in B["flashes"] if t >= f), default=0)
        out["dark"] = max(0, .2 - flash)
        out["hud"] = [newspaper(min(1, (t - B["periodico"]) / .8))]
    elif i == 11:  # fenómeno nacional: breaking news
        out["bg"] = "tv"
        out["cam"] = Cam((750, 470, 1.05), (750, 470, 1.15), k)
        out["over"] = [tv_content("noticia", k, t)]
    elif i in (12, 13):  # some saw it, others: a secret experiment
        out["bg"] = "plaza"
        gy = g["plaza"]["ground"]
        out["cam"] = Cam((700, 540, 1.3), (840, 540, 1.4), k)
        point = ease(lt / .5)
        out["chars"] = [person(base, FARMER, x=560, y=gy, scale=.95, face=.5, look=(.6, -.6), mouth=talk(t) if i == 12 else "flat", eye=1.25, brow=.4,
                               arm_r=(lerp(.1, 2.6, point) if i == 12 else .1, .1)),
                        person(base, WOMAN, x=820, y=gy, scale=.92, face=-.4, look=(-.6, 0), mouth=talk(t) if i == 13 else "flat", blink=blink(t, .5)),
                        person(base, MAN2, x=1040, y=gy, scale=.94, face=-.5, look=(-.7, 0), mouth="flat", brow=-.3, blink=blink(t, 1.4))]
        if i == 12:
            out["over"] = [bubble(640, gy - 330, "monstruo", ease(lt / .4), w=170, h=140)]
        else:
            out["over"] = [bubble(760, gy - 320, "matraz", ease(lt / .4)), bubble(980, gy - 320, "ovni", ease((lt - .6) / .4))]
    elif i in (14, 15, 16):  # the lab: lights on, the monster's shadow becomes a sick coyote
        out["bg"] = "laboratorio"
        tx, ty = g["laboratorio"]["table"]
        on = ease((t - B["luz_lab"]) / .25)
        out["dark"] = lerp(.75, .05, on) if i == 14 else .05
        out["flicker"] = .4 if i == 14 else 0
        reveal = ease((t - B["revela"]) / 1.4)
        if i == 14:
            out["cam"] = Cam((768, 470, 1.0), (768, 470, 1.15), k)
            out["over"] = [shadow_on_wall(1.0, tx - 250, g["laboratorio"]["wall_y"] + 140)]
            out["char"] = person(base, DOCTOR, x=lerp(160, 470, ease(k)), y=g["laboratorio"]["ground"], scale=.95, walk=t * 6 if k < .9 else None, face=.6, look=(.8, -.3), mouth="flat")
        elif i == 15:
            out["cam"] = Cam((768, 470, 1.15), (tx, ty - 40, 1.6), k)
            out["over"] = [shadow_on_wall(1 - reveal, tx - 250, g["laboratorio"]["wall_y"] + 140),
                           lambda c, tt, p: coyote(c, tx, ty, .9, 1, tt) if reveal > 0 else None]
            out["char"] = person(base, DOCTOR, x=470, y=g["laboratorio"]["ground"], scale=.95, face=.6, look=(.8, -.4), mouth="o" if reveal > .3 else "flat", eye=1.1,
                                 arm_r=(2.0 * reveal, .2))
        else:
            out["cam"] = Cam((tx + 20, ty - 50, 2.1), (tx + 60, ty - 50, 2.5), k)
            out["over"] = [lambda c, tt, p: coyote(c, tx, ty, .9, 1, tt)]
    elif i == 17:  # never confirmed: the thicket is empty, the eyes are gone
        out["bg"] = "monte"
        tx, ty = g["monte"]["thicket"]
        out["cam"] = Cam((tx, ty - 120, 1.9), (768, 432, 1.0), k)
        out["dark"] = .35
        out["flicker"] = 0
        out["over"] = [eyes(tx, ty - 40, 1.0, 1 - ease(k / .3))]
    elif i in (18, 19):  # a legend of popular culture
        if i == 18:
            out["bg"] = "sala"
            cx, cy = g["sala"]["couch"]
            out["cam"] = Cam((640, 460, 1.22), (700, 450, 1.05), k)
            out["over"] = [tv_glow(.8)]
            out["chars"] = [person(base, MAN2, x=cx - 60, y=cy, scale=.85, sit=True, face=.6, look=(1, -.2), mouth="flat"),
                            person(base, KID, x=cx + 90, y=cy + 6, scale=.7, sit=True, face=.6, look=(1, -.3), mouth=talk(t), blink=blink(t, 1.1))]
        else:
            out["bg"] = "tv"
            out["cam"] = Cam((750, 470, 1.15), (750, 470, 1.0), k)
            out["over"] = [tv_content("leyenda", k, t)]
    else:  # ¿Tú recuerdas...? the kid turns to us; behind, two red eyes at the window
        out["bg"] = "sala"
        cx, cy = g["sala"]["couch"]
        out["cam"] = Cam((cx + 60, cy - 220, 1.7), (cx + 80, cy - 230, 1.95), k)
        out["over"] = [tv_glow(.8)]
        out["char"] = person(base, KID, x=cx + 90, y=cy + 6, scale=.7, sit=True, face=0, look=(0, 0), mouth=talk(t) if k < .55 else "flat", brow=.2)
        win = g["sala"].get("window")
        if win:
            out["over"].append(eyes(win[0], win[1], .7, ease((t - B["ojos_final"]) / .5)))
        else:
            out["over"].append(eyes(cx + 520, cy - 360, .7, ease((t - B["ojos_final"]) / .5)))
    return out


terminar(shots, LAYOUT, "chupacabras")
