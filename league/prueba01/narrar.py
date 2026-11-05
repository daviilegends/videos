"""Narration for the 10 s test: clones voice A sentence by sentence and writes narracion.wav plus timings."""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import voxcpm.model.voxcpm2 as vm
from voxcpm import VoxCPM

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tts" / "benchmark"))
sys.path.insert(0, str(HERE.parent / "voces"))
from voxcpm_stream import install

install(vm)
REF = HERE.parent / "voces" / "B_youtuber_seguro.wav"
REF_TEXT = ("¿Sabías que cada vez que golpeas al campeón enemigo, sus súbditos se giran para atacarte? "
            "No es mala suerte. Es una regla del juego, y hoy vas a aprender a usarla a tu favor. "
            "¿Ya lo sabías, o llevabas años perdiendo vida sin entender por qué?")
LINES = ["¿Por qué los súbditos te pegan cuando atacas al rival?",
         "Porque si golpeas a un campeón con un ataque básico, sus súbditos cercanos se giran contra ti."]
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
sr = model.tts_model.sample_rate
parts, times, t = [np.zeros(int(sr * .15))], [], .15
for line in LINES:
    torch.manual_seed(11)
    wav = model.generate(text=line, prompt_wav_path=str(REF), prompt_text=REF_TEXT, cfg_value=2.0, inference_timesteps=10)
    idx = np.where(np.abs(wav) > .01)[0]
    wav = wav[max(0, idx[0] - 400):idx[-1] + 1200]
    times.append(dict(text=line, start=round(t, 2), end=round(t + len(wav) / sr, 2)))
    parts += [wav, np.zeros(int(sr * .3))]
    t += len(wav) / sr + .3
sf.write(HERE / "narracion.wav", np.concatenate(parts), sr)
(HERE / "lineas.json").write_text(json.dumps(times, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(times, ensure_ascii=False))
