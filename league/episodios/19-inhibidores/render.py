"""Class 19: inhibitors (destroying one makes your side send a super minion in that lane each wave; all three: two per lane;
respawn after 5 min with a warning ~15 s before; 4000 health; once one falls, the nexus turrets and nexus can be attacked)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=19)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, minion, pulse, shot  # noqa: E402

G = M.G
IX = G.W - 1100
IY = G.lane_y("inferior", IX)
INH = (IX, IY)
CAM = (IX - 260, IY - 80, 1.1)


def broken(c, k, t):
    """Draws the broken inhibitor (gray shards) over the map's crystal."""
    if k <= 0:
        return
    c.drawCircle(IX, IY, 100, M.fill(M.alpha(0xFF3A3F48, k)))
    c.drawCircle(IX, IY, 100, M.stroke(8, M.alpha(M.INK, k)))
    for j in range(5):
        a = j * 1.25
        c.drawPath(M.path([(IX + math.cos(a) * 20, IY + math.sin(a) * 20), (IX + math.cos(a + .3) * 70, IY + math.sin(a + .3) * 70),
                           (IX + math.cos(a + .6) * 30, IY + math.sin(a + .6) * 30)]), M.fill(M.alpha(0xFF8A8A98, k)))


def hp_bar(c, frac):
    c.drawRoundRect(M.skia.Rect.MakeXYWH(IX - 110, IY - 180, 220, 22), 8, 8, M.fill(0xFF0A1424))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(IX - 110, IY - 180, 220 * clamp(frac), 22), 8, 8, M.fill(RED))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(IX - 110, IY - 180, 220, 22), 8, 8, M.stroke(4, GOLD))


def super_wave(c, lt, t, t0, n_super=1, x0=None):
    """A blue wave marching right with super minions in front."""
    if lt < t0:
        return
    d = (lt - t0) * 260
    x0 = x0 or IX - 1500
    for j in range(n_super):
        minion(c, x0 + d - j * 140, IY - 40 + j * 80, "azul", 1, t, kind="super")
    for j in range(3):
        minion(c, x0 + d - 220 - j * 70, IY + (j - 1) * 60, "azul", 1, t)


# ---------------- classroom
M.pizarra("hook", [("¿QUÉ PASA SI ROMPES", 540, 450, 90, CHALK, .1), ("UN INHIBIDOR?", 540, 600, 104, CHALK_Y, "inhibidor")],
          prof=[(0, "piensa")])
M.pizarra("spoiler", [("LA PARTIDA", 540, 520, 110, CHALK, "partida"), ("EMPIEZA A CERRARSE", 540, 690, 90, CHALK_R, "cerrarse")],
          prof=[(0, "explica")])
M.pizarra("broma", [("SÚPER SÚBDITO =", 540, 500, 96, CHALK, "súper"), ("EL PRIMO GRANDOTE", 540, 680, 96, CHALK_Y, "primo")],
          prof=[(0, "feliz")], extra=lambda c, lt, b: M.chalk_minion(c, 540, 900, 2.0, 0xFFC8A8F8, ease((lt - b.at("primo")) / .4)))
M.pizarra("vida", [("INHIBIDOR", 540, 500, 110, CHALK, 0), ("4,000 DE VIDA", 540, 680, 100, CHALK_Y, "cuatro")],
          prof=[(0, "explica")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("INHIBIDOR ROTO", 540, 580, 96, CHALK, "inhibidor"),
                  ("= PRESIÓN SIN TI", 540, 740, 96, 0xFF8EE08E, "presión")], prof=[(0, "explica"), ("base", "guino")])
M.pizarra("tip2", [("¿TE ROMPIERON UNO?", 540, 520, 90, CHALK, "tiran"), ("NO PELEES LEJOS", 540, 690, 96, CHALK_R, "lejos")],
          prof=[(0, "asombro")])
M.pizarra("tip3", [("MÁTALOS RÁPIDO", 540, 520, 100, CHALK, "mátalos"), ("CON TU EQUIPO CERCA", 540, 690, 86, CHALK_Y, "equipo")],
          prof=[(0, "explica")])
M.pizarra("tip4", [("¿EL RIVAL TIENE LOS 3?", 540, 520, 84, CHALK, "tres"), ("MUCHA PRESIÓN", 540, 690, 100, CHALK_R, "presión")],
          prof=[(0, "asombro")])
K.cierre_teemo("INHIBIDOR ROTO = SÚPER SÚBDITOS", "VUELVE EN 5 MIN", "1 LIKE = 1 SÚPER SÚBDITO")


# ---------------- enemy base, bot lane
@M.escena("que", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("cristales"))])
def que(c, lt, b):
    t = b.t0 + lt
    M.ring(c, INH, 140, (lt - b.at("cristales")) / .4, RED, "INHIBIDOR", t)
    with b.hud(c):
        M.sign(c, t, lt / .5, "INHIBIDORES", "Y SÚPER SÚBDITOS")


