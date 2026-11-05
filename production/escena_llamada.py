"""Sticks, Ideas propias: a 911 call from your own house. One visible action per sentence; positions are in background pixels.
Usage: render_env/Scripts/python.exe escena_llamada.py <episode folder> [--stills ...] [--full] [--audio] [--short]"""
from palitos import *

LAYOUT = {
    "central": dict(light=0xFFA8C4E8, ground=800, seat=(560, 800), monitor=(700, 330, 960, 500), phone=(1010, 560), floor_bag=(400, 800)),
    "pantalla": dict(screen=(230, 110, 1300, 700)),
    "calle": dict(light=0xFFB4C0DC, ground=815, door=(768, 650), car=(1180, 800)),
    "sala": dict(light=0xFFE6CCA8, ground=812, chair=(380, 760), mug=(560, 640), photos=[(560, 330), (720, 330), (880, 330)], kitchen=(1290, 800)),
    "armario": dict(light=0xFFAEBCD8, ground=805, closet=(600, 230, 940, 790)),
}
LAYOUT.update(json.loads((EP / "layout.json").read_text(encoding="utf-8")) if (EP / "layout.json").exists() else {})

YOU = dict(jacket=(0xFF2C3A4E, 0xFF1F2A3A), hair=0xFF2A1E18)
HER = dict(jacket=(0xFFB4485A, 0xFF8A3444), hair=0xFF1E1410)
COP = dict(jacket=(0xFF26324A, 0xFF1A2336), hair=0xFF141414, police_cap=True)
GRAY = 0xFF8A8E94
RED, BLUE = 0xFFE0302A, 0xFF3A6CFF


# ---------------------------------------------------------------- props
def glow(c, x, y, rx, ry, color, alpha):
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, rx * .9))
    p.setColor(skia.ColorSetARGB(int(max(0, min(1, alpha)) * 200), (color >> 16) & 255, (color >> 8) & 255, color & 255))
    c.drawOval(skia.Rect.MakeXYWH(x - rx * 2, y - ry * 2, rx * 4, ry * 4), p)


def rings(x, y, level, t, color=0xFFF2E21E):
    """Concentric arcs coming out of a ringing phone."""
    def draw(c, tt, paint):
        if level <= 0:
            return
        for j in range(3):
            ph = ((tt * 2.2) + j / 3) % 1
            a = int(255 * level * (1 - ph))
            for side in (-1, 1):
                r = 20 + ph * 60
                c.drawArc(skia.Rect.MakeXYWH(x - r, y - r, 2 * r, 2 * r), (-35 if side > 0 else 145), 70, False, stroke(5, (a << 24) | (color & 0xFFFFFF)))
    return draw


def headset(c, ch):
    """Headset drawn over a character's head (head centre is 248 px above the feet when standing, 182 when seated)."""
    hy = -182 if ch.get("sit") else -248
    c.save()
    c.translate(ch["x"], ch["y"])
    c.scale(ch["scale"] * ch.get("dir", 1), ch["scale"])
    c.drawArc(skia.Rect.MakeXYWH(-70, hy - 74, 140, 130), 200, 140, False, stroke(8))
    c.drawRoundRect(skia.Rect.MakeXYWH(52, hy - 18, 22, 36), 8, 8, fill(0xFF22262C))
    c.drawLine(62, hy + 14, 34, hy + 40, stroke(5))
    c.restore()


