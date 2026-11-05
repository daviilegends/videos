"""2D Summoner's Rift map in a clean minimap style (khaki walkways, dark maze walls, blue river, light bases),
drawn in our art style (ink outlines, turret icons). The layout is traced from ref/minimapa_ref.png.
Orientation: blue base bottom-left, red top-right. World: 9000 x 9000 px (0.6 px per game unit).
API: draw(c, t, view_rect) draws the visible world; minimap(c, x, y, size, view_rect, t); named_turret(name).
The previous sand style is kept in grieta_arena.py."""
import math
from pathlib import Path

import numpy as np
import skia
from PIL import Image, ImageFilter

from mapa import brush, fill, polyline, stroke

S = 9000
BLUE, RED = 0xFF3FA9F5, 0xFFE84855
TILE, RES = 1024, 1.5
REF = Path(__file__).with_name("ref") / "minimapa_ref.png"
SQ0, SQ1 = 30, 528  # map square inside the reference image (pixels)

# terrain classes: 0 walkway, 1 wall, 2 river, 3 base, 4 outside
COLORS = np.array([(201, 192, 140), (34, 50, 60), (52, 160, 210), (160, 182, 190), (18, 27, 34)], np.float32)
COLORS_D = np.array([(182, 172, 122), (26, 40, 49), (40, 136, 186), (140, 162, 172), (14, 21, 27)], np.float32)
INK_RGB = np.array((30, 34, 40), np.float32)


def rf(px, py):
    """Reference pixel -> world coordinates."""
    return ((px - SQ0) / (SQ1 - SQ0) * S, (py - SQ0) / (SQ1 - SQ0) * S)


_T_RED = {"superior_exterior": (172, 57), "superior_interior": (296, 72), "superior_inhibidor": (383, 65),
          "central_exterior": (330, 237), "central_interior": (358, 183), "central_inhibidor": (404, 148),
          "inferior_exterior": (497, 375), "inferior_interior": (480, 250), "inferior_inhibidor": (488, 170),
          "nexo_1": (455, 82), "nexo_2": (470, 100)}
_T_BLUE = {"superior_exterior": (57, 175), "superior_interior": (75, 300), "superior_inhibidor": (67, 380),
           "central_exterior": (225, 310), "central_interior": (197, 365), "central_inhibidor": (150, 400),
           "inferior_exterior": (380, 490), "inferior_interior": (262, 480), "inferior_inhibidor": (172, 488),
           "nexo_1": (83, 450), "nexo_2": (100, 470)}
_INHIB = {"rojo": [(409, 64), (422, 130), (488, 145)], "azul": [(66, 410), (131, 420), (142, 488)]}
_NEXUS = {"rojo": (478, 80), "azul": (72, 476)}
_FOUNTAIN = {"rojo": (515, 40), "azul": (40, 515)}
ICON_PIX = (list(_T_RED.values()) + list(_T_BLUE.values()) + _INHIB["rojo"] + _INHIB["azul"] + list(_NEXUS.values())
            + [(497, 35), (37, 492), (20, 20)])

TURRETS = [(*rf(*p), RED) for p in _T_RED.values()] + [(*rf(*p), BLUE) for p in _T_BLUE.values()]
BARON, DRAGON = rf(183, 185), rf(372, 372)


def named_turret(name):
    """'rojo_inferior_exterior', 'azul_central_interior', ..."""
    team, rest = name.split("_", 1)
    return rf(*(_T_RED if team == "rojo" else _T_BLUE)[rest])


# ---------------- terrain from the reference ----------------
_F = {}


