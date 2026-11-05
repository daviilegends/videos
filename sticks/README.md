# Sticks

Historias "¿Qué pasaría si...?" con personajes de palitos sobre fondos dibujados. Se publican como Shorts verticales con un título amarillo encima del video. Duración máxima: 3 minutos.

## Carpetas
| Carpeta | Contenido |
|---|---|
| `guiones/` | Guiones fuente (`que pasaria si.txt`, `archivo mexico.txt`) |
| `ideas.json` | Ideas propias pendientes de elegir |
| `episodios/NN-nombre/` | Cada episodio terminado: video horizontal, Short, título y archivos de tiempo |

## Producir un episodio
El motor está en `C:\videos-youtube\production` y trabaja un episodio a la vez.

1. Escribir `production\story.json` con el texto del guion, una escena por grupo de frases.
2. Definir los fondos en `production\gen_backgrounds.py` (objetos importantes dentro de la ilustración, no dibujados encima) y ejecutarlo.
3. Voz y subtítulos: `narrate.py`, `tighten_audio.py` y `align_subs.py` con `..\tts\env\Scripts\python.exe`.
4. Escribir una toma por frase en `production\render.py` y las posiciones en `production\layout.py`. Revisar cuadros con `render.py --stills t1,t2,...` antes del render completo.
5. `render_env\Scripts\python.exe mix_audio.py`, luego `render.py --full`, unir audio con ffmpeg y pasar `qc.py`.
6. Short vertical: lienzo 1080x1920 negro, video centrado y título en Impact amarillo `#F2E21E` (ver el comando en `episodios/08-elevador`).
7. Copiar el episodio a `episodios/` y ponerlo en la cola de publicación (`C:\videos-youtube\publicar\sticks\cola`).

## Episodios
| # | Episodio | Estado |
|---|---|---|
| 08 | 24 horas atrapado en un elevador | Terminado, en la cola de publicación |

Los casos reales de `archivo mexico.txt` (Guardería ABC, Tlatelolco y otros) tienen víctimas reales: decidir el tono antes de animarlos con este estilo.
