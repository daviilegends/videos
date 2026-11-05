"""Class 12: ultimate at levels 6/11/16; exceptions Elise, Karma, Nidalee (from level 1) and Jayce (one rank)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=12)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse, shot  # noqa: E402

LY = M.G.lane_y("central", 6000)
YOU, RIV = (5800, LY + 20), (6250, LY - 20)
CAM = (6020, LY - 60, 1.3)


def r_key(c, x, y, lvl_ranks, k=1.0, glow=0.0, t=0.0):
    """The R ability key with 3 rank pips."""
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.scale(M.back(min(1, k)), M.back(min(1, k)))
    if glow > 0:
        p = M.skia.Paint(AntiAlias=True, Color=M.alpha(0xFFFFE27A, .7 * glow), MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 30))
        c.drawRoundRect(M.skia.Rect.MakeXYWH(-90, -90, 180, 180), 30, 30, p)
    c.drawRoundRect(M.skia.Rect.MakeXYWH(-70, -70, 140, 140), 24, 24, M.fill(0xFF1A2230 if lvl_ranks == 0 else 0xFF4A3A8A))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(-70, -70, 140, 140), 24, 24, M.stroke(7, GOLD))
    M.text(c, "R", 0, 30, M.font("segoeuib.ttf", 90), 0xFFFFFFFF if lvl_ranks else 0xFF6A7080, 8)
    for j in range(3):
        c.drawCircle(-36 + j * 36, 100, 13, M.fill(0xFFFFE27A if j < lvl_ranks else 0xFF3A3F48))
        c.drawCircle(-36 + j * 36, 100, 13, M.stroke(4))
    c.restore()


# ---------------- classroom
M.pizarra("hook", [("NIVEL 6", 540, 520, 160, CHALK_Y, .2), ("¿POR QUÉ LA EMOCIÓN?", 540, 720, 76, CHALK, "emocionan")],
          prof=[(0, "piensa"), ("seis", "asombro")])
M.pizarra("spoiler", [("LA LÍNEA SE JUEGA", 540, 520, 84, CHALK, "línea"), ("DISTINTO", 540, 680, 120, CHALK_Y, "distinto")],
          prof=[(0, "explica")])


def regla_extra(c, lt, b):
    for j, (lvl, key) in enumerate(((6, "seis"), (11, "once"), (16, "dieciséis"))):
        K.level_badge(c, 260 + j * 280, 760, lvl, (lt - b.at(key)) / .35, size=70)


M.pizarra("regla", [("LA R (DEFINITIVA)", 540, 470, 90, CHALK, "definitiva")], prof=[(0, "explica")], extra=regla_extra)
M.pizarra("salto", [("EL PRIMER GRAN SALTO", 540, 520, 80, CHALK, "salto"), ("DE PODER", 540, 660, 110, CHALK_Y, "poder")],
          prof=[(0, "feliz")])
M.pizarra("rangos", [("6 · 11 · 16", 540, 560, 140, CHALK_Y, "seis"), ("3 RANGOS. NO HAY MÁS.", 540, 780, 76, CHALK, "más")],
          prof=[(0, "explica"), ("más", "guino")])


def exc_extra(c, lt, b):
    for j, (n, key) in enumerate((("Elise", "elise"), ("Karma", "karma"), ("Nidalee", "nidalee"))):
        k = ease((lt - b.at(key)) / .35)
        if k > 0:
            c.save()
            c.translate(270 + j * 270, 790)
            c.scale(M.back(k), M.back(k))
            c.save()
            c.clipPath(M.skia.Path.Circle(0, 0, 90), doAntiAlias=True)
            c.drawImageRect(M.icon(n), M.skia.Rect.MakeXYWH(-95, -95, 190, 190), M.skia.SamplingOptions(M.skia.FilterMode.kLinear))
            c.restore()
            c.drawCircle(0, 0, 90, M.stroke(8, GOLD))
            c.restore()
            M.chalk_line(c, "R EN NIVEL 1", 270 + j * 270, 940, 40, (lt - b.at(key) - .3) / .3, CHALK_Y)


M.pizarra("excepciones", [("EXCEPCIONES", 540, 460, 100, CHALK_R, "excepciones")], prof=[(0, "explica")], extra=exc_extra)


def jayce_extra(c, lt, b):
    k = ease((lt - b.at("jayce")) / .35)
    if k > 0:
        c.save()
        c.translate(540, 780)
        c.scale(M.back(k), M.back(k))
        c.save()
        c.clipPath(M.skia.Path.Circle(0, 0, 110), doAntiAlias=True)
        c.drawImageRect(M.icon("Jayce"), M.skia.Rect.MakeXYWH(-115, -115, 230, 230), M.skia.SamplingOptions(M.skia.FilterMode.kLinear))
        c.restore()
        c.drawCircle(0, 0, 110, M.stroke(8, GOLD))
        c.restore()


M.pizarra("jayce", [("JAYCE: DESDE EL INICIO", 540, 450, 76, CHALK, "jayce"), ("CON 1 SOLO RANGO", 540, 560, 76, CHALK_Y, "rango")],
          prof=[(0, "explica")], extra=jayce_extra)
M.pizarra("broma", [("NIVEL 6 =", 540, 500, 110, CHALK, "seis"), ("VIERNES EN LA TARDE", 540, 680, 84, CHALK_Y, "viernes")],
          prof=[(0, "feliz"), ("invencible", "picara")])
M.pizarra("primero", [("¿LLEGASTE PRIMERO?", 540, 500, 86, CHALK, "primero"), ("APROVÉCHALO YA", 540, 680, 96, 0xFF8EE08E, "aprovéchala")],
          prof=[(0, "explica"), ("suba", "guino")])
M.pizarra("cuenta", [("¿ESTÁ POR SUBIR?", 540, 500, 90, CHALK, "subir"), ("ESPERA AL TUYO", 540, 680, 96, CHALK_Y, "espera")],
          prof=[(0, "explica")])
M.pizarra("broma2", [("SIN TU R CONTRA SU R", 540, 480, 80, CHALK, "pelear"), ("CUCHARA VS ESPADA", 540, 660, 96, CHALK_R, "cuchara")],
          prof=[(0, "picara"), ("espadas", "asombro")])
K.cierre_teemo("R EN 6 · 11 · 16", "CUIDADO CUANDO EL RIVAL LLEGA A 6", "1 LIKE = 1 NIVEL PARA TI")


# ---------------- lane
@M.escena("seis", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("seis")), ("habilidad", b.at("truco"))])
def seis(c, lt, b):
    t = b.t0 + lt
    up = b.at("seis")
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, pulse(lt, up, 4), 1, s=.85)
    K.level_badge(c, YOU[0] + 70, YOU[1] - 110, 6 if lt > up else 5, 1, size=34)
    shot(c, YOU, RIV, (lt - b.at("truco")) / .45, "habilidad", 0xFFB06CF0)
    champ(c, *RIV, "Draven", "rojo", "RIVAL", 1, pulse(lt, b.at("truco") + .45, 8), .8, s=.85)
    with b.hud(c):
        M.sign(c, t, lt / .5, "NIVELES", "Y LA DEFINITIVA")
        r_key(c, 540, 1240, 1 if lt > up else 0, 1, pulse(lt, up, 2), t)


@M.escena("once", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("once")), ("habilidad", b.at("fuerte"))])
def once(c, lt, b):
    t = b.t0 + lt
    up = b.at("once")
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, pulse(lt, up, 4), 1, s=.85)
    K.level_badge(c, YOU[0] + 70, YOU[1] - 110, 11 if lt > up else 10, 1, size=34)
    shot(c, YOU, RIV, (lt - b.at("fuerte")) / .4, "habilidad", 0xFFB06CF0)
    champ(c, *RIV, "Draven", "rojo", "RIVAL", 1, pulse(lt, b.at("fuerte") + .4, 8), .6, s=.85)
    with b.hud(c):
        r_key(c, 540, 1240, 2 if lt > up else 1, 1, pulse(lt, up, 2), t)


@M.escena("dieciseis", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("dieciséis"))])
def dieciseis(c, lt, b):
    t = b.t0 + lt
    up = b.at("dieciséis")
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, pulse(lt, up, 4), 1, s=.85)
    K.level_badge(c, YOU[0] + 70, YOU[1] - 110, 16 if lt > up else 15, 1, size=34)
    with b.hud(c):
        r_key(c, 540, 1240, 3 if lt > up else 2, 1, pulse(lt, up, 2), t)
        caption(c, "R AL MÁXIMO", (lt - b.at("máximo")) / .3, GOLD)


@M.escena("rival", "mapa", prof=lambda b: [(0, "puntero"), ("cuidado", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ding", b.at("seis")), ("draven_hacha", b.at("pelea")), ("draven_hit", b.at("pelea") + .45)])
def rival(c, lt, b):
    t = b.t0 + lt
    up = b.at("seis")
    champ(c, *RIV, "Draven", "rojo", "RIVAL", 1, pulse(lt, up, 4), 1, s=.85)
    K.level_badge(c, RIV[0] + 70, RIV[1] - 110, 6 if lt > up else 5, 1, RED, 34)
    M.shot(c, RIV, YOU, (lt - b.at("pelea")) / .45, "hacha")
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, pulse(lt, b.at("pelea") + .45, 8), 1 - .3 * ease((lt - b.at("pelea") - .45) / .3), s=.85)
    with b.hud(c):
        caption(c, "RIVAL EN NIVEL 6 = OTRA PELEA", (lt - b.at("cuidado")) / .3, 0xFFFF6B74)


@M.escena("barra", "mapa", cam=lambda b: [(0, (RIV[0], RIV[1] - 100, 2.2))], sfx=lambda b: [("ding", b.at("nivel"))])
def barra(c, lt, b):
    t = b.t0 + lt
    champ(c, *RIV, "Draven", "rojo", "RIVAL", 1, 0, 1, s=.85)
    K.level_badge(c, RIV[0] - 80, RIV[1] - 98, 5, 1, RED, 30)
    k = ease((lt - b.at("nivel")) / .4)
    if k > 0:
        M.chalk_circle(c, RIV[0] - 80, RIV[1] - 98, 46, k, 0xFFFFE27A, 6)
    with b.hud(c):
        caption(c, "EL NIVEL, JUNTO A SU BARRA DE VIDA", (lt - b.at("barra")) / .3, GOLD)


if __name__ == "__main__":
    M.main()
