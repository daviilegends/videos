"""Rebuilds narration with shorter pauses from the existing sentence timings, then checks it against the script."""
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import soundfile as sf
import torch  # puts torch's CUDA DLLs on the path, which faster-whisper needs on Windows
from faster_whisper import WhisperModel

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent  # episode folder
SENTENCE_PAUSE, SCENE_PAUSE = 0.2, 0.4
HEAD = 0.3

wav, sr = sf.read(ROOT / "audio" / "narracion.wav", dtype="float32")
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
if not (ROOT / "audio" / "narracion_raw.wav").exists():
    sf.write(ROOT / "audio" / "narracion_raw.wav", wav, sr)
parts, cursor = [np.zeros(int(sr * HEAD), dtype=np.float32)], HEAD
for scene in tl["scenes"]:
    scene["start"] = round(cursor, 3)
    for i, line in enumerate(scene["lines"]):
        clip = wav[int(line["start"] * sr):int(line["end"] * sr)]
        line["start"], line["end"] = round(cursor, 3), round(cursor + len(clip) / sr, 3)
        pause = SENTENCE_PAUSE if i < len(scene["lines"]) - 1 else SCENE_PAUSE
        parts += [clip, np.zeros(int(sr * pause), dtype=np.float32)]
        cursor += len(clip) / sr + pause
    scene["end"] = round(cursor, 3)
tl["duration"] = round(cursor, 3)
out = np.concatenate(parts)
peak = float(np.abs(out).max())
sf.write(ROOT / "audio" / "narracion.wav", out, sr)
(ROOT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
print("duracion", tl["duration"], "pico", round(peak, 3))


def words(t):
    t = "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-zñ0-9]+", t)


model = WhisperModel("small", device="cuda", compute_type="int8_float16")
segs, _ = model.transcribe(str(ROOT / "audio" / "narracion.wav"), language="es", beam_size=5)
hyp = words(" ".join(s.text for s in segs))
ref = words(" ".join(l["text"] for s in tl["scenes"] for l in s["lines"]))
ops = SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes()
print("palabras", len(ref), "diferencias:", [f"{' '.join(ref[a:b])} -> {' '.join(hyp[c:d])}" for t, a, b, c, d in ops if t != "equal"])
