"""Shared text, chunking and metrics for the TTS benchmark. No third-party model imports here."""
import json
import re
import time
from pathlib import Path

import numpy as np
import psutil
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
REFS = ROOT / "refs"
RESULTS = ROOT / "results.jsonl"
OUT.mkdir(exist_ok=True)
REFS.mkdir(exist_ok=True)

TEXT = (
    "Abres los ojos y lo primero que escuchas es el silencio. "
    "Este hospital lleva más de veinte años cerrado, y según los registros, nadie debería estar aquí. "
    "Entonces, desde el fondo del pasillo, alguien grita tu nombre. "
    "Caminas despacio, con la linterna temblando en la mano, pasando junto a camillas volcadas, "
    "puertas entreabiertas y un olor a medicina vieja que no termina de irse. "
    "Y cuando por fin llegas a la última puerta, algo, desde el otro lado, empieza a abrirla."
)
REF_TEXT = (
    "Hay lugares que guardan silencio durante años, esperando a que alguien vuelva. "
    "Esta es la historia de uno de ellos, y de lo que encontramos al abrir sus puertas."
)
VOICE_ES = (
    "Narrador masculino adulto latinoamericano, acento mexicano neutro, voz grave y cálida, "
    "ritmo pausado, tono de documental de suspenso"
)
VOICE_EN = (
    "Adult male Latin American Spanish narrator, neutral Mexican accent, deep warm voice, "
    "slow measured pace, suspenseful documentary storytelling"
)
PAUSE_S = 0.28


def sentences(text=TEXT):
    return re.findall(r"[^.!?]+[.!?]+", text)


def join(chunks, sr, pause=PAUSE_S):
    gap = np.zeros(int(sr * pause), dtype=np.float32)
    parts = []
    for i, c in enumerate(chunks):
        parts.append(np.asarray(c, dtype=np.float32).squeeze())
        if i < len(chunks) - 1:
            parts.append(gap)
    return np.concatenate(parts)


class Run:
    """Times a benchmark run and appends one record to results.jsonl, including failures."""

    def __init__(self, id, model, checkpoint, config):
        self.rec = dict(id=id, model=model, checkpoint=checkpoint, config=config, error=None)

    def __enter__(self):
        torch.cuda.reset_peak_memory_stats()
        self.proc = psutil.Process()
        self.t0 = time.time()
        return self

    def save(self, wav, sr):
        path = OUT / f"{self.rec['id']}.wav"
        sf.write(path, wav, sr)
        self.rec.update(audio=path.name, sr=sr, audio_s=round(len(wav) / sr, 2))

    def __exit__(self, et, ev, tb):
        gen = time.time() - self.t0
        self.rec.update(
            gen_s=round(gen, 1),
            rtf=round(gen / self.rec["audio_s"], 2) if self.rec.get("audio_s") else None,
            vram_peak_gb=round(torch.cuda.max_memory_reserved() / 1e9, 2),
            ram_rss_gb=round(self.proc.memory_info().rss / 1e9, 2),
        )
        if ev is not None:
            self.rec["error"] = f"{et.__name__}: {ev}"[:500]
        with RESULTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(self.rec, ensure_ascii=False) + "\n")
        print(self.rec, flush=True)
        return True
