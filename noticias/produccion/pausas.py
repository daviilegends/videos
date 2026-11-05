"""Re-spaces the narration with longer breathing pauses (news pacing) and moves the timeline to match.
    python pausas.py <pausa_frase> <pausa_escena> <inicio> <final>"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent
SENT, SCENE, HEAD, TAIL = (float(v) for v in sys.argv[1:5])
wav, sr = sf.read(ROOT / "audio" / "narracion.wav", dtype="float32")
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
parts, cursor = [np.zeros(int(sr * HEAD), dtype=np.float32)], HEAD
for scene in tl["scenes"]:
    scene["start"] = round(cursor, 3)
    for i, ln in enumerate(scene["lines"]):
        clip = wav[int(ln["start"] * sr):int(ln["end"] * sr)]
        ln["start"], ln["end"] = round(cursor, 3), round(cursor + len(clip) / sr, 3)
        pause = SENT if i < len(scene["lines"]) - 1 else SCENE
        parts += [clip, np.zeros(int(sr * pause), dtype=np.float32)]
        cursor += len(clip) / sr + pause
    scene["end"] = round(cursor, 3)
parts.append(np.zeros(int(sr * TAIL), dtype=np.float32))
tl["duration"] = round(cursor + TAIL, 3)
sf.write(ROOT / "audio" / "narracion.wav", np.concatenate(parts), sr)
(ROOT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
print("duracion", tl["duration"])
