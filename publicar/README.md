# Publicar

Una cola por proyecto (cada uno es un canal distinto) y un solo flujo de n8n que publica en YouTube, Facebook y TikTok.

| Proyecto | Plataformas previstas | Activas hoy |
|---|---|---|
| sticks | YouTube, Facebook, TikTok | YouTube |
| minecraft | YouTube, Facebook, TikTok | YouTube |
| 3dpartes | YouTube (Facebook y TikTok listos para activar) | YouTube |
| league | YouTube (20:00; la descripción lleva sola el aviso de Riot) | YouTube, falta conectar la cuenta en n8n |

## Poner un video en la cola
Crear `<proyecto>\cola\<nombre>\` (por ejemplo `sticks\cola\09-desierto\`) con:
- `video.mp4`: el Short final (máximo 3 minutos).
- `metadata.json`:
```json
{
  "titulo": "Título con gancho, máximo 100 caracteres",
  "descripcion": "Dos o tres frases sobre el video.",
  "tags": ["tag 1", "tag 2"]
}
```
La categoría, los hashtags y los horarios salen del proyecto en `config.json`.

TikTok se sube a mano: cada video lleva un `tiktok.txt` con el texto listo para copiar.

## Qué ya se subió y qué no
```
python C:\videos-youtube\publicar\publicar.py estado
```
Muestra cada video con su horario y una marca por plataforma (✔ hecho, · pendiente). El detalle de cada video, con los ids de cada plataforma, está en su `estado.json`. Cuando todas sus plataformas activas están hechas, la carpeta pasa de `cola\` a `subidos\`.

## Subir
1. Iniciar n8n con `C:\videos-youtube\n8n\iniciar_n8n.bat`.
2. En el flujo "Publicar - Sticks, Minecraft, 3dpartes y League", pulsar **Execute workflow** en "Subir cola".
   - YouTube: sube como privado con fecha; YouTube lo publica a su hora.
   - Facebook: sube el Reel como programado a la misma hora.
3. Para TikTok, activar el flujo: el disparador "Cada 15 minutos" publica cada video cuando llega su hora, porque la API de TikTok no permite programar.

## Cómo evita choques
- Cada video recibe un horario libre de la agenda de su proyecto (`<proyecto>\agenda.json`) antes de subirse, y lo usa en todas sus plataformas.
- Un segundo clic no duplica nada: las plataformas hechas se saltan y las reservas se reutilizan.
- Si algo falla, el video sigue en la cola y el siguiente clic retoma solo lo que falta.

## Activar Facebook o TikTok en un proyecto
1. En n8n, en los nodos de esa plataforma y proyecto, elegir la cuenta:
   - Facebook: credencial "Header Auth" con nombre `Authorization` y valor `OAuth <token de la página>`.
   - TikTok: credencial OAuth2 de una app de TikTok con el permiso `video.publish`.
2. En `config.json`, en ese proyecto: `"activo": true` y, para Facebook, el `page_id` de la página.

Hasta entonces esos nodos no reciben videos.

## Límites conocidos
- TikTok: mientras la app no pase la auditoría de TikTok, todo se publica como privado (`SELF_ONLY`).
- Facebook: la documentación oficial permite programar Reels, pero hay reportes de que no funciona. Hay que probarlo con la primera página.
- Horarios: son un punto de partida, no medidos con datos de tu público.
