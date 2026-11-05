"""Class 20: death timer (base wait by level: 10 s at level 1 ... 16 s at 6, 35 s at 11, 52.5 s at 18; from 15:00 a time
factor grows every half minute, capped at +50%: maximum 78.75 s)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=20)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse, shot  # noqa: E402

LY = M.G.lane_y("central", 6000)
YOU = (6000, LY)
CAM = (6000, LY - 80, 1.4)


def gray_screen(c, k, secs, t):
    """HUD: the gray death screen with a countdown."""
    if k <= 0:
        return
    c.drawRect(M.skia.Rect.MakeWH(M.W, M.H), M.fill(M.alpha(0xCC50545A, k)))
    f = M.font("segoeuib.ttf", 200)
    s_ = f"{secs}"
    M.text(c, s_, 540, 760, f, M.alpha(0xFFFFFFFF, k), 18)
    M.text(c, "REVIVES EN", 540, 520, M.font("segoeuib.ttf", 60), M.alpha(0xFFE8E8E8, k), 10)


def death(c, lt, b, t_die, total, shown_from=None):
    t = b.t0 + lt
    champ(c, *YOU, "Garen", "azul", "TÚ", 1, pulse(lt, t_die, 8), 0 if lt > t_die else .1, ease((lt - t_die) / .3), s=.9)
    k = ease((lt - t_die - .2) / .4)
    left = max(0, total - max(0, lt - t_die - .2) * (total / 6))
    return k, int(math.ceil(left))


# ---------------- classroom
M.pizarra("hook", [("AL PRINCIPIO: INSTANTE", 540, 450, 80, 0xFF8EE08E, "principio"), ("AL FINAL: ETERNIDAD", 540, 600, 84, CHALK_R, "eternidad")],
          prof=[(0, "piensa"), ("eternidad", "asombro")])
M.pizarra("spoiler", [("NO ES TU IMAGINACIÓN", 540, 520, 84, CHALK, "imaginación"), ("EL JUEGO TE CASTIGA", 540, 690, 90, CHALK_R, "castiga")],
          prof=[(0, "picara")])
M.pizarra("nivel", [("1. DEPENDE", 540, 520, 100, CHALK, "depende"), ("DE TU NIVEL", 540, 680, 110, CHALK_Y, "nivel")],
          prof=[(0, "explica")])


def ejemplo_extra(c, lt, b):
    for j, (lvl, s_, key) in enumerate(((6, "16 s", "seis"), (11, "35 s", "once"))):
        K.level_badge(c, 330, 620 + j * 220, lvl, (lt - b.at(key)) / .35, size=70)
        M.chalk_line(c, s_, 720, 650 + j * 220, 110, (lt - b.at(key) - .3) / .4, CHALK_Y)


M.pizarra("ejemplo", [("ANTES DEL MINUTO 15", 540, 440, 76, CHALK, "minuto")], prof=[(0, "explica")], extra=ejemplo_extra)
M.pizarra("tiempo", [("2. DESDE EL MINUTO 15", 540, 500, 84, CHALK, "quince"), ("SUMA UN EXTRA", 540, 650, 96, CHALK_Y, "extra"),
                     ("CADA MEDIO MINUTO", 540, 790, 80, CHALK, "medio")], prof=[(0, "explica")])
M.pizarra("tope", [("LÍMITE:", 540, 520, 110, CHALK, "límite"), ("+50%", 540, 720, 180, CHALK_R, "cincuenta")],
          prof=[(0, "explica")])
M.pizarra("broma", [("CASI 1 MIN Y MEDIO", 540, 480, 84, CHALK, "minuto"), ("CAFÉ… Y ARREPENTIRTE", 540, 660, 84, CHALK_Y, "café")],
          prof=[(0, "picara"), ("arrepentirte", "asombro")])
M.pizarra("por_que", [("MUERTO =", 540, 520, 120, CHALK, "muerto"), ("TU EQUIPO CON 1 MENOS", 540, 700, 80, CHALK_R, "menos")],
          prof=[(0, "explica")])
M.pizarra("tarde", [("UNA MUERTE TARDE =", 540, 460, 80, CHALK, "muerte"), ("BARÓN · INHIBIDOR", 540, 620, 90, CHALK_Y, "barón"),
                    ("· NEXO", 540, 760, 110, CHALK_R, "nexo")], prof=[(0, "asombro")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("MÁS TARDE =", 540, 580, 100, CHALK, "avanzada"),
                  ("MÁS VALE TU VIDA", 540, 740, 96, 0xFF8EE08E, "vida")], prof=[(0, "explica")])
M.pizarra("tip2", [("¿MATASTE TARDE?", 540, 520, 96, CHALK, "matas"), ("1 MINUTO PARA ALGO GRANDE", 540, 690, 70, CHALK_Y, "grande")],
          prof=[(0, "feliz")])
M.pizarra("tip3", [("MINUTO 30:", 540, 520, 120, CHALK, "treinta"), ("CADA MUERTE PESA", 540, 700, 96, CHALK_R, "pesa")],
          prof=[(0, "asombro")])
M.pizarra("tip4", [("ANTES DE PELEAR TARDE:", 540, 500, 80, CHALK, "pelear"), ("¿VALE CASI 1 MINUTO?", 540, 680, 84, CHALK_Y, "minuto")],
          prof=[(0, "piensa")])
K.cierre_teemo("NIVEL 1: 10 s · NIVEL 18: 52.5 s", "MÁXIMO: 78.75 s", "1 LIKE = 1 MINUTO EN GRIS PARA TEEMO")


# ---------------- deaths
@M.escena("uno", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("campeon_muere", .3), ("ding", b.at("diez"))])
def uno(c, lt, b):
    t = b.t0 + lt
    k, left = death(c, lt, b, .3, 10)
    K.level_badge(c, YOU[0] + 80, YOU[1] - 110, 1, 1, size=30)
    with b.hud(c):
        M.sign(c, t, lt / .5, "EL TIEMPO", "DE REAPARICIÓN") if lt < .3 else gray_screen(c, k, left, t)


@M.escena("dieciocho", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("campeon_muere", .3), ("ding", b.at("cincuenta"))])
def dieciocho(c, lt, b):
    t = b.t0 + lt
    k, left = death(c, lt, b, .3, 52)
    K.level_badge(c, YOU[0] + 80, YOU[1] - 110, 18, 1, size=30)
    with b.hud(c):
        gray_screen(c, k, left, t)
        caption(c, "NIVEL 18: 52.5 SEGUNDOS", (lt - b.at("cincuenta")) / .3, GOLD)


@M.escena("maximo", "mapa", prof=lambda b: [(0, "puntero"), ("setenta", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("campeon_muere", .2), ("ding", b.at("setenta"))])
def maximo(c, lt, b):
    t = b.t0 + lt
    k, left = death(c, lt, b, .2, 79)
    with b.hud(c):
        gray_screen(c, k, left, t)
        caption(c, "MÁXIMO: 78.75 SEGUNDOS", (lt - b.at("setenta")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