def backpack(c, x, y, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    body = skia.Rect.MakeXYWH(-40, -96, 80, 96)
    c.drawRoundRect(body, 22, 22, fill(GRAY))
    c.drawRoundRect(skia.Rect.MakeXYWH(-30, -50, 60, 40), 10, 10, fill(0xFF73777E))
    c.drawRoundRect(skia.Rect.MakeXYWH(-30, -50, 60, 40), 10, 10, stroke(4))
    c.drawRoundRect(body, 22, 22, stroke(5))
    c.drawArc(skia.Rect.MakeXYWH(-18, -116, 36, 36), 180, 180, False, stroke(6))
    c.restore()


def mug(c, x, y, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawArc(skia.Rect.MakeXYWH(14, -40, 26, 26), -90, 180, False, stroke(6))
    c.drawRoundRect(skia.Rect.MakeXYWH(-20, -50, 40, 50), 6, 6, fill(0xFFE8E4DA))
    c.drawRoundRect(skia.Rect.MakeXYWH(-20, -50, 40, 50), 6, 6, stroke(5))
    c.restore()


def portrait(c, x, y, who, level=1.0, t=0.0, w=110, h=130):
    """A framed photo on the wall; `who` is a look dict (or None for an empty frame). level fades the person in."""
    rect = skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)
    c.drawRect(rect, fill(0xFFD8E2E6))
    if who and level > 0:
        c.save()
        c.clipRect(rect)
        c.saveLayer(None, skia.Paint(Alphaf=level))
        ch = dict(who, x=x, y=y + h * .95, scale=.42, t=t, mouth="smile", blink=0)
        character(c, ch)
        c.restore()
        c.restore()
    c.drawRect(rect, stroke(9, 0xFF5A3A22))
    c.drawRect(rect, stroke(3))


def patrol(c, x, y, t, lights=True, s=1.0):
    """Side view of a patrol car facing left, with the light bar flashing red and blue."""
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
        glow(c, x - 30 * s, y - 160 * s, 160 * s, 90 * s, RED if int(t * 4) % 2 else BLUE, .55)


def inset(name, draw_in, k=1.0, rect=(820, 70, 420, 260), cam=None):
    """Picture-in-picture window (screen pixels) showing another background with its own drawings (background pixels)."""
    def draw(c, t, paint):
        if k <= 0:
            return
        x, y, w, h = rect
        sc = lerp(.6, 1, ease(k))
        c.save()
        c.translate(x + w / 2, y + h / 2)
        c.scale(sc, sc)
        c.translate(-w / 2, -h / 2)
        a = min(1, k * 1.5)
        c.saveLayer(None, skia.Paint(Alphaf=a))
        c.drawRect(skia.Rect.MakeXYWH(6, 8, w, h), fill(0x88000000))
        c.save()
        c.clipRect(skia.Rect.MakeWH(w, h))
        cx, cy, z = cam or (BG_W / 2, BG_H / 2, 1.0)
        s = w / BG_W * z
        c.translate(w / 2, h / 2)
        c.scale(s, s)
        c.translate(-cx, -cy)
        c.drawImage(BGS[name], 0, 0, SAMPLING)
        draw_in(c, t)
        c.restore()
        c.drawRect(skia.Rect.MakeWH(w, h), stroke(6, 0xFFE8EEF2))
        c.restore()
        c.restore()
    return draw


def screen(c, t, k_text, k_pin, alarm=0.0):
    """Content of the call-center monitor: incoming call, address being typed, and a map pin on a house."""
    x0, y0, x1, y1 = LAYOUT["pantalla"]["screen"]
    w, h = x1 - x0, y1 - y0
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(x0, y0, x1, y1))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), fill(0xFF0E2238))
    head_c = RED if int(t * 3) % 2 else 0xFFB02420
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y0 + h * .14), fill(head_c))
    f = font(int(h * .075))
    c.drawString("LLAMADA ENTRANTE  •  00:00:" + f"{int(t) % 60:02d}", x0 + w * .03, y0 + h * .1, f, fill(0xFFFFFFFF))
    c.drawString("DIRECCIÓN:", x0 + w * .04, y0 + h * .3, f, fill(0xFF8FC8F0))
    address = "CALLE ROBLE 14"
    n = int(ease(k_text) * len(address))
    cur = "_" if int(t * 3) % 2 else ""
    big = font(int(h * .12))
    c.drawString(address[:n] + cur, x0 + w * .04, y0 + h * .48, big, fill(0xFFFFFFFF))
    mx0, my0 = x0 + w * .56, y0 + h * .56
    c.drawRect(skia.Rect.MakeLTRB(mx0, my0, x1 - w * .03, y1 - h * .05), fill(0xFF1C3A54))
    for j in range(6):
        c.drawLine(mx0, my0 + j * h * .07, x1 - w * .03, my0 + j * h * .07 + 20, stroke(5, 0xFF2E5878))
        c.drawLine(mx0 + j * w * .07, my0, mx0 + j * w * .07 - 14, y1 - h * .05, stroke(5, 0xFF2E5878))
    if k_pin > 0:
        px, py = mx0 + w * .2, my0 + h * .2
        drop = lerp(-80, 0, ease(min(1, k_pin * 2)))
        glow(c, px, py, 30, 20, RED, .5 + .4 * math.sin(t * 6))
        c.drawPath(poly([(px - 18, py - 40 + drop), (px + 18, py - 40 + drop), (px, py + drop)]), fill(RED))
        c.drawCircle(px, py - 46 + drop, 20, fill(RED))
        c.drawCircle(px, py - 46 + drop, 8, fill(0xFFFFFFFF))
    if alarm > 0:
        tag = "TU CASA"
        fb = font(int(h * .1))
        c.drawRoundRect(skia.Rect.MakeXYWH(x0 + w * .04, y0 + h * .62, fb.measureText(tag) + 40, h * .16), 14, 14,
                        fill(skia.ColorSetARGB(int(255 * alarm), 224, 48, 42)))
        c.drawString(tag, x0 + w * .04 + 20, y0 + h * .74, fb, fill(skia.ColorSetARGB(int(255 * alarm), 255, 255, 255)))
    c.restore()


