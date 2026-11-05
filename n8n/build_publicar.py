"""Writes one n8n workflow that publishes the three projects. n8n cannot pick a credential per item, so a Switch sends
each video to the nodes of its own channel. No secrets inside: accounts are chosen in n8n after importing.

- "Subir cola" (manual): YouTube and Facebook, which can schedule, get every queued video now with its future time.
Facebook and TikTok receive items only when their "activo" flag is true in publicar\\config.json."""
import json
from pathlib import Path

PY = r"C:\Users\david\AppData\Local\Programs\Python\Python313\python.exe"
SCRIPT = r"C:\videos-youtube\publicar\publicar.py"
PROJECTS = ["sticks", "minecraft", "3dpartes", "league"]
GRAPH = "https://graph.facebook.com/v25.0"
PARSE = """const out = String($json.stdout || '').trim().split(/\\r?\\n/).pop();
const data = JSON.parse(out);
for (const o of data.omitidos) console.log('Omitido', o.proyecto, o.slug, o.problemas.join('; '));
return data.videos.map(v => ({ json: v }));"""

nodes, conn = [], {}


def node(name, kind, version, x, y, params, **extra):
    if kind in ("youTube", "httpRequest"):
        extra.setdefault("onError", "continueErrorOutput")
    nodes.append(dict(id=name.lower().replace(" ", "-"), name=name, type=f"n8n-nodes-base.{kind}", typeVersion=version, position=[x, y], parameters=params, **extra))
    return name


def link(a, b, output=0):
    outs = conn.setdefault(a, {"main": []})["main"]
    while len(outs) <= output:
        outs.append([])
    outs[output].append({"node": b, "type": "main", "index": 0})


def http(name, x, y, method, url, query=(), headers=(), body=None, auth=None):
    p = {"method": method, "url": url, "options": {}}
    if auth:
        p.update(authentication="genericCredentialType", genericAuthType=auth)
    if query:
        p.update(sendQuery=True, queryParameters={"parameters": [{"name": k, "value": v} for k, v in query]})
    if headers:
        p.update(sendHeaders=True, headerParameters={"parameters": [{"name": k, "value": v} for k, v in headers]})
    if body == "binary":
        p.update(sendBody=True, contentType="binaryData", inputDataFieldName="data")
    elif body:
        p.update(sendBody=True, specifyBody="json", jsonBody=body)
    return node(name, "httpRequest", 4.2, x, y, p)


def read_video(name, x, y, source):
    return node(name, "readWriteFile", 1.1, x, y, {"fileSelector": f"={{{{ $('{source}').item.json.archivo }}}}", "options": {"dataPropertyName": "data"}})


def switch(name, x, y, routes):
    rules = [{"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2}, "combinator": "and",
                             "conditions": [{"leftValue": "={{ $json.ruta }}", "rightValue": r, "operator": {"type": "string", "operation": "equals"}}]},
              "renameOutput": True, "outputKey": r} for r in routes]
    return node(name, "switch", 3.2, x, y, {"rules": {"values": rules}, "options": {}})


def register(name, x, y, source, ident):
    cmd = (f'="{PY}" "{SCRIPT}" registrar "{{{{ $(\'{source}\').item.json.proyecto }}}}" "{{{{ $(\'{source}\').item.json.slug }}}}" '
           f'"{{{{ $(\'{source}\').item.json.plataforma }}}}" "{ident}"')
    return node(name, "executeCommand", 1, x, y, {"command": cmd})


