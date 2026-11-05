"""Sticks, Archivo México: el caso de la Mataviejitas. Serious chronicle: no victims and no violence on screen,
only places, documents, silhouettes and the investigation. Positions are in background pixels.
Usage: render_env/Scripts/python.exe escena_mataviejitas.py <episode folder> [--stills ...] [--full] [--audio] [--short]"""
from palitos import *

LAYOUT = {
    "ciudad": dict(light=0xFFB8C0D4, ground=810, windows=[(300, 360), (420, 360), (300, 470), (420, 470), (1100, 340), (1220, 340), (1100, 450), (1220, 450)]),
    "puerta": dict(light=0xFFC8C4B8, ground=820, door=(560, 120, 980, 800)),
    "oficina": dict(light=0xFFD8D0B8, ground=812, board=(430, 150, 1110, 520)),
    "calle": dict(light=0xFFD0D4DC, ground=815, gate=(700, 640), car=(1180, 800), window=(420, 380)),
    "ring": dict(light=0xFFFFF0D8, ground=600, ring=(768, 600)),
    "juzgado": dict(light=0xFFD8DCE4, ground=815, bench=(768, 440)),
}
LAYOUT.update(json.loads((EP / "layout.json").read_text(encoding="utf-8")) if (EP / "layout.json").exists() else {})

DET = dict(jacket=(0xFF5A6070, 0xFF444A58), hair=0xFF2A2420)
DET2 = dict(jacket=(0xFF7A6248, 0xFF5E4A36), hair=0xFF141414)
COP = dict(jacket=(0xFF26324A, 0xFF1A2336), hair=0xFF141414, police_cap=True)
TENANT = dict(jacket=(0xFF6E8A5A, 0xFF566C46), hair=0xFF3A2A1E)
RED, BLUE, PAPER = 0xFFE0302A, 0xFF3A6CFF, 0xFFEFE9D8


def glow(c, x, y, rx, ry, color, alpha):
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, rx * .9))
    p.setColor(skia.ColorSetARGB(int(max(0, min(1, alpha)) * 200), (color >> 16) & 255, (color >> 8) & 255, color & 255))
    c.drawOval(skia.Rect.MakeXYWH(x - rx * 2, y - ry * 2, rx * 4, ry * 4), p)


def silhouette(c, d, alpha=1.0, color=0xFF0E0E12):
    """Draws a rig character as a flat dark shape (no face)."""
    c.saveLayer(None, skia.Paint(Alphaf=alpha, ColorFilter=skia.ColorFilters.Blend(color, skia.BlendMode.kSrcIn)))
    character(c, d)
    c.restore()


def outline(text, x, y, size, color=0xFFF2E6B8):
    f = font(size)
    return lambda c, t, p: (c.drawString(text, x - f.measureText(text) / 2, y, f, stroke(10)), c.drawString(text, x - f.measureText(text) / 2, y, f, fill(color)))


def lit_windows(level_of):
    """Warm lights in the apartment windows; level_of(j) gives each window's brightness."""
    def draw(c, t, paint):
        for j, (x, y) in enumerate(LAYOUT["ciudad"]["windows"]):
            lv = level_of(j)
            if lv > 0:
                c.drawRect(skia.Rect.MakeXYWH(x - 26, y - 28, 52, 56), fill(skia.ColorSetARGB(int(150 * min(1, lv)), 255, 200, 110)))
                glow(c, x, y, 40, 34, 0xFFFFC870, min(1, lv))
    return draw


