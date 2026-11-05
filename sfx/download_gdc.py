"""Downloads a Sonniss GDC bundle from its official mirror, one part at a time. Keeps audio only; finished parts are skipped on re-run.
Usage: python -I download_gdc.py"""
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIB = ROOT / "library" / "gdc2017"
BASE = "https://ftpmirror.your.org/pub/misc/sonniss2017/"
NAME = "Sonniss.com - GDC 2017 - Game Audio Bundle Part {}of9.zip"
AUDIO = {".wav", ".flac", ".aif", ".aiff", ".ogg", ".mp3"}
INVALID = re.compile(r'[<>:"|?*\x00-\x1f]')
MIN_FREE_GB = 15
LIB.mkdir(parents=True, exist_ok=True)


def safe_path(name):
    """Bundle folders can contain tabs or trailing spaces, which Windows rejects; ".." and empty parts are dropped."""
    parts = [INVALID.sub(" ", p).strip().rstrip(".") for p in re.split(r"[\\/]", name)]
    parts = [p for p in parts if p and p != ".."]
    # Windows' 260-character path limit: keep short names on disk; names.jsonl keeps the originals for the catalog.
    parts[0] = re.sub(r".*Part (\d)of9$", r"Part \1", parts[0])
    tag = f"{zlib.crc32(name.encode('utf-8')):08x}"
    stem, suffix = Path(parts[-1]).stem, Path(parts[-1]).suffix
    if len(parts[-1]) > 90:
        parts[-1] = f"{stem[:75].strip()} {tag}{suffix}"
    parts[:-1] = [p if len(p) <= 50 else f"{p[:41].strip()} {zlib.crc32(p.encode('utf-8')):08x}" for p in parts[:-1]]
    return LIB.joinpath(*parts)


def free_gb():
    return shutil.disk_usage(ROOT).free / 1e9


for part in range(1, 10):
    done = LIB / f".part{part}.done"
    if done.exists():
        print(f"parte {part}: ya estaba", flush=True)
        continue
    if free_gb() < MIN_FREE_GB + 5:
        sys.exit(f"DETENIDO antes de la parte {part}: {free_gb():.1f} GB libres")
    target = ROOT / f"part{part}.zip"
    url = BASE + urllib.parse.quote(NAME.format(part))
    if not (target.exists() and zipfile.is_zipfile(target)):
        r = subprocess.run(["curl", "-sS", "-f", "-L", "-C", "-", "--retry", "5", "--retry-delay", "20", "--connect-timeout", "30", "-o", str(target), url])
        if r.returncode:
            sys.exit(f"DETENIDO: la descarga de la parte {part} falló (curl {r.returncode}); volver a ejecutar continúa donde quedó")
    kept = size = 0
    with zipfile.ZipFile(target) as z:
        bad = z.testzip()
        if bad:
            sys.exit(f"DETENIDO: archivo dañado en la parte {part}: {bad}")
        for info in z.infolist():
            if not info.is_dir() and Path(info.filename).suffix.lower() in AUDIO:
                dest = safe_path(info.filename)
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, dest.open("wb") as out:
                    shutil.copyfileobj(src, out)
                with (ROOT / "library" / "names.jsonl").open("a", encoding="utf-8") as log:
                    log.write(json.dumps(dict(path=str(dest.relative_to(ROOT / "library")), original=info.filename), ensure_ascii=False) + "\n")
                kept += 1
                size += info.file_size
    target.unlink()
    done.touch()
    print(f"parte {part}: {kept} audios, {size / 1e9:.2f} GB, {free_gb():.1f} GB libres", flush=True)
print("completo", flush=True)
