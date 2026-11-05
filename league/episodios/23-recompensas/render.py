"""Class 23: kill gold and bounties (300 at levels 1-6 up to 420 at 18; first blood +100; bounty grows with gold advantage and
shrinks with deaths down to 50; assists split half; cap = base + 700, the excess carries over)."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "motor"))
import motor as M  # noqa: E402
M.setup(__file__, clase=23)
import kit as K  # noqa: E402
from motor import BLUE, CHALK, CHALK_R, CHALK_Y, GOLD, RED, badge, caption, champ, clamp, ease, pulse, shot  # noqa: E402

LY = M.G.lane_y("central", 6000)
YOU, RIV = (5780, LY + 30), (6220, LY - 30)
CAM = (6000, LY - 60, 1.35)


def wanted(c, x, y, k, amount, name="Draven"):
    """Old-west wanted poster with the champion icon and the bounty."""
    if k <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(-4)
    c.scale(M.back(min(1, k)), M.back(min(1, k)))
    r = M.skia.Rect.MakeXYWH(-170, -230, 340, 460)
    c.drawRect(r, M.fill(0xFFE8D2A0))
    c.drawRect(r, M.stroke(7, 0xFF6B4A2B))
    M.text(c, "SE BUSCA", 0, -170, M.font("segoeuib.ttf", 56), 0xFF5A2A10)
    c.save()
    c.clipPath(M.skia.Path.Circle(0, -30, 100), doAntiAlias=True)
    c.drawImageRect(M.icon(name), M.skia.Rect.MakeXYWH(-105, -135, 210, 210), M.skia.SamplingOptions(M.skia.FilterMode.kLinear))
    c.restore()
    c.drawCircle(0, -30, 100, M.stroke(6, 0xFF5A2A10))
    M.text(c, f"{amount} ORO", 0, 150, M.font("segoeuib.ttf", 60), 0xFFB02A20)
    c.restore()


# ---------------- classroom
M.pizarra("hook", [("¿POR QUÉ MATAR AL QUE", 540, 450, 80, CHALK, .1), ("VA GANANDO DA TANTO?", 540, 590, 84, CHALK_Y, "ganando")],
          prof=[(0, "piensa")])
M.pizarra("spoiler", [("EL JUEGO LE PONE", 540, 520, 96, CHALK, "juego"), ("PRECIO A SU CABEZA", 540, 690, 90, CHALK_R, "cabeza")],
          prof=[(0, "picara")])


def base_extra(c, lt, b):
    K.level_badge(c, 300, 760, 1, (lt - b.at("trescientos") + .2) / .3, size=60)
    M.chalk_line(c, "300", 600, 790, 120, (lt - b.at("trescientos")) / .4, K.ORO)
    K.level_badge(c, 300, 950, 18, (lt - b.at("dieciocho")) / .3, size=60)
    M.chalk_line(c, "420", 600, 980, 120, (lt - b.at("cuatrocientos")) / .4, K.ORO)


M.pizarra("base", [("MATAR A UN CAMPEÓN", 540, 450, 84, CHALK, "matar")], prof=[(0, "explica")], extra=base_extra,
          sfx_extra=lambda b: [("oro", b.at("trescientos"))])
M.pizarra("ejemplo", [("NIVEL 3 → 300", 540, 520, 110, K.ORO, "tres"), ("MÁS QUE CUALQUIER SÚBDITO", 540, 700, 72, CHALK, "súbdito")],
          prof=[(0, "explica")])
M.pizarra("broma2", [("MUERES MUCHO →", 540, 500, 96, CHALK, "mueres"), ("VALES CASI NADA", 540, 680, 96, CHALK_R, "nada")],
          prof=[(0, "picara"), ("auch", "asombro")])
M.pizarra("asistencia", [("LOS QUE AYUDAN:", 540, 520, 96, CHALK, "ayudan"), ("SE REPARTEN LA MITAD", 540, 690, 84, CHALK_Y, "mitad")],
          prof=[(0, "explica")])
M.pizarra("tope", [("TOPE POR MUERTE:", 540, 500, 96, CHALK, "tope"), ("BASE + 700", 540, 690, 130, CHALK_Y, "setecientos")],
          prof=[(0, "explica")])
M.pizarra("sobra", [("LO QUE SOBRA…", 540, 520, 100, CHALK, "sobra"), ("PARA LA PRÓXIMA", 540, 690, 100, CHALK_Y, "próxima")],
          prof=[(0, "explica")])
M.pizarra("tip", [("CONSEJO DE LA PROFE", 540, 420, 60, GOLD, 0), ("¿VAS PERDIENDO?", 540, 580, 100, CHALK, "perdiendo"),
                  ("CAZA AL QUE GANA", 540, 740, 100, 0xFF8EE08E, "cazar")], prof=[(0, "explica"), ("vuelta", "guino")])
M.pizarra("tip2", [("¿VAS GANANDO?", 540, 520, 100, CHALK, "ganando"), ("ERES EL PREMIO GORDO", 540, 700, 86, CHALK_R, "premio")],
          prof=[(0, "asombro")])
M.pizarra("tip3", [("JUEGA SEGURO", 540, 500, 110, CHALK, "seguro"), ("Y CON VISIÓN", 540, 680, 110, CHALK_Y, "visión")],
          prof=[(0, "explica")])
M.pizarra("tip4", [("¿CAZAS?", 540, 520, 120, CHALK, "caza"), ("VE EN GRUPO", 540, 700, 120, 0xFF8EE08E, "grupo")],
          prof=[(0, "feliz")])
K.cierre_teemo("BASE: 300 → 420 · 1ª SANGRE: +100", "VAS GANANDO = VALES MÁS", "1 LIKE = MÁS RECOMPENSA POR TEEMO")


# ---------------- lane
@M.escena("primera", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("caitlyn_basico", .2), ("campeon_muere", .5), ("oro", b.at("cien"))])
def primera(c, lt, b):
    t = b.t0 + lt
    shot(c, YOU, RIV, (lt - .2) / .3, "bala", BLUE)
    champ(c, *RIV, "Draven", "rojo", "RIVAL", 1, pulse(lt, .5, 8), 0 if lt > .5 else .1, ease((lt - .5) / .3), s=.85)
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.85)
    K.coin_pop(c, YOU[0], YOU[1] - 130, lt - b.at("cien"), 100)
    with b.hud(c):
        M.sign(c, t, lt / .5, "RECOMPENSAS", "POR CABEZA")
        M.badge(c, "PRIMERA SANGRE", 540, 1240, 50, RED, 0xFFFFFFFF, (lt - b.at("primera")) / .3)


@M.escena("sube", "mapa", prof=lambda b: [(0, "puntero"), ("recompensa", "asombro")], cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("oro", .3 + j * .5, .6) for j in range(4)] + [("ding", b.at("recompensa"))])
def sube(c, lt, b):
    t = b.t0 + lt
    champ(c, *RIV, "Draven", "rojo", "RIVAL", 1, 0, 1, s=.85)
    for j in range(4):
        K.coin_pop(c, RIV[0], RIV[1] - 130, lt - .3 - j * .5)
    amount = int(300 + 400 * clamp((lt - b.at("recompensa")) / 1.5))
    with b.hud(c):
        wanted(c, 540, 1180, (lt - b.at("recompensa")) / .4, amount)


@M.escena("broma", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("busca"))])
def broma(c, lt, b):
    t = b.t0 + lt
    champ(c, *RIV, "Draven", "rojo", "RIVAL", 1, 0, 1, s=.85)
    with b.hud(c):
        wanted(c, 540, 1180, 1, 700)
        caption(c, "SE BUSCA, VIVO O MUERTO", (lt - b.at("busca")) / .3, GOLD)


@M.escena("baja", "mapa", cam=lambda b: [(0, CAM)],
          sfx=lambda b: [("draven_hacha", .2 + j * .9) for j in range(3)] + [("campeon_muere", .65 + j * .9) for j in range(3)])
def baja(c, lt, b):
    t = b.t0 + lt
    deaths = sum(lt > .65 + j * .9 for j in range(3))
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, max([pulse(lt, .65 + j * .9, 8) for j in range(3)]), 1, s=.85)
    champ(c, *RIV, "Draven", "rojo", "RIVAL", 1, 0, 1, s=.85)
    for j in range(3):
        M.shot(c, RIV, YOU, (lt - .2 - j * .9) / .45, "hacha")
    with b.hud(c):
        wanted(c, 540, 1180, 1, max(50, 300 - deaths * 80), "Caitlyn")


@M.escena("minimo", "mapa", cam=lambda b: [(0, CAM)], sfx=lambda b: [("ding", b.at("cincuenta"))])
def minimo(c, lt, b):
    t = b.t0 + lt
    champ(c, *YOU, "Caitlyn", "azul", "TÚ", 1, 0, 1, s=.85)
    with b.hud(c):
        wanted(c, 540, 1180, 1, 50 if lt > b.at("cincuenta") else 60, "Caitlyn")
        caption(c, "MÍNIMO: 50 DE ORO", (lt - b.at("cincuenta")) / .3, GOLD)


if __name__ == "__main__":
    M.main()
