# Estado de los canales (4 de noviembre de 2026, noche)

Todo se publica con n8n (flujo "Publicar - Sticks, Minecraft, 3dpartes y League"): `C:\videos-youtube\n8n\iniciar_n8n.bat` y luego **Execute workflow** en "Subir cola".
Para ver qué falta: `python C:\videos-youtube\publicar\publicar.py estado`.

## Resumen

| Canal | Subidos | En cola, sin subir | En producción | Guiones listos | Ideas |
|---|---|---|---|---|---|
| **Sticks** (¿Qué pasaría si? / Archivo México) | 2 | 3 | — | 6 | 13 |
| **3dpartes** (cómo se construye) | 4 | 1 | — | 2 (en pausa) | 14 |
| **Minecraft** (¿Cómo se hace?) | 0 | 0 | — (en pausa) | 0 | — |
| **League** (la profe, canal nuevo) | 0 | 0 | 2 | 0 aparte | 10 |

## Sticks — YouTube + Facebook (página 806452805879704)
**Subidos**
- 08 Elevador: publicado el 3 de noviembre a las 19:30.
- 09 Irán / Qeshm (noticia): publicado el 3 de noviembre a las 10:00.

**En cola, sin subir** (reciben horario al pulsar "Subir cola": uno al día a las 19:30)
- 10 Chupacabras
- 11 Llamada de emergencia
- 12 Mataviejitas

**Guiones listos, sin producir** (`sticks\guiones\`)
- Archivo México:
  - 01 Guardería ABC
  - 02 2 de octubre de 1968
  - 03 El Mochaorejas
- ¿Qué pasaría si…?:
  - 06 Te entierran vivo
  - 07 No duermes 7 días
  - 09 Te pierdes en el desierto
  - 10 La Tierra deja de girar

**Ideas** (`sticks\ideas.json`): 13 sin usar. La siguiente acordada es **#15 Gasolinera**, todavía sin confirmar.

## 3dpartes — YouTube + Facebook
**Subidos** (cada uno programado a las 19:30)
- 01 Carretera: 3 de noviembre.
- 02 Relleno sanitario: 4 de noviembre.
- 03 Pista de hielo: 5 de noviembre.
- 04 Muro de contención: 6 de noviembre.

**En cola, sin subir**
- 05 Edificio antisísmico (en inglés). Toma el siguiente día libre: 7 de noviembre.

**Guiones listos, en pausa porque los temas son menos llamativos**
- 05 Fosa séptica
- 06 Green de golf

**Ideas aprobadas** (en inglés)
- Túnel bajo el mar
- Rascacielos en suelo blando
- Isla artificial
- Presa
- Búnker
- Bóveda de banco
- Puente sobre agua
- Pista de F1
- Estación de metro

**Hay que revisar:** en `publicar\config.json`, 3dpartes usa **la misma página de Facebook que Minecraft** (1215820188285579). Si cada canal debe tener su propia página, hay que cambiar ese dato.

## Minecraft — en pausa
- Frituras: rechazado y borrado.
- No se hacen videos nuevos hasta que lo pidas.
- Cuenta con YouTube y con la página de Facebook 1215820188285579.

## League — la profe (canal nuevo, solo YouTube, 2 al día: 14:00 y 20:00)
**Subido**
- 01 El agro de súbditos: miércoles 4 a las 20:30.

**En cola**
| Fecha | 14:00 | 20:00 |
|---|---|---|
| Jue 5 | 02 Torre objetivo | 03 Disparos de torre a súbditos |
| Vie 6 | 04 Arbusto | 05 Recall |
| Sáb 7 | 06 Reloj de oleadas | 07 Alma del dragón |
| Dom 8 | 08 Flash | 09 4 mitos |

Cada video:
- dura entre 62 y 76 segundos;
- usa sonidos reales del juego, el mapa simplificado y humor;
- cierra con el gag de Teemo;
- lleva solo el aviso de Riot en la descripción.

**Pendiente**
- El nombre de la profe.
- Temas para la semana siguiente (quedan ideas en `league\temas.md`).

Para subir un video: carpeta `publicar\league\cola\<slug>\` con `video.mp4` y `metadata.json`.
