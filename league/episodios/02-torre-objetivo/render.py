"""Class 02: how the turret picks its target (Warming Up, Reinforced Armor). Run with render_env (see motor.py)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
from motor import (BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, back, badge, big_number, burst, caption, champ,  # noqa: E402
                   chalk_arrow, chalk_check, chalk_circle, chalk_cross, chalk_line, chalk_stroke, clamp, ease, keys,
                   lerp, minion, mix, pulse, ring, shot, sign, target_line, turret_heat)

M.setup(__file__, clase=2)
G = M.G
TURRET = G.named_turret("rojo_inferior_exterior")
TOP = (TURRET[0], TURRET[1] - 190)
# Layout was designed around a turret on a diagonal lane; P() rotates it onto the horizontal bot lane
# (enemy turret on the right, our side coming from the left).
O = (960, 360)
_A = math.radians(51.5)


def P(x, y):
    dx, dy = x - O[0], y - O[1]
    return (TURRET[0] + dx * math.cos(_A) - dy * math.sin(_A), TURRET[1] + dx * math.sin(_A) + dy * math.cos(_A))


def C(x, y, z):
    return (*P(x, y), z)


RANGE = 750 * M.UNIT
CAM = (TURRET[0] - 280, TURRET[1], 1.15)  # turret on the right of the frame, action to its left
CAM_Z = (TURRET[0] - 240, TURRET[1], 1.35)
JINX_OUT, JINX_IN = P(540, 950), P(650, 660)
ASHE = P(880, 500)
WAVE_START = [P(560, 1000), P(520, 1050), P(600, 1060)]
WAVE_IN = [P(770, 600), P(745, 700), P(820, 660)]
CS = .8  # champion scale in this episode


def jinx(c, pos, flash=0.0, hp=1.0, k=1.0):
    champ(c, *pos, "Jinx", "azul", "TÚ", k, flash, hp, s=CS)


def ashe(c, flash=0.0, hp=1.0, dx=0.0):
    champ(c, ASHE[0] + dx, ASHE[1], "Ashe", "rojo", "RIVAL", 1, flash, hp, s=CS)


def turret_shots(c, lt, fires, dur=.35, power=None):
    """fires: list of (time, target position); draws the bolts and impacts."""
    for j, (tf, p) in enumerate(fires):
        k = (lt - tf) / dur
        if 0 <= k < 1:
            c.save()
            sc = 1 + (power[j] if power else 0) * .35
            shot(c, TOP, p, k, "torre", RED)
            c.restore()
        burst(c, p, pulse(lt, tf + dur, 5), 0xFFFF8A5A, 60 * (1 + (power[j] if power else 0) * .4))


def crystal_glow(c, k, heat=0.0):
    if k <= 0:
        return
    p = M.skia.Paint(AntiAlias=True, Color=M.alpha(RED, k * .7), MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 30 + 30 * heat))
    c.drawCircle(*TOP, 70 + 60 * heat, p)


def wave(c, t, pos_list, alive=(1, 1, 1), pops=(0, 0, 0), hps=None):
    for j, (x, y) in enumerate(pos_list):
        if alive[j]:
            minion(c, x, y, "azul", .9, t, pop=pops[j], kind="mago" if j == 2 else "melee")
            if hps:
                c.drawRoundRect(M.skia.Rect.MakeXYWH(x - 36, y - 78, 72, 10), 5, 5, M.fill(0xFF0A1424))
                c.drawRoundRect(M.skia.Rect.MakeXYWH(x - 36, y - 78, 72 * clamp(hps[j]), 10), 5, 5, M.fill(0xFF4CD07A))


# ---------------- classroom ----------------
def chalk_turret(c, x, y, s, k, color=CHALK):
    chalk_stroke(c, [(x - 40 * s, y), (x - 28 * s, y - 140 * s), (x + 28 * s, y - 140 * s), (x + 40 * s, y), (x - 40 * s, y)], k, color, 7)
    chalk_stroke(c, [(x, y - 215 * s), (x + 24 * s, y - 175 * s), (x, y - 145 * s), (x - 24 * s, y - 175 * s), (x, y - 215 * s)], k * 1.3 - .3, CHALK_R, 7)


@M.escena("hook", "aula", prof=[(0, "piensa"), ("repente", "asombro"), ("profe", "picara")],
          sfx=lambda b: [("tiza", .1), ("tiza", .8), ("ding", b.at("elige")), ("tiza", b.at("profe"))])
def hook(c, lt, b):
    chalk_line(c, "¿POR QUÉ LA TORRE", 540, 460, 84, (lt - .1) / .6)
    chalk_line(c, "TE ELIGE A TI?", 540, 590, 100, (lt - .8) / .5, CHALK_Y)
    chalk_turret(c, 250, 960, 1.2, (lt - b.at("torre")) / .6)
    chalk_arrow(c, (330, 740), (700, 860), (lt - b.at("elige")) / .35, CHALK_R)
    chalk_circle(c, 800, 870, 60, (lt - b.at("elige") - .1) / .4, CHALK_Y)
    chalk_line(c, "TÚ", 800, 890, 50, (lt - b.at("elige") - .3) / .3, CHALK_Y)
    kp = (lt - b.at("profe")) / .3
    for j, (dx, dy) in enumerate(((75, -50), (95, -10))):  # sweat drops
        x, y = 800 + dx, 870 + dy + 8 * math.sin((b.t0 + lt) * 6 + j)
        chalk_stroke(c, [(x, y - 22), (x + 12, y), (x, y + 10), (x - 12, y), (x, y - 22)], kp - j * .2, M.CHALK_B, 6)
    chalk_line(c, "¿Y TÚ QUÉ OPINAS?", 540, 1030, 46, (lt - b.at("pregunta")) / .5, CHALK_R)


@M.escena("reglas", "aula", prof=[(0, "explica"), ("enseño", "guino")],
          sfx=lambda b: [("tiza", 0), ("tiza", b.at("reglas")), ("ding", b.at("enseño"))])
def reglas(c, lt, b):
    chalk_line(c, "¿TE ODIA?", 540, 500, 100, lt / .4)
    chalk_cross(c, 820, 460, (lt - b.at("odie")) / .4, s=1.2)
    chalk_line(c, "SIGUE REGLAS", 540, 740, 110, (lt - b.at("reglas")) / .5, CHALK_Y)
    chalk_stroke(c, [(200, 785), (880, 780)], (lt - b.at("claras")) / .3, CHALK_Y, 8)


@M.escena("tope", "aula", prof=[(0, "explica"), ("cuarto", "asombro"), ("dos", "picara"), ("recibo", "asombro")],
          sfx=lambda b: [("tiza", 0)] + [("tiza", b.at("cuarto") + j * .25, .5) for j in range(4)] + [("ding", b.at("dos")), ("ding", b.at("recibo"))])
def tope(c, lt, b):
    chalk_line(c, "MÁXIMO: +150%", 540, 400, 80, (lt - b.at("ciento")) / .5, CHALK_Y)
    vals = [("1º", 100), ("2º", 150), ("3º", 200), ("4º", 250)]
    t0 = b.at("cuarto")
    for j, (n, v) in enumerate(vals):
        k = ease((lt - t0 - j * .25) / .35)
        x = 220 + j * 210
        h = v * 1.6 * k
        col = [CHALK, CHALK_Y, 0xFFFFB14A, CHALK_R][j]
        if k > 0:
            chalk_stroke(c, [(x - 55, 970), (x - 55, 970 - h), (x + 55, 970 - h), (x + 55, 970)], 1, col, 8)
            chalk_line(c, f"{v}%", x, 950 - h, 46, 1, col)
            chalk_line(c, n, x, 1040, 46, 1, col)
    chalk_stroke(c, [(120, 972), (960, 972)], (lt - t0 + .3) / .4, CHALK, 6)
    if lt > b.at("dos"):
        c.save()
        big_number(c, "×2.5", 560, 520, (lt - b.at("dos")) / .35, CHALK_R, 120)
        c.restore()
    kr = (lt - b.at("recibo")) / .35
    if kr > 0:  # electricity bill, shaking
        c.save()
        c.translate(190, 600)
        c.rotate(-8 + math.sin((b.t0 + lt) * 25) * 3 * clamp(kr))
        c.scale(back(min(1, kr)), back(min(1, kr)))
        pts = [(-70, -90), (70, -90), (70, 80)] + [(70 - j * 20, 80 + (10 if j % 2 else 0)) for j in range(1, 8)] + [(-70, 80)]
        chalk_stroke(c, pts + [(-70, -90)], 1, CHALK, 6)
        chalk_line(c, "LUZ", 0, -45, 40, 1, CHALK)
        chalk_line(c, "$$$$", 0, 20, 52, 1, CHALK_R)
        c.restore()


@M.escena("reset", "aula", prof=[(0, "piensa"), ("cinco", "explica")],
          sfx=lambda b: [("tiza", 0), ("ding", b.at("cinco")), ("tiza", b.at("último"))])
def reset(c, lt, b):
    chalk_line(c, "SE ENFRÍA EN", 540, 420, 80, lt / .5)
    tc = b.at("cinco")
    chalk_circle(c, 540, 680, 170, (lt - tc + .2) / .5, CHALK_Y, 9)
    if lt > tc:
        sweep = clamp((lt - tc) / 2.5)
        ang = -math.pi / 2 + sweep * 2 * math.pi
        c.drawLine(540, 680, 540 + math.cos(ang) * 140, 680 + math.sin(ang) * 140, M.stroke(9, CHALK_R))
        secs = max(0, 5 - int(sweep * 5))
        chalk_line(c, f"{secs} s" if secs else "0 s", 540, 720, 110, 1, CHALK_Y)
    chalk_line(c, "SIN DISPARAR A CAMPEONES", 540, 960, 60, (lt - b.at("último")) / .6)


@M.escena("tip", "aula", prof=[(0, "explica"), ("pegues", "picara"), ("rematarlo", "guino")],
          sfx=lambda b: [("ding", 0), ("tiza", b.at("entra")), ("tiza", b.at("pegues"))])
def tip(c, lt, b):
    badge(c, "CONSEJO DE LA PROFE", 540, 380, 50, GOLD, M.INK, lt / .35, rot=-3)
    te, tp = b.at("entra"), b.at("pegues")
    chalk_check(c, 160, 560, (lt - te - .6) / .3, s=1.2)
    chalk_line(c, "ENTRA CON TU", 240, 540, 64, (lt - te) / .5, CHALK, 720, "l")
    chalk_line(c, "OLEADA ADENTRO", 240, 620, 64, (lt - te - .3) / .5, CHALK, 720, "l")
    chalk_cross(c, 160, 810, (lt - tp - .6) / .3, s=.9)
    chalk_line(c, "NO PEGUES BAJO SU", 240, 790, 64, (lt - tp) / .5, CHALK_Y, 720, "l")
    chalk_line(c, "TORRE SI NO REMATAS", 240, 870, 64, (lt - tp - .4) / .5, CHALK_Y, 720, "l")


@M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), ("teemo", "feliz"), ("dos", "guino")],
          sfx=lambda b: [("tiza", 0), ("tiza", .5), ("tiza", 1.0), ("ding", b.at("like")), ("puno", b.at("teemo") - .1),
                         ("puno", b.at("dos") - .1), ("teemo_muere", b.at("dos") + .15)])
def cierre(c, lt, b):
    chalk_line(c, "CÓMO PIENSA LA TORRE", 540, 380, 70, lt / .5, CHALK_Y)
    for j, s_ in enumerate(("1. LA PRIMERA EN ENTRAR", "2. DEFIENDE A SUS CAMPEONES", "3. +50% POR DISPARO")):
        chalk_line(c, s_, 130, 470 + j * 75, 46, (lt - .5 - j * .45) / .5, CHALK, 820, "l")
    badge(c, "1 LIKE = 1 PUÑETAZO", 540, 745, 44, GOLD, M.INK, (lt - b.at("like")) / .35, rot=-3)
    M.teemo_punch(c, lt, [b.at("teemo"), b.at("dos")], 720, 910, ease((lt - b.at("like")) / .4), b.t0 + lt)
    badge(c, "COMENTAS = ×2", 280, 1010, 34, RED, 0xFFFFFFFF, (lt - b.at("comentas")) / .35, rot=-2)


# ---------------- lane, around the enemy turret ----------------
def range_ring(c, t, k, label=None):
    ring(c, TURRET, RANGE, k, RED, label, t, label_dy=RANGE - 10)


@M.escena("regla1", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [(s, b.at("ataca") + j * .75 + d) for j in range(3) for s, d in (("torre_disparo", 0), ("torre_impacto", .35))]
          + [("subdito_muere", b.at("ataca") + 1.85)])
def regla1(c, lt, b):
    t = b.t0 + lt
    tp, ta = b.at("primera"), b.at("ataca")
    range_ring(c, t, .55)
    walk = ease(lt / max(.1, tp))
    pos = [mix(WAVE_START[j], WAVE_IN[j], walk) for j in range(3)]
    fires = [(ta + j * .75, pos[0]) for j in range(3)]
    hp0 = 1 - .45 * sum(lt > f + .35 for f, _ in fires)
    die = clamp((lt - fires[2][0] - .35) / .4)
    wave(c, t, pos, pops=(die, 0, 0), hps=(max(0, hp0), 1, 1))
    if die < 1:
        target_line(c, (TURRET[0] - 20, TURRET[1] - 30), pos[0], (lt - tp) / .3, RED, t)
    turret_shots(c, lt, fires)
    crystal_glow(c, max(pulse(lt, f, 4) for f, _ in fires))
    badge(c, "1ª EN ENTRAR", pos[0][0] - 20, pos[0][1] - 110, 32, RED, 0xFFFFFFFF, (lt - tp) / .3 if die < 1 else 0)
    jinx(c, JINX_OUT)
    ashe(c)
    with b.hud(c):
        sign(c, t, lt / .5, "¿A QUIÉN", "ATACA LA TORRE?")
        caption(c, "…HASTA QUE MUERE", (lt - b.at("muere")) / .3, 0xFFFF6B74)


@M.escena("rango", "mapa", cam=lambda b: [(0, CAM), ("setecientas", (TURRET[0] - 40, TURRET[1] + 40, .85))], sfx=lambda b: [("ding", b.at("setecientas"))])
def rango(c, lt, b):
    t = b.t0 + lt
    k = .55 + .45 * ease((lt - b.at("rango")) / .4)
    range_ring(c, t, k, "750 UNIDADES" if lt > b.at("setecientas") else None)
    wave(c, t, WAVE_IN[1:], alive=(1, 1))
    jinx(c, JINX_OUT)
    ashe(c)


@M.escena("subditos", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("torre_disparo", b.at("entretiene") + j * .8) for j in range(2)])
def subditos(c, lt, b):
    t = b.t0 + lt
    range_ring(c, t, .55)
    walk = ease((lt - b.at("entran") + .3) / .8)
    pos = [mix(WAVE_START[j], WAVE_IN[j], walk) for j in range(3)]
    wave(c, t, pos)
    fires = [(b.at("entretiene") + j * .8, pos[1]) for j in range(2)]
    turret_shots(c, lt, fires)
    target_line(c, (TURRET[0] - 20, TURRET[1] - 30), pos[1], (lt - b.at("entretiene") + .3) / .3, RED, t)
    jp = mix(JINX_OUT, JINX_IN, ease((lt - b.at("entretiene") - .2) / .9))
    jinx(c, jp)
    ashe(c)
    with b.hud(c):
        caption(c, "TUS SÚBDITOS = TU ESCUDO", (lt - b.at("entretiene")) / .3, BLUE)


@M.escena("excepcion", "mapa", cam=lambda b: [(0, CAM), ("dañas", CAM_Z)],
          sfx=lambda b: [("ding", b.at("excepción")), ("jinx_basico", b.at("dañas")), ("impacto", b.at("dañas") + .3)])
def excepcion(c, lt, b):
    t = b.t0 + lt
    range_ring(c, t, .55)
    wave(c, t, WAVE_IN)
    target_line(c, (TURRET[0] - 20, TURRET[1] - 30), WAVE_IN[1], 1, RED, t)
    td = b.at("dañas")
    shot(c, JINX_IN, ASHE, (lt - td) / .3, "bala", BLUE)
    jinx(c, JINX_IN)
    ashe(c, pulse(lt, td + .3, 9), 1 - .15 * ease((lt - td - .3) / .3), math.sin(t * 60) * 8 * pulse(lt, td + .3))
    burst(c, ASHE, pulse(lt, td + .3, 4))
    with b.hud(c):
        badge(c, "EXCEPCIÓN", 540, 300, 60, GOLD, M.INK, (lt - b.at("excepción")) / .3, rot=-3)


@M.escena("cambia", "mapa", prof=lambda b: [(0, "puntero"), ("ti", "asombro")], cam=lambda b: [(0, CAM_Z)],
          sfx=lambda b: [("ding", b.at("cambia")), ("torre_disparo", b.at("ti")), ("torre_impacto", b.at("ti") + .35)])
def cambia(c, lt, b):
    t = b.t0 + lt
    range_ring(c, t, .55)
    wave(c, t, WAVE_IN)
    tc = b.at("cambia")
    src = (TURRET[0] - 20, TURRET[1] - 30)
    if lt < tc:
        target_line(c, src, WAVE_IN[1], 1, RED, t)
    else:
        target_line(c, src, JINX_IN, (lt - tc) / .25, RED, t)
    badge(c, "!", TURRET[0] - 110, TURRET[1] - 210, 50, RED, 0xFFFFFFFF, (lt - tc) / .3)
    crystal_glow(c, pulse(lt, tc, 2))
    turret_shots(c, lt, [(b.at("ti"), JINX_IN)])
    jinx(c, JINX_IN, pulse(lt, b.at("ti") + .35, 8), 1 - .12 * ease((lt - b.at("ti") - .35) / .3))
    ashe(c, hp=.85)
    with b.hud(c):
        caption(c, "NUEVO OBJETIVO: TÚ", (lt - tc) / .3, 0xFFFF6B74)


@M.escena("calienta", "mapa", prof=lambda b: [(0, "puntero"), ("peor", "asombro"), ("cada", "puntero")],
          cam=lambda b: [(0, CAM_Z)],
          sfx=lambda b: [(s, b.at("cada") + j * .9 + d, 1 + j * .3) for j in range(3) for s, d in (("torre_disparo", 0), ("torre_impacto", .35))]
          + [("ding", b.at("cincuenta"))])
def calienta(c, lt, b):
    t = b.t0 + lt
    range_ring(c, t, .45)
    wave(c, t, WAVE_IN)
    fires = [(b.at("cada") + j * .9, JINX_IN) for j in range(3)]
    level = sum(lt > f + .35 for f, _ in fires)
    target_line(c, (TURRET[0] - 20, TURRET[1] - 30), JINX_IN, 1, RED, t)
    turret_shots(c, lt, fires, power=[0, 1, 2])
    crystal_glow(c, .6 + .4 * math.sin(t * 6), level / 3)
    M.steam(c, TOP[0], TOP[1] - 60, ease((lt - b.at("calienta")) / .4), t)
    turret_heat(c, TURRET[0] - 230, TURRET[1] - 130, min(3, level), (lt - fires[0][0]) / .3)
    jinx(c, JINX_IN, max(pulse(lt, f + .35, 8) for f, _ in fires), .88 - sum(.1 * (1 + j * .5) for j, (f, _) in enumerate(fires) if lt > f + .35))
    ashe(c, hp=.85)
    with b.hud(c):
        big_number(c, "+50%", 330, 560, (lt - b.at("cincuenta")) / .35, 0xFFFF7A3A, 150)
        if lt < b.at("tío"):
            caption(c, "POR CADA DISPARO QUE TE DA", (lt - b.at("cincuenta") - .2) / .3, 0xFFFFB14A)
        else:
            caption(c, "MÁS RÁPIDO QUE TU TÍO CON EL FÚTBOL", (lt - b.at("tío")) / .3, 0xFFFF7A3A)


@M.escena("cambio", "mapa", cam=lambda b: [(0, (TURRET[0] - 260, TURRET[1] + 20, 1.25))],
          sfx=lambda b: [("torre_disparo", .2), ("torre_impacto", .55), ("ding", b.at("salta")), ("torre_disparo", b.at("caliente") - .4, 1.5),
                         ("torre_impacto", b.at("caliente") - .05, 1.5)])
def cambio(c, lt, b):
    t = b.t0 + lt
    cait = P(840, 780)
    range_ring(c, t, .45)
    wave(c, t, WAVE_IN[:2], alive=(1, 1))
    ts = b.at("salta")
    src = (TURRET[0] - 20, TURRET[1] - 30)
    if lt < ts:
        target_line(c, src, cait, 1, RED, t)
    else:
        target_line(c, src, JINX_IN, (lt - ts) / .25, RED, t)
    tf2 = b.at("caliente") - .4
    turret_shots(c, lt, [(.2, cait), (tf2, JINX_IN)], power=[1, 2])
    turret_heat(c, TURRET[0] - 230, TURRET[1] - 130, 2 + (lt > tf2 + .35), 1)
    crystal_glow(c, .8, .7)
    champ(c, *cait, "Caitlyn", "azul", "ALIADO", 1, pulse(lt, .55, 8), .55, s=CS)
    jinx(c, JINX_IN, pulse(lt, tf2 + .35, 8), .6 - .25 * ease((lt - tf2 - .35) / .3))
    ashe(c, hp=.85)
    with b.hud(c):
        caption(c, "NO SE ENFRÍA AL CAMBIAR", (lt - b.at("reinicia")) / .3, GOLD) if lt < ts else caption(c, "¡TE LLEGA CALIENTE!", (lt - ts) / .3, 0xFFFF6B74)


def turret_hp(c, k_show, hp):
    if k_show <= 0:
        return
    x, y = TURRET[0] - 90, TURRET[1] - 110
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x, y, 180, 20), 8, 8, M.fill(0xFF0A1424))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x, y, 180 * hp, 20), 8, 8, M.fill(RED))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(x, y, 180, 20), 8, 8, M.stroke(4, GOLD))


def shield(c, t, k):
    if k <= 0:
        return
    p = M.skia.Paint(AntiAlias=True, Color=M.alpha(0xFF9AD0F5, .35 * k))
    c.drawCircle(TURRET[0], TURRET[1] - 110, 125 * back(k), p)
    c.drawCircle(TURRET[0], TURRET[1] - 110, 125 * back(k), M.stroke(8, M.alpha(0xFF9AD0F5, k)))
    for j in range(6):
        a = j * math.pi / 3 + t
        c.drawCircle(TURRET[0] + math.cos(a) * 125, TURRET[1] - 110 + math.sin(a) * 125, 8, M.fill(M.alpha(0xFFFFFFFF, k)))


JINX_SIEGE = P(720, 640)


@M.escena("armadura", "mapa", cam=lambda b: [(0, (TURRET[0] - 200, TURRET[1] - 60, 1.35))],
          sfx=lambda b: [("jinx_basico", b.at("ochenta") - .6 + j * .7) for j in range(3)] + [("ding", b.at("ochenta"))])
def armadura(c, lt, b):
    t = b.t0 + lt
    fires = [b.at("ochenta") - .6 + j * .7 for j in range(3)]
    for f in fires:
        shot(c, JINX_SIEGE, (TURRET[0] - 20, TURRET[1] - 80), (lt - f) / .25, "bala", BLUE)
    shield(c, t, (lt - b.at("sin")) / .4)
    turret_hp(c, 1, 1 - .01 * sum(lt > f + .25 for f in fires))
    badge(c, "SIN SÚBDITOS ENEMIGOS", TURRET[0] - 200, TURRET[1] + 110, 34, M.INK, 0xFFFFFFFF, (lt - b.at("súbditos")) / .3)
    jinx(c, JINX_SIEGE)
    with b.hud(c):
        big_number(c, "-80%", 300, 680, (lt - b.at("ochenta")) / .35, 0xFF9AD0F5, 160)
        caption(c, "DE DAÑO RECIBIDO", (lt - b.at("ochenta") - .2) / .3, 0xFF9AD0F5, 800)


@M.escena("porqueso", "mapa", prof=lambda b: [(0, "puntero"), ("cachetadas", "asombro")], cam=lambda b: [(0, (TURRET[0] - 200, TURRET[1] - 60, 1.35))],
          sfx=lambda b: [("jinx_basico", .2 + j * .55, .8) for j in range(int((b.at("cachetadas") - .4) / .55))]
          + [("puno", b.at("cachetadas") + j * .35, .7) for j in range(3)])
def porqueso(c, lt, b):
    t = b.t0 + lt
    tc = b.at("cachetadas")
    n = int(max(0, min(lt, tc - .4) - .2) / .55) + 1
    for j in range(3):  # slaps against the turret
        k = (lt - tc - j * .35 + .15) / .15
        if 0 < k < 2.2:
            M.slap(c, TURRET[0] - 120, TURRET[1] - 100 + j * 30, min(1, k), -10 + j * 8)
            M.pow_text(c, "¡PLAF!", TURRET[0] - 230, TURRET[1] - 300 + j * 40, min(1, k - 1) if k > 1 else 0, size=60)
    for j in range(n):
        shot(c, JINX_SIEGE, (TURRET[0] - 20, TURRET[1] - 80), (lt - .2 - j * .55) / .25, "bala", BLUE)
    shield(c, t, 1)
    turret_hp(c, 1, .97 - .004 * n)
    jinx(c, JINX_SIEGE)
    with b.hud(c):
        caption(c, "SIN TU OLEADA… CASI NADA", (lt - b.at("oleada")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
