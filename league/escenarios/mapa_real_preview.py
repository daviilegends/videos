"""Sketch v2 preview: the whole real-shaped map with labels. Output: grieta_real_boceto3.png"""
import sys
from pathlib import Path

import numpy as np
import skia
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grieta_real as G  # noqa: E402
from mapa import fill, stroke  # noqa: E402

N = 2400
sc = N / G.S
pix = np.zeros((N, N, 4), dtype=np.uint8)
surf = skia.Surface(pix, colorType=skia.kRGBA_8888_ColorType)
c = surf.getCanvas()
c.scale(sc, sc)
G.draw(c, 1.0, skia.Rect.MakeWH(G.S, G.S))
font = skia.Font(skia.Typeface("Segoe UI", skia.FontStyle.Bold()), 230)
small = skia.Font(skia.Typeface("Segoe UI", skia.FontStyle.Bold()), 170)


def label(text, gx, gy, col=0xFFFFFFFF, f=font):
    x, y = G.P(gx, gy)
    w = f.measureText(text)
    c.drawString(text, x - w / 2, y, f, stroke(44, 0xE0101418))
    c.drawString(text, x - w / 2, y, f, fill(col))


label("BARÓN · HERALDO · LARVAS", 5200, 12850, 0xFFC9A6FF)
label("DRAGONES", 9300, 3200, 0xFFFFB27A)
label("TOP", 2600, 12600)
label("MID", 6200, 7200)
label("BOT", 12300, 2500)
label("BASE AZUL", 2300, 600, 0xFF8FD0FF)
label("BASE ROJA", 12500, 14300, 0xFFFF9AA2)
for name, (gx, gy) in G.CAMPS.items():
    label(name.split()[0].upper(), gx, gy - 80, 0xFFFFE9A8, small)
for gx, gy in G.SCUTTLE:
    label("CANGREJO", gx, gy - 80, 0xFF9AD6F0, small)
out = Path(__file__).resolve().parent / "grieta_real_boceto3.png"
Image.fromarray(pix[:, :, :3].copy()).save(out)
print(out)
