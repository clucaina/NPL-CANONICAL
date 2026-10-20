#!/usr/bin/env python3
"""Jardín Sináptico: read-only federated project pulse.

Architectural metaphor is operational:
  roots=isolated source of truth; mycelium=allowlisted typed *metadata*;
  sap=bounded work priority; buds=unverified proposals; fruit=verified results;
  quarantine=failures/regressions; stoma=privacy-safe public bulletin.
No accounts created, secrets used, deployments, or AI execution.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.request import Request, urlopen

ROOTS=[
 {"id":"neurocity","title":"NeuroCity","subtitle":"Ciudad 3D navegable","privacy":"public","source":"clucaina/NPL-CANONICAL","modules":["NPL","Conflictómetro"],"focus":"Realismo 3D, interacción, rendimiento y fuentes geográficas","position":[175,140],"next":"Comparación de renders con referencias y FPS real"},
 {"id":"neuropsicolucia","title":"Neuropsicolucía","subtitle":"Educación y experiencia","privacy":"private","source":None,"modules":[],"focus":"Contenido, accesibilidad y diseño editorial","position":[460,88],"next":"Comparar rama production con sitio real y pruebas"},
 {"id":"psicologia_politica","title":"Psicología Política","subtitle":"Observatorio contrastable","privacy":"public","source":"clucaina/psicologia-politica","modules":[],"focus":"Indicadores, periodismo y verificación","position":[740,156],"next":"Resolver gate NO-GO con fuente y hosting"},
 {"id":"apj","title":"APJ","subtitle":"Práctica pericial privada","privacy":"private","source":None,"modules":[],"focus":"Eficiencia, facturación y oportunidades legítimas","position":[140,370],"next":"Conectar versión canónica privada con consentimiento"},
 {"id":"sicnar","title":"SICNAR","subtitle":"Investigación metodológica","privacy":"private","source":None,"modules":[],"focus":"Contraste de hipótesis, límites y validación","position":[355,405],"next":"Pre-registrar rúbrica de validez, sesgos y acuerdo"},
 {"id":"voynich","title":"Voynich","subtitle":"Descifrado falsable","privacy":"research","source":None,"modules":[],"focus":"Cruces de folios, glifos, ilustraciones e hipótesis","position":[645,375],"next":"Asegurar corpus y transcripciones por folio"},
 {"id":"neurovida","title":"NeuroVida","subtitle":"Acceso, aprendizaje, autonomía","privacy":"private","source":None,"modules":["Semilla","Noema","NeuroPuente"],"focus":"Usabilidad sin conexión y pruebas de utilidad","position":[870,335],"next":"Recuperar fuentes canónicas y pilotos seguros"},
 {"id":"multife","title":"Multife","subtitle":"Religiones, evidencia y contexto","privacy":"research","source":None,"modules":[],"focus":"Comparaciones documentadas sin falsos universales","position":[775,585],"next":"Versionar textos y pasajes verificables"},
 {"id":"videoforge","title":"VideoForge","subtitle":"Vídeo local y reproducible","privacy":"private","source":None,"modules":[],"focus":"Pipeline local, vídeo y seguridad","position":[440,600],"next":"Prueba de compatibilidad y límites GPU"},
 {"id":"conciencia","title":"Conciencia","subtitle":"Investigación experimental","privacy":"research","source":None,"modules":[],"focus":"Protocolos replicables, controles y falsación","position":[185,598],"next":"Definir muestras públicas y protocolo preregistrado"}
]
# Edge contracts transfer only tiny, explicitly typed public or method-level
# metadata. An edge NEVER means a shared file system or client-data transfer.
EDGES=[
 {"from":"neurocity","to":"psicologia_politica","type":"public_indicator_schema","enabled":False},
 {"from":"apj","to":"sicnar","type":"methodology_only","enabled":False},
 {"from":"neurovida","to":"neuropsicolucia","type":"published_educational_method","enabled":False},
 {"from":"voynich","to":"multife","type":"public_source_criticism","enabled":False},
 {"from":"videoforge","to":"neurocity","type":"tool_capability_no_assets","enabled":False},
 {"from":"sicnar","to":"conciencia","type":"public_method_protocol","enabled":False}
]
PUBLIC_TYPES={"public_indicator_schema","published_educational_method","public_source_criticism","tool_capability_no_assets","public_method_protocol","methodology_only"}
ALLOWED_FIELDS={"edge_type","source_id","target_id","observation_hash","public_citation","review_status","version"}
SAFE_CITATION=re.compile(r"^https://(?:doi[.]org/|github[.]com/|www[.]openstreetmap[.]org/)[a-zA-Z0-9/_#.?&=%:+-]*$")
def transmit(edge,payload):
    """Returns a safe contracted signal, not arbitrary source data."""
    if edge not in EDGES or not edge["enabled"]: raise PermissionError("Synapse disabled until validation")
    if edge["type"] not in PUBLIC_TYPES:raise PermissionError("Signal type is not approved")
    if set(payload)-ALLOWED_FIELDS:raise PermissionError("Potentially sensitive payload field")
    if payload.get("edge_type")!=edge["type"] or payload.get("source_id")!=edge["from"] or payload.get("target_id")!=edge["to"]:
        raise PermissionError("Endpoint/type mismatch")
    if payload.get("review_status")!="APPROVED_PUBLIC_METADATA":raise PermissionError("Not peer-reviewed and approved")
    citation=payload.get("public_citation","")
    if citation and not SAFE_CITATION.fullmatch(citation):raise PermissionError("Citation is not allowlisted")
    hashv=payload.get("observation_hash","")
    if hashv and not re.fullmatch(r"[a-f0-9]{64}",hashv):raise PermissionError("Invalid digest")
    return dict(payload)
def fetch_public_repo(repo,opener=urlopen):
    url="https://api.github.com/repos/"+repo+"/actions/runs?per_page=30"
    headers={"User-Agent":"NeuralGarden-EvidenceGate/1","Accept":"application/vnd.github+json"}
    token=os.getenv("GITHUB_TOKEN","")
    if token:headers["Authorization"]="Bearer "+token
    req=Request(url,headers=headers)
    # The official GH CLI handles authenticated GitHub Actions APIs reliably.
    # Fixed allowlisted repo names only, never a user-controlled command.
    if os.getenv("GH_TOKEN") and shutil.which("gh"):
        result=subprocess.run(["gh","api","repos/"+repo+"/actions/runs?per_page=30"],
                              capture_output=True,text=True,timeout=24)
        if result.returncode!=0:raise ValueError("GitHub CLI evidence unavailable")
        obj=json.loads(result.stdout)
    else:
        with opener(req,timeout=18) as res:
            obj=json.loads(res.read(1000000))
    data=obj.get("workflow_runs",[])
    if not isinstance(data,list):raise ValueError("GitHub runs are malformed")
    runs=[]
    for t in data[:30]:
        if not isinstance(t,dict):continue
        name=str(t.get("name") or "")[:110]
        if not name:continue
        # Exclude this observatory and passive inventory jobs: prevent artificial "new progress" loops.
        if name.startswith(("Jardín Sináptico","Factory independent shift","NPL Alicante 3D - open city on free CPU")):continue
        runs.append({"name":name,"status":str(t.get("status","unknown"))[:25],
                     "conclusion":str(t.get("conclusion") or "pending")[:25],
                     "time":str(t.get("created_at") or "")[:35],
                     "url":str(t.get("html_url") or "")[:210],
                     "branch":str(t.get("head_branch") or "")[:120],
                     "sha":str(t.get("head_sha") or "")[:40]})
    return runs
def classify_ci(runs):
    """Inspect latest *completed* run per (workflow, branch).

    A successful unrelated workflow cannot clear a failing deployment gate,
    and an older failed attempt cannot override a later successful attempt
    of the same check on the same branch. This is CI state, not product proof.
    """
    latest={}
    for run in sorted(runs,key=lambda r:(r.get("time") or "",r.get("url") or ""),reverse=True):
        if run.get("status")!="completed":
            continue
        key=(run.get("name"),run.get("branch"))
        latest.setdefault(key,run)
    failures=[r for r in latest.values()
              if r.get("conclusion") in {"failure","timed_out","action_required"}]
    failures.sort(key=lambda r:(r.get("time") or "",r.get("url") or ""),reverse=True)
    if failures:
        return "CHECKS_FAILED",failures
    if any(r.get("conclusion")=="success" for r in latest.values()):
        return "CI_PRESENT_NOT_PRODUCT_VALIDATION",[]
    return "IN_PROGRESS_UNVERIFIED",[]

def choose_turns(states,budget=3,previous=None):
    """Finite-resource priority, safety-before-novelty, fair across eligible roots."""
    prev=previous or {}
    queue=[]
    for root in ROOTS:
        state=states[root["id"]]
        if not root["source"]:continue # don't pretend private corpora are available
        last=int(prev.get(root["id"],0))
        debt=4 if state["status"]=="CHECKS_FAILED" else 0
        aging=min(5,last) # neglected projects gain priority instead of starving
        weight=int(root["id"]=="neurocity")*3
        score=3+debt+weight+aging
        queue.append({"id":root["id"],"score":score,
                      "turn":"VERIFY_FAILURE" if debt else "VALIDATE_NEXT_INDEPENDENT_DELTA"})
    queue.sort(key=lambda t:(-t["score"],t["id"]))
    return queue[:max(0,budget)]
def assemble(fetcher=fetch_public_repo,previous=None):
    ids={r["id"] for r in ROOTS}
    if len(ids)!=len(ROOTS) or any(e["from"] not in ids or e["to"] not in ids for e in EDGES):
        raise ValueError("Broken botanical topology")
    outputs=[]
    state={}
    for root in ROOTS:
        runs=[];error=None
        if root["source"]:
            try:runs=fetcher(root["source"])
            except Exception as exc:error=type(exc).__name__+((":"+str(exc.code)) if hasattr(exc,"code") else "")
        failures=[]
        if not root["source"]:
            status="NEEDS_PRIVATE_CANONICAL_SOURCE" if root["privacy"]=="private" else "NEEDS_PUBLIC_CORPUS"
        elif error:status="SOURCE_UNREACHABLE"
        elif not runs:status="NO_RECENT_CI_OBSERVED"
        else:status,failures=classify_ci(runs)
        state[root["id"]]={"status":status}
        outputs.append({**root,"status":status,"verification_error":error,
                        "recent_runs":runs[:5],"failure_evidence":failures[:8],
                        "last_seen":runs[0]["time"] if runs else None,
                        "achievements_verified":False,
                        "note":"Passing a CI job is NOT evidence of scientific, functional or visual quality"})
    turns=choose_turns(state,previous=previous)
    report={"title":"Jardín Sináptico · Ecosistema federado","generated_utc":datetime.now(timezone.utc).isoformat(),
            "roots":outputs,"synapses":EDGES,"active_turns":turns,
            "safety":{"cross_project_signals_enabled":sum(int(x["enabled"]) for x in EDGES),
               "raw_data_transfers":0,"client_records_read":0,
               "automatic_deployments":0,"llm_code_generation":0},
            "limits":["Not all projects have executable sources","GitHub scheduler is periodic, not uninterrupted",
                      "The private repo is NOT accessed from this public coordinator",
                      "Observations are read-only API states; no unsupported progress is inferred"]}
    return report
def save(report,out,html_template=None):
    out.mkdir(parents=True,exist_ok=True)
    (out/"snapshot.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    if html_template:
        template=Path(html_template).read_text(encoding="utf-8")
        data=json.dumps(report,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
        if "__GARDEN_DATA__" not in template:raise ValueError("Viewer binding missing")
        (out/"index.html").write_text(template.replace("__GARDEN_DATA__",data),encoding="utf-8")
    lines=["# Jardín Sináptico · Observatorio público", "", "Generado: "+report["generated_utc"],"",
           "| Raíz autónoma | Estado verificado | Fuente accesible |","|---|---|---|"]
    lines.extend("| "+r["title"]+" | "+r["status"]+" | "+(r["source"] or "No conectada")+
                 " |" for r in report["roots"])
    lines+=["","## Turnos elegibles (nunca inventar trabajo realizado)"]
    lines+=["- "+t["id"]+" · "+t["turn"]+" · prioridad "+str(t["score"]) for t in report["active_turns"]]
    lines+=["","Las sinapsis están bloqueadas hasta aprobar contratos y procedencia. NO hay despliegue, IA programadora ni datos privados."]
    (out/"status.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return report
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--out",default="garden-output")
    a.add_argument("--html",default="cloud_factory/garden_view.html")
    args=a.parse_args()
    result=assemble()
    save(result,Path(args.out),args.html)
    print((Path(args.out)/"status.md").read_text(encoding="utf-8"))