def board(k_pins, k_sketch=0.0, k_swap=0.0):
    """Cork board: case cards appear and get joined with red string; then a sketch of a man is pinned in the middle."""
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT["oficina"]["board"]
        w, h = x1 - x0, y1 - y0
        r = random.Random(4)
        cards = [(x0 + w * (.1 + .8 * r.random()), y0 + h * (.15 + .7 * r.random())) for _ in range(9)]
        n = int(ease(k_pins) * len(cards) + .001)
        for j in range(1, n):
            c.drawLine(*cards[j - 1], *cards[j], stroke(3, 0xFFB02420))
        for j in range(n):
            x, y = cards[j]
            c.drawRect(skia.Rect.MakeXYWH(x - 34, y - 24, 68, 48), fill(PAPER))
            c.drawRect(skia.Rect.MakeXYWH(x - 34, y - 24, 68, 48), stroke(3))
            for q in range(3):
                c.drawLine(x - 24, y - 10 + q * 10, x + 22, y - 10 + q * 10, stroke(3, 0xFF9A958A))
            c.drawCircle(x, y - 24, 6, fill(RED))
        if k_sketch > 0:
            cx, cy = x0 + w / 2, y0 + h / 2
            sc = lerp(1.4, 1, ease(k_sketch))
            c.save()
            c.translate(cx, cy)
            c.scale(sc, sc)
            c.drawRect(skia.Rect.MakeXYWH(-70, -90, 140, 180), fill(0xFFF4F0E4))
            sketch_face(c, 0, 0, 1 - k_swap)
            if k_swap > 0:
                c.drawString("?", -18, 30, font(90), fill(skia.ColorSetARGB(int(255 * k_swap), 176, 36, 32)))
            c.drawRect(skia.Rect.MakeXYWH(-70, -90, 140, 180), stroke(4))
            c.drawCircle(0, -90, 7, fill(RED))
            c.restore()
    return draw


def sketch_face(c, x, y, level=1.0):
    """Pencil composite sketch of a man: short hair, moustache, plain shirt collar."""
    if level <= 0:
        return
    a = int(255 * level)
    pen = lambda w: stroke(w, skia.ColorSetARGB(a, 60, 60, 66))  # noqa: E731
    c.drawOval(skia.Rect.MakeXYWH(x - 38, y - 64, 76, 96), pen(3))
    c.drawArc(skia.Rect.MakeXYWH(x - 40, y - 70, 80, 60), 180, 180, False, pen(6))
    for s in (-1, 1):
        c.drawLine(x + s * 10, y - 22, x + s * 26, y - 22, pen(3))
        c.drawCircle(x + s * 17, y - 14, 3, fill(skia.ColorSetARGB(a, 60, 60, 66)))
    c.drawLine(x - 14, y + 8, x + 14, y + 8, pen(5))
    c.drawLine(x - 8, y + 18, x + 8, y + 18, pen(2))
    c.drawLine(x - 50, y + 90, x - 20, y + 36, pen(3))
    c.drawLine(x + 50, y + 90, x + 20, y + 36, pen(3))


def headline(k, top, big, sub=""):
    """Newspaper slides up with the headline of the time (screen space)."""
    def draw(c, t, paint):
        if k <= 0:
            return
        c.save()
        c.translate(W / 2, H / 2 + (1 - ease(k)) * 600)
        c.rotate(-3)
        page = skia.Rect.MakeXYWH(-330, -230, 660, 440)
        c.drawRect(skia.Rect.MakeXYWH(-322, -222, 660, 440), fill(0x66000000))
        c.drawRect(page, fill(PAPER))
        c.drawRect(page, stroke(6))
        f = font(34)
        c.drawString(top, -f.measureText(top) / 2, -185, f, fill(INK))
        c.drawLine(-300, -168, 300, -168, stroke(4))
        fb = font(64)
        c.drawString(big, -fb.measureText(big) / 2, -100, fb, fill(INK))
        if sub:
            fs = font(30)
            c.drawString(sub, -fs.measureText(sub) / 2, -55, fs, fill(0xFF3A3A40))
        c.drawRect(skia.Rect.MakeXYWH(-300, -30, 250, 220), fill(0xFFE0DAC8))
        sketch_face(c, -175, 70, 1.0)
        for j in range(8):
            c.drawLine(-20, -20 + j * 28, 300 - (j % 3) * 30, -20 + j * 28, stroke(7, 0xFF8A857A))
        c.restore()
    return draw


