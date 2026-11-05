"""Thin HTTP wrapper over the production scripts, called by n8n. One job at a time; n8n stays the orchestrator.
Run: python production\\studio_service.py   (http://127.0.0.1:8772). Standard library only."""
import json
import os
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RENDER_PY = str(ROOT / "render_env" / "Scripts" / "python.exe")
TTS_PY = str(ROOT.parent / "tts" / "env" / "Scripts" / "python.exe")
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
FINAL = ROOT / "output" / "hospital_prototipo.mp4"
SILENT = ROOT / "output" / "video_mudo.mp4"
lock = threading.Lock()


def run(cmd, timeout=1800):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode:
        raise RuntimeError(f"{cmd[1] if len(cmd) > 1 else cmd[0]} falló: {r.stderr[-800:] or r.stdout[-800:]}")
    return dict(seconds=round(time.time() - t0, 1), log=r.stdout[-400:])


def story(_):
    # Prototype: returns the hand-written story. There is no story-generation model behind this step yet.
    data = json.loads((ROOT / "story.json").read_text(encoding="utf-8"))
    return dict(source="fixed_prototype_story", title=data["title"], scenes=len(data["scenes"]))


def backgrounds(_):
    return run(["python", "gen_backgrounds.py"])


def assets(_):
    # The character is drawn by code in render.py, so there are no files to generate.
    return dict(character="render.py (rig vectorial)", generated=False)


def narration(_):
    # Uses the approved narration. Regenerating it would require re-tuning scene timing, so this step only checks it.
    wav, cues = ROOT / "audio" / "narracion.wav", ROOT / "cues.json"
    if not wav.exists() or not cues.exists():
        raise RuntimeError("Falta narracion.wav o cues.json; ejecuta narrate.py, tighten_audio.py y align_subs.py")
    return dict(audio_path=str(wav), cues=str(cues), bytes=wav.stat().st_size)


def animation(_):
    tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
    return dict(duration=tl["duration"], scenes=[dict(id=s["id"], bg=s["bg"], start=s["start"], end=s["end"]) for s in tl["scenes"]])


def render(_):
    step = run([RENDER_PY, "render.py", "--full"])
    run([RENDER_PY, "mix_audio.py"])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(SILENT), "-i", str(ROOT / "audio" / "mezcla.wav"), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(FINAL)], check=True)
    return dict(output=str(FINAL), render_seconds=step["seconds"])


def validate(_):
    run([TTS_PY, "qc.py"])
    q = json.loads((ROOT / "output" / "qc.json").read_text(encoding="utf-8"))
    checks = dict(resolution=q["resolution"] == "1280x720", fps=q["fps"] == "30/1", codecs=q["video_codec"] == "h264" and q["audio_codec"] == "aac",
                  duration=45 <= q["duration_s"] <= 60, no_black=not q["black_segments"], no_freezes=not q["freezes_over_2_5s"],
                  intelligible=q["word_error_rate"] <= .05, subtitles=(q["max_subtitle_offset_s"] or 9) <= .5)
    return dict(passed=all(checks.values()), checks=checks, report=str(ROOT / "output" / "qc.json"), output=q["file"])


ROUTES = {"/story": story, "/assets": assets, "/backgrounds": backgrounds, "/narration": narration, "/animation": animation, "/render": render, "/validate": validate}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.send(200, dict(status="ok", disk_free_gb=round(shutil.disk_usage(ROOT).free / 1e9, 1), steps=list(ROUTES)))

    def do_POST(self):
        fn = ROUTES.get(self.path.rstrip("/"))
        if not fn:
            return self.send(404, dict(status="error", error=f"Ruta desconocida: {self.path}"))
        size = int(self.headers.get("Content-Length") or 0)
        data = json.loads(self.rfile.read(size) or b"{}")
        if not lock.acquire(blocking=False):
            return self.send(409, dict(status="busy"))
        try:
            self.send(200, dict(status="completed", **fn(data)))
        except Exception as exc:
            self.send(500, dict(status="error", error=str(exc)))
        finally:
            lock.release()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8772), Handler).serve_forever()
