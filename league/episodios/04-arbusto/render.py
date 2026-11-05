"""Class 04: brush. Hidden from enemies outside; any sight reveals; targeted attacks/abilities reveal 300 radius for 2 s."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
from motor import (BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, burst, caption, champ, chalk_line, chalk_stroke,  # noqa: E402
                   clamp, ease, keys, lerp, pulse, shot)

M.setup(__file__, clase=4)
G = M.G
BR = G._brush_pos(7700, "inferior", 1)             # brush below the bot lane
LY = G.lane_y("inferior", 7700)
CAM = (7700, LY + 120, 1.25)
HIDE = (BR[0] - 20, BR[1] - 10)
LANE_L, LANE_R = (7250, LY - 20), (8150, LY - 20)


def jinx(c, pos=HIDE, a=1.0, flash=0.0, k=1.0):
    champ(c, *pos, "Jinx", "azul", "TÚ", k, flash, 1.0, s=.85, a=a)


def draven(c, pos, flash=0.0, hp=1.0):
    champ(c, *pos, "Draven", "rojo", "RIVAL", 1, flash, hp, s=.85)


def hidden_mark(c, k, t):
    if k <= 0:
        return
    pp = M.stroke(6, M.alpha(0xFFFFFFFF, .8 * k))
    pp.setPathEffect(M.skia.DashPathEffect.Make([16, 10], t * 30))
    c.drawCircle(*HIDE, 82, pp)
    badge(c, "OCULTA", HIDE[0], HIDE[1] + 120, 28, M.INK, 0xFFFFFFFF, k)


def chalk_bush(c, x, y, k, color=0xFF8EE08E):
    for j in range(7):
        bx = x - 120 + j * 40
        chalk_stroke(c, [(bx - 18, y), (bx, y - 90 - 20 * math.sin(j * 1.7)), (bx + 18, y)], k * 1.4 - j * .06, color, 7)


# ---------------- classroom ----------------
def hook_extra(c, lt, b):
    chalk_bush(c, 540, 930, (lt - b.at("arbusto")) / .6)
    k = (lt - b.at("encontraron")) / .3
    for sx in (-1, 1):
        M.chalk_circle(c, 540 + sx * 40, 860, 18, k, CHALK_Y, 6)
    chalk_line(c, "!", 690, 820, 110, k - .3, CHALK_R)


M.pizarra("hook", [("¿TE ESCONDISTE", 540, 450, 90, CHALK, .1), ("Y TE ENCONTRARON?", 540, 590, 84, CHALK_Y, .7)],
          prof=[(0, "piensa"), ("encontraron", "asombro")], extra=hook_extra)


def spoiler_extra(c, lt, b):
    M.chalk_cross(c, 820, 470, (lt - b.at("magia") - .3) / .3, s=1.1)


M.pizarra("spoiler", [("¿MAGIA?", 540, 500, 110, CHALK, 0), ("NO: REGLAS", 540, 720, 110, CHALK_Y, "reglas")],
          prof=[(0, "picara"), ("reglas", "explica")], extra=spoiler_extra)
M.pizarra("vision", [("CUALQUIER VISIÓN", 540, 520, 90, CHALK, 0), ("SOBRE EL ARBUSTO", 540, 640, 80, CHALK, "arbusto"),
                     ("= TE REVELA", 540, 800, 110, CHALK_Y, "revela")], prof=[(0, "explica")])


def ejemplos_extra(c, lt, b):
    for j, key in enumerate(("guardián", "aliado", "habilidad")):
        M.chalk_check(c, 170, 470 + j * 150 - 20, (lt - b.at(key) - .3) / .3)


M.pizarra("ejemplos", [("GUARDIÁN", 250, 470, 80, CHALK, "guardián", .5, "l"), ("ALIADO ADENTRO", 250, 620, 80, CHALK, "aliado", .5, "l"),
                       ("HABILIDAD CON VISIÓN", 250, 770, 66, CHALK, "habilidad", .5, "l"), ("TODO CUENTA", 540, 950, 90, CHALK_Y, "cuenta")],
          prof=[(0, "explica")], extra=ejemplos_extra)
M.pizarra("tip1", [("CONSEJO DE LA PROFE", 540, 400, 60, GOLD, 0), ("¿EMBOSCADA?", 540, 560, 96, CHALK, "emboscar"),
                   ("ENTRA ANTES", 540, 720, 96, CHALK_Y, "antes"), ("DE QUE TE VEAN", 540, 840, 80, CHALK_Y, "vean")],
          prof=[(0, "explica"), ("antes", "guino")])
M.pizarra("tip2", [("ATACA PARA", 540, 500, 96, CHALK, 0), ("REMATAR", 540, 640, 120, 0xFF8EE08E, "rematar"),
                   ("NO PARA AVISAR", 540, 820, 90, CHALK_R, "avisar")], prof=[(0, "explica"), ("avisar", "picara")])


@M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), ("teemo", "feliz")],
          sfx=lambda b: [("tiza", 0), ("ding", b.at("like")), ("ward", b.at("guardián")), ("puno", b.at("teemo") + .4),
                         ("teemo_muere", b.at("teemo") + .6)])
def cierre(c, lt, b):
    chalk_line(c, "EL ARBUSTO TE ESCONDE…", 540, 420, 66, lt / .5)
    chalk_line(c, "HASTA QUE HAY VISIÓN", 540, 530, 72, (lt - .6) / .5, CHALK_Y)
    badge(c, "1 LIKE = 1 GUARDIÁN", 540, 680, 46, GOLD, M.INK, (lt - b.at("like")) / .35, rot=-3)
    chalk_bush(c, 720, 1000, (lt - b.at("arbusto", 1)) / .5)
    M.ward(c, 900, 960, (lt - b.at("guardián")) / .4, b.t0 + lt, "azul")
    M.teemo_punch(c, lt, [b.at("teemo") + .5], 720, 880, ease((lt - b.at("teemo")) / .4), b.t0 + lt)


# ---------------- lane ----------------
def walker(lt, t0, t1, a=LANE_R, z=LANE_L):
    return keys(lt, [(t0, a), (t1, z)])


@M.escena("regla", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("arbusto", .1), ("ding", b.at("ven"))])
def regla(c, lt, b):
    t = b.t0 + lt
    k_in = ease(lt / .9)
    jinx(c, (lerp(HIDE[0] - 300, HIDE[0], k_in), lerp(LY + 60, HIDE[1], k_in)), a=lerp(1, .45, ease((lt - .7) / .3)))
    hidden_mark(c, ease((lt - .9) / .3), t)
    dp = walker(lt, 0, b.dur)
    draven(c, dp)
    badge(c, "?", dp[0], dp[1] - 150, 44, RED, 0xFFFFFFFF, (lt - b.at("afuera")) / .3)
    with b.hud(c):
        M.sign(c, t, lt / .5, "EL ARBUSTO", "Y LA VISIÓN")
        caption(c, "LOS DE AFUERA NO TE VEN", (lt - b.at("ven")) / .3, 0xFF8EE08E)


def ninja_band(c, k, t):
    if k <= 0:
        return
    c.save()
    c.translate(*HIDE)
    c.drawRect(M.skia.Rect.MakeXYWH(-70, -40, 140, 26), M.fill(M.alpha(0xFF1E2228, k)))
    for j in (-1, 1):
        c.drawLine(64, -28, 110, -28 + j * 18 + math.sin(t * 8) * 8, M.stroke(10, M.alpha(0xFF1E2228, k)))
    c.restore()


@M.escena("broma", "mapa", prof=lambda b: [(0, "picara"), ("cuidado", "explica")], cam=lambda b: [(0, (HIDE[0], HIDE[1] - 60, 1.6))],
          sfx=lambda b: [("whoosh", b.at("ninja"), .5)])
def broma(c, lt, b):
    t = b.t0 + lt
    jinx(c, a=.6)
    ninja_band(c, ease((lt - b.at("ninja")) / .3), t)
    with b.hud(c):
        caption(c, "NINJA DE PELÍCULA…", (lt - b.at("ninja")) / .3, GOLD) if lt < b.at("cuidado") else \
            caption(c, "…PERO CUIDADO", (lt - b.at("cuidado")) / .3, 0xFFFF6B74)


@M.escena("ward", "mapa", prof=lambda b: [(0, "puntero"), ("completito", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ward", b.at("guardián")), ("ding", b.at("completito"))])
def ward_(c, lt, b):
    t = b.t0 + lt
    tw = b.at("guardián")
    rev = ease((lt - tw - .3) / .5)
    M.ward(c, HIDE[0] + 150, HIDE[1] + 20, (lt - tw) / .4, t, "rojo", rev)
    jinx(c, a=lerp(.45, 1, rev), flash=pulse(lt, tw + .5, 5))
    if rev <= 0:
        hidden_mark(c, 1, t)
    draven(c, (LANE_R[0] - 120, LANE_R[1]))
    badge(c, "¡TE VEN!", HIDE[0], HIDE[1] - 150, 40, RED, 0xFFFFFFFF, (lt - b.at("completito")) / .3)
    with b.hud(c):
        caption(c, "VISIÓN EN EL ARBUSTO = TE VEN", (lt - tw) / .3, 0xFFFF6B74)


@M.escena("ataque", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("jinx_basico", b.at("ataque")), ("jinx_hit", b.at("ataque") + .3)])
def ataque(c, lt, b):
    t = b.t0 + lt
    ta = b.at("ataque")
    dp = (LANE_R[0] - 300, LANE_R[1])
    jinx(c, a=.45 if lt < ta else 1.0)
    if lt < ta:
        hidden_mark(c, 1, t)
    shot(c, HIDE, dp, (lt - ta) / .3, "bala", BLUE)
    draven(c, dp, pulse(lt, ta + .3, 9), 1 - .1 * ease((lt - ta - .3) / .3))
    badge(c, "ERROR CLÁSICO", HIDE[0] - 40, HIDE[1] - 160, 36, RED, 0xFFFFFFFF, (lt - b.at("error")) / .3)
    with b.hud(c):
        caption(c, "ATAQUE O HABILIDAD CON OBJETIVO", (lt - b.at("objetivo")) / .3, GOLD)


def reveal_ring(c, k, t, timer=None):
    if k <= 0:
        return
    r = 300 * M.UNIT
    c.drawCircle(*HIDE, r * ease(k), M.fill(M.alpha(0x33FFE27A, k)))
    pp = M.stroke(6, M.alpha(0xFFFFE27A, k))
    pp.setPathEffect(M.skia.DashPathEffect.Make([18, 12], t * 40))
    c.drawCircle(*HIDE, r * ease(k), pp)
    if timer is not None:
        w = 200
        c.drawRoundRect(M.skia.Rect.MakeXYWH(HIDE[0] - w / 2, HIDE[1] - r - 50, w, 22), 11, 11, M.fill(0xEE0A1424))
        c.drawRoundRect(M.skia.Rect.MakeXYWH(HIDE[0] - w / 2, HIDE[1] - r - 50, w * clamp(timer), 22), 11, 11, M.fill(0xFFFFE27A))


@M.escena("revela", "mapa", prof=lambda b: [(0, "puntero"), ("dos", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ding", b.at("dos")), ("ding", b.at("trescientas"))])
def revela(c, lt, b):
    t = b.t0 + lt
    td = b.at("dos")
    timer = 1 - clamp((lt - td) / 2.0)
    reveal_ring(c, 1 if timer > 0 else ease(1 - (lt - td - 2) / .3), t, timer if timer > 0 else None)
    jinx(c, a=1 if timer > 0 else .45)
    draven(c, (LANE_R[0] - 300, LANE_R[1]), hp=.9)
    badge(c, "2 s", HIDE[0] + 170, HIDE[1] - 160, 40, GOLD, M.INK, (lt - td) / .3)
    with b.hud(c):
        caption(c, "2 SEGUNDOS · 300 UNIDADES", (lt - b.at("trescientas")) / .3, GOLD)


def bulb(c, x, y, k, t):
    if k <= 0:
        return
    glow = M.skia.Paint(AntiAlias=True, Color=M.alpha(0xFFFFF3A0, .7 * k), MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 30))
    c.drawCircle(x, y, 70, glow)
    c.drawCircle(x, y, 38 * k, M.fill(0xFFFFF3A0))
    c.drawCircle(x, y, 38 * k, M.stroke(6))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x - 18, y + 30, 36, 24), 6, 6, M.fill(0xFF9AA0A8))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x - 18, y + 30, 36, 24), 6, 6, M.stroke(5))


@M.escena("broma2", "mapa", prof=lambda b: [(0, "picara")], cam=lambda b: [(0, (HIDE[0], HIDE[1] - 80, 1.6))],
          sfx=lambda b: [("ding", b.at("luz"))])
def broma2(c, lt, b):
    t = b.t0 + lt
    jinx(c)
    bulb(c, HIDE[0], HIDE[1] - 190, ease((lt - b.at("prendes")) / .3), t)
    with b.hud(c):
        caption(c, "TÚ SOLITO PRENDES LA LUZ", (lt - b.at("prendes")) / .3, GOLD)


def xmas(c, k, t):
    if k <= 0:
        return
    for j in range(12):
        a = j * math.pi / 6 + t
        col = [0xFFE84855, 0xFFFFE27A, 0xFF3FA9F5, 0xFF8EE08E][j % 4]
        on = (int(t * 6) + j) % 2
        c.drawCircle(HIDE[0] + math.cos(a) * 95, HIDE[1] + math.sin(a) * 95, 12 * k, M.fill(col if on else M.alpha(col, .4)))


@M.escena("ejemplo", "mapa", prof=lambda b: [(0, "puntero"), ("navidad", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("jinx_basico", b.at("golpeas")), ("jinx_hit", b.at("golpeas") + .3), ("ding", b.at("brillas"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    tg = b.at("golpeas")
    dp = walker(lt, 0, tg, LANE_R, (LANE_R[0] - 350, LANE_R[1]))
    jinx(c, a=.45 if lt < tg else 1.0)
    if lt < tg:
        hidden_mark(c, 1, t)
    shot(c, HIDE, dp, (lt - tg) / .3, "bala", BLUE)
    draven(c, dp, pulse(lt, tg + .3, 9), 1 - .1 * ease((lt - tg - .3) / .3))
    xmas(c, ease((lt - b.at("brillas")) / .3), t)
    with b.hud(c):
        caption(c, "BRILLAS COMO ÁRBOL DE NAVIDAD", (lt - b.at("brillas")) / .3, 0xFF8EE08E)


@M.escena("dos", "mapa", prof=lambda b: [(0, "puntero"), ("persigan", "asombro")], cam=lambda b: [(0, (HIDE[0] - 150, LY + 100, 1.15))],
          sfx=lambda b: [("draven_hacha", b.at("persigan")), ("draven_hit", b.at("persigan") + .45)])
def dos(c, lt, b):
    t = b.t0 + lt
    tp = b.at("persigan")
    jp = keys(lt, [(tp - .3, HIDE), (b.dur, (HIDE[0] - 520, LY + 40))])
    dp = keys(lt, [(0, (LANE_R[0] - 350, LANE_R[1])), (tp - .2, (LANE_R[0] - 350, LANE_R[1])), (b.dur, (jp[0] + 280, LY - 20))])
    reveal_ring(c, 1 - ease((lt - 1.6) / .3), t)
    jinx(c, jp, flash=pulse(lt, tp + .45, 9))
    M.shot(c, dp, jp, (lt - tp) / .45, "hacha")
    draven(c, dp)
    with b.hud(c):
        caption(c, "ALCANZAN PARA QUE TE PERSIGAN", (lt - tp) / .3, 0xFFFF6B74)


@M.escena("tip3", "mapa", prof=lambda b: [(0, "puntero"), ("sospecha", "picara")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ding", b.at("sospecha"))])
def tip3(c, lt, b):
    t = b.t0 + lt
    cp = walker(lt, 0, b.dur, LANE_L, LANE_R)
    champ(c, *cp, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.85)
    champ(c, *HIDE, "Draven", "rojo", None, 1, 0, 1, s=.85, a=.0)  # hidden: invisible to you
    badge(c, "?", HIDE[0], HIDE[1] - 40, 80, M.INK, 0xFFFFFFFF, (lt - b.at("sin")) / .3)
    badge(c, "¡SOSPECHA!", cp[0], cp[1] - 150, 36, GOLD, M.INK, (lt - b.at("sospecha")) / .3)
    with b.hud(c):
        caption(c, "ARBUSTO SIN VISIÓN = PELIGRO", (lt - b.at("pasas")) / .3, GOLD)


@M.escena("tip4", "mapa", prof=lambda b: [(0, "puntero"), ("revisar", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("ward", b.at("revisar")), ("ding", b.at("revisar") + .7)])
def tip4(c, lt, b):
    t = b.t0 + lt
    tr = b.at("revisar")
    rev = ease((lt - tr - .3) / .5)
    M.ward(c, HIDE[0] + 150, HIDE[1] + 20, (lt - tr) / .4, t, "azul", rev)
    champ(c, *HIDE, "Draven", "rojo", "RIVAL", 1, pulse(lt, tr + .5, 5), 1, s=.85, a=rev)
    champ(c, LANE_L[0] + 250, LANE_L[1], "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.85)
    badge(c, "¡TE ATRAPÉ!", HIDE[0], HIDE[1] - 150, 38, BLUE, 0xFFFFFFFF, (lt - tr - .7) / .3)
    with b.hud(c):
        caption(c, "REVISA EL ARBUSTO CON VISIÓN", (lt - tr) / .3, BLUE)


if __name__ == "__main__":
    M.main()
