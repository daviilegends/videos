"""Class 21: Ignite (true damage over 5 s, Grievous Wounds -40% healing and regen for 5 s, reveals the target, 600 range,
180 s cooldown)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=21)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse  # noqa: E402

LY = M.G.lane_y("inferior", 6000)
YOU, RIV = (5780, LY + 30), (6200, LY - 30)
CAM = (5990, LY - 60, 1.35)
FIRE = 0xFFFF8A3A


def flames(c, pos, k, t):
    if k <= 0:
        return
    for j in range(8):
        ph = (t * 1.8 + j / 8) % 1
        c.drawCircle(pos[0] - 60 + j * 17, pos[1] - 40 - ph * 130, 16 * (1 - ph) * k, M.fill(M.alpha(FIRE, (1 - ph) * k)))


def ignite_cast(c, lt, t0, src=YOU, dst=RIV):
    M.spell_pop(c, "SummonerDot", src[0], src[1] - 190, lt - t0)
    k = (lt - t0) / .3
    if 0 <= k < 1:
        p = (src[0] + (dst[0] - src[0]) * k, src[1] + (dst[1] - src[1]) * k)
        c.drawCircle(*p, 26, M.fill(FIRE))
        c.drawCircle(*p, 26, M.stroke(5))


def heal_bar(c, x, y, base, gained, k):
    """HUD: a heal that comes in at full or at 60% (grievous wounds)."""
    if k <= 0:
        return
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x, y, 500, 40), 14, 14, M.fill(0xEE0A1424))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x + 4, y + 4, 492 * base, 32), 12, 12, M.fill(0xFF4CD07A))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x + 4 + 492 * base, y + 4, 492 * gained, 32), 12, 12, M.fill(0xFFB8F0C0))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x, y, 500, 40), 14, 14, M.stroke(4, GOLD))


# ---------------- classroom
M.pizarra("hook", [("IGNITE:", 540, 470, 120, FIRE, .1), ("TERROR DE LOS QUE SE CURAN", 540, 640, 70, CHALK, "curan")],
          prof=[(0, "picara")], extra=lambda c, lt, b: M.icono(c, "SummonerDot", 540, 880, 220, (lt - .4) / .4))
M.pizarra("spoiler", [("NO SOLO QUEMA", 540, 520, 100, CHALK, "quema"), ("CORTA LA CURACIÓN", 540, 690, 96, CHALK_R, "curación")],
          prof=[(0, "explica")])
M.pizarra("verdadero", [("DAÑO VERDADERO", 540, 520, 100, CHALK_Y, "verdadero"), ("NO IMPORTA LA ARMADURA", 540, 690, 80, CHALK, "armadura")],
          prof=[(0, "explica")])
M.pizarra("broma", [("SAL EN LA HERIDA", 540, 540, 110, CHALK_R, "sal"), ("LITERAL", 540, 720, 100, CHALK, "literal")],
          prof=[(0, "picara")])
M.pizarra("comparacion", [("MENOS QUE FLASH (300 s)", 540, 520, 76, CHALK, "flash"), ("PERO MAL USADO = A ESPERAR", 540, 690, 72, CHALK_R, "esperar")],
          prof=[(0, "explica")])
M.pizarra("cuando", [("¿CUÁNDO?", 540, 460, 120, CHALK, 0), ("A PUNTO DE CURARSE", 540, 640, 84, CHALK_Y, "curarse"),
                     ("O YA CASI LO TIENES", 540, 780, 84, CHALK_Y, "tienes")], prof=[(0, "explica")])
M.pizarra("no", [("NO AL INICIO", 540, 520, 110, CHALK_R, "inicio"), ("GUÁRDALO PARA REMATAR", 540, 700, 80, 0xFF8EE08E, "rematar")],
          prof=[(0, "explica"), ("rematar", "guino")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("¿RIVAL SANADOR?", 540, 580, 100, CHALK, "sanador"),
                  ("IGNITE LE ARRUINA EL DÍA", 540, 740, 76, FIRE, "arruina")], prof=[(0, "picara")])
M.pizarra("tip2", [("¿TÚ TE CURAS MUCHO?", 540, 520, 90, CHALK, "cura"), ("CUIDADO CON SU IGNITE", 540, 690, 84, CHALK_R, "ignite")],
          prof=[(0, "asombro")])
M.pizarra("tip3", [("LO VES BRILLAR →", 540, 520, 96, CHALK, "brillar"), ("ALÉJATE", 540, 700, 140, CHALK_R, "aléjate")],
          prof=[(0, "explica")])
K.cierre_teemo("DAÑO VERDADERO · 5 s", "HERIDAS GRAVES: -40% CURACIÓN", "1 LIKE = 1 IGNITE")


# ---------------- lane
@M.escena("que", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ignite", b.at("quema"))])
def que(c, lt, b):
    t = b.t0 + lt
    tq = b.at("quema")
    ignite_cast(c, lt, tq)
    flames(c, RIV, ease((lt - tq - .3) / .3), t)
    hp = 1 - .5 * clamp((lt - tq - .3) / 3.0)
    champ(c, *RIV, "Soraka", "rojo", "RIVAL", 1, 0, hp, s=.85)
    champ(c, *YOU, "Garen", "azul", "TÚ", 1, 0, 1, s=.85)
    with b.hud(c):
        M.sign(c, t, lt / .5, "IGNITE", "QUEMAR Y CORTAR")
        caption(c, "DAÑO VERDADERO DURANTE 5 s", (lt - b.at("cinco")) / .3, FIRE)


@M.escena("heridas", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("heridas"))])
def heridas(c, lt, b):
    t = b.t0 + lt
    flames(c, RIV, 1, t)
    champ(c, *RIV, "Soraka", "rojo", "RIVAL", 1, 0, .5, s=.85)
    k = ease((lt - b.at("heridas")) / .3)
    if k > 0:
        M.chalk_cross(c, RIV[0] + 110, RIV[1] - 120, k, RED, .8)
    champ(c, *YOU, "Garen", "azul", "TÚ", 1, 0, 1, s=.85)
    with b.hud(c):
        caption(c, "HERIDAS GRAVES", (lt - b.at("heridas")) / .3, RED)


@M.escena("cuarenta", "mapa", prof=lambda b: [(0, "puntero"), ("cuarenta", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ding", b.at("cuarenta"))])
def cuarenta(c, lt, b):
    t = b.t0 + lt
    flames(c, RIV, 1, t)
    champ(c, *RIV, "Soraka", "rojo", "RIVAL", 1, 0, .5, s=.85)
    with b.hud(c):
        M.big_number(c, "-40%", 300, 620, (lt - b.at("cuarenta")) / .35, RED)
        caption(c, "CURACIÓN Y REGENERACIÓN", (lt - b.at("curación")) / .3, RED)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("cien")), ("ignite", b.at("sesenta"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    champ(c, *RIV, "Soraka", "rojo", "RIVAL", 1, 0, .5, s=.85)
    with b.hud(c):
        heal_bar(c, 290, 560, .3, .3 * clamp((lt - b.at("cien")) / .6), ease((lt - b.at("cien")) / .3))
        M.text(c, "SIN IGNITE: +100", 540, 540, M.font("segoeuib.ttf", 40), 0xFF8EE08E, 8)
        heal_bar(c, 290, 760, .3, .18 * clamp((lt - b.at("sesenta")) / .6), ease((lt - b.at("sesenta")) / .3))
        M.text(c, "CON IGNITE: +60", 540, 740, M.font("segoeuib.ttf", 40), FIRE, 8)


@M.escena("revela", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("arbusto", b.at("arbusto"))])
def revela(c, lt, b):
    t = b.t0 + lt
    br = M.G._brush_pos(6950, "inferior", -1)
    flames(c, br, 1, t)
    champ(c, *br, "Soraka", "rojo", "RIVAL", 1, 0, .4, s=.85, a=1.0)
    with b.hud(c):
        caption(c, "TE VEN AUNQUE TE ESCONDAS", (lt - b.at("revela")) / .3, FIRE)


@M.escena("rango", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("seiscientas"))])
def rango(c, lt, b):
    t = b.t0 + lt
    M.ring(c, YOU, 600 * M.UNIT, (lt - b.at("alcance")) / .4, FIRE, "600 UNIDADES" if lt > b.at("seiscientas") else None, t)
    champ(c, *YOU, "Garen", "azul", "TÚ", 1, 0, 1, s=.85)
    champ(c, *RIV, "Soraka", "rojo", "RIVAL", 1, 0, 1, s=.85)


@M.escena("cd", "mapa", prof=lambda b: [(0, "puntero"), ("tres", "asombro")], cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("ciento"))])
def cd(c, lt, b):
    t = b.t0 + lt
    champ(c, *YOU, "Garen", "azul", "TÚ", 1, 0, 1, s=.85)
    with b.hud(c):
        K.cd_clock(c, 540, 1240, 1 - clamp((lt - b.at("ciento")) / 4), ease((lt - b.at("enfriamiento")) / .3), "I", 0x99FF8A3A)
        M.big_number(c, "180 s", 330, 620, (lt - b.at("ciento")) / .35, FIRE, 140)


if __name__ == "__main__":
    M.main()
