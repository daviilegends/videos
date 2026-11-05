"""Class 11: shared minion experience (1500 units; solo 100%; 2+ champions share 130% total: 65% each for two; cap 18)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=11)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, minion, pulse  # noqa: E402

LY = M.G.lane_y("central", 6000)
DEAD = (6150, LY)
R = 1500 * M.UNIT
CAM = (6050, LY - 30, .9)
PURPLE = 0xFF9B6CF0


def xp_orbs(c, lt, t0, targets, n=6):
    """Purple orbs flying from the dead minion to each champion."""
    for j, p in enumerate(targets):
        for i in range(n):
            k = (lt - t0 - i * .06) / .6
            if 0 < k < 1:
                x = DEAD[0] + (p[0] - DEAD[0]) * ease(k)
                y = DEAD[1] + (p[1] - DEAD[1]) * ease(k) - math.sin(k * math.pi) * 120
                c.drawCircle(x, y, 12, M.fill(PURPLE))
                c.drawCircle(x, y, 12, M.stroke(3))


def dying_minion(c, lt, t, t_die):
    minion(c, *DEAD, "rojo", -1, t, pop=clamp((lt - t_die) / .4))


# ---------------- classroom
M.pizarra("hook", [("¿POR QUÉ EL QUE VA SOLO", 540, 450, 70, CHALK, .1), ("SUBE MÁS RÁPIDO?", 540, 580, 90, CHALK_Y, "rápido")],
          prof=[(0, "piensa"), ("abajo", "asombro")])
M.pizarra("spoiler", [("NO ES SUERTE", 540, 500, 100, CHALK, 0), ("SON MATEMÁTICAS", 540, 680, 96, CHALK_Y, "matemáticas")],
          prof=[(0, "picara"), ("matemáticas", "explica")])
M.pizarra("ejemplo", [("1 SÚBDITO = 100", 540, 480, 96, CHALK, "súbdito"), ("2 CAMPEONES:", 540, 640, 80, CHALK, "dos"),
                      ("65 + 65", 540, 790, 120, CHALK_Y, "sesenta")], prof=[(0, "explica")])


def mas_extra(c, lt, b):
    rows = [("3", "43 c/u", "tres"), ("4", "32 c/u", "cuatro"), ("5", "26 c/u", "cinco")]
    for j, (n, v, key) in enumerate(rows):
        y = 560 + j * 120
        M.chalk_line(c, f"{n} CAMPEONES", 330, y, 64, (lt - b.at(key)) / .4)
        M.chalk_line(c, v, 780, y, 70, (lt - b.at(key) - .3) / .4, CHALK_Y)


M.pizarra("mas", [("TOTAL: SIEMPRE 130%", 540, 430, 76, CHALK_R, "total")], prof=[(0, "explica")], extra=mas_extra)
M.pizarra("broma", [("COMO LA PIZZA", 540, 460, 96, CHALK, "pizza")], prof=[(0, "feliz")],
          extra=lambda c, lt, b: [K.pizza(c, 300 + j * 240, 820, 95, 1 + j * 2, ease((lt - b.at("amigos") - j * .3) / .4)) for j in range(3)])
M.pizarra("por_eso", [("SOLO EN SU LÍNEA", 540, 480, 90, 0xFF8EE08E, "solo"), ("> PAREJA DE ABAJO", 540, 650, 90, CHALK_R, "pareja")],
          prof=[(0, "explica"), ("pareja", "guino")])
M.pizarra("broma2", [("TE VAS A PASEAR…", 540, 500, 90, CHALK, "pasear"), ("LA EXPERIENCIA LLORA", 540, 680, 80, CHALK_Y, "llorando")],
          prof=[(0, "picara")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("SIN PELEA →", 540, 580, 96, CHALK, "peleando"),
                  ("CERCA DE LAS OLEADAS", 540, 740, 80, 0xFF8EE08E, "oleadas")], prof=[(0, "explica")])
M.pizarra("tip2", [("VARIOS EN UNA LÍNEA", 540, 520, 84, CHALK, "varios"), ("= TODOS SUBEN LENTO", 540, 690, 84, CHALK_R, "lento")],
          prof=[(0, "explica"), ("lento", "asombro")])
M.pizarra("max", [("NIVEL MÁXIMO", 540, 480, 96, CHALK, "máximo"), ("18", 540, 720, 200, CHALK_Y, "dieciocho")],
          prof=[(0, "explica"), ("clase", "guino")])
K.cierre_teemo("SOLO: 100% · COMPARTIDO: 130% REPARTIDO", "RANGO: 1,500 UNIDADES", "1 LIKE = EXPERIENCIA PARA TI")


# ---------------- lane
YOU = (DEAD[0] - 380, LY + 60)
ALLY = (DEAD[0] - 300, LY - 120)
FAR = (DEAD[0] - R - 260, LY - 40)


@M.escena("regla", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("subdito_muere", b.at("muere")), ("ding", b.at("reparte"))])
def regla(c, lt, b):
    t = b.t0 + lt
    td = b.at("muere")
    dying_minion(c, lt, t, td)
    champ(c, *YOU, "Garen", "azul", "TÚ", 1, 0, 1, s=.8)
    xp_orbs(c, lt, b.at("reparte"), [YOU])
    with b.hud(c):
        M.sign(c, t, lt / .5, "LA EXPERIENCIA", "COMPARTIDA")
        K.xp_bar(c, 240, 1300, 600, clamp((lt - b.at("reparte") - .5) / .6) * .4 + .2, 1, "EXPERIENCIA")


@M.escena("rango", "mapa", cam=lambda b: [(0, (DEAD[0] - 300, LY - 30, .7))], sfx=lambda b: [("ding", b.at("mil"))])
def rango(c, lt, b):
    t = b.t0 + lt
    M.ring(c, DEAD, R, (lt - b.at("menos")) / .5, PURPLE, "1,500 UNIDADES" if lt > b.at("mil") else None, t)
    minion(c, *DEAD, "rojo", -1, t)
    champ(c, *YOU, "Garen", "azul", "TÚ", 1, 0, 1, s=.8)


@M.escena("solo", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("subdito_muere", .3), ("ding", b.at("cien"))])
def solo(c, lt, b):
    t = b.t0 + lt
    dying_minion(c, lt, t, .3)
    champ(c, *YOU, "Garen", "azul", "TÚ", 1, 0, 1, s=.8)
    xp_orbs(c, lt, .5, [YOU], 8)
    with b.hud(c):
        M.big_number(c, "100%", 300, 620, (lt - b.at("cien")) / .35, PURPLE)


@M.escena("dos", "mapa", prof=lambda b: [(0, "puntero"), ("reparte", "explica")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("subdito_muere", .3), ("ding", b.at("ciento")), ("ding", b.at("sesenta"))])
def dos(c, lt, b):
    t = b.t0 + lt
    dying_minion(c, lt, t, .3)
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.8)
    champ(c, *ALLY, "Soraka", "azul", None, 1, 0, 1, s=.75)
    xp_orbs(c, lt, .5, [YOU, ALLY], 5)
    badge(c, "65%", YOU[0], YOU[1] - 140, 34, PURPLE, 0xFFFFFFFF, (lt - b.at("sesenta")) / .3)
    badge(c, "65%", ALLY[0], ALLY[1] - 140, 34, PURPLE, 0xFFFFFFFF, (lt - b.at("sesenta")) / .3)
    with b.hud(c):
        M.big_number(c, "130%", 300, 620, (lt - b.at("ciento")) / .35, PURPLE)
        caption(c, "…PERO SE REPARTE", (lt - b.at("reparte")) / .3, GOLD)


@M.escena("lejos", "mapa", prof=lambda b: [(0, "puntero"), ("nada", "asombro")], cam=lambda b: [(0, (DEAD[0] - 500, LY - 30, .6))],
          sfx=lambda b: [("subdito_muere", .3), ("ding", b.at("nada"))])
def lejos(c, lt, b):
    t = b.t0 + lt
    M.ring(c, DEAD, R, 1, PURPLE, None, t)
    dying_minion(c, lt, t, .3)
    champ(c, *FAR, "Garen", "azul", "TÚ", 1, 0, 1, s=1.0)
    badge(c, "0 EXP", FAR[0], FAR[1] - 170, 40, RED, 0xFFFFFFFF, (lt - b.at("nada")) / .3)
    with b.hud(c):
        caption(c, "FUERA DEL CÍRCULO: NADA", (lt - b.at("nada")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
