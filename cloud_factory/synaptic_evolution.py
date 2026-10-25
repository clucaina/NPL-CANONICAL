#!/usr/bin/env python3
"""Bounded experimental plasticity for the EXISTING public Neural Garden.

This is not a second agent, LLM, crawler or scheduler. It reads ONLY the
Garden's public GitHub CI observations, proposes falsifiable engineering checks,
remembers candidates between existing runs, and prunes duplicates. No client
content, model weights, telemetry, new cloud state or network calls.

NOT a certification of scientific originality or an executor of proposed work.
"""
from __future__ import annotations
from hashlib import sha256
import json
import re

SCHEMA="neurohuerto.evolution.v1"
MAX_CANDIDATES=2
MAX_HISTORY=32
MAX_BYTES=90_000
CI_URL=re.compile(r"^https://github\.com/clucaina/(NPL-CANONICAL|psicologia-politica)/actions/runs/[0-9]{1,18}$")
FINGERPRINT=re.compile(r"^[0-9a-f]{20}$")

# Each hypothesis is a verifiable engineering EXPERIMENT. The laboratory does
# not invent novelty, claim a measured outcome or move public data between repos.
# Only owners of two public roots have source-level observations in this Garden.
EXPERIMENTS={
 "neurocity":(
  ("render-parity","REVISAR VISOR 3D EN MÓVIL",
   "La escena accesible a móvil preserva elementos esenciales visibles en escritorio.",
   "Capturar el MISMO estado y fuente en dos tamaños; cotejar elementos, LOD, errores y accesibilidad.",
   "Un objeto crítico se pierde, se sustituye por un sustituto inferior o faltan capturas comparables."),
  ("provenance","PROCEDENCIA DE GEOMETRÍA",
   "Los objetos geográficos derivados se distinguen de mediciones originales verificadas.",
   "Tomar una muestra trazable de geometrías y contrastar origen, licencia, fecha y geometría real.",
   "Una geometría sin origen se presenta como medida o licencia no comprobada."),
  ("fallback","ALTERNATIVA SIN GPU",
   "Hay lectura útil incluso cuando WebGL no carga o el usuario reduce movimiento.",
   "Probar WebGL desactivado y navegación por teclado sin inyectar datos falsos.",
   "El visitante pierde contenido esencial o queda atrapado en controles inaccesibles."),
  ("performance","PRESUPUESTO DE RECURSOS",
   "La carga de un conjunto de mallas permanece dentro de límites medidos en el dispositivo objetivo.",
   "Recoger FPS, memoria y errores WebGL reales en equipos definidos, sin extrapolar emulaciones.",
   "Los límites fallan o solo se aportan benchmarks inventados."),
  ("source-drift","DERIVA DE FUENTES URBANAS",
   "Una actualización de las fuentes no convierte estimaciones en alturas o fachadas observadas.",
   "Comparar identificadores y SHA de fuente, conservando incertidumbre y fechas.",
   "Una diferencia de fuente crea certezas injustificadas o pierde procedencia."),
  ("consent","USABILIDAD SIN VIGILANCIA",
   "La interacción educativa conserva utilidad sin perfiles personales ni rastreo forzado.",
   "Probar la escena en sesión limpia sin cookies y comprobar todos los controles.",
   "El contenido exige seguimiento personal o utiliza métricas sin consentimiento.")
 ),
 "psicologia_politica":(
  ("missingness","AUSENCIA NO EQUIVALE A CERO",
   "Los mapas no convierten datos ausentes en valores cero ni inventan periodos.",
   "Inspeccionar casos sintéticos de 0, NULL, no disponible y distintos periodos.",
   "Un dato ausente se representa como 0 o como observación vigente."),
  ("ecological","AGREGADOS NO IDENTIFICAN PERSONAS",
   "El visor no transforma correlaciones territoriales en perfiles individuales.",
   "Crear un agregado sintético con contraejemplo y examinar titulares y fichas.",
   "El producto infiere conductas individuales desde promedios territoriales."),
  ("data-lineage","ORIGEN POR INDICADOR",
   "Cada serie muestra unidad, ámbito, fecha y fuente antes de compararla.",
   "Contrastar metadatos de tres indicadores públicos contra su fuente primaria.",
   "Una comparación usa unidades o periodos incompatibles sin advertencia."),
  ("release-gate","VERSIONES Y ESTADO DE PRODUCCIÓN",
   "Un código que pasa pruebas no se describe como desplegado sin verificación HTTP pública.",
   "Comparar SHA, pruebas y versión de hosting sin escribir en producción.",
   "La interfaz pública carece del cambio aunque el repositorio lo marque completado."),
  ("cause","CAUSALIDAD NO DERIVADA DEL TITULAR",
   "Una diferencia de proporciones se presenta con sus límites y alternativas.",
   "Falsar una interpretación causal usando variables omitidas en un caso sintético.",
   "La presentación afirma causalidad solo por una correlación o tendencia."),
  ("accessible","LECTURA DE CIFRAS ACCESIBLE",
   "Mapa y tabla comunican el mismo denominador y sentido de la incertidumbre.",
   "Comparar salida accesible con el gráfico ante teclado y lector de pantalla.",
   "El dato o su límite desaparece en la versión no visual.")
 )
}
_PUBLIC_REPOS={
 "neurocity":"clucaina/NPL-CANONICAL",
 "psicologia_politica":"clucaina/psicologia-politica"
}