def folder(k, name):
    """Case file opened on the desk with the name typed on the tab (screen space)."""
    def draw(c, t, paint):
        if k <= 0:
            return
        c.save()
        c.translate(W / 2, H / 2 - 10)
        sc = lerp(.7, 1, ease(k))
        c.scale(sc, sc)
        c.saveLayer(None, skia.Paint(Alphaf=min(1, k * 1.5)))
        c.drawRoundRect(skia.Rect.MakeXYWH(-360, -200, 720, 400), 10, 10, fill(0xFFD8B878))
        c.drawRoundRect(skia.Rect.MakeXYWH(-360, -200, 720, 400), 10, 10, stroke(5))
        c.drawRect(skia.Rect.MakeXYWH(-320, -170, 640, 340), fill(PAPER))
        c.drawRect(skia.Rect.MakeXYWH(-320, -170, 640, 340), stroke(4))
        c.drawString("EXPEDIENTE", -290, -120, font(34), fill(0xFF8A2A22))
        n = int(ease(min(1, k * 1.3)) * len(name))
        f = font(40)
        c.drawString(name[:n], -290, -40, f, fill(INK))
        for j in range(5):
            c.drawLine(-290, 20 + j * 30, 120 - (j % 2) * 60, 20 + j * 30, stroke(6, 0xFF9A958A))
        c.drawRect(skia.Rect.MakeXYWH(150, -10, 140, 160), fill(0xFF3A3A40))
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(150, -10, 140, 160))
        silhouette(c, dict(t=0, x=220, y=200, scale=.5, back=False), 1.0, 0xFF1A1A20)
        c.restore()
        c.restore()
        c.restore()
    return draw


