"""Class 03: how many turret shots each minion takes (melee 45%, caster 70%, siege 14%, super 5% of max health)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
from motor import (BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, big_number, burst, caption, champ, chalk_arrow,  # noqa: E402
                   chalk_circle, chalk_line, chalk_minion, chalk_stroke, clamp, ease, minion, pulse, shot)

M.setup(__file__, clase=3)
G = M.G
T = G.named_turret("azul_inferior_exterior")  # OUR turret: enemy minions come from the right
TOP = (T[0], T[1] - 190)
CAM = (T[0] + 260, T[1] - 20, 1.45)
SPOT = (T[0] + 330, T[1] + 30)       # where the enemy minion stands under our turret
YOU = (T[0] - 40, T[1] + 150)        # Caitlyn waiting for the last hit
ORO = 0xFFFFD34D


def caitlyn(c, k=1.0, flash=0.0):
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", k, flash, 1.0, s=.85)


def tshots(c, lt, fires, target, dur=.32):
    for tf in fires:
        shot(c, TOP, target, (lt - tf) / dur, "torre", BLUE)
        burst(c, target, pulse(lt, tf + dur, 5), 0xFF9AD0F5, 50)


def victim(c, lt, t, kind, fires, pct, pos=SPOT, extra=(), s=1.0):
    """Red minion under fire: each turret shot removes `pct`; extra = ((time, damage), ...) for your own hits."""
    events = sorted([(f + .32, pct) for f in fires] + list(extra))
    hp, dead_at, acc = 1.0, None, 0.0
    for h, d in events:
        acc += d
        if acc >= .999 and dead_at is None:
            dead_at = h
        if lt > h:
            hp -= d
    hp = max(0.0, hp)
    pop = clamp((lt - dead_at) / .45) if dead_at is not None else 0
    fl = max([pulse(lt, h, 10) for h, _ in events] + [0])
    minion(c, *pos, "rojo", -1, t, kind=kind, flash=fl, pop=pop, s=s)
    if pop < 1:
        M.minion_hp(c, pos[0], pos[1] - (30 if kind in ("canon", "super") else 0), hp, 1.0 if kind != "super" else 1.4)
    return hp, dead_at


def gold_pop(c, x, y, k):
    if k <= 0 or k > 1.6:
        return
    a = 1 - max(0, (k - 1) / .6)
    c.save()
    c.translate(x, y - 90 - 80 * ease(k))
    c.drawCircle(0, 0, 26, M.fill(M.alpha(ORO, a)))
    c.drawCircle(0, 0, 26, M.stroke(5, M.alpha(M.INK, a)))
    M.text(c, "+ORO", 70, 12, M.font("segoeuib.ttf", 34), M.alpha(ORO, a), 8, M.alpha(M.INK, a))
    c.restore()


def chalk_turret(c, x, y, s, k, color=CHALK):
    chalk_stroke(c, [(x - 40 * s, y), (x - 28 * s, y - 140 * s), (x + 28 * s, y - 140 * s), (x + 40 * s, y), (x - 40 * s, y)], k, color, 7)
    chalk_stroke(c, [(x, y - 215 * s), (x + 24 * s, y - 175 * s), (x, y - 145 * s), (x - 24 * s, y - 175 * s), (x, y - 215 * s)], k * 1.3 - .3, color, 7)


# ---------------- classroom ----------------
def hook_extra(c, lt, b):
    k = (lt - b.at("contar")) / .3
    for j in range(3):
        chalk_line(c, f"{j + 1}…", 300 + j * 240, 900, 110, k - j * .4, CHALK_Y)


M.pizarra("hook", [("¿POR QUÉ PIERDES", 540, 470, 84, CHALK, .1), ("SÚBDITOS BAJO", 540, 590, 84, CHALK, .6),
                   ("TU TORRE?", 540, 720, 104, CHALK_Y, 1.1)],
          prof=[(0, "piensa"), ("parado", "asombro"), ("contar", "picara")], extra=hook_extra)


def regla_extra(c, lt, b):
    k = ease((lt - b.at("vida")) / .5)
    if k > 0:
        c.drawRect(M.skia.Rect.MakeXYWH(190, 820, 700, 70), M.stroke(7, CHALK))
        c.drawRect(M.skia.Rect.MakeXYWH(190, 820, 700 * (1 - .35 * k), 70), M.fill(M.alpha(0x664CD07A, 1)))
        chalk_stroke(c, [(190 + 700 * .65, 800), (190 + 700 * .65, 910)], k, CHALK_R, 8)
        chalk_line(c, "-%", 190 + 700 * .82, 875, 60, k, CHALK_R)


M.pizarra("regla", [("CADA DISPARO", 540, 450, 84, CHALK, 0), ("= % FIJO DE SU", 540, 580, 80, CHALK_Y, "porcentaje"),
                    ("VIDA MÁXIMA", 540, 700, 80, CHALK_Y, "vida")], prof=[(0, "explica")], extra=regla_extra)


def simetria_extra(c, lt, b):
    chalk_turret(c, 300, 880, 1.2, (lt - .2) / .6, 0xFF9AD0F5)
    chalk_line(c, "=", 540, 780, 140, (lt - b.at("misma")) / .3, CHALK_Y)
    chalk_turret(c, 780, 880, 1.2, (lt - b.at("rival")) / .6, CHALK_R)


M.pizarra("simetria", [("TU TORRE Y LA DEL RIVAL", 540, 430, 66, CHALK, 0)], prof=[(0, "explica")], extra=simetria_extra)


def resumen_extra(c, lt, b):
    for j, (name, n, key) in enumerate((("MELEE", "3", "melee"), ("MAGO", "2", "mago"), ("CAÑÓN", "8", "cañón"), ("SÚPER", "20", "súper"))):
        k = (lt - b.at(key)) / .4
        y = 520 + j * 130
        chalk_line(c, name, 180, y, 70, k, CHALK, 500, "l")
        chalk_line(c, n, 780, y, 90, k - .3, CHALK_Y)
        chalk_stroke(c, [(560, y - 25), (690, y - 25)], k - .2, CHALK, 6)


M.pizarra("resumen", [("DISPAROS PARA MORIR", 540, 400, 64, CHALK_Y, 0)], prof=[(0, "explica")], extra=resumen_extra)


def porque_extra(c, lt, b):
    k = ease((lt - b.at("oro")) / .4)
    for j in range(5):
        c.drawCircle(300 + j * 120, 880 - 40 * math.sin(j), 40 * k, M.fill(M.alpha(ORO, k)))
        c.drawCircle(300 + j * 120, 880 - 40 * math.sin(j), 40 * k, M.stroke(6, M.alpha(M.INK, k)))
    M.chalk_cross(c, 540, 870, (lt - b.at("pierde")) / .4, s=3.2)


M.pizarra("porque", [("SÚBDITO QUE SE ESCAPA", 540, 480, 70, CHALK, .2), ("= ORO PERDIDO", 540, 620, 90, CHALK_R, "oro")],
          prof=[(0, "explica"), ("pierde", "asombro")], extra=porque_extra, sfx_extra=lambda b: [("oro", b.at("oro"))])


@M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), ("teemo", "feliz"), ("cañón", "guino")],
          sfx=lambda b: [("tiza", 0), ("ding", b.at("like")), ("torre_disparo", b.at("teemo") - .3), ("puno", b.at("teemo") - .05),
                         ("teemo_muere", b.at("cañón"))])
def cierre(c, lt, b):
    chalk_line(c, "MELEE 3 · MAGO 2", 540, 420, 70, lt / .5)
    chalk_line(c, "CAÑÓN 8 · SÚPER 20", 540, 530, 70, (lt - .5) / .5, CHALK_Y)
    badge(c, "1 LIKE = 1 DISPARO DE TORRE", 540, 680, 44, GOLD, M.INK, (lt - b.at("like")) / .35, rot=-3)
    M.teemo_punch(c, lt, [b.at("teemo"), b.at("cañón")], 720, 880, ease((lt - b.at("like")) / .4), b.t0 + lt)


# ---------------- lane, under our turret ----------------
def base(c, b, lt):
    t = b.t0 + lt
    caitlyn(c)
    return t


@M.escena("melee", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [(s, f + d) for f in (b.at("quita"), b.at("quita") + .9, b.at("tres")) for s, d in (("torre_a_subdito", 0), ("torre_subdito_hit", .32))]
          + [("subdito_muere", b.at("tres") + .35)])
def melee(c, lt, b):
    t = base(c, b, lt)
    fires = [b.at("quita"), b.at("quita") + .9, b.at("tres")]
    victim(c, lt, t, "melee", fires, .45)
    tshots(c, lt, fires, SPOT)
    with b.hud(c):
        M.sign(c, t, lt / .5, "DISPAROS DE TORRE", "VS SÚBDITOS")
        big_number(c, "45%", 300, 620, (lt - b.at("cuarenta")) / .35, RED)
        caption(c, "MELEE: 3 DISPAROS", (lt - b.at("tres")) / .3, GOLD)


@M.escena("truco_melee", "mapa", prof=lambda b: [(0, "puntero"), ("golpe", "guino")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_a_subdito", .1), ("torre_a_subdito", 1.0), ("caitlyn_basico", b.at("golpe") - .3), ("oro", b.at("golpe"))])
def truco_melee(c, lt, b):
    t = base(c, b, lt)
    tg = b.at("golpe")
    fires = [.1, 1.0]
    victim(c, lt, t, "melee", fires, .45, extra=((tg, .1),))
    tshots(c, lt, fires, SPOT)
    shot(c, YOU, SPOT, (lt - tg + .3) / .3, "bala", BLUE)
    gold_pop(c, *SPOT, (lt - tg) / .6)
    badge(c, "10%", SPOT[0] + 90, SPOT[1] - 95, 34, RED, 0xFFFFFFFF, (lt - b.at("diez")) / .3)
    with b.hud(c):
        caption(c, "2 DISPAROS + TU GOLPE", (lt - b.at("golpe")) / .3, 0xFF8EE08E)


@M.escena("mago", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [(s, f + d) for f in (b.at("quita"), b.at("dos")) for s, d in (("torre_a_subdito", 0), ("torre_subdito_hit", .32))]
          + [("subdito_muere", b.at("dos") + .35)])
def mago(c, lt, b):
    t = base(c, b, lt)
    fires = [b.at("quita"), b.at("dos")]
    victim(c, lt, t, "mago", fires, .70)
    tshots(c, lt, fires, SPOT)
    with b.hud(c):
        big_number(c, "70%", 300, 620, (lt - b.at("setenta")) / .35, RED)
        caption(c, "MAGO: 2 DISPAROS", (lt - b.at("dos")) / .3, GOLD)


@M.escena("truco_mago", "mapa", prof=lambda b: [(0, "puntero"), ("lleva", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_a_subdito", .1), ("torre_a_subdito", b.at("lleva") - .3), ("subdito_muere", b.at("lleva"))])
def truco_mago(c, lt, b):
    t = base(c, b, lt)
    fires = [.1, b.at("lleva") - .3]
    victim(c, lt, t, "mago", fires, .70)
    tshots(c, lt, fires, SPOT)
    badge(c, "30%", SPOT[0] + 90, SPOT[1] - 95, 34, RED, 0xFFFFFFFF, (lt - b.at("treinta")) / .3)
    badge(c, "SIN ORO", YOU[0], YOU[1] - 150, 34, RED, 0xFFFFFFFF, (lt - b.at("lleva")) / .3)
    with b.hud(c):
        caption(c, "…Y LA TORRE SE LO LLEVA", (lt - b.at("lleva")) / .3, 0xFFFF6B74)


@M.escena("orden", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_a_subdito", b.at("primero")), ("ding", b.at("primero"))])
def orden(c, lt, b):
    t = base(c, b, lt)
    k1 = ease(lt / 1.2)
    k2 = ease((lt - .4) / 1.2)
    p1 = (SPOT[0] + 400 * (1 - k1), SPOT[1])
    p2 = (SPOT[0] + 120 + 400 * (1 - k2), SPOT[1] + 90)
    minion(c, *p2, "rojo", -1, t, kind="mago")
    minion(c, *p1, "rojo", -1, t)
    tp = b.at("primero")
    if lt > tp:
        M.target_line(c, (TOP[0] + 20, TOP[1] + 40), p1, (lt - tp) / .3, BLUE, t)
        badge(c, "1º EN ENTRAR", p1[0], p1[1] - 110, 32, BLUE, 0xFFFFFFFF, (lt - tp) / .3)
    tshots(c, lt, [tp], p1)
    with b.hud(c):
        caption(c, "DISPARA AL PRIMERO QUE ENTRA", (lt - tp) / .3, BLUE)


@M.escena("canon", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_a_subdito", b.at("cada") + j * .45, .7) for j in range(8)])
def canon(c, lt, b):
    t = base(c, b, lt)
    fires = [b.at("cada") + j * .45 for j in range(8)]
    hp, _ = victim(c, lt, t, "canon", fires[:7], .14)  # stays alive on screen with 2% left
    tshots(c, lt, fires[:7], SPOT)
    n = sum(lt > f for f in fires[:7])
    badge(c, f"{n}/8", SPOT[0] + 110, SPOT[1] - 130, 36, M.INK, 0xFFFFFFFF, 1 if n else 0)
    with b.hud(c):
        big_number(c, "14%", 300, 620, (lt - b.at("catorce")) / .35, RED)
        caption(c, "CAÑÓN: 8 DISPAROS", (lt - b.at("ocho")) / .3, GOLD)


def party_hat(c, x, y, k):
    if k <= 0:
        return
    hat = M.path([(x - 26, y), (x, y - 70 * k), (x + 26, y)])
    c.drawPath(hat, M.fill(0xFFB06CF0))
    c.drawPath(hat, M.stroke(5))
    c.drawCircle(x, y - 70 * k, 10, M.fill(0xFFFFE27A))


@M.escena("broma", "mapa", prof=lambda b: [(0, "picara")], cam=lambda b: [(0, (SPOT[0] - 40, SPOT[1] - 60, 1.5))],
          sfx=lambda b: [("ding", b.at("fiesta"))])
def broma(c, lt, b):
    t = base(c, b, lt)
    minion(c, *SPOT, "rojo", -1, t, kind="canon", swing=abs(math.sin(t * 5)) * .5)
    M.minion_hp(c, SPOT[0], SPOT[1] - 30, .02)
    party_hat(c, SPOT[0] - 5, SPOT[1] - 70, ease((lt - b.at("fiesta")) / .3))
    for j in range(14):  # confetti
        k = (lt - b.at("fiesta") - j * .05)
        if k > 0:
            x = SPOT[0] - 260 + (j * 97) % 520
            y = SPOT[1] - 300 + (k * 220) % 420
            c.drawRect(M.skia.Rect.MakeXYWH(x, y, 16, 10), M.fill([0xFFFFE27A, 0xFFE84855, 0xFF3FA9F5, 0xFF8EE08E][j % 4]))
    with b.hud(c):
        caption(c, "EL TÍO QUE NO SE VA DE LA FIESTA", (lt - b.at("tío")) / .3, GOLD)


@M.escena("super", "mapa", prof=lambda b: [(0, "puntero"), ("despeina", "picara")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_a_subdito", .2 + j * .45, .6) for j in range(int(max(1, (b.dur - .6) / .45)))])
def super_(c, lt, b):
    t = base(c, b, lt)
    fires = [.2 + j * .45 for j in range(int(max(1, (b.dur - .6) / .45)))]
    victim(c, lt, t, "super", fires, .05, pos=(SPOT[0] + 20, SPOT[1] - 10))
    tshots(c, lt, fires, (SPOT[0] + 20, SPOT[1] - 40))
    with b.hud(c):
        big_number(c, "5%", 300, 620, (lt - b.at("cinco")) / .35, RED)
        caption(c, "SÚPER: 20 DISPAROS", (lt - b.at("veinte")) / .3, GOLD) if lt < b.at("despeina") else \
            caption(c, "…Y NI SE DESPEINA", (lt - b.at("despeina")) / .3, 0xFFB06CF0)


@M.escena("tip", "mapa", prof=lambda b: [(0, "puntero"), ("último", "guino")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_a_subdito", b.at("trabaje") - .4), ("torre_a_subdito", b.at("trabaje") + .5),
                         ("caitlyn_basico", b.at("último") - .3), ("oro", b.at("último"))])
def tip(c, lt, b):
    t = base(c, b, lt)
    tl = b.at("último")
    fires = [b.at("trabaje") - .4, b.at("trabaje") + .5]
    victim(c, lt, t, "melee", fires, .45, extra=((tl, .1),))
    tshots(c, lt, fires, SPOT)
    shot(c, YOU, SPOT, (lt - tl + .3) / .3, "bala", BLUE)
    gold_pop(c, *SPOT, (lt - tl) / .6)
    badge(c, "ESPERA…", YOU[0], YOU[1] - 150, 34, GOLD, M.INK, (lt - b.at("pegues")) / .3 if lt < tl - .3 else 0)
    with b.hud(c):
        caption(c, "LA TORRE TRABAJA, TÚ REMATAS", (lt - b.at("trabaje")) / .3, 0xFF8EE08E)


@M.escena("tip2", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_a_subdito", .2), ("caitlyn_basico", b.at("golpe") - .3), ("oro", b.at("golpe"))])
def tip2(c, lt, b):
    t = base(c, b, lt)
    tg = b.at("golpe")
    victim(c, lt, t, "mago", [.2], .70, extra=((tg, .3),))
    tshots(c, lt, [.2], SPOT)
    shot(c, YOU, SPOT, (lt - tg + .3) / .3, "bala", BLUE)
    gold_pop(c, *SPOT, (lt - tg) / .6)
    badge(c, "30%", SPOT[0] + 90, SPOT[1] - 95, 34, RED, 0xFFFFFFFF, .9 if .6 < lt < tg else 0)
    with b.hud(c):
        caption(c, "SI NO ALCANZA: TU GOLPE ANTES", (lt - b.at("alcanza")) / .3, GOLD)


if __name__ == "__main__":
    M.main()
