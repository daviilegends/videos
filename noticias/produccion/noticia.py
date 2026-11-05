"""News explainer in the Sticks style: flat 2D drawings with thick outlines, a hand-made map of the Persian Gulf,
stick figures and icons, one shot per sentence of the narration.
    render_env\\Scripts\\python.exe noticia.py <segundos_hasta> [--stills 1,5,9]"""
import json
import math
import random
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import numpy as np
import skia
import soundfile as sf

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 30
UNTIL = float(sys.argv[1])
TL = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
CUES = json.loads((ROOT / "cues.json").read_text(encoding="utf-8"))
LINES = [l for s in TL["scenes"] for l in s["lines"]]
INK, PAPER, SEA, SEA_DARK, LAND, LAND_DARK = 0xFF1E1A17, 0xFFF3E9D6, 0xFF6FA8C8, 0xFF4F87A8, 0xFFE3C99A, 0xFFC8A876
RED, BLUE, GREEN, WHITE, YELLOW = 0xFFD9443A, 0xFF2F4E8F, 0xFF2E8B4E, 0xFFFFFFFF, 0xFFF2C230
BOLD = skia.Typeface.MakeFromFile("C:/Windows/Fonts/ariblk.ttf")
SUBF = skia.Font(skia.Typeface.MakeFromFile("C:/Windows/Fonts/comicbd.ttf"), 36)


def font(size):
    return skia.Font(BOLD, size)


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def line(width, color=INK):
    return skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=color,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def pop(k):
    """Scale for an icon popping in with a small overshoot."""
    k = max(0.0, min(1.0, k))
    return 0 if k == 0 else 1 + math.sin(k * math.pi) * .25 * (1 - k) if k > .5 else ease(k * 2) * 1.15


def label(c, text, x, y, size=34, color=INK, bg=None):
    f = font(size)
    w = f.measureText(text)
    if bg is not None:
        r = skia.Rect.MakeXYWH(x - w / 2 - 16, y - size * .95, w + 32, size * 1.35)
        c.drawRoundRect(r, 10, 10, fill(bg))
        c.drawRoundRect(r, 10, 10, line(4))
    c.drawString(text, x - w / 2, y, f, fill(color))


def poly(points):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    p.close()
    return p


# ---------------------------------------------------------------- the map (map units 0..1000 x 0..600)
IRAN = [(0, 0), (1000, 0), (1000, 250), (880, 262), (800, 242), (730, 222), (650, 228), (560, 200), (450, 172), (350, 150),
        (250, 120), (150, 92), (0, 72)]
ARABIA = [(0, 600), (0, 300), (150, 332), (300, 392), (420, 432), (520, 442), (600, 402), (640, 334), (688, 284), (708, 262),
          (732, 300), (762, 382), (822, 440), (1000, 470), (1000, 600)]
QESHM = (640, 246)


def gulf_map(c, cx, cy, zoom, t):
    """Draws the map so that map point (cx, cy) sits at the centre of the screen."""
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(zoom * 1.28, zoom * 1.28)
    c.translate(-cx, -cy)
    c.drawRect(skia.Rect.MakeLTRB(-400, -400, 1400, 1000), fill(SEA))
    for i in range(14):  # gentle wave strokes on the water
        y = i * 45 + math.sin(t + i) * 4
        c.drawLine(-400, y, 1400, y + 30, line(2, 0x22FFFFFF))
    for shape in (IRAN, ARABIA):
        c.drawPath(poly(shape), fill(LAND))
        c.drawPath(poly(shape), line(5))
    c.save()
    c.translate(*QESHM)
    c.rotate(-14)
    c.drawOval(skia.Rect.MakeXYWH(-48, -9, 96, 18), fill(LAND_DARK))
    c.drawOval(skia.Rect.MakeXYWH(-48, -9, 96, 18), line(3))
    c.restore()
    c.restore()


def to_screen(mx, my, cx, cy, zoom):
    return W / 2 + (mx - cx) * zoom * 1.28, H / 2 + (my - cy) * zoom * 1.28


def explosion(c, x, y, k, size=120):
    if not 0 < k < 1:
        return
    r = size * ease(k * 1.4)
    for i, col in enumerate((0xFFF27A2A, YELLOW, 0xFFFFF4D0)):
        rr = r * (1 - i * .3)
        spikes = []
        for j in range(16):
            a = j * math.pi / 8 + k
            spikes.append((x + math.cos(a) * rr * (1 if j % 2 else .62), y + math.sin(a) * rr * (1 if j % 2 else .62)))
        c.drawPath(poly(spikes), fill((col & 0x00FFFFFF) | (int(255 * (1 - k) ** .5) << 24)))


