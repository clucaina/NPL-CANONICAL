#!/usr/bin/env python3
"""Free-CPU AI seed: exclusively PUBLIC open-source NeuroCity research.
No secrets, clinical data, customer files, commits, PRs, deployments or auto-approvals.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

FOCI={"VISUAL","DATOS","CONTENIDO","INTEGRACION","SEGURIDAD","GENERAL"}
MODEL="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF Q4_K_M (Apache-2.0)"
def parse_focus(text):
    m=re.search(r"(?m)^FOCO:\s*(VISUAL|DATOS|CONTENIDO|INTEGRACION|SEGURIDAD|GENERAL)\s*$",text)
    return m.group(1) if m else "GENERAL"
def prompt(focus="GENERAL"):
    assert focus in FOCI
    return (
        "Eres revisor de software open-source, no un programador con acceso a producción.\n"
        "Tienes SOLO contexto público de una demo geográfica experimental de Alicante.\n"
        "El pipeline OSM/PNOA/Blender genera un archivo GLB; 614 footprints, "
        "solo 2 etiquetas de altura OSM comprobadas en una ejecución del 19/10/2026. "
        "Una revisión de Chromium validó carga de seis grupos de mallas, pero NO certifica "
        "fotorrealismo, FPS, colisiones ni integración funcional con datos sociales.\n"
        "La ciudad real privada NeuroCity está en otra fuente canónica y NO debes decir que "
        "este prototipo público la sustituye.\n"
        f"Foco de revisión: {focus}.\n"
        "Diseña SOLO UNA mejora técnica concreta, sin inventar resultados.\n"
        "Devuelve: HIPOTESIS, CAMBIO PROPUESTO, ARCHIVOS PUBLICOS A INSPECCIONAR, "
        "PRUEBAS QUE PODRIAN FALSARLA, DATOS OBLIGATORIOS, LIMITES, CRITERIO DE ACEPTACION.\n"
        "No inventes nombres de archivos ni porcentajes. No pidas datos personales, "
        "avatares, credenciales o expedientes periciales. "
        "No afirmes que has realizado un cambio ni probado la interfaz.\n"
    )
def sanitize(text):
    # Machine content is untrusted and never executed. Avoid accidental publication of
    # generated private-data proposals. A strict refusal result is a safer fallback.
    patterns=[
        r"(?i)(?:sk-[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{15,})",
        r"(?i)\b(?:password|contrase[ñn]a|api[_ -]?key)\s*[:=]\s*\S+",
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        r"(?i)\b(?:DNI|NIE|paciente|peritado|expediente cl[ií]nico)\b"
    ]
    if any(re.search(p,text) for p in patterns):
        return "[PROPUESTA BLOQUEADA: posible información privada o petición de credenciales.]","blocked"
    # Strip llama.cpp banner, model filesystem path, echoed prompts, and CLI footer.
    # Only a separately detected hypothesis section may enter a shareable artifact.
    text=re.sub(r"\\x1b\\[[0-9;]*[A-Za-z]","",text)
    start=re.search(r"(?im)^\\s*(?:HIPOTESIS|HIPÓTESIS)\\s*:",text)
    if not start:
        return "[MODELO SIN HIPÓTESIS IDENTIFICABLE: ninguna propuesta válida.]","insufficient"
    body=text[start.start():]
    body=re.split(r"(?im)^\\s*Exiting\\.\\.\\.\\s*$",body)[0].strip()
    if len(body)<120:
        return "[MODELO SIN RESPUESTA ÚTIL: ninguna propuesta aprobada.]","insufficient"
    required=("CAMBIO PROPUESTO","PRUEBAS","CRITERIO DE ACEPTACION")
    if any(k not in body.upper() for k in required):
        return body[:6500],"candidate_unstructured_needs_review"
    if re.search(r"(?i)no hay datos obligatorios",body):
        return body[:6500],"candidate_requires_missing_evidence"
    return body[:6500],"candidate_unverified"
def output(model_output,focus,folder):
    cleaned,state=sanitize(model_output)
    record={
        "model":MODEL,"inference_trust":"unverified",
        "project":"neurocity-public-geographic-demo-only",
        "focus":focus,"review_status":state,
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "no_source_change":True,"no_private_data_read":True,
        "no_deployment":True,"no_scientific_claim":True,
        "model_output_sha256":hashlib.sha256(model_output.encode()).hexdigest(),
        "proposal":cleaned,
        "required_review":"Independent human/advanced-model code review, unit tests, browser QA and reference comparisons BEFORE any change",
        "observed_limit":"Only 2/614 OSM building heights were explicitly measured in the last referenced run. No inference about 612 individual heights is validated."
    }
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"candidate.json").write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding="utf-8")
    (folder/"candidate.md").write_text(
        "# NeuroCity open-source research proposal (UNVERIFIED)\n\n"+
        "**Status:** "+state+" · **Model:** "+MODEL+
        "\n\n**Nothing has been changed, approved or deployed.**\n\n"+
        cleaned+"\n",encoding="utf-8")
    print(json.dumps({"status":state,"length":len(cleaned),"focus":focus}))
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--focus-file",type=Path)
    ap.add_argument("--prompt-out",type=Path)
    ap.add_argument("--result-in",type=Path)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    focus=parse_focus(args.focus_file.read_text(encoding="utf-8",errors="replace")[:6000]) if args.focus_file and args.focus_file.exists() else "GENERAL"
    if args.prompt_out:
        args.prompt_out.write_text(prompt(focus),encoding="utf-8")
    if args.result_in:
        assert args.out is not None
        output(args.result_in.read_text(encoding="utf-8",errors="replace"),focus,args.out)
if __name__=="__main__":main()
