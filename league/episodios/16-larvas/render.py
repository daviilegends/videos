"""Class 16: Voidgrubs (top pit at 8:00, 3 grubs once per game, gone at 14:45; each spawns 4 voidmites every 12 s in combat;
each kill = Touch of the Void stack for the team: structures burn with true damage; 3 stacks = allied voidmites vs turrets;
Rift Herald in the same pit at 15:00)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=16)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse, shot  # noqa: E402

P = M.G.BARON
CAM = (P[0], P[1] - 40, 1.15)
VOID = 0xFF9B6CF0
GRUBS = [(P[0] - 150, P[1] + 40), (P[0] + 10, P[1] - 60), (P[0] + 160, P[1] + 50)]
T = M.G.named_turret("rojo_superior_exterior")


def grubs(c, t, k=1.0, alive=(1, 1, 1), flash=(0, 0, 0)):
    for j, (x, y) in enumerate(GRUBS):
        if alive[j]:
            K.monster(c, x, y, .55, t + j, VOID, None, "bug", (k - j * .15), flash=flash[j], angry=True)


def mites(c, t, center, n, k, color=VOID):
    if k <= 0:
        return
    for j in range(n):
        a = j * 2 * math.pi / n + t * 2
        r = 110 * ease(min(1, k)) + 10 * math.sin(t * 6 + j)
        x, y = center[0] + math.cos(a) * r, center[1] + math.sin(a) * r * .6 + 40
        c.drawCircle(x, y, 16, M.fill(color))
        c.drawCircle(x, y, 16, M.stroke(4))
        c.drawCircle(x + 5, y - 4, 4, M.fill(0xFFFFF4C8))


def burn(c, x, y, k, t):
    if k <= 0:
        return
    for j in range(7):
        ph = (t * 1.6 + j / 7) % 1
        c.drawCircle(x - 60 + j * 20, y - ph * 160, 18 * (1 - ph) * k, M.fill(M.alpha(VOID, (1 - ph) * k)))


def marks(c, n, k):
    for j in range(3):
        on = j < n
        c.drawCircle(400 + j * 140, 1240, 44, M.fill(VOID if on else 0xFF2A2F38))
        c.drawCircle(400 + j * 140, 1240, 44, M.stroke(6, GOLD))


# ---------------- classroom
M.pizarra("hook", [("¿QUÉ SON ESOS", 540, 450, 96, CHALK, .1), ("BICHOS MORADOS?", 540, 590, 96, 0xFFC8A8F8, "morados")],
          prof=[(0, "piensa")])
M.pizarra("spoiler", [("PARECEN INOFENSIVOS…", 540, 520, 84, CHALK, "inofensivos"), ("PUEDEN GANAR LA PARTIDA", 540, 690, 76, CHALK_Y, "ganar")],
          prof=[(0, "picara")])
M.pizarra("hasta", [("SI NADIE LAS MATA:", 540, 500, 86, CHALK, "nadie"), ("SE VAN A LAS 14:45", 540, 680, 96, CHALK_Y, "catorce")],
          prof=[(0, "explica")])
M.pizarra("broma", [("UNA CUCARACHA…", 540, 500, 96, CHALK, "cucaracha"), ("CON TODA SU FAMILIA", 540, 680, 84, CHALK_R, "familia")],
          prof=[(0, "asombro")])
M.pizarra("para_que", [("NO SON PARA PELEAR", 540, 500, 86, CHALK, "pelear"), ("SON PARA TIRAR TORRES", 540, 680, 84, CHALK_Y, "torres")],
          prof=[(0, "explica"), ("torres", "guino")])
M.pizarra("despues", [("MISMO FOSO, MINUTO 15:", 540, 500, 76, CHALK, "quince"), ("EL HERALDO", 540, 680, 110, 0xFFC8A8F8, "heraldo")],
          prof=[(0, "picara")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("¿QUIEREN TORRES?", 540, 580, 96, CHALK, "torres"),
                  ("LARVAS = VALEN MUCHO", 540, 740, 84, 0xFF8EE08E, "valen")], prof=[(0, "explica")])
M.pizarra("tip2", [("CUIDADO:", 540, 500, 100, CHALK_R, "cuidado"), ("EL JUNGLA RIVAL LLEGA", 540, 680, 84, CHALK, "jungla")],
          prof=[(0, "asombro")])
M.pizarra("tip3", [("HAZLAS CUANDO SABES", 540, 520, 84, CHALK, "sabes"), ("DÓNDE ESTÁ EL RIVAL", 540, 680, 90, CHALK_Y, "otro")],
          prof=[(0, "explica"), ("otro", "guino")])
K.cierre_teemo("8:00 · 3 LARVAS · UNA VEZ", "MARCAS = QUEMAR ESTRUCTURAS", "1 LIKE = 1 LARVA MÁS")


# ---------------- the pit
@M.escena("que", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("ocho"))])
def que(c, lt, b):
    t = b.t0 + lt
    grubs(c, t, (lt - b.at("larvas")) / .5)
    with b.hud(c):
        M.sign(c, t, lt / .5, "LAS LARVAS", "DEL VACÍO")
        caption(c, "FOSO DE ARRIBA · MINUTO 8", (lt - b.at("ocho")) / .3, VOID)


@M.escena("tres", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("tres"))])
def tres(c, lt, b):
    t = b.t0 + lt
    grubs(c, t)
    for j, (x, y) in enumerate(GRUBS):
        badge(c, str(j + 1), x, y - 120, 32, VOID, 0xFFFFFFFF, (lt - b.at("tres") - j * .2) / .3)
    with b.hud(c):
        caption(c, "3 LARVAS · UNA SOLA VEZ", (lt - b.at("vez")) / .3, GOLD)


@M.escena("pelea", "mapa", prof=lambda b: [(0, "puntero"), ("cuatro", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("impacto", b.at("doce")), ("impacto", b.at("cuatro"))])
def pelea(c, lt, b):
    t = b.t0 + lt
    grubs(c, t)
    for (x, y) in GRUBS:
        mites(c, t, (x, y), 4, (lt - b.at("cuatro")) / .5)
    champ(c, P[0] - 420, P[1] + 220, "Warwick", "azul", "TÚ", 1, 0, .8, s=.8)
    with b.hud(c):
        caption(c, "CADA 12 s: 4 BICHITOS POR LARVA", (lt - b.at("cuatro")) / .3, 0xFFFF6B74)


@M.escena("premio", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("subdito_muere", .3), ("ding", b.at("marca"))])
def premio(c, lt, b):
    t = b.t0 + lt
    grubs(c, t, 1, alive=(lt < .5, 1, 1), flash=(pulse(lt, .2, 8), 0, 0))
    champ(c, P[0] - 420, P[1] + 220, "Warwick", "azul", "TÚ", 1, 0, .8, s=.8)
    with b.hud(c):
        marks(c, 1 if lt > b.at("marca") else 0, 1)
        caption(c, "1 LARVA = 1 MARCA PARA TODO TU EQUIPO", (lt - b.at("equipo")) / .3, VOID)


@M.escena("quema", "mapa", cam=lambda b: [(0, (T[0] + 260, T[1] - 40, 1.2))],
          sfx=lambda b: [("caitlyn_basico", b.at("golpes")), ("ignite", b.at("quemen"))])
def quema(c, lt, b):
    t = b.t0 + lt
    you = (T[0] + 380, T[1] + 40)
    shot(c, you, (T[0] + 10, T[1] - 80), (lt - b.at("golpes")) / .25, "bala", BLUE)
    burn(c, T[0], T[1] - 60, ease((lt - b.at("quemen")) / .4), t)
    champ(c, *you, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.8)
    with b.hud(c):
        marks(c, 2, 1)
        caption(c, "ESTRUCTURAS ARDEN · DAÑO VERDADERO", (lt - b.at("verdadero")) / .3, VOID)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, (T[0] + 260, T[1] - 40, 1.2))],
          sfx=lambda b: [("caitlyn_basico", b.at("pegas")), ("ignite", b.at("ardiendo"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    you = (T[0] + 380, T[1] + 40)
    shot(c, you, (T[0] + 10, T[1] - 80), (lt - b.at("pegas")) / .25, "bala", BLUE)
    burn(c, T[0], T[1] - 60, ease((lt - b.at("ardiendo")) / .4) * (1 - ease((lt - b.at("rato") - .8) / .5)), t)
    champ(c, *you, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.8)
    with b.hud(c):
        caption(c, "TU GOLPE + ARDE UN RATO", (lt - b.at("ardiendo")) / .3, VOID)


@M.escena("tres_marcas", "mapa", prof=lambda b: [(0, "puntero"), ("torres", "feliz")], cam=lambda b: [(0, (T[0] + 260, T[1] - 40, 1.2))],
          sfx=lambda b: [("ding", b.at("tres")), ("impacto", b.at("torres"))])
def tres_marcas(c, lt, b):
    t = b.t0 + lt
    mites(c, t, (T[0] + 60, T[1] + 20), 8, (lt - b.at("invocas")) / .5, 0xFF7AB8F8)
    burn(c, T[0], T[1] - 60, 1, t)
    champ(c, T[0] + 400, T[1] + 40, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.8)
    with b.hud(c):
        marks(c, 3 if lt > b.at("tres") else 2, 1)
        caption(c, "3 MARCAS = BICHITOS ALIADOS VS TORRES", (lt - b.at("torres")) / .3, 0xFF7AB8F8)


if __name__ == "__main__":
    M.main()
