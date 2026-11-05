"""Class 01: minion aggro. One concrete action per sentence. Run with render_env (see motor.py)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
from motor import (BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, back, badge, big_number, burst, caption, champ,  # noqa: E402
                   chalk_arrow, chalk_check, chalk_circle, chalk_cross, chalk_line, chalk_minion, chalk_stroke, clamp,
                   ease, keys, lerp, lock, minion, mix, pulse, ring, shot, sign, target_line)

M.setup(__file__, clase=1)
G = M.G
# The scenes were laid out on a diagonal lane; P() places them on the horizontal bot lane of the map
# (blue on the left, red on the right), next to where the river meets the lane.
O = (540, 1000)
N = (6000, G.lane_y("inferior", 6000))
_A = math.radians(51.5)


def P(x, y):
    dx, dy = x - O[0], y - O[1]
    return (N[0] + dx * math.cos(_A) - dy * math.sin(_A), N[1] + dx * math.sin(_A) + dy * math.cos(_A))


def C(x, y, z):
    return (*P(x, y), z)


YOU, RIVAL = P(380, 1200), P(700, 805)
BLUES = [(x + 75, y) for x, y in (P(445, 1120), P(488, 1172), P(400, 1080))]
REDS = [P(560, 990), P(612, 1040), P(515, 1035)]
CHARGED = [P(500, 1170), P(470, 1235), P(440, 1120)]  # red minions after charging at you
PURPLE = 0xFFB06CF0
TURRET = G.named_turret("rojo_inferior_exterior")


def fight(c, t, k_stop=0.0):
    """Both waves trading blows in the middle of the lane (they stop when k_stop -> 1)."""
    for j, (x, y) in enumerate(BLUES):
        minion(c, x, y, "azul", .8, t, swing=abs(math.sin(t * 6 + j * 1.7)) * (1 - k_stop) if j < 2 else 0)


def caitlyn(c, lt, b, k=1.0, flash=0.0, hp=1.0, pos=YOU, dead=0.0):
    champ(c, *pos, "Caitlyn", "azul", "TÚ", k, flash, hp, dead)


def draven(c, lt, b, k=1.0, flash=0.0, hp=1.0, dx=0.0):
    champ(c, RIVAL[0] + dx, RIVAL[1], "Draven", "rojo", "RIVAL", k, flash, hp)


# ---------------- classroom ----------------
@M.escena("hook", "aula", prof=[(0, "piensa"), ("repente", "asombro")],
          sfx=lambda b: [("tiza", .1), ("tiza", .7), ("ding", b.at("lanzó"))])
def hook(c, lt, b):
    chalk_line(c, "¿POR QUÉ TE PEGA", 540, 470, 88, (lt - .1) / .55)
    chalk_line(c, "TODA LA OLEADA?", 540, 610, 100, (lt - .7) / .55, CHALK_Y)
    k = ease((lt - b.at("lanzó")) / .5)
    for j, x in enumerate((230, 350, 470)):
        chalk_minion(c, x + 60 * k, 840, 1.0, CHALK_R, ease((lt - b.at("oleada") - j * .12) / .3))
    chalk_arrow(c, (560, 840), (720, 840), k)
    chalk_circle(c, 820, 840, 60, (lt - b.at("golpeaste")) / .4, CHALK_Y)
    chalk_line(c, "TÚ", 820, 860, 50, (lt - b.at("golpeaste") - .2) / .3, CHALK_Y)


@M.escena("nosuerte", "aula", prof=[(0, "explica"), ("explico", "guino")],
          sfx=lambda b: [("tiza", 0), ("tiza", b.at("regla")), ("ding", b.at("explico"))])
def nosuerte(c, lt, b):
    chalk_line(c, "MALA SUERTE", 540, 520, 100, lt / .5)
    chalk_stroke(c, [(220, 490), (860, 500)], (lt - b.at("es", 1)) / .3, CHALK_R, 12)
    chalk_line(c, "REGLA DEL JUEGO", 540, 760, 104, (lt - b.at("regla")) / .5, CHALK_Y)
    chalk_stroke(c, [(150, 800), (930, 795)], (lt - b.at("regla") - .5) / .3, CHALK_Y, 8)
    chalk_check(c, 540, 930, (lt - b.at("explico")) / .3, s=1.6)


@M.escena("cerebro", "aula", prof=[(0, "piensa"), ("lista", "explica")],
          sfx=lambda b: [("tiza", 0), ("tiza", b.at("lista"))])
def cerebro(c, lt, b):
    chalk_line(c, "EL CEREBRO DEL SÚBDITO", 540, 400, 72, lt / .6)
    k = ease((lt - .4) / .4)
    chalk_minion(c, 540, 700, 2.6, CHALK, k)
    # little brain over the helmet
    if k > 0:
        for j in range(6):
            a = math.pi + j * math.pi / 5
            chalk_circle(c, 540 + math.cos(a) * 52, 520 + math.sin(a) * 26, 26, (lt - b.at("cerebro") - j * .05) / .3, CHALK_R, 6)
    kp = (lt - b.at("chícharo")) / .3
    if kp > 0:
        c.drawCircle(720, 500, 16, M.fill(M.alpha(0xFF8EE08E, clamp(kp))))
        chalk_arrow(c, (850, 470), (750, 495), kp - .3, CHALK_Y, 6)
        chalk_line(c, "TAMAÑO REAL", 880, 455, 40, kp - .6, CHALK_Y)
    chalk_line(c, "= LISTA DE PRIORIDADES", 540, 950, 70, (lt - b.at("lista")) / .5, CHALK_Y)


ITEMS = [("p1", 0.0, ("CAMPEÓN QUE ATACA", "A SU CAMPEÓN")),
         ("p2", 0.0, ("SÚBDITO QUE ATACA", "A SU CAMPEÓN")),
         ("p3", "después", ("LO QUE ATACA", "A SUS SÚBDITOS")),
         ("p3", "final", ("LO MÁS CERCANO", ""))]


def item_start(n):
    bid, when, _ = ITEMS[n]
    b = next(x for x in M.S["beats"] if x.id == bid)
    return b.t0 + (b.at(when) if isinstance(when, str) else .15)


def priority_board(c, lt, b):
    t = b.t0 + lt
    chalk_line(c, "PRIORIDADES", 540, 380, 80, 1 if b.id != "p1" else lt / .5, CHALK_Y)
    for n, (_, _, (l1, l2)) in enumerate(ITEMS):
        t0 = item_start(n)
        if t < t0:
            continue
        y = 500 + n * 150
        cur = n == max(j for j in range(len(ITEMS)) if item_start(j) <= t)
        col = CHALK_Y if cur else CHALK
        if cur:
            hl = ease((t - t0) / .3)
            c.drawRoundRect(M.skia.Rect.MakeXYWH(95, y - 62, 890, 140 if l2 else 84), 20, 20, M.fill(M.alpha(0x30F2D35A, hl)))
        chalk_circle(c, 160, y + 10, 40, (t - t0) / .3, col, 6)
        chalk_line(c, str(n + 1), 160, y + 30, 58, (t - t0) / .2, col)
        chalk_line(c, l1, 230, y, 56, (t - t0 - .1) / .5, col, 740, "l")
        if l2:
            chalk_line(c, l2, 230, y + 62, 56, (t - t0 - .5) / .5, col, 740, "l")
    if b.id == "p1":
        badge(c, "LA MÁS ALTA", 860, 440, 30, RED, 0xFFFFFFFF, (lt - b.at("campeón")) / .3, rot=4)


for _id, _s in (("p1", [("tiza", .15)]), ("p2", [("tiza", .15)]), ("p3", None)):
    M.escena(_id, "aula", prof=[(0, "explica")],
             sfx=(lambda b, s=_s: s) if _s else (lambda b: [("tiza", b.at("después")), ("tiza", b.at("final"))]))(priority_board)


@M.escena("quiz", "aula", prof=[(0, "picara"), ("no", "asombro"), ("alarma", "explica")],
          sfx=lambda b: [("ding", 0), ("tiza", b.at("golpeas")), ("tiza", b.at("no")), ("tiza", b.at("alarma"))])
def quiz(c, lt, b):
    badge(c, "PREGUNTA RÁPIDA", 540, 380, 54, GOLD, M.INK, lt / .35, rot=-3)
    chalk_line(c, "¿GOLPEO UN SÚBDITO", 540, 530, 72, (lt - b.at("golpeas")) / .5)
    chalk_line(c, "Y ME ATACAN TODOS?", 540, 630, 72, (lt - b.at("atacan")) / .5)
    chalk_line(c, "NO NECESARIAMENTE", 540, 780, 78, (lt - b.at("no")) / .5, CHALK_R)
    chalk_line(c, "LA ALARMA: GOLPEAR", 540, 900, 64, (lt - b.at("alarma")) / .5, CHALK_Y)
    chalk_line(c, "A UN CAMPEÓN", 540, 990, 64, (lt - b.at("campeón")) / .4, CHALK_Y)


@M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), ("teemo", "feliz"), ("comentarios", "guino")],
          sfx=lambda b: [("tiza", 0), ("tiza", .7), ("ding", b.at("like")), ("puno", b.at("teemo") - .1),
                         ("teemo_muere", b.at("teemo") + .15), ("ding", b.at("comentarios"))])
def cierre(c, lt, b):
    chalk_line(c, "GOLPEAS AL CAMPEÓN", 540, 400, 76, lt / .5)
    chalk_arrow(c, (540, 440), (540, 520), (lt - .5) / .25)
    chalk_line(c, "TE ATACA LA OLEADA", 540, 610, 80, (lt - .7) / .5, CHALK_Y)
    badge(c, "1 LIKE = 1 PUÑETAZO", 540, 730, 46, GOLD, M.INK, (lt - b.at("like")) / .35, rot=-3)
    M.teemo_punch(c, lt, [b.at("teemo")], 720, 900, ease((lt - b.at("like")) / .4), b.t0 + lt)
    badge(c, "TE LEO EN COMENTARIOS", 300, 1010, 32, RED, 0xFFFFFFFF, (lt - b.at("comentarios")) / .35, rot=-2)


# ---------------- lane ----------------
@M.escena("golpe", "mapa", cam=lambda b: [(0, C(540, 1000, 1.0)), ("golpeas", C(540, 1010, 1.15))],
          sfx=lambda b: [("caitlyn_basico", b.at("golpeas") + .05), ("impacto", b.at("golpeas") + .35),
                         ("habilidad", b.at("habilidad")), ("habilidad_hit", b.at("habilidad") + .45)])
def golpe(c, lt, b):
    t = b.t0 + lt
    fight(c, t)
    for j, (x, y) in enumerate(REDS):
        minion(c, x, y, "rojo", -.8, t, swing=abs(math.sin(t * 6 + j * 1.3 + 1)) if j < 2 else 0)
    t1 = b.at("golpeas") + .05
    t2 = b.at("habilidad")
    shot(c, YOU, RIVAL, (lt - t1) / .3, "bala", BLUE)
    shot(c, YOU, RIVAL, (lt - t2) / .45, "habilidad", PURPLE)
    hit = max(pulse(lt, t1 + .3), pulse(lt, t2 + .45))
    caitlyn(c, lt, b, ease((lt + .1) / .4))
    draven(c, lt, b, ease(lt / .4), hit, 1 - .12 * ease((lt - t1 - .3) / .3) - .15 * ease((lt - t2 - .45) / .3),
           math.sin(t * 60) * 8 * hit)
    burst(c, RIVAL, pulse(lt, t1 + .3, 4))
    burst(c, RIVAL, pulse(lt, t2 + .45, 4), PURPLE, 90)
    badge(c, "ATAQUE BÁSICO", *P(330, 930), 38, BLUE, 0xFFFFFFFF, (lt - b.at("básico")) / .3)
    badge(c, "HABILIDAD DIRIGIDA", *P(640, 1250), 36, PURPLE, 0xFFFFFFFF, (lt - b.at("dirigida")) / .3)
    with b.hud(c):
        sign(c, t, lt / .5, "EL AGRO", "DE SÚBDITOS")


def red_charge(lt, start, j):
    """Position of red minion j when charging at you from `start`."""
    km = ease((lt - start) / .6)
    return mix(REDS[j], CHARGED[j], km), km


@M.escena("giran", "mapa", cam=lambda b: [(0, C(540, 1010, 1.15)), ("giran", C(500, 1080, 1.3))],
          sfx=lambda b: [("ding", b.at("giran"))] + [("golpe_subdito", b.at("giran") + .8 + j * .22) for j in range(5)])
def giran(c, lt, b):
    t = b.t0 + lt
    tg = b.at("giran")
    stop = ease((lt - b.at("dejan")) / .3)
    fight(c, t, stop)
    caitlyn(c, lt, b, flash=max(pulse(lt, tg + .8 + j * .22, 9) for j in range(5)),
            hp=1 - .25 * ease((lt - tg - .8) / 1.0))
    draven(c, lt, b, hp=.73)
    for j in range(3):
        (x, y), km = red_charge(lt, tg + .25, j)
        hop = -abs(math.sin((lt - tg) * 14 + j)) * 14 if 0 < km < 1 else 0
        face = -.8 if lt < tg else -1
        minion(c, x, y + hop, "rojo", face, t, swing=abs(math.sin(t * 7 + j)) * (km >= 1) + abs(math.sin(t * 6 + j)) * (1 - stop) * (j < 2))
        badge(c, "!", x, y - 75, 40, RED, 0xFFFFFFFF, ease((lt - tg - j * .06) / .25))
    with b.hud(c):
        sign(c, t, 1 - (lt - b.at("ti")) / .5 if lt > b.at("ti") else 1, "EL AGRO", "DE SÚBDITOS")
        caption(c, "…Y SUS SÚBDITOS VAN POR TI", (lt - tg) / .3, 0xFFFF6B74)


@M.escena("radio", "mapa", cam=lambda b: [(0, C(500, 1120, 1.3)), ("quinientas", C(480, 1150, 1.15))],
          sfx=lambda b: [("ding", b.at("quinientas"))])
def radio(c, lt, b):
    t = b.t0 + lt
    fight(c, t, 1)
    ring(c, CHARGED[0], 500 * M.UNIT, (lt - b.at("cerca")) / .4, RED, "≈ 500 UNIDADES" if lt > b.at("quinientas") else "¿QUÉ TAN CERCA?", t)
    caitlyn(c, lt, b, hp=.75)
    draven(c, lt, b, hp=.73)
    for j, (x, y) in enumerate(CHARGED):
        minion(c, x, y, "rojo", -1, t, swing=abs(math.sin(t * 7 + j)))


@M.escena("dano", "mapa", cam=lambda b: [(0, C(460, 1180, 1.6))],
          sfx=lambda b: [("golpe_subdito", b.at("pega") + .1), ("golpe_subdito", b.at("campeones") + .1), ("ding", b.at("sesenta"))])
def dano(c, lt, b):
    t = b.t0 + lt
    hits = [b.at("pega") + .1, b.at("campeones") + .1]
    caitlyn(c, lt, b, flash=max(pulse(lt, h, 9) for h in hits), hp=.75 - .03 * sum(lt > h for h in hits))
    x, y = CHARGED[0]
    sw = max(clamp(1 - abs(lt - h + .08) / .12) for h in hits)
    minion(c, x, y, "rojo", -1, t, swing=sw, s=1.15)
    badge(c, "POQUITO", x + 40, y - 95, 32, M.INK, 0xFFFFFFFF, (lt - b.at("poquito")) / .3)
    with b.hud(c):
        big_number(c, "60%", 300, 620, (lt - b.at("sesenta")) / .35)
        caption(c, "DE SU DAÑO CONTRA CAMPEONES", (lt - b.at("sesenta") - .2) / .3, GOLD, 760, 48)


SIX = [(YOU[0] + math.cos(a) * 125, YOU[1] + math.sin(a) * 105) for a in [-.4, .45, 1.3, 2.3, 3.4, 4.6]]


@M.escena("duele", "mapa", prof=lambda b: [(0, "puntero"), ("cruda", "asombro")],
          cam=lambda b: [(0, C(430, 1180, 1.35))],
          sfx=lambda b: [("golpe_subdito", b.at("pegan") + j * .17, 1.2) for j in range(int((b.at("cruda") - b.at("pegan")) / .17))]
          + [("impacto", b.at("cruda")), ("muerte", b.at("base"))])
def duele(c, lt, b):
    t = b.t0 + lt
    ts, td, tb = b.at("seis"), b.at("pegan"), b.at("base")
    hp = keys(lt, [(td, .72), (b.at("cruda"), .35), (b.at("vida"), .12), (tb, 0.0)])
    beating = td <= lt < tb
    for j, p in enumerate(SIX):
        start = CHARGED[j] if j < 3 else (RIVAL[0] - 60 + j * 20, RIVAL[1] + 120)
        k = ease((lt - ts + .4 - (j >= 3) * .1 * j) / .5) if j >= 3 else 1
        pos = mix(start, p, k if j >= 3 else ease(lt / .5))
        face = -1 if pos[0] > YOU[0] else 1
        minion(c, *pos, "rojo", face, t, swing=abs(math.sin(t * 11 + j * 1.1)) * beating, pop=clamp((lt - tb - .8) / .4) * 0)
    dead = ease((lt - tb) / .3)
    caitlyn(c, lt, b, flash=(abs(math.sin(t * 17)) * .7) if beating else 0, hp=hp, dead=dead)
    M.dizzy(c, YOU[0], YOU[1] - 150, ease((lt - b.at("cruda")) / .3) if lt < tb + .6 else 0, t)
    badge(c, "×6", YOU[0] + 150, YOU[1] - 150, 44, RED, 0xFFFFFFFF, (lt - ts) / .3)
    with b.hud(c):
        caption(c, "¡MÁS QUE LA CRUDA DEL LUNES!", (lt - b.at("cruda")) / .3, 0xFFFF6B74) if lt < tb else None
        caption(c, "…DIRECTO A LA BASE", (lt - tb) / .3, 0xFFFF6B74)


@M.escena("fijo", "mapa", cam=lambda b: [(0, C(540, 1060, 1.3))],
          sfx=lambda b: [("ding", b.at("eligen")), ("caitlyn_basico", b.at("aparece")), ("impacto", b.at("aparece") + .3),
                         ("ding", b.at("prioridad"))])
def fijo(c, lt, b):
    t = b.t0 + lt
    te, ta, tp = b.at("eligen"), b.at("aparece"), b.at("prioridad")
    red, blue = P(600, 1000), P(505, 1085)
    minion(c, *blue, "azul", .8, t, swing=abs(math.sin(t * 6)))
    switched = lt >= tp
    minion(c, *red, "rojo", -1, t, swing=abs(math.sin(t * 6 + 1)) * (not switched))
    caitlyn(c, lt, b, pos=keys(lt, [(0, P(300, 1300)), (ta - .2, P(390, 1190))]))
    draven(c, lt, b, flash=pulse(lt, ta + .3, 9), hp=.8)
    shot(c, P(390, 1190), RIVAL, (lt - ta) / .3, "bala", BLUE)
    if not switched:
        target_line(c, (red[0] - 30, red[1] + 10), (blue[0] + 25, blue[1] - 10), (lt - te) / .3, RED, t)
        lock(c, red[0], red[1] - 85, (lt - te) / .3)
    else:
        target_line(c, (red[0] - 30, red[1] + 10), P(430, 1160), (lt - tp) / .25, RED, t)
        badge(c, "PRIORIDAD 1", red[0] + 40, red[1] - 95, 32, RED, 0xFFFFFFFF, (lt - tp) / .3)
    with b.hud(c):
        caption(c, "OBJETIVO FIJO", (lt - te) / .3, GOLD) if not switched else caption(c, "SOLO CAMBIA POR MÁS PRIORIDAD", (lt - tp) / .3, 0xFFFF6B74)


@M.escena("reves", "mapa", prof=lambda b: [(0, "puntero"), ("echan", "feliz")], cam=lambda b: [(0, C(560, 1000, 1.15))],
          sfx=lambda b: [("draven_hacha", b.at("golpea")), ("draven_hit", b.at("golpea") + .45), ("ding", b.at("echan"))])
def reves(c, lt, b):
    t = b.t0 + lt
    tg, tl = b.at("golpea"), b.at("echan")
    for j, (x, y) in enumerate(REDS):
        minion(c, x, y, "rojo", -.8, t, swing=abs(math.sin(t * 6 + j)))
    for j, (x, y) in enumerate(BLUES):
        km = ease((lt - tl - .2) / .6)
        tx, ty = RIVAL[0] - 90 + j * 50, RIVAL[1] + 90 + (j - 1) * 30
        hop = -abs(math.sin((lt - tl) * 14 + j)) * 14 if 0 < km < 1 else 0
        minion(c, lerp(x, tx, km), lerp(y, ty, km) + hop, "azul", .9, t, swing=abs(math.sin(t * 8 + j)) * (km >= 1))
        badge(c, "!", lerp(x, tx, km), lerp(y, ty, km) - 75, 40, BLUE, 0xFFFFFFFF, ease((lt - tl - j * .06) / .25))
    shot(c, RIVAL, YOU, (lt - tg) / .45, "hacha")
    caitlyn(c, lt, b, flash=pulse(lt, tg + .45, 9), hp=1 - .15 * ease((lt - tg - .45) / .3))
    M.tamal(c, RIVAL[0], RIVAL[1] - 190, 1.0, (lt - b.at("tamales")) / .35, t)
    for j, (x, y) in enumerate(BLUES):
        M.heart(c, x + 20, y - 110 - ((t * 60 + j * 20) % 40), 18, ease((lt - b.at("tamales") - j * .1) / .3))
    draven(c, lt, b, flash=max(pulse(lt, tl + .85 + j * .25, 9) for j in range(4)), hp=1 - .3 * ease((lt - tl - .8) / 1.2))
    with b.hud(c):
        caption(c, "TE PEGA… Y TUS SÚBDITOS VAN POR ÉL", (lt - tl) / .3, BLUE) if lt < b.at("tías") else             caption(c, "COMO TÍAS A LOS TAMALES EN NAVIDAD", (lt - b.at("tías")) / .3, GOLD)


@M.escena("tip", "mapa", prof=lambda b: [(0, "puntero"), ("arriesgue", "guino")], cam=lambda b: [(0, C(560, 1020, 1.15))],
          sfx=lambda b: [("ding", b.at("pequeña")), ("draven_hacha", b.at("arriesgue")), ("ding", b.at("arriesgue") + .6)])
def tip(c, lt, b):
    t = b.t0 + lt
    tp, ta = b.at("pequeña"), b.at("arriesgue")
    blues = BLUES + [P(520, 1150)]
    for j, (x, y) in enumerate(blues):
        minion(c, x, y, "azul", .9, t, swing=abs(math.sin(t * 6 + j)) * (j < 2))
    minion(c, *REDS[0], "rojo", -.8, t, swing=abs(math.sin(t * 6)))
    badge(c, "4", *P(450, 1010), 40, BLUE, 0xFFFFFFFF, (lt - tp) / .3)
    badge(c, "1", REDS[0][0] + 60, REDS[0][1] - 80, 40, RED, 0xFFFFFFFF, (lt - tp) / .3)
    shot(c, RIVAL, YOU, (lt - ta) / .45, "hacha")
    caitlyn(c, lt, b, flash=pulse(lt, ta + .45, 9))
    draven(c, lt, b)
    with b.hud(c):
        if lt < ta:
            caption(c, "SU OLEADA ES PEQUEÑA → PELEA", (lt - tp) / .3, 0xFF8EE08E)
        else:
            caption(c, "QUE ÉL SE ARRIESGUE A PEGARTE", (lt - ta) / .3, GOLD)


@M.escena("torres", "mapa", prof=lambda b: [(0, "puntero"), ("próxima", "picara")],
          cam=lambda b: [(0, C(560, 1000, 1.15)), ("torres", (TURRET[0] - 120, TURRET[1] + 120, 1.1))],
          sfx=lambda b: [("torre_disparo", b.at("torres") + .3), ("ding", b.at("próxima"))])
def torres(c, lt, b):
    t = b.t0 + lt
    fight(c, t)
    for j, (x, y) in enumerate(REDS):
        minion(c, x, y, "rojo", -.8, t, swing=abs(math.sin(t * 6 + j)))
    caitlyn(c, lt, b)
    draven(c, lt, b)
    tt = b.at("torres")
    glow = pulse(lt, tt + .3, 2)
    if glow > 0:
        p = M.skia.Paint(AntiAlias=True, Color=M.alpha(RED, glow * .7), MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 40))
        c.drawCircle(TURRET[0], TURRET[1] - 190, 110, p)
    badge(c, "!", TURRET[0], TURRET[1] - 300, 50, RED, 0xFFFFFFFF, (lt - tt - .3) / .3)
    with b.hud(c):
        badge(c, "PRÓXIMA CLASE", 540, 1300, 52, GOLD, M.INK, (lt - b.at("próxima")) / .35, rot=-3)


if __name__ == "__main__":
    M.main()
