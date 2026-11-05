"""Class 14: Smite (600 true damage to monsters/minions, 2 charges, 90 s recharge, 500 range; Unleashed 1000 after 15 treats,
Primal 1400 to nearby monsters after 35; upgraded can hit champions for a little damage + slow)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=14)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse  # noqa: E402

JY = (M.G.lane_y("central", 4000) + M.G.lane_y("inferior", 4000)) / 2
MON = (4100, JY)
YOU = (3780, JY + 40)
CAM = (3960, JY - 60, 1.3)
BARON = M.G.BARON


def bolt(c, x, y, k, color=0xFFFFE27A, w=1.0):
    """Lightning strike from above (k = seconds since the smite) + the official Smite icon."""
    M.spell_pop(c, "SummonerSmite", x - 170, y - 230, k, 100)
    if not 0 <= k < .5:
        return
    a = 1 - k / .5
    pts = [(x + math.sin(j * 7.3) * 30 * w, y - 600 + j * 100) for j in range(7)] + [(x, y)]
    c.drawPath(M.path(pts, close=False), M.stroke(22 * w, M.alpha(color, a * .5)))
    c.drawPath(M.path(pts, close=False), M.stroke(9 * w, M.alpha(0xFFFFFFFF, a)))
    M.burst(c, (x, y), a, color, 70 * w)


def smite_dmg(c, x, y, k, amount):
    if 0 < k < 1.4:
        M.text(c, f"-{amount}", x + 60, y - 150 - 50 * ease(k), M.font("segoeuib.ttf", 54), M.alpha(0xFFFFFFFF, 1 - max(0, k - 1) / .4), 10)


# ---------------- classroom
M.pizarra("hook", [("¿POR QUÉ EL JUNGLA", 540, 460, 84, CHALK, .1), ("SIEMPRE LLEVA SMITE?", 540, 600, 84, CHALK_Y, "smite")],
          prof=[(0, "piensa")], extra=lambda c, lt, b: M.icono(c, "SummonerSmite", 540, 860, 220, (lt - b.at("smite")) / .4))
M.pizarra("spoiler", [("SIN ÉL: JUNGLA LENTÍSIMA", 540, 500, 74, CHALK, "lentísimo"), ("Y OBJETIVOS PERDIDOS", 540, 660, 80, CHALK_R, "objetivos")],
          prof=[(0, "explica")])
M.pizarra("verdadero", [("DAÑO VERDADERO", 540, 500, 100, CHALK_Y, "verdadero"), ("IGNORA ARMADURA", 540, 650, 80, CHALK, "armadura"),
                        ("Y RESISTENCIA MÁGICA", 540, 760, 80, CHALK, "resistencia")], prof=[(0, "explica")])


def cargas_extra(c, lt, b):
    for j in range(2):
        K.cd_clock(c, 380 + j * 320, 820, 1 if lt < b.at("noventa") else 1 - clamp((lt - b.at("noventa")) / 2.5) * (j == 0), (lt - b.at("dos") - j * .2) / .3, "S", 0x99FFE27A)


M.pizarra("cargas", [("2 CARGAS", 540, 460, 100, CHALK, "dos"), ("90 s CADA UNA", 540, 590, 90, CHALK_Y, "noventa")],
          prof=[(0, "explica")], extra=cargas_extra)
M.pizarra("broma", [("EL ÚLTIMO TACO", 540, 500, 100, CHALK, "taco"), ("SE LO COME EL QUE LLEGA", 540, 680, 74, CHALK_Y, "come")],
          prof=[(0, "feliz")])
M.pizarra("nervios", [("NO LO GASTES", 540, 520, 100, CHALK_R, "gastes"), ("POR NERVIOS", 540, 680, 100, CHALK, "nervios")],
          prof=[(0, "explica"), ("importa", "guino")])
M.pizarra("rival", [("JUNGLA RIVAL CERCA", 540, 520, 84, CHALK, "jungla"), ("CUIDA TU SMITE", 540, 680, 100, CHALK_Y, "cuida"),
                    ("COMO TU CARTERA", 540, 820, 76, CHALK_R, "cartera")], prof=[(0, "picara")])
M.pizarra("ambos", [("ÉL TAMBIÉN TIENE UNO", 540, 520, 84, CHALK, "suyo"), ("DUELO DE REFLEJOS", 540, 690, 90, CHALK_Y, "duelo")],
          prof=[(0, "explica")])
K.cierre_teemo("600 DAÑO VERDADERO · 2 CARGAS", "EL ÚLTIMO GOLPE GANA EL OBJETIVO", "1 LIKE = 1 SMITE")


# ---------------- jungle
@M.escena("que", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("impacto", b.at("seiscientos")), ("ding", b.at("monstruo"))])
def que(c, lt, b):
    t = b.t0 + lt
    ts = b.at("seiscientos")
    K.monster(c, *MON, .9, t, 0xFF6ABF6A, 0xFFCFF0C0, "blob", sprite="gromp", k=1, hp=1 - .35 * (lt > ts), flash=pulse(lt, ts, 8))
    bolt(c, *MON, lt - ts)
    smite_dmg(c, *MON, lt - ts, 600)
    champ(c, *YOU, "Warwick", "azul", "TÚ", 1, 0, 1, s=.85)
    with b.hud(c):
        M.sign(c, t, lt / .5, "SMITE", "EL HECHIZO DEL JUNGLA")
        caption(c, "600 DE DAÑO VERDADERO", (lt - ts) / .3, 0xFFFFE27A)


@M.escena("rango", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("quinientas"))])
def rango(c, lt, b):
    t = b.t0 + lt
    M.ring(c, YOU, 500 * M.UNIT, (lt - b.at("alcance")) / .4, 0xFFFFE27A, "500 UNIDADES" if lt > b.at("quinientas") else None, t)
    K.monster(c, *MON, .9, t, 0xFF6ABF6A, 0xFFCFF0C0, "blob", sprite="gromp", k=1)
    champ(c, *YOU, "Warwick", "azul", "TÚ", 1, 0, 1, s=.85)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("cerca"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    M.ring(c, YOU, 500 * M.UNIT, 1, 0xFFFFE27A, None, t)
    K.monster(c, *MON, .9, t, 0xFF6ABF6A, 0xFFCFF0C0, "blob", sprite="gromp", k=1)
    champ(c, YOU[0] + 80 * ease(lt / 1.5), YOU[1], "Warwick", "azul", "TÚ", 1, 0, 1, s=.85)
    with b.hud(c):
        caption(c, "CERCA, PERO NO ENCIMA", (lt - b.at("cerca")) / .3, GOLD)


def pet(c, x, y, s, t, k=1.0):
    if k <= 0:
        return
    c.save()
    c.translate(x, y + math.sin(t * 6) * 6)
    c.scale(s * M.back(min(1, k)), s * M.back(min(1, k)))
    c.drawOval(M.skia.Rect.MakeXYWH(-40, -36, 80, 72), M.fill(0xFF7AD0A0))
    c.drawOval(M.skia.Rect.MakeXYWH(-40, -36, 80, 72), M.stroke(5))
    for sx in (-1, 1):
        c.drawPath(M.path([(sx * 18, -30), (sx * 30, -60), (sx * 36, -26)]), M.fill(0xFF7AD0A0))
        c.drawPath(M.path([(sx * 18, -30), (sx * 30, -60), (sx * 36, -26)]), M.stroke(4))
        c.drawCircle(sx * 14, -6, 7, M.fill(M.INK))
    c.restore()


@M.escena("mascota", "mapa", prof=lambda b: [(0, "puntero"), ("mil", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("oro", b.at("quince")), ("impacto", b.at("mil"))])
def mascota(c, lt, b):
    t = b.t0 + lt
    pet(c, YOU[0] - 90, YOU[1] - 120, 1.0, t, (lt - b.at("mascota")) / .3)
    n = int(clamp((lt - b.at("premios")) / 1.2) * 15)
    badge(c, f"{n}/15", YOU[0] - 90, YOU[1] - 220, 30, GOLD, M.INK, 1 if lt > b.at("premios") else 0)
    tm = b.at("mil")
    K.monster(c, *MON, .9, t, 0xFF6ABF6A, 0xFFCFF0C0, "blob", sprite="gromp", k=1, hp=1 - .5 * (lt > tm), flash=pulse(lt, tm, 8))
    bolt(c, *MON, lt - tm, 0xFF9AF0C0, 1.3)
    smite_dmg(c, *MON, lt - tm, 1000)
    champ(c, *YOU, "Warwick", "azul", "TÚ", 1, 0, 1, s=.85)


@M.escena("primal", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("impacto", b.at("mil")), ("impacto", b.at("mil") + .1)])
def primal(c, lt, b):
    t = b.t0 + lt
    tm = b.at("mil")
    for j, dx in enumerate((-140, 0, 140)):
        K.monster(c, MON[0] + dx, MON[1] + (60 if j != 1 else 0), .6 if j != 1 else .9, t, 0xFF6ABF6A, 0xFFCFF0C0, "blob", sprite="gromp", k=1,
                  hp=1 - .6 * (lt > tm), flash=pulse(lt, tm, 8))
    bolt(c, *MON, lt - tm, 0xFF9AF0C0, 1.6)
    M.ring(c, MON, 260, ease((lt - tm) / .2) * (1 - ease((lt - tm - .6) / .3)), 0xFF9AF0C0, None, t)
    smite_dmg(c, *MON, lt - tm, 1400)
    pet(c, YOU[0] - 90, YOU[1] - 120, 1.2, t)
    champ(c, *YOU, "Warwick", "azul", "TÚ", 1, 0, 1, s=.85)
    with b.hud(c):
        caption(c, "35 PREMIOS: 1,400 (Y A LOS DE ALREDEDOR)", (lt - b.at("treinta")) / .3, 0xFF9AF0C0)


@M.escena("campeones", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("impacto", b.at("golpear"))])
def campeones(c, lt, b):
    t = b.t0 + lt
    tg = b.at("golpear")
    enemy = (MON[0], MON[1] + 20)
    bolt(c, *enemy, lt - tg, 0xFF9AF0C0)
    champ(c, *enemy, "LeeSin", "rojo", "RIVAL", 1, pulse(lt, tg, 8), 1 - .05 * (lt > tg), s=.85)
    badge(c, "LENTO", enemy[0], enemy[1] + 150, 30, 0xFF9AD0F5, M.INK, (lt - b.at("ralentiza")) / .3)
    champ(c, *YOU, "Warwick", "azul", "TÚ", 1, 0, 1, s=.85)
    with b.hud(c):
        caption(c, "POQUITO DAÑO, PERO RALENTIZA", (lt - b.at("poquito")) / .3, 0xFF9AD0F5)


@M.escena("robo", "mapa", prof=lambda b: [(0, "puntero"), ("último", "feliz")], cam=lambda b: [(0, (BARON[0], BARON[1] - 60, 1.15))],
          sfx=lambda b: [("impacto", b.at("último")), ("anciano_muere", b.at("último") + .3)])
def robo(c, lt, b):
    t = b.t0 + lt
    tu = b.at("último")
    hp = max(.04, .4 - lt * .05) if lt < tu else 0
    K.monster(c, *BARON, .9, t, 0xFF8A5AD0, None, "baron", 1 - ease((lt - tu - .3) / .4), hp=hp, flash=pulse(lt, tu, 8))
    bolt(c, *BARON, lt - tu)
    champ(c, BARON[0] - 330, BARON[1] + 120, "LeeSin", "rojo", "RIVAL", 1, 0, 1, s=.8)
    champ(c, BARON[0] + 330, BARON[1] + 160, "Warwick", "azul", "TÚ", 1, 0, 1, s=.8)
    with b.hud(c):
        caption(c, "EL ÚLTIMO GOLPE SE LO LLEVA", (lt - tu) / .3, GOLD)


@M.escena("cuenta", "mapa", prof=lambda b: [(0, "puntero"), ("ahí", "guino")], cam=lambda b: [(0, (MON[0], MON[1] - 80, 1.6))],
          sfx=lambda b: [("impacto", b.at("ahí"))])
def cuenta(c, lt, b):
    t = b.t0 + lt
    ta = b.at("ahí")
    hp = max(.12, 1 - lt / max(1, ta) * .88) if lt < ta else 0
    K.monster(c, *MON, .9, t, 0xFF6ABF6A, 0xFFCFF0C0, "blob", sprite="gromp", k=1 - ease((lt - ta - .3) / .4), hp=hp, flash=pulse(lt, ta, 8))
    if lt < ta:
        x0 = MON[0] - 67
        c.drawLine(x0 + 135 * .14, MON[1] - 175, x0 + 135 * .14, MON[1] - 150, M.stroke(6, 0xFFFFE27A))
    bolt(c, *MON, lt - ta)
    with b.hud(c):
        caption(c, "VIDA < 600 → ¡SMITE!", (lt - b.at("vida")) / .3, 0xFFFFE27A)


if __name__ == "__main__":
    M.main()
