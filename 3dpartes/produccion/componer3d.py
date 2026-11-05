"""Shared compositor for 3dpartes: puts the hook title, Spanish subtitles and the yellow labels (Spanish term, English
term below) on the Blender frames, mixes the narration with the effects listed in the episode's sonido.json, and writes the MP4.

    render_env\\Scripts\\python.exe componer3d.py <carpeta_episodio> <salida.mp4> [--solo-audio]

sonido.json is a list of entries. Times ("a", "b", "en") accept a number, a beat name from beats.json ("tubo"),
an index into a beat list ("topadora.1"), a scene edge ("b5.start", "b7.end") or "fin"; "mas" adds seconds to "a"/"en".
    {"tipo": "ambiente", "archivo": ..., "gain": .05}                          whole video, looped
    {"tipo": "cama", "archivo": ..., "a": ..., "b": ..., "gain": .3, "inicio": 3, "af": "lowpass=f=900"}
    {"tipo": "golpe", "archivo": ..., "en": "estacas", "gain": .2, "dur": .35, "cada": 2}   one hit per time (or per list item)
    {"tipo": "repetir", "archivo": ..., "a": ..., "b": ..., "cada": .5, "gain": .1, "dur": .3}
    {"tipo": "derrape", "a": ..., "b": ..., "gain": .2}                           synthesized tyre screech
"""
import json
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import numpy as np
import soundfile as sf

EP, OUT = Path(sys.argv[1]), Path(sys.argv[2])
FPS, W, H, SR = 30, 1080, 1920, 48000
ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "sfx" / "library"
CATALOG = {PureWindowsPath(i["path"]).name: i["path"] for i in json.loads((ROOT / "sfx" / "catalog.json").read_text(encoding="utf-8"))}
tl = json.loads((EP / "timeline.json").read_text(encoding="utf-8"))
beats = json.loads((EP / "beats.json").read_text(encoding="utf-8"))
story = json.loads((EP / "story.json").read_text(encoding="utf-8"))
SC = {s["id"]: s for s in tl["scenes"]}
YELLOW = 0xFFFFC61A
MAX_LINE = 30
SUB_BASELINE = 1520      # last subtitle line; above the Shorts buttons and caption


# ------------------------------------------------------------------ text on screen
def wrap(words, limit):
    lines, cur = [], []
    for w in words:
        if cur and len(" ".join(cur + [w])) > limit:
            lines.append(" ".join(cur))
            cur = []
        cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def cards():
    """Each English line shows its Spanish translation, in cards of at most two lines, timed by character share."""
    out = []
    for scene in tl["scenes"]:
        for ln in scene["lines"]:
            lines = wrap(ln["es"].split(), MAX_LINE)
            groups = [lines[i:i + 2] for i in range(0, len(lines), 2)]
            if len(groups) > 1 and len(groups[-1]) == 1 and len(groups[-1][0]) < 14:
                groups[-2].append(groups.pop()[0])
            total = sum(len(" ".join(g)) for g in groups)
            t, span = ln["start"], ln["end"] - ln["start"]
            for g in groups:
                d = span * len(" ".join(g)) / total
                out.append([t, t + d, g])
                t += d
    for a, b in zip(out, out[1:]):
        if b[0] - a[1] < .45:
            a[1] = b[0]
    out[-1][1] += .6
    return out


def title_lines(title):
    words = title.upper().split()
    best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:])))) if len(words) > 1 else 1
    return [" ".join(words[:best]), " ".join(words[best:])] if len(words) > 1 else words


MODE = story.get("subtitulos", "tarjetas_es")   # tarjetas_es: Spanish cards; palabra_en: one English word at a time
WORD_Y = story.get("subtitulo_y", 1040)
CARDS = cards() if MODE == "tarjetas_es" else []
WORDS = []
if MODE == "palabra_en":
    WORDS = json.loads((EP / "words.json").read_text(encoding="utf-8"))
    for a, b in zip(WORDS, WORDS[1:]):  # each word stays until the next one starts, unless there is a real pause
        if b["start"] - a["end"] < .35:
            a["end"] = b["start"]
LABELS = []
for scene in tl["scenes"]:
    if scene.get("etiqueta"):
        named = next((ln for ln in scene["lines"] if ln.get("nombra")), scene["lines"][-1])
        LABELS.append((named["start"], scene["end"], scene["etiqueta"], scene.get("termino_en", "")))
second = tl["scenes"][1]["start"] if len(tl["scenes"]) > 1 else 3.0
TITLE = (0.0, second - .1, title_lines(story["title"]))


