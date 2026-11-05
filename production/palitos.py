"""Sticks engine: the stick-figure rig, camera, light, subtitles, sound map and output, shared by every episode.
An episode script does `from palitos import *`, defines LAYOUT and shots(t), and calls terminar(shots, LAYOUT).
Usage: python escena_<tema>.py <episode folder> [--stills 3,10,20] [--full] [--audio] [--short]
  --stills writes review frames to <ep>/stills, --full renders the silent video, --audio mixes narration and
  sonido.json, --short muxes the horizontal video and builds the vertical Short with the yellow title."""
import json
import math
import random
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import numpy as np
import skia

ROOT = Path(__file__).resolve().parent
EP = Path(sys.argv[1]).resolve()
W, H, FPS = 1280, 720, 30
BG_W, BG_H = 1536, 864
BASE = W / BG_W
TL = json.loads((EP / "timeline.json").read_text(encoding="utf-8"))
STORY = json.loads((EP / "story.json").read_text(encoding="utf-8"))
LINES = [x for s in TL["scenes"] for x in s["lines"]]
CUES = json.loads((EP / "cues.json").read_text(encoding="utf-8")) if (EP / "cues.json").exists() else []
BGS = {p.stem: skia.Image.open(str(p)) for p in (EP / "bg").glob("*.png")}
SAMPLING = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
INK = 0xFF0B0B0D
SKIN, SHADE = 0xFFF5F3EC, 0xFFD5D6D4
HAIR, JACKET, JACKET_DARK, SHIRT = 0xFF4A2C20, 0xFF9A5A3C, 0xFF7A4530, 0xFFD8D4C6
FONT_FILE = "C:/Windows/Fonts/comicbd.ttf"
SUB_FONT = skia.Font(skia.Typeface.MakeFromFile(FONT_FILE), 38)
CAPTION_FONT = skia.Font(skia.Typeface.MakeFromFile(FONT_FILE), 64)
BEATS = {}


def font(size, file=FONT_FILE):
    return skia.Font(skia.Typeface.MakeFromFile(file), size)


def beat(name, t):
    """Stores the time of a visible action so sonido.json can put a sound on it."""
    BEATS[name] = [round(float(x), 3) for x in t] if isinstance(t, (list, tuple)) else round(float(t), 3)
    return t


def linea(t):
    """Index of the sentence being spoken at t, time since it started (lt) and its progress 0..1 (k)."""
    i = max((j for j, l in enumerate(LINES) if t >= l["start"]), default=0)
    start = LINES[i]["start"] if i else 0.0
    stop = LINES[i + 1]["start"] if i + 1 < len(LINES) else TL["duration"]
    return i, t - start, min(1.0, (t - start) / max(.1, stop - start))


def cue_start(fragment, after=0.0):
    """Start time of the first subtitle cue at or after `after` that contains the fragment (accent-sensitive)."""
    return next(c["start"] for c in CUES if fragment in c["text"] and c["start"] >= after)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def stroke(width, color=INK):
    return skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=color,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)


def fill(color):
    return skia.Paint(AntiAlias=True, Color=color)


