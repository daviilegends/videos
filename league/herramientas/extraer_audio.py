"""Copies the League of Legends audio (sound banks + event index + champion data) into our folder,
so it stays available after the game is uninstalled. No downloads: Python 3.14 (compression.zstd) + pure-Python xxh64.
Usage: py -3.14 -I extraer_audio.py "<...>/Game/DATA/FINAL" <output_dir>"""
import json
import struct
import sys
import zlib
from compression import zstd
from pathlib import Path

M64 = (1 << 64) - 1
P1, P2, P3, P4, P5 = 11400714785074694791, 14029467366897019727, 1609587929392839161, 9650029242287828579, 2870177450012600261


def rotl(x, r):
    return ((x << r) | (x >> (64 - r))) & M64


def xxh64(data, seed=0):
    n = len(data)
    i = 0
    if n >= 32:
        v = [(seed + P1 + P2) & M64, (seed + P2) & M64, seed, (seed - P1) & M64]
        while i + 32 <= n:
            for k in range(4):
                (lane,) = struct.unpack_from("<Q", data, i + 8 * k)
                v[k] = (rotl((v[k] + lane * P2) & M64, 31) * P1) & M64
            i += 32
        h = (rotl(v[0], 1) + rotl(v[1], 7) + rotl(v[2], 12) + rotl(v[3], 18)) & M64
        for k in range(4):
            h ^= (rotl((v[k] * P2) & M64, 31) * P1) & M64
            h = (h * P1 + P4) & M64
    else:
        h = (seed + P5) & M64
    h = (h + n) & M64
    while i + 8 <= n:
        (lane,) = struct.unpack_from("<Q", data, i)
        h ^= (rotl((lane * P2) & M64, 31) * P1) & M64
        h = (rotl(h, 27) * P1 + P4) & M64
        i += 8
    if i + 4 <= n:
        (w,) = struct.unpack_from("<I", data, i)
        h ^= (w * P1) & M64
        h = (rotl(h, 23) * P2 + P3) & M64
        i += 4
    while i < n:
        h ^= (data[i] * P5) & M64
        h = (rotl(h, 11) * P1) & M64
        i += 1
    h ^= h >> 33
    h = (h * P2) & M64
    h ^= h >> 29
    h = (h * P3) & M64
    h ^= h >> 32
    return h


def index(fn):
    with open(fn, "rb") as f:
        head = f.read(4)
        assert head[:2] == b"RW" and head[2] >= 3
        f.read(264)
        (n,) = struct.unpack("<I", f.read(4))
        return {h: (off, cs, sz, typ & 15) for h, off, cs, sz, typ, _, _, _ in
                (struct.unpack("<QIIIBBHQ", f.read(32)) for _ in range(n))}


def read(f, e):
    off, cs, sz, typ = e
    f.seek(off)
    raw = f.read(cs)
    if typ == 0:
        return raw
    if typ == 1:
        return zlib.decompress(raw, 16 + zlib.MAX_WBITS)
    if typ in (3, 4):
        return zstd.decompress(raw)
    return None


def main():
    final, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    report = {"campeones": {}, "mapas": {}}
    total = 0
    # 1) champions: known paths
    champs = sorted(p for p in (final / "Champions").glob("*.wad.client") if p.name.count(".") == 2)
    for wad in champs:
        name = wad.name.split(".")[0]
        lo = name.lower()
        ents = index(wad)
        want = {
            "sfx_audio.bnk": f"assets/sounds/wwise2016/sfx/characters/{lo}/skins/base/{lo}_base_sfx_audio.bnk",
            "sfx_audio.wpk": f"assets/sounds/wwise2016/sfx/characters/{lo}/skins/base/{lo}_base_sfx_audio.wpk",
            "sfx_events.bnk": f"assets/sounds/wwise2016/sfx/characters/{lo}/skins/base/{lo}_base_sfx_events.bnk",
            "skin0.bin": f"data/characters/{lo}/skins/skin0.bin",
            "campeon.bin": f"data/characters/{lo}/{lo}.bin",
        }
        got = []
        with open(wad, "rb") as f:
            for short, path in want.items():
                e = ents.get(xxh64(path.lower().encode()))
                if e is None:
                    continue
                data = read(f, e)
                if data is None:
                    continue
                d = out / "campeones" / name
                d.mkdir(parents=True, exist_ok=True)
                (d / short).write_bytes(data)
                total += len(data)
                got.append(short)
        report["campeones"][name] = got
        print(f"{name:14s} {', '.join(got)}", flush=True)
    # 2) maps / shared: every sound bank (by content), and every small .bin that mentions sound events
    for wadname in ("Maps/Shipping/Map11.wad.client", "Maps/Shipping/Common.wad.client", "Global.wad.client"):
        wad = final / wadname
        if not wad.exists():
            continue
        ents = index(wad)
        tag = wad.name.split(".")[0]
        d = out / "mapas" / tag
        d.mkdir(parents=True, exist_ok=True)
        n_bnk = n_bin = 0
        with open(wad, "rb") as f:
            for h, e in ents.items():
                off, cs, sz, typ = e
                if sz > 60_000_000:
                    continue
                if typ == 0:
                    f.seek(off)
                    head = f.read(4)
                    if head not in (b"BKHD", b"r3d2"):
                        continue
                    data = read(f, e)
                elif typ in (3, 4) and sz < 3_000_000:
                    data = read(f, e)
                    if data is None or not (data[:4] in (b"BKHD", b"r3d2") or (data[:4] == b"PROP" and b"Play_" in data)):
                        continue
                else:
                    continue
                ext = {b"BKHD": "bnk", b"r3d2": "wpk", b"PROP": "bin"}[data[:4]]
                (d / f"{h:016x}.{ext}").write_bytes(data)
                total += len(data)
                n_bnk += ext != "bin"
                n_bin += ext == "bin"
        report["mapas"][tag] = dict(bancos=n_bnk, bins=n_bin)
        print(f"{tag}: {n_bnk} banks, {n_bin} event bins", flush=True)
    (out / "reporte.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"total {total / 1048576:.1f} MB -> {out}")


if __name__ == "__main__":
    main()