def plane(c, x, y, s, angle, smoke=False, t=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    body = poly([(-40 * s, -6 * s), (36 * s, -6 * s), (48 * s, 0), (36 * s, 6 * s), (-40 * s, 6 * s)])
    c.drawPath(body, fill(0xFF9AA3AB))
    c.drawPath(body, line(3 * s))
    for wing in ((-6, -6, -18, -34, 8, -6), (-6, 6, -18, 34, 8, 6)):
        w = poly([(wing[0] * s, wing[1] * s), (wing[2] * s, wing[3] * s), (wing[4] * s, wing[5] * s)])
        c.drawPath(w, fill(0xFF7E8890))
        c.drawPath(w, line(3 * s))
    c.restore()
    if smoke:
        for i in range(6):
            k = (t * 1.5 + i / 6) % 1
            c.drawCircle(x - 30 * s * (1 + k * 3), y - 10 * s * k * 3, (6 + 14 * k) * s, fill(skia.ColorSetARGB(int(160 * (1 - k)), 70, 70, 70)))


def tanker(c, x, y, s):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    hull = poly([(-60, -10), (60, -10), (48, 12), (-56, 12)])
    c.drawPath(hull, fill(0xFF5B3A2A))
    c.drawPath(hull, line(3))
    for i in range(3):
        c.drawRect(skia.Rect.MakeXYWH(-46 + i * 26, -18, 20, 8), fill(0xFFB04A2A))
    c.drawRect(skia.Rect.MakeXYWH(32, -30, 20, 20), fill(WHITE))
    c.drawRect(skia.Rect.MakeXYWH(32, -30, 20, 20), line(3))
    c.restore()


def flag_us(c, x, y, w, h, wave):
    c.save()
    c.translate(x, y)
    for i in range(7):
        c.drawRect(skia.Rect.MakeXYWH(0, i * h / 7 + math.sin(wave + i) * 2, w, h / 7), fill(RED if i % 2 == 0 else WHITE))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, w * .42, h * .54), fill(BLUE))
    for i in range(12):
        c.drawCircle(w * .06 + (i % 4) * w * .1, h * .1 + (i // 4) * h * .16, 3, fill(WHITE))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, w, h), line(5))
    c.restore()


def flag_iran(c, x, y, w, h, wave):
    c.save()
    c.translate(x, y)
    for i, col in enumerate((GREEN, WHITE, RED)):
        c.drawRect(skia.Rect.MakeXYWH(0, i * h / 3 + math.sin(wave + i) * 2, w, h / 3), fill(col))
    c.drawCircle(w / 2, h / 2, h * .1, line(4, RED))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, w, h), line(5))
    c.restore()


def stick(c, x, y, s, t, talk=False, arm=0.0, tie=None, suit=None, hair=None):
    """Sticks-style figure: round head, dot eyes, thick limbs; optional suit, tie and hair for identity."""
    breath = math.sin(t * 2) * 2 * s
    hy = y - 170 * s + breath
    for side in (-1, 1):
        c.drawLine(x, y - 70 * s, x + side * 22 * s, y, line(9 * s))
    if suit:
        torso = poly([(x - 30 * s, y - 135 * s + breath), (x + 30 * s, y - 135 * s + breath), (x + 34 * s, y - 62 * s), (x - 34 * s, y - 62 * s)])
        c.drawPath(torso, fill(suit))
        c.drawPath(torso, line(5 * s))
    else:
        c.drawLine(x, y - 130 * s + breath, x, y - 70 * s, line(9 * s))
    if tie:
        c.drawPath(poly([(x - 6 * s, y - 132 * s + breath), (x + 6 * s, y - 132 * s + breath), (x + 8 * s, y - 85 * s), (x, y - 76 * s), (x - 8 * s, y - 85 * s)]), fill(tie))
    c.drawLine(x - 26 * s, y - 128 * s + breath, x - 40 * s, y - 80 * s, line(8 * s))
    ax, ay = x + 26 * s + math.sin(arm) * 40 * s, y - 128 * s + breath - math.sin(arm) * 30 * s + 48 * s * math.cos(arm)
    c.drawLine(x + 26 * s, y - 128 * s + breath, ax, ay, line(8 * s))
    c.drawCircle(x, hy, 40 * s, fill(0xFFF5F0E6))
    c.drawCircle(x, hy, 40 * s, line(6 * s))
    if hair:
        c.drawPath(poly([(x - 42 * s, hy - 8 * s), (x - 30 * s, hy - 40 * s), (x + 10 * s, hy - 46 * s), (x + 46 * s, hy - 26 * s), (x + 30 * s, hy - 18 * s), (x - 20 * s, hy - 22 * s)]), fill(hair))
    for side in (-1, 1):
        c.drawCircle(x + side * 13 * s, hy, 4.5 * s, fill(INK))
    if talk and int(t * 9) % 2:
        c.drawOval(skia.Rect.MakeXYWH(x - 7 * s, hy + 14 * s, 14 * s, 10 * s), fill(INK))
    else:
        c.drawLine(x - 9 * s, hy + 18 * s, x + 9 * s, hy + 18 * s, line(4 * s))