def poly(points, close=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def limb(c, a, b, width=9):
    c.drawLine(*a, *b, stroke(width))


def arm(c, shoulder, angle, bend, side, holding=False):
    """Two-segment arm; angle is measured from straight down, positive toward the character's front."""
    upper, lower = 48, 46
    ex = shoulder[0] + math.sin(angle) * upper * side
    ey = shoulder[1] + math.cos(angle) * upper
    fa = angle + bend
    hx = ex + math.sin(fa) * lower * side
    hy = ey + math.cos(fa) * lower
    limb(c, shoulder, (ex, ey))
    limb(c, (ex, ey), (hx, hy))
    c.drawCircle(hx, hy, 8, fill(INK))
    if holding:
        c.save()
        c.translate(hx, hy)
        c.rotate(90 - math.degrees(fa) if side > 0 else math.degrees(fa) - 90)
        c.drawRoundRect(skia.Rect.MakeXYWH(-6, -7, 34, 14), 4, 4, fill(0xFF3A3F44))
        c.drawRoundRect(skia.Rect.MakeXYWH(-6, -7, 34, 14), 4, 4, stroke(3))
        c.drawRect(skia.Rect.MakeXYWH(28, -10, 8, 20), fill(0xFFF3E7A8))
        c.drawRect(skia.Rect.MakeXYWH(28, -10, 8, 20), stroke(3))
        c.restore()
    return hx, hy


def head(c, cx, cy, s):
    """Layered head: s holds look, blink, mouth, brows, tilt and facing (-1..1 profile bias)."""
    r = 66
    c.save()
    c.translate(cx, cy)
    c.rotate(s.get("tilt", 0))
    face = s.get("face", 0)
    c.drawCircle(0, 0, r, fill(SKIN))
    clip = skia.Path()
    clip.addCircle(0, 0, r)
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    c.drawCircle(-face * 18 - 16, -8, r + 3, fill(SHADE))
    c.drawCircle(-face * 18 - 8, -6, r - 4, fill(SKIN))
    c.restore()
    # hair: jagged fringe, drawn over the skull
    spikes = [(-r - 2, -14)]
    for i in range(7):
        x = lerp(-r + 6, r - 6, i / 6) + face * 6
        spikes += [(x - 8, -36 - (i % 2) * 7), (x + 4, -20 + (i % 3) * 3)]
    spikes += [(r + 2, -14), (r - 8, -46), (40, -70), (6, -78), (-34, -72), (-r + 6, -48)]
    c.drawPath(poly(spikes), fill(s.get("hair", HAIR)))
    c.drawPath(poly(spikes), stroke(6))
    if s.get("helmet"):
        c.drawArc(skia.Rect.MakeXYWH(-r - 8, -r - 22, 2 * r + 16, 2 * r + 10), 180, 180, True, fill(0xFFC9A23A))
        c.drawArc(skia.Rect.MakeXYWH(-r - 8, -r - 22, 2 * r + 16, 2 * r + 10), 180, 180, True, stroke(6))
        c.drawLine(-r - 18, -28, r + 18, -28, stroke(10))
    if s.get("police_cap"):  # navy peaked cap with a small gold badge
        navy = s.get("cap_color", 0xFF1E2A44)
        crown = poly([(-r + 2, -r + 18), (-r - 6, -r - 20), (0, -r - 30), (r + 6, -r - 20), (r - 2, -r + 18)])
        c.drawPath(crown, fill(navy))
        c.drawPath(crown, stroke(6))
        c.drawLine(-r + 2, -r + 16, r - 2, -r + 16, stroke(10, 0xFF0E1424))
        visor = skia.Rect.MakeXYWH(-r + 4 + face * 10, -r + 12, 2 * r - 8, 18)
        c.drawOval(visor, fill(0xFF0E1424))
        c.drawCircle(face * 8, -r - 6, 9, fill(0xFFE2B84A))
        c.drawCircle(face * 8, -r - 6, 9, stroke(4))
    if s.get("sombrero"):  # wide-brimmed straw hat
        straw, band = 0xFFD9B66A, 0xFF7A3B22
        c.drawOval(skia.Rect.MakeXYWH(-r - 48, -r + 2, 2 * r + 96, 34), fill(straw))
        c.drawOval(skia.Rect.MakeXYWH(-r - 48, -r + 2, 2 * r + 96, 34), stroke(6))
        crown = poly([(-46, -r + 14), (-38, -r - 46), (0, -r - 56), (38, -r - 46), (46, -r + 14)])
        c.drawPath(crown, fill(straw))
        c.drawPath(crown, stroke(6))
        c.drawLine(-44, -r + 2, 44, -r + 2, stroke(9, band))
    if s.get("back"):  # seen from behind: only hair
        c.drawCircle(0, -6, r + 1, fill(s.get("hair", HAIR)))
        c.drawCircle(0, -6, r + 1, stroke(6))
        c.restore()
        return
    # face
    fx = face * 22
    lx, ly = s.get("look", (0, 0))
    wide = s.get("eye", 1.0)
    blink = s.get("blink", 0.0)
    for ex in (-22 + fx - abs(face) * 2, 22 + fx + abs(face) * 2):
        eye = skia.Rect.MakeXYWH(ex + lx * 7 - 6.5 * wide, 2 + ly * 5 - 8 * wide * (1 - blink), 13 * wide, max(2.5, 16 * wide * (1 - blink)))
        c.drawOval(eye, fill(INK))
    brow = s.get("brow", 0)  # negative worried, positive angry
    c.drawLine(-34 + fx, -14 - brow * 6, -14 + fx, -14 + brow * 6, stroke(4.5))
    c.drawLine(14 + fx, -14 + brow * 6, 34 + fx, -14 - brow * 6, stroke(4.5))
    mouth = s.get("mouth", "flat")
    mx, my = fx + lx * 3, 34
    if mouth == "flat":
        c.drawLine(mx - 13, my, mx + 13, my, stroke(4.5))
    elif mouth == "worry":
        p = skia.Path()
        p.moveTo(mx - 15, my + 5)
        p.quadTo(mx, my - 7, mx + 15, my + 5)
        c.drawPath(p, stroke(4.5))
    elif mouth == "smile":
        p = skia.Path()
        p.moveTo(mx - 16, my - 3)
        p.quadTo(mx, my + 12, mx + 16, my - 3)
        c.drawPath(p, stroke(4.5))
    else:
        size = {"o": 12, "talk1": 6, "talk2": 13, "gasp": 16}.get(mouth, 8)
        rect = skia.Rect.MakeXYWH(mx - size * .75, my - size * .7, size * 1.5, size * 1.4)
        c.drawOval(rect, fill(0xFF3A1416))
        c.drawOval(rect, stroke(4))
    if s.get("sweat"):
        drop = (s["t"] * 26) % 34
        c.drawCircle(r * .82, -r * .1 + drop, 6, fill(0xFF9FD3E8))
        c.drawCircle(r * .82, -r * .1 + drop, 6, stroke(2.5))
    c.restore()


def character(c, s):
    """Character rig. Origin between the feet; s['walk'] is a phase in radians, None when standing."""
    c.save()
    c.translate(s["x"], s["y"])
    c.scale(s["scale"] * s.get("dir", 1), s["scale"])
    c.rotate(s.get("lean", 0))
    walk = s.get("walk")
    breath = math.sin(s["t"] * s.get("breath_rate", 1.7)) * s.get("breath_amp", 2)
    bob = abs(math.sin(walk)) * 7 if walk is not None else 0
    sit = s.get("sit")
    hip = (0, (-46 if sit else -112 - bob) + breath * .3)
    shoulder_y = (-126 if sit else -192 - bob) + breath
    jacket, jacket_dark = s.get("jacket", (JACKET, JACKET_DARK))
    swing = math.sin(walk) * .55 if walk is not None else 0
    for side, sw in (() if sit else ((-1, swing), (1, -swing))):
        knee = (hip[0] + side * 10 + math.sin(sw) * 54, hip[1] + math.cos(sw) * 54)
        lift = max(0, math.sin(sw * 4)) * 8 if walk is not None else 0
        foot = (knee[0] + math.sin(sw * .4) * 54, -4 - lift)
        limb(c, (hip[0] + side * 10, hip[1]), knee)
        limb(c, knee, foot)
        c.drawLine(foot[0] - 2, foot[1], foot[0] + 18, foot[1], stroke(11))
    left, right = (-24, shoulder_y + 8), (24, shoulder_y + 8)
    arm_back = s.get("arm_l", (-.1, .1))
    arm(c, left, arm_back[0] + (swing if walk is not None else 0), arm_back[1], -1)
    # gown
    gown = skia.Path()
    gown.moveTo(-26, shoulder_y)
    gown.quadTo(0, shoulder_y - 9, 26, shoulder_y)
    hem = 4 if sit else 38
    gown.lineTo(46, hip[1] + hem)
    gown.quadTo(0, hip[1] + hem + 11, -46, hip[1] + hem)
    gown.close()
    c.drawPath(gown, fill(jacket))
    c.save()
    c.clipPath(gown, doAntiAlias=True)
    c.drawRect(skia.Rect.MakeLTRB(-60, shoulder_y, -10, hip[1] + 60), fill(jacket_dark))
    if not s.get("back"):
        c.drawLine(0, shoulder_y + 12, 0, hip[1] + 60, stroke(3))
    c.restore()
    c.drawPath(gown, stroke(6))
    if not s.get("back"):
        c.drawPath(poly([(-13, shoulder_y - 4), (0, shoulder_y + 15), (13, shoulder_y - 4)]), fill(SHIRT))
        c.drawPath(poly([(-13, shoulder_y - 4), (0, shoulder_y + 15), (13, shoulder_y - 4)]), stroke(4.5))
    if sit:  # knees drawn up in front of the body
        for side in (-1, 1):
            knee, foot = (side * 30, hip[1] - 66), (side * 50, -4)
            for width, color in ((34, INK), (24, 0xFF2F3A44)):
                c.drawLine(side * 16, hip[1] + 6, *knee, stroke(width, color))
                c.drawLine(*knee, *foot, stroke(width, color))
            c.drawLine(foot[0] - 4 * side, foot[1], foot[0] + 22 * side, foot[1], stroke(16))
    arm_front = s.get("arm_r", (.1, .1))
    s["hand"] = arm(c, right, arm_front[0] - (swing * .25 if walk is not None else 0), arm_front[1], 1, holding=s.get("flashlight", False))
    if s.get("phone"):
        hx, hy = s["hand"]
        c.drawRoundRect(skia.Rect.MakeXYWH(hx - 12, hy - 40, 26, 46), 5, 5, fill(0xFF1C2226))
        c.drawRoundRect(skia.Rect.MakeXYWH(hx - 12, hy - 40, 26, 46), 5, 5, stroke(4))
        c.drawRect(skia.Rect.MakeXYWH(hx - 7, hy - 34, 16, 32), fill(0xFFB9E4EC))
    head(c, 0 + s.get("head_dx", 0), shoulder_y - 56, s)
    c.restore()


class Cam:
    def __init__(self, a, b, t):
        k = ease(t)
        self.x, self.y, self.z = lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)

    def apply(self, c, shake=(0, 0)):
        scale = BASE * self.z
        half_w, half_h = W / 2 / scale, H / 2 / scale
        self.x = min(max(self.x, half_w), BG_W - half_w)
        self.y = min(max(self.y, half_h), BG_H - half_h)
        c.translate(W / 2 + shake[0], H / 2 + shake[1])
        c.scale(scale, scale)
        c.translate(-self.x, -self.y)


