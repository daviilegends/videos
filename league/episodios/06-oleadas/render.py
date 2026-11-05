"""Class 06: the wave clock. Waves from 00:30 every 30 s; 25 s from 14:00; 20 s from 30:00. Siege (cannon) minion first in
wave 3 (01:30); every 3 waves until 14:00, every 2 after, every wave from 25:00; not in waves with super minions."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
from motor import (BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, chalk_circle, chalk_line,  # noqa: E402
                   chalk_minion, chalk_stroke, clamp, ease, keys, minion, pulse, shot)

M.setup(__file__, clase=6)
G = M.G
MY = G.H / 2  # mid lane
X_SPAWN = 1150
CAM = (1750, MY - 60, 1.0)
ORO = 0xFFFFD34D


def game_clock(c, s_, k, warn=False):
    if k <= 0:
        return
    f = M.font("segoeuib.ttf", 58)
    w = f.measureText(s_)
    c.save()
    c.translate(540, 300)
    sc = M.back(k)
    c.scale(sc, sc)
    r = M.skia.Rect.MakeXYWH(-w / 2 - 70, -58, w + 110, 78)
    c.drawRoundRect(r, 18, 18, M.fill(0xEE0E1418))
    c.drawRoundRect(r, 18, 18, M.stroke(5, GOLD))
    c.drawCircle(-w / 2 - 34, -19, 20, M.stroke(5, GOLD))
    c.drawLine(-w / 2 - 34, -19, -w / 2 - 34, -32, M.stroke(4, GOLD))
    c.drawLine(-w / 2 - 34, -19, -w / 2 - 24, -19, M.stroke(4, GOLD))
    c.drawString(s_, -w / 2 + 6, 0, f, M.fill(0xFFFF6B74 if warn else 0xFFFFFFFF))
    c.restore()


def wave(c, lt, t, t_spawn, cannon=False, speed=260, kinds=None):
    """A blue wave that leaves the base at t_spawn and marches right."""
    if lt < t_spawn:
        return
    d = (lt - t_spawn) * speed
    kinds = kinds or (["melee"] * 3 + (["canon"] if cannon else []) + ["mago"] * 3)
    for j, kind in enumerate(kinds):
        x = X_SPAWN + d - j * 75
        if x < X_SPAWN - 10:
            continue
        y = MY + ((j % 3) - 1) * 60
        minion(c, x, y, "azul", 1, t, kind=kind)


def mmss(sec):
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"


def chalk_clock(c, x, y, r, k, t):
    chalk_circle(c, x, y, r, k, CHALK, 8)
    if k >= 1:
        a = t * 2
        c.drawLine(x, y, x + math.cos(a) * r * .75, y + math.sin(a) * r * .75, M.stroke(8, CHALK_Y))
        c.drawLine(x, y, x + math.cos(a / 12) * r * .5, y + math.sin(a / 12) * r * .5, M.stroke(8, CHALK))


def waves_row(c, lt, b, y, n, every, start_key, color=CHALK_Y):
    """Chalk row of n waves; the cannon ones (every `every`) are highlighted."""
    t0 = b.at(start_key) if isinstance(start_key, str) else start_key
    for j in range(n):
        x = 160 + j * 95
        k = (lt - t0 - j * .12) / .25
        cann = every and (j + 1) % every == 0
        chalk_circle(c, x, y, 34, k, color if cann else CHALK, 7 if cann else 5)
        if cann and k > 1:
            c.drawCircle(x, y, 14, M.fill(color))


# ---------------- classroom ----------------
def hook_extra(c, lt, b):
    chalk_clock(c, 540, 860, 120, (lt - b.at("horario")) / .6, b.t0 + lt)


M.pizarra("hook", [("LOS SÚBDITOS", 540, 450, 90, CHALK, .1), ("TIENEN HORARIO", 540, 590, 96, CHALK_Y, "horario")],
          prof=[(0, "piensa"), ("camión", "picara")], extra=hook_extra)
M.pizarra("porque", [("SABER EL HORARIO", 540, 520, 90, CHALK, "horario"), ("= GANAR LA LÍNEA", 540, 680, 96, CHALK_Y, "ganar")],
          prof=[(0, "explica"), ("mira", "guino")])
M.pizarra("medio", [("00:00", 330, 520, 100, CHALK, "empieza"), ("EMPIEZA", 330, 640, 60, CHALK, "empieza"),
                    ("00:30", 750, 520, 100, CHALK_Y, "primera"), ("1ª OLEADA", 750, 640, 60, CHALK_Y, "medio")],
          prof=[(0, "explica")], extra=lambda c, lt, b: M.chalk_arrow(c, (470, 490), (600, 490), (lt - b.at("primera")) / .3))
M.pizarra("m14", [("MINUTO 14", 540, 480, 110, CHALK, "catorce"), ("SE ACELERAN", 540, 630, 80, CHALK_R, "aceleran"),
                  ("CADA 25 s", 540, 800, 120, CHALK_Y, "veinticinco")], prof=[(0, "explica"), ("aceleran", "asombro")])
M.pizarra("m30", [("MINUTO 30", 540, 520, 110, CHALK, "treinta"), ("CADA 20 s", 540, 720, 120, CHALK_Y, "veinte")],
          prof=[(0, "explica")])
M.pizarra("porminuto", [("AL INICIO: 2 / MIN", 540, 540, 96, CHALK, "dos"), ("AL FINAL: 3 / MIN", 540, 740, 96, CHALK_Y, "tres")],
          prof=[(0, "explica")])


def jefe_extra(c, lt, b):
    chalk_clock(c, 540, 820, 110, (lt - b.at("jefe")) / .5, b.t0 + lt)
    M.badge(c, "REPORTES", 760, 950, 36, CHALK_R, M.INK, (lt - b.at("jefe") - .4) / .3, rot=8)


M.pizarra("broma2", [("MÁS PUNTUAL QUE", 540, 470, 84, CHALK, 0), ("TU JEFE", 540, 600, 110, CHALK_R, "jefe")],
          prof=[(0, "picara")], extra=jefe_extra)
M.pizarra("canon2", [("HASTA EL MINUTO 14", 540, 440, 72, CHALK, "catorce"), ("CAÑÓN CADA 3 OLEADAS", 540, 560, 70, CHALK_Y, "tres")],
          prof=[(0, "explica")], extra=lambda c, lt, b: waves_row(c, lt, b, 780, 9, 3, "tres"))


def canon3_extra(c, lt, b):
    chalk_line(c, "DESPUÉS: CADA 2", 540, 700, 60, (lt - b.at("dos")) / .4, CHALK_Y)
    waves_row(c, lt, b, 800, 8, 2, "dos")
    chalk_line(c, "MINUTO 25: TODAS", 540, 960, 60, (lt - b.at("veinticinco")) / .4, CHALK_R)


M.pizarra("canon3", [("EL CAÑÓN", 540, 450, 90, CHALK, 0)], prof=[(0, "explica"), ("todas", "asombro")], extra=canon3_extra)


def super_extra(c, lt, b):
    chalk_minion(c, 380, 860, 2.0, 0xFFB06CF0, ease((lt - b.at("súper")) / .4))
    chalk_line(c, "→", 560, 880, 110, (lt - b.at("cañón")) / .3)
    chalk_line(c, "SIN CAÑÓN", 790, 880, 70, (lt - b.at("sale")) / .4, CHALK_R)


M.pizarra("super", [("¿SÚPER SÚBDITOS?", 540, 480, 90, CHALK, "súper")], prof=[(0, "explica"), ("sale", "picara")], extra=super_extra)


def contar_extra(c, lt, b):
    for j in range(3):
        chalk_line(c, str(j + 1), 250 + j * 170, 760, 120, (lt - b.at("cuentas") - j * .35) / .25, CHALK if j < 2 else CHALK_Y)
    chalk_line(c, "= CAÑÓN", 820, 760, 80, (lt - b.at("cañón")) / .3, CHALK_Y)
    M.chalk_cross(c, 540, 950, (lt - b.at("reloj")) / .4, s=.8)
    chalk_clock(c, 540, 950, 60, (lt - b.at("reloj") + .4) / .4, b.t0 + lt)


M.pizarra("contar", [("CUENTA LAS OLEADAS", 540, 470, 80, CHALK, "cuentas")], prof=[(0, "explica"), ("reloj", "guino")], extra=contar_extra)


def tamal_extra(c, lt, b):
    M.tamal(c, 540, 850, 1.8, (lt - b.at("tamales")) / .4, b.t0 + lt)


M.pizarra("broma", [("COMO SABER A QUÉ HORA", 540, 470, 66, CHALK, "hora"), ("PASA EL DE LOS TAMALES", 540, 580, 66, CHALK_Y, "tamales")],
          prof=[(0, "feliz")], extra=tamal_extra)


@M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), ("teemo", "feliz")],
          sfx=lambda b: [("tiza", 0), ("ding", b.at("like")), ("golpe_subdito", b.at("teemo") - .1, 2), ("puno", b.at("teemo") + .1),
                         ("teemo_muere", b.at("teemo") + .3)])
def cierre(c, lt, b):
    chalk_line(c, "00:30 · CADA 30 s", 540, 400, 64, lt / .5)
    chalk_line(c, "MIN 14: 25 s · MIN 30: 20 s", 540, 500, 56, (lt - .5) / .5, CHALK_Y)
    badge(c, "1 LIKE = 1 OLEADA ENCIMA", 540, 640, 44, GOLD, M.INK, (lt - b.at("like")) / .35, rot=-3)
    for j in range(5):  # chalk minions running at Teemo
        k = clamp((lt - b.at("oleada") - j * .08) / .5)
        if k > 0:
            chalk_minion(c, 200 + 300 * k + j * 50, 920 + (j % 2) * 40, .9, CHALK_R, 1)
    M.teemo_punch(c, lt, [b.at("teemo") + .2], 760, 880, ease((lt - b.at("like")) / .4), b.t0 + lt)


# ---------------- lane ----------------
@M.escena("inicio", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ding", b.at("oleada")), ("ding", b.at("oleada") + 2.2)])
def inicio(c, lt, b):
    t = b.t0 + lt
    to = b.at("oleada")
    wave(c, lt, t, to)
    wave(c, lt, t, to + 2.2)
    with b.hud(c):
        game_clock(c, mmss(min(60, 30 + max(0, lt - to) * 30 / 2.2)), (lt - to) / .3)
        M.sign(c, t, lt / .5, "EL RELOJ", "DE LAS OLEADAS") if lt < to else None
        caption(c, "UNA OLEADA CADA 30 SEGUNDOS", (lt - b.at("cada")) / .3, GOLD)


@M.escena("canon1", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("tercera"))])
def canon1(c, lt, b):
    t = b.t0 + lt
    tt = b.at("tercera")
    wave(c, lt, t, tt - .2, cannon=True, speed=200)
    with b.hud(c):
        game_clock(c, "01:30", lt / .3)
        caption(c, "OLEADA 3: LLEGA EL CAÑÓN", (lt - tt) / .3, GOLD)


@M.escena("quien", "mapa", cam=lambda b: [(0, (2000, MY - 40, 1.4))],
          sfx=lambda b: [("golpe_subdito", b.at("dispara") + .3 + j * .9, 2.5) for j in range(3)])
def quien(c, lt, b):
    t = b.t0 + lt
    cpos = (1860, MY)
    for j, (dx, dy) in enumerate(((180, -60), (220, 0), (180, 60))):
        minion(c, cpos[0] + dx, cpos[1] + dy, "azul", 1, t)
    minion(c, *cpos, "azul", 1, t, kind="canon")
    for j in range(3):
        f = b.at("dispara") + j * .9
        shot(c, (cpos[0] + 40, cpos[1] - 10), (cpos[0] + 520, cpos[1] - 10), (lt - f) / .5, "bala", 0xFF6B6B6B)
    badge(c, "GRANDOTE", cpos[0], cpos[1] - 120, 32, BLUE, 0xFFFFFFFF, (lt - b.at("grandote")) / .3)
    with b.hud(c):
        caption(c, "DISPARA DESDE ATRÁS", (lt - b.at("dispara")) / .3, GOLD)


@M.escena("tip", "mapa", prof=lambda b: [(0, "puntero"), ("perderlo", "guino")], cam=lambda b: [(0, (2600, MY - 40, 1.3))],
          sfx=lambda b: [("caitlyn_basico", b.at("perderlo") - .3), ("oro", b.at("perderlo"))])
def tip(c, lt, b):
    t = b.t0 + lt
    cpos = (2800, MY)
    tp = b.at("perderlo")
    k = clamp((lt - tp) / .45)
    minion(c, *cpos, "rojo", -1, t, kind="canon", pop=k, flash=pulse(lt, tp, 10))
    if k < 1:
        M.minion_hp(c, cpos[0], cpos[1] - 30, .08 if lt < tp else 0)
    you = (2450, MY + 60)
    champ(c, *you, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.85)
    shot(c, you, cpos, (lt - tp + .3) / .3, "bala", BLUE)
    if 0 < lt - tp < 1.6:
        M.text(c, "+ORO", cpos[0], cpos[1] - 130 - 60 * ease(lt - tp), M.font("segoeuib.ttf", 40), ORO, 8)
    with b.hud(c):
        caption(c, "NO PIERDAS EL CAÑÓN", (lt - b.at("cañón")) / .3, 0xFF8EE08E) if lt < b.at("regresar") else \
            caption(c, "…Y PLANEA TU REGRESO A BASE", (lt - b.at("regresar")) / .3, BLUE)


@M.escena("tip2", "mapa", prof=lambda b: [(0, "puntero"), ("alejes", "asombro")], cam=lambda b: [(0, (2050, MY - 300, 1.0))],
          sfx=lambda b: [("ding", b.at("seguido")), ("ding", b.at("seguido") + 1.3)])
def tip2(c, lt, b):
    t = b.t0 + lt
    ts = b.at("seguido")
    for j in range(4):
        wave(c, lt, t, ts - 1.5 + j * 1.3, speed=320)
    champ(c, 2350, MY - 650, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.85)
    badge(c, "¡LEJOS!", 2350, MY - 800, 36, RED, 0xFFFFFFFF, (lt - b.at("alejes")) / .3)
    with b.hud(c):
        game_clock(c, "31:40", lt / .3, warn=True)
        caption(c, "LLEGAN MÁS SEGUIDO: NO TE ALEJES", (lt - b.at("alejes")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