def paper_bg(c):
    c.drawRect(skia.Rect.MakeWH(W, H), fill(PAPER))
    r = random.Random(1)
    for _ in range(90):
        c.drawCircle(r.uniform(0, W), r.uniform(0, H), r.uniform(1, 3), fill(0x18000000))


# ---------------------------------------------------------------- shots, one per sentence
def s_hook(c, t, k):
    paper_bg(c)
    sh = 8 * math.exp(-max(0, k - .45) * 10) if k > .45 else 0
    c.translate(math.sin(t * 60) * sh, 0)
    flag_us(c, 120 - 80 * (1 - ease(k * 3)), 220, 360, 220, t * 3)
    flag_iran(c, 800 + 80 * (1 - ease(k * 3)), 220, 360, 220, t * 3)
    explosion(c, 640, 330, (k - .45) / .5, 170)
    label(c, "EE.UU. vs IRÁN", 640, 610, 62)


def s_question(c, t, k):
    paper_bg(c)
    stick(c, 640, 640, 1.6, t, talk=True, arm=1.2 + math.sin(t * 3) * .2)
    for i, (x, y) in enumerate(((330, 260), (950, 240))):
        s = pop((k - .1 - i * .25) * 3)
        if s:
            c.save()
            c.translate(x, y)
            c.scale(s, s)
            label(c, "?", 0, 60, 170, RED)
            c.restore()


def s_strike(c, t, k):
    z = 1.0 + 1.6 * ease(k * 1.2)
    cx, cy = 500 + 140 * ease(k), 300 - 54 * ease(k)
    gulf_map(c, cx, cy, z, t)
    qx, qy = to_screen(*QESHM, cx, cy, z)
    px = -100 + 1500 * ease((k - .3) / .45)
    plane(c, px, 120 + 40 * math.sin(k * 3), 1.4, 12)
    mk = (k - .55) / .2
    if 0 < mk < 1:
        c.drawLine(qx - 300 * (1 - mk), qy - 300 * (1 - mk), qx - 300 * (1 - mk) + 30, qy - 300 * (1 - mk) + 30, line(10, RED))
    explosion(c, qx, qy, (k - .74) / .26, 110)
    label(c, "QESHM", qx, qy + 70, 34, INK, WHITE)
    label(c, "IRÁN", W / 2, 90, 46)
    label(c, "2 NOV", 160, 90, 40, WHITE, RED)


def s_hormuz(c, t, k):
    cx, cy, z = 690, 290, 2.3
    gulf_map(c, cx, cy, z, t)
    for i in range(4):  # tankers in single file through the gap between Iran and the tip of the peninsula
        u = (k * .7 + i * .25) % 1
        mx = 560 + u * 300
        my = 300 - 50 * math.sin(min(1, max(0, (mx - 560) / 300)) * math.pi) + (8 if mx > 700 else 0)
        sx, sy = to_screen(mx, my, cx, cy, z)
        tanker(c, sx, sy, .75)
    label(c, "ESTRECHO DE ORMUZ", W / 2, 80, 44, INK, WHITE)
    s = pop((k - .45) * 3)
    if s:
        c.save()
        c.translate(1060, 430)
        c.scale(s, s)
        c.drawRoundRect(skia.Rect.MakeXYWH(-40, -60, 80, 110), 14, 14, fill(0xFF333333))
        c.drawRoundRect(skia.Rect.MakeXYWH(-40, -60, 80, 110), 14, 14, line(5))
        label(c, "1/5", 0, 10, 40, WHITE)
        c.restore()
        label(c, "DEL PETRÓLEO DEL MUNDO", 980, 560, 30, INK, WHITE)


