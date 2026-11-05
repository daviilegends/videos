"""Voice identity drift per benchmark file. Run with the chatterbox interpreter, which has its voice encoder."""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
from huggingface_hub import snapshot_download
from chatterbox.models.voice_encoder import VoiceEncoder
import torch

ROOT = Path(__file__).resolve().parent
ve = VoiceEncoder()
ckpt = Path(snapshot_download("ResembleAI/chatterbox", local_files_only=True, allow_patterns=["ve.pt"]))
ve.load_state_dict(torch.load(ckpt / "ve.pt", map_location="cpu", weights_only=True))
ve.to("cuda").eval()
res = {}
for wav in sorted((ROOT / "out").glob("*.wav")):
    y, _ = librosa.load(wav, sr=16000)
    parts = np.array_split(y, 6)
    e = ve.embeds_from_wavs([p for p in parts], sample_rate=16000)
    e = e / np.linalg.norm(e, axis=1, keepdims=True)
    mean = e.mean(0)
    mean /= np.linalg.norm(mean)
    res[wav.stem] = round(float((e @ mean).min()), 3)
    print(wav.stem, res[wav.stem], flush=True)
(ROOT / "consistency.json").write_text(json.dumps(res), encoding="utf-8")
