"""Lists the smallest catalog matches per query group. Usage: python -I candidates.py"""
import json
import re
from pathlib import Path

catalog = json.loads((Path(__file__).resolve().parent / "catalog.json").read_text(encoding="utf-8"))
QUERIES = {
    "pasos": r"foot ?steps?.*(concrete|tile|wood|hard|stone|shoe|sneaker)",
    "puerta": r"\bdoor",
    "cerradura": r"\block|handle|latch",
    "interior": r"bunker|room ?tone|basement|cellar|abandon",
    "crujido": r"creak",
    "tension": r"drone|tension|dark|horror|eerie",
    "golpe": r"knock|thud|hit.*(wood|door)|bang",
    "tiza": r"chalk|scribbl|writ",
    "luz": r"fluorescent|neon|flicker|\bhum\b",
}
for label, query in QUERIES.items():
    found = [i for i in catalog if re.search(query, i["original"].replace("_", " "), re.I)]
    print("==", label, len(found))
    for item in sorted(found, key=lambda x: x["mb"])[:9]:
        print(f"  {item['mb']:6.1f} {re.split(r'[\\/]', item['original'])[-1][:85]}")