def s_island(c, t, k):
    c.drawRect(skia.Rect.MakeWH(W, 300), fill(0xFFB8DCEB))
    c.drawRect(skia.Rect.MakeXYWH(0, 300, W, 420), fill(LAND))
    c.drawRect(skia.Rect.MakeXYWH(0, 300, 300, 420), fill(SEA))
    c.drawLine(0, 300, W, 300, line(6))
    items = [(.08, "MISILES BAJO TIERRA", 470), (.38, "BASE NAVAL", 160), (.68, "DESALINIZADORA", 980)]
    for start, name, x in items:
        s = pop((k - start) * 3)
        if not s:
            continue
        c.save()
        c.translate(x, 470 if x != 160 else 280)
        c.scale(s, s)
        if name.startswith("MISILES"):
            c.drawRect(skia.Rect.MakeXYWH(-150, -40, 300, 150), fill(0xFF8F7550))
            c.drawRect(skia.Rect.MakeXYWH(-150, -40, 300, 150), line(5))
            for i in range(3):
                m = poly([(-90 + i * 90, 90), (-90 + i * 90, 0), (-78 + i * 90, -30), (-66 + i * 90, 0), (-66 + i * 90, 90)])
                c.drawPath(m, fill(WHITE))
                c.drawPath(m, line(4))
            label(c, name, 0, 160, 28, INK, WHITE)
        elif name == "BASE NAVAL":
            hull = poly([(-90, 0), (90, 0), (70, 30), (-80, 30)])
            c.drawPath(hull, fill(0xFF6B7883))
            c.drawPath(hull, line(5))
            c.drawRect(skia.Rect.MakeXYWH(-20, -40, 50, 40), fill(0xFF8A96A0))
            c.drawRect(skia.Rect.MakeXYWH(-20, -40, 50, 40), line(4))
            label(c, name, 0, 90, 28, INK, WHITE)
        else:
            c.drawRect(skia.Rect.MakeXYWH(-90, -60, 180, 120), fill(0xFFDDE6EC))
            c.drawRect(skia.Rect.MakeXYWH(-90, -60, 180, 120), line(5))
            drop = skia.Path()
            drop.moveTo(0, -40)
            drop.cubicTo(40, 0, 30, 40, 0, 40)
            drop.cubicTo(-30, 40, -40, 0, 0, -40)
            c.drawPath(drop, fill(0xFF3E9FD9))
            c.drawPath(drop, line(4))
            label(c, name, 0, 110, 28, INK, WHITE)
        c.restore()


def s_official(c, t, k):
    paper_bg(c)
    flag_us(c, 900, 150, 240, 150, t * 3)
    c.drawRect(skia.Rect.MakeXYWH(470, 470, 220, 250), fill(0xFF6B4A33))
    c.drawRect(skia.Rect.MakeXYWH(470, 470, 220, 250), line(6))
    stick(c, 580, 560, 1.5, t, talk=True, arm=1.4 + math.sin(t * 2.5) * .25, suit=0xFF3A3F4A, tie=BLUE)
    s = pop((k - .15) * 3)
    if s and k < .6:
        c.save()
        c.translate(300, 200)
        c.scale(s, s)
        c.drawPath(poly([(-70, -80), (70, -80), (70, 10), (0, 80), (-70, 10)]), fill(0xFF4A90C8))
        c.drawPath(poly([(-70, -80), (70, -80), (70, 10), (0, 80), (-70, 10)]), line(6))
        c.restore()
        label(c, "DEFENSIVO", 300, 340, 38, INK, WHITE)
    if k >= .6:
        plane(c, 300, 230, 1.6, -8, smoke=True, t=t)
        label(c, "AERONAVE DE EE.UU. ALCANZADA", 330, 360, 26, INK, WHITE)


def s_centcom(c, t, k):
    paper_bg(c)
    doc = skia.Rect.MakeXYWH(440, 120, 400, 480)
    c.drawRect(doc, fill(WHITE))
    c.drawRect(doc, line(6))
    for i in range(7):
        c.drawLine(480, 200 + i * 45, 800 - (i % 3) * 60, 200 + i * 45, line(6, 0xFFB8B0A4))
    label(c, "COMANDO CENTRAL", 640, 170, 30)
    s = pop((k - .2) * 3)
    if s:
        c.save()
        c.translate(640, 480)
        c.rotate(-12)
        c.scale(s, s)
        label(c, "SIN ANUNCIO OFICIAL", 0, 0, 34, RED, 0x00000000)
        c.drawRoundRect(skia.Rect.MakeXYWH(-230, -42, 460, 60), 8, 8, line(6, RED))
        c.restore()