def blink(t, seed=0.0):
    phase = (t + seed) % 3.7
    return 1.0 if phase < .09 else 0.0


def talk(t):
    return ["talk1", "talk2", "o", "talk2", "talk1"][int(t * 9) % 5]


def beam(c, x, y, angle, length=560, spread=13, alpha=72):
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    paint = skia.Paint(AntiAlias=True, BlendMode=skia.BlendMode.kScreen, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    paint.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(length, 0)],
                                                   [skia.ColorSetARGB(alpha, 245, 230, 170), skia.ColorSetARGB(0, 245, 230, 170)]))
    half = math.tan(math.radians(spread)) * length
    c.drawPath(poly([(0, -6), (length, -half), (length, half), (0, 6)]), paint)
    c.restore()


def steam(c, x, y, t):
    for i in range(3):
        p = skia.Path()
        ox = x + (i - 1) * 16
        p.moveTo(ox, y)
        for j in range(1, 5):
            p.quadTo(ox + math.sin(t * 2 + i + j) * 15, y - j * 21 + 10, ox + math.sin(t * 2 + i + j + 1) * 7, y - j * 21)
        paint = stroke(5, skia.ColorSetARGB(int(95 + 40 * math.sin(t + i)), 225, 230, 225))
        c.drawPath(p, paint)


