"""Sticks, Ideas propias: the gas station you keep coming back to. One visible action per sentence; positions are in
background pixels (layout.json of the episode overrides LAYOUT).
Usage: render_env/Scripts/python.exe escena_gasolinera.py <episode folder> [--stills ...] [--full] [--audio] [--short]"""
from palitos import *

LAYOUT = {
    "carretera": dict(light=0xFFA8B8D8, road=700),
    "letrero": dict(light=0xFFB8C4D8, sign=(480, 180, 1060, 520), road=800),
    "gasolinera": dict(light=0xFFB8E0C8, ground=790, pump=(720, 700), sign=(150, 160, 420, 300), door=(1230, 790)),
    "tienda": dict(light=0xFFC8E8C0, ground=800, counter_y=640, clerk=(900, 700), clock=(770, 230, 70), you=(520, 810)),
}
LAYOUT.update(json.loads((EP / "layout.json").read_text(encoding="utf-8")) if (EP / "layout.json").exists() else {})

YOU = dict(jacket=(0xFF3A5A7A, 0xFF2A4058), hair=0xFF2A1E18)
CLERK = dict(jacket=(0xFF5A6A54, 0xFF46523F), hair=0xFF9A9A9A, police_cap=True, cap_color=0xFFC0302A)
CAR_COLOR = 0xFF6C8FB0
RED, NEON = 0xFFE0302A, 0xFF6CFF9A
PLATE = "JKL-217"


# ---------------------------------------------------------------- props
def glow(c, x, y, rx, ry, color, alpha):
    p = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, rx * .9))
    p.setColor(skia.ColorSetARGB(int(max(0, min(1, alpha)) * 200), (color >> 16) & 255, (color >> 8) & 255, color & 255))
    c.drawOval(skia.Rect.MakeXYWH(x - rx * 2, y - ry * 2, rx * 4, ry * 4), p)


def car(c, x, y, t, s=1.0, direction=1, driver=True, lights=True, moving=True, sigh=0.0):
    """Side view of a small sedan; direction 1 faces right. The driver's head shows in the window."""
    c.save()
    c.translate(x, y)
    c.scale(s * direction, s)
    if lights:
        glow(c, 250, -60, 120, 40, 0xFFFFF0B0, .7)
        beam(c, 236, -62, 0, 520, 9, 70)
    body = poly([(-230, -30), (-224, -86), (-130, -98), (-80, -150), (80, -150), (140, -98), (232, -86), (236, -30)])
    c.drawPath(body, fill(CAR_COLOR))
    c.drawPath(body, stroke(6))
    for wx0, wx1 in ((-66, -6), (8, 74)):
        win = poly([(wx0, -102), (wx0 + 10, -140), (wx1, -140), (wx1 + 14, -102)])
        c.drawPath(win, fill(0xFF22303E))
        c.drawPath(win, stroke(4))
    if driver:  # driver's head in the front window
        c.save()
        c.clipPath(poly([(8, -102), (18, -140), (74, -140), (88, -102)]), doAntiAlias=True)
        character(c, dict(YOU, t=t, x=48, y=-48 + (6 * math.sin(t * 3) if sigh else 0), scale=.38, face=.8, look=(1, 0),
                          mouth="o" if sigh else "flat", blink=blink(t), eye=.7 if sigh else 1.0))
        c.restore()
    c.drawRect(skia.Rect.MakeXYWH(-232, -46, 468, 14), fill(0xFF4A5E74))
    spin = t * 14 if moving else 0
    for wx in (-140, 150):
        c.drawCircle(wx, -26, 34, fill(INK))
        c.drawCircle(wx, -26, 16, fill(0xFF9A9A9A))
        c.drawLine(wx, -26, wx + math.cos(spin) * 14, -26 + math.sin(spin) * 14, stroke(4))
    c.drawRect(skia.Rect.MakeXYWH(220, -78, 16, 12), fill(0xFFFFF0B0))
    c.drawRect(skia.Rect.MakeXYWH(-232, -78, 12, 12), fill(RED))
    c.restore()


def fit_font(s_, size, max_w):
    """Font at `size`, shrunk until `s_` fits in max_w."""
    f = font(int(size))
    w_ = f.measureText(s_)
    return f if w_ <= max_w else font(int(size * max_w / w_))


