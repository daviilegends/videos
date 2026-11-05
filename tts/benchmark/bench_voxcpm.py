"""VoxCPM2: design a synthetic narrator once, then clone it for every sentence."""
import json
import struct

import soundfile as sf
import torch
import voxcpm.model.voxcpm2 as vm
from voxcpm import VoxCPM

# The stock load holds the whole 4.6 GB file next to the model, which exhausts this machine's
# commit memory (access violation with mmap, MemoryError without). Stream it into the model instead.
DTYPES = {"BF16": torch.bfloat16, "F16": torch.float16, "F32": torch.float32, "F64": torch.float64,
          "I64": torch.int64, "I32": torch.int32, "U8": torch.uint8, "BOOL": torch.bool}
source = {}
vm.load_file = lambda path: source.update(path=path) or {}
_load_state_dict = vm.VoxCPM2Model.load_state_dict


def stream_state_dict(self, state, strict=False):
    result = _load_state_dict(self, state, strict=False)
    own = self.state_dict()
    copied = 0
    with open(source["path"], "rb") as f:
        size = struct.unpack("<Q", f.read(8))[0]
        header = json.loads(f.read(size))
        base = 8 + size
        with torch.no_grad():
            for name, info in header.items():
                if name in own:
                    start, end = info["data_offsets"]
                    f.seek(base + start)
                    data = torch.frombuffer(bytearray(f.read(end - start)), dtype=DTYPES[info["dtype"]])
                    own[name].copy_(data.reshape(info["shape"]))
                    copied += 1
    print(f"streamed {copied}/{len(header)} tensors", flush=True)
    return result


vm.VoxCPM2Model.load_state_dict = stream_state_dict

from common import REF_TEXT, REFS, Run, TEXT, VOICE_EN, join, sentences

torch.manual_seed(7)
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
sr = model.tts_model.sample_rate
ref = REFS / "narrador_voxcpm.wav"
CFG = dict(cfg_value=2.0, inference_timesteps=10)

with Run("voxcpm2_diseno", "VoxCPM2", "openbmb/VoxCPM2", f"voice design, texto completo, {CFG}") as r:
    r.save(model.generate(text=f"({VOICE_EN}){TEXT}", **CFG), sr)

sf.write(ref, model.generate(text=f"({VOICE_EN}){REF_TEXT}", **CFG), sr)
with Run("voxcpm2_clon_frases", "VoxCPM2", "openbmb/VoxCPM2", f"narrador diseñado + clon por frase, {CFG}") as r:
    chunks = [
        model.generate(text=s.strip(), prompt_wav_path=str(ref), prompt_text=REF_TEXT,
                       reference_wav_path=str(ref), **CFG)
        for s in sentences()
    ]
    r.save(join(chunks, sr), sr)
