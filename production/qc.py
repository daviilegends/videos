"""Measures the delivered MP4, not the intermediates, and writes output/qc.json plus a contact sheet."""
import json
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import torch  # puts torch's CUDA DLLs on the path for faster-whisper
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent
MP4 = ROOT / "output" / "elevador.mp4"
tl = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))


def run(*args):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def words(t):
    t = "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-zñ0-9]+", t)


probe = json.loads(run("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(MP4)).stdout)
video = next(s for s in probe["streams"] if s["codec_type"] == "video")
audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
log = run("ffmpeg", "-v", "info", "-i", str(MP4), "-vf", "blackdetect=d=0.2:pix_th=0.06,freezedetect=n=0.0005:d=2.5",
          "-af", "ebur128=peak=true", "-f", "null", "-").stderr
blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)
freezes = re.findall(r"freeze_duration: ([\d.]+)", log)
lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)

model = WhisperModel("small", device="cuda", compute_type="int8_float16")
segs, _ = model.transcribe(str(MP4), language="es", beam_size=5, word_timestamps=True)
heard = [w for s in segs for w in s.words]
hyp = words(" ".join(w.word for w in heard))
lines = [l for s in tl["scenes"] for l in s["lines"]]
ref = words(" ".join(l["text"] for l in lines))
ops = SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes()
diffs = [f"{' '.join(ref[a:b])} -> {' '.join(hyp[c:d])}" for t, a, b, c, d in ops if t != "equal"]
errors = sum(max(b - a, d - c) for t, a, b, c, d in ops if t != "equal")

# subtitle sync: when each sentence's first subtitle appears against the first word heard in the delivered MP4
cues = json.loads((ROOT / "cues.json").read_text(encoding="utf-8"))
first_cue = {c["sentence"]: c["start"] for c in reversed(cues)}
offsets = []
hw = [words(w.word) for w in heard]
flat = [(x, w.start) for x_list, w in zip(hw, heard) for x in x_list]
cursor = 0
for line in lines:
    first = words(line["text"])[0]
    for i in range(cursor, len(flat)):
        if flat[i][0] == first and abs(flat[i][1] - line["start"]) < 2.5:
            offsets.append(round(flat[i][1] - first_cue[lines.index(line)], 3))
            cursor = i + 1
            break
report = dict(
    file=str(MP4), size_mb=round(MP4.stat().st_size / 1e6, 1), duration_s=round(float(probe["format"]["duration"]), 2),
    resolution=f"{video['width']}x{video['height']}", fps=video["r_frame_rate"], video_codec=video["codec_name"],
    audio_codec=audio["codec_name"], frames=int(video["nb_frames"]), black_segments=blacks, freezes_over_2_5s=freezes,
    integrated_lufs=float(lufs[-1]) if lufs else None, true_peak_dbfs=float(peak[-1]) if peak else None,
    script_words=len(ref), word_error_rate=round(errors / len(ref), 3), whisper_diffs=diffs,
    subtitle_offsets_s=offsets, max_subtitle_offset_s=max((abs(o) for o in offsets), default=None), sentences_matched=f"{len(offsets)}/{len(lines)}",
)
(ROOT / "output" / "qc.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=1))

times = [round(tl["duration"] * (i + .5) / 12, 1) for i in range(12)]
inputs = []
for x in times:
    inputs += ["-ss", str(x), "-i", str(MP4)]
chain = "".join(f"[{i}:v]scale=480:-1[v{i}];" for i in range(len(times))) + "".join(f"[v{i}]" for i in range(len(times))) + f"xstack=inputs={len(times)}:grid=4x3"
result = run("ffmpeg", "-y", "-v", "error", *inputs, "-frames:v", "1", "-filter_complex", chain, str(ROOT / "output" / "contact_sheet.jpg"))
print(result.stderr[-300:])
