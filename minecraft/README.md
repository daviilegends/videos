# ¿Cómo se hace? (canal Minecraft)

Desde el 3 de noviembre de 2026, este canal pasa a la serie **"¿Cómo se hace?"**: cómo se fabrican las cosas que usamos (frituras, botellas, tortillas, latas…), con animación 3D por capas y un corte que deja ver dentro de cada máquina. Usa el mismo estilo y motor que 3dpartes. Son Shorts de entre 1 y 3 minutos.

## Formato
- Voz en español: narrador profesional, `3dpartes\produccion\voces\narrador_es.wav` (alternativa más enérgica: `narrador_es_alternativa.wav`).
- Subtítulos en español, palabra por palabra, a media pantalla. Etiquetas amarillas en español.
- Guion en ciclo: problema, "entonces" la solución, el nombre de la máquina y el cierre "Felicidades, hiciste…".
- Sin marcas: "frituras de queso", "refresco de cola", nunca el nombre de una marca en el título ni en la imagen. El nombre puede ir en las etiquetas de búsqueda.
- Sin recetas: se explica el proceso y por qué cada máquina hace lo que hace, sin cantidades ni fórmulas.
- La fábrica siempre tiene contexto: nave con techo, ventanales, luces y el campo afuera.

## Hacer un episodio
El motor y los compositores viven en `C:\videos-youtube\3dpartes\produccion\`.

| Paso | Comando (desde `3dpartes\produccion\`) |
|---|---|
| Voz | `..\..\tts\env\Scripts\python.exe narrar_en.py C:\videos-youtube\minecraft\episodios\NN-tema --voz narrador_es --idioma es` |
| Revisar cuadros | `blender -b --python escena_<tema>.py -- C:\videos-youtube\minecraft\episodios\NN-tema 95 --cuadros 2,10,20 --rapido` |
| Render completo (calidad alta; las frituras tardaron ~4-7 s por cuadro antes de fijar el corte) | lo mismo sin `--cuadros` ni `--rapido` |
| Video final | `..\..\production\render_env\Scripts\python.exe componer3d.py C:\videos-youtube\minecraft\episodios\NN-tema C:\videos-youtube\minecraft\episodios\NN-tema\video.mp4` |

En `story.json` cada línea lleva su texto en `"es"` y el archivo usa `"subtitulos": "palabra_en"` (palabra por palabra, en cualquier idioma).

## Episodios
| # | Tema | Estado |
|---|---|---|
| 01 | Frituras de maíz inflado | descartado (se veía genérico) |
| 02 | Botella de plástico (PET) | en pausa (carpeta descartados) |

Ideas siguientes: botella de plástico, tortillas, refresco de cola en lata, papas fritas de bolsa, lata de aluminio, helado, papel higiénico, lápiz, gomitas, llanta, frasco de vidrio.

Para publicar: `publicar\minecraft\cola\NN-tema\` (YouTube y Facebook activos).