SHOTS = [("Estados Unidos volvió", s_hook), ("¿Qué está pasando", s_question), ("Según The Wall", s_strike),
         ("Qeshm está justo", s_hormuz), ("En la isla", s_island), ("Funcionarios", s_official), ("El Comando Central", s_centcom)]


def subtitle(c, t):
    for cue in CUES:
        if cue["start"] <= t < cue["end"] + .1:
            text = cue["text"].rstrip(".,;")
            x = (W - SUBF.measureText(text)) / 2
            c.drawString(text, x, H - 30, SUBF, line(8))
            c.drawString(text, x, H - 30, SUBF, fill(WHITE))
            return


def frame(c, t):
    starts = []
    for prefix, fn in SHOTS:
        ln = next((l for l in LINES if l["text"].startswith(prefix)), None)
        if ln:
            starts.append((ln["start"], fn))
    starts.sort()
    i = max([j for j, (s, _) in enumerate(starts) if t >= s] or [0])
    start = 0 if i == 0 else starts[i][0]
    stop = starts[i + 1][0] if i + 1 < len(starts) else UNTIL
    c.clear(PAPER)
    c.save()
    starts[i][1](c, t, (t - start) / max(.1, stop - start))
    c.restore()
    vig = skia.Paint()
    vig.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * .75, [0x00000000, 0x55000000], [.6, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), vig)
    fade = max(1 - t / .4, (t - (UNTIL - .6)) / .6)
    if fade > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill(skia.ColorSetARGB(int(255 * min(1, fade)), 0, 0, 0)))
    subtitle(c, t)


def audio(path):
    voice, sr = sf.read(ROOT / "audio" / "narracion.wav", dtype="float32")
    voice = voice if voice.ndim == 1 else voice.mean(1)
    n = int(UNTIL * sr)
    mix = np.zeros(n, dtype=np.float32)
    mix[:min(n, len(voice))] += voice[:n] / max(np.abs(voice).max(), 1e-6) * .9
    catalog = {PureWindowsPath(i["path"]).name: i["path"] for i in json.loads(Path(r"C:\videos-youtube\sfx\catalog.json").read_text(encoding="utf-8"))}

    def place(name, at, gain, dur=None):
        cmd = ["ffmpeg", "-v", "error"] + (["-t", str(dur)] if dur else []) + ["-i", str(Path(r"C:\videos-youtube\sfx\library") / catalog[name]),
               "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
        x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)
        x = x / max(np.abs(x).max(), 1e-6)
        i = int(at * sr)
        if 0 <= i < n:
            mix[i:min(n, i + len(x))] += x[:min(n, i + len(x)) - i] * gain

    def when(prefix, frac=0.0):
        ln = next(l for l in LINES if l["text"].startswith(prefix))
        nxt = LINES[LINES.index(ln) + 1]["start"] if LINES.index(ln) + 1 < len(LINES) else ln["end"]
        return ln["start"] + (nxt - ln["start"]) * frac

    place("Bluezone-BC0214-explosion-whooshe-003.wav", when("Estados Unidos volvió", .45), .35)
    place("Whooshes_059.wav", when("Según The Wall", .3), .3, 1)
    place("Bluezone-BC0226-hit-impact-004.wav", when("Según The Wall", .74), .5)
    edge = np.minimum(1, np.arange(n) / (sr * .3)) * np.minimum(1, (n - np.arange(n)) / (sr * .6))
    sf.write(path, np.stack([mix * edge] * 2, 1), sr)


def main():
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    surface = skia.Surface(pixels, colorType=skia.kRGBA_8888_ColorType)
    c = surface.getCanvas()
    if "--stills" in sys.argv:
        from PIL import Image
        for v in sys.argv[sys.argv.index("--stills") + 1].split(","):
            frame(c, float(v))
            Image.fromarray(pixels[:, :, :3].copy()).save(ROOT / f"cuadro_{float(v):05.1f}.png")
        return
    silent, mixed, final = ROOT / "noticia_mudo.mp4", ROOT / "noticia_audio.wav", ROOT / "noticia_prueba.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for i in range(int(UNTIL * FPS)):
        frame(c, i / FPS)
        ff.stdin.write(pixels.tobytes())
    ff.stdin.close()
    ff.wait()
    audio(mixed)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(mixed), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", str(final)], check=True)
    print("ok", final)


if __name__ == "__main__":
    main()