# ---------------------------------------------------------------- frame
DUST = [(random.Random(i).uniform(0, W), random.Random(i + 900).uniform(0, H), random.Random(i + 77).uniform(.4, 1.4)) for i in range(55)]


def frame(canvas, t, shots, layout):
    """shots(t) returns a dict: bg, cam, and optionally shake, dark, flicker, over, chars, front, caption, fade."""
    s = dict(shake=(0, 0), dark=0.0, flicker=.15, over=[], front=[])
    s.update(shots(t))
    look = layout.get(s["bg"], {})
    canvas.clear(skia.ColorBLACK)
    canvas.save()
    s["cam"].apply(canvas, s["shake"])
    bg_paint = skia.Paint(ColorFilter=skia.ColorFilters.Blend(look.get("tint", 0xFFFFFFFF), skia.BlendMode.kModulate))
    canvas.drawImage(BGS[s["bg"]], 0, 0, SAMPLING, bg_paint)
    for item in s["over"]:
        item(canvas, t, bg_paint)
    chars = s.get("chars") or ([s["char"]] if s.get("char") else [])
    for ch in sorted(chars, key=lambda c: c["y"]):
        canvas.drawOval(skia.Rect.MakeXYWH(ch["x"] - 74 * ch["scale"], ch["y"] - 12 * ch["scale"], 148 * ch["scale"], 26 * ch["scale"]),
                        skia.Paint(AntiAlias=True, Color=0x9A000000, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9)))
        canvas.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Blend(look.get("light", 0xFFFFFFFF), skia.BlendMode.kModulate)))
        character(canvas, ch)
        canvas.restore()
    for item in s["front"]:
        item(canvas, t, bg_paint)
    canvas.restore()
    noise = math.sin(t * 37) * math.sin(t * 11.3) * math.sin(t * 5.1)
    level = s["dark"] + max(0, noise) * .2 * s["flicker"]
    if level > 0:
        canvas.drawRect(skia.Rect.MakeWH(W, H), fill(skia.ColorSetARGB(int(min(1, level) * 255), 0, 0, 0)))
    for i, (x, y, z) in enumerate(DUST):
        px = (x + math.sin(t * .3 + i) * 26 + t * 6 * z) % W
        py = (y + math.cos(t * .23 + i) * 18 - t * 3 * z) % H
        canvas.drawCircle(px, py, 1.3 * z, fill(skia.ColorSetARGB(int(42 * z), 225, 235, 225)))
    vig = skia.Paint()
    vig.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * .68, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(200, 0, 0, 0)], [.5, 1.0]))
    canvas.drawRect(skia.Rect.MakeWH(W, H), vig)
    for item in s.get("hud", []):  # screen-space overlays (newspaper, titles), drawn in 1280x720 pixels
        item(canvas, t, None)
    if s.get("caption"):
        x = (W - CAPTION_FONT.measureText(s["caption"])) / 2
        canvas.drawString(s["caption"], x, 110, CAPTION_FONT, stroke(12))
        canvas.drawString(s["caption"], x, 110, CAPTION_FONT, fill(0xFFF2E6B8))
    fade = max(s.get("fade", 0), 1 - ease(t / .45), ease((t - (TL["duration"] - .5)) / .45))
    if fade > 0:
        canvas.drawRect(skia.Rect.MakeWH(W, H), fill(skia.ColorSetARGB(int(fade * 255), 0, 0, 0)))
    subtitle(canvas, t)


