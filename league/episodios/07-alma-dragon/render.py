"""Class 07: dragon soul. 4 drakes -> soul; first two drakes are different elements, then the rift's dominant element;
soul permanent for the team; then the Elder dragon; Aspect of the Dragon for living allies, 150 s, lost on death."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
from motor import (BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, chalk_circle, chalk_line,  # noqa: E402
                   chalk_stroke, clamp, ease, keys, pulse, shot)

M.setup(__file__, clase=7)
G = M.G
D = G.DRAGON
CAM = (D[0] - 60, D[1] - 80, 1.15)
FIRE, OCEAN, ELDER = 0xFFFF8A3A, 0xFF3FA9C5, 0xFFB9A6E8
TEAM = [((D[0] - 430, D[1] - 140), "Caitlyn"), ((D[0] - 390, D[1] + 120), "Jinx")]
ENEMIES = [((D[0] + 360, D[1] - 260), "Draven"), ((D[0] + 140, D[1] - 360), "Ashe")]


def team(c, a_aura=0.0, t=0.0, dead=(), hp=1.0):
    for j, (p, n) in enumerate(TEAM):
        if a_aura > 0 and n not in dead:
            glow = M.skia.Paint(AntiAlias=True, Color=M.alpha(ELDER, .55 * a_aura * (.8 + .2 * math.sin(t * 5))),
                                MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 30))
            c.drawCircle(*p, 120, glow)
        champ(c, *p, n, "azul", None, 1, 0, 0 if n in dead else hp, 1.0 if n in dead else 0, s=.8)


def enemies(c):
    for p, n in ENEMIES:
        champ(c, *p, n, "rojo", None, 1, 0, 1, s=.8)


def tracker(c, n_blue, k, color=FIRE, y=380):
    """HUD: 4 dragon slots for your team."""
    if k <= 0:
        return
    for j in range(4):
        x = 540 + (j - 1.5) * 120
        c.drawCircle(x, y, 44, M.fill(0xEE0E1418))
        c.drawCircle(x, y, 44, M.stroke(5, GOLD))
        if j < n_blue:
            M.icono(c, M.ICON_COLORS.get(color, "monstruos/dragon"), x, y, 74, k)


# ---------------- classroom ----------------
M.pizarra("hook", [("¿POR QUÉ TODOS", 540, 450, 90, CHALK, .1), ("PELEAN EL DRAGÓN?", 540, 590, 84, CHALK_Y, "dragón")],
          prof=[(0, "piensa"), ("tamal", "picara")], extra=lambda c, lt, b: M.tamal(c, 540, 860, 1.8, (lt - b.at("tamal")) / .4, b.t0 + lt))
M.pizarra("spoiler", [("NO ES EL DRAGÓN", 540, 520, 90, CHALK, "dragón"), ("ES LO QUE VIENE", 540, 680, 90, CHALK_Y, "después"),
                      ("DESPUÉS", 540, 800, 100, CHALK_Y, "después", .6)], prof=[(0, "picara")])


def marcas_extra(c, lt, b):
    for j in range(4):
        x = 230 + j * 160
        k = (lt - b.at("cuatro") - j * .25) / .3
        chalk_circle(c, x, 760, 55, (lt - b.at("marca")) / .4, CHALK, 7)
        if k > 0:
            M.icono(c, "monstruos/dragon_infernal", x, 760, 90, k)
    chalk_line(c, "= ALMA", 540, 960, 110, (lt - b.at("alma")) / .4, CHALK_Y)


M.pizarra("marcas", [("1 DRAGÓN = 1 MARCA", 540, 470, 80, CHALK, "marca")], prof=[(0, "explica"), ("alma", "feliz")], extra=marcas_extra)
M.pizarra("alma", [("EL ALMA ES DEL", 540, 450, 84, CHALK, "alma"), ("ELEMENTO DEL MAPA", 540, 570, 76, CHALK_Y, "alma"),
                   ("PERMANENTE", 540, 760, 110, 0xFF8EE08E, "permanente"), ("PARA TODO TU EQUIPO", 540, 900, 70, CHALK, "equipo")],
          prof=[(0, "explica"), ("permanente", "feliz")])


def vivos_extra(c, lt, b):
    M.chalk_check(c, 330, 860, (lt - b.at("vivos")) / .3, s=2)
    M.chalk_cross(c, 750, 860, (lt - b.at("murió")) / .3, s=1.6)
    chalk_line(c, "VIVO", 330, 1010, 56, (lt - b.at("vivos")) / .3, 0xFF8EE08E)
    chalk_line(c, "MURIÓ", 750, 1010, 56, (lt - b.at("murió")) / .3, CHALK_R)


M.pizarra("vivos", [("SOLO ALIADOS VIVOS", 540, 500, 84, CHALK_Y, "vivos")], prof=[(0, "explica")], extra=vivos_extra)
M.pizarra("broma", [("EL PODER MÁS FUERTE", 540, 480, 80, CHALK, "poder"), ("…PERDIDO POR", 540, 640, 84, CHALK, "valiente"),
                    ("ANDAR DE VALIENTE", 540, 770, 84, CHALK_R, "valiente", .7)], prof=[(0, "picara")])


def tip_extra(c, lt, b):
    for j in range(3):
        x = 230 + j * 160
        if lt > b.at("tres") + j * .2:
            M.icono(c, "monstruos/dragon_infernal", x, 780, 96, (lt - b.at("tres") - j * .2) / .3)
    chalk_circle(c, 230 + 3 * 160, 780, 48, (lt - b.at("cuarto")) / .4, CHALK_Y, 8)
    chalk_line(c, "NO SE REGALA", 540, 960, 90, (lt - b.at("regala")) / .4, CHALK_Y)


M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("RIVAL CON 3 DRAGONES", 540, 580, 70, CHALK, "tres")],
          prof=[(0, "explica"), ("regala", "guino")], extra=tip_extra)


@M.escena("cierre", "aula", prof=[(0, "explica"), ("like", "picara"), ("teemo", "feliz")],
          sfx=lambda b: [("tiza", 0), ("ding", b.at("like")), ("dragon_fuego", b.at("teemo") - .1), ("teemo_muere", b.at("teemo") + .2)])
def cierre(c, lt, b):
    chalk_line(c, "4 DRAGONES = ALMA", 540, 400, 70, lt / .5)
    chalk_line(c, "ANCESTRAL: 150 s (SI SIGUES VIVO)", 540, 500, 54, (lt - .6) / .5, CHALK_Y)
    badge(c, "1 LIKE = 1 ALIENTO DE DRAGÓN", 540, 640, 42, GOLD, M.INK, (lt - b.at("like")) / .35, rot=-3)
    M.dragon(c, 300, 900, .9, b.t0 + lt, FIRE, ease((lt - b.at("aliento")) / .4))
    tt = b.at("teemo")
    shot(c, (380, 860), (700, 880), (lt - tt + .3) / .3, "habilidad", FIRE)
    M.teemo_punch(c, lt, [tt], 760, 880, ease((lt - b.at("like")) / .4), b.t0 + lt)


# ---------------- map: the dragon pit ----------------
@M.escena("cuatro", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("dragon_vuela", .2), ("ding", b.at("cuatro")), ("ding", b.at("alma"))])
def cuatro(c, lt, b):
    t = b.t0 + lt
    M.dragon(c, *D, 1.0, t, FIRE, ease(lt / .5))
    team(c)
    enemies(c)
    with b.hud(c):
        M.sign(c, t, lt / .5, "EL ALMA", "DEL DRAGÓN")
        n = int(clamp((lt - b.at("cuatro")) / 1.2) * 4)
        tracker(c, n, 1 if lt > b.at("cuatro") else 0, y=360)
        caption(c, "4 DRAGONES = ALMA DEL DRAGÓN", (lt - b.at("alma")) / .3, GOLD)


@M.escena("dos", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("dragon_vuela", b.at("dos")), ("dragon_vuela", b.at("distintos"))])
def dos(c, lt, b):
    t = b.t0 + lt
    M.dragon(c, D[0] - 150, D[1], .8, t, FIRE, ease((lt - b.at("dos")) / .4), label="ELEMENTO 1")
    M.dragon(c, D[0] + 160, D[1] - 20, .8, t + 1, OCEAN, ease((lt - b.at("distintos")) / .4), label="ELEMENTO 2")
    with b.hud(c):
        caption(c, "LOS 2 PRIMEROS: ELEMENTOS DISTINTOS", (lt - b.at("distintos")) / .3, GOLD)


def embers(c, k, t):
    if k <= 0:
        return
    c.drawRect(M.skia.Rect.MakeXYWH(D[0] - 2000, D[1] - 2000, 4000, 4000), M.fill(M.alpha(0x22FF6A2A, k)))
    for j in range(40):
        x = D[0] - 900 + (j * 137) % 1800
        y = D[1] + 700 - ((t * 120 + j * 53) % 1400)
        c.drawCircle(x, y, 8, M.fill(M.alpha(0xFFFFB14A, k * .8)))


@M.escena("mapa", "mapa", prof=lambda b: [(0, "puntero"), ("cambian", "asombro")], cam=lambda b: [(0, CAM), ("río", (D[0] - 500, D[1] - 300, .85))],
          sfx=lambda b: [("dragon_fuego", b.at("cambian"))])
def mapa(c, lt, b):
    t = b.t0 + lt
    embers(c, ease((lt - b.at("cambian")) / .6), t)
    M.dragon(c, *D, .9, t, FIRE)
    with b.hud(c):
        caption(c, "EL MAPA CAMBIA DE ASPECTO", (lt - b.at("cambian")) / .3, 0xFFFFB14A)


@M.escena("resto", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("dragon_vuela", b.at("todos")), ("ding", b.at("domina"))])
def resto(c, lt, b):
    t = b.t0 + lt
    embers(c, 1, t)
    for j in range(3):
        M.dragon(c, D[0] - 260 + j * 260, D[1] - 20 * j, .65, t + j, FIRE, ease((lt - b.at("todos") - j * .25) / .4))
    with b.hud(c):
        caption(c, "DESPUÉS: EL ELEMENTO QUE DOMINA", (lt - b.at("domina")) / .3, 0xFFFFB14A)


@M.escena("elder", "mapa", prof=lambda b: [(0, "puntero"), ("ancestral", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("dragon_vuela", b.at("aparece")), ("ding", b.at("ancestral"))])
def elder(c, lt, b):
    t = b.t0 + lt
    with b.hud(c):
        tracker(c, 4, 1, FIRE, y=360)
    M.dragon(c, *D, 1.3, t, ELDER, ease((lt - b.at("aparece")) / .5), label="ANCESTRAL" if lt > b.at("ancestral") else None)
    team(c)
    with b.hud(c):
        caption(c, "CON EL ALMA: APARECE EL ANCESTRAL", (lt - b.at("ancestral")) / .3, ELDER)


@M.escena("aspecto", "mapa", prof=lambda b: [(0, "puntero"), ("aspecto", "feliz")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("anciano_muere", b.at("matan")), ("ding", b.at("ciento"))])
def aspecto(c, lt, b):
    t = b.t0 + lt
    tm = b.at("matan")
    M.dragon(c, *D, 1.3, t, ELDER, 1 - ease((lt - tm - .3) / .4))
    team(c, ease((lt - b.at("aspecto")) / .4), t)
    badge(c, "150 s", TEAM[1][0][0] + 130, TEAM[1][0][1] - 120, 38, ELDER, M.INK, (lt - b.at("ciento")) / .3)
    with b.hud(c):
        caption(c, "ASPECTO DEL DRAGÓN · 150 SEGUNDOS", (lt - b.at("aspecto")) / .3, ELDER)


@M.escena("muerte", "mapa", prof=lambda b: [(0, "puntero"), ("pierdes", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("campeon_muere", b.at("mueres"))])
def muerte(c, lt, b):
    t = b.t0 + lt
    dead = ("Jinx",) if lt > b.at("mueres") else ()
    team(c, 1, t, dead)
    enemies(c)
    badge(c, "LO PIERDES", TEAM[1][0][0], TEAM[1][0][1] - 140, 36, RED, 0xFFFFFFFF, (lt - b.at("pierdes")) / .3)
    with b.hud(c):
        caption(c, "SI MUERES, LO PIERDES", (lt - b.at("pierdes")) / .3, 0xFFFF6B74)


@M.escena("tip2", "mapa", prof=lambda b: [(0, "puntero"), ("decidir", "asombro")], cam=lambda b: [(0, (D[0] - 300, D[1] - 150, 1.0))],
          sfx=lambda b: [("caitlyn_basico", b.at("pelea")), ("draven_hacha", b.at("pelea") + .4), ("jinx_basico", b.at("pelea") + .8),
                         ("ding", b.at("decidir"))])
def tip2(c, lt, b):
    t = b.t0 + lt
    M.dragon(c, *D, .9, t, FIRE)
    tp = b.at("pelea")
    for j in range(3):
        f = tp + j * .4
        a, z = (TEAM[j % 2][0], ENEMIES[j % 2][0]) if j % 2 == 0 else (ENEMIES[0][0], TEAM[0][0])
        shot(c, a, z, (lt - f) / .35, "hacha" if j % 2 else "bala", BLUE)
    team(c)
    enemies(c)
    with b.hud(c):
        tracker(c, 2, 1, FIRE, y=360)
        caption(c, "DESDE EL 3er DRAGÓN, CADA PELEA PESA", (lt - b.at("tercer")) / .3, GOLD)


if __name__ == "__main__":
    M.main()
