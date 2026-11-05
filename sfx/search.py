"""Searches catalog.json by regular expression. Usage: python -I search.py "regex" [limit]"""
import json
import re
import sys
from pathlib import Path

catalog = json.loads((Path(__file__).resolve().parent / "catalog.json").read_text(encoding="utf-8"))
query = re.compile(sys.argv[1], re.I)
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 15
found = [i for i in catalog if query.search(i["original"].replace("_", " "))]
print(len(found), "resultados")
for item in found[:limit]:
    print(f"{item['mb']:8.2f} MB  {Path(item['path']).name}  [{Path(item['path']).parent.name}]")
