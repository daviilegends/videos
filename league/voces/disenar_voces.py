"""Designs narrator voice candidates for the League academy test with VoxCPM2 (one file per candidate)."""
import sys
from pathlib import Path

import soundfile as sf
import torch
import voxcpm.model.voxcpm2 as vm
from voxcpm import VoxCPM

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tts" / "benchmark"))
from voxcpm_stream import install

install(vm)
OUT = Path(__file__).resolve().parent
TEXT = ("¿Sabías que cada vez que golpeas al campeón enemigo, sus súbditos se giran para atacarte? "
        "No es mala suerte. Es una regla del juego, y hoy vas a aprender a usarla a tu favor. "
        "¿Ya lo sabías, o llevabas años perdiendo vida sin entender por qué?")
VOICES = {
    "A_profesor_calido": "Adult male Latin American Spanish narrator, neutral accent, warm friendly slightly deep voice, "
                         "conversational educational tone, clear articulation, moderate energy, a teacher who enjoys explaining",
    "B_youtuber_seguro": "Male Latin American Spanish YouTube explainer in his thirties, neutral accent, confident clear voice, "
                         "upbeat but calm, natural conversational rhythm, curious and engaging",
    "C_locutor_grave": "Adult male Latin American Spanish radio host, neutral accent, deep smooth warm voice, "
                       "calm and friendly, relaxed natural pacing, expressive intonation",
}
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
sr = model.tts_model.sample_rate
for name, desc in VOICES.items():
    torch.manual_seed(11)
    sf.write(OUT / f"{name}.wav", model.generate(text=f"({desc}){TEXT}", cfg_value=2.0, inference_timesteps=10), sr)
    print("ok", name, flush=True)
