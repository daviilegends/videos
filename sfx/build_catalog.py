"""Indexes the sound library by file and folder names only (audio content is not used for any training).
Writes catalog.json, and catalog_summary.txt with the matches per topic. Usage: python -I build_catalog.py"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIB = ROOT / "library"
AUDIO = {".wav", ".flac", ".aif", ".aiff", ".ogg", ".mp3"}
TOPICS = {
    "pisadas": r"foot ?steps?|footfall|walk(ing)?\b|boots?\b.*(step|walk)",
    "puertas": r"\bdoors?\b|gate\b",
    "cerraduras": r"\blocks?\b|unlock|latch|deadbolt|door ?handle|door ?knob",
    "llaves": r"\bkeys?\b|keyring|key ?chain",
    "vidrio": r"\bglass\b|shatter|window ?break",
    "bocinas_carro": r"\bhonk|car ?horn|\bhorn\b.*(car|vehicle)|(car|vehicle).*\bhorn\b",
    "carros": r"\bcars?\b|vehicle|engine|traffic",
    "golpes": r"\bknock|\bthud|\bslam|\bimpact",
    "crujidos": r"\bcreak|squeak",
    "metal": r"\bmetal\b|\bchain\b|\bsteel\b",
    "ambiente_interior": r"room ?tone|ambien(ce|t).*(hospital|interior|room|building|corridor)|hospital|corridor|hallway",
    "electricidad_zumbido": r"\bhum\b|\bbuzz|fluorescent|electric",
    "corazon": r"heart ?beat|heartbeat",
    "lluvia_viento": r"\brain\b|\bwind\b|thunder",
    "agua": r"\bwater\b|splash|\bdrip",
    "construccion": r"construction|hammer|drill|excavator|concrete|\bsaw\b",
    "suspenso_musical": r"\bdrone\b|\briser\b|\bstinger\b|tension|suspense",
    "interfaz_transiciones": r"whoosh|\bswish\b|\bswoosh\b|\bui\b|\bpop\b",
}
RULES = {k: re.compile(v, re.I) for k, v in TOPICS.items()}


def plain(path):
    t = "".join(c for c in unicodedata.normalize("NFD", str(path)) if unicodedata.category(c) != "Mn")
    return re.sub(r"[_\-.]+", " ", t)


items, counts, samples = [], {k: 0 for k in TOPICS}, {k: [] for k in TOPICS}
size = 0
names = {}
log = LIB / "names.jsonl"
if log.exists():
    for line in log.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        names[row["path"]] = row["original"]
for f in LIB.rglob("*"):
    if not f.is_file() or f.suffix.lower() not in AUDIO:
        continue
    rel = f.relative_to(LIB)
    original = names.get(str(rel), str(rel))
    text = plain(original)
    tags = [k for k, r in RULES.items() if r.search(text)]
    b = f.stat().st_size
    size += b
    items.append(dict(path=str(rel), original=original, tags=tags, mb=round(b / 1e6, 2)))
    for k in tags:
        counts[k] += 1
        if len(samples[k]) < 3:
            samples[k].append(rel.name)
(ROOT / "catalog.json").write_text(json.dumps(items, ensure_ascii=False, indent=0), encoding="utf-8")
lines = [f"archivos {len(items)}, {size / 1e9:.1f} GB, sin etiqueta {sum(1 for i in items if not i['tags'])}"]
for k in TOPICS:
    lines.append(f"{k}: {counts[k]} | " + " ; ".join(samples[k]))
(ROOT / "catalog_summary.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