def monitor_glow(level=1.0):
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT["central"]["monitor"]
        glow(c, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * .8, (y1 - y0) * .8, 0xFF6FA8FF, level * (.85 + .15 * math.sin(t * 9)))
    return draw


def closet_open(k, inside=None):
    """Dark gap between the closet doors that widens as they open; `inside` draws what is in there."""
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT["armario"]["closet"]
        mid = (x0 + x1) / 2
        half = (x1 - x0) / 2 * ease(k)
        if half <= 1:
            return
        rect = skia.Rect.MakeLTRB(mid - half, y0, mid + half, y1)
        c.drawRect(rect, fill(0xFF0A0C12))
        if inside:
            c.save()
            c.clipRect(rect)
            inside(c, t)
            c.restore()
        for side in (-1, 1):  # door edges swinging toward us
            ex = mid + side * half
            c.drawPath(poly([(ex, y0), (ex + side * 40 * ease(k), y0 - 16), (ex + side * 40 * ease(k), y1 + 16), (ex, y1)]), fill(0xFF6A4A2E))
            c.drawPath(poly([(ex, y0), (ex + side * 40 * ease(k), y0 - 16), (ex + side * 40 * ease(k), y1 + 16), (ex, y1)]), stroke(5))
    return draw


def paper(k, title, lines=6):
    """A document held up to camera (screen space)."""
    def draw(c, t, paint):
        if k <= 0:
            return
        c.save()
        c.translate(W / 2 + 300, H / 2 - 40 + (1 - ease(k)) * 500)
        c.rotate(-4)
        r = skia.Rect.MakeXYWH(-150, -190, 300, 380)
        c.drawRect(skia.Rect.MakeXYWH(-142, -182, 300, 380), fill(0x66000000))
        c.drawRect(r, fill(0xFFF2EEE2))
        c.drawRect(r, stroke(5))
        f = font(34)
        c.drawString(title, -f.measureText(title) / 2, -140, f, fill(INK))
        for j in range(lines):
            c.drawLine(-120, -90 + j * 34, 120 - (j % 3) * 30, -90 + j * 34, stroke(6, 0xFF9A958A))
        c.drawPath(poly([(-110, 140), (-60, 120), (-20, 150), (30, 118)], close=False), stroke(4, 0xFF2A4AA0))
        c.restore()
    return draw