def sign_text(lines, k=1.0, shake=0.0):
    """Paints the roadside sign: GASOLINERA / 2 KM, in the blank board of the background."""
    def draw(c, t, paint):
        x0, y0, x1, y1 = LAYOUT["letrero"]["sign"]
        w, h = x1 - x0, y1 - y0
        c.save()
        c.translate(math.sin(t * 50) * shake * 4, 0)
        c.drawRect(skia.Rect.MakeLTRB(x0 + 8, y0 + 8, x1 - 8, y1 - 8), fill(0xFFE8E2CC))
        c.drawRect(skia.Rect.MakeLTRB(x0 + 8, y0 + 8, x1 - 8, y1 - 8), stroke(6))
        f1, f2 = fit_font(lines[0], h * .26, w * .84), fit_font(lines[1], h * .34, w * .6)
        a = int(255 * max(0, min(1, k)))
        for j, (s_, f, col) in enumerate(((lines[0], f1, 0xFF2A3A2A), (lines[1], f2, 0xFFB02A20))):
            c.drawString(s_, (x0 + x1) / 2 - f.measureText(s_) / 2, y0 + h * (.42 + j * .4), f, fill((a << 24) | (col & 0xFFFFFF)))
        ax = (x0 + x1) / 2 + f2.measureText(lines[1]) / 2 + 24  # arrow right after "2 KM"
        ay = y0 + h * .82 - h * .12
        c.drawPath(poly([(ax, ay - 22), (ax + 60, ay), (ax, ay + 22)], close=True), fill((a << 24) | 0xB02A20))
        c.restore()
    return draw


