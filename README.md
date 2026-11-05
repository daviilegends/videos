# Videos de YouTube

Tres series de Shorts, todas de máximo 3 minutos, y un sistema de publicación compartido.

| Carpeta | Qué es | Estado |
|---|---|---|
| `sticks\` | Historias "¿Qué pasaría si...?" con personajes de palitos | Un episodio terminado (elevador) |
| `3dpartes\` | Construcción paso a paso con animación 3D por capas | Esqueleto |
| `minecraft\` | Temas explicados con escenas de Minecraft | Esqueleto, falta el video de referencia |
| `publicar\` | Una cola y agenda por proyecto para YouTube, Facebook y TikTok | Listo, sin probar contra las plataformas |
| `production\` | Motor de render de Sticks (un episodio a la vez) | En uso |
| `n8n\` | Flujos de n8n y el `.bat` para iniciarlo | Ver abajo |
| `tts\`, `image\`, `sfx\` | Voz (VoxCPM2), fondos (ComfyUI con Flux) y biblioteca de sonidos | Compartidos |

Cada carpeta de serie tiene su propio `README.md` con los pasos.

## Motor de Sticks (`production\`)
Ejecutar desde `production\` con `PYTHONUTF8=1`. Cerrar juegos y dejar al menos 9 GB libres en C: antes de cargar VoxCPM2.

| Paso | Comando |
|---|---|
| Fondos (usa la caché de `assets\bg`) | `python gen_backgrounds.py [nombres] [--force]` |
| Narración | `..\tts\env\Scripts\python.exe narrate.py` |
| Acortar pausas | `..\tts\env\Scripts\python.exe tighten_audio.py` (solo justo después de narrate.py; borrar antes `audio\narracion_raw.wav`) |
| Subtítulos | `..\tts\env\Scripts\python.exe align_subs.py` |
| Revisar tomas | `render_env\Scripts\python.exe render.py --stills 3,10,20` |
| Sonido | `render_env\Scripts\python.exe mix_audio.py` |
| Video | `render_env\Scripts\python.exe render.py --full` |
| Unir audio | `ffmpeg -y -i output\video_mudo.mp4 -i audio\mezcla.wav -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest output\elevador.mp4` |
| Control de calidad | `..\tts\env\Scripts\python.exe qc.py` |

Si se regenera un fondo, hay que reajustar sus posiciones en `layout.py`.

## Sonido
`mix_audio.py` toma ambiente y efectos de `sfx\library` (Sonniss GDC 2017), buscados por nombre en `sfx\catalog.json`. Buscar sonidos: `python -I sfx\search.py`.
Licencia: se puede usar en videos monetizados sin atribución. No se puede redistribuir como efectos sueltos ni usar para entrenar IA.

## n8n
- Iniciar: `n8n\iniciar_n8n.bat`.
- Publicar: importar `n8n\Publicar_Videos.json` (se regenera con `python n8n\build_publicar.py`). Un solo flujo para los tres canales; ver `publicar\README.md`.
- `n8n\referencia\` guarda el flujo anterior de Pokémon. Contiene tokens de Facebook en texto plano: revócalos y no compartas ese archivo.
- `production\studio_service.py` y `n8n\AI_Animation_Studio_Prototype.json` son del prototipo del hospital y no sirven para las series actuales.

## Notas de esta máquina
- VoxCPM2 necesita `tts\benchmark\voxcpm_stream.py`: la carga estándar se cae por falta de memoria virtual.
- ComfyUI está fijado en v0.3.75 porque las versiones recientes piden un PyTorch más nuevo que 2.6.
- ComfyUI usa `--cpu-vae`, `--cache-none` y decodificación por partes. `gen_backgrounds.py` lo inicia y lo cierra, y se detiene si C: baja de 2 GB libres.
- La caché de Hugging Face guarda los archivos grandes en `hub\blobs`. Borrar la carpeta de un modelo no libera ese espacio.
