"""Kokoro-82M lightweight baseline, Spanish male preset."""
import numpy as np
from kokoro import KPipeline

from common import Run, TEXT

VOICE = "em_alex"
pipe = KPipeline(lang_code="e", repo_id="hexgrad/Kokoro-82M")

with Run("kokoro_em_alex", "Kokoro-82M", "hexgrad/Kokoro-82M", f"voz {VOICE}, lang e, speed 0.95") as r:
    audio = [np.asarray(a) for _, _, a in pipe(TEXT, voice=VOICE, speed=0.95, split_pattern=r"(?<=[.!?])\s+")]
    r.save(np.concatenate(audio), 24000)
