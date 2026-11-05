"""Class 13: blue buff (ability haste, mana/energy regen) and red buff (burn + slow on attacks, regen out of combat);
both last 120 s and transfer to the champion who kills you (refreshing)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=13)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse, shot  # noqa: E402

AZUL, ROJO = 0xFF4A9FE8, 0xFFE8584A
JY = (M.G.lane_y("central", 4000) + M.G.lane_y("inferior", 4000)) / 2  # jungle between mid and bot
MB, MR = (3700, JY), (4500, JY)
CAM = (4100, JY - 40, 1.0)


def aura(c, x, y, color, k, t):
    if k <= 0:
        return
    p = M.skia.Paint(AntiAlias=True, Color=M.alpha(color, .55 * k * (.8 + .2 * math.sin(t * 5))),
                     MaskFilter=M.skia.MaskFilter.MakeBlur(M.skia.kNormal_BlurStyle, 26))
    c.drawCircle(x, y, 110, p)


def you(c, pos, t, blue=0.0, red=0.0, flash=0.0, dead=0.0, hp=1.0):
    aura(c, *pos, AZUL, blue, t)
    aura(c, *pos, ROJO, red, t)
    champ(c, *pos, "Warwick", "azul", "TÚ", 1, flash, hp, dead, s=.85)


# ---------------- classroom
M.pizarra("hook", [("BUFF AZUL", 540, 450, 100, 0xFF9AD0F5, .2), ("BUFF ROJO", 540, 590, 100, CHALK_R, .6),
                   ("¿QUÉ TIENEN?", 540, 760, 96, CHALK, "especial")], prof=[(0, "piensa"), ("rojo", "explica")])
M.pizarra("spoiler", [("NO SON SOLO COLORES", 540, 520, 80, CHALK, "colores"), ("CAMBIAN TU CAMPEÓN", 540, 680, 84, CHALK_Y, "cambian")],
          prof=[(0, "picara")])
M.pizarra("azul2", [("+ REGENERACIÓN", 540, 520, 90, 0xFF9AD0F5, "regeneración"), ("DE MANÁ O ENERGÍA", 540, 660, 84, CHALK, "energía")],
          prof=[(0, "explica")])
M.pizarra("rojo2", [("FUERA DE PELEA:", 540, 520, 90, CHALK, "peleando"), ("+ VIDA", 540, 690, 140, 0xFF8EE08E, "vida")],
          prof=[(0, "explica")])
M.pizarra("dura", [("LOS DOS DURAN", 540, 500, 96, CHALK, "duran"), ("120 s", 540, 720, 180, CHALK_Y, "ciento")],
          prof=[(0, "explica")])
M.pizarra("broma", [("TE ASALTAN…", 540, 500, 96, CHALK, "asaltaran"), ("Y SE LLEVAN TU TORTA", 540, 680, 84, CHALK_R, "torta")],
          prof=[(0, "picara")])


def quien_extra(c, lt, b):
    M.chalk_line(c, "AZUL → MAGOS", 540, 600, 84, (lt - b.at("azul")) / .4, 0xFF9AD0F5)
    M.chalk_line(c, "ROJO → ATAQUES BÁSICOS", 540, 760, 76, (lt - b.at("rojo")) / .4, CHALK_R)


M.pizarra("quien", [("¿QUIÉN LO NECESITA?", 540, 440, 84, CHALK, "necesita")], prof=[(0, "explica")], extra=quien_extra)
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("¿LLEVAS BUFF?", 540, 580, 96, CHALK, "buff"),
                  ("NO TE ARRIESGUES", 540, 740, 96, CHALK_R, "arriesgues")], prof=[(0, "explica"), ("regalas", "asombro")])
M.pizarra("tip2", [("RIVAL BRILLANDO", 540, 520, 96, CHALK, "brillando"), ("= PREMIO EXTRA", 540, 690, 100, CHALK_Y, "premio")],
          prof=[(0, "picara")])
M.pizarra("jungla", [("¿ERES EL JUNGLA?", 540, 520, 96, CHALK, "jungla"), ("COMPARTE", 540, 690, 120, 0xFF8EE08E, "necesitar")],
          prof=[(0, "explica"), ("necesitar", "guino")])
K.cierre_teemo("AZUL: HABILIDADES Y MANÁ", "ROJO: QUEMA, RALENTIZA Y CURA", "1 LIKE = 1 BUFF PARA TI")


# ---------------- jungle
@M.escena("donde", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("azul")), ("ding", b.at("rojo"))])
def donde(c, lt, b):
    t = b.t0 + lt
    K.monster(c, *MB, .9, t, AZUL, 0xFFBFE0FF, "blob", (lt - b.at("azul")) / .4, label="AZUL", sprite="azul")
    K.monster(c, *MR, .9, t, ROJO, 0xFFFFC0B0, "blob", (lt - b.at("rojo")) / .4, label="ROJO", sprite="rojo")
    with b.hud(c):
        M.sign(c, t, lt / .5, "LOS BUFFS", "DE LA JUNGLA")


@M.escena("azul", "mapa", cam=lambda b: [(0, (MB[0] + 200, JY - 40, 1.3))], sfx=lambda b: [("ding", b.at("aceleración")), ("habilidad", b.at("vuelven"))])
def azul(c, lt, b):
    t = b.t0 + lt
    K.monster(c, *MB, .9, t, AZUL, 0xFFBFE0FF, "blob", 1 - ease((lt - .2) / .3) * 1.0 + 0.0001, sprite="azul")
    pos = (MB[0] + 300, JY + 40)
    you(c, pos, t, blue=ease((lt - .4) / .4))
    with b.hud(c):
        K.cd_clock(c, 540, 1240, 1 - clamp((lt - b.at("vuelven")) / 1.0), ease((lt - b.at("aceleración")) / .3), "Q", 0x999AD0F5)
        caption(c, "TUS HECHIZOS VUELVEN MÁS RÁPIDO", (lt - b.at("vuelven")) / .3, 0xFF9AD0F5)


@M.escena("rojo", "mapa", cam=lambda b: [(0, (MR[0], JY - 40, 1.3))], sfx=lambda b: [("caitlyn_basico", b.at("ataques")), ("ignite", b.at("quemen"))])
def rojo(c, lt, b):
    t = b.t0 + lt
    pos = (MR[0] - 300, JY + 40)
    enemy = (MR[0] + 200, JY - 20)
    you(c, pos, t, red=1)
    ta = b.at("ataques")
    shot(c, pos, enemy, (lt - ta) / .3, "bala", ROJO)
    burnt = lt > ta + .3
    champ(c, *enemy, "Draven", "rojo", "RIVAL", 1, pulse(lt, ta + .3, 8), .8, s=.85)
    if burnt:
        for j in range(5):
            ph = (t * 2 + j / 5) % 1
            c.drawCircle(enemy[0] - 40 + j * 20, enemy[1] - 60 - ph * 80, 12 * (1 - ph), M.fill(M.alpha(0xFFFF8A3A, 1 - ph)))
        badge(c, "LENTO", enemy[0], enemy[1] + 150, 30, 0xFF9AD0F5, M.INK, (lt - b.at("ralenticen")) / .3)
    with b.hud(c):
        caption(c, "QUEMA Y RALENTIZA", (lt - b.at("quemen")) / .3, ROJO)


@M.escena("ejemplo", "mapa", cam=lambda b: [(0, (6000, M.G.lane_y("inferior", 6000) - 40, 1.15))],
          sfx=lambda b: [("caitlyn_basico", b.at("ralentiza")), ("ignite", b.at("ralentiza") + .3)])
def ejemplo(c, lt, b):
    t = b.t0 + lt
    LYb = M.G.lane_y("inferior", 6000)
    run = (5900 + 180 * ease(lt / 3), LYb - 20)
    chase = (5550 + 260 * ease(lt / 3), LYb + 20)
    aura(c, *chase, ROJO, 1, t)
    champ(c, *chase, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.85)
    shot(c, chase, run, (lt - b.at("ralentiza")) / .3, "bala", ROJO)
    champ(c, *run, "Draven", "rojo", "RIVAL", 1, pulse(lt, b.at("ralentiza") + .3, 8), .5, s=.85)
    with b.hud(c):
        caption(c, "MUY DIFÍCIL ESCAPARLE", (lt - b.at("difícil")) / .3, ROJO)


@M.escena("roba", "mapa", prof=lambda b: [(0, "puntero"), ("lleva", "asombro")], cam=lambda b: [(0, (4100, JY - 40, 1.25))],
          sfx=lambda b: [("draven_hacha", b.at("mata") - .3), ("campeon_muere", b.at("mata")), ("ding", b.at("lleva"))])
def roba(c, lt, b):
    t = b.t0 + lt
    tm, tl = b.at("mata"), b.at("lleva")
    pos, enemy = (3950, JY + 30), (4300, JY - 30)
    M.shot(c, enemy, pos, (lt - tm + .3) / .3, "hacha")
    you(c, pos, t, blue=1 - ease((lt - tl) / .4), dead=ease((lt - tm) / .3), hp=0 if lt > tm else .2)
    aura(c, *enemy, AZUL, ease((lt - tl) / .4), t)
    champ(c, *enemy, "Draven", "rojo", "RIVAL", 1, 0, 1, s=.85)
    if 0 < lt - tl < 1:  # the buff flies to the killer
        k = ease(lt - tl)
        c.drawCircle(pos[0] + (enemy[0] - pos[0]) * k, pos[1] + (enemy[1] - pos[1]) * k - math.sin(k * 3.14) * 120, 30, M.fill(AZUL))
    with b.hud(c):
        caption(c, "TE MATA… Y SE LLEVA TU BUFF", (lt - tl) / .3, 0xFFFF6B74)


@M.escena("inversa", "mapa", prof=lambda b: [(0, "puntero"), ("tuyo", "feliz")], cam=lambda b: [(0, (4100, JY - 40, 1.25))],
          sfx=lambda b: [("caitlyn_basico", b.at("matas") - .3), ("campeon_muere", b.at("matas")), ("ding", b.at("tuyo"))])
def inversa(c, lt, b):
    t = b.t0 + lt
    tm, tt = b.at("matas"), b.at("tuyo")
    pos, enemy = (3950, JY + 30), (4300, JY - 30)
    shot(c, pos, enemy, (lt - tm + .3) / .3, "bala", BLUE)
    aura(c, *enemy, ROJO, 1 - ease((lt - tt) / .4), t)
    champ(c, *enemy, "Draven", "rojo", "RIVAL", 1, 0, 0 if lt > tm else .2, ease((lt - tm) / .3), s=.85)
    you(c, pos, t, red=ease((lt - tt) / .4))
    with b.hud(c):
        caption(c, "LO MATAS: EL BUFF ES TUYO (Y SE REINICIA)", (lt - tt) / .3, 0xFF8EE08E)


if __name__ == "__main__":
    M.main()
