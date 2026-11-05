"""Transcribe each benchmark file and compare with the script; also writes loudness-matched copies for listening."""
import json
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from faster_whisper import WhisperModel

from common import OUT, ROOT, TEXT

NORM = ROOT / "norm"
NORM.mkdir(exist_ok=True)
model = WhisperModel("small", device="cuda", compute_type="int8_float16")


def words(t):
    t = "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-zñ0-9]+", t)


res = {}
ref = words(TEXT)
for wav in sorted(OUT.glob("*.wav")):
    segs, _ = model.transcribe(str(wav), language="es", beam_size=5, vad_filter=False)
    text = " ".join(s.text.strip() for s in segs)
    hyp = words(text)
    ops = SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes()
    diffs = [f"{' '.join(ref[a:b])} -> {' '.join(hyp[c:d])}" for tag, a, b, c, d in ops if tag != "equal"]
    errors = sum(max(b - a, d - c) for tag, a, b, c, d in ops if tag != "equal")
    res[wav.stem] = dict(wer=round(errors / len(ref), 3), diffs=diffs, text=text)
    print(wav.stem, res[wav.stem]["wer"], diffs, flush=True)
    sr = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=sample_rate",
                                  "-of", "csv=p=0", str(wav)], text=True).strip()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", sr, str(NORM / wav.name)], check=True)
(ROOT / "whisper.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
