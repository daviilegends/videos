"""Builds subtitle cues from the words actually heard in the narration, so they follow the voice and not the script timing."""
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import torch  # puts torch's CUDA DLLs on the path for faster-whisper
from faster_whisper import WhisperModel

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent  # episode folder
LIMIT, MIN_TAIL = 36, 12
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))


def norm(t):
    t = "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")
    return "".join(re.findall(r"[a-zñ0-9]+", t))


def phrases(text):
    parts, cur = [], []
    for word in text.split():
        if cur and len(" ".join(cur + [word])) > LIMIT:
            parts.append(cur)
            cur = []
        cur.append(word)
        if word[-1] in ",:;" and len(" ".join(cur)) > 14:
            parts.append(cur)
            cur = []
    if cur:
        parts.append(cur)
    if len(parts) > 1 and len(" ".join(parts[-1])) < MIN_TAIL:
        tail = parts.pop()
        parts[-1] += tail
    return parts


model = WhisperModel("small", device="cuda", compute_type="int8_float16")
segs, _ = model.transcribe(str(ROOT / "audio" / "narracion.wav"), language="es", beam_size=5, word_timestamps=True)
heard = [w for s in segs for w in s.words if norm(w.word)]
script = [(i, w) for i, line in enumerate(l for s in tl["scenes"] for l in s["lines"]) for w in line["text"].split()]
matcher = SequenceMatcher(None, [norm(w) for _, w in script], [norm(w.word) for w in heard], autojunk=False)
times = {}
for a, b, size in matcher.get_matching_blocks():
    for k in range(size):
        times[a + k] = (heard[b + k].start, heard[b + k].end)
print("palabras alineadas", len(times), "de", len(script))
# one entry per script word, for one-word-at-a-time captions
words = [dict(text=w, start=round(times[k][0], 3), end=round(times[k][1], 3), sentence=i) for k, (i, w) in enumerate(script) if k in times]
(ROOT / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")

cues, at, n = [], 0, 0
for line in (l for s in tl["scenes"] for l in s["lines"]):
    parts = phrases(line["text"])
    total = sum(len(p) for p in parts)
    done = 0
    for part in parts:
        idx = range(at, at + len(part))
        known = [times[i] for i in idx if i in times]
        if not known:  # Whisper heard none of these words: share the sentence's time by word count
            span = line["end"] - line["start"]
            known = [(line["start"] + span * done / total, line["start"] + span * (done + len(part)) / total)]
        cues.append(dict(text=" ".join(part), start=round(known[0][0], 3), end=round(known[-1][1], 3), sentence=n))
        at += len(part)
        done += len(part)
    n += 1
for prev, nxt in zip(cues, cues[1:]):  # hold each cue until the next one when the gap is short
    if nxt["start"] - prev["end"] < .35:
        prev["end"] = nxt["start"]
(ROOT / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(cues), "subtitulos; mas largo:", max(len(c["text"]) for c in cues))
