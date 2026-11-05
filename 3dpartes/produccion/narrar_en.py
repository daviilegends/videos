"""English narrator for 3dpartes: designs a voice once, clones it for every line, writes the timeline and the
word-by-word timings (words.json) that the word captions follow.

    ..\\..\\tts\\env\\Scripts\\python.exe narrar_en.py <carpeta_episodio> [--voz narrador_en] [--tempo 1.0]
    ..\\..\\tts\\env\\Scripts\\python.exe narrar_en.py <carpeta_episodio> --semillas 11,23,37 [--estilo energico]

--semillas only writes candidate reference voices to voces\\candidato_<estilo>_<semilla>.wav; copy the chosen one to
voces\\<voz>.wav. Voices: narrador_en (calm documentary, episodes 01-02) and narrador_energico (fast viral explainer,
from episode 03). --tempo speeds each line up without changing the pitch (ffmpeg atempo)."""
import json
import re
import subprocess
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import soundfile as sf


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


EP = Path(sys.argv[1]).resolve()
SEEDS = [int(s) for s in arg("--semillas", "").split(",")] if "--semillas" in sys.argv else None
STYLE = arg("--estilo", "documental")
VOICE = arg("--voz", "narrador_en")
TEMPO = float(arg("--tempo", "1.0"))
LANG = arg("--idioma", "en")          # en: reads ln["en"]; es: reads ln["es"]
sys.argv = sys.argv[:1]
sys.path.insert(0, r"C:\videos-youtube\tts\benchmark")
import torch  # noqa: E402
import voxcpm.model.voxcpm2 as vm  # noqa: E402
from voxcpm import VoxCPM  # noqa: E402

from voxcpm_stream import install  # noqa: E402

install(vm)
VOICES = Path(__file__).resolve().parent / "voces"
VOICES.mkdir(exist_ok=True)
STYLES = {
    "documental": ("A fluent, confident male documentary narrator with a clear, warm American accent, deep and smooth, "
                   "energetic and engaging like a popular science channel, natural flowing delivery, studio microphone",
                   "Every great road starts with a simple line on the ground. Let's see how it's built, one layer at a time."),
    "profesional_es": ("Narrador profesional masculino de documental, voz grave, cálida y clara, español latino neutro, "
                       "dicción perfecta, entusiasta y con energía, como un programa de ciencia de televisión, micrófono de estudio",
                       "Todo empieza con un grano de maíz. Y lo que pasa después, dentro de estas máquinas, es increíble."),
    "energico": ("A young American male narrator, fast-talking, upbeat and punchy, like a viral explainer short, with strong "
                 "emphasis on key words, lively rising and falling intonation, a playful storytelling tone, crisp studio microphone",
                 "So you dig a hole and fill it with water. But by morning, the water is gone! So you build a cage of steel, and spray it with concrete."),
}
REF_TEXTS = {"narrador_en": STYLES["documental"][1], "narrador_energico": STYLES["energico"][1], "narrador_es": STYLES["profesional_es"][1]}
HEAD, LINE_PAUSE, SCENE_PAUSE = .3, .12, .28

model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
sr = model.tts_model.sample_rate


def trim(wav, floor=.02):
    """Cuts leading and trailing silence, keeping a few milliseconds so words are not clipped."""
    loud = np.flatnonzero(np.abs(wav) > floor * np.abs(wav).max())
    if not len(loud):
        return wav
    pad = int(sr * .03)
    return wav[max(0, loud[0] - pad):loud[-1] + pad]


def faster(wav):
    if abs(TEMPO - 1) < 1e-3:
        return wav
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-af", f"atempo={TEMPO}",
                          "-f", "f32le", "-"], input=wav.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


if SEEDS:
    desc, text = STYLES[STYLE]
    for seed in SEEDS:
        torch.manual_seed(seed)
        wav = np.asarray(model.generate(text=f"({desc}){text}", cfg_value=2.0, inference_timesteps=10), dtype=np.float32).squeeze()
        sf.write(VOICES / f"candidato_{STYLE}_{seed}.wav", trim(wav), sr)
        print(seed, round(len(wav) / sr, 2), "s", flush=True)
    sys.exit()

REF, REF_TEXT = VOICES / f"{VOICE}.wav", REF_TEXTS[VOICE]
story = json.loads((EP / "story.json").read_text(encoding="utf-8"))
(EP / "audio").mkdir(exist_ok=True)
parts, timeline, cursor = [np.zeros(int(sr * HEAD), dtype=np.float32)], [], HEAD
t0 = time.time()
torch.manual_seed(7)
for scene in story["scenes"]:
    start, lines = cursor, []
    for i, ln in enumerate(scene["lines"]):
        wav = faster(trim(np.asarray(model.generate(text=ln[LANG], prompt_wav_path=str(REF), prompt_text=REF_TEXT, reference_wav_path=str(REF),
                                                    cfg_value=2.0, inference_timesteps=10), dtype=np.float32).squeeze()))
        dur = len(wav) / sr
        lines.append(dict(en=ln.get("en", ""), es=ln.get("es", ""), texto=ln[LANG], nombra=ln.get("nombra", False), start=round(cursor, 3), end=round(cursor + dur, 3)))
        pause = LINE_PAUSE if i < len(scene["lines"]) - 1 else SCENE_PAUSE
        parts += [wav, np.zeros(int(sr * pause), dtype=np.float32)]
        cursor += dur + pause
        print(f"{scene['id']} {dur:.1f}s {ln[LANG]}", flush=True)
    timeline.append(dict(id=scene["id"], etiqueta=scene.get("etiqueta", ""), termino_en=scene.get("termino_en", ""),
                         start=round(start, 3), end=round(cursor, 3), lines=lines))
cursor += .8
parts.append(np.zeros(int(sr * .8), dtype=np.float32))
sf.write(EP / "audio" / "narracion.wav", np.concatenate(parts), sr)
(EP / "timeline.json").write_text(json.dumps(dict(duration=round(cursor, 3), scenes=timeline), ensure_ascii=False, indent=1), encoding="utf-8")
print(f"duracion {cursor:.1f}s, generacion {time.time() - t0:.0f}s")

# ------------------------------------------------------------------ word timings for word-by-word captions
del model
torch.cuda.empty_cache()
from faster_whisper import WhisperModel  # noqa: E402


def norm(w):
    import unicodedata
    w = "".join(c for c in unicodedata.normalize("NFD", w.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9'ñ]", "", w)


heard = [w for s in WhisperModel("small", device="cuda", compute_type="int8_float16").transcribe(
    str(EP / "audio" / "narracion.wav"), language=LANG, word_timestamps=True)[0] for w in s.words if norm(w.word)]
script = [(n, w) for n, ln in enumerate(l for s in timeline for l in s["lines"]) for w in ln["texto"].split()]
times = {}
for a, b, size in SequenceMatcher(None, [norm(w) for _, w in script], [norm(w.word) for w in heard], autojunk=False).get_matching_blocks():
    for k in range(size):
        times[a + k] = (heard[b + k].start, heard[b + k].end)
flat = [l for s in timeline for l in s["lines"]]
words = []
for k, (n, w) in enumerate(script):
    if k in times:
        a, b = times[k]
    else:  # not heard: place it between its neighbours inside its line
        ln = flat[n]
        idx = [j for j, (m, _) in enumerate(script) if m == n]
        a = ln["start"] + (ln["end"] - ln["start"]) * idx.index(k) / len(idx)
        b = a + .2
    words.append(dict(text=w, start=round(a, 3), end=round(b, 3), line=n))
(EP / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
print("palabras alineadas", len(times), "de", len(script))