def person(base, appearance, **kw):
    d = dict(base)
    d.update(appearance)
    d.update(kw)
    return d


# ---------------------------------------------------------------- beats
L = LINES
mid = lambda j, f=.5: L[j]["start"] + (L[j]["end"] - L[j]["start"]) * f  # noqa: E731
B = {}
B["timbre"] = beat("timbre", L[2]["start"] + .4)
B["contesta"] = beat("contesta", L[3]["start"] + .1)
B["susurro"] = beat("susurro", L[5]["start"] + .2)
B["teclea"] = beat("teclea", L[7]["start"] + .3)
B["pin"] = beat("pin", mid(8, .2))
B["tu_casa"] = beat("tu_casa", L[9]["start"] + .2)
B["armario_inset"] = beat("armario_inset", L[11]["start"] + .2)
B["patrulla_radio"] = beat("patrulla_radio", L[14]["start"] + .3)
B["mochila_cae"] = beat("mochila_cae", mid(16, .62))
B["mira_mochila"] = beat("mira_mochila", L[17]["start"] + .1)
B["mira_uniforme"] = beat("mira_uniforme", L[18]["start"] + .1)
B["corre"] = beat("corre", L[19]["start"] + .2)
B["sirena"] = beat("sirena", L[20]["start"])
B["puerta"] = beat("puerta", L[21]["start"] + .15)
B["armario_abre"] = beat("armario_abre", L[24]["start"] + .3)
B["mirada"] = beat("mirada", L[26]["start"] + .2)
B["papeles"] = beat("papeles", L[27]["start"] + .3)
B["fotos_cambian"] = beat("fotos_cambian", L[31]["start"] + .1)
B["timbre_final"] = beat("timbre_final", mid(32, .6))
B["contesta_final"] = beat("contesta_final", L[34]["start"] + .2)


