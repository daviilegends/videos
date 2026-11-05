# 3dpartes

Explicaciones paso a paso con animación 3D por capas: un terreno que se va construyendo ante la cámara (por ejemplo, "así se construye una carretera"). Shorts de máximo 3 minutos. Blender 5.2 está instalado en `C:\Program Files\Blender Foundation\Blender 5.2`.

## Estado
El episodio 01-carretera está terminado y en la cola de publicación. La alberca se descartó porque otros canales ya la hicieron; su prueba sigue en `produccion\` (alberca_prueba.mp4, escena.py y componer.py, que son del formato anterior). Hay seis guiones en `guiones\` y la lista en `ideas.json`.

## Carpetas
| Carpeta | Contenido |
|---|---|
| `guiones/` | Guiones, uno por archivo |
| `referencias/` | Videos de referencia del estilo |
| `episodios/NN-nombre/` | Cada episodio: story.json, sonido.json, voz, cuadros y video |
| `produccion/` | motor3d.py, componer3d.py, narrar_en.py, la voz y una escena por tema |

## Formato
- Voz en inglés: narrador de documental (`produccion\voces\narrador_en.wav`, la misma en todos los episodios).
- Subtítulos en español en la parte baja, y una etiqueta amarilla con el término en español y en inglés debajo.
- Paisaje completo alrededor del terreno (colinas, árboles, campos, pueblo, montañas): nunca un bloque flotando.
- Cada frase tiene su acción en pantalla, y cada acción su sonido.
- Guion en ciclo: problema, "entonces" la solución, el nombre técnico y el cierre "felicidades, construiste X".

## Hacer un episodio nuevo
Todo corre en local. Solo el paso 2 necesita código nuevo.
1. `episodios\NN-tema\story.json`: escenas con líneas `{"en", "es", "nombra"}`, más `etiqueta` y `termino_en` (ver 01-carretera).
2. `produccion\escena_<tema>.py`: empieza con `from motor3d import *` y describe solo las capas, las máquinas, las acciones y las cámaras del tema. `motor3d.py` ya trae el paisaje, el corte, las máquinas, los coches, la lluvia, la grava, el vapor, el rociador, `shot`/`follow` y `terminar()`. Cada acción guarda su tiempo con `beat("nombre", t)`.
3. `episodios\NN-tema\sonido.json`: qué sonido va en cada beat (el formato está al inicio de `componer3d.py`).
   La mezcla final se hace sola: limpia y realza la voz, baja los efectos 6 dB mientras habla el narrador y deja todo en -14 LUFS (lo que usan YouTube y Facebook). Para cambiarlo, pon en story.json `"mezcla": {"lufs": -14, "bajar_efectos_db": 6, "cadena_voz": true}`.

| Paso | Comando (desde `produccion\`) |
|---|---|
| Voz | `..\..\tts\env\Scripts\python.exe narrar_en.py ..\episodios\NN-tema` |
| Revisar cuadros | `blender -b --python escena_<tema>.py -- C:\videos-youtube\3dpartes\episodios\NN-tema 80 --cuadros 2,10,20` |
| Render completo (~1 s por cuadro) | lo mismo sin `--cuadros` |
| Video final | `..\..\production\render_env\Scripts\python.exe componer3d.py ..\episodios\NN-tema ..\episodios\NN-tema\video.mp4` |

Pasa a Blender la ruta completa del episodio: con una ruta relativa, los cuadros se guardan en otra carpeta.

Para publicar, copia el video a `publicar\3dpartes\cola\NN-tema\video.mp4` con su `metadata.json` (categoría Educación).
