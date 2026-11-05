"""Turns the extracted LoL banks into named .wav files.
For each champion: event names (from the .bin files) -> FNV-1 hash -> Wwise events (sfx_events.bnk) -> actions -> sounds/containers
-> media ids (.wem) -> decoded by vgmstream from sfx_audio.bnk.
Usage: py -3.14 -I sonidos_lol.py Caitlyn Draven ...   (or 'todos')
Output: assets/sonidos_lol/wav/<Champion>/<event>__<n>.wav + indice.json"""
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "sonidos_lol" / "campeones"
OUT = ROOT / "assets" / "sonidos_lol" / "wav"
VGM = Path(__file__).resolve().parent / "vgmstream" / "vgmstream-cli.exe"


def fnv1(name):
    h = 2166136261
    for b in name.lower().encode():
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= b
    return h


def chunks(data):
    i = 0
    while i + 8 <= len(data):
        tag, size = data[i:i + 4], struct.unpack_from("<I", data, i + 4)[0]
        yield tag, data[i + 8:i + 8 + size]
        i += 8 + size


def hirc(data):
    objs = {}
    for tag, body in chunks(data):
        if tag != b"HIRC":
            continue
        (n,) = struct.unpack_from("<I", body, 0)
        i = 4
        for _ in range(n):
            typ = body[i]
            (size,) = struct.unpack_from("<I", body, i + 1)
            (oid,) = struct.unpack_from("<I", body, i + 5)
            objs[oid] = (typ, body[i + 9:i + 5 + size])
            i += 5 + size
    return objs


def didx(data):
    ids = []
    for tag, body in chunks(data):
        if tag == b"DIDX":
            for j in range(0, len(body), 12):
                ids.append(struct.unpack_from("<I", body, j)[0])
    return ids


def media_of(objs, oid, media_ids, seen=None):
    """Media ids reachable from object oid (sound -> its source; container -> children)."""
    seen = seen or set()
    if oid in seen or oid not in objs:
        return set()
    seen.add(oid)
    typ, p = objs[oid]
    out = set()
    if typ == 2 and len(p) >= 9:  # sound: plugin u32, stream type u8, source id u32
        sid = struct.unpack_from("<I", p, 5)[0]
        if sid in media_ids:
            out.add(sid)
        return out
    # containers and others: any u32 inside that is a known object id or media id
    for j in range(0, len(p) - 3):
        v = struct.unpack_from("<I", p, j)[0]
        if v != oid and v in objs and objs[v][0] in (2, 5, 6, 9):
            out |= media_of(objs, v, media_ids, seen)
        elif v in media_ids and typ == 2:
            out.add(v)
    return out


def event_actions(objs, p):
    for fmt, w in (("<B", 1), ("<I", 4)):
        (n,) = struct.unpack_from(fmt, p, 0)
        if 0 < n < 64 and len(p) >= w + 4 * n:
            ids = [struct.unpack_from("<I", p, w + 4 * k)[0] for k in range(n)]
            if all(a in objs and objs[a][0] == 3 for a in ids):
                return ids
    return []


def process(champ):
    d = SRC / champ
    events_bnk, audio_bnk = d / "sfx_events.bnk", d / "sfx_audio.bnk"
    if not (events_bnk.exists() and audio_bnk.exists()):
        return None
    names = set()
    for b in d.glob("*.bin"):
        names |= {m.decode() for m in re.findall(rb"Play_[A-Za-z0-9_]+", b.read_bytes())}
    audio = audio_bnk.read_bytes()
    media = didx(audio)
    media_ids = set(media)
    objs = hirc(events_bnk.read_bytes())
    objs.update(hirc(audio))
    by_hash = {fnv1(n): n for n in names}
    out_dir = OUT / champ
    tmp = out_dir / "_tmp"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    tmp.mkdir(parents=True)
    subprocess.run([str(VGM), "-S", "0", "-o", str(tmp / "?n.wav"), str(audio_bnk)], check=True, capture_output=True)
    index = {}
    used = set()
    for eid, (typ, p) in objs.items():
        if typ != 4 or eid not in by_hash:
            continue
        name = by_hash[eid]
        mids = set()
        for a in event_actions(objs, p):
            atyp, ap = objs[a]
            if len(ap) >= 6:
                target = struct.unpack_from("<I", ap, 2)[0]
                mids |= media_of(objs, target, media_ids)
        files = []
        for k, m in enumerate(sorted(mids)):
            src = tmp / f"{m}.wav"
            if src.exists():
                dst = out_dir / f"{name}__{k}.wav"
                shutil.copy(src, dst)
                files.append(dst.name)
                used.add(m)
        if files:
            index[name] = files
    # sounds that no event points to: keep them with their id
    for m in media:
        if m not in used and (tmp / f"{m}.wav").exists():
            shutil.move(str(tmp / f"{m}.wav"), str(out_dir / f"_sin_nombre_{m}.wav"))
    shutil.rmtree(tmp)
    (out_dir / "indice.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    return len(index), len(media), len(used)


if __name__ == "__main__":
    champs = sys.argv[1:]
    if champs == ["todos"]:
        champs = sorted(p.name for p in SRC.iterdir() if p.is_dir())
    for ch in champs:
        r = process(ch)
        print(f"{ch:14s} " + ("no audio" if r is None else f"{r[0]} named events, {r[2]}/{r[1]} sounds identified"), flush=True)
