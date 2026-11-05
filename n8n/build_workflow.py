"""Writes the exportable workflow JSON. No credentials: it only calls local services."""
import json
from pathlib import Path

BASE = "http://127.0.0.1:8772"
STEPS = [("Historia", "/story"), ("Personaje", "/assets"), ("Fondos", "/backgrounds"), ("Narracion", "/narration"),
         ("Animacion", "/animation"), ("Render", "/render"), ("Validar", "/validate")]
nodes = [{"id": "webhook", "name": "Nuevo proyecto", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 200], "webhookId": "ai-animation-prototipo",
          "parameters": {"httpMethod": "POST", "path": "ai-animation-prototipo", "responseMode": "responseNode", "options": {}}}]
conn = {}
prev = "Nuevo proyecto"
for i, (name, path) in enumerate(STEPS):
    nodes.append({"id": name.lower(), "name": name, "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [240 * (i + 1), 200], "onError": "continueErrorOutput",
                  "parameters": {"method": "POST", "url": BASE + path, "sendBody": True, "specifyBody": "json", "jsonBody": "={{ JSON.stringify({ title: $('Nuevo proyecto').first().json.body?.title }) }}",
                                 "options": {"timeout": 2400000}}})
    if prev == "Nuevo proyecto":
        conn[prev] = {"main": [[{"node": name, "type": "main", "index": 0}]]}
    else:
        conn[prev] = {"main": [[{"node": name, "type": "main", "index": 0}], [{"node": "Error", "type": "main", "index": 0}]]}
    prev = name
conn[prev] = {"main": [[{"node": "Aprobado", "type": "main", "index": 0}], [{"node": "Error", "type": "main", "index": 0}]]}
x = 240 * (len(STEPS) + 1)
nodes += [
    {"id": "aprobado", "name": "Aprobado", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [x, 200],
     "parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2}, "combinator": "and",
                                   "conditions": [{"id": "qc", "leftValue": "={{ $json.passed }}", "rightValue": True, "operator": {"type": "boolean", "operation": "true", "singleValue": True}}]}, "options": {}}},
    {"id": "ok", "name": "Responder OK", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [x + 240, 100],
     "parameters": {"respondWith": "json", "responseBody": "={{ JSON.stringify({ status: 'completed', output: $json.output, report: $json.report, checks: $json.checks }) }}", "options": {}}},
    {"id": "qcfail", "name": "Responder QC fallido", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [x + 240, 300],
     "parameters": {"respondWith": "json", "responseBody": "={{ JSON.stringify({ status: 'qc_failed', report: $json.report, checks: $json.checks }) }}", "options": {"responseCode": 422}}},
    {"id": "error", "name": "Error", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [x, 480],
     "parameters": {"respondWith": "json", "responseBody": "={{ JSON.stringify({ status: 'error', node: $prevNode.name, detail: $json.error ?? $json }) }}", "options": {"responseCode": 500}}},
]
conn["Aprobado"] = {"main": [[{"node": "Responder OK", "type": "main", "index": 0}], [{"node": "Responder QC fallido", "type": "main", "index": 0}]]}
wf = [{"id": "AiAnimPrototipo01", "name": "AI Animation Studio - Prototype", "active": False, "nodes": nodes, "connections": conn, "settings": {"executionOrder": "v1"}, "pinData": {}, "versionId": "11111111-2222-4333-8444-555555555501"}]
Path(__file__).with_name("AI_Animation_Studio_Prototype.json").write_text(json.dumps(wf, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(nodes), "nodos")