# ---- branch 1: manual click, YouTube and Facebook scheduled in each video's slot
# One click uploads the whole queue: "Uno por uno" loops over the videos one at a time; every branch (success, error or
# no matching channel) goes back to the loop, so a failing video is skipped and the rest keep going.
LOOP = "Uno por uno"
link(node("Subir cola", "manualTrigger", 1, 0, 0, {}), "Leer colas y reservar horarios")
link(node("Leer colas y reservar horarios", "executeCommand", 1, 220, 0, {"command": f'"{PY}" "{SCRIPT}" programar'}), "Videos a programar")
link(node("Videos a programar", "code", 2, 440, 0, {"jsCode": PARSE}), LOOP)
node(LOOP, "splitInBatches", 3, 560, 0, {"batchSize": 1, "options": {}})
link(LOOP, "Canal", 1)  # output 1 = next video; output 0 = done
SRC = LOOP
routes = [f"{p}/youtube" for p in PROJECTS] + [f"{p}/facebook" for p in PROJECTS]
switch("Canal", 700, 0, routes)
nodes[-1]["parameters"]["options"] = {"fallbackOutput": "extra"}
link("Canal", LOOP, len(routes))  # a video for a channel without a branch: back to the loop
y = -360
for out, route in enumerate(routes):
    project, platform = route.split("/")
    tag = f"{project} {platform}"
    if platform == "youtube":
        first = read_video(f"Leer video {tag}", 900, y, SRC)
        up = node(f"YouTube {project}", "youTube", 1, 1120, y, {
            "resource": "video", "operation": "upload", "title": f"={{{{ $('{SRC}').item.json.titulo }}}}", "regionCode": "MX",
            "categoryId": f"={{{{ $('{SRC}').item.json.categoria }}}}", "binaryProperty": "data",
            "options": {"description": f"={{{{ $('{SRC}').item.json.descripcion }}}}", "tags": f"={{{{ $('{SRC}').item.json.tags }}}}",
                        "privacyStatus": "private", "publishAt": f"={{{{ $('{SRC}').item.json.publishAt }}}}",
                        "selfDeclaredMadeForKids": "={{ false }}", "defaultLanguage": "es", "notifySubscribers": True}})
        link(first, up)
        link(up, LOOP, 1)  # upload failed: skip it, keep going
        last, ident = up, "{{ $json.id || $json.uploadId }}"
    else:  # Facebook Reel: start, send the file, finish as scheduled. The page token lives in a Header Auth credential.
        page = f"{{{{ $('{SRC}').item.json.page_id }}}}"
        first = http(f"Facebook {project} inicio", 900, y, "POST", f"={GRAPH}/{page}/video_reels", query=[("upload_phase", "start")], auth="httpHeaderAuth")
        read = read_video(f"Leer video {tag}", 1120, y, SRC)
        send = http(f"Facebook {project} enviar", 1340, y, "POST", f"={{{{ $('Facebook {project} inicio').item.json.upload_url }}}}",
                    headers=[("offset", "0"), ("file_size", f"={{{{ $('{SRC}').item.json.tamano }}}}")], body="binary", auth="httpHeaderAuth")
        last = http(f"Facebook {project} programar", 1560, y, "POST", f"={GRAPH}/{page}/video_reels", auth="httpHeaderAuth", query=[
            ("upload_phase", "finish"), ("video_id", f"={{{{ $('Facebook {project} inicio').item.json.video_id }}}}"), ("video_state", "SCHEDULED"),
            ("scheduled_publish_time", f"={{{{ $('{SRC}').item.json.publish_unix }}}}"), ("description", f"={{{{ $('{SRC}').item.json.descripcion }}}}")])
        link(first, read)
        link(read, send)
        link(send, last)
        for n_ in (first, send, last):
            link(n_, LOOP, 1)  # Facebook failed: skip it, keep going
        ident = f"{{{{ $('Facebook {project} inicio').item.json.video_id }}}}"
    link("Canal", first, out)
    link(last, register(f"Registrar {tag}", 1800, y, SRC, ident))
    link(f"Registrar {tag}", LOOP)  # registered: next video
    y += 160

# (TikTok branch removed on 2026-11-04 at the user's request; see git history / backups to restore it)

wf = {"name": "Publicar - Sticks, Minecraft, 3dpartes y League", "nodes": nodes, "connections": conn, "settings": {"executionOrder": "v1"}, "pinData": {}}
target = Path(__file__).with_name("Publicar_Videos.json")
target.write_text(json.dumps(wf, ensure_ascii=False, indent=1), encoding="utf-8")
old = Path(__file__).with_name("YouTube_Publicar_Cola.json")
if old.exists():
    old.unlink()
print(len(nodes), "nodos ->", target)
