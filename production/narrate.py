"""Generates the prototype narration with VoxCPM2: one wav per sentence, concatenated, plus scene timings."""
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent  # episode folder
BENCH = Path(__file__).resolve().parent.parent / "tts" / "benchmark"
sys.path.insert(0, str(BENCH))
sys.argv = sys.argv[:1]

import torch
import voxcpm.model.voxcpm2 as vm
from voxcpm import VoxCPM

from voxcpm_stream import install

install(vm)
from common import REF_TEXT

REF = BENCH / "refs" / "narrador_voxcpm.wav"
OUT = ROOT / "audio"
OUT.mkdir(exist_ok=True)
SENTENCE_PAUSE, SCENE_PAUSE = 0.32, 0.65

story = json.loads((ROOT / "story.json").read_text(encoding="utf-8"))
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
sr = model.tts_model.sample_rate
parts, timeline, cursor = [], [], 0.0
t0 = time.time()
torch.manual_seed(7)
for scene in story["scenes"]:
    start = cursor
    lines = []
    sents = re.findall(r"[^.!?]+[.!?]+", scene["text"])
    for i, s in enumerate(sents):
        wav = np.asarray(model.generate(text=s.strip(), prompt_wav_path=str(REF), prompt_text=REF_TEXT,
                                        reference_wav_path=str(REF), cfg_value=2.0, inference_timesteps=10),
                         dtype=np.float32).squeeze()
        dur = len(wav) / sr
        lines.append(dict(text=s.strip(), start=round(cursor, 3), end=round(cursor + dur, 3)))
        pause = SENTENCE_PAUSE if i < len(sents) - 1 else SCENE_PAUSE
        parts += [wav, np.zeros(int(sr * pause), dtype=np.float32)]
        cursor += dur + pause
        print(f"{scene['id']} {dur:.1f}s {s.strip()}", flush=True)
    timeline.append(dict(id=scene["id"], bg=scene["bg"], start=round(start, 3), end=round(cursor, 3), lines=lines))
sf.write(OUT / "narracion.wav", np.concatenate(parts), sr)
(ROOT / "timeline.json").write_text(json.dumps(dict(duration=round(cursor, 3), scenes=timeline), ensure_ascii=False, indent=1), encoding="utf-8")
print(f"duracion {cursor:.1f}s, generacion {time.time() - t0:.0f}s")