def subtitle(canvas, t):
    for cue in CUES:
        if cue["start"] <= t < cue["end"] + .12:
            clean = cue["text"].rstrip(".,;")
            x = (W - SUB_FONT.measureText(clean)) / 2
            canvas.drawString(clean, x, H - 44, SUB_FONT, stroke(9))
            canvas.drawString(clean, x, H - 44, SUB_FONT, fill(0xFFFFFFFF))
            return


# ---------------------------------------------------------------- sound
SR = 48000
LIBRARY = ROOT.parent / "sfx" / "library"


def _catalog():
    return {PureWindowsPath(i["path"]).name: i["path"] for i in json.loads((ROOT.parent / "sfx" / "catalog.json").read_text(encoding="utf-8"))}


def _load(cat, name, start=0.0, dur=None, af=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start)] + (["-t", str(dur)] if dur else []) + ["-i", str(LIBRARY / cat[name])]
    cmd += (["-af", af] if af else []) + ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).reshape(-1, 2).copy()
    return x / max(np.abs(x).max(), 1e-6)


def _fades(x, a=.15, b=.3):
    n = len(x)
    env = np.minimum(1, np.arange(n) / max(1, SR * a)) * np.minimum(1, (n - np.arange(n)) / max(1, SR * b))
    return x * env[:, None]