def shots(t):
    i, lt, k = linea(t)
    base = dict(t=t, blink=blink(t))
    g = LAYOUT
    out = dict(bg="central")
    sx, sy = g["central"]["seat"]
    px, py = g["central"]["phone"]
    you_seat = lambda **kw: person(base, YOU, **{**dict(x=sx, y=sy, scale=.95, sit=True, face=.6, look=(.8, -.3)), **kw})  # noqa: E731
    if i <= 1:  # 3 a.m., quiet shift
        out["cam"] = Cam((768, 470, 1.0), (sx + 120, sy - 220, 1.5), (t - 0) / max(.1, L[2]["start"]))
        out["dark"] = .2
        out["over"] = [monitor_glow(.8)]
        ch = you_seat(mouth="flat", eye=.8, tilt=-8 if i == 1 else 0, blink=blink(t) if i == 0 else max(blink(t), .55 * (lt > 1)))
        out["char"] = ch
        out["front"] = [lambda c, tt, p: headset(c, ch)]
        if i == 0:
            out["hud"] = [lambda c, tt, p: (c.drawString("3:00 A.M.", 60, 120, font(72), stroke(10)), c.drawString("3:00 A.M.", 60, 120, font(72), fill(0xFFF2E6B8)))]
    elif i <= 6:  # the call
        ring = 1.0 if (i == 2 and t >= B["timbre"]) else 0
        answered = t >= B["contesta"]
        out["cam"] = Cam((sx + 150, sy - 220, 1.5), (sx + 120, sy - 240, 1.9 if i >= 5 else 1.6), (t - L[2]["start"]) / (L[7]["start"] - L[2]["start"]))
        out["dark"] = .25 if i < 5 else .35
        out["over"] = [monitor_glow(1.0), rings(px, py - 30, ring, t)]
        pressing = i == 3
        arm = (lerp(.1, 2.7, ease(lt / .4)), 1.4) if pressing else ((2.7, 1.4) if i == 4 else (.1, .1))
        mouth = talk(t) if i == 4 else ("gasp" if i == 2 else "flat")
        ch = you_seat(mouth=mouth, eye=1.25 if i in (2, 6) else 1.0, brow=-.8 if i >= 5 else 0, arm_r=arm, look=(.8, -.3) if i < 5 else (.3, 0))
        out["char"] = ch
        out["front"] = [lambda c, tt, p: headset(c, ch)]
        if i >= 5:  # the whisper: a sound wave on the headset and a dark living room inset
            def wave(c, tt, p):
                for j in range(26):
                    a = abs(math.sin(tt * 9 + j * .7)) * (.4 + .6 * abs(math.sin(j * .4)))
                    c.drawLine(80 + j * 14, 640 - a * 40, 80 + j * 14, 640 + a * 40, stroke(6, 0xFF8FC8F0))
            out["hud"] = [wave]
            if i == 6:
                out["hud"].append(inset("sala", lambda c, tt: None, ease((lt) / .4), cam=(768, 500, 1.3)))
                out["shake"] = (math.sin(t * 40) * 2, 0)
    elif i <= 9:  # the screen
        out["bg"] = "pantalla"
        out["cam"] = Cam((768, 420, 1.0), (760, 400, 1.35), (t - L[7]["start"]) / (L[10]["start"] - L[7]["start"]))
        kt = (t - B["teclea"]) / 1.6
        kp = (t - B["pin"]) / .5
        ka = ease((t - B["tu_casa"]) / .3)
        out["over"] = [lambda c, tt, p: screen(c, tt, kt, kp, ka)]
        if i == 8:
            out["dark"] = .15 + .1 * math.sin(t * 3)
        if i == 9:
            hit = math.exp(-(t - B["tu_casa"]) * 4)
            out["shake"] = (random.Random(int(t * FPS)).uniform(-1, 1) * hit * 16, random.Random(int(t * FPS) + 7).uniform(-1, 1) * hit * 10)
    elif i <= 13:  # hide, don't hang up; she enters the closet; but you live alone
        out["cam"] = Cam((sx + 120, sy - 240, 1.7), (sx + 60, sy - 200, 1.3), k)
        out["dark"] = .3
        out["over"] = [monitor_glow(1.0)]
        talking = i == 10
        ch = you_seat(mouth=talk(t) if talking else "flat", arm_r=(2.7, 1.4), arm_l=(.9, 1.0) if talking else (-.1, .1),
                      eye=1.2 if i >= 12 else 1.0, brow=-.9 if i >= 12 else -.4, sweat=i == 13, look=(.8, -.3) if i < 12 else (-.6, 0))
        out["char"] = ch
        out["front"] = [lambda c, tt, p: headset(c, ch)]
        if i == 11:
            x0, y0, x1, y1 = g["armario"]["closet"]
            her = lambda c, tt: character(c, person(dict(t=tt, blink=0), HER, x=lerp(x0 - 160, (x0 + x1) / 2, ease(lt / 1.6)), y=g["armario"]["ground"], scale=.9,  # noqa: E731
                                                     walk=tt * 7 if lt < 1.6 else None, face=.4, look=(.6, 0), phone=True, arm_r=(2.6, 1.5), mouth="worry", brow=-1))
            out["hud"] = [inset("armario", lambda c, tt: (her(c, tt), closet_open(1 - ease((lt - 1.6) / .6) if lt > 1.6 else 1.0)(c, tt, None)),
                                ease(lt / .4), cam=(768, 500, 1.1))]
        if i == 13:
            out["hud"] = [inset("sala", lambda c, tt: None, ease(lt / .4), cam=(768, 500, 1.2)),
                          lambda c, tt, p: c.drawString("?", 1010, 245, font(110), fill(0xFFF2E21E))]
    elif i <= 16:  # the patrol, she can see him, the description
        out["cam"] = Cam((sx + 100, sy - 220, 1.4), (sx + 160, sy - 240, 1.6), k)
        out["dark"] = .3
        out["over"] = [monitor_glow(1.0)]
        ch = you_seat(mouth=talk(t) if i == 14 else "flat", arm_r=(2.7, 1.4), arm_l=(lerp(-.1, 1.4, ease(lt / .3)), 1.1) if i == 14 else (-.1, .1),
                      eye=1.15, brow=-.6, look=(.8, -.3))
        out["char"] = ch
        out["front"] = [lambda c, tt, p: headset(c, ch)]
        if i == 15:  # her eyes through the closet gap
            out["hud"] = [inset("armario", lambda c, tt: closet_open(.12, lambda cc, ttt: [cc.drawOval(skia.Rect.MakeXYWH(758 + s * 14, 420, 12, 8), fill(0xFFF0F0F0)) for s in (-1, 1)])(c, tt, None),
                                ease(lt / .4), cam=(768, 480, 1.6))]
        if i == 16:  # a figure in a dark uniform comes in from the kitchen and drops a gray backpack on the armchair
            kx, ky = g["sala"]["kitchen"]
            cx, cy = g["sala"]["chair"]
            drop = t >= B["mochila_cae"]
            walk_k = ease(min(1, lt / ((B["mochila_cae"] - L[16]["start"]) or 1)))

            def intruder(c, tt):
                x = lerp(kx, cx + 140, walk_k)
                character(c, person(dict(t=tt, blink=0), YOU, x=x, y=ky, scale=.95, back=True, walk=tt * 6 if not drop else None,
                                    arm_r=(1.2, .4) if not drop else (.1, .1)))
                if drop:
                    backpack(c, cx, cy - 40, .9)
                else:
                    backpack(c, x + 40, ky - 150, .8)
            out["hud"] = [inset("sala", intruder, ease(lt / .4), cam=(900, 520, 1.15))]
    elif i <= 18:  # you look at your gray backpack, then at your uniform
        bx, by = g["central"]["floor_bag"]
        out["over"] = [monitor_glow(1.0), lambda c, tt, p: backpack(c, bx, by, 1.0)]
        if i == 17:
            out["cam"] = Cam((sx - 40, sy - 160, 1.6), (bx + 30, by - 60, 2.6), ease(lt / 1.2))
            ch = you_seat(mouth="o", eye=1.35, brow=-1, look=(-.9, .8), face=-.3, arm_r=(2.7, 1.4))
        else:
            out["cam"] = Cam((sx, sy - 180, 2.0), (sx, sy - 160, 2.5), k)
            ch = you_seat(mouth="gasp", eye=1.4, brow=-1, look=(.2, 1), face=0, arm_l=(1.2, 1.3), arm_r=(1.0, 1.3), sweat=True)
        out["dark"] = .35
        out["char"] = ch
        out["front"] = [lambda c, tt, p: headset(c, ch)]
    elif i <= 20:  # running home; the patrol is already there
        out["bg"] = "calle"
        dx, dy = g["calle"]["door"]
        carx, cary = g["calle"]["car"]
        gy = g["calle"]["ground"]
        out["dark"] = .2
        out["over"] = [lambda c, tt, p: patrol(c, carx, cary, tt, lights=True)] if i == 20 else []
        if i == 19:
            out["cam"] = Cam((500, 520, 1.3), (dx, 520, 1.2), k)
            out["char"] = person(base, YOU, x=lerp(-60, dx - 120, k), y=gy, scale=.95, walk=t * 10, lean=8, face=.6, look=(1, 0), mouth="gasp", brow=-1, eye=1.2)
        else:
            out["cam"] = Cam((dx, 520, 1.2), ((dx + carx) / 2, 560, 1.35), k)
            out["char"] = person(base, YOU, x=dx - 120, y=gy, scale=.95, face=.7, look=(1, 0), mouth="o", brow=-1, eye=1.2, breath_amp=5, breath_rate=5)
    elif i <= 23:  # inside: everything as you left it
        out["bg"] = "sala"
        cx, cy = g["sala"]["chair"]
        mx, my = g["sala"]["mug"]
        photos = g["sala"]["photos"]
        gy = g["sala"]["ground"]
        out["over"] = [lambda c, tt, p: [portrait(c, x, y, YOU, 1.0, tt) for x, y in photos], lambda c, tt, p: mug(c, mx, my, 1.0)]
        if i == 21:
            out["cam"] = Cam((1100, 500, 1.3), (900, 480, 1.2), k)
            out["char"] = person(base, YOU, x=lerp(1500, 1080, ease(lt / 1.0)), y=gy, scale=.95, walk=t * 6 if lt < 1 else None, face=-.6, look=(-1, 0), mouth="flat")
        elif i == 22:
            out["cam"] = Cam((900, 470, 1.2), (600, 470, 1.15), k)
            out["char"] = person(base, YOU, x=1080, y=gy, scale=.95, face=-.6, look=(-1, -.2), mouth="flat", brow=-.4)
        else:  # mug, photos, armchair
            stops = [(mx, my - 40, 2.6), (photos[1][0], photos[1][1], 2.2), (cx, cy - 80, 2.0)]
            j = min(2, int(k * 3))
            out["cam"] = Cam(stops[j], stops[j], 0)
    elif i <= 26:  # the closet
        out["bg"] = "armario"
        x0, y0, x1, y1 = g["armario"]["closet"]
        gy = g["armario"]["ground"]
        kopen = ease((t - B["armario_abre"]) / .8)
        tremble = math.sin(t * 38) * 3

        def her_inside(c, tt):
            character(c, person(dict(t=tt, blink=0), HER, x=(x0 + x1) / 2 + tremble, y=y1 - 10, scale=.95, sit=True, face=.0, look=(0, 0),
                                phone=True, arm_r=(2.4, 1.6), mouth="worry", brow=-1, eye=1.3, sweat=True))
        out["over"] = [closet_open(kopen, her_inside if i >= 25 or kopen > .3 else None)]
        out["dark"] = .3
        if i == 24:
            out["cam"] = Cam((768, 480, 1.1), ((x0 + x1) / 2, 520, 1.3), k)
            out["char"] = person(base, YOU, x=lerp(260, x0 - 60, ease(lt / 1.0)), y=gy + 30, scale=1.0, walk=t * 6 if lt < 1 else None, face=.5,
                                 look=(1, 0), arm_r=(lerp(.1, 1.6, kopen), .3), mouth="flat")
        elif i == 25:
            out["cam"] = Cam(((x0 + x1) / 2, y1 - 180, 1.8), ((x0 + x1) / 2, y1 - 200, 2.1), k)
        else:  # she stares at you as if you were the intruder
            out["cam"] = Cam(((x0 + x1) / 2, y1 - 220, 2.4), ((x0 + x1) / 2, y1 - 220, 2.9), k)
            out["dark"] = .45
    elif i <= 31:  # police, her papers, the photos
        out["bg"] = "sala"
        photos = g["sala"]["photos"]
        gy = g["sala"]["ground"]
        swap = 1.0 if i >= 29 else 0.0  # from "su nombre está... en las fotos" on, every photo on the wall is hers
        mixed = i >= 29

        def wall(c, tt):
            for x, y in photos:
                if mixed:
                    portrait(c, x, y, YOU, 1 - swap, tt)
                    portrait(c, x, y, HER, swap, tt)
                else:
                    portrait(c, x, y, YOU, 1.0, tt)
        out["over"] = [lambda c, tt, p: wall(c, tt)]
        cops = [person(base, COP, x=900, y=gy, scale=.95, face=-.4, look=(-.5, .4), mouth="flat", arm_r=(1.4, 1.2), arm_l=(1.2, 1.2), blink=blink(t, .3)),
                person(base, COP, x=1120, y=gy + 10, scale=.97, face=-.5, look=(-.8, 0), mouth="flat", blink=blink(t, 1.7))]
        her = person(base, HER, x=640, y=gy + 4, scale=.92, face=.5, look=(.7, 0), mouth="flat", brow=-.3, blink=blink(t, .9))
        if i == 27:
            out["cam"] = Cam((800, 520, 1.2), (900, 520, 1.35), k)
            out["chars"] = cops + [her]
            out["hud"] = [paper(ease((t - B["papeles"]) / .5), "IDENTIFICACIÓN")]
        elif i == 28:
            out["cam"] = Cam((640, 480, 1.5), (640, 470, 1.7), k)
            out["chars"] = cops + [dict(her, tilt=6 * math.sin(lt * 6) if lt < 1 else 0)]
        elif i == 29:
            out["cam"] = Cam((photos[1][0], photos[1][1] + 40, 1.6), (photos[1][0], photos[1][1] + 60, 1.4), k)
            out["chars"] = [her]
            out["hud"] = [paper(ease(lt / .5), "CONTRATO", 8)]
        else:  # you look for your photos; they are gone
            you = person(base, YOU, x=380, y=gy + 10, scale=1.0, face=.5, look=(.6, -.9), mouth="o" if i == 31 else "flat", eye=1.3, brow=-1, sweat=i == 31,
                         arm_r=(lerp(.1, 2.4, ease(lt / .5)), .2) if i == 30 else (.1, .1))
            out["chars"] = [you] + ([] if i == 30 else cops[:1])
            out["cam"] = Cam((600, 450, 1.3), (photos[1][0], photos[1][1] + 30, 1.9), k) if i == 30 else Cam((photos[1][0], photos[1][1] + 30, 1.9), (photos[1][0], photos[1][1] + 30, 2.2), k)
    else:  # taken to the patrol; her phone rings; the voice that answers is yours
        out["bg"] = "calle"
        dx, dy = g["calle"]["door"]
        carx, cary = g["calle"]["car"]
        gy = g["calle"]["ground"]
        out["dark"] = .25
        out["over"] = [lambda c, tt, p: patrol(c, carx, cary, tt, lights=True)]
        walk_k = ease(min(1, (t - L[32]["start"]) / 3.5))
        x = lerp(dx - 40, carx - 260, walk_k)
        moving = walk_k < 1
        her = person(base, HER, x=dx + 110, y=gy - 6, scale=.9, face=-.4, look=(-.7, 0), phone=True, arm_r=(1.4, 1.2) if i == 32 else (2.6, 1.5), mouth="flat")
        out["chars"] = [person(base, COP, x=x - 110, y=gy + 6, scale=.97, walk=t * 6 if moving else None, face=.6, look=(1, 0)),
                        person(base, YOU, x=x, y=gy + 10, scale=.95, walk=t * 6 if moving else None, face=-.5, look=(-1, -.1), mouth="worry", brow=-1, arm_l=(.5, .3), arm_r=(.5, .3)),
                        person(base, COP, x=x + 110, y=gy + 4, scale=.97, walk=t * 6 if moving else None, face=.6, look=(1, 0)), her]
        out["over"].append(rings(dx + 160, gy - 190, 1.0 if t >= B["timbre_final"] and i == 32 else 0, t))
        if i == 32:
            out["cam"] = Cam((dx, 520, 1.2), ((dx + carx) / 2, 540, 1.15), k)
        else:
            out["cam"] = Cam((dx + 100, 500, 1.4), (dx + 120, 470, 1.6), k)

            def desk(c, tt):
                ch = person(dict(t=tt, blink=blink(tt)), YOU, x=sx, y=sy, scale=.95, sit=True, face=.6, look=(.8, -.3), arm_r=(2.7, 1.4),
                            mouth=talk(tt) if (i == 34 and tt >= B["contesta_final"]) else "flat")
                character(c, ch)
                headset(c, ch)
            out["hud"] = [inset("central", desk, ease(lt / .4) if i == 33 else 1.0, rect=(760, 60, 470, 290), cam=(sx + 100, sy - 200, lerp(1.3, 1.7, k) if i == 34 else 1.3))]
            if i == 34:
                out["fade"] = ease((k - .85) / .15) * .0
    return out


terminar(shots, LAYOUT, "llamada")