def fields():
    if _F:
        return _F
    im = np.asarray(Image.open(REF).convert("RGB")).astype(np.float32)
    ref_cols = np.array([(143, 155, 107), (5, 15, 25), (30, 140, 180), (105, 145, 155), (200, 30, 40), (40, 140, 200), (60, 230, 40)],
                        np.float32)
    lab = ((im[:, :, None, :] - ref_cols[None, None]) ** 2).sum(3).argmin(2)
    lab = np.where(lab == 5, 2, lab)
    unknown = lab >= 4  # red icons and green dots
    yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]
    for px, py in ICON_PIX:
        unknown |= (xx - px) ** 2 + (yy - py) ** 2 < 25 ** 2
    lab = np.where(unknown, -1, lab)
    for _ in range(60):  # fill the holes with the majority of the known neighbours
        if not (lab < 0).any():
            break
        votes = np.zeros(lab.shape + (4,), np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                sh = np.roll(np.roll(lab, dy, 0), dx, 1)
                for k in range(4):
                    votes[..., k] += sh == k
        lab = np.where((lab < 0) & (votes.max(2) > 0), votes.argmax(2), lab)
    lab = np.clip(lab, 0, 3).astype(np.uint8)
    lab = np.asarray(Image.fromarray(lab).filter(ImageFilter.ModeFilter(7)))  # removes small leftover specks
    sq = lab[SQ0:SQ1, SQ0:SQ1]
    n = 1600
    soft = []
    for k in range(4):
        m = Image.fromarray(((sq == k) * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC).filter(ImageFilter.GaussianBlur(5))
        soft.append(np.asarray(m, np.float32) / 255)
    _F["soft"] = np.stack(soft, 0)
    rng = np.random.default_rng(3)
    noise = (rng.random((48, 48)) * 255).astype(np.uint8)
    _F["noise"] = np.asarray(Image.fromarray(noise).resize((n, n), Image.BICUBIC), np.float32) / 255
    return _F


def sample(arr, X, Y):
    n = arr.shape[-1]
    u = np.clip(X / S * (n - 1), 0, n - 1.001)
    v = np.clip(Y / S * (n - 1), 0, n - 1.001)
    i, j = u.astype(np.int32), v.astype(np.int32)
    fu, fv = u - i, v - j
    return (arr[..., j, i] * (1 - fu) * (1 - fv) + arr[..., j, i + 1] * fu * (1 - fv)
            + arr[..., j + 1, i] * (1 - fu) * fv + arr[..., j + 1, i + 1] * fu * fv)


def classify(X, Y):
    lab = sample(fields()["soft"], X, Y).argmax(0)
    return np.where((X < 0) | (Y < 0) | (X > S) | (Y > S), 4, lab)


_STATE = {"tiles": {}}


def _tile(i, j):
    key = (i, j)
    if key in _STATE["tiles"]:
        return _STATE["tiles"][key]
    n = int(TILE * RES)
    pad = 20
    xs = i * TILE + (np.arange(-pad, n + pad) + .5) / RES
    ys = j * TILE + (np.arange(-pad, n + pad) + .5) / RES
    X, Y = np.meshgrid(xs, ys)
    lab = classify(X, Y)
    shade = sample(fields()["noise"], X, Y)[..., None]
    rgb = COLORS[lab] * (1 - .4 * shade) + COLORS_D[lab] * (.4 * shade)

    def near_other(r):
        m = np.zeros(lab.shape, bool)
        for a in np.linspace(0, 2 * math.pi, 12, endpoint=False):
            dy, dx = int(round(math.sin(a) * r)), int(round(math.cos(a) * r))
            m |= np.roll(np.roll(lab, dy, 0), dx, 1) != lab
        return m
    rim = near_other(16)
    rgb = np.where(((lab == 1) & rim)[..., None], rgb * .8 + np.array((70, 95, 105), np.float32) * .2, rgb)
    rgb = np.where(((lab == 2) & rim)[..., None], rgb * .75 + np.array((160, 220, 240), np.float32) * .25, rgb)
    rgb = np.where(((lab == 0) & rim)[..., None], rgb * .9, rgb)
    rgb = np.where(near_other(4)[..., None], INK_RGB, rgb)
    rgb = rgb[pad:-pad, pad:-pad]
    rgba = np.concatenate([np.clip(rgb, 0, 255).astype(np.uint8), np.full(rgb.shape[:2] + (1,), 255, np.uint8)], 2)
    img = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType)
    _STATE["tiles"][key] = img
    return img


# ---------------- structures and animated parts ----------------
def turret(c, x, y, team, t, s=1.0):
    """Turret icon in our style; crystal at (x, y - 185*s)."""
    body = 0xFF5FB8F5 if team == BLUE else 0xFFF06A72
    dark = 0xFF2C6E9E if team == BLUE else 0xFF9E2C35
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawOval(skia.Rect.MakeXYWH(-80, -26, 160, 56), fill(0x55000000))
    base = skia.Rect.MakeXYWH(-70, -32, 140, 50)
    c.drawRoundRect(base, 18, 18, fill(dark))
    c.drawRoundRect(base, 18, 18, stroke(7))
    tower = polyline([(-46, -14), (-34, -130), (34, -130), (46, -14)])
    tower.close()
    c.drawPath(tower, fill(body))
    c.drawPath(tower, stroke(7))
    c.drawLine(-22, -110, -28, -30, stroke(7, 0x88FFFFFF))
    crown = polyline([(-50, -126), (-50, -160), (-28, -160), (-28, -146), (-10, -146), (-10, -160), (10, -160), (10, -146), (28, -146),
                      (28, -160), (50, -160), (50, -126)])
    crown.close()
    c.drawPath(crown, fill(dark))
    c.drawPath(crown, stroke(7))
    glow = .6 + .4 * math.sin(t * 3)
    p = skia.Paint(AntiAlias=True, Color=(int(140 * glow) << 24) | (team & 0xFFFFFF), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20))
    c.drawCircle(0, -190, 42, p)
    gem = polyline([(0, -232), (22, -192), (0, -164), (-22, -192)])
    gem.close()
    c.drawPath(gem, fill(0xFFFFFFFF))
    c.drawPath(gem, stroke(6))
    c.drawPath(polyline([(0, -222), (12, -192), (0, -174)]), fill(team))
    c.restore()


