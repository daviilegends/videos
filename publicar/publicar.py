"""Publishing queues for n8n: one queue and one agenda per project, and the state of every video on every platform.

    python publicar.py programar                           videos to upload now to platforms that schedule (YouTube, Facebook)
    python publicar.py vencidos                            videos whose time has come on platforms that cannot schedule (TikTok)
    python publicar.py registrar PROYECTO SLUG PLATAFORMA ID   marks one platform as done
    python publicar.py estado                              what is uploaded and what is not, per project

A queued video is a folder in <proyecto>\\cola holding video.mp4 and metadata.json. Its slot is reserved in the
project's agenda.json before any upload, so two clicks never give two videos of the same channel the same time.
Its estado.json records each platform; when every active platform is done the folder moves to <proyecto>\\subidos.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
TZ = timezone(timedelta(hours=CONFIG["utc_offset_horas"]))
sys.stdout.reconfigure(encoding="utf-8")


def read(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def active(project):
    return [name for name, p in CONFIG["proyectos"][project]["plataformas"].items() if p["activo"]]


def slots(project, after):
    """Publishing times from the project's daily hours, starting after the given moment."""
    day = after.date()
    while True:
        for hour in CONFIG["proyectos"][project]["horarios"]:
            h, m = map(int, hour.split(":"))
            slot = datetime(day.year, day.month, day.day, h, m, tzinfo=TZ)
            if slot > after:
                yield slot
        day += timedelta(days=1)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    return float(out.stdout.strip() or 0)


def problems(meta, video):
    found = []
    if not video.exists():
        found.append("falta video.mp4")
    elif duration(video) > CONFIG["duracion_maxima_s"]:
        found.append(f"dura más de {CONFIG['duracion_maxima_s']} s")
    if not 0 < len(meta.get("titulo", "")) <= 100:
        found.append("el título debe tener de 1 a 100 caracteres")
    if len(meta.get("descripcion", "")) > 2000:
        found.append("la descripción pasa de 2000 caracteres")
    if len(",".join(meta.get("tags", []))) > 450:
        found.append("los tags pasan de 450 caracteres")
    return found


def queued(project):
    """Each valid video in the project's queue with its state, after reserving a slot for it."""
    folder = ROOT / project / "cola"
    agenda_path = ROOT / project / "agenda.json"
    agenda = read(agenda_path, [])
    earliest = datetime.now(TZ) + timedelta(minutes=CONFIG["anticipacion_minutos"])
    out, skipped = [], []
    for video_dir in sorted(p for p in folder.iterdir() if p.is_dir()):
        meta_path, video = video_dir / "metadata.json", video_dir / "video.mp4"
        if not meta_path.exists():
            continue
        meta = read(meta_path, {})
        found = problems(meta, video)
        if found:
            skipped.append(dict(proyecto=project, slug=video_dir.name, problemas=found))
            continue
        state = read(video_dir / "estado.json", {"plataformas": {}})
        started = any(p.get("estado") == "hecho" for p in state["plataformas"].values())
        # A slot from a failed attempt is reused while it is still ahead; once something is published it is kept.
        # A slot set by hand ("fijo": true) is always kept.
        if state.get("slot") and not started and not state.get("fijo") and datetime.fromisoformat(state["slot"]) < earliest:
            agenda = [e for e in agenda if e["slug"] != video_dir.name]
            state.pop("slot")
        if not state.get("slot"):
            taken = {e["slot"] for e in agenda}
            state["slot"] = next(s for s in slots(project, earliest) if s.isoformat() not in taken).isoformat()
            agenda.append(dict(slot=state["slot"], slug=video_dir.name))
        write(video_dir / "estado.json", state)
        out.append((video_dir, meta, state))
    write(agenda_path, sorted(agenda, key=lambda e: e["slot"]))
    return out, skipped


def description(conf, meta, hashtags):
    """Video description + hashtags + the project's fixed footer (e.g. Riot's fan-content notice for League)."""
    text = f"{meta['descripcion']}\n\n{hashtags}".strip()
    if conf.get("pie_descripcion"):
        text += "\n\n" + conf["pie_descripcion"].replace("{titulo}", meta["titulo"])
    return text


def item(project, platform, video_dir, meta, state):
    conf = CONFIG["proyectos"][project]
    pconf = conf["plataformas"][platform]
    slot = datetime.fromisoformat(state["slot"])
    video = video_dir / "video.mp4"
    hashtags = " ".join(conf["hashtags"])
    return dict(
        ruta=f"{project}/{platform}", proyecto=project, plataforma=platform, slug=video_dir.name,
        archivo=str(video), tamano=video.stat().st_size, titulo=meta["titulo"],
        descripcion=description(conf, meta, hashtags), texto_corto=f"{meta['titulo']} {hashtags}".strip(),
        tags=",".join(meta["tags"]), categoria=conf["categoria_youtube"], publishAt=slot.isoformat(), publish_unix=int(slot.timestamp()),
        page_id=pconf.get("page_id", ""), privacidad=pconf.get("privacidad", ""),
    )


def pending(scheduled):
    """Items for platforms that schedule (scheduled=True), or for the others once their slot has arrived."""
    now = datetime.now(TZ)
    items, skipped = [], []
    for project in CONFIG["proyectos"]:
        videos, bad = queued(project)
        skipped += bad
        for video_dir, meta, state in videos:
            for platform in active(project):
                if CONFIG["proyectos"][project]["plataformas"][platform]["programa"] != scheduled:
                    continue
                if state["plataformas"].get(platform, {}).get("estado") == "hecho":
                    continue
                if not scheduled and datetime.fromisoformat(state["slot"]) > now:
                    continue
                items.append(item(project, platform, video_dir, meta, state))
    print(json.dumps(dict(videos=items, omitidos=skipped), ensure_ascii=False))


def register(project, slug, platform, ident):
    video_dir = ROOT / project / "cola" / slug
    state = read(video_dir / "estado.json", None)
    if state is None:
        raise SystemExit(f"No está en la cola: {project}/{slug}")
    state["plataformas"][platform] = dict(estado="hecho", id=ident, fecha=datetime.now(TZ).isoformat(timespec="seconds"))
    write(video_dir / "estado.json", state)
    finished = all(state["plataformas"].get(p, {}).get("estado") == "hecho" for p in active(project))
    if finished:
        done = ROOT / project / "subidos"
        done.mkdir(exist_ok=True)
        video_dir.rename(done / slug)
    print(json.dumps(dict(correcto=True, proyecto=project, slug=slug, plataforma=platform, id=ident, terminado=finished), ensure_ascii=False))


def status():
    for project in CONFIG["proyectos"]:
        platforms = active(project)
        print(f"\n== {project}  ({', '.join(platforms)})")
        for where in ("cola", "subidos"):
            folder = ROOT / project / where
            for video_dir in sorted(p for p in folder.iterdir() if p.is_dir()) if folder.exists() else []:
                state = read(video_dir / "estado.json", {"plataformas": {}})
                marks = "  ".join(f"{p}:{'✔' if state['plataformas'].get(p, {}).get('estado') == 'hecho' else '·'}" for p in platforms)
                print(f"  {where:8} {state.get('slot', 'sin horario'):26} {marks}  {video_dir.name}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["programar"]:
        pending(True)
    elif args == ["vencidos"]:
        pending(False)
    elif len(args) == 5 and args[0] == "registrar":
        register(*args[1:])
    elif args == ["estado"]:
        status()
    else:
        raise SystemExit(__doc__)
