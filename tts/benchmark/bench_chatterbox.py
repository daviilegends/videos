"""Chatterbox general vs es-MX-LATAM. Run with the existing voz\\chatterbox\\env interpreter (read-only use)."""
import sys
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from safetensors.torch import load_file

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chatterbox.models.s3gen import S3Gen
from chatterbox.models.t3 import T3
from chatterbox.models.t3.modules.t3_config import T3Config
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

from common import REFS, Run, join, sentences

REF = str(REFS / "narrador_qwen.wav")
CONFIGS = {"actual": dict(exaggeration=0.5, cfg_weight=0.5), "narrador": dict(exaggeration=0.65, cfg_weight=0.35)}


def run(name, ckpt, model):
    model.prepare_conditionals(REF, exaggeration=0.5)
    for label, cfg in CONFIGS.items():
        with Run(f"{name}_{label}", "Chatterbox Multilingual", ckpt, f"ref narrador sintético, por frase, {cfg}") as r:
            torch.manual_seed(7)
            r.save(join([model.generate(s.strip(), language_id="es", **cfg).squeeze().cpu().numpy()
                          for s in sentences()], model.sr), model.sr)


if sys.argv[1] == "general":
    run("chatterbox_general", "ResembleAI/chatterbox", ChatterboxMultilingualTTS.from_pretrained("cuda"))
else:
    model = ChatterboxMultilingualTTS.from_pretrained("cpu")
    latam = Path(snapshot_download("ResembleAI/Chatterbox-Multilingual-es-mx-latam", local_files_only=True,
                                   allow_patterns=["t3_es_mx_latam.safetensors", "s3gen_v3.safetensors"]))
    t3 = T3(T3Config.multilingual())
    t3.load_state_dict(load_file(latam / "t3_es_mx_latam.safetensors"))
    model.t3 = t3.eval()
    s3 = S3Gen()
    print("s3gen_v3:", s3.load_state_dict(load_file(latam / "s3gen_v3.safetensors"), strict=False), flush=True)
    model.s3gen = s3.eval()
    model.device = "cuda"
    model.t3.to("cuda"), model.s3gen.to("cuda"), model.ve.to("cuda")
    run("chatterbox_latam", "ResembleAI/Chatterbox-Multilingual-es-mx-latam", model)