def neon(k_on, t):
    """Flickering neon on the station's blank sign board."""
    def draw(c, tt, paint):
        x0, y0, x1, y1 = LAYOUT["gasolinera"]["sign"]
        flick = 1.0 if (int(tt * 7) % 9) not in (2, 6) else .25
        a = max(0, min(1, k_on)) * flick
        s_ = "GAS 24 H"
        f = fit_font(s_, (y1 - y0) * .5, (x1 - x0) * .86)
        x = (x0 + x1) / 2 - f.measureText(s_) / 2
        y = (y0 + y1) / 2 + (y1 - y0) * .18
        glow(c, (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * .5, (y1 - y0) * .5, NEON, .6 * a)
        c.drawString(s_, x, y, f, stroke(10, skia.ColorSetARGB(int(255 * a), 30, 80, 50)))
        c.drawString(s_, x, y, f, fill(skia.ColorSetARGB(int(255 * a), 160, 255, 190)))
    return draw


def clock(c, k=1.0, zoom_hint=0, t=0.0, tick=False):
    """Wall clock stuck at 2:17 (painted over the blank clock face)."""
    cx, cy, r = LAYOUT["tienda"]["clock"]
    c.drawCircle(cx, cy, r, fill(0xFFF4F0E2))
    c.drawCircle(cx, cy, r, stroke(7))
    for j in range(12):
        a = j * math.pi / 6
        c.drawLine(cx + math.cos(a) * r * .8, cy + math.sin(a) * r * .8, cx + math.cos(a) * r * .92, cy + math.sin(a) * r * .92, stroke(4))
    hour = math.radians((2 + 17 / 60) * 30 - 90)
    minute = math.radians(17 * 6 - 90)
    sec = math.radians(((t * 6) if tick else 0) - 90 + 6 * 23)
    c.drawLine(cx, cy, cx + math.cos(hour) * r * .5, cy + math.sin(hour) * r * .5, stroke(8))
    c.drawLine(cx, cy, cx + math.cos(minute) * r * .75, cy + math.sin(minute) * r * .75, stroke(6))
    c.drawLine(cx, cy, cx + math.cos(sec) * r * .8, cy + math.sin(sec) * r * .8, stroke(3, RED))
    c.drawCircle(cx, cy, 6, fill(INK))


def ticket(c, x, y, s=1.0, rot=-12):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    r = skia.Rect.MakeXYWH(-26, -36, 52, 72)
    c.drawRect(r, fill(0xFFF6F2E4))
    c.drawRect(r, stroke(4))
    for j in range(5):
        c.drawLine(-16, -22 + j * 11, 14 - (j % 2) * 10, -22 + j * 11, stroke(3, 0xFF9A958A))
    c.drawString("2:17", -18, 30, font(16), fill(INK))
    c.restore()


def hose(c, pump, hand):
    p = skia.Path()
    px, py = pump
    p.moveTo(px + 45, py - 95)  # nozzle holder on the pump's right side (pump = base center)
    p.quadTo((px + 45 + hand[0]) / 2, max(py - 95, hand[1]) + 70, hand[0], hand[1])
    c.drawPath(p, stroke(10))


def bubble(text, x, y, k=1.0, think=False):
    def draw(c, t, paint):
        if k <= 0:
            return
        f = font(44)
        w = f.measureText(text) + 60
        c.save()
        c.translate(x, y)
        sc = lerp(.5, 1, ease(min(1, k)))
        c.scale(sc, sc)
        r = skia.Rect.MakeXYWH(-w / 2, -60, w, 90)
        c.drawRoundRect(r, 40, 40, fill(0xFFF8F6EE))
        c.drawRoundRect(r, 40, 40, stroke(5))
        if think:
            for j, (dx, dy, rr) in enumerate(((-30, 50, 12), (-50, 76, 8))):
                c.drawCircle(dx, dy, rr, fill(0xFFF8F6EE))
                c.drawCircle(dx, dy, rr, stroke(4))
        else:
            c.drawPath(poly([(-20, 28), (10, 28), (-30, 70)]), fill(0xFFF8F6EE))
        c.drawString(text, -w / 2 + 30, 2, f, fill(INK))
        c.restore()
    return draw


def gauge(k_needle, t):
    """HUD fuel gauge with the needle in the red."""
    def draw(c, tt, paint):
        x, y, r = W - 200, 200, 120
        c.drawCircle(x, y, r + 10, fill(0xEE101418))
        c.drawArc(skia.Rect.MakeXYWH(x - r, y - r, 2 * r, 2 * r), 200, 140, False, stroke(14, 0xFF3A4048))
        c.drawArc(skia.Rect.MakeXYWH(x - r, y - r, 2 * r, 2 * r), 200, 26, False, stroke(14, RED))
        a = math.radians(lerp(300, 206, ease(k_needle)) + math.sin(tt * 8) * 1.5)
        c.drawLine(x, y, x + math.cos(a) * r * .85, y + math.sin(a) * r * .85, stroke(7, 0xFFF2E6B8))
        c.drawString("E", x - r + 10, y + 20, font(36), fill(RED))
        c.drawString("F", x + r - 34, y + 20, font(36), fill(0xFFF2E6B8))
        if int(tt * 3) % 2:
            c.drawCircle(x, y + 50, 14, fill(RED))
    return draw


def hud_text(s_, k=1.0, y=120, size=72):
    def draw(c, t, paint):
        if k <= 0:
            return
        a = int(255 * min(1, k))
        c.drawString(s_, 60, y, font(size), stroke(10, (a << 24) | 0x101010))
        c.drawString(s_, 60, y, font(size), fill((a << 24) | 0xF2E6B8))
    return draw


def plates(k):
    def draw(c, t, paint):
        if k <= 0:
            return
        for j, x in enumerate((W / 2 - 260, W / 2 + 260)):
            c.save()
            c.translate(x, H / 2 - 60 + (1 - ease(min(1, k * 1.5 - j * .3))) * 500)
            r = skia.Rect.MakeXYWH(-200, -70, 400, 140)
            c.drawRoundRect(r, 16, 16, fill(0xFFF2F2EA))
            c.drawRoundRect(r, 16, 16, stroke(7))
            c.drawRect(skia.Rect.MakeXYWH(-200, -70, 400, 30), fill(0xFF2A4A9A))
            f = font(76)
            c.drawString(PLATE, -f.measureText(PLATE) / 2, 50, f, fill(INK))
            lbl = "TU COCHE" if j == 0 else "EL OTRO"
            c.drawString(lbl, -font(34).measureText(lbl) / 2, -90, font(34), fill(0xFFF2E6B8))
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
B["motor"] = beat("motor", [L[0]["start"], L[2]["start"]])
B["letrero1"] = beat("letrero1", L[2]["start"] + .2)
B["suspiro"] = beat("suspiro", L[3]["start"] + .1)
B["llega1"] = beat("llega1", [L[4]["start"], L[4]["end"]])
B["neon"] = beat("neon", L[5]["start"] + .3)
B["cobra"] = beat("cobra", mid(6, .6))
B["reloj1"] = beat("reloj1", L[7]["start"] + .2)
B["bomba"] = beat("bomba", [L[8]["start"] + .2, mid(8, .55)])
B["sale1"] = beat("sale1", mid(8, .75))
B["letrero2"] = beat("letrero2", L[10]["start"] + .1)
B["llega2"] = beat("llega2", L[12]["start"])
B["ticket"] = beat("ticket", L[14]["start"] + .4)
B["otra_vez"] = beat("otra_vez", mid(15, .7))
B["reloj2"] = beat("reloj2", L[16]["start"] + .2)
B["vuelta"] = beat("vuelta", mid(17, .4))
B["acelera"] = beat("acelera", [mid(17, .6), L[19]["start"]])
B["letrero3"] = beat("letrero3", L[19]["start"] + .1)
B["otro_coche"] = beat("otro_coche", L[20]["start"] + .3)
B["placas"] = beat("placas", L[21]["start"] + .2)
B["doble"] = beat("doble", L[22]["start"] + .4)
B["suspira_viejo"] = beat("suspira_viejo", L[23]["start"] + .3)
B["reloj3"] = beat("reloj3", L[25]["start"] + .2)


def shots(t):
    i, lt, k = linea(t)
    base = dict(t=t, blink=blink(t))
    g = LAYOUT
    out = dict(bg="carretera")
    if i <= 1 or i in (17, 18):  # driving on the desert highway
        road = g["carretera"]["road"]
        out["dark"] = .25
        if i <= 1:
            x = lerp(-300, BG_W + 300, (t - L[0]["start"]) / (L[2]["start"] - L[0]["start"]))
            out["cam"] = Cam((768, 432, 1.0), (x, road - 120, 1.6), ease((t - L[1]["start"]) / 1.2) if i == 1 else 0)
            out["over"] = [lambda c, tt, p: car(c, x, road, tt)]
            out["hud"] = [hud_text("2:00 A.M.", 1.0)] if i == 0 else [gauge(ease(lt / 1.5), t)]
        else:  # U-turn and flooring it the other way
            tv = B["vuelta"]
            if t < tv:
                x = lerp(500, 800, (t - L[17]["start"]) / max(.1, tv - L[17]["start"]))
                d = 1
            else:
                x = 800 - (t - tv) ** 1.6 * 520
                d = -1
            out["cam"] = Cam((x, road - 140, 1.3), (x, road - 140, 1.3), 0)
            out["over"] = [lambda c, tt, p: car(c, x, road, tt, direction=d)]
            if t > tv:
                out["over"].append(lambda c, tt, p: [c.drawLine(x + 250 + j * 60, road - 40 - j * 25, x + 420 + j * 90, road - 40 - j * 25, stroke(6, 0x88F2E6B8)) for j in range(4)])
                out["shake"] = (math.sin(t * 50) * 3, 0)
            if i == 18:
                out["hud"] = [hud_text("NO TE DETENGAS", ease(lt / .3), 140, 64)]
    elif i in (2, 3, 9, 10, 11, 19):  # the roadside sign
        out["bg"] = "letrero"
        x0, y0, x1, y1 = g["letrero"]["sign"]
        road = g["letrero"]["road"]
        cx = (x0 + x1) / 2
        ks = 1.0 if i not in (2, 9) else ease((t - (B["letrero1"] if i == 2 else L[9]["start"])) / .5)
        shake = .6 if i == 19 else 0
        out["over"] = [sign_text(("GASOLINERA", "2 KM"), ks if i != 9 else .0 + ks, shake)]
        out["dark"] = .2 if i != 19 else .45
        if i in (2, 3):
            out["cam"] = Cam((768, 432, 1.0), (cx, (y0 + y1) / 2 + 40, 1.3), k if i == 2 else 1)
            if i == 3:  # you breathe out, relieved, in the car passing under the sign
                xcar = lerp(200, 1300, lt / max(.5, L[3]["end"] - L[3]["start"]))
                out["over"].append(lambda c, tt, p: car(c, xcar, road, tt, sigh=1.0))
                out["cam"] = Cam((cx, (y0 + y1) / 2 + 120, 1.15), (cx, (y0 + y1) / 2 + 160, 1.25), k)
        elif i == 9:
            out["hud"] = [hud_text("20 MINUTOS DESPUÉS", ease(lt / .3), 130, 60)]
            out["cam"] = Cam((768, 432, 1.0), (cx, (y0 + y1) / 2 + 40, 1.2), k)
        elif i == 10:
            out["cam"] = Cam((cx, (y0 + y1) / 2, 1.3), (cx, (y0 + y1) / 2, 1.6), k)
        elif i == 11:  # "debe ser otra": thought bubble from the car
            xcar = lerp(300, 900, k)
            out["over"].append(lambda c, tt, p: car(c, xcar, road, tt))
            out["cam"] = Cam((cx, (y0 + y1) / 2 + 140, 1.15), (cx, (y0 + y1) / 2 + 140, 1.2), k)
            out["hud"] = [bubble("¿OTRA?", W / 2 + 180, H / 2 + 80, ease(lt / .3), think=True)]
        else:  # 19: the same sign again, the world shakes
            out["cam"] = Cam((cx, (y0 + y1) / 2, 1.1), (cx, (y0 + y1) / 2, 1.9), ease(lt / 1.2))
            out["shake"] = (random.Random(int(t * FPS)).uniform(-6, 6), random.Random(int(t * FPS) + 3).uniform(-4, 4))
    elif i in (4, 5, 8, 12, 13, 14, 20, 21, 22):  # the gas station
        out["bg"] = "gasolinera"
        px, py = g["gasolinera"]["pump"]
        gy = g["gasolinera"]["ground"]
        out["dark"] = .2
        out["over"] = [neon(1.0, t)]
        stop_x = px - 330
        if i == 4 or i == 12:
            t0 = L[i]["start"]
            xc = lerp(-300, stop_x, ease((t - t0) / 1.6))
            out["over"].append(lambda c, tt, p: car(c, xc, gy, tt, moving=t - t0 < 1.6))
            out["cam"] = Cam((768, 432, 1.0), (768, 450, 1.05), k)
            if i == 12:
                out["hud"] = [hud_text("LA MISMA", ease((lt - .6) / .3), 140, 70)]
        elif i == 5 or i == 13:
            out["over"].append(lambda c, tt, p: car(c, stop_x, gy, tt, moving=False, lights=False))
            x0, y0, x1, y1 = g["gasolinera"]["sign"]
            out["cam"] = Cam((px, py - 200, 1.4), ((x0 + x1) / 2, (y0 + y1) / 2 + 80, 1.6), ease((lt - .6) / 1.2))
        elif i == 8:  # fill up, ticket into the pocket, back to the road
            tb0, tb1 = B["bomba"]
            leave = B["sale1"]
            tank = (stop_x + 160, gy - 100)
            you_x = stop_x + 235
            filling = tb0 <= t < tb1

            def scene8(c, tt, p):
                if t < leave:
                    car(c, stop_x, gy, tt, moving=False, lights=False, driver=False)
                    ch = person(dict(t=tt, blink=blink(tt)), YOU, x=you_x, y=gy, scale=.95, face=-.6, look=(-1, .1),
                                arm_r=(1.5, .3) if filling else (lerp(1.5, .2, ease((t - tb1) / .4)), 1.6), mouth="flat")
                    character(c, ch)
                    if filling:
                        hose(c, (px, py), tank)
                    elif t < tb1 + .5:
                        ticket(c, *ch.get("hand", (you_x + 40, gy - 150)), .9)
                else:
                    car(c, lerp(stop_x, BG_W + 300, ease((t - leave) / 1.4)), gy, tt)
            out["over"].append(scene8)
            out["cam"] = Cam((px - 150, py - 200, 1.5), (px - 150, py - 220, 1.4), k)
        elif i == 14:  # your ticket on the floor next to the pump
            out["over"].append(lambda c, tt, p: car(c, stop_x, gy, tt, moving=False, lights=False))
            out["over"].append(lambda c, tt, p: ticket(c, px - 60, gy - 10, 1.0, -30))
            out["cam"] = Cam((px - 40, gy - 120, 1.5), (px - 60, gy - 30, 3.2), ease((t - B["ticket"]) / 1.0))
        else:  # 20-22: another car at the pump, same plate, someone in your clothes filling it
            other_x = px - 330
            mine_x = 260

            def scene_double(c, tt, p):
                car(c, other_x, gy, tt, moving=False, lights=False, driver=False)
                car(c, mine_x, gy + 30, tt, moving=False, lights=True, driver=i < 22)
                if i == 22:
                    ch = person(dict(t=tt, blink=0), YOU, x=other_x + 235, y=gy, scale=.95, back=True, arm_r=(1.5, .3))
                    character(c, ch)
                    hose(c, (px, py), (other_x + 160, gy - 100))
                    me = person(dict(t=tt, blink=blink(tt)), YOU, x=mine_x + 200, y=gy + 30, scale=.95, face=.7, look=(1, 0),
                                mouth="gasp", eye=1.4, brow=-1, sweat=True)
                    character(c, me)
            out["over"].append(scene_double)
            if i == 20:
                out["cam"] = Cam((768, 432, 1.0), (other_x, gy - 160, 1.4), k)
            elif i == 21:
                out["cam"] = Cam((other_x, gy - 160, 1.4), (other_x, gy - 140, 1.5), k)
                out["hud"] = [plates(ease((t - B["placas"]) / .6))]
            else:
                out["cam"] = Cam((px - 300, gy - 200, 1.2), (px - 120, gy - 230, 1.8), ease(lt / 2.0))
                out["dark"] = .35
    else:  # the store: the clerk with the red cap, the clock at 2:17
        out["bg"] = "tienda"
        gy = g["tienda"]["ground"]
        clx, cly = g["tienda"]["clerk"]
        yx, yy = g["tienda"]["you"]
        cx, cy, r = g["tienda"]["clock"]
        out["dark"] = .15
        tick = i in (7,)
        out["over"] = [lambda c, tt, p: clock(c, 1.0, t=tt, tick=tick)]
        clerk = person(base, CLERK, x=clx, y=cly, scale=.95, face=-.6, look=(-1, .1), mouth="flat", blink=blink(t, .6))
        you = person(base, YOU, x=yx, y=yy, scale=1.0, face=.6, look=(1, -.1), mouth="flat")
        if i == 6:  # he charges you without a word
            kc = ease((t - B["cobra"]) / .5)
            clerk.update(arm_r=(lerp(.1, 1.5, kc), .4))
            you.update(arm_r=(lerp(.1, 1.4, ease((lt - .3) / .5)), .3))
            out["chars"] = [you, clerk]
            out["cam"] = Cam(((yx + clx) / 2, 470, 1.25), ((yx + clx) / 2, 480, 1.35), k)
        elif i == 7 or i == 16 or i == 25:  # the clock
            out["chars"] = [you, clerk]
            z = {7: 2.4, 16: 3.0, 25: 3.6}[i]
            out["cam"] = Cam(((yx + clx) / 2, 470, 1.25), (cx, cy + 10, z), ease(lt / (1.0 if i != 25 else 2.5)))
            if i == 25:
                out["dark"] = .15 + .4 * ease(k)
        elif i == 15:  # "otra vez tú"
            kl = ease((t - L[15]["start"]) / .6)
            clerk.update(look=(-1, lerp(.6, -.1, kl)), brow=-.4, mouth=talk(t) if t >= B["otra_vez"] else "flat")
            you.update(eye=1.3, brow=-.8, mouth="o")
            out["chars"] = [you, clerk]
            out["cam"] = Cam(((yx + clx) / 2, 470, 1.3), (clx - 60, cly - 220, 1.9), k)
            out["hud"] = [bubble("Otra vez tú.", W / 2 + 160, 200, ease((t - B["otra_vez"]) / .3))]
        else:  # 23-24: he sighs; "ya van muchas vueltas esta noche"
            sigh = i == 23
            clerk.update(eye=.35 if sigh else 1.0, mouth="o" if sigh else talk(t), tilt=-8 if sigh else 0, breath_amp=8 if sigh else 2)
            you.update(eye=1.35, brow=-1, mouth="gasp", sweat=True)
            out["chars"] = [you, clerk]
            out["cam"] = Cam((clx - 40, cly - 220, 1.8), (clx - 40, cly - 230, 2.0), k) if sigh else Cam(((yx + clx) / 2, 470, 1.35), ((yx + clx) / 2, 470, 1.45), k)
            if not sigh:
                out["hud"] = [bubble("Ya van muchas vueltas esta noche.", W / 2, 200, ease(lt / .3))]
    return out


terminar(shots, LAYOUT, "gasolinera")
