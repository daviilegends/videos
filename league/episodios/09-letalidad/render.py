"""Class 09: Lethality vs % armor penetration. Facts (wiki): damage x 100/(100+armor) -> 100 armor = half; lethality =
flat armor pen, full value at every level since V14.1; Lord Dominik's Regards 35% armor pen; Youmuu's 18 lethality;
order: % penetration first, then lethality."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=9)
import kit as K  # noqa: E402
from motor import CHALK, CHALK_R, CHALK_Y, GOLD, RED, caption, champ, clamp, ease  # noqa: E402

LY = M.G.lane_y("central", 6000)
YOU, RIV = (5780, LY + 40), (6230, LY - 30)
CAM = (6000, LY - 80, 1.3)
STEEL = 0xFFB9C7D6
LETAL = 0xFFFF6A5A
PCT = 0xFFB98CFF
YOUMUU, DOMINIK = "objetos/3142", "objetos/3036"


def shield(c, x, y, value, k, color=STEEL, label="ARMADURA", s=1.0):
    """Armor badge: steel shield with the current armor number (animated by the caller)."""
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    sc = M.back(min(1, k)) * s
    c.scale(sc, sc)
    p = M.path([(-62, -70), (62, -70), (62, 0), (0, 78), (-62, 0)])
    c.drawPath(p, M.fill(0xEE0E1418))
    c.drawPath(p, M.stroke(7, color))
    M.text(c, f"{round(value)}", 0, 8, M.font("segoeuib.ttf", 52), 0xFFFFFFFF, 8)
    M.text(c, label, 0, 112, M.font("segoeuib.ttf", 26), color, 6)
    c.restore()


def swipe(c, a, b_, k, color=LETAL):
    """Slash from attacker to target (k = seconds since the hit)."""
    if not 0 <= k < .35:
        return
    a_ = 1 - k / .35
    mx, my = (a[0] + b_[0]) / 2, (a[1] + b_[1]) / 2 - 40
    c.drawPath(M.path([a, (mx, my), b_], close=False), M.stroke(16, M.alpha(color, a_ * .8)))
    M.burst(c, b_, a_, color, 60)


def dmg(c, x, y, k, txt, color=0xFFFFFFFF, size=56):
    if 0 < k < 1.4:
        M.text(c, txt, x, y - 50 * ease(k), M.font("segoeuib.ttf", size), M.alpha(color, 1 - max(0, k - 1) / .4), 10)


# ---------------- classroom
def hook_extra(c, lt, b):
    M.icono(c, YOUMUU, 330, 870, 190, (lt - b.at("letalidad")) / .4)
    M.chalk_line(c, "VS", 540, 900, 90, (lt - b.at("penetración")) / .3, CHALK)
    M.icono(c, DOMINIK, 750, 870, 190, (lt - b.at("armadura")) / .4)


M.pizarra("hook", [("¿LETALIDAD", 540, 450, 104, LETAL, .1), ("O PENETRACIÓN?", 540, 600, 96, PCT, "penetración")],
          prof=[(0, "piensa"), ("basura", "asombro")], extra=hook_extra)
M.pizarra("spoiler", [("LAS DOS IGNORAN ARMADURA", 540, 520, 76, CHALK, "ignoran"), ("PERO NO IGUAL", 540, 690, 110, CHALK_Y, "igual")],
          prof=[(0, "explica"), ("igual", "guino")])


def pct_extra(c, lt, b):
    M.icono(c, DOMINIK, 540, 820, 200, (lt - b.at("dominik")) / .4)
    M.big_number(c, "-35%", 540, 1010, (lt - b.at("treinta")) / .35, PCT, 120)


M.pizarra("porcentaje", [("% = PORCENTAJE", 540, 500, 100, PCT, "porcentual")], prof=[(0, "explica")], extra=pct_extra)
M.pizarra("broma", [("TIRAR UN MURO", 540, 520, 110, CHALK, "muro"), ("CON UNA CUCHARA", 540, 690, 100, CHALK_R, "cuchara")],
          prof=[(0, "picara")], extra=lambda c, lt, b: M.chalk_cross(c, 540, 900, (lt - b.at("cuchara") - .3) / .3, RED, 1.2))


def regla_extra(c, lt, b):
    M.icono(c, YOUMUU, 900, 610, 110, (lt - b.at("letalidad")) / .4)
    M.icono(c, DOMINIK, 900, 850, 110, (lt - b.at("porcentaje")) / .4)


M.pizarra("regla", [("REGLA DE LA PROFE", 540, 400, 64, GOLD, 0),
                    ("¿POCA ARMADURA?", 500, 540, 76, CHALK, "poca"), ("→ LETALIDAD", 500, 640, 84, LETAL, "letalidad"),
                    ("¿PURAS ARMADURAS?", 500, 780, 76, CHALK, "puras"), ("→ PORCENTAJE", 500, 880, 84, PCT, "porcentaje")],
          prof=[(0, "explica"), ("porcentaje", "guino")], extra=regla_extra)
M.pizarra("orden", [("¿LAS DOS?", 540, 450, 110, CHALK, "dos"), ("1° EL %", 540, 640, 100, PCT, "porcentaje"),
                    ("2° LA LETALIDAD", 540, 790, 100, LETAL, "después"), ("SE COMPLEMENTAN", 540, 960, 76, 0xFF8EE08E, "complementan")],
          prof=[(0, "explica"), ("complementan", "feliz")])
M.pizarra("nivel", [("DESDE EL PARCHE 14", 540, 500, 88, CHALK, "parche"), ("LETALIDAD COMPLETA", 540, 660, 92, LETAL, "completo"),
                    ("DESDE NIVEL 1", 540, 800, 100, CHALK_Y, "uno")], prof=[(0, "explica")])


def tip_extra(c, lt, b):
    for j, it in enumerate(("objetos/3143", "objetos/3075", "objetos/1029")):
        M.icono(c, it, 330 + j * 210, 900, 150, (lt - b.at("armaduras") - j * .15) / .3)


M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 400, 60, GOLD, 0), ("MIRA SUS OBJETOS", 540, 560, 100, CHALK, "objetos"),
                  ("¿ARMADURAS? CAMBIA EL PLAN", 540, 720, 70, CHALK_Y, "plan")], prof=[(0, "explica"), ("plan", "guino")], extra=tip_extra)
K.cierre_teemo("LETALIDAD: RESTA FIJA (18 = -18)", "% : RESTA PORCENTAJE (35%)", "1 LIKE = 1 PUNTO DE LETALIDAD")


# ---------------- lane
@M.escena("armadura", "mapa", prof=lambda b: [(0, "puntero"), ("mitad", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("impacto", b.at("mitad"))])
def armadura(c, lt, b):
    t = b.t0 + lt
    th = b.at("mitad")
    champ(c, *RIV, "Malphite", "rojo", "RIVAL", 1, M.pulse(lt, th, 8), 1 - .1 * (lt > th), s=.9)
    champ(c, *YOU, "Zed", "azul", "TÚ", 1, 0, 1, s=.9)
    swipe(c, YOU, RIV, lt - th)
    shield(c, RIV[0], RIV[1] - 270, 100, ease((lt - b.at("cien")) / .3))
    dmg(c, RIV[0] - 230, RIV[1] - 120, lt - th, "100 → 50", GOLD)
    with b.hud(c):
        M.sign(c, t, lt / .5, "LETALIDAD VS %", "QUIÉN ROMPE ARMADURA")
        caption(c, "100 ARMADURA = RECIBE LA MITAD", (lt - b.at("mitad")) / .3, STEEL)


@M.escena("letalidad", "mapa", prof=lambda b: [(0, "puntero")], cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("fija"))])
def letalidad(c, lt, b):
    tf = b.at("fija")
    M.spell_pop(c, YOUMUU, YOU[0], YOU[1] - 190, lt - tf, 110, 2.6)
    champ(c, *YOU, "Zed", "azul", "TÚ", 1, 0, 1, s=.9)
    champ(c, *RIV, "Caitlyn", "rojo", "RIVAL", 1, 0, 1, s=.9)
    k = clamp((lt - b.at("menos")) / .8)
    shield(c, RIV[0], RIV[1] - 270, 30 - 18 * ease(k), 1, LETAL if k > 0 else STEEL)
    with b.hud(c):
        caption(c, "LETALIDAD = RESTA FIJA", (lt - tf) / .3, LETAL)
        M.big_number(c, "-18", 300, 620, (lt - b.at("dieciocho")) / .35, LETAL, 130)


@M.escena("debil", "mapa", prof=lambda b: [(0, "puntero"), ("nada", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("impacto", b.at("pegas")), ("impacto", b.at("pegas") + .5), ("habilidad_hit", b.at("nada"))])
def debil(c, lt, b):
    tp = b.at("pegas")
    hits = [tp, tp + .5, b.at("nada")]
    hp = 1 - .28 * sum(lt > h for h in hits)
    fl = max(M.pulse(lt, h, 8) for h in hits)
    champ(c, *RIV, "Caitlyn", "rojo", "RIVAL", 1, fl, hp, s=.9)
    champ(c, *YOU, "Zed", "azul", "TÚ", 1, 0, 1, s=.9)
    for h in hits:
        swipe(c, YOU, RIV, lt - h)
        dmg(c, RIV[0] - 200, RIV[1] - 110, lt - h, "-310", GOLD)
    shield(c, RIV[0], RIV[1] - 270, 12, 1, LETAL, "30 → 12")
    with b.hud(c):
        caption(c, "TIRADOR: 30 → 12 DE ARMADURA", (lt - b.at("tirador")) / .3, LETAL)


@M.escena("tanque", "mapa", prof=lambda b: [(0, "puntero"), ("cosquillas", "picara")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ding", b.at("ciento")), ("impacto", b.at("cosquillas"))])
def tanque(c, lt, b):
    tc = b.at("cosquillas")
    champ(c, *RIV, "Malphite", "rojo", "TANQUE", 1, M.pulse(lt, tc, 8), .98 if lt > tc else 1, s=1.0)
    champ(c, *YOU, "Zed", "azul", "TÚ", 1, 0, 1, s=.9)
    swipe(c, YOU, RIV, lt - tc, 0xFF8A93A0)
    dmg(c, RIV[0] + 150, RIV[1] - 60, lt - tc, "-1", 0xFFB0B0B0, 46)
    with b.hud(c):
        shield(c, 540, 330, 300, ease((lt - b.at("trescientos")) / .3), STEEL, "TANQUE", 1.1)
        k1 = ease((lt - b.at("ciento")) / .4)
        if k1 > 0:
            M.icono(c, DOMINIK, 200, 610, 110, k1)
            shield(c, 370, 600, 300 - 105 * clamp((lt - b.at("ciento")) / .8), k1, PCT, "35% → 195", .8)
        k2 = ease((lt - b.at("letalidad")) / .4)
        if k2 > 0:
            M.icono(c, YOUMUU, 640, 610, 110, k2)
            shield(c, 810, 600, 300 - 18 * clamp((lt - b.at("letalidad")) / .8), k2, LETAL, "-18 → 282", .8)


@M.escena("asesinos", "mapa", prof=lambda b: [(0, "puntero"), ("magos", "guino")], cam=lambda b: [(0, (6000, LY - 80, 1.15))],
          sfx=lambda b: [("impacto", b.at("cazan")), ("impacto", b.at("magos"))])
def asesinos(c, lt, b):
    a1, a2 = (5800, LY - 140), (6250, LY + 90)
    t1, t2 = b.at("cazan"), b.at("magos")
    zx = YOU if lt < t1 else ((a1[0] - 120, a1[1] + 160) if lt < t2 else (a2[0] - 240, a2[1] - 10))
    champ(c, *a1, "Caitlyn", "rojo", "TIRADOR", 1, M.pulse(lt, t1, 8), .35 if lt > t1 else 1, s=.85)
    champ(c, *a2, "Karma", "rojo", "MAGO", 1, M.pulse(lt, t2, 8), .35 if lt > t2 else 1, s=.85)
    shield(c, a1[0] + 150, a1[1] - 30, 30, ease((lt - b.at("armadura")) / .3), STEEL, "POCA", .7)
    shield(c, a2[0] + 150, a2[1] - 30, 25, ease((lt - b.at("armadura")) / .3), STEEL, "POCA", .7)
    swipe(c, zx, a1, lt - t1)
    swipe(c, zx, a2, lt - t2)
    champ(c, *zx, "Zed", "azul", "ASESINO", 1, 0, 1, s=.9)
    with b.hud(c):
        caption(c, "ASESINOS → LETALIDAD", (lt - b.at("asesinos")) / .3, LETAL)


if __name__ == "__main__":
    M.main()