def _when(v, duration):
    """A number, a beat name, 'beat.N' for one of a list of beats, 'lN.start'/'lN.end' for sentence N, or 'fin'."""
    if isinstance(v, (int, float)):
        return [float(v)]
    if v == "fin":
        return [duration]
    if v in BEATS:
        b = BEATS[v]
        return [float(x) for x in b] if isinstance(b, (list, tuple)) else [float(b)]
    name, _, part = v.rpartition(".")
    if name in BEATS and part.isdigit():
        return [float(BEATS[name][int(part)])]
    if name.startswith("l") and name[1:].isdigit() and part in ("start", "end"):
        return [LINES[int(name[1:])][part]]
    raise KeyError(f"tiempo desconocido en sonido.json: {v}")


VOICE_CHAIN = ("highpass=f=75,equalizer=f=260:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,treble=g=1.5:f=9000,"
               "deesser=i=0.35,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2")


def mezclar(lufs=-14.0, duck_db=6.0):
    """Narration through the voice chain, sonido.json under it (ducked while the narrator speaks), loudness-normalized."""
    import soundfile as sf
    duration = TL["duration"]
    n = int(duration * SR)
    cmd = ["ffmpeg", "-v", "error", "-i", str(EP / "audio" / "narracion.wav"), "-af", VOICE_CHAIN, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    voice = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).copy()
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    mix = np.zeros((n, 2), dtype=np.float32)
    cat = _catalog()

    def place(clip, at, gain):
        i = int(at * SR)
        if 0 <= i < n:
            end = min(n, i + len(clip))
            mix[i:end] += clip[:end - i] * gain

    spec = EP / "sonido.json"
    for e in (json.loads(spec.read_text(encoding="utf-8")) if spec.exists() else []):
        kind, gain = e["tipo"], e.get("gain", .2)
        if kind == "ambiente":
            mix += np.resize(_load(cat, e["archivo"], 0, duration + 1, e.get("af")), (n, 2)) * gain
            continue
        if kind == "golpe":
            clip = _load(cat, e["archivo"], e.get("inicio", 0), e.get("dur"), e.get("af"))
            if e.get("dur"):
                clip = _fades(clip, .005, min(.3, e["dur"] / 2))
            for j, tt in enumerate(_when(e["en"], duration)):
                if j % e.get("cada", 1) == 0:
                    place(clip, tt + e.get("mas", 0), gain)
            continue
        a = _when(e["a"], duration)[0] + e.get("mas", 0)
        b = min(duration, _when(e["b"], duration)[-1] + e.get("mas_b", 0))
        if kind == "cama":
            place(_fades(_load(cat, e["archivo"], e.get("inicio", 0), b - a + .1, e.get("af")), .3, .5), a, gain)
        elif kind == "repetir":
            clip = _load(cat, e["archivo"], e.get("inicio", 0), e.get("dur"), e.get("af"))
            if e.get("dur"):
                clip = _fades(clip, .005, min(.3, e["dur"] / 2))
            tt = a
            while tt < b:
                place(clip, tt, gain)
                tt += e["cada"]
        else:
            raise ValueError(f"tipo desconocido en sonido.json: {kind}")
    if duck_db:  # effects dip while the narrator speaks and swell back in the pauses
        hop = SR // 100
        lv = np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, mode="same")[::hop])
        on = np.clip((20 * np.log10(lv + 1e-9) + 45) / 10, 0, 1)
        env = np.zeros_like(on)
        for j in range(1, len(on)):
            env[j] = env[j - 1] + (on[j] - env[j - 1]) * (.5 if on[j] > env[j - 1] else .03)
        mix *= (10 ** (-duck_db / 20 * np.interp(np.arange(n), np.arange(len(env)) * hop, env)))[:, None]
    out = (voice * (.9 / max(np.abs(voice).max(), 1e-6)))[:, None] + mix
    fade = np.minimum(1, np.arange(n) / (SR * .2)) * np.minimum(1, (n - np.arange(n)) / (SR * .8))
    raw = EP / "audio" / "mezcla.wav"
    sf.write(raw, np.tanh(out * fade[:, None] * 1.02) * .97, SR)
    target = f"I={lufs}:TP=-1.5:LRA=9"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    final = EP / "audio" / "mezcla_final.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af",
                    f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
                    f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true", "-ar", str(SR), str(final)], check=True)
    print("audio", final)
    return final