@M.escena("super", "mapa", prof=lambda b: [(0, "puntero"), ("súper", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("caitlyn_basico", .2 + j * .45) for j in range(int(max(1, (b.at("destruyes") + .4) / .45)))] + [("muerte", b.at("destruyes") + .4), ("ding", b.at("súper"))])
def super_(c, lt, b):
    t = b.t0 + lt
    td = b.at("destruyes") + .4
    you = (IX - 420, IY + 60)
    n = int(max(1, (b.at("destruyes") + .4) / .45))
    for j in range(n):
        shot(c, you, INH, (lt - .2 - j * .45) / .25, "bala", BLUE)
    hp_bar(c, max(0, 1 - lt / max(.1, td))) if lt < td else None
    broken(c, ease((lt - td) / .3), t)
    M.burst(c, INH, pulse(lt, td, 3), 0xFFFF8A5A, 120)
    champ(c, *you, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.8)
    super_wave(c, lt, t, b.at("súper"), 1, IX - 900)
    with b.hud(c):
        caption(c, "TU BASE MANDA SÚPER SÚBDITOS", (lt - b.at("súper")) / .3, 0xFFC8A8F8)


@M.escena("presion", "mapa", cam=lambda b: [(0, (IX - 600, IY - 60, 1.0))], sfx=lambda b: [("golpe_subdito", .5 + j * .5, 1.5) for j in range(8)])
def presion(c, lt, b):
    t = b.t0 + lt
    broken(c, 1, t)
    super_wave(c, lt, t, 0, 1, IX - 1300)
    with b.hud(c):
        caption(c, "ENORMES · AGUANTAN · PEGAN FUERTE", (lt - b.at("enormes")) / .3, 0xFFC8A8F8)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, (IX - 600, IY - 60, 1.0))], sfx=lambda b: [("recall_llega", b.at("regresas"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    broken(c, 1, t)
    super_wave(c, lt, t, 0, 1, IX - 1200)
    gone = ease((lt - b.at("regresas")) / .5)
    champ(c, IX - 1100, IY + 200, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.8, a=1 - gone)
    with b.hud(c):
        caption(c, "TÚ EN BASE · ELLOS SIGUEN EMPUJANDO", (lt - b.at("siguen")) / .3, 0xFF8EE08E)


@M.escena("tres", "mapa", cam=lambda b: [(0, (G.W - 1300, G.H / 2, .55))], sfx=lambda b: [("ding", b.at("dos"))])
def tres(c, lt, b):
    t = b.t0 + lt
    for lane in ("superior", "central", "inferior"):
        y = G.lane_y(lane, IX)
        k = ease((lt - b.at("tres")) / .4)
        if k > 0:
            c.drawCircle(IX, y, 100, M.fill(M.alpha(0xFF3A3F48, k)))
        for j in range(2):
            if lt > b.at("dos"):
                minion(c, IX - 900 + (lt - b.at("dos")) * 200 - j * 150, y + (j - .5) * 90, "azul", 1, t, kind="super", s=1.3)
    with b.hud(c):
        caption(c, "LOS 3 ROTOS = 2 SÚPER POR LÍNEA", (lt - b.at("dos")) / .3, 0xFFC8A8F8)


@M.escena("vuelve", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("cinco"))])
def vuelve(c, lt, b):
    t = b.t0 + lt
    k = ease((lt - b.at("cinco") - .6) / .8)
    broken(c, 1 - k, t)
    with b.hud(c):
        K.cd_clock(c, 540, 1240, k, ease((lt - b.at("cinco")) / .3), "5'", 0x99E84855)
        caption(c, "REAPARECE A LOS 5 MINUTOS", (lt - b.at("cinco")) / .3, GOLD)


@M.escena("aviso", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("anunciador")), ("ding", b.at("anunciador") + .4)])
def aviso(c, lt, b):
    t = b.t0 + lt
    broken(c, 1, t)
    with b.hud(c):
        M.badge(c, "¡INHIBIDOR POR REAPARECER!", 540, 380, 44, 0xFFFF6B74, 0xFFFFFFFF, (lt - b.at("anunciador")) / .3)
        caption(c, "AVISO ~15 s ANTES", (lt - b.at("quince")) / .3, GOLD)


@M.escena("nexo", "mapa", prof=lambda b: [(0, "puntero"), ("nexo", "asombro")], cam=lambda b: [(0, (G.W - 650, G.H / 2 + 200, .8))],
          sfx=lambda b: [("ding", b.at("nexo"))])
def nexo(c, lt, b):
    t = b.t0 + lt
    broken(c, 1, t)
    k = ease((lt - b.at("torres")) / .4)
    for tx, ty, team in G.TURRETS:
        if tx > G.W - 1700 and team == RED:
            M.ring(c, (tx, ty - 80), 120, k, RED, None, t)
    M.ring(c, (G.W - 300, G.H / 2 - 150), 220, ease((lt - b.at("nexo")) / .4), RED, "ATACABLE", t)
    with b.hud(c):
        caption(c, "TORRES DEL NEXO Y NEXO: YA SE PUEDEN ATACAR", (lt - b.at("nexo")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
