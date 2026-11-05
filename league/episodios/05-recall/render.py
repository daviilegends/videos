"""Class 05: recall. 0.5 s cast + 8 s channel; damage cancels it (not if a shield absorbs it, not in the final 0.1 s);
stuns, silences, knock-ups, roots and Flash cancel it; Empowered Recall 4 s."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
from motor import (BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, chalk_line, chalk_stroke, clamp,  # noqa: E402
                   ease, keys, pulse)

M.setup(__file__, clase=5)
G = M.G
X0 = 5300
LY = G.lane_y("inferior", X0)
YOU = (X0, LY)
ENEMY = (X0 + 430, LY - 30)
CAM = (X0 + 150, LY - 60, 1.25)
SAFE = (X0 - 250, LY - 470)  # in the jungle, behind the trees


def cait(c, pos=YOU, flash=0.0, hp=1.0, k=1.0, a=1.0):
    champ(c, *pos, "Caitlyn", "azul", "TÚ", k, flash, hp, s=.85, a=a)


def draven(c, pos=ENEMY, flash=0.0):
    champ(c, *pos, "Draven", "rojo", "RIVAL", 1, flash, 1.0, s=.85)


def recall(c, lt, t, t0, pos=YOU, cancel_at=None, length=8.5, done_at=None):
    """Draws the recall channel started at t0; returns progress."""
    if lt < t0:
        return 0
    k = clamp((lt - t0) / length)
    if cancel_at is not None and lt >= cancel_at:
        k = clamp((cancel_at - t0) / length)
        M.recall_fx(c, *pos, k, t, cancel=clamp((lt - cancel_at) / .5))
        badge(c, "CANCELADO", pos[0], pos[1] - 160, 34, RED, 0xFFFFFFFF, (lt - cancel_at) / .3)
        return k
    M.recall_fx(c, *pos, k, t)
    return k


def axe(c, lt, tf, a=ENEMY, b=YOU):
    M.shot(c, a, b, (lt - tf) / .45, "hacha")


def chalk_bar(c, x, y, w, k, color=0xFF6FC3FF):
    c.drawRect(M.skia.Rect.MakeXYWH(x, y, w, 60), M.stroke(7, CHALK))
    if k > 0:
        c.drawRect(M.skia.Rect.MakeXYWH(x + 6, y + 6, (w - 12) * clamp(k), 48), M.fill(M.alpha(color, .7)))


# ---------------- classroom ----------------
def hook_extra(c, lt, b):
    k = clamp((lt - .3) / 1.6) * .97
    chalk_bar(c, 190, 820, 700, k)
    if lt > b.at("último"):
        chalk_stroke(c, [(830, 800), (800, 850), (850, 870), (815, 920)], (lt - b.at("último")) / .3, CHALK_R, 9)
        chalk_line(c, "¡NOOO!", 540, 1010, 70, (lt - b.at("último") - .2) / .3, CHALK_R)


M.pizarra("hook", [("¿TE CORTARON", 540, 450, 96, CHALK, .1), ("EL RECALL?", 540, 600, 110, CHALK_Y, "recall")],
          prof=[(0, "piensa"), ("último", "asombro")], extra=hook_extra)


def total_extra(c, lt, b):
    chalk_bar(c, 190, 820, 700, clamp((lt - b.at("total")) / 1.5))


M.pizarra("total", [("0.5 s + 8 s", 540, 500, 110, CHALK, 0), ("= 8.5 SEGUNDOS", 540, 660, 96, CHALK_Y, "total"),
                    ("UNA ETERNIDAD", 540, 1000, 60, CHALK_R, "eternidad")], prof=[(0, "explica"), ("eternidad", "asombro")], extra=total_extra)


def ejemplo_extra(c, lt, b):
    tz = b.at("cero")
    k = clamp((lt - .2) / 1.4) * .7 if lt < tz else 0
    chalk_bar(c, 190, 820, 700, k)
    M.chalk_arrow(c, (700, 990), (260, 990), (lt - tz) / .4, CHALK_R)


M.pizarra("ejemplo", [("UN GOLPE", 540, 460, 100, CHALK, "golpe"), ("= DESDE CERO", 540, 620, 100, CHALK_R, "cero")],
          prof=[(0, "explica")], extra=ejemplo_extra)


def cc_extra(c, lt, b):
    for j, key in enumerate(("aturdimientos", "silencios", "derribos", "enraizamientos")):
        M.chalk_cross(c, 160, 470 + j * 140 - 25, (lt - b.at(key) - .3) / .3, s=.7)


M.pizarra("cc", [("ATURDIMIENTO", 250, 470, 76, CHALK, "aturdimientos", .4, "l"), ("SILENCIO", 250, 610, 76, CHALK, "silencios", .4, "l"),
                 ("DERRIBO", 250, 750, 76, CHALK, "derribos", .4, "l"), ("ENRAIZAMIENTO", 250, 890, 76, CHALK, "enraizamientos", .4, "l")],
          prof=[(0, "explica")], extra=cc_extra)
M.pizarra("cc2", [("SIN CONTROL", 540, 540, 110, CHALK, "control"), ("= SIN RECALL", 540, 720, 110, CHALK_R, "recall")],
          prof=[(0, "explica"), ("recall", "picara")])


def mejorado_extra(c, lt, b):
    chalk_line(c, "NORMAL", 260, 760, 50, (lt - .3) / .3, CHALK, 300)
    chalk_bar(c, 390, 715, 500, clamp((lt - .3) / 3.0))
    chalk_line(c, "MEJORADO", 260, 900, 46, (lt - b.at("mejorado")) / .3, CHALK_Y, 300)
    chalk_bar(c, 390, 855, 500, clamp((lt - b.at("mejorado")) / 1.5), 0xFFF2D35A)


M.pizarra("mejorado", [("RECALL MEJORADO", 540, 450, 84, CHALK_Y, "mejorado"), ("SOLO 4 s", 540, 590, 96, CHALK, "cuatro")],
          prof=[(0, "explica"), ("cuatro", "feliz")], extra=mejorado_extra)
M.pizarra("tip2", [("¿TE LO CORTARON?", 540, 500, 90, CHALK, "cortaron"), ("CAMBIA DE LUGAR", 540, 680, 96, CHALK_Y, "mismo")],
          prof=[(0, "explica"), ("mismo", "guino")])


@M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), ("teemo", "feliz")],
          sfx=lambda b: [("tiza", 0), ("ding", b.at("like")), ("recall", b.at("like") + .2, .5), ("puno", b.at("último") - .05),
                         ("teemo_muere", b.at("último") + .2)])
def cierre(c, lt, b):
    chalk_line(c, "8.5 s · DAÑO = CANCELA", 540, 420, 64, lt / .5)
    chalk_line(c, "ESCUDO Y ÚLTIMA DÉCIMA = SIGUE", 540, 520, 56, (lt - .6) / .5, CHALK_Y)
    badge(c, "1 LIKE = 1 RECALL CORTADO", 540, 650, 44, GOLD, M.INK, (lt - b.at("like")) / .35, rot=-3)
    tl = b.at("último")
    k = clamp((lt - b.at("like")) / max(.5, tl - b.at("like"))) * .97
    if lt < tl:
        M.recall_fx(c, 720, 880, k, b.t0 + lt)
    M.teemo_punch(c, lt, [tl], 720, 880, ease((lt - b.at("like")) / .4), b.t0 + lt)


# ---------------- lane ----------------
@M.escena("dur", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("recall", b.at("medio"))])
def dur(c, lt, b):
    t = b.t0 + lt
    t0 = b.at("medio")
    recall(c, lt, t, t0)
    cait(c)
    badge(c, "0.5 s", YOU[0] - 190, YOU[1] - 120, 34, GOLD, M.INK, (lt - b.at("medio")) / .3)
    badge(c, "+ 8 s", YOU[0] + 190, YOU[1] - 120, 34, BLUE, 0xFFFFFFFF, (lt - b.at("ocho")) / .3)
    with b.hud(c):
        M.sign(c, t, lt / .5, "EL RECALL", "Y SUS ENEMIGOS")
        caption(c, "MEDIO SEGUNDO + 8 DE CANALIZACIÓN", (lt - b.at("canalización")) / .3, 0xFF6FC3FF)


@M.escena("broma", "mapa", prof=lambda b: [(0, "puntero"), ("tres", "asombro")], cam=lambda b: [(0, (YOU[0], YOU[1] - 60, 1.55))],
          sfx=lambda b: [("recall", .1, .6)])
def broma(c, lt, b):
    t = b.t0 + lt
    k = recall(c, lt, t, -2.0, length=14)
    cait(c, hp=.03)
    for j in range(2):  # sweat drops
        y = YOU[1] - 60 + ((t * 80 + j * 40) % 70)
        c.drawCircle(YOU[0] + 85 + j * 15, y, 9, M.fill(0xFF9AD0F5))
    with b.hud(c):
        caption(c, "…CON 3 DE VIDA", (lt - b.at("tres")) / .3, 0xFFFF6B74)


@M.escena("dano", "mapa", prof=lambda b: [(0, "puntero"), ("cancela", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("recall", 0, .5), ("draven_hacha", b.at("daño") - .3), ("draven_hit", b.at("daño") + .15)])
def dano(c, lt, b):
    t = b.t0 + lt
    th = b.at("daño") + .15
    recall(c, lt, t, -1.5, cancel_at=th)
    axe(c, lt, th - .45)
    cait(c, flash=pulse(lt, th, 9), hp=1 - .12 * ease((lt - th) / .3))
    draven(c)
    with b.hud(c):
        caption(c, "DAÑO = SE CANCELA", (lt - b.at("cancela")) / .3, 0xFFFF6B74)


def shield(c, pos, k, t):
    if k <= 0:
        return
    c.drawCircle(*pos, 110 * M.back(k), M.fill(M.alpha(0xFFFFE27A, .25 * k)))
    c.drawCircle(*pos, 110 * M.back(k), M.stroke(7, M.alpha(0xFFFFE27A, k)))


@M.escena("escudo", "mapa", prof=lambda b: [(0, "puntero"), ("sigue", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("recall", 0, .5), ("draven_hacha", b.at("absorbe") - .3), ("ding", b.at("absorbe") + .15)])
def escudo(c, lt, b):
    t = b.t0 + lt
    th = b.at("absorbe") + .15
    recall(c, lt, t, -2.5)
    shield(c, YOU, ease((lt - b.at("escudo")) / .3) * (1 - ease((lt - th - .3) / .3)), t)
    axe(c, lt, th - .45)
    M.burst(c, YOU, pulse(lt, th, 4), 0xFFFFE27A, 110)
    cait(c)
    draven(c)
    with b.hud(c):
        caption(c, "ESCUDO ABSORBE = EL RECALL SIGUE", (lt - b.at("sigue")) / .3, GOLD)


@M.escena("final", "mapa", prof=lambda b: [(0, "puntero"), ("cancela", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("draven_hacha", b.at("última") - .3), ("recall_llega", b.at("última") + .2)])
def final(c, lt, b):
    t = b.t0 + lt
    tend = b.at("última") + .15
    k = recall(c, lt, t, tend - 8.5) if lt < tend else 1
    axe(c, lt, tend - .45)
    gone = ease((lt - tend) / .4)
    if gone > 0:
        p = M.skia.Paint(AntiAlias=True, Color=M.alpha(0xFF6FC3FF, (1 - gone)), MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 40))
        c.drawCircle(*YOU, 160, p)
    cait(c, a=1 - gone)
    draven(c)
    badge(c, "ÚLTIMA DÉCIMA", YOU[0], YOU[1] - 170, 34, GOLD, M.INK, (lt - b.at("décima")) / .3)
    with b.hud(c):
        caption(c, "EN LA ÚLTIMA DÉCIMA YA NO SE CORTA", (lt - b.at("cancela")) / .3, 0xFF8EE08E)


@M.escena("flash", "mapa", prof=lambda b: [(0, "puntero"), ("cancela", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("recall", 0, .5), ("flash", b.at("flash"))])
def flash(c, lt, b):
    t = b.t0 + lt
    tf = b.at("flash")
    dest = (YOU[0] - 60, YOU[1] - 230)
    recall(c, lt, t, -3, cancel_at=tf)
    M.flash_fx(c, YOU, dest, lt - tf)
    cait(c, pos=YOU if lt < tf else dest)
    badge(c, "FLASH", dest[0], dest[1] - 150, 34, 0xFFFFE27A, M.INK, (lt - tf) / .3)
    with b.hud(c):
        caption(c, "FLASH A MEDIO RECALL = CANCELADO", (lt - b.at("cancela")) / .3, 0xFFFF6B74)


BRUSH_HIDE = (X0 + 380, LY + 300)


@M.escena("rival", "mapa", prof=lambda b: [(0, "puntero"), ("pegarte", "asombro")], cam=lambda b: [(0, (X0 + 200, LY + 60, 1.15))],
          sfx=lambda b: [("recall", b.at("empieces") - .2, .5), ("draven_hacha", b.at("pegarte") + .1), ("draven_hit", b.at("pegarte") + .55)])
def rival(c, lt, b):
    t = b.t0 + lt
    tp = b.at("pegarte") + .55
    recall(c, lt, t, b.at("empieces") - .2, cancel_at=tp)
    dp = keys(lt, [(0, BRUSH_HIDE), (tp - .6, BRUSH_HIDE), (tp - .2, (BRUSH_HIDE[0] - 120, BRUSH_HIDE[1] - 150))])
    champ(c, *dp, "Draven", "rojo", "RIVAL", 1, 0, 1, s=.85, a=.45 if lt < tp - .6 else 1)
    axe(c, lt, tp - .45, dp, YOU)
    cait(c, flash=pulse(lt, tp, 9), hp=1 - .2 * ease((lt - tp) / .3))
    with b.hud(c):
        caption(c, "TE ESPERAN… Y TE PEGAN", (lt - b.at("esperan")) / .3, 0xFFFF6B74)


@M.escena("tip", "mapa", prof=lambda b: [(0, "puntero"), ("arbusto", "guino")], cam=lambda b: [(0, (SAFE[0] + 200, SAFE[1] + 200, 1.15))],
          sfx=lambda b: [("recall", b.at("fuera"), .5)])
def tip(c, lt, b):
    t = b.t0 + lt
    pos = keys(lt, [(0, YOU), (b.at("fuera") - .2, SAFE)])
    recall(c, lt, t, b.at("fuera"), pos=SAFE)
    cait(c, pos=pos)
    badge(c, "A SALVO", SAFE[0], SAFE[1] - 160, 34, 0xFF8EE08E, M.INK, (lt - b.at("muro")) / .3)
    with b.hud(c):
        caption(c, "RECALL FUERA DE SU VISTA", (lt - b.at("fuera")) / .3, 0xFF8EE08E)


@M.escena("broma2", "mapa", prof=lambda b: [(0, "picara")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("recall", 0, .5), ("ding", b.at("invisible"))])
def broma2(c, lt, b):
    t = b.t0 + lt
    recall(c, lt, t, -1)
    cait(c)
    draven(c)
    k = ease((lt - b.at("medio")) / .3)
    if k > 0:
        M.chalk_cross(c, YOU[0], YOU[1], k, RED, 2.6)
    with b.hud(c):
        caption(c, "¿RECALL EN MEDIO DE LA LÍNEA? NO", (lt - b.at("medio")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