def _memory(previous):
    """Reject malformed/untrusted state rather than copying arbitrary fields."""
    if not isinstance(previous,dict):return []
    try:
        if len(json.dumps(previous,ensure_ascii=True))>MAX_BYTES:return []
    except (ValueError,TypeError,OverflowError):return []
    stored=previous.get("evolution")
    if not isinstance(stored,dict) or stored.get("schema")!=SCHEMA:return []
    ids=stored.get("recent_ids")
    if not isinstance(ids,list) or len(ids)>MAX_HISTORY:return []
    if not all(type(x) is str and FINGERPRINT.fullmatch(x) for x in ids):return []
    return list(dict.fromkeys(ids))

def _observed_run(root):
    if not isinstance(root,dict):return None
    repo=_PUBLIC_REPOS.get(root.get("id"))
    if not repo or root.get("source")!=repo:return None
    runs=root.get("recent_runs")
    if not isinstance(runs,list):return None
    # Latest completed per workflow; do not re-open a superseded failure.
    latest={}
    for run in runs[:12]:
        if not isinstance(run,dict) or run.get("status")!="completed":continue
        name=run.get("name")
        url=run.get("url")
        when=run.get("time","")
        if type(name) is not str or not (1<=len(name)<=110):continue
        if type(url) is not str or not CI_URL.fullmatch(url) or ("/"+repo.split("/")[1]+"/") not in url:continue
        if type(when) is not str or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",when):continue
        if run.get("conclusion") not in ("success","failure"):continue
        if name not in latest or when>latest[name]["time"]:latest[name]=run
    if not latest:return None
    failures=[r for r in latest.values() if r["conclusion"]=="failure"]
    return max(failures or list(latest.values()),key=lambda r:r["time"])

def evolve(report,previous=None,budget=MAX_CANDIDATES):
    if type(budget) is not int or budget<0 or budget>MAX_CANDIDATES:
        raise ValueError("Only 0..2 public research hypotheses per pulse")
    if not isinstance(report,dict) or not isinstance(report.get("roots"),list):
        raise TypeError("Missing public Garden root inventory")
    previously=_memory(previous)
    seen=set(previously)
    candidates=[]
    available=0
    rejected=0
    for root in report["roots"]:
        if not isinstance(root,dict):continue
        root_id=root.get("id")
        run=_observed_run(root)
        if run is None:continue
        available+=1
        for code,title,hypothesis,measurement,falsifier in EXPERIMENTS[root_id]:
            signature=sha256((root_id+"|"+code+"|"+run["url"]+"|"+run["conclusion"]).encode()).hexdigest()[:20]
            if signature in seen:
                rejected+=1
                continue
            # This prioritizes unresolved real failures over unvalidated
            # innovation work, but does not claim we have reproduced either.
            is_failure=run["conclusion"]=="failure"
            priority=(100 if is_failure else 25)+(10 if code in ("render-parity","missingness","source-drift") else 0)
            candidates.append({
                "id":signature,"root":root_id,"track":code,"title":title,
                "hypothesis":hypothesis,"test_to_run":measurement,"falsifier":falsifier,
                "evidence_url":run["url"],"evidence_kind":"LATEST_PER_WORKFLOW_FAILED_CI" if is_failure else "CI_OBSERVED_NOT_PRODUCT_VALIDATION",
                "priority":priority,
                "status":"ENGINEERING_HYPOTHESIS_REQUIRES_REAL_TEST",
                "is_global_invention":False,"code_changed":False,
                "scientific_validation":False,"deployment":False
            })
    candidates.sort(key=lambda p:(-p["priority"],p["root"],p["track"],p["id"]))
    selected=candidates[:budget]
    # Limit memory: no histories of users, article content or raw CI logs.
    history=(previously+[p["id"] for p in selected])[-MAX_HISTORY:]
    return {
        "schema":SCHEMA,"mode":"READ_ONLY_EXPERIMENT_TRIAGE",
        "scope":"TWO_PUBLIC_SOURCE_ROOTS_ONLY",
        "evidence_roots":available,"candidate_combinations_checked":len(candidates)+rejected,
        "repeat_candidates_pruned":rejected,"unproven_hypotheses_created":len(selected),
        "hypotheses":selected,"recent_ids":history,
        "last_pulse_made_code_changes":False,
        "originality_verified":False,"real_world_effect_verified":False,
        "active_workers_claimed":0,"private_data_transferred":0,
        "publication_authorized":False,"external_accounts_touched":False,
        "last_pulse_result":"NOVEL_TEST_PROPOSAL_ONLY" if selected else "NO_NEW_VERIFIABLE_HYPOTHESIS",
        "note":"Diversity and deduplication are local to observed public run fingerprints; NOT claims of world-first inventions or automatic execution."
    }

def markdown(result):
    if result.get("schema")!=SCHEMA:raise ValueError("Invalid experiment report")
    lines=[
     "## Plasticidad experimental · propuestas NO validadas",
     "",
     "Se han considerado "+str(result["candidate_combinations_checked"])+
     " hipótesis técnicas; duplicadas descartadas "+str(result["repeat_candidates_pruned"])+
     ". **Esto no ejecuta los experimentos ni demuestra inventos.**",
    ]
    for x in result["hypotheses"]:
        lines+=["","- **"+x["root"]+" · "+x["title"]+"**: "+x["hypothesis"],
                "  - Falsación propuesta: "+x["falsifier"],
                "  - Evidencia de CI (no validación de producto): "+x["evidence_url"]]
    if not result["hypotheses"]:lines+=["","- Sin hallazgos nuevos verificables que justifiquen otro candidato."]
    lines+=["","La web privada y los datos personales permanecen fuera de este motor."]
    return "\n".join(lines)+"\n"
