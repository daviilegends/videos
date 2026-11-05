"""Narrates an episode with voice B (VoxCPM2 clone) line by line, then aligns words with faster-whisper.
Usage: tts/env/Scripts/python.exe narrar.py <episode_dir> [--solo-alinear]
Writes narracion.wav, lineas.json (start/end per line) and palabras.json (per-line word timings, global seconds)."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

EP = Path(sys.argv[1]).resolve()
LEAGUE = Path(__file__).resolve().parents[1]
GAP, LEAD = .42, .25
guion = json.loads((EP / "guion.json").read_text(encoding="utf-8"))
LINES = guion["lineas"]

if "--solo-alinear" not in sys.argv:
    import torch
    import voxcpm.model.voxcpm2 as vm
    from voxcpm import VoxCPM

    sys.path.insert(0, str(LEAGUE.parent / "tts" / "benchmark"))
    from voxcpm_stream import install

    install(vm)
    REF = LEAGUE / "voces" / "B_youtuber_seguro.wav"
    REF_TEXT = ("¿Sabías que cada vez que golpeas al campeón enemigo, sus súbditos se giran para atacarte? "
                "No es mala suerte. Es una regla del juego, y hoy vas a aprender a usarla a tu favor. "
                "¿Ya lo sabías, o llevabas años perdiendo vida sin entender por qué?")
    model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
    sr = model.tts_model.sample_rate
    parts, times, t = [np.zeros(int(sr * LEAD))], [], LEAD
    import hashlib
    cache = EP / "_cache_voz"
    cache.mkdir(exist_ok=True)
    for n, line in enumerate(LINES):
        voz = line.get("voz", line["text"])
        key = cache / (hashlib.md5(voz.encode()).hexdigest()[:16] + ".npy")
        if key.exists():
            wav = np.load(key)
        else:
            torch.manual_seed(11)
            wav = model.generate(text=voz, prompt_wav_path=str(REF), prompt_text=REF_TEXT, cfg_value=2.0, inference_timesteps=10)
            np.save(key, wav)
        idx = np.where(np.abs(wav) > .01)[0]
        wav = wav[max(0, idx[0] - 400):idx[-1] + 1200]
        dur = len(wav) / sr
        times.append(dict(id=line["id"], text=line["text"], start=round(t, 3), end=round(t + dur, 3)))
        parts += [wav, np.zeros(int(sr * GAP))]
        t += dur + GAP
        print(f"[{n + 1}/{len(LINES)}] {dur:5.2f}s  {line['text'][:60]}", flush=True)
    sf.write(EP / "narracion.wav", np.concatenate(parts), sr)
    (EP / "lineas.json").write_text(json.dumps(times, ensure_ascii=False, indent=1), encoding="utf-8")
    del model
    torch.cuda.empty_cache()

# ---------- word alignment ----------
import torch  # noqa: E402,F401  (loads the CUDA DLLs that faster-whisper needs)
from faster_whisper import WhisperModel  # noqa: E402

times = json.loads((EP / "lineas.json").read_text(encoding="utf-8"))
audio, sr = sf.read(EP / "narracion.wav")
audio = audio if audio.ndim == 1 else audio.mean(1)
wm = WhisperModel("small", device="cuda", compute_type="int8_float16")
out = []
for ln in times:
    seg = audio[int(ln["start"] * sr):int(ln["end"] * sr)].astype(np.float32)
    if sr != 16000:
        import librosa
        seg = librosa.resample(seg, orig_sr=sr, target_sr=16000)
    segs, _ = wm.transcribe(seg, language="es", word_timestamps=True, beam_size=5)
    asr = [w for s in segs for w in s.words]
    words = ln["text"].split()
    line_def = next(x for x in LINES if x["id"] == ln["id"])
    vwords = line_def.get("voz", ln["text"]).split()
    assert len(vwords) == len(words), f"{ln['id']}: voice text and subtitle text must have the same number of words"
    import difflib
    sw = [re.sub(r"[^\wñ]", "", w.lower()) for w in vwords]
    aw = [re.sub(r"[^\wñ]", "", a.word.lower()) for a in asr]
    st, en = [None] * len(words), [None] * len(words)
    for blk in difflib.SequenceMatcher(None, sw, aw, autojunk=False).get_matching_blocks():
        for j in range(blk.size):
            st[blk.a + j], en[blk.a + j] = asr[blk.b + j].start, asr[blk.b + j].end
    a0 = asr[0].start if asr else 0
    a1 = asr[-1].end if asr else ln["end"] - ln["start"]
    lens = [len(x) + 1 for x in sw]
    cum = np.concatenate([[0], np.cumsum(lens)]) / sum(lens)
    known = [(cum[j], st[j]) for j in range(len(words)) if st[j] is not None]
    known_e = [(cum[j + 1], en[j]) for j in range(len(words)) if en[j] is not None]
    kx = [0.0] + [k[0] for k in known] + [1.0]
    ky = [a0] + [k[1] for k in known] + [a1]
    ex = [0.0] + [k[0] for k in known_e] + [1.0]
    ey = [a0] + [k[1] for k in known_e] + [a1]
    miss = sum(x is None for x in st)
    timed = []
    for j, w in enumerate(words):
        s_ = st[j] if st[j] is not None else float(np.interp(cum[j], kx, ky))
        e_ = en[j] if en[j] is not None else float(np.interp(cum[j + 1], ex, ey))
        timed.append(dict(w=w, s=ln["start"] + s_, e=ln["start"] + max(e_, s_ + .05)))
    if miss:
        print(f"  ~ {ln['id']}: {miss} of {len(words)} words interpolated")
    out.append(dict(id=ln["id"], words=[dict(w=d["w"], s=round(d["s"], 3), e=round(d["e"], 3)) for d in timed]))
(EP / "palabras.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", EP / "narracion.wav", f"{times[-1]['end']:.1f}s")
