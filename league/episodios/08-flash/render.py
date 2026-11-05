"""Class 08: Flash. 400 range, instant, over walls, casts at max range if clicked beyond; 300 s cooldown; cancels Recall."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
from motor import (BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, chalk_circle, chalk_line,  # noqa: E402
                   chalk_stroke, clamp, ease, keys, pulse, shot)

M.setup(__file__, clase=8)
G = M.G
X0 = 5400
LY = G.lane_y("inferior", X0)
YOU = (X0, LY)
CAM = (X0 + 120, LY - 80, 1.2)
R400 = 400 * M.UNIT
WALL_X = X0 + 330  # a rock wall we draw across the scene for the "over walls" shots


def cait(c, pos=YOU, flash=0.0, hp=1.0, a=1.0):
    champ(c, *pos, "Caitlyn", "azul", "TÚ", 1, flash, hp, s=.85, a=a)


def draven(c, pos, flash=0.0):
    champ(c, *pos, "Draven", "rojo", "RIVAL", 1, flash, 1.0, s=.85)


def rock_wall(c, x, y0, y1):
    rnd = __import__("random").Random(4)
    for j in range(int((y1 - y0) / 70) + 1):
        y = y0 + j * 70
        r = rnd.uniform(48, 66)
        b = M.path([(x + math.cos(a) * r * (1 + .15 * math.sin(a * 3 + j)), y + math.sin(a) * r * .85) for a in [k * math.pi / 5 for k in range(10)]])
        c.drawPath(b, M.fill(0xFF6E7268))
        c.drawPath(b, M.stroke(6))


def range_ring(c, center, k, t, label=None):
    if k <= 0:
        return
    pp = M.stroke(6, M.alpha(0xFFFFF3A0, k))
    pp.setPathEffect(M.skia.DashPathEffect.Make([18, 12], t * 40))
    c.drawCircle(*center, R400 * ease(k), M.fill(M.alpha(0x22FFF3A0, k)))
    c.drawCircle(*center, R400 * ease(k), pp)
    if label:
        badge(c, label, center[0], center[1] + R400 + 40, 32, 0xFFFFF3A0, M.INK, k)


def cd_clock(c, x, y, frac, k, size=150):
    """Flash cooldown as in the game: official icon + sweep + seconds left of the 300 s."""
    M.spell_cd(c, "SummonerFlash", x, y, size, frac, k, round(300 * clamp(frac)))


# ---------------- classroom ----------------
M.pizarra("hook", [("¿POR QUÉ TODOS", 540, 450, 90, CHALK, .1), ("LLEVAN FLASH?", 540, 600, 104, CHALK_Y, "flash")],
          prof=[(0, "piensa"), ("flash", "explica")],
          extra=lambda c, lt, b: M.icono(c, "SummonerFlash", 540, 860, 220, (lt - b.at("flash")) / .4))
M.pizarra("poquito", [("POQUITO…", 540, 520, 100, CHALK, "poquito"), ("MORIR", 300, 760, 90, CHALK_R, "morir"),
                      ("ESCAPAR", 780, 760, 90, 0xFF8EE08E, "escapar")], prof=[(0, "explica"), ("escapar", "feliz")],
          extra=lambda c, lt, b: chalk_line(c, "VS", 540, 760, 70, (lt - b.at("morir") - .3) / .3))
M.pizarra("tiempo", [("5 MINUTOS", 540, 480, 110, CHALK, "cinco"), ("= 10 OLEADAS", 540, 650, 100, CHALK_Y, "diez")],
          prof=[(0, "explica"), ("muchísimo", "asombro")],
          extra=lambda c, lt, b: [M.chalk_minion(c, 170 + j * 82, 880, .7, CHALK, ease((lt - b.at("diez") - j * .08) / .25)) for j in range(10)])
M.pizarra("broma", [("5 MIN SIN FLASH", 540, 480, 96, CHALK, 0), ("DURA MÁS QUE TU", 540, 640, 80, CHALK, "dura"),
                    ("RACHA DE VICTORIAS", 540, 760, 80, CHALK_R, "racha")], prof=[(0, "picara")])
M.pizarra("sabe", [("Y EL RIVAL", 540, 560, 100, CHALK, "rival"), ("TAMBIÉN LO SABE", 540, 720, 96, CHALK_R, "sabe")],
          prof=[(0, "picara")])
M.pizarra("sin", [("¿SIN FLASH?", 540, 520, 104, CHALK, 0), ("JUEGA MÁS ATRÁS", 540, 700, 90, CHALK_Y, "atrás")],
          prof=[(0, "explica"), ("vuelva", "guino")])
M.pizarra("orden", [("1. ESCAPA", 540, 540, 110, 0xFF8EE08E, "primero"), ("2. RECALL", 540, 720, 110, CHALK_Y, "después")],
          prof=[(0, "explica"), ("después", "guino")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("NO POR NERVIOS", 540, 580, 90, CHALK_R, "nervios"),
                  ("FLASH = VIDA EXTRA", 540, 740, 90, CHALK_Y, "vida")], prof=[(0, "explica"), ("salva", "guino")])


@M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), ("teemo", "feliz")],
          sfx=lambda b: [("tiza", 0), ("ding", b.at("like")), ("puno", b.at("atrapamos") - .05), ("teemo_muere", b.at("atrapamos") + .2)])
def cierre(c, lt, b):
    chalk_line(c, "400 UNIDADES · 300 s", 540, 400, 70, lt / .5)
    chalk_line(c, "PASA MUROS · CANCELA EL RECALL", 540, 500, 54, (lt - .6) / .5, CHALK_Y)
    badge(c, "1 LIKE = 1 FLASH QUE TEEMO NO TIENE", 540, 640, 40, GOLD, M.INK, (lt - b.at("like")) / .35, rot=-3)
    cd_clock(c, 300, 900, 1 - clamp((lt - b.at("teemo")) / 3), ease((lt - b.at("teemo")) / .3))
    M.teemo_punch(c, lt, [b.at("atrapamos")], 760, 880, ease((lt - b.at("like")) / .4), b.t0 + lt)


# ---------------- lane ----------------
@M.escena("que", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("flash", b.at("teletransporta"))])
def que(c, lt, b):
    t = b.t0 + lt
    tf = b.at("teletransporta")
    dest = (YOU[0] + R400 * .95, YOU[1] - 20)
    M.flash_fx(c, YOU, dest, lt - tf)
    cait(c, YOU if lt < tf else dest)
    with b.hud(c):
        M.sign(c, t, lt / .5, "FLASH", "EL HECHIZO DE TODOS")
        caption(c, "DISTANCIA CORTA, AL INSTANTE", (lt - b.at("corta")) / .3, 0xFFFFF3A0)


@M.escena("instante", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("flash", b.at("desapareces"))])
def instante(c, lt, b):
    t = b.t0 + lt
    tf = b.at("desapareces")
    a, z = (YOU[0] + R400 * .95, YOU[1] - 20), YOU
    M.flash_fx(c, a, z, lt - tf)
    cait(c, a if lt < tf else z)
    draven(c, (YOU[0] + 520, YOU[1] - 200))
    badge(c, "?", YOU[0] + 520, YOU[1] - 350, 44, RED, 0xFFFFFFFF, (lt - tf - .2) / .3)
    with b.hud(c):
        caption(c, "SIN ANIMACIÓN QUE SE VEA VENIR", (lt - b.at("animación")) / .3, GOLD)


@M.escena("rango", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("cuatrocientas"))])
def rango(c, lt, b):
    t = b.t0 + lt
    range_ring(c, YOU, (lt - b.at("alcance")) / .4, t, "400 UNIDADES" if lt > b.at("cuatrocientas") else None)
    cait(c)


@M.escena("max", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("flash", b.at("máximo"))])
def max_(c, lt, b):
    t = b.t0 + lt
    range_ring(c, YOU, 1, t)
    click = (YOU[0] + R400 * 1.9, YOU[1] - 90)
    kc = (lt - b.at("clic")) / .3
    if kc > 0:
        c.drawCircle(*click, 30 * M.back(min(1, kc)), M.stroke(6, 0xFF8EE08E))
        c.drawLine(click[0] - 20, click[1], click[0] + 20, click[1], M.stroke(5, 0xFF8EE08E))
        c.drawLine(click[0], click[1] - 20, click[0], click[1] + 20, M.stroke(5, 0xFF8EE08E))
    tf = b.at("máximo")
    ang = math.atan2(click[1] - YOU[1], click[0] - YOU[0])
    dest = (YOU[0] + math.cos(ang) * R400, YOU[1] + math.sin(ang) * R400)
    M.flash_fx(c, YOU, dest, lt - tf)
    cait(c, YOU if lt < tf else dest)
    with b.hud(c):
        caption(c, "MÁS LEJOS = SALE AL MÁXIMO", (lt - tf) / .3, GOLD)


@M.escena("muros", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("flash", b.at("muros"))])
def muros(c, lt, b):
    t = b.t0 + lt
    rock_wall(c, WALL_X, LY - 360, LY + 360)
    tf = b.at("muros")
    a, z = (WALL_X - 150, YOU[1]), (WALL_X + 150, YOU[1])
    M.flash_fx(c, a, z, lt - tf)
    cait(c, a if lt < tf else z)
    with b.hud(c):
        caption(c, "PASA POR ENCIMA DE MUROS", (lt - tf) / .3, 0xFFFFF3A0) if lt < b.at("escapar") else \
            caption(c, "PARA ESCAPAR… O PERSEGUIR", (lt - b.at("escapar")) / .3, GOLD)


@M.escena("ejemplo", "mapa", prof=lambda b: [(0, "puntero"), ("pared", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("flash", b.at("saltas")), ("ding", b.at("pared"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    rock_wall(c, WALL_X, LY - 360, LY + 360)
    ts = b.at("saltas")
    a, z = (WALL_X - 150, YOU[1]), (WALL_X + 150, YOU[1])
    cp = keys(lt, [(0, (WALL_X - 420, YOU[1])), (ts - .1, a)]) if lt < ts else z
    dp = keys(lt, [(0, (WALL_X - 700, YOU[1] + 30)), (ts + .2, (WALL_X - 220, YOU[1] + 30))])
    M.flash_fx(c, a, z, lt - ts)
    cait(c, cp)
    draven(c, dp)
    badge(c, "…", dp[0], dp[1] - 150, 44, RED, 0xFFFFFFFF, (lt - b.at("mirando")) / .3)
    with b.hud(c):
        caption(c, "…Y SE QUEDA MIRANDO LA PARED", (lt - b.at("mirando")) / .3, 0xFF8EE08E)


@M.escena("cd", "mapa", prof=lambda b: [(0, "puntero"), ("cinco", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ding", b.at("trescientos"))])
def cd(c, lt, b):
    t = b.t0 + lt
    cait(c)
    cd_clock(c, YOU[0] + 260, YOU[1] - 200, 1 - clamp((lt - b.at("enfriamiento")) / 6), ease((lt - b.at("enfriamiento")) / .3), 190)
    with b.hud(c):
        M.big_number(c, "300 s", 330, 620, (lt - b.at("trescientos")) / .35, GOLD, 140)
        caption(c, "5 MINUTOS SIN FLASH", (lt - b.at("cinco")) / .3, 0xFFFF6B74)


@M.escena("uso", "mapa", prof=lambda b: [(0, "puntero"), ("expuesto", "picara")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("flash", b.at("usa")), ("ding", b.at("avísale"))])
def uso(c, lt, b):
    t = b.t0 + lt
    tf = b.at("usa")
    a = (YOU[0] + 520, YOU[1] - 60)
    z = (a[0] + R400 * .9, a[1] - 40)
    M.flash_fx(c, a, z, lt - tf)
    draven(c, a if lt < tf else z)
    cd_clock(c, z[0], z[1] - 210, 1, ease((lt - tf - .3) / .3))
    cait(c)
    badge(c, "¡SIN FLASH!", YOU[0], YOU[1] - 150, 36, BLUE, 0xFFFFFFFF, (lt - b.at("avísale")) / .3)
    with b.hud(c):
        caption(c, "AVÍSALE A TU EQUIPO: 5 MINUTOS", (lt - b.at("avísale")) / .3, BLUE)


@M.escena("recall", "mapa", prof=lambda b: [(0, "puntero"), ("cancelas", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("recall", 0, .5), ("flash", b.at("flash"))])
def recall(c, lt, b):
    t = b.t0 + lt
    tf = b.at("flash")
    dest = (YOU[0] - R400 * .9, YOU[1] - 30)
    k = clamp((min(lt, tf) + 2) / 8.5)
    M.recall_fx(c, *YOU, k, t, cancel=clamp((lt - tf) / .5) if lt > tf else 0)
    M.flash_fx(c, YOU, dest, lt - tf)
    cait(c, YOU if lt < tf else dest)
    with b.hud(c):
        caption(c, "FLASH EN RECALL = CANCELADO", (lt - b.at("cancelas")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
