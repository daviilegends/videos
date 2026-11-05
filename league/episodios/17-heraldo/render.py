"""Class 17: Rift Herald (top pit at 15:00, once, gone at 19:45; drops the Eye 20 s; summoned: 2.5 s wind-up, first headbutt
3000 true damage to the structure, later ones less; loses a big chunk of health per hit; knocks back nearby enemies)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=17)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse  # noqa: E402

P = M.G.BARON
HER = 0xFF8A6AD8
T = M.G.named_turret("rojo_superior_exterior")
CAMP = (P[0], P[1] - 40, 1.15)
CAMT = (T[0] + 300, T[1] - 60, 1.15)


def herald_at(c, x, y, t, k=1.0, hp=1.0, flash=0.0, s=.75):
    K.monster(c, x, y, s, t, HER, None, "herald", k, hp=hp, flash=flash)


def eye_item(c, x, y, k, t):
    if k <= 0:
        return
    c.save()
    c.translate(x, y + math.sin(t * 4) * 8)
    c.scale(M.back(min(1, k)), M.back(min(1, k)))
    p = M.skia.Paint(AntiAlias=True, Color=M.alpha(HER, .6), MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 24))
    c.drawCircle(0, 0, 60, p)
    c.drawOval(M.skia.Rect.MakeXYWH(-44, -28, 88, 56), M.fill(0xFFF4F0FF))
    c.drawOval(M.skia.Rect.MakeXYWH(-44, -28, 88, 56), M.stroke(6))
    c.drawCircle(0, 0, 18, M.fill(HER))
    c.drawCircle(0, 0, 8, M.fill(M.INK))
    c.restore()


def tower_hp(c, frac):
    c.drawRoundRect(M.skia.Rect.MakeXYWH(T[0] - 110, T[1] - 300, 220, 22), 8, 8, M.fill(0xFF0A1424))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(T[0] - 110, T[1] - 300, 220 * clamp(frac), 22), 8, 8, M.fill(RED))
    c.drawRoundRect(M.skia.Rect.MakeXYWH(T[0] - 110, T[1] - 300, 220, 22), 8, 8, M.stroke(4, GOLD))


def charge(c, lt, t, t0, frac0=1.0, dmg=.6, enemies=False):
    """Summoned Herald: wind-up 2.5 s (shortened on screen), leap and headbutt the turret."""
    wind = clamp((lt - t0) / 1.2)
    hit = t0 + 1.5
    x = T[0] + 520 - 400 * ease(clamp((lt - t0 - 1.2) / .3))
    shake = math.sin(t * 40) * 8 * (wind if lt < t0 + 1.2 else 0)
    herald_at(c, x + shake, T[1] + 20, t, 1, flash=pulse(lt, hit, 8))
    frac = frac0 - dmg * (lt > hit)
    tower_hp(c, frac)
    M.burst(c, (T[0] + 60, T[1] - 80), pulse(lt, hit, 4), 0xFFFFE27A, 110)
    if enemies:
        kb = ease(clamp((lt - hit) / .4))
        champ(c, T[0] + 180 - 260 * kb, T[1] + 160, "LeeSin", "rojo", "RIVAL", 1, pulse(lt, hit, 8), .9, s=.75)
    return hit


# ---------------- classroom
M.pizarra("hook", [("¿UN MONSTRUO QUE", 540, 450, 90, CHALK, .1), ("TIRA TORRES?", 540, 600, 110, 0xFFC8A8F8, "torres")],
          prof=[(0, "piensa"), ("cabezazo", "asombro")])
M.pizarra("spoiler", [("NO ES UN CAMPEÓN", 540, 520, 90, CHALK, "campeón"), ("TU EQUIPO LO INVOCA", 540, 690, 84, CHALK_Y, "invocar")],
          prof=[(0, "explica")])
M.pizarra("una", [("1 SOLA VEZ", 540, 500, 120, CHALK, "sola"), ("SE VA A LAS 19:45", 540, 690, 90, CHALK_Y, "diecinueve")],
          prof=[(0, "explica")])
M.pizarra("broma", [("3,000", 540, 520, 180, CHALK_R, "tres"), ("NI TU TÍO EN LA FINAL", 540, 720, 80, CHALK, "tío")],
          prof=[(0, "feliz")])
M.pizarra("despues", [("DESPUÉS, EN ESE FOSO:", 540, 500, 84, CHALK, "después"), ("EL BARÓN", 540, 680, 120, 0xFFC8A8F8, "barón")],
          prof=[(0, "picara")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("ÚSALO SIN DEFENSORES", 540, 600, 80, CHALK, "defensores"),
                  ("PARA QUE CUENTE", 540, 760, 96, CHALK_Y, "cuente")], prof=[(0, "explica"), ("cuente", "guino")])
M.pizarra("tip3", [("TORRE DE 5 MINUTOS", 540, 520, 86, CHALK, "cinco"), ("→ CAE EN 1", 540, 700, 130, CHALK_Y, "uno")],
          prof=[(0, "feliz")])
K.cierre_teemo("15:00 · UNA VEZ · OJO 20 s", "CABEZAZO: 3,000 DE DAÑO VERDADERO", "1 LIKE = 1 CABEZAZO")


# ---------------- pit and turret
@M.escena("que", "mapa", cam=lambda b: [(0, CAMP)], sfx=lambda b: [("dragon_vuela", b.at("quince"))])
def que(c, lt, b):
    t = b.t0 + lt
    herald_at(c, *P, t, (lt - b.at("heraldo")) / .5)
    with b.hud(c):
        M.sign(c, t, lt / .5, "EL HERALDO", "DE LA GRIETA")
        caption(c, "MINUTO 15 · FOSO DE ARRIBA", (lt - b.at("quince")) / .3, HER)


@M.escena("ojo", "mapa", cam=lambda b: [(0, CAMP)], sfx=lambda b: [("anciano_muere", .3), ("ding", b.at("ojo"))])
def ojo(c, lt, b):
    t = b.t0 + lt
    herald_at(c, *P, t, 1 - ease((lt - .3) / .4), hp=0, flash=pulse(lt, .2, 8))
    entrance = (P[0] - 200, P[1] + 330)
    eye_item(c, *entrance, (lt - b.at("ojo")) / .4, t)
    badge(c, "20 s", entrance[0] + 120, entrance[1] - 80, 32, GOLD, M.INK, (lt - b.at("veinte")) / .3)
    with b.hud(c):
        caption(c, "SUELTA SU OJO · 20 SEGUNDOS", (lt - b.at("veinte")) / .3, HER)


@M.escena("recoge", "mapa", cam=lambda b: [(0, CAMP)], sfx=lambda b: [("ding", b.at("recoge")), ("dragon_vuela", b.at("invoca"))])
def recoge(c, lt, b):
    t = b.t0 + lt
    entrance = (P[0] - 200, P[1] + 330)
    k = ease(lt / 1.0)
    you = (entrance[0] - 300 + 300 * k, entrance[1] + 20)
    eye_item(c, *entrance, 1 - ease((lt - b.at("recoge")) / .3), t)
    herald_at(c, entrance[0] + 120, entrance[1] - 60, t, (lt - b.at("invoca")) / .5, s=.6)
    champ(c, *you, "Garen", "azul", "TÚ", 1, 0, 1, s=.8)
    with b.hud(c):
        caption(c, "LO RECOGES → LO INVOCAS DE TU LADO", (lt - b.at("invoca")) / .3, BLUE)


@M.escena("carga", "mapa", cam=lambda b: [(0, CAMT)], sfx=lambda b: [("dragon_vuela", b.at("prepara")), ("impacto", b.at("prepara") + 1.5)])
def carga(c, lt, b):
    t = b.t0 + lt
    charge(c, lt, t, b.at("prepara"), 1.0, .5)
    with b.hud(c):
        caption(c, "SE PREPARA… Y SALTA CONTRA LA TORRE", (lt - b.at("salta")) / .3, HER)


@M.escena("tresmil", "mapa", prof=lambda b: [(0, "puntero"), ("tres", "asombro")], cam=lambda b: [(0, CAMT)],
          sfx=lambda b: [("impacto", .3), ("ding", b.at("tres"))])
def tresmil(c, lt, b):
    t = b.t0 + lt
    herald_at(c, T[0] + 140, T[1] + 20, t)
    tower_hp(c, .5)
    with b.hud(c):
        M.big_number(c, "3,000", 330, 620, (lt - b.at("tres")) / .35, HER, 150)
        caption(c, "DE DAÑO VERDADERO", (lt - b.at("verdadero")) / .3, HER)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, CAMT)], sfx=lambda b: [("impacto", b.at("pedazo"))])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    hit = b.at("pedazo")
    herald_at(c, T[0] + 140, T[1] + 20, t, flash=pulse(lt, hit, 8))
    tower_hp(c, 1 - .55 * (lt > hit))
    M.burst(c, (T[0] + 60, T[1] - 80), pulse(lt, hit, 4), 0xFFFFE27A, 110)
    with b.hud(c):
        caption(c, "UN BUEN PEDAZO DE UN SOLO GOLPE", (lt - hit) / .3, GOLD)


@M.escena("menos", "mapa", cam=lambda b: [(0, CAMT)], sfx=lambda b: [("impacto", .4), ("impacto", 1.6, .6)])
def menos(c, lt, b):
    t = b.t0 + lt
    hp = 1 - .66 * (lt > .4)
    herald_at(c, T[0] + 140, T[1] + 20, t, hp=max(.1, hp - .2 * (lt > 1.6)), flash=max(pulse(lt, .4, 8), pulse(lt, 1.6, 8)))
    tower_hp(c, .45 - .15 * (lt > .4) - .08 * (lt > 1.6))
    with b.hud(c):
        caption(c, "CADA GOLPE: MENOS DAÑO Y MENOS VIDA", (lt - b.at("menos")) / .3, GOLD)


@M.escena("campeones", "mapa", cam=lambda b: [(0, CAMT)], sfx=lambda b: [("dragon_vuela", .2), ("impacto", 1.7)])
def campeones(c, lt, b):
    t = b.t0 + lt
    charge(c, lt, t, .2, .6, .3, enemies=True)
    with b.hud(c):
        caption(c, "A LOS ENEMIGOS CERCA, LOS AVIENTA", (lt - b.at("avienta")) / .3, 0xFFFF6B74)


@M.escena("tip2", "mapa", cam=lambda b: [(0, (T[0] + 240, T[1] - 40, 1.05))],
          sfx=lambda b: [("dragon_vuela", .2), ("impacto", 1.7), ("torre_a_subdito", .6)])
def tip2(c, lt, b):
    t = b.t0 + lt
    for j, (dx, dy) in enumerate(((240, -80), (290, 10), (250, 90))):
        M.minion(c, T[0] + dx, T[1] + dy, "azul", -1, t)
    charge(c, lt, t, .2, .8, .35)
    with b.hud(c):
        caption(c, "CON TU OLEADA: LA TORRE NO SABE A QUIÉN", (lt - b.at("elegir")) / .3, BLUE)


if __name__ == "__main__":
    M.main()
