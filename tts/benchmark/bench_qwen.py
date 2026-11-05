"""Qwen3-TTS 1.7B VoiceDesign, whole text and per sentence (a fixed seed does not guarantee one identity)."""
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

from common import REF_TEXT, REFS, Run, TEXT, VOICE_EN, join, sentences

CKPT = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
model = Qwen3TTSModel.from_pretrained(CKPT, device_map="cuda:0", dtype=torch.bfloat16, attn_implementation="sdpa")


def say(text, seed=7):
    torch.manual_seed(seed)
    wavs, sr = model.generate_voice_design(text=text, language="Spanish", instruct=VOICE_EN)
    return wavs[0], sr


with Run("qwen17_diseno", "Qwen3-TTS", CKPT, "voice design, texto completo, bf16, sdpa") as r:
    wav, sr = say(TEXT)
    r.save(wav, sr)

with Run("qwen17_diseno_frases", "Qwen3-TTS", CKPT, "voice design por frase, misma semilla, bf16, sdpa") as r:
    chunks = [say(s.strip()) for s in sentences()]
    r.save(join([c[0] for c in chunks], chunks[0][1]), chunks[0][1])

wav, sr = say(REF_TEXT)
sf.write(REFS / "narrador_qwen.wav", wav, sr)
