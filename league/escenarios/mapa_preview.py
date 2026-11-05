"""Full-map preview of grieta.py with labels (lanes, turrets, brushes, pits). Output: grieta_mapa_completo.png"""
import sys
from pathlib import Path

import skia
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grieta as G  # noqa: E402
from mapa import fill, stroke  # noqa: E402

OUT_W = 2400
sc = OUT_W / G.W
OUT_H = int(G.H * sc)
pix = np.zeros((OUT_H, OUT_W, 4), dtype=np.uint8)
surf = skia.Surface(pix, colorType=skia.kRGBA_8888_ColorType)
c = surf.getCanvas()
c.scale(sc, sc)
view = skia.Rect.MakeWH(G.W, G.H)
G.draw(c, 1.0, view)
font = skia.Font(skia.Typeface("Segoe UI", skia.FontStyle.Bold()), 150)


def label(text, x, y, col=0xFFFFFFFF):
    w = font.measureText(text)
    c.drawString(text, x - w / 2, y, font, stroke(34, 0xE0101418))
    c.drawString(text, x - w / 2, y, font, fill(col))


label("BARÓN · HERALDO · LARVAS", G.BARON[0] + 250, G.BARON[1] - 470, 0xFFC9A6FF)
label("DRAGONES", G.DRAGON[0] - 150, G.DRAGON[1] + 560, 0xFFFFB27A)
label("RÍO", G.RIVER_X + 330, G.H / 2 - 520, 0xFF9AD6F0)
label("TOP", G.W / 2 - 1600, G.lane_y("superior", G.W / 2 - 1600) - 330)
label("MID", G.W / 2 - 1600, G.H / 2 - 330)
label("BOT", G.W / 2 - 1600, G.lane_y("inferior", G.W / 2 - 1600) + 450)
label("BASE AZUL", 700, G.H / 2 + 650, 0xFF8FD0FF)
label("BASE ROJA", G.W - 700, G.H / 2 + 650, 0xFFFF9AA2)
out = Path(__file__).resolve().parent / "grieta_mapa_completo.png"
Image.fromarray(pix[:, :, :3].copy()).save(out)
print(out)

# close-up like the in-video camera: the river crossing mid (must be one continuous straight line)
zw, zh = 1080, 1350
pz = np.zeros((zh, zw, 4), dtype=np.uint8)
sz = skia.Surface(pz, colorType=skia.kRGBA_8888_ColorType)
cz = sz.getCanvas()
z = .45
cz.translate(zw / 2, zh / 2)
cz.scale(z, z)
cz.translate(-G.RIVER_X, -G.H / 2 + 300)
G.draw(cz, 1.0, skia.Rect.MakeXYWH(G.RIVER_X - zw / z / 2, G.H / 2 - 300 - zh / z / 2, zw / z, zh / z))
Image.fromarray(pz[:, :, :3].copy()).save(out.with_name("grieta_zoom_rio.png"))
print(out.with_name("grieta_zoom_rio.png"))
