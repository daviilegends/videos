"""Renders the middle of every sentence (and thirds of the long ones) into contact sheets for review."""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
times = []
for s in tl["scenes"]:
    for l in s["lines"]:
        d = l["end"] - l["start"]
        times += [l["start"] + d * f for f in ((.2, .8) if d > 3.5 else (.55,))]
out = ROOT / "stills"
out.mkdir(exist_ok=True)
for f in out.glob("*.png"):
    f.unlink()
subprocess.run([sys.executable, str(ROOT / "render.py"), "--stills", ",".join(f"{t:.2f}" for t in times)], check=True)
files = sorted(out.glob("*.png"))
per, cols = 24, 4
tw, th = 400, 225
for page in range(0, len(files), per):
    chunk = files[page:page + per]
    sheet = Image.new("RGB", (cols * tw, ((len(chunk) + cols - 1) // cols) * th))
    for i, f in enumerate(chunk):
        im = Image.open(f).convert("RGB").resize((tw, th))
        ImageDraw.Draw(im).text((4, 4), f.stem, fill=(255, 255, 0))
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out / f"sheet_{page // per}.jpg", quality=82)
print(len(files), "cuadros")
