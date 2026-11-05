"""Finds and decodes Summoner's Rift sounds (turrets, minions, gold, recall) from the extracted map banks.
Usage: py -3.14 -I sonidos_mapa.py  -> assets/sonidos_lol/wav/_mapa/<event>__<n>.wav + indice.json"""
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sonidos_lol import didx, event_actions, fnv1, hirc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MAPAS = ROOT / "assets" / "sonidos_lol" / "mapas"
OUT = ROOT / "assets" / "sonidos_lol" / "wav" / "_mapa"
VGM = Path(__file__).resolve().parent / "vgmstream" / "vgmstream-cli.exe"
WANT = re.compile(r"(map11_(Order|Chaos)Turret(Champion|Minion)BasicAttack|Env_TurretChampionBasicAttack|SRU_(Order|Chaos)Minion"
                  r"(Melee|Ranged|Siege)_|GoldAquisition|Recall_Shared|Recall_return|ENV_(Order|Chaos)Turret_break|SummonerFlash|SummonerTeleport|SummonerDot|SightWard_SightWardAudioBuff_OnBuffActivate|BlueTrinket|Brush_OnMovement|SRU_Dragon_death_cast|SRU_Dragon_DragonFireball_hit|SRU_Dragon_DragonTakeOff|SRU_Dragon_Elder_death_vox|Death_Self|SRU_Crab_death_pop)", re.I)


def main():
    names = set()
    for f in MAPAS.glob("*/*.bin"):
        names |= {m.decode() for m in re.findall(rb"Play_[A-Za-z0-9_]+", f.read_bytes())}
    targets = {fnv1(n): n for n in names if WANT.search(n)}
    print(len(targets), "target events")
    objs, media_bank, events = {}, {}, {}
    banks = sorted(MAPAS.glob("*/*.bnk"))
    for k, b in enumerate(banks):
        data = b.read_bytes()
        for m in didx(data):
            media_bank.setdefault(m, b)
        o = hirc(data)
        for oid, (typ, p) in o.items():
            if typ == 4 and oid in targets:
                events[oid] = (p, o)
        objs.update({oid: v for oid, v in o.items() if v[0] in (2, 3, 5, 6, 9)})
        if k % 1500 == 0:
            print(f"  {k}/{len(banks)} banks", flush=True)
    print(len(events), "events found")

    def media_of(oid, seen):
        if oid in seen or oid not in objs:
            return set()
        seen.add(oid)
        typ, p = objs[oid]
        if typ == 2:
            sid = struct.unpack_from("<I", p, 5)[0]
            return {sid} if sid in media_bank else set()
        out = set()
        for j in range(len(p) - 3):
            v = struct.unpack_from("<I", p, j)[0]
            if v != oid and v in objs and objs[v][0] in (2, 5, 6, 9):
                out |= media_of(v, seen)
        return out

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    tmp = OUT / "_tmp"
    decoded = {}
    index = {}
    for eid, (p, local) in events.items():
        name = targets[eid]
        allobjs = dict(objs)
        allobjs.update(local)
        mids = set()
        for a in event_actions(allobjs, p):
            ap = allobjs[a][1]
            if len(ap) >= 6:
                mids |= media_of(struct.unpack_from("<I", ap, 2)[0], set())
        files = []
        for n, m in enumerate(sorted(mids)):
            bank = media_bank[m]
            if bank not in decoded:
                d = tmp / bank.stem
                d.mkdir(parents=True, exist_ok=True)
                subprocess.run([str(VGM), "-S", "0", "-o", str(d / "?n.wav"), str(bank)], capture_output=True)
                decoded[bank] = d
            src = decoded[bank] / f"{m}.wav"
            if src.exists():
                dst = OUT / f"{name}__{n}.wav"
                shutil.copy(src, dst)
                files.append(dst.name)
        if files:
            index[name] = files
            print(f"{name}: {len(files)}", flush=True)
    shutil.rmtree(tmp, ignore_errors=True)
    (OUT / "indice.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    print("ok", OUT)


if __name__ == "__main__":
    main()
