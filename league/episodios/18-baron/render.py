"""Class 18: Baron Nashor (20:00 since V26.01, was 25:00; respawn 6:00; Hand of Baron 180 s to living allies: AD, AP,
faster recall, aura that greatly empowers nearby minions)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=18)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, minion, pulse, shot  # noqa: E402

P = M.G.BARON
BAR = 0xFF8A5AD0
CAMP = (P[0], P[1] - 60, 1.1)
TEAM = [((P[0] - 380, P[1] + 220), "Garen"), ((P[0] - 160, P[1] + 330), "Caitlyn"), ((P[0] + 120, P[1] + 330), "Soraka")]
T = M.G.named_turret("rojo_central_exterior")


def baron(c, t, k=1.0, hp=1.0, flash=0.0):
    K.monster(c, *P, .85, t, BAR, None, "baron", k, hp=hp, flash=flash)


def team(c, t, aura=0.0, dead=()):
    for p, n in TEAM:
        if aura > 0 and n not in dead:
            g = M.skia.Paint(AntiAlias=True, Color=M.alpha(BAR, .55 * aura * (.8 + .2 * math.sin(t * 5))),
                             MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 26))
            c.drawCircle(*p, 110, g)
        champ(c, *p, n, "azul", None, 1, 0, 0 if n in dead else 1, 1.0 if n in dead else 0, s=.75)


# ---------------- classroom
M.pizarra("hook", [("¿POR QUÉ EL BARÓN", 540, 460, 96, CHALK, .1), ("CAMBIA LA PARTIDA?", 540, 600, 90, 0xFFC8A8F8, "partida")],
          prof=[(0, "piensa")])
M.pizarra("spoiler", [("NO ES SOLO UN MONSTRUO", 540, 500, 80, CHALK, "monstruo"), ("ES EL BOTÓN DE EMPUJAR", 540, 680, 80, CHALK_Y, "empujar")],
          prof=[(0, "picara")])
M.pizarra("antes", [("ANTES: 25:00", 540, 500, 110, CHALK, "veinticinco"), ("AHORA: 20:00", 540, 680, 110, 0xFF8EE08E, "sale"),
                    ("PARCHE 26.1", 540, 820, 70, CHALK_Y, "parche")], prof=[(0, "explica")],
          extra=lambda c, lt, b: M.chalk_stroke(c, [(250, 470), (830, 480)], (lt - b.at("sale") - .2) / .3, CHALK_R, 10))
M.pizarra("reaparece", [("LO MATAN →", 540, 520, 100, CHALK, "matan"), ("VUELVE EN 6 MIN", 540, 700, 100, CHALK_Y, "seis")],
          prof=[(0, "explica")])
M.pizarra("da", [("+ DAÑO DE ATAQUE", 540, 520, 90, CHALK, "daño"), ("+ PODER DE HABILIDAD", 540, 680, 84, CHALK_Y, "poder")],
          prof=[(0, "explica")])
M.pizarra("recall", [("RECALL", 540, 520, 120, 0xFF9AD0F5, "recall"), ("MUCHO MÁS RÁPIDO", 540, 700, 96, CHALK_Y, "rápido")],
          prof=[(0, "feliz")])
M.pizarra("broma", [("DE PRIMARIA…", 540, 500, 100, CHALK, "primaria"), ("A LUCHADORES PRO", 540, 680, 100, CHALK_Y, "luchadores")],
          prof=[(0, "feliz")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("ANTES DEL BARÓN:", 540, 580, 90, CHALK, "barón"),
                  ("QUE EL RIVAL NO LLEGUE", 540, 740, 84, CHALK_Y, "llegar")], prof=[(0, "explica"), ("pelea", "guino")])
M.pizarra("tip2", [("CON EL BUFF:", 540, 520, 100, CHALK, "buff"), ("EMPUJA", 540, 700, 150, 0xFF8EE08E, "empuja")],
          prof=[(0, "feliz")])
M.pizarra("tip3", [("¿EL RIVAL LO TIENE?", 540, 500, 86, CHALK, "rival"), ("DEFIENDE CON TORRES", 540, 680, 86, CHALK_Y, "defiende")],
          prof=[(0, "explica")])
K.cierre_teemo("20:00 · VUELVE EN 6 MIN", "MANO DEL BARÓN: 180 s (SOLO VIVOS)", "1 LIKE = 1 BARÓN PARA TI")


# ---------------- pit and lane
@M.escena("cuando", "mapa", cam=lambda b: [(0, CAMP)], sfx=lambda b: [("dragon_vuela", b.at("veinte"))])
def cuando(c, lt, b):
    t = b.t0 + lt
    baron(c, t, (lt - b.at("barón")) / .5)
    with b.hud(c):
        M.sign(c, t, lt / .5, "BARÓN NASHOR", "EL GRAN PREMIO")
        caption(c, "MINUTO 20 · FOSO DE ARRIBA", (lt - b.at("veinte")) / .3, BAR)


@M.escena("premio", "mapa", prof=lambda b: [(0, "puntero"), ("mano", "feliz")], cam=lambda b: [(0, (P[0] - 100, P[1] + 60, 1.0))],
          sfx=lambda b: [("anciano_muere", b.at("matarlo")), ("ding", b.at("ciento"))])
def premio(c, lt, b):
    t = b.t0 + lt
    tm = b.at("matarlo")
    baron(c, t, 1 - ease((lt - tm - .3) / .5), hp=.05 if lt < tm else 0, flash=pulse(lt, tm, 8))
    team(c, t, ease((lt - b.at("mano")) / .4))
    with b.hud(c):
        caption(c, "MANO DEL BARÓN · 180 SEGUNDOS", (lt - b.at("ciento")) / .3, BAR)


WAVE = [(T[0] - 280, T[1] - 70), (T[0] - 240, T[1] + 20), (T[0] - 300, T[1] + 90)]


def tower_hp(c, frac):
    c.drawRoundRect(M.skia.Rect.MakeXYWH(T[0] - 110, T[1] - 300, 220, 22), 8, 8, M.fill(0xFF0A1424))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(T[0] - 110, T[1] - 300, 220 * clamp(frac), 22), 8, 8, M.fill(RED))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(T[0] - 110, T[1] - 300, 220, 22), 8, 8, M.stroke(4, GOLD))


def wave(c, t, lt, buffed, hit_t):
    for j, p in enumerate(WAVE):
        if buffed:
            g = M.skia.Paint(AntiAlias=True, Color=M.alpha(BAR, .5), MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 20))
            c.drawCircle(*p, 70, g)
        minion(c, *p, "azul", 1, t, s=1.35 if buffed else 1.0, swing=abs(math.sin(t * 6 + j)))


@M.escena("subditos", "mapa", cam=lambda b: [(0, (T[0] - 240, T[1] - 40, 1.2))], sfx=lambda b: [("ding", b.at("poderosos"))])
def subditos(c, lt, b):
    t = b.t0 + lt
    buffed = lt > b.at("poderosos")
    wave(c, t, lt, buffed, 0)
    tower_hp(c, 1)
    champ(c, T[0] - 520, T[1] + 40, "Garen", "azul", "TÚ", 1, 0, 1, s=.8)
    with b.hud(c):
        caption(c, "SÚBDITOS CERCA DE TI: MUCHO MÁS FUERTES", (lt - b.at("poderosos")) / .3, BAR)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, (T[0] - 240, T[1] - 40, 1.2))],
          sfx=lambda b: [("golpe_subdito", .3 + j * .4, 1.5) for j in range(int(5 / .4))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    td = b.at("barón")
    buffed = lt > td
    wave(c, t, lt, buffed, 0)
    frac = 1 - .03 * min(lt, td) - (.2 * (lt - td) if buffed else 0)
    tower_hp(c, max(0, frac))
    with b.hud(c):
        caption(c, "CON BARÓN: LA DERRITE", (lt - td) / .3, BAR) if buffed else caption(c, "SIN BARÓN: COSQUILLAS", (lt - b.at("cosquillas")) / .3, CHALK)


@M.escena("vivos", "mapa", prof=lambda b: [(0, "puntero"), ("vivos", "explica")], cam=lambda b: [(0, (P[0] - 100, P[1] + 60, 1.0))],
          sfx=lambda b: [("anciano_muere", .2), ("ding", b.at("vivos"))])
def vivos(c, lt, b):
    t = b.t0 + lt
    team(c, t, ease((lt - .6) / .4), dead=("Soraka",))
    badge(c, "SIN BUFF", TEAM[2][0][0], TEAM[2][0][1] - 140, 30, RED, 0xFFFFFFFF, (lt - b.at("vivos")) / .3)
    with b.hud(c):
        caption(c, "SOLO LOS ALIADOS VIVOS", (lt - b.at("vivos")) / .3, BAR)


@M.escena("riesgo", "mapa", prof=lambda b: [(0, "puntero"), ("robar", "asombro")], cam=lambda b: [(0, (P[0], P[1] + 40, .95))],
          sfx=lambda b: [("impacto", b.at("encuentra")), ("impacto", b.at("robar"))])
def riesgo(c, lt, b):
    t = b.t0 + lt
    baron(c, t, 1, hp=.2)
    team(c, t)
    k = ease((lt - b.at("encuentra")) / .8)
    for j, n in enumerate(("LeeSin", "Draven")):
        champ(c, P[0] + 700 - 300 * k, P[1] - 220 + j * 180, n, "rojo", None, 1, 0, 1, s=.75)
    with b.hud(c):
        caption(c, "TE ENCUENTRAN A MEDIO BARÓN…", (lt - b.at("encuentra")) / .3, 0xFFFF6B74)


if __name__ == "__main__":
    M.main()
