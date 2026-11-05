"""Writes a read-only n8n workflow that asks YouTube which channel each saved credential belongs to."""
import json
from pathlib import Path

CREDENTIALS = [("NnTmpM4UV41k2UwT", "YouTube account"), ("mxEcDKwmWxzah274", "YouTube account 2"),
               ("Za7TkeGfN2D8U8Ge", "YouTube account 3"), ("OhfBChzyVAI9gaHW", "YouTube account 4")]
nodes = [{"id": "start", "name": "Identificar", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 240], "parameters": {}}]
conn = {"Identificar": {"main": [[]]}}
for i, (cid, cname) in enumerate(CREDENTIALS):
    ask, show = f"Preguntar {cname}", f"Canal de {cname}"
    nodes.append({"id": f"ask{i}", "name": ask, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [260, i * 160],
                  "onError": "continueRegularOutput", "credentials": {"youTubeOAuth2Api": {"id": cid, "name": cname}},
                  "parameters": {"url": "https://www.googleapis.com/youtube/v3/channels", "authentication": "predefinedCredentialType",
                                 "nodeCredentialType": "youTubeOAuth2Api", "sendQuery": True,
                                 "queryParameters": {"parameters": [{"name": "part", "value": "snippet"}, {"name": "mine", "value": "true"}]}, "options": {}}})
    code = (f"const ch = ($json.items || [])[0];\n"
            f"return [{{ json: {{ credencial: '{cname}', canal: ch ? ch.snippet.title : 'sin canal o sin acceso: ' + JSON.stringify($json.error || $json).slice(0, 200), "
            f"id_canal: ch ? ch.id : '', url: ch ? 'https://www.youtube.com/channel/' + ch.id : '' }} }}];")
    nodes.append({"id": f"show{i}", "name": show, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [520, i * 160], "parameters": {"jsCode": code}})
    conn["Identificar"]["main"][0].append({"node": ask, "type": "main", "index": 0})
    conn[ask] = {"main": [[{"node": show, "type": "main", "index": 0}]]}
wf = {"name": "Identificar canales de YouTube", "nodes": nodes, "connections": conn, "settings": {"executionOrder": "v1"}, "pinData": {}}
target = Path(__file__).with_name("Identificar_Canales_YouTube.json")
target.write_text(json.dumps(wf, ensure_ascii=False, indent=1), encoding="utf-8")
print(target)