def inhibitor(c, x, y, team):
    c.drawCircle(x, y, 95, fill(0xFF6E7A86))
    c.drawCircle(x, y, 95, stroke(8))
    c.drawCircle(x, y, 62, fill(team))
    c.drawCircle(x, y, 62, stroke(6))
    gem = polyline([(x, y - 34), (x + 24, y), (x, y + 34), (x - 24, y)])
    gem.close()
    c.drawPath(gem, fill(0xFFFFFFFF))
    c.drawPath(gem, stroke(5))


def nexus(c, x, y, team, t):
    c.drawOval(skia.Rect.MakeXYWH(x - 200, y - 70, 400, 170), fill(0xFF6E7A86))
    c.drawOval(skia.Rect.MakeXYWH(x - 200, y - 70, 400, 170), stroke(9))
    bob = math.sin(t * 2) * 10
    p = skia.Paint(AntiAlias=True, Color=(0x99 << 24) | (team & 0xFFFFFF), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40))
    c.drawCircle(x, y - 150 + bob, 120, p)
    gem = polyline([(x, y - 300 + bob), (x + 95, y - 140 + bob), (x, y - 20 + bob), (x - 95, y - 140 + bob)])
    gem.close()
    c.drawPath(gem, fill(team))
    c.drawPath(gem, stroke(8))
    c.drawLine(x - 25, y - 250 + bob, x - 50, y - 140 + bob, stroke(8, 0xAAFFFFFF))


def fountain(c, x, y, team, t):
    p = skia.Paint(AntiAlias=True, Color=(0x88 << 24) | (team & 0xFFFFFF), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 50))
    c.drawCircle(x, y, 200 + 20 * math.sin(t * 2), p)
    c.drawCircle(x, y, 150, fill(team))
    c.drawCircle(x, y, 150, stroke(9))


