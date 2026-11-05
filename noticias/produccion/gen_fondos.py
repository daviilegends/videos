"""Generates backgrounds through the local ComfyUI API. Existing files are kept, so the folder works as an asset cache.
Usage: gen_backgrounds.py [name ...] [--force]"""
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
COMFY = Path(r"C:\videos-youtube\image\ComfyUI")
MIN_FREE_GB = 2.0
OUT = Path(__file__).resolve().parent / "assets" / "bg"
OUT.mkdir(parents=True, exist_ok=True)
W, H, STEPS = 1536, 864, 4

STYLE = ("Hand-drawn 2D cartoon background illustration for an animated news explainer, clean thick black ink outlines, flat colors "
         "with soft cel shading, rich detail, vibrant but natural palette, cinematic wide composition, polished professional animation art. "
         "Empty scene with no people, no text, no letters, no logos, no flags.")
SCENES = {
    "estudio": (501, "Modern TV news studio set at night, curved anchor desk, big blank screens glowing blue, city skyline through tall windows."),
    "golfo_noche": (503, "Dark sea at night seen from above a warship deck, distant rocky island with a few lights on the horizon, searchlights, moon reflections."),
    "isla": (507, "Desert island coastline at dusk on a turquoise sea, a small naval harbor with grey patrol boats, a large white industrial water desalination plant with pipes and tanks, rocky hills with bunker entrances."),
    "sala_prensa": (509, "Government press briefing room, wooden podium in the center, blue curtains, rows of empty chairs, soft spotlights."),
    "cielo_combate": (511, "Wide sky over the sea at sunset with scattered clouds and distant smoke trails, dramatic light."),
    "oficina_militar": (513, "Military command office, wall of dark monitors with blank radar screens, large map table with no labels, steel lockers."),
    "casilla": (515, "Polling station inside a school gym, voting booths with curtains, a transparent ballot box on a table, bunting in plain colors."),
    "casa_blanca": (517, "Classic white neoclassical mansion with columns seen across a green lawn, fountain, blue sky, autumn trees."),
    "pentagono": (519, "Aerial view of a huge five-sided government building surrounded by parking lots and highways, morning light."),
    "gasolinera": (521, "Gas station at dusk, fuel pumps under a lit canopy, empty road, price sign with blank panels."),
    "capitolio": (523, "Large white domed capitol building on a hill at sunset, wide steps, trees on both sides."),
    "mesa_negociacion": (525, "Elegant negotiation room, long table with two chairs facing each other, tall windows with light, folders on the table."),
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
    log = (Path(r"C:\videos-youtube\logs") / "comfy.log").open("w", encoding="utf-8")
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
names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(SCENES)
pending = [n for n in names if force or not (OUT / f"{n}.png").exists()]
print("en cache:", [n for n in names if n not in pending], flush=True)
server = start_server() if pending else None
atexit.register(lambda: server and server.kill())
for name in pending:
    target = OUT / f"{name}.png"
    seed, desc = SCENES[name]
    t0 = time.time()
    pid = post("/prompt", {"prompt": workflow(f"{desc} {STYLE}", seed, name)})["prompt_id"]
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