def video():
    import skia
    face = skia.Typeface.MakeFromFile("C:/Windows/Fonts/ariblk.ttf")
    bold = skia.Typeface.MakeFromFile("C:/Windows/Fonts/arialbd.ttf")
    label_font, term_font = skia.Font(face, 74), skia.Font(bold, 40)
    sub_font, title_font = skia.Font(bold, 58), skia.Font(face, 88)
    word_font = skia.Font(skia.Typeface.MakeFromFile("C:/Windows/Fonts/seguibl.ttf"), 92)

    def outlined(c, text, x, y, font, color, width):
        c.drawString(text, x, y, font, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=0xFF101010,
                                                   StrokeJoin=skia.Paint.kRound_Join))
        c.drawString(text, x, y, font, skia.Paint(AntiAlias=True, Color=color))

    def centered(c, text, y, font, color, width):
        size, f = font.getSize(), font
        while f.measureText(text) > W - 110:
            size -= 4
            f = skia.Font(f.getTypeface(), size)
        outlined(c, text, (W - f.measureText(text)) / 2, y, f, color, width)

    def pop_in(c, t0, t, cx, cy, rot=0):
        k = min(1.0, (t - t0) / .2)
        c.translate(cx, cy)
        c.rotate(rot)
        c.scale(.65 + .35 * k, .65 + .35 * k)
        c.translate(-cx, -cy)

    def overlay(c, t):
        a, b, lines = TITLE
        if a <= t < b:
            c.save()
            pop_in(c, a, t, W / 2, 300)
            for i, line in enumerate(lines):
                centered(c, line, 270 + i * 104, title_font, YELLOW, 18)
            c.restore()
        for start, end, name, term in LABELS:
            if start <= t < end:
                c.save()
                pop_in(c, start, t, W / 2, 330, -4)
                centered(c, name, 330, label_font, YELLOW, 16)
                if term:
                    centered(c, term, 392, term_font, 0xFFFFFFFF, 9)
                c.restore()
        for w in WORDS:
            if w["start"] <= t < w["end"]:
                text = w["text"].strip(".,;:!?\"")
                text = text[:1].upper() + text[1:]
                c.save()
                pop_in(c, w["start"] - .1, t, W / 2, WORD_Y - 30)
                shadow = skia.Paint(AntiAlias=True, Color=0x88000000, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
                f = word_font
                while f.measureText(text) > W - 120:
                    f = skia.Font(f.getTypeface(), f.getSize() - 6)
                x = (W - f.measureText(text)) / 2
                c.drawString(text, x + 4, WORD_Y + 6, f, shadow)
                outlined(c, text, x, WORD_Y, f, 0xFFFFFFFF, 12)
                c.restore()
                break
        for start, end, lines in CARDS:
            if start <= t < end:
                y0 = SUB_BASELINE - (len(lines) - 1) * 70
                for i, line in enumerate(lines):
                    centered(c, line, y0 + i * 70, sub_font, 0xFFFFFFFF, 12)
                break

    frames = sorted((EP / "frames").glob("f_*.jpg"))
    silent = EP / "video_mudo.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    surface = skia.Surface(pixels, colorType=skia.kRGBA_8888_ColorType)
    c = surface.getCanvas()
    for i, fr in enumerate(frames):
        c.drawImage(skia.Image.open(str(fr)), 0, 0)
        overlay(c, i / FPS)
        ff.stdin.write(pixels.tobytes())
    ff.stdin.close()
    ff.wait()
    return silent, len(frames) / FPS


# ------------------------------------------------------------------ sound
_cache = {}


def load(name, start=0.0, dur=None, af=None):
    k = (name, start, dur, af)
    if k not in _cache:
        cmd = ["ffmpeg", "-v", "error", "-ss", str(start)] + (["-t", str(dur)] if dur else []) + ["-i", str(LIBRARY / CATALOG[name])]
        cmd += (["-af", af] if af else []) + ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
        x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).reshape(-1, 2).copy()
        _cache[k] = x / max(np.abs(x).max(), 1e-6)
    return _cache[k]


def fades(x, a=.15, b=.3):
    n = len(x)
    env = np.minimum(1, np.arange(n) / max(1, SR * a)) * np.minimum(1, (n - np.arange(n)) / max(1, SR * b))
    return x * env[:, None]


def skid(dur=1.3):
    t = np.arange(int(SR * dur)) / SR
    rng = np.random.default_rng(3)
    noise = np.convolve(rng.standard_normal(len(t)), np.ones(6) / 6, mode="same")
    noise -= np.convolve(noise, np.ones(40) / 40, mode="same")
    f = 1150 + 120 * np.sin(2 * np.pi * 7 * t) - 250 * t / dur
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + .4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x = (tone * .5 + noise * 1.6) * (.6 + .4 * np.sin(2 * np.pi * 13 * t) ** 2)
    x = fades(np.stack([x, x * .95], 1), .05, .35)
    return x / np.abs(x).max()


def when(v, duration):
    """Resolves a time reference from sonido.json."""
    if isinstance(v, (int, float)):
        return [float(v)]
    if v == "fin":
        return [duration]
    if v in beats:
        b = beats[v]
        return [float(x) for x in b] if isinstance(b, list) else [float(b)]
    name, _, part = v.rpartition(".")
    if name in SC and part in ("start", "end"):
        return [SC[name][part]]
    if name in beats and part.isdigit():
        return [float(beats[name][int(part)])]
    raise KeyError(f"tiempo desconocido en sonido.json: {v}")


