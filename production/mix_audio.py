"""Mixes room tone and effects from the sound library under the narration, on the same beats as render.py."""
import json
import subprocess
from pathlib import Path, PureWindowsPath

import numpy as np
import soundfile as sf

from layout import beats

ROOT = Path(__file__).resolve().parent
LIBRARY = ROOT.parent / "sfx" / "library"
CATALOG = {PureWindowsPath(i["path"]).name: i["path"] for i in json.loads((ROOT.parent / "sfx" / "catalog.json").read_text(encoding="utf-8"))}
voice, sr = sf.read(ROOT / "audio" / "narracion.wav", dtype="float32")
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
n = len(voice)
t = np.arange(n) / sr
BT = beats(tl)
LINES = BT["lines"]

BED = "ambient bunker big space inside small room moving noises stereo M10.wav"
MECHANISM = "elevator_mechanism_002_wide.wav"
DOOR = "soviet_elevator_door_close_001.wav"
BUTTON = "Pressing Buttons 6.wav"
HUM = "electric_hum_buzz_01.wav"
STEPS = "015_Foley_Footsteps_Asphalt_Boot_Walk_Fast_Run_Jog_Close.wav"
STEP_ONSETS = (.34, .64, .96, 1.26, 1.58, 1.9, 2.84, 3.16, 3.48)
IMPACT = "Bluezone-BC0226-hit-impact-004.wav"
STRAIN = "Metal_Door_Squeak_Creak_03.wav"
BREATH = "scared breath 12.wav"
VENT = "Hvac,Ventilation,Exhaust,Industrial,Drone,Slight rumble,Loop.wav"
KNOCK = "Massey_Foley_Door_Closing_Int.wav"


def load(name, start=0.0, dur=None, af=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start)]
    if dur:
        cmd += ["-t", str(dur)]
    cmd += ["-i", str(LIBRARY / CATALOG[name])]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "2", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def peak(x, level=1.0):
    return x * level / max(np.abs(x).max(), 1e-6)


def rms(x, level):
    return x * level / max(np.sqrt((x ** 2).mean()), 1e-6)


def edges(x, fade_in=.003, fade_out=.04):
    a, b = int(sr * fade_in), min(len(x), int(sr * fade_out))
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None]
    x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def around_peak(name, before=.03, after=.9, af=None):
    x = load(name, af=af)
    i = int(np.abs(x).sum(axis=1).argmax())
    return edges(peak(x[max(0, i - int(sr * before)):i + int(sr * after)]), .002, .2)


def loop_to(x, length, cross=1.0):
    c = int(sr * cross)
    ramp = np.linspace(0, np.pi / 2, c)[:, None]
    out = x
    while len(out) < length:
        out = np.concatenate([out[:-c], out[-c:] * np.cos(ramp) + x[:c] * np.sin(ramp), x[c:]])
    return out[:length]


def place(track, clip, at, gain=1.0):
    i = int(at * sr)
    end = min(n, i + len(clip))
    if 0 <= i < n:
        track[i:end] += clip[: end - i] * gain


def window(a, b, fade=.15):
    """Envelope that is 1 between a and b, with short fades."""
    return (np.clip((t - a) / fade, 0, 1) * np.clip((b - t) / fade, 0, 1))[:, None].astype(np.float32)


fx = np.zeros((n, 2), dtype=np.float32)
ambience = rms(loop_to(load(BED), n), .009).astype(np.float32)

# footsteps while walking to the doors
raw = load(STEPS, af="highpass=f=70,lowpass=f=7000")
clips = [edges(peak(raw[int(o * sr):int((o + .27) * sr)]), .001, .1) for o in STEP_ONSETS]
rng = np.random.default_rng(7)
at, stop = .35, BT["press"] - .2
while at < stop:
    place(fx, clips[rng.integers(len(clips))], at, .1 * rng.uniform(.8, 1))
    at += np.pi / 6

place(fx, edges(peak(load(DOOR)), .005, .2), BT["door_open"], .16)
place(fx, edges(peak(load(BUTTON, 0, .5)), .002, .05), BT["press_hit"], .3)

# the motor runs from the moment it starts rising until the hit, then stops dead
motor = peak(loop_to(load(MECHANISM), n, .5), .1)
fx += motor * window(BT["rise"] - .3, BT["hit"], .25)

hit_clip = around_peak(IMPACT, after=1.1)
place(fx, hit_clip, BT["hit"], .75)
d = np.arange(int(sr * 1.2)) / sr
place(fx, np.stack([np.sin(2 * np.pi * 44 * d) * np.exp(-d * 3.6)] * 2, axis=1).astype(np.float32), BT["hit"], .6)
place(fx, around_peak(IMPACT, after=.6), BT["halt"], .22)

# the tube buzzes only while it flickers
hum = peak(loop_to(load(HUM, af="highpass=f=80"), n, .5), .05)
fx += hum * window(LINES[4]["start"], BT["halt"], .08)

for p in BT["presses"]:
    place(fx, edges(peak(load(BUTTON, 0, .5)), .002, .05), p, .26)

place(fx, edges(peak(load(STRAIN, af="lowpass=f=4000")), .05, .5), BT["push"] + .4, .1)
breath = peak(loop_to(load(BREATH), n, .3), .07)
fx += breath * window(LINES[9]["start"], LINES[9]["start"] + 3.2, .4)
vent = peak(loop_to(load(VENT), n, .5), .035)
fx += vent * window(BT["vent"], LINES[11]["start"], .7)
span = LINES[19]["start"] - LINES[18]["start"]
fx += vent * window(LINES[18]["start"] + span * .42, LINES[18]["start"] + span * .64, .3)
fx += breath * window(LINES[12]["start"], LINES[13]["start"], .5)

# fists on the doors, the alarm button and the rescue doors opening
knock = around_peak(KNOCK, after=.5, af="lowpass=f=2500")
for k in BT["knocks"]:
    place(fx, knock, k, .5)
place(fx, edges(peak(load(BUTTON, 0, .5)), .002, .05), BT["alarm"], .3)
place(fx, edges(peak(load(DOOR)), .005, .2), BT["doors"], .2)

env = np.abs(voice)
w = int(sr * .25)
env = np.convolve(env, np.ones(w, dtype=np.float32) / w, mode="same")
duck = (1 - .35 * np.clip(env / (np.percentile(env, 95) + 1e-6), 0, 1))[:, None]
voice_gain = .92 / max(np.abs(voice).max(), 1e-6)
mix = (voice * voice_gain)[:, None] + (ambience + fx) * duck
fade = np.minimum(1.0, t / .3) * np.minimum(1.0, (t[-1] - t) / .4)
mix *= fade[:, None]
mix = np.tanh(mix * 1.02) * .97
sf.write(ROOT / "audio" / "mezcla.wav", mix, sr)
print("pico", round(float(np.abs(mix).max()), 3), "efectos pico", round(float(np.abs(fx).max()), 3))
