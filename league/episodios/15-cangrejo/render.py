"""Class 15: Rift Scuttler (two at 2:55, top and bottom river; gold and xp grow with level; speed shrine 90 s with sight and
bonus move speed; after both die, one respawns every 2:30 with a marker)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=15)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse, shot  # noqa: E402

(A1, B1), (A2, B2) = M.G.RIVERS
CRAB_T = ((A1[0] + B1[0]) / 2, (A1[1] + B1[1]) / 2 + 200)
CRAB_B = ((A2[0] + B2[0]) / 2, (A2[1] + B2[1]) / 2 - 200)
CAM = (CRAB_B[0], CRAB_B[1] - 60, 1.15)
CRAB = 0xFF6AB8C8


def crab(c, pos, t, k=1.0, hp=1.0, flash=0.0, walk=True):
    x = pos[0] + (math.sin(t * .8) * 80 if walk else 0)
    K.monster(c, x, pos[1], .7, t, CRAB, None, "crab", k, hp=hp, flash=flash)
    return (x, pos[1])


def shrine(c, pos, k, t, show_ring=True):
    if k <= 0:
        return
    x, y = pos
    if show_ring:
        c.drawCircle(x, y, 520 * ease(k), M.fill(M.alpha(0x22FFF2B0, k)))
        pp = M.stroke(6, M.alpha(0xFFFFE27A, k))
        pp.setPathEffect(M.skia.DashPathEffect.Make([18, 12], t * 30))
        c.drawCircle(x, y, 520 * ease(k), pp)
    c.drawOval(M.skia.Rect.MakeXYWH(x - 120, y - 40, 240, 80), M.fill(M.alpha(0xFF8AD8C8, k)))
    c.drawOval(M.skia.Rect.MakeXYWH(x - 120, y - 40, 240, 80), M.stroke(6))
    for j in range(3):
        ph = (t * 1.5 + j / 3) % 1
        c.drawPath(M.path([(x - 30, y - 10 - ph * 80), (x, y - 40 - ph * 80), (x + 30, y - 10 - ph * 80)], close=False),
                   M.stroke(6, M.alpha(0xFFFFFFFF, (1 - ph) * k)))


# ---------------- classroom
M.pizarra("hook", [("¿POR QUÉ TODOS", 540, 450, 90, CHALK, .1), ("PERSIGUEN AL CANGREJO?", 540, 590, 76, CHALK_Y, "cangrejo")],
          prof=[(0, "piensa"), ("tamal", "picara")], extra=lambda c, lt, b: M.tamal(c, 540, 860, 1.6, (lt - b.at("tamal")) / .4, b.t0 + lt))
M.pizarra("spoiler", [("TIERNO…", 540, 520, 110, CHALK, "tierno"), ("PERO DA MUCHO", 540, 700, 100, CHALK_Y, "mucho")],
          prof=[(0, "feliz")])
M.pizarra("da", [("ORO + EXPERIENCIA", 540, 520, 86, K.ORO, "oro"), ("MÁS TARDE = MÁS", 540, 690, 90, CHALK_Y, "avanzada")],
          prof=[(0, "explica")], sfx_extra=lambda b: [("oro", b.at("oro"))])
M.pizarra("broma", [("CÁMARA DE SEGURIDAD", 540, 500, 80, CHALK, "cámara"), ("+ CAMINADORA", 540, 660, 96, CHALK_Y, "caminadora")],
          prof=[(0, "feliz")])
M.pizarra("reaparece", [("LOS 2 PRIMEROS MUEREN →", 540, 500, 72, CHALK, "primeros"), ("1 CADA 2:30", 540, 680, 110, CHALK_Y, "dos")],
          prof=[(0, "explica")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("ES DEL JUNGLA…", 540, 580, 90, CHALK, "jungla"),
                  ("PERO TU LÍNEA AYUDA", 540, 740, 84, 0xFF8EE08E, "ayudar")], prof=[(0, "explica")])
M.pizarra("tip2", [("1 CANGREJO", 540, 520, 110, CHALK, "cangrejo"), ("≠ TU VIDA", 540, 700, 120, CHALK_R, "vida")],
          prof=[(0, "picara")])
M.pizarra("tip3", [("GANA EL QUE TIENE", 540, 520, 90, CHALK, "gana"), ("SU LÍNEA CERCA", 540, 680, 96, CHALK_Y, "línea")],
          prof=[(0, "explica"), ("gana", "guino")])
K.cierre_teemo("2:55 · SANTUARIO 90 s", "VISIÓN + VELOCIDAD EN EL RÍO", "1 LIKE = 1 CANGREJO")


# ---------------- river
@M.escena("que", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("huye"))])
def que(c, lt, b):
    t = b.t0 + lt
    crab(c, CRAB_B, t, (lt - .2) / .4)
    badge(c, "PACÍFICO", CRAB_B[0], CRAB_B[1] - 150, 32, CRAB, 0xFFFFFFFF, (lt - b.at("pacífico")) / .3)
    with b.hud(c):
        M.sign(c, t, lt / .5, "EL CANGREJO", "DEL RÍO")
        caption(c, "NO ATACA: SOLO HUYE", (lt - b.at("huye")) / .3, CRAB)


@M.escena("cuando", "mapa", cam=lambda b: [(0, (6000, 3000, .55))], sfx=lambda b: [("ding", b.at("dos", 1))])
def cuando(c, lt, b):
    t = b.t0 + lt
    k = (lt - b.at("aparecen")) / .4
    crab(c, CRAB_T, t, k)
    crab(c, CRAB_B, t, k - .2)
    with b.hud(c):
        caption(c, "MINUTO 2:55 · UNO ARRIBA, UNO ABAJO", (lt - b.at("dos", 1)) / .3, CRAB)


@M.escena("santuario", "mapa", prof=lambda b: [(0, "puntero"), ("noventa", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("caitlyn_basico", .2), ("subdito_muere", .6), ("ding", b.at("santuario"))])
def santuario(c, lt, b):
    t = b.t0 + lt
    p = crab(c, CRAB_B, t, 1, hp=0 if lt > .6 else .1, flash=pulse(lt, .5, 8), walk=False) if lt < 1.0 else CRAB_B
    shrine(c, CRAB_B, (lt - b.at("santuario")) / .5, t, False)
    champ(c, CRAB_B[0] - 380, CRAB_B[1] + 60, "Warwick", "azul", "TÚ", 1, 0, 1, s=.8)
    with b.hud(c):
        caption(c, "SANTUARIO DE VELOCIDAD · 90 s", (lt - b.at("noventa")) / .3, 0xFF8AD8C8)


@M.escena("vision", "mapa", cam=lambda b: [(0, (CRAB_B[0], CRAB_B[1] - 60, .95))], sfx=lambda b: [("ward", b.at("visión"))])
def vision(c, lt, b):
    t = b.t0 + lt
    shrine(c, CRAB_B, 1 if lt > b.at("visión") else .5, t, lt > b.at("visión"))
    with b.hud(c):
        caption(c, "DA VISIÓN ALREDEDOR", (lt - b.at("visión")) / .3, 0xFFFFE27A)


@M.escena("rapido", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("whoosh", b.at("caminan"), .6)])
def rapido(c, lt, b):
    t = b.t0 + lt
    shrine(c, CRAB_B, 1, t)
    k = ease((lt - b.at("caminan")) / 1.4)
    x = CRAB_B[0] - 500 + 1000 * k
    champ(c, x, CRAB_B[1] + 40, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.8)
    if 0 < k < 1:
        for j in range(4):
            c.drawLine(x - 140 - j * 40, CRAB_B[1] + 20 + j * 12, x - 260 - j * 60, CRAB_B[1] + 20 + j * 12, M.stroke(6, 0x88FFFFFF))
    with b.hud(c):
        caption(c, "ALIADOS ENCIMA = MÁS VELOCIDAD", (lt - b.at("rápido")) / .3, 0xFF8EE08E)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, (CRAB_B[0] + 200, CRAB_B[1] + 100, .8))], sfx=lambda b: [("ding", b.at("ves"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    shrine(c, CRAB_B, 1, t)
    k = ease(lt / 2.0)
    champ(c, CRAB_B[0] - 300 + 700 * k, CRAB_B[1] + 40 + 300 * k, "Warwick", "azul", None, 1, 0, 1, s=.75)
    champ(c, CRAB_B[0] + 300, CRAB_B[1] - 250, "LeeSin", "rojo", "RIVAL", 1, 0, 1, s=.75, a=.4 + .6 * ease((lt - b.at("ves")) / .3))
    with b.hud(c):
        caption(c, "TU JUNGLA LLEGA RÁPIDO · TÚ VES AL RIVAL", (lt - b.at("ves")) / .3, GOLD)


@M.escena("marca", "mapa", cam=lambda b: [(0, (6000, 3000, .55))], sfx=lambda b: [("ding", b.at("marca"))])
def marca(c, lt, b):
    t = b.t0 + lt
    k = ease((lt - b.at("marca")) / .3)
    if k > 0:
        x, y = CRAB_T
        c.drawCircle(x, y, 90 + 20 * math.sin(t * 6), M.stroke(10, M.alpha(0xFFFFE27A, k)))
        M.text(c, "!", x, y + 30, M.font("segoeuib.ttf", 110), M.alpha(0xFFFFE27A, k), 10)
    with b.hud(c):
        caption(c, "EL MAPA MARCA DÓNDE SALDRÁ", (lt - b.at("marca")) / .3, 0xFFFFE27A)


@M.escena("pelea", "mapa", prof=lambda b: [(0, "puntero"), ("pelea", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("impacto", b.at("pelea")), ("impacto", b.at("pelea") + .4)])
def pelea(c, lt, b):
    t = b.t0 + lt
    crab(c, CRAB_B, t)
    k = ease(lt / 1.2)
    a, z = (CRAB_B[0] - 450 + 200 * k, CRAB_B[1] + 40), (CRAB_B[0] + 450 - 200 * k, CRAB_B[1] - 40)
    champ(c, *a, "Warwick", "azul", "TÚ", 1, pulse(lt, b.at("pelea") + .4, 8), 1, s=.8)
    champ(c, *z, "LeeSin", "rojo", "RIVAL", 1, pulse(lt, b.at("pelea"), 8), 1, s=.8)
    with b.hud(c):
        caption(c, "EL CANGREJO: EXCUSA PARA PELEAR", (lt - b.at("excusa")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
