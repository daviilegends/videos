"""Adds one-word captions and yellow technical labels to the Blender frames, mixes voice and effects, and writes the MP4.

    render_env\\Scripts\\python.exe componer.py <carpeta_episodio> <segundos_hasta> <salida.mp4>
"""
import json
import subprocess
import sys
import unicodedata
from pathlib import Path, PureWindowsPath

import numpy as np
import skia
import soundfile as sf

EP, UNTIL, OUT = Path(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3])
FPS, W, H = 30, 1080, 1920
ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "sfx" / "library"
CATALOG = {PureWindowsPath(i["path"]).name: i["path"] for i in json.loads((ROOT / "sfx" / "catalog.json").read_text(encoding="utf-8"))}
story = json.loads((EP / "story.json").read_text(encoding="utf-8"))
tl = json.loads((EP / "timeline.json").read_text(encoding="utf-8"))
words = json.loads((EP / "words.json").read_text(encoding="utf-8"))
beats = json.loads((EP / "beats.json").read_text(encoding="utf-8"))
FACE = skia.Typeface.MakeFromFile("C:/Windows/Fonts/ariblk.ttf")
WORD_FONT = skia.Font(FACE, 92)
LABEL_FONT = skia.Font(FACE, 64)
YELLOW = 0xFFFFC61A


def plain(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn").strip("¿?¡!.,;:")


def labels():
    """Each technical name appears when the narrator first says it and stays until its sentence group ends."""
    out = []
    for scene, timed in zip(story["scenes"], tl["scenes"]):
        name = scene.get("etiqueta")
        if not name:
            continue
        first = plain(name.split()[0])
        said = [w for w in words if timed["start"] - .05 <= w["start"] < timed["end"] and plain(w["text"]) == first]
        out.append((said[0]["start"] if said else timed["start"], timed["end"], name))
    return out


LABELS = labels()


def outlined(c, text, x, y, font, color, width):
    c.drawString(text, x, y, font, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=0xFF101010,
                                               StrokeJoin=skia.Paint.kRound_Join))
    c.drawString(text, x, y, font, skia.Paint(AntiAlias=True, Color=color))


def overlay(c, t):
    for start, end, name in LABELS:
        if start <= t < end:
            k = min(1.0, (t - start) / .18)
            c.save()
            c.translate(W / 2, 330)
            c.rotate(-4)
            c.scale(.6 + .4 * k, .6 + .4 * k)
            outlined(c, name, -LABEL_FONT.measureText(name) / 2, 0, LABEL_FONT, YELLOW, 14)
            c.restore()
    word = next((w for w in words if w["start"] <= t < w["end"] + .08), None)
    if word:
        text = word["text"].strip(",.;:")
        size = 92
        font = WORD_FONT
        while font.measureText(text) > W - 120:
            size -= 6
            font = skia.Font(FACE, size)
        tech = any(s <= word["start"] < e and plain(text) in [plain(p) for p in n.split()] for s, e, n in LABELS)
        outlined(c, text, (W - font.measureText(text)) / 2, H * .62, font, YELLOW if tech else 0xFFFFFFFF, 16)


def video():
    frames = sorted((EP / "frames").glob("f_*.jpg"))
    total = min(len(frames), int(UNTIL * FPS))
    silent = EP / "video_mudo.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    surface = skia.Surface(pixels, colorType=skia.kRGBA_8888_ColorType)
    c = surface.getCanvas()
    for i in range(total):
        c.drawImage(skia.Image.open(str(frames[i])), 0, 0)
        overlay(c, i / FPS)
        ff.stdin.write(pixels.tobytes())
    ff.stdin.close()
    ff.wait()
    return silent


def load(name, sr, start=0.0, dur=None, af=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start)] + (["-t", str(dur)] if dur else []) + ["-i", str(LIBRARY / CATALOG[name])]
    cmd += (["-af", af] if af else []) + ["-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).reshape(-1, 2).copy()


def audio():
    voice, sr = sf.read(EP / "audio" / "narracion.wav", dtype="float32")
    n = min(len(voice), int(UNTIL * sr))
    voice = voice[:n]
    mix = np.zeros((n, 2), dtype=np.float32)

    def place(clip, at, gain):
        i = int(at * sr)
        if 0 <= i < n:
            end = min(n, i + len(clip))
            mix[i:end] += clip[:end - i] * gain

    def peak(x):
        return x / max(np.abs(x).max(), 1e-6)

    birds = load("birds_outside_002_wide.wav", sr)
    while len(birds) < n:
        birds = np.concatenate([birds, birds])
    mix += peak(birds[:n]) * .05
    pop = peak(load("Whooshes_059.wav", sr, dur=.6))
    for t in beats["estacas"]:
        place(pop, t, .12)
    a, b = beats["excavar"]
    dig = peak(load("Multiple Rock Hit Dirt_RBDII 07.wav", sr))
    t = a
    while t < b:
        place(dig, t, .25)
        t += .7
    place(peak(load("Crumbling Rock Slide_RBDII 07.wav", sr)), beats["derrumbe"], .45)
    place(peak(load("Hit Rock into Gravel_RBDII 06.wav", sr)), beats["grava"], .4)
    a, b = beats["compactar"]
    thump = peak(load("Plate_Impact_Hard_02.wav", sr, dur=.25))
    t = a
    while t < b:
        place(thump, t, .12)
        t += .2
    place(peak(load("FOUNTAIN Small, Splashes of Multiple Squirts on the Ground, Close.wav", sr, dur=beats["agua"][1] - beats["agua"][0] + 1)), beats["agua"][0], .25)
    place(peak(load("ICE Thin Cracked Crust on Lake 16.wav", sr, dur=1.5)), beats["grietas"], .5)
    gain = .92 / max(np.abs(voice).max(), 1e-6)
    out = (voice * gain)[:, None] + mix
    fade = np.minimum(1, np.arange(n) / (sr * .2)) * np.minimum(1, (n - np.arange(n)) / (sr * .4))
    out = np.tanh(out * fade[:, None] * 1.02) * .97
    path = EP / "audio" / "mezcla.wav"
    sf.write(path, out, sr)
    return path


silent, mixed = video(), audio()
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(mixed), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", "-shortest", str(OUT)], check=True)
print("ok", OUT)
