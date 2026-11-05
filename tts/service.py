"""Local TTS service. The model loads once on the first request that needs it and is reused afterwards.
Run: tts\\env\\Scripts\\python.exe tts\\service.py   (http://127.0.0.1:8771)"""
import re
import shutil
import sys
import threading
import time
import uuid
from pathlib import Path

import numpy as np
import soundfile as sf
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
BENCH = ROOT / "benchmark"
sys.path.insert(0, str(BENCH))
OUT = ROOT.parent / "production" / "audio" / "generated"
MODEL = "voxcpm2"
VOICES = {"narrador": (BENCH / "refs" / "narrador_voxcpm.wav",
                       "Hay lugares que guardan silencio durante años, esperando a que alguien vuelva. "
                       "Esta es la historia de uno de ellos, y de lo que encontramos al abrir sus puertas.")}
MIN_FREE_GB = 3.0  # loading the model can grow the Windows page file by several GB
SENTENCE_PAUSE = 0.2

app = FastAPI(title="Local TTS")
lock = threading.Lock()
state = {"model": None, "load_s": None}


class TTSRequest(BaseModel):
    text: str
    model: str = MODEL
    voice: str = "narrador"
    language: str = "es"
    style: str | None = None
    speed: float = 1.0


class BenchmarkRequest(BaseModel):
    text: str
    voice: str = "narrador"


def free_gb():
    return shutil.disk_usage(ROOT).free / 1e9


def load():
    if state["model"] is None:
        if free_gb() < MIN_FREE_GB + 6:
            raise HTTPException(507, f"Solo hay {free_gb():.1f} GB libres; cargar el modelo puede llenar el disco")
        import voxcpm.model.voxcpm2 as vm
        from voxcpm import VoxCPM
        from voxcpm_stream import install

        t0 = time.time()
        install(vm)
        state["model"] = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
        state["load_s"] = round(time.time() - t0, 1)
    return state["model"]


def sentences(text):
    """Keeps sentence boundaries; a text without final punctuation still produces its last chunk."""
    found = re.findall(r"[^.!?]+[.!?]+|[^.!?]+$", text.strip())
    return [s.strip() for s in found if s.strip()]


def synthesize(req):
    if req.model != MODEL:
        raise HTTPException(400, f"Modelo no disponible: {req.model}")
    if req.voice not in VOICES:
        raise HTTPException(400, f"Voz no disponible: {req.voice}")
    chunks = sentences(req.text)
    if not chunks:
        raise HTTPException(400, "Texto vacío")
    ref, ref_text = VOICES[req.voice]
    style = f"({req.style})" if req.style else ""
    with lock:
        model = load()
        sr = model.tts_model.sample_rate
        parts = []
        for i, chunk in enumerate(chunks):
            wav = np.asarray(model.generate(text=style + chunk, prompt_wav_path=str(ref), prompt_text=ref_text,
                                            reference_wav_path=str(ref), cfg_value=2.0, inference_timesteps=10),
                             dtype=np.float32).squeeze()
            parts.append(wav)
            if i < len(chunks) - 1:
                parts.append(np.zeros(int(sr * SENTENCE_PAUSE), dtype=np.float32))
    return np.concatenate(parts), sr


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": state["model"] is not None, "load_s": state["load_s"], "disk_free_gb": round(free_gb(), 1)}


@app.get("/models")
def models():
    return {"models": [{"id": MODEL, "checkpoint": "openbmb/VoxCPM2", "license": "Apache-2.0", "voices": list(VOICES)}]}


@app.post("/tts/generate")
def generate(req: TTSRequest):
    if abs(req.speed - 1.0) > 1e-3:
        raise HTTPException(400, "speed distinto de 1.0 no está implementado; usa style, por ejemplo 'slightly slower'")
    wav, sr = synthesize(req)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{uuid.uuid4().hex[:12]}.wav"
    sf.write(path, wav, sr)
    return {"status": "completed", "audio_path": str(path), "duration": round(len(wav) / sr, 2), "model": req.model}


@app.post("/tts/benchmark")
def benchmark(req: BenchmarkRequest):
    was_loaded = state["model"] is not None
    t0 = time.time()
    wav, sr = synthesize(TTSRequest(text=req.text, voice=req.voice))
    gen = time.time() - t0
    import torch
    return {"model": MODEL, "voice": req.voice, "model_was_loaded": was_loaded, "generation_s": round(gen, 1), "audio_s": round(len(wav) / sr, 2),
            "rtf": round(gen / (len(wav) / sr), 2), "vram_peak_gb": round(torch.cuda.max_memory_reserved() / 1e9, 2)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8771)
