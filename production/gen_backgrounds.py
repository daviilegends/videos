"""Generates backgrounds through the local ComfyUI API. Existing files are kept, so the folder works as an asset cache.
Usage: gen_backgrounds.py [name ...] [--force] [--ep <episode folder>]
With --ep, the scenes come from <episode>/fondos.json ({"estilo": optional, "fondos": {name: [seed, description, optional style]}})
and the images go to <episode>/bg."""
import atexit
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8188"
ROOT = Path(__file__).resolve().parent
COMFY = ROOT.parent / "image" / "ComfyUI"
MIN_FREE_GB = 2.0
OUT = ROOT / "assets" / "bg"
OUT.mkdir(parents=True, exist_ok=True)
W, H, STEPS = 1536, 864, 4

STYLE = (
    "Hand-drawn 2D cartoon background illustration, thick slightly irregular black ink outlines, flat colors with soft "
    "cel shading, graphic novel web cartoon style. Very dark low-key night scene, deep shadows covering most of the "
    "image, walls and floor in dark slate teal and charcoal, only small pools of dim light, moody horror atmosphere, "
    "muted desaturated teal, gray, green and brown palette, highly detailed environment, wide cinematic composition. "
    "Empty scene with no people, no characters, no text, no letters."
)
SCENES = {
    "lobby": (101, "Lobby of an old apartment building at night, frontal view. Closed brushed steel elevator double doors centered on the back wall, unlit call button panel beside them, empty arrow indicator above, worn tiled floor completely clear in the foreground, one dim ceiling lamp, row of closed metal mailboxes on the side wall."),
    "cabina": (113, "Inside a small old elevator cabin, frontal view of the back wall. Scratched brushed steel walls, metal handrail across the back wall, rectangular fluorescent ceiling panel, plain dark floor, narrow cramped space, cold greenish light."),
    "panel": (127, "Extreme close-up of an old elevator control panel on a steel wall. Two neat vertical columns of round blank metal push buttons with no markings, a small speaker grille, screws at the corners, scratches and fingerprints, cold light."),
    "techo": (131, "Looking straight up at the ceiling of an old elevator from inside. Flickering rectangular fluorescent light panel in the middle, small square ventilation grille with slats beside it, scratched steel ceiling, dark corners."),
    "hueco": (163, "Front cutaway view inside a tall narrow concrete elevator shaft. A small elevator car in the middle of the frame, hanging from thick steel cables that go straight up to a big pulley wheel at the very top of the shaft. Two vertical steel guide rails run the full height on both sides, touching the car. Concrete shaft walls close to the car on both sides, closed metal landing doors of the floors above and below on the back wall, a counterweight block hanging on its own cables beside the car, faint light leaking from the car door seam."),
    "hueco2": (171, "Front cutaway view inside a tall narrow concrete elevator shaft. A small elevator car in the middle of the frame, hanging from thick steel cables that go straight up to a big pulley wheel at the very top of the shaft. Two vertical steel guide rails run the full height on both sides, touching the car. Concrete shaft walls close to the car on both sides, closed metal landing doors of the floors above and below on the back wall, a counterweight block hanging on its own cables beside the car, faint light leaking from the car door seam."),
    "puertas": (149, "Inside an old elevator, frontal view of the closed brushed steel double doors with a dark vertical seam in the middle, scratches and dents, steel door frame, plain dark floor, cold greenish light."),
    "rejilla": (151, "Close-up of a square metal ventilation grille with slanted slats in the steel wall of an elevator, dust on the slats, darkness behind the slats, screws at the corners, cold light."),
}


def post(path, body):
    req = urllib.request.Request(API + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def workflow(prompt, seed, name):
    return {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-schnell-Q4_K_S.gguf"}},
        "2": {"class_type": "DualCLIPLoaderGGUF", "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5-v1_1-xxl-encoder-Q3_K_L.gguf", "type": "flux"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "split_files\\vae\\ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "EmptySD3LatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0],
                                                    "seed": seed, "steps": STEPS, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "8": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["7", 0], "vae": ["3", 0], "tile_size": 512, "overlap": 64,
                                                          "temporal_size": 64, "temporal_overlap": 8}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": name}},
    }


def start_server():
    # This script owns the server, so memory and page file growth end with it. The VAE runs on the CPU because
    # moving the GGUF model off the GPU crashes on this machine.
    log = (ROOT.parent / "logs" / "comfy.log").open("w", encoding="utf-8")
    proc = subprocess.Popen([str(COMFY.parent / "env" / "Scripts" / "python.exe"), "main.py", "--listen", "127.0.0.1", "--port", "8188",
                             "--disable-auto-launch", "--cpu-vae", "--cache-none"], cwd=COMFY, stdout=log, stderr=log)
    for _ in range(120):
        try:
            urllib.request.urlopen(f"{API}/system_stats", timeout=2)
            return proc
        except OSError:
            if proc.poll() is not None:
                raise SystemExit(f"ComfyUI terminó al arrancar con código {proc.returncode}")
            time.sleep(1)
    proc.kill()
    raise SystemExit("ComfyUI no respondió")


def check_disk():
    free = shutil.disk_usage("C:\\").free / 1e9
    if free < MIN_FREE_GB:
        raise SystemExit(f"DETENIDO: solo quedan {free:.1f} GB libres en C:")


force = "--force" in sys.argv
args = sys.argv[1:]
if "--ep" in args:
    ep = Path(args.pop(args.index("--ep") + 1)); args.remove("--ep")
    spec = json.loads((ep / "fondos.json").read_text(encoding="utf-8"))
    SCENES = {k: tuple(v) for k, v in spec["fondos"].items()}
    STYLE = spec.get("estilo", STYLE)
    OUT = ep / "bg"
    OUT.mkdir(parents=True, exist_ok=True)
names = [a for a in args if not a.startswith("--")] or list(SCENES)
pending = [n for n in names if force or not (OUT / f"{n}.png").exists()]
print("en cache:", [n for n in names if n not in pending], flush=True)
server = start_server() if pending else None
atexit.register(lambda: server and server.kill())
for name in pending:
    target = OUT / f"{name}.png"
    seed, desc, *own_style = SCENES[name]  # an optional third field replaces the episode style for this background
    t0 = time.time()
    pid = post("/prompt", {"prompt": workflow(f"{desc} {own_style[0] if own_style else STYLE}", seed, name)})["prompt_id"]
    while True:
        check_disk()
        if server.poll() is not None:
            raise SystemExit(f"ComfyUI se cayó con código {server.returncode}")
        hist = json.load(urllib.request.urlopen(f"{API}/history/{pid}"))
        if pid in hist and hist[pid].get("status", {}).get("completed") is not None or (pid in hist and hist[pid].get("outputs")):
            break
        if pid in hist and hist[pid].get("status", {}).get("status_str") == "error":
            raise SystemExit(json.dumps(hist[pid]["status"])[:1500])
        time.sleep(2)
    if not hist[pid].get("outputs"):
        raise SystemExit(json.dumps(hist[pid].get("status"))[:1500])
    info = hist[pid]["outputs"]["9"]["images"][0]
    url = f"{API}/view?filename={info['filename']}&type=output"
    target.write_bytes(urllib.request.urlopen(url).read())
    print(name, f"{time.time() - t0:.0f}s", flush=True)
