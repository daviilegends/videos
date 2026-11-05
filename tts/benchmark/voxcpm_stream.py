"""Streams VoxCPM2 weights into the built model. The stock load keeps the whole 4.6 GB file next to the model,
which exhausts this machine's commit memory (access violation with mmap, MemoryError without)."""
import json
import struct

import torch

DTYPES = {"BF16": torch.bfloat16, "F16": torch.float16, "F32": torch.float32, "F64": torch.float64,
          "I64": torch.int64, "I32": torch.int32, "U8": torch.uint8, "BOOL": torch.bool}


def install(vm):
    source = {}
    vm.load_file = lambda path: source.update(path=path) or {}
    original = vm.VoxCPM2Model.load_state_dict

    def stream_state_dict(self, state, strict=False):
        result = original(self, state, strict=False)
        own = self.state_dict()
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
        return result

    vm.VoxCPM2Model.load_state_dict = stream_state_dict