# Mix settings; story.json can override any of them under "mezcla".
MEZCLA = {"cadena_voz": True, "lufs": -14.0, "pico": -1.5, "bajar_efectos_db": 6.0}
MEZCLA.update(story.get("mezcla", {}))

# Narrator chain: remove rumble, clear the low-mid mud, add presence and air,
# tame harsh "s" sounds, then even out the level so every word reads.
CADENA_VOZ = ",".join([
    "highpass=f=75",
    "equalizer=f=260:t=q:w=1.2:g=-2.5",
    "equalizer=f=3200:t=q:w=1.0:g=2.5",
    "treble=g=1.5:f=9000",
    "deesser=i=0.35",
    "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2",
])


def leer_voz():
    src = EP / "audio" / "narracion.wav"
    if not MEZCLA["cadena_voz"]:
        voice, sr = sf.read(src, dtype="float32")
        if voice.ndim > 1:
            voice = voice.mean(1)
        if sr != SR:
            voice = np.interp(np.arange(int(len(voice) * SR / sr)) * sr / SR, np.arange(len(voice)), voice).astype(np.float32)
        return voice
    cmd = ["ffmpeg", "-v", "error", "-i", str(src), "-af", CADENA_VOZ, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).copy()


def envolvente_voz(voice, n):
    """0..1 curve that rises fast when the narrator speaks and falls slowly after."""
    hop = SR // 100
    frames = np.sqrt(np.convolve(voice[:n] ** 2, np.ones(hop) / hop, mode="same")[::hop])
    on = np.clip((20 * np.log10(frames + 1e-9) + 45) / 10, 0, 1)
    env = np.zeros_like(on)
    for i in range(1, len(on)):
        k = .5 if on[i] > env[i - 1] else .03
        env[i] = env[i - 1] + (on[i] - env[i - 1]) * k
    return np.interp(np.arange(n), np.arange(len(env)) * hop, env)


def masterizar(path):
    """Two-pass loudness normalization to the platform target, with a true-peak ceiling."""
    target = f"I={MEZCLA['lufs']}:TP={MEZCLA['pico']}:LRA=9"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    out = path.with_name("mezcla_final.wav")
    measured = (f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
                f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-af", f"loudnorm={target}{measured}", "-ar", str(SR), str(out)], check=True)
    return out


def audio(duration):
    voice = leer_voz()
    n = int(duration * SR)
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    mix = np.zeros((n, 2), dtype=np.float32)

    def place(clip, at, gain):
        i = int(at * SR)
        if 0 <= i < n:
            end = min(n, i + len(clip))
            mix[i:end] += clip[:end - i] * gain

    for e in json.loads((EP / "sonido.json").read_text(encoding="utf-8")):
        kind, gain = e["tipo"], e.get("gain", .2)
        if kind == "ambiente":
            mix += np.resize(load(e["archivo"], 0, duration + 1), (n, 2)) * gain
            continue
        if kind == "golpe":
            clip = load(e["archivo"], e.get("inicio", 0), e.get("dur"), e.get("af"))
            if e.get("dur"):
                clip = fades(clip, .005, min(.3, e["dur"] / 2))
            for i, t in enumerate(when(e["en"], duration)):
                if i % e.get("cada", 1) == 0:
                    place(clip, t + e.get("mas", 0), gain)
            continue
        a = when(e["a"], duration)[0] + e.get("mas", 0)
        b = min(duration, when(e["b"], duration)[-1] + e.get("mas_b", 0))
        if kind == "cama":
            place(fades(load(e["archivo"], e.get("inicio", 0), b - a + .1, e.get("af")), .3, .5), a, gain)
        elif kind == "repetir":
            clip = load(e["archivo"], e.get("inicio", 0), e.get("dur"), e.get("af"))
            if e.get("dur"):
                clip = fades(clip, .005, min(.3, e["dur"] / 2))
            t = a
            while t < b:
                place(clip, t, gain)
                t += e["cada"]
        elif kind == "derrape":
            place(skid(b - a + .1), a, gain)
        else:
            raise ValueError(f"tipo desconocido en sonido.json: {kind}")
    gain = .9 / max(np.abs(voice).max(), 1e-6)
    if MEZCLA["bajar_efectos_db"]:
        # Duck the effects under the narrator so words stay clear, and let them swell back in the pauses.
        mix *= (10 ** (-MEZCLA["bajar_efectos_db"] / 20 * envolvente_voz(voice, n)))[:, None]
    out = (voice * gain)[:, None] + mix
    fade = np.minimum(1, np.arange(n) / (SR * .2)) * np.minimum(1, (n - np.arange(n)) / (SR * .8))
    out = np.tanh(out * fade[:, None] * 1.02) * .97
    path = EP / "audio" / "mezcla.wav"
    sf.write(path, out, SR)
    return masterizar(path) if MEZCLA["lufs"] else path


if "--solo-audio" in sys.argv:
    print("ok", audio(len(list((EP / "frames").glob("f_*.jpg"))) / FPS))
    sys.exit()
silent, duration = video()
mixed = audio(duration)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(mixed), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", "-shortest", str(OUT)], check=True)
print("ok", OUT, round(duration, 2), "s")