def patrol(c, x, y, t, lights=True, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = poly([(-230, -30), (-220, -86), (-120, -96), (-70, -150), (90, -150), (150, -96), (230, -86), (236, -30)])
    c.drawPath(body, fill(0xFFEDEDE8))
    c.drawPath(poly([(-232, -64), (236, -64), (236, -30), (-230, -30)]), fill(0xFF1E2A44))
    c.drawPath(body, stroke(6))
    for wx0, wx1 in ((-60, 0), (14, 80)):
        c.drawPath(poly([(wx0, -100), (wx0 + 8, -140), (wx1, -140), (wx1 + 14, -100)]), fill(0xFF8FB6D0))
        c.drawPath(poly([(wx0, -100), (wx0 + 8, -140), (wx1, -140), (wx1 + 14, -100)]), stroke(4))
    for wx in (-140, 150):
        c.drawCircle(wx, -26, 34, fill(INK))
        c.drawCircle(wx, -26, 14, fill(0xFF9A9A9A))
    on = int(t * 4) % 2
    for j, col in ((-1, RED), (1, BLUE)):
        lit = lights and ((j < 0) == bool(on))
        c.drawRoundRect(skia.Rect.MakeXYWH(-6 + j * 24 - 18, -168, 36, 18), 5, 5, fill(col if lit else 0xFF3A3A44))
        c.drawRoundRect(skia.Rect.MakeXYWH(-6 + j * 24 - 18, -168, 36, 18), 5, 5, stroke(4))
    c.restore()
    if lights:
        glow(c, x - 30 * s, y - 160 * s, 160 * s, 90 * s, RED if on else BLUE, .55)


def bars(k):
    """Prison bars slide down over the whole frame (screen space)."""
    def draw(c, t, paint):
        if k <= 0:
            return
        drop = lerp(-H, 0, ease(k))
        for j in range(9):
            x = 70 + j * 142
            c.drawRect(skia.Rect.MakeXYWH(x - 9, drop, 18, H), fill(0xFF2A2C30))
            c.drawRect(skia.Rect.MakeXYWH(x - 9, drop, 18, H), stroke(4))
        c.drawRect(skia.Rect.MakeXYWH(0, drop + H * .2, W, 22), fill(0xFF2A2C30))
        c.drawRect(skia.Rect.MakeXYWH(0, drop + H * .2, W, 22), stroke(4))
    return draw


def gavel(k_hit):
    """The judge's gavel comes down on the bench."""
    def draw(c, t, paint):
        bx, by = LAYOUT["juzgado"]["bench"]
        ang = lerp(-50, 0, ease(min(1, k_hit))) if k_hit < 1 else 0
        c.save()
        c.translate(bx + 160, by - 10)
        c.rotate(ang)
        c.drawLine(0, 0, -120, -10, stroke(14, 0xFF6A4A2E))
        c.drawLine(0, 0, -120, -10, stroke(4))
        c.drawRoundRect(skia.Rect.MakeXYWH(-150, -40, 50, 64), 8, 8, fill(0xFF6A4A2E))
        c.drawRoundRect(skia.Rect.MakeXYWH(-150, -40, 50, 64), 8, 8, stroke(5))
        c.restore()
    return draw


def counter(text, k, y=560, size=58, color=0xFFF2E6B8):
    def draw(c, t, paint):
        if k <= 0:
            return
        f = font(size)
        x = (W - f.measureText(text)) / 2
        c.saveLayer(None, skia.Paint(Alphaf=min(1, k * 2)))
        c.drawString(text, x, y + (1 - ease(k)) * 30, f, stroke(12))
        c.drawString(text, x, y + (1 - ease(k)) * 30, f, fill(color))
        c.restore()
    return draw


# ---------------------------------------------------------------- beats
L = LINES
mid = lambda j, f=.5: L[j]["start"] + (L[j]["end"] - L[j]["start"]) * f  # noqa: E731
B = {}
B["ventanas"] = beat("ventanas", [L[0]["start"] + d for d in (1.0, 2.0, 3.0, 4.0)])
B["toca"] = beat("toca", L[1]["start"] + .6)
B["abre"] = beat("abre", mid(1, .55))
B["pines"] = beat("pines", L[2]["start"] + .3)
B["periodico"] = beat("periodico", mid(3, .45))
B["retrato"] = beat("retrato", L[4]["start"] + .4)
B["giro"] = beat("giro", L[5]["start"] + .2)
B["fecha"] = beat("fecha", L[6]["start"] + .1)
B["sale"] = beat("sale", mid(6, .55))
B["inquilino"] = beat("inquilino", L[7]["start"] + .2)
B["sirena"] = beat("sirena", mid(7, .4))
B["expediente"] = beat("expediente", L[8]["start"] + .1)
B["foco"] = beat("foco", L[9]["start"] + .2)
B["nombre_ring"] = beat("nombre_ring", mid(9, .6))
B["mazo"] = beat("mazo", L[10]["start"] + .3)
B["cifras"] = beat("cifras", [mid(10, .35), mid(10, .8)])
B["rejas"] = beat("rejas", L[11]["start"] + .1)
B["cambio"] = beat("cambio", mid(12, .45))


def person(base, appearance, **kw):
    d = dict(base)
    d.update(appearance)
    d.update(kw)
    return d


def shots(t):
    i, lt, k = linea(t)
    base = dict(t=t, blink=blink(t))
    g = LAYOUT
    out = dict(bg="ciudad")
    if i == 0:  # years, the city: window lights go out one by one
        out["cam"] = Cam((768, 432, 1.0), (768, 440, 1.2), k)
        out["dark"] = .2
        n_off = sum(t >= x for x in B["ventanas"])
        out["over"] = [lit_windows(lambda j: 0 if j % 4 < n_off else 1)]
    elif i == 1:  # a backlit silhouette at the door, offering help; the door opens a crack
        out["bg"] = "puerta"
        x0, y0, x1, y1 = g["puerta"]["door"]
        out["cam"] = Cam((768, 470, 1.1), ((x0 + x1) / 2, 470, 1.35), k)
        out["dark"] = .25
        knock = math.exp(-max(0, t - B["toca"]) * 5) if t >= B["toca"] else 0
        opening = ease((t - B["abre"]) / .8)
        gy = g["puerta"]["ground"]

        def shadow(c, tt, p):
            if opening > 0:  # warm light spills through the gap and a long shadow falls across the floor
                gap = skia.Rect.MakeLTRB(x1 - (x1 - x0) * .18 * opening, y0, x1, y1)
                c.drawRect(gap, fill(0xFFF0D8A0))
                sh = skia.Paint(AntiAlias=True, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
                sh.setColor(0x99000000)
                c.drawPath(poly([(x1 - 60, y1), (x1 - 10, y1), (x1 + 220 * opening, gy + 40), (x1 + 120 * opening, gy + 50)]), sh)
            if knock > 0:
                for j in range(2):
                    c.drawArc(skia.Rect.MakeXYWH((x0 + x1) / 2 - 40 - j * 20, (y0 + y1) / 2 - 40 - j * 20, 80 + j * 40, 80 + j * 40), -40, 80, False,
                              stroke(5, skia.ColorSetARGB(int(255 * knock), 242, 226, 30)))
        out["over"] = [shadow]
        out["shake"] = (knock * 4 * math.sin(t * 60), 0)
    elif i <= 4:  # the investigation board, the press name, the sketch of a man
        out["bg"] = "oficina"
        x0, y0, x1, y1 = g["oficina"]["board"]
        gy = g["oficina"]["ground"]
        kp = (t - B["pines"]) / 3.0
        ks = ease((t - B["retrato"]) / .6) if i == 4 else 0
        out["over"] = [board(min(1, max(0, kp)), ks)]
        out["dark"] = .15
        out["flicker"] = 0
        dets = [person(base, DET, x=x0 + 60, y=gy, scale=.95, face=.5, look=(.5, -.9), mouth="flat", brow=-.5, arm_r=(2.3, .3) if i == 4 else (.1, .1)),
                person(base, DET2, x=x1 - 40, y=gy + 8, scale=.97, face=-.5, look=(-.5, -.9), mouth="flat", brow=-.5, blink=blink(t, 1.3))]
        out["chars"] = dets
        if i == 2:
            out["cam"] = Cam((768, 432, 1.0), ((x0 + x1) / 2, (y0 + y1) / 2 + 60, 1.25), k)
        elif i == 3:
            out["cam"] = Cam(((x0 + x1) / 2, (y0 + y1) / 2 + 60, 1.25), ((x0 + x1) / 2, (y0 + y1) / 2 + 60, 1.3), k)
            out["hud"] = [headline((t - B["periodico"]) / .7, "DIARIO DE LA CIUDAD", "EL MATAVIEJITAS", "La policía investiga una serie de casos")]
        else:
            out["cam"] = Cam(((x0 + x1) / 2, (y0 + y1) / 2 + 80, 1.2), ((x0 + x1) / 2, (y0 + y1) / 2, 1.9), k)
            out["hud"] = [counter("SE BUSCA A UN HOMBRE", ease((lt - 1.4) / .5), 120, 52)]
    elif i == 5:  # but there was something nobody expected
        out["cam"] = Cam((768, 440, 1.2), (768, 470, 1.6), k)
        out["dark"] = .45
        out["flicker"] = .6
        out["over"] = [lit_windows(lambda j: 0)]
        out["shake"] = (math.exp(-max(0, t - B["giro"]) * 3) * math.sin(t * 50) * 6, 0)
    elif i <= 7:  # 25 Jan 2006: a woman leaves the house; a tenant sees her, a patrol car stops
        out["bg"] = "calle"
        gx, gy0 = g["calle"]["gate"]
        carx, cary = g["calle"]["car"]
        wx, wy = g["calle"]["window"]
        gy = g["calle"]["ground"]
        walk_k = ease((t - B["sale"]) / 2.4)
        stop = i == 7 and t >= B["sirena"]
        wx_now = lerp(gx, gx + 230, walk_k) if not stop else lerp(gx, gx + 230, ease((B["sirena"] - B["sale"]) / 2.4))
        figure = dict(t=t, x=wx_now, y=gy, scale=.95, walk=t * 5 if (0 < walk_k < 1 and not stop) else None, face=.6, look=(1, 0),
                      jacket=(0xFF8A3A4A, 0xFF6A2C38), hair=0xFF1A1410)
        out["over"] = [lambda c, tt, p: silhouette(c, figure, .97) if t >= B["sale"] - .3 else None]
        out["dark"] = .1
        if i == 6:
            out["cam"] = Cam((768, 470, 1.1), (gx + 120, 520, 1.3), k)
            out["hud"] = [counter("25 DE ENERO DE 2006", ease((t - B["fecha"]) / .4) * (1 - ease((lt - 3.5) / .5)), 120, 56)]
        else:
            out["cam"] = Cam((gx + 60, 500, 1.15), ((gx + carx) / 2, 540, 1.1), k)
            point = ease((t - B["inquilino"]) / .4)
            out["chars"] = [person(base, TENANT, x=wx, y=wy + 160, scale=.6, face=.6, look=(1, .3), arm_r=(lerp(.1, 2.2, point), .1), mouth="o")]
            if stop:
                on = int(t * 6) % 2
                out["over"].append(lambda c, tt, p: (glow(c, 1000, 495, 30, 16, RED, .9 if on else .2), glow(c, 1070, 495, 30, 16, BLUE, .2 if on else .9)))
                kw = ease((t - B["sirena"] - .3) / 1.4)
                out["chars"].append(person(base, COP, x=lerp(1010, wx_now + 190, kw), y=gy + 10, scale=.95, face=-.6, look=(-1, 0),
                                           walk=t * 5 if 0 < kw < 1 else None, arm_r=(1.4, .3) if kw >= 1 else (.1, .1), mouth="flat"))
    elif i == 8:  # her name, on the case file
        out["bg"] = "oficina"
        out["cam"] = Cam((768, 432, 1.15), (768, 432, 1.25), k)
        out["dark"] = .45
        out["hud"] = [folder((t - B["expediente"]) / 1.2, "JUANA BARRAZA SAMPERIO")]
    elif i == 9:  # former wrestler, "La Dama del Silencio": a masked silhouette under the spotlight
        out["bg"] = "ring"
        rx, ry = g["ring"]["ring"]
        on = ease((t - B["foco"]) / .3)
        out["dark"] = lerp(.8, .2, on)
        out["flicker"] = 0
        out["cam"] = Cam((rx, ry - 160, 1.2), (rx, ry - 200, 1.6), k)
        wrestler = dict(t=t, x=rx, y=ry, scale=1.0, face=0, arm_l=(.4, .5), arm_r=(.4, .5), breath_amp=4)

        def figure(c, tt, p):
            glow(c, rx, ry - 200, 220, 280, 0xFFFFF0C8, .7 * on)
            silhouette(c, wrestler, on)
            hx, hy = rx, ry - 248  # mask highlights on the head
            for s in (-1, 1):
                c.drawPath(poly([(hx + s * 10, hy - 6), (hx + s * 40, hy - 20), (hx + s * 36, hy + 6)]), fill(skia.ColorSetARGB(int(255 * on), 200, 40, 50)))
            c.drawLine(hx, hy - 66, hx, hy - 20, stroke(6, skia.ColorSetARGB(int(255 * on), 200, 40, 50)))
        out["over"] = [figure]
        out["hud"] = [counter("LA DAMA DEL SILENCIO", ease((t - B["nombre_ring"]) / .5), 120, 60)]
    elif i <= 11:  # conviction and sentence, today still in prison
        out["bg"] = "juzgado"
        bx, by = g["juzgado"]["bench"]
        out["dark"] = .15
        out["flicker"] = 0
        if i == 10:
            hit = (t - B["mazo"]) / .25
            out["cam"] = Cam((bx, by + 40, 1.1), (bx, by, 1.3), k)
            out["over"] = [gavel(max(0, hit))]
            imp = math.exp(-(t - B["mazo"]) * 8) if t >= B["mazo"] + .25 else 0
            out["shake"] = (0, imp * 8)
            out["hud"] = [counter("16 HOMICIDIOS · 12 ROBOS", ease((t - B["cifras"][0]) / .4), 560, 54),
                          counter("759 AÑOS DE PRISIÓN", ease((t - B["cifras"][1]) / .4), 640, 64, 0xFFF2E21E)]
        else:
            out["cam"] = Cam((bx, by, 1.3), (bx, by, 1.4), k)
            out["dark"] = .35
            out["hud"] = [bars((t - B["rejas"]) / .6), counter("HOY SIGUE PRESA", ease((lt - .5) / .4), 380, 64)]
    else:  # the person they were looking for was not who everyone imagined
        x0, y0, x1, y1 = g["oficina"]["board"]
        if i == 12:
            out["bg"] = "oficina"
            out["cam"] = Cam(((x0 + x1) / 2, (y0 + y1) / 2, 1.9), ((x0 + x1) / 2, (y0 + y1) / 2, 2.1), k)
            out["over"] = [board(1, 1, ease((t - B["cambio"]) / .8))]
            out["dark"] = .2
        else:
            out["cam"] = Cam((768, 470, 1.5), (768, 432, 1.0), k)
            out["dark"] = .3
            out["over"] = [lit_windows(lambda j: ease(k * 2 - j * .1))]
    return out


terminar(shots, LAYOUT, "mataviejitas")
