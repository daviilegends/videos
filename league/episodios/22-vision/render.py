"""Class 22: wards (stealth ward turns invisible shortly after being placed, 900 sight, 90-120 s, trinket with 2 charges, up to 3
on the map; control ward 75 gold, visible, reveals and disables enemy wards, 1 placed per player)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=22)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse  # noqa: E402

(A2, B2) = M.G.RIVERS[1]
RIV = ((A2[0] + B2[0]) / 2, (A2[1] + B2[1]) / 2)
WARD = (RIV[0] - 60, RIV[1] + 40)
CAM = (RIV[0], RIV[1] - 40, 1.1)
R900 = 900 * M.UNIT


def ward_vis(c, pos, k, t, color="azul", ring=True, alpha_=1.0):
    if ring and k > 0:
        c.drawCircle(*pos, R900 * ease(k), M.fill(M.alpha(0x22FFF2B0, k)))
        pp = M.stroke(6, M.alpha(0xFFFFE27A, k))
        pp.setPathEffect(M.skia.DashPathEffect.Make([18, 12], t * 30))
        c.drawCircle(*pos, R900 * ease(k), pp)
    if alpha_ < 1:
        c.saveLayerAlpha(None, int(255 * alpha_))
    M.ward(c, *pos, 1, t, color)
    if alpha_ < 1:
        c.restore()


def control_ward(c, pos, k, t):
    if k <= 0:
        return
    x, y = pos
    c.save()
    c.translate(x, y - (1 - M.back(min(1, k))) * 120)
    c.drawOval(M.skia.Rect.MakeXYWH(-30, 18, 60, 18), M.fill(0x55000000))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(-10, -40, 20, 64), 8, 8, M.fill(0xFF6B4A2B))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(-10, -40, 20, 64), 8, 8, M.stroke(5))
    c.drawOval(M.skia.Rect.MakeXYWH(-30, -80, 60, 42), M.fill(0xFFE84855))
    c.drawOval(M.skia.Rect.MakeXYWH(-30, -80, 60, 42), M.stroke(5))
    c.drawCircle(0, -59, 9, M.fill(0xFFFFF4C8))
    c.restore()


# ---------------- classroom
M.pizarra("hook", [("¿POR QUÉ SIEMPRE", 540, 450, 96, CHALK, .1), ("SABEN DÓNDE ESTÁS?", 540, 600, 96, CHALK_Y, "sabe")],
          prof=[(0, "piensa"), ("estás", "asombro")])
M.pizarra("spoiler", [("NO ES MAGIA NI HACKS", 540, 520, 84, CHALK, "magia"), ("ES VISIÓN", 540, 700, 130, CHALK_Y, "visión")],
          prof=[(0, "picara")])
M.pizarra("cargas", [("ACCESORIO: 2 CARGAS", 540, 500, 84, CHALK, "dos"), ("HASTA 3 EN EL MAPA", 540, 680, 90, CHALK_Y, "tres")],
          prof=[(0, "explica")])
M.pizarra("limite", [("ELIGE BIEN DÓNDE", 540, 520, 96, CHALK, "elige"), ("PONES EL DE CONTROL", 540, 680, 90, CHALK_R, "control")],
          prof=[(0, "explica")])
M.pizarra("broma", [("GUARDIÁN DE CONTROL =", 540, 480, 80, CHALK, "control"), ("VECINO CHISMOSO", 540, 660, 104, CHALK_Y, "chismoso")],
          prof=[(0, "feliz")])
M.pizarra("jungla", [("CERCA DE LOS OBJETIVOS:", 540, 470, 80, CHALK, "objetivos"), ("DRAGÓN · LARVAS", 540, 620, 90, CHALK_Y, "dragón"),
                     ("HERALDO · BARÓN", 540, 760, 90, CHALK_Y, "heraldo")], prof=[(0, "explica")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("¿NO VES AL JUNGLA?", 540, 580, 96, CHALK, "jungla"),
                  ("VIENE POR TI", 540, 760, 120, CHALK_R, "viene")], prof=[(0, "asombro")])
M.pizarra("tip2", [("¿UN GUARDIÁN RIVAL?", 540, 520, 90, CHALK, "guardián"), ("QUÍTALO", 540, 700, 140, 0xFF8EE08E, "quítalo")],
          prof=[(0, "explica"), ("cámara", "guino")])
K.cierre_teemo("GUARDIÁN: 900 DE VISIÓN · 90-120 s", "CONTROL: 75 ORO · REVELA Y APAGA", "1 LIKE = 1 GUARDIÁN")


# ---------------- river
@M.escena("respuesta", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ward", b.at("guardianes"))])
def respuesta(c, lt, b):
    t = b.t0 + lt
    ward_vis(c, WARD, (lt - b.at("guardianes")) / .4, t) if lt > b.at("guardianes") else None
    with b.hud(c):
        M.sign(c, t, lt / .5, "LA VISIÓN", "GUARDIANES")


@M.escena("invisible", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ward", .2)])
def invisible(c, lt, b):
    t = b.t0 + lt
    k = 1 - .75 * ease((lt - b.at("invisible")) / .6)
    ward_vis(c, WARD, 1, t, alpha_=k)
    champ(c, WARD[0] + 380, WARD[1] - 220, "Draven", "rojo", "RIVAL", 1, 0, 1, s=.75)
    badge(c, "?", WARD[0] + 380, WARD[1] - 380, 44, RED, 0xFFFFFFFF, (lt - b.at("invisible")) / .3)
    with b.hud(c):
        caption(c, "EL RIVAL NO LO VE", (lt - b.at("invisible")) / .3, GOLD)


@M.escena("radio", "mapa", cam=lambda b: [(0, (RIV[0], RIV[1] - 40, .85))], sfx=lambda b: [("ding", b.at("novecientas"))])
def radio(c, lt, b):
    t = b.t0 + lt
    ward_vis(c, WARD, 1, t)
    with b.hud(c):
        caption(c, "900 UNIDADES DE VISIÓN", (lt - b.at("novecientas")) / .3, 0xFFFFE27A)


@M.escena("dura", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("noventa"))])
def dura(c, lt, b):
    t = b.t0 + lt
    ward_vis(c, WARD, 1, t)
    with b.hud(c):
        K.cd_clock(c, 540, 1240, 1 - clamp((lt - b.at("noventa")) / 3), ease((lt - b.at("dura")) / .3), "W", 0x99FFE27A)
        caption(c, "DURA DE 90 A 120 SEGUNDOS", (lt - b.at("noventa")) / .3, GOLD)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, (RIV[0], RIV[1] - 40, .9))], sfx=lambda b: [("ding", b.at("cruza"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    ward_vis(c, WARD, 1, t)
    k = ease(lt / 2.5)
    champ(c, RIV[0] - 500 + 900 * k, RIV[1] - 300 + 500 * k, "LeeSin", "rojo", "RIVAL", 1, 0, 1, s=.75)
    with b.hud(c):
        caption(c, "VES QUIÉN CRUZA EL RÍO", (lt - b.at("cruza")) / .3, 0xFFFFE27A)


@M.escena("control", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ward", b.at("control")), ("oro", b.at("setenta"))])
def control(c, lt, b):
    t = b.t0 + lt
    control_ward(c, (WARD[0] + 180, WARD[1]), (lt - b.at("control")) / .4, t)
    with b.hud(c):
        caption(c, "GUARDIÁN DE CONTROL · 75 DE ORO", (lt - b.at("setenta")) / .3, RED)


@M.escena("revela", "mapa", prof=lambda b: [(0, "puntero"), ("desactiva", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ding", b.at("revela")), ("impacto", b.at("desactiva"))])
def revela(c, lt, b):
    t = b.t0 + lt
    cw = (WARD[0] + 180, WARD[1])
    control_ward(c, cw, 1, t)
    enemy_w = (WARD[0] - 220, WARD[1] - 140)
    seen = ease((lt - b.at("revela")) / .4)
    off = lt > b.at("desactiva")
    c.saveLayerAlpha(None, int(255 * (.25 + .75 * seen) * (.4 if off else 1)))
    M.ward(c, *enemy_w, 1, t, "rojo")
    c.restore()
    if off:
        M.chalk_cross(c, enemy_w[0], enemy_w[1] - 50, ease((lt - b.at("desactiva")) / .3), RED, .9)
    with b.hud(c):
        caption(c, "REVELA Y APAGA LOS GUARDIANES RIVALES", (lt - b.at("revela")) / .3, RED)


@M.escena("uno", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("uno"))])
def uno(c, lt, b):
    t = b.t0 + lt
    control_ward(c, (WARD[0] + 180, WARD[1]), 1, t)
    badge(c, "1", WARD[0] + 180, WARD[1] - 140, 44, RED, 0xFFFFFFFF, (lt - b.at("uno")) / .3)
    with b.hud(c):
        caption(c, "SOLO 1 PUESTO A LA VEZ", (lt - b.at("vez")) / .3, RED)


@M.escena("donde", "mapa", cam=lambda b: [(0, (RIV[0] - 100, RIV[1], .6))],
          sfx=lambda b: [("ward", b.at("río")), ("ward", b.at("arbustos")), ("ward", b.at("entrada"))])
def donde(c, lt, b):
    t = b.t0 + lt
    spots = [(WARD, "río"), (M.G._brush_pos(6950, "inferior", -1), "arbustos"), ((RIV[0] - 900, RIV[1] - 300), "entrada")]
    for p, key in spots:
        if lt > b.at(key):
            ward_vis(c, p, (lt - b.at(key)) / .4, t)
    with b.hud(c):
        caption(c, "RÍO · ARBUSTOS · ENTRADA DE LA JUNGLA", (lt - b.at("río")) / .3, 0xFFFFE27A)


if __name__ == "__main__":
    M.main()
