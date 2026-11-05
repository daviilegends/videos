"""Class 10: turret plates (5 per outer turret, 120 local gold each, last hit/assist within 10 s, Bulwark)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=10)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, minion, pulse, shot  # noqa: E402

T = M.G.named_turret("rojo_inferior_exterior")
TOP = (T[0], T[1] - 190)
CAM = (T[0] - 280, T[1] - 20, 1.2)
YOU = (T[0] - 330, T[1] + 60)
ALLY = (T[0] - 480, T[1] - 80)
FAR = (T[0] - 1100, T[1] + 40)


def turret_bar(c, lt, plates, flash=-1, k=1.0):
    K.plated_bar(c, T[0], T[1] - 320, 300, plates, k, flash)


def hits(c, lt, times, src=YOU):
    for tf in times:
        shot(c, src, (T[0] - 20, T[1] - 80), (lt - tf) / .25, "bala", BLUE)
        M.burst(c, (T[0], T[1] - 100), pulse(lt, tf + .25, 5), 0xFFFFE27A, 60)


def cait(c, pos=YOU, flash=0.0):
    champ(c, *pos, "Caitlyn", "azul", "TÚ", 1, flash, 1, s=.8)


# ---------------- classroom
def hook_extra(c, lt, b):
    k = ease((lt - b.at("alcancía")) / .4)
    if k > 0:
        c.drawRoundRect(M.skia.Rect.MakeXYWH(420, 760, 240, 180), 60, 60, M.fill(M.alpha(0xFFF0A0B8, k)))
        c.drawRoundRect(M.skia.Rect.MakeXYWH(420, 760, 240, 180), 60, 60, M.stroke(7))
        c.drawRect(M.skia.Rect.MakeXYWH(510, 760, 60, 10), M.fill(M.INK))
        for j in range(3):
            K.coin_pop(c, 540 + (j - 1) * 70, 760, (lt - b.at("oro") - j * .2) * .8)


M.pizarra("hook", [("LA TORRE DEL RIVAL", 540, 450, 80, CHALK, .1), ("= ALCANCÍA", 540, 590, 110, CHALK_Y, "alcancía")],
          prof=[(0, "picara"), ("oro", "feliz")], extra=hook_extra, sfx_extra=lambda b: [("oro", b.at("oro"))])
M.pizarra("spoiler", [("NO ES BROMA", 540, 520, 100, CHALK, 0), ("HOY LE SACAMOS EL ORO", 540, 680, 70, CHALK_Y, "oro")],
          prof=[(0, "guino")])
M.pizarra("cuenta", [("5 PLACAS", 540, 470, 100, CHALK, "cinco"), ("× 120 ORO", 540, 600, 100, CHALK, "ciento"),
                     ("= 600 ORO", 540, 780, 130, CHALK_Y, "seiscientos")], prof=[(0, "explica"), ("seiscientos", "feliz")],
          sfx_extra=lambda b: [("oro", b.at("seiscientos"))])
M.pizarra("cada_torre", [("POR CADA TORRE", 540, 480, 96, CHALK, 0), ("× 3 LÍNEAS", 540, 640, 120, CHALK_Y, "tres"),
                         ("HAZ CUENTAS", 540, 820, 76, CHALK_R, "cuentas")], prof=[(0, "explica"), ("cuentas", "guino")])


def broma_extra(c, lt, b):
    for j in range(4):
        k = (lt - b.at("billetes") - j * .15) / .3
        if k > 0:
            c.save()
            c.translate(300 + j * 160, 860 - 30 * math.sin(j))
            c.rotate(-10 + j * 8)
            c.drawRect(M.skia.Rect.MakeXYWH(-60, -30, 120, 60), M.fill(0xFF8EC68E))
            c.drawRect(M.skia.Rect.MakeXYWH(-60, -30, 120, 60), M.stroke(5))
            M.text(c, "$", 0, 18, M.font("segoeuib.ttf", 44), 0xFF2A5A2A)
            c.restore()


M.pizarra("broma", [("BILLETES EN LA", 540, 470, 90, CHALK, "billetes"), ("CHAMARRA VIEJA", 540, 600, 90, CHALK_Y, "chamarra")],
          prof=[(0, "feliz")], extra=broma_extra)
M.pizarra("bulwark2", [("MÁS PLACAS ROTAS", 540, 500, 90, CHALK, 0), ("= TORRE MÁS DURA", 540, 660, 90, CHALK_R, "trabajo")],
          prof=[(0, "explica")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("PLACAS A TIEMPO", 540, 600, 96, 0xFF8EE08E, "placas"),
                  ("> PELEA PERDIDA", 540, 760, 96, CHALK_R, "pelea")], prof=[(0, "explica"), ("pelea", "guino")])
K.cierre_teemo("5 PLACAS · 120 ORO CADA UNA", "ORO LOCAL: SOLO LOS QUE ESTÁN CERCA", "1 LIKE = 1 PLACA MENOS")


# ---------------- lane
@M.escena("placas", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("placas"))])
def placas(c, lt, b):
    t = b.t0 + lt
    turret_bar(c, lt, 5, k=(lt - b.at("placas")) / .3)
    cait(c)
    with b.hud(c):
        M.sign(c, t, lt / .5, "LAS PLACAS", "DE LA TORRE")


@M.escena("cinco", "mapa", cam=lambda b: [(0, (T[0] - 60, T[1] - 260, 1.8))], sfx=lambda b: [("tiza", b.at("cinco"))])
def cinco(c, lt, b):
    turret_bar(c, lt, 5)
    for j in range(5):
        badge(c, str(j + 1), T[0] - 120 + j * 60, T[1] - 360, 26, GOLD, M.INK, (lt - b.at("cinco") - j * .15) / .25)
    with b.hud(c):
        caption(c, "5 PLACAS = 5 REBANADAS", (lt - b.at("rebanadas")) / .3, GOLD)


@M.escena("oro", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("caitlyn_basico", b.at("destruyes") + j * .5) for j in range(3)] + [("oro", b.at("ciento"))])
def oro(c, lt, b):
    hs = [b.at("destruyes") + j * .5 for j in range(3)]
    broke = lt > b.at("ciento")
    turret_bar(c, lt, 4 if broke else 5, flash=4 if 0 < lt - b.at("ciento") < .2 else -1)
    hits(c, lt, hs)
    cait(c)
    K.coin_pop(c, YOU[0], YOU[1] - 120, lt - b.at("ciento"), 120)
    with b.hud(c):
        caption(c, "1 PLACA = 120 DE ORO", (lt - b.at("ciento")) / .3, K.ORO)


@M.escena("local", "mapa", prof=lambda b: [(0, "puntero"), ("cerca", "explica")], cam=lambda b: [(0, (T[0] - 520, T[1] - 20, .95))],
          sfx=lambda b: [("oro", b.at("cerca"))])
def local(c, lt, b):
    t = b.t0 + lt
    M.ring(c, (T[0] - 250, T[1]), 520, (lt - b.at("local")) / .4, BLUE, "CERCA", t)
    turret_bar(c, lt, 4)
    cait(c)
    champ(c, *ALLY, "Jinx", "azul", None, 1, 0, 1, s=.75)
    champ(c, *FAR, "Ashe", "azul", None, 1, 0, 1, s=.75)
    K.coin_pop(c, YOU[0], YOU[1] - 120, lt - b.at("cerca"))
    K.coin_pop(c, ALLY[0], ALLY[1] - 120, lt - b.at("cerca"))
    badge(c, "NADA", FAR[0], FAR[1] - 140, 30, RED, 0xFFFFFFFF, (lt - b.at("cerca") - .3) / .3)
    with b.hud(c):
        caption(c, "ORO LOCAL: SOLO LOS CERCANOS", (lt - b.at("local")) / .3, BLUE)


@M.escena("remate", "mapa", cam=lambda b: [(0, (T[0] - 520, T[1] - 20, .95))],
          sfx=lambda b: [("jinx_basico", b.at("golpe") - .3), ("oro", b.at("diez"))])
def remate(c, lt, b):
    t = b.t0 + lt
    turret_bar(c, lt, 4 if lt < b.at("golpe") else 3)
    hits(c, lt, [b.at("golpe") - .3], FAR)
    champ(c, *FAR, "Jinx", "azul", None, 1, 0, 1, s=.75)
    cait(c)
    K.coin_pop(c, FAR[0], FAR[1] - 120, lt - b.at("diez"), 120)
    badge(c, "10 s", FAR[0] + 150, FAR[1] - 150, 32, GOLD, M.INK, (lt - b.at("diez")) / .3)
    with b.hud(c):
        caption(c, "GOLPE O AYUDA EN 10 s: TAMBIÉN TE TOCA", (lt - b.at("diez")) / .3, GOLD)


def shield(c, k, t):
    if k <= 0:
        return
    c.drawCircle(TOP[0], TOP[1] + 60, 150 * k, M.fill(M.alpha(0x339AD0F5, 1)))
    c.drawCircle(TOP[0], TOP[1] + 60, 150 * k, M.stroke(8, M.alpha(0xFF9AD0F5, k)))


@M.escena("bulwark", "mapa", prof=lambda b: [(0, "puntero"), ("resistente", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("caitlyn_basico", .3 + j * .6) for j in range(4)] + [("ding", b.at("resistente"))])
def bulwark(c, lt, b):
    t = b.t0 + lt
    n = max(1, 3 - int(max(0, lt - .5) / 1.2))
    shield(c, ease((lt - b.at("resistente")) / .5), t)
    turret_bar(c, lt, n)
    hits(c, lt, [.3 + j * .6 for j in range(4)])
    cait(c)
    with b.hud(c):
        caption(c, "PIERDE PLACAS → SE VUELVE MÁS RESISTENTE", (lt - b.at("resistente")) / .3, 0xFF9AD0F5)


@M.escena("cuando", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("recall_llega", b.at("regresó"))])
def cuando(c, lt, b):
    t = b.t0 + lt
    gone = ease((lt - b.at("regresó")) / .5)
    champ(c, T[0] - 60, T[1] + 160, "Draven", "rojo", "RIVAL", 1, 0, 1, s=.75, a=1 - gone)
    turret_bar(c, lt, 3)
    cait(c)
    badge(c, "RIVAL EN BASE", T[0] - 60, T[1] + 40, 32, RED, 0xFFFFFFFF, (lt - b.at("regresó") - .3) / .3)
    with b.hud(c):
        caption(c, "SIN RIVAL EN LA LÍNEA = HORA DE PLACAS", (lt - b.at("cuándo")) / .3, 0xFF8EE08E)


WAVE = [(T[0] - 240, T[1] - 60), (T[0] - 200, T[1] + 30), (T[0] - 260, T[1] + 100)]


@M.escena("oleada", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_a_subdito", .4 + j * .9) for j in range(3)] + [("caitlyn_basico", 1.0 + j * .9) for j in range(3)])
def oleada(c, lt, b):
    t = b.t0 + lt
    for p in WAVE:
        minion(c, *p, "azul", 1, t)
    for j in range(3):
        f = .4 + j * .9
        shot(c, TOP, WAVE[0], (lt - f) / .32, "torre", RED)
    hits(c, lt, [1.0 + j * .9 for j in range(3)])
    turret_bar(c, lt, 3)
    M.target_line(c, (T[0] - 20, T[1] - 30), WAVE[0], 1, RED, t)
    cait(c)
    with b.hud(c):
        caption(c, "CON TU OLEADA ADELANTE", (lt - b.at("oleada")) / .3, BLUE)


@M.escena("riesgo", "mapa", prof=lambda b: [(0, "puntero"), ("tumba", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_disparo", .3 + j * .8, 1 + j * .3) for j in range(3)] + [("campeon_muere", b.at("tumba"))])
def riesgo(c, lt, b):
    t = b.t0 + lt
    fires = [.3 + j * .8 for j in range(3)]
    for j, f in enumerate(fires):
        shot(c, TOP, YOU, (lt - f) / .32, "torre", RED)
    hp = 1 - .3 * sum(lt > f + .32 for f in fires)
    turret_bar(c, lt, 3)
    M.target_line(c, (T[0] - 20, T[1] - 30), YOU, 1, RED, t)
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, max([pulse(lt, f + .32, 8) for f in fires]), max(0, hp), dead=ease((lt - b.at("tumba")) / .4), s=.8)
    with b.hud(c):
        caption(c, "SOLO: LA ALCANCÍA SE VUELVE TU TUMBA", (lt - b.at("tumba")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
