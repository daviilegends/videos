"""Minimal reader for League of Legends .wad.client files (v3). Uses only xxhash + zlib.
Usage: python wad.py <file.wad.client> [path_in_wad ...]  -> lists the entry count and reports whether each path is present."""
import struct
import sys
import zlib

import xxhash

TYPES = {0: "raw", 1: "gzip", 2: "link", 3: "zstd", 4: "zstd-multi"}


def read_index(fn):
    with open(fn, "rb") as f:
        head = f.read(4)
        assert head[:2] == b"RW", "not a WAD"
        major = head[2]
        if major >= 3:
            f.read(256 + 8)
        else:
            raise SystemExit(f"unsupported WAD version {major}")
        (n,) = struct.unpack("<I", f.read(4))
        ents = {}
        for _ in range(n):
            h, off, csize, size, typ, dup, sub, chk = struct.unpack("<QIIIBBHQ", f.read(32))
            ents[h] = (off, csize, size, typ & 15)
    return ents


def phash(path):
    return xxhash.xxh64(path.lower().encode()).intdigest()


def extract(fn, ents, path):
    e = ents.get(phash(path))
    if e is None:
        return None
    off, csize, size, typ = e
    with open(fn, "rb") as f:
        f.seek(off)
        data = f.read(csize)
    if typ == 0:
        return data
    if typ == 1:
        return zlib.decompress(data, 16 + zlib.MAX_WBITS)
    if typ in (3, 4):
        try:
            import zstandard
        except ImportError:
            raise RuntimeError("zstd")
        return zstandard.ZstdDecompressor().decompress(data, max_output_size=size)
    raise RuntimeError(f"type {typ}")


if __name__ == "__main__":
    ents = read_index(sys.argv[1])
    print(len(ents), "entries")
    for p in sys.argv[2:]:
        e = ents.get(phash(p))
        print(("OK  " + TYPES.get(e[3], str(e[3])) + f" {e[2]} bytes") if e else "--  missing", p)