# brushes: placed beside lanes and in the river mouths (reference pixels), nudged onto walkway
BRUSH_PIX = [(400, 470), (330, 470), (452, 430), (482, 330), (482, 410), (300, 430), (240, 330), (230, 255), (78, 230), (78, 150),
             (150, 78), (230, 78), (110, 110), (430, 440), (310, 230), (420, 340)]


def _brushes():
    if "brushes" not in _STATE:
        out = []
        for px, py in BRUSH_PIX:
            X, Y = rf(px, py)
            best = None
            for r in range(0, 600, 40):
                for a in np.linspace(0, 2 * math.pi, 16, endpoint=False):
                    q = (X + math.cos(a) * r, Y + math.sin(a) * r)
                    if classify(np.array([q[0]]), np.array([q[1]]))[0] == 0:
                        best = q
                        break
                if best:
                    break
            if best:
                out.append((best[0], best[1], 130, 80))
        _STATE["brushes"] = out
    return _STATE["brushes"]


def draw(c, t, view):
    samp = skia.SamplingOptions(skia.FilterMode.kLinear)
    i0, i1 = math.floor(view.left() / TILE), math.floor(view.right() / TILE)
    j0, j1 = math.floor(view.top() / TILE), math.floor(view.bottom() / TILE)
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            c.drawImageRect(_tile(i, j), skia.Rect.MakeXYWH(i * TILE, j * TILE, TILE, TILE), samp)
    vo = view.makeOutset(300, 300)
    for team_name, team in (("rojo", RED), ("azul", BLUE)):
        fx, fy = rf(*_FOUNTAIN[team_name])
        if vo.contains(fx, fy):
            fountain(c, fx, fy, team, t)
        for p in _INHIB[team_name]:
            x, y = rf(*p)
            if vo.contains(x, y):
                inhibitor(c, x, y, team)
        nx, ny = rf(*_NEXUS[team_name])
        if vo.contains(nx, ny):
            nexus(c, nx, ny, team, t)
    for j, (x, y, rx, ry) in enumerate(_brushes()):
        if vo.contains(x, y):
            brush(c, x, y, rx, ry, t, j)
    for x, y, team in TURRETS:
        if vo.contains(x, y):
            turret(c, x, y, team, t)


_MINI = {}


def minimap(c, x, y, size, view, t):
    if size not in _MINI:
        xs = (np.arange(size) + .5) / size * S
        X, Y = np.meshgrid(xs, xs)
        rgb = COLORS[classify(X, Y)].astype(np.uint8)
        rgba = np.concatenate([rgb, np.full(rgb.shape[:2] + (1,), 255, np.uint8)], 2)
        surf = skia.Surface(size, size)
        m = surf.getCanvas()
        m.drawImage(skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType), 0, 0)
        sc = size / S
        for tx, ty, team in TURRETS:
            m.drawCircle(tx * sc, ty * sc, 4, fill(team))
            m.drawCircle(tx * sc, ty * sc, 4, stroke(1.5))
        _MINI[size] = surf.makeImageSnapshot()
    c.save()
    c.translate(x, y)
    r = skia.Rect.MakeWH(size, size)
    c.drawRoundRect(r.makeOutset(8, 8), 14, 14, fill(0xFF0E1418))
    c.drawImage(_MINI[size], 0, 0)
    c.drawRoundRect(r.makeOutset(8, 8), 14, 14, stroke(6, 0xFFE8C26A))
    sc = size / S
    v = skia.Rect.MakeLTRB(max(0, view.left() * sc), max(0, view.top() * sc), min(size, view.right() * sc), min(size, view.bottom() * sc))
    c.drawRect(v, stroke(4, 0xFFFFFFFF))
    c.drawCircle(v.centerX(), v.centerY(), 6 + 2 * math.sin(t * 6), fill(0xFFFFE27A))
    c.restore()