# ---------------------------------------------------------------- output
def _ff_path(p):
    return Path(p).as_posix().replace(":", "\\:")


def short(slug):
    """Horizontal video with sound, then the vertical 1080x1920 Short with the yellow Impact title above it."""
    out = EP / "output"
    horizontal, vertical = out / f"{slug}_horizontal.mp4", out / f"{slug}_short.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out / "video_mudo.mp4"), "-i", str(EP / "audio" / "mezcla_final.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(horizontal)], check=True)
    draws = []
    for j, text in enumerate(STORY.get("short_title", STORY["title"]).split("\n")):
        f = out / f"titulo_{j}.txt"
        f.write_text(text, encoding="utf-8")
        draws.append(f"drawtext=fontfile='{_ff_path('C:/Windows/Fonts/impact.ttf')}':textfile='{_ff_path(f)}':fontcolor=0xF2E21E"
                     f":fontsize=104:x=(w-text_w)/2:y={210 + j * 128}")
    vf = "scale=1080:-2,pad=1080:1920:0:(oh-ih)/2:black," + ",".join(draws)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(horizontal), "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(vertical)], check=True)
    print("ok", horizontal, vertical)


def terminar(shots, layout, slug):
    (EP / "beats.json").write_text(json.dumps(BEATS, indent=1), encoding="utf-8")
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    surface = skia.Surface(pixels, colorType=skia.kRGBA_8888_ColorType)
    canvas = surface.getCanvas()
    if "--stills" in sys.argv:
        from PIL import Image
        out = EP / "stills"
        out.mkdir(exist_ok=True)
        for value in sys.argv[sys.argv.index("--stills") + 1].split(","):
            frame(canvas, float(value), shots, layout)
            Image.fromarray(pixels[:, :, :3].copy()).save(out / f"t{float(value):05.1f}.png")
        print("stills", out)
    if "--full" in sys.argv:
        total = int(TL["duration"] * FPS)
        target = EP / "output" / "video_mudo.mp4"
        target.parent.mkdir(exist_ok=True)
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(target)], stdin=subprocess.PIPE)
        for i in range(total):
            frame(canvas, i / FPS, shots, layout)
            ff.stdin.write(pixels.tobytes())
            if i % 300 == 0:
                print(i, total, flush=True)
        ff.stdin.close()
        ff.wait()
        print("ok", target)
    if "--audio" in sys.argv:
        mezclar()
    if "--short" in sys.argv:
        short(slug)

