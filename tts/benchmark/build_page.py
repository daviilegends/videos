"""Builds comparison.html from the measured results. Letters are fixed so listening can start without model bias."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
results = {}
for line in (ROOT / "results.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    results[r["id"]] = r
whisper = json.loads((ROOT / "whisper.json").read_text(encoding="utf-8"))
drift = json.loads((ROOT / "consistency.json").read_text(encoding="utf-8"))

ORDER = [
    ("voxcpm2_clon_frases", "VoxCPM2", "Narrador diseñado y clonado frase por frase", "Apache-2.0", "4.96 GB"),
    ("voxcpm2_diseno", "VoxCPM2", "Diseño de voz, texto completo de una vez", "Apache-2.0", "4.96 GB"),
    ("qwen17_diseno", "Qwen3-TTS 1.7B VoiceDesign", "Diseño de voz, texto completo de una vez", "Apache-2.0", "4.52 GB"),
    ("qwen17_diseno_frases", "Qwen3-TTS 1.7B VoiceDesign", "Diseño de voz frase por frase", "Apache-2.0", "4.52 GB"),
    ("chatterbox_latam_narrador", "Chatterbox es-MX-LATAM", "Ajuste narrador (exag. 0.65, cfg 0.35)", "MIT", "3.2 GB"),
    ("chatterbox_latam_actual", "Chatterbox es-MX-LATAM", "Ajuste de tu servidor (0.5 / 0.5)", "MIT", "3.2 GB"),
    ("chatterbox_general_narrador", "Chatterbox general (el actual)", "Ajuste narrador (exag. 0.65, cfg 0.35)", "MIT", "ya instalado"),
    ("chatterbox_general_actual", "Chatterbox general (el actual)", "Ajuste de tu servidor (0.5 / 0.5)", "MIT", "ya instalado"),
    ("kokoro_em_alex", "Kokoro-82M", "Voz predefinida em_alex", "Apache-2.0", "0.31 GB"),
]


def real_diffs(i):
    return [d for d in whisper[i]["diffs"] if d != "veinte -> 20"]


cards = []
rows = []
for n, (i, model, cfg, lic, size) in enumerate(ORDER):
    r = results[i]
    letter = chr(65 + n)
    diffs = real_diffs(i)
    note = "; ".join(diffs) if diffs else "sin diferencias"
    cards.append(f"""<article><h2><span>{letter}</span> {html.escape(model)}</h2><p class="cfg">{html.escape(cfg)}</p>
<audio controls preload="metadata" src="norm/{r['audio']}"></audio>
<p class="note">Whisper entendió: {html.escape(note)}</p></article>""")
    rows.append(f"<tr><td>{letter}</td><td>{html.escape(model)}</td><td>{r['audio_s']} s</td><td>{r['gen_s']} s</td>"
                f"<td>{r['rtf']}×</td><td>{r['vram_peak_gb']} GB</td><td>{r['ram_rss_gb']} GB</td><td>{r['sr'] // 1000} kHz</td>"
                f"<td>{len(diffs)}</td><td>{drift[i]:.3f}</td><td>{lic}</td><td>{size}</td></tr>")

page = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Comparación de voces</title><style>
:root{{color-scheme:dark;--bg:#14181b;--card:#1e2428;--line:#333c42;--text:#e8ecee;--muted:#a3afb6;--accent:#d7c56f}}
body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1040px;margin:auto;padding:32px 16px 64px}}h1{{margin:0 0 8px;font-size:30px}}
.lead,.cfg,.note,small{{color:var(--muted)}}blockquote{{margin:20px 0;padding:14px 18px;border-left:3px solid var(--accent);background:var(--card)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:14px;margin:24px 0}}
article{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}}
h2{{font-size:17px;margin:0}}h2 span{{display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;border-radius:50%;background:var(--accent);color:#14181b;margin-right:6px}}
.cfg{{margin:6px 0 12px;font-size:14px}}.note{{margin:10px 0 0;font-size:13px}}audio{{width:100%}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px;min-width:820px}}th,td{{padding:8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}th{{color:var(--muted);font-weight:600}}
</style></head><body><main><h1>Comparación de voces</h1>
<p class="lead">Mismo texto, generado en tu RTX 2060 y con el volumen igualado a -16 LUFS. Escucha con audífonos y fíjate en el acento, las pausas y la tensión dramática.</p>
<blockquote>{html.escape(" ".join(__import__("common").TEXT.split()))}</blockquote>
<div class="grid">{''.join(cards)}</div><h2>Mediciones</h2><div class="scroll"><table><tr><th></th><th>Modelo</th><th>Audio</th><th>Generación</th><th>Tiempo por s de audio</th><th>VRAM pico</th><th>RAM</th><th>Muestreo</th><th>Dif. Whisper</th><th>Estabilidad de voz</th><th>Licencia</th><th>Descarga</th></tr>{''.join(rows)}</table></div>
<p><small>Estabilidad de voz: similitud mínima de seis tramos contra el promedio del audio (1 = idéntica). Es una medición aproximada. "Dif. Whisper" cuenta diferencias contra el guion, sin contar "veinte" transcrito como "20"; puede ser un error de Whisper y no del modelo. Ningún número sustituye tu oído.</small></p>
</main></body></html>"""
(ROOT / "comparison.html").write_text(page, encoding="utf-8")
print("ok", len(cards))
