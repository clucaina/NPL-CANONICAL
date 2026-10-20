#!/usr/bin/env python3
"""Cross-chat NeuroCity branch-head ledger.

Inspects the actual Git repository (not chat transcripts) and records which
public source lines can be converged. READ ONLY. Does not import GML/GLB bytes,
patient data, private Drive assets, or modify any refs or the user's site.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

SOURCES = (
    ("g19_v50_current", "fix/neurocity-v7-g19-continuous-wall-sweep-20261020", True),
    ("cadastre_browser_acceptance", "feat/neurocity-collision-physical-acceptance-20261020", True),
    ("multi_source_rehearsal", "ci/neurocity-multi-source-unification-rehearsal-20261020", True),
    ("private_assembly_code_only", "tools/neurocity-private-world-reproducible-assembler-20261020", False),
)
UNSAFE_BYTES_PATTERN = re.compile(r"(^|/)(world-master|patient_data|private_glbs)/|\.(glb|gml|blend|las|laz)$", re.I)
REQUIRED_AT_LEAST_ONE = {
    "public_city_viewer": "demos/npl-world/visual_viewer/app.js",
    "public_npl_contract": "demos/npl-world/visual_viewer/public_layers.mjs",
    "public_spatial_collision": "demos/npl-world/visual_viewer/city_collision.mjs",
}
def git(repo: Path, *args: str, check=True) -> str:
    p = subprocess.run(("git", "-C", str(repo), *args),
                       text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=False, timeout=20)
    if check and p.returncode:
        raise RuntimeError("git operation failed: " + " ".join(args[:2]) +
                           " (exit " + str(p.returncode) + ")")
    return p.stdout.strip() if p.returncode == 0 else ""

def changes(repo:Path, source_ref:str, base_ref:str="origin/main")->list[str]:
    merge_base=git(repo,"merge-base",base_ref,source_ref)
    return sorted(filter(None,git(repo,"diff","--name-only",merge_base,source_ref,
                                  "--","demos/npl-world","tools/neurocity",
                                  ".github/workflows").splitlines()))

def overlaps(change_sets:dict[str,list[str]]) -> list[dict]:
    result=[]
    labels=sorted(change_sets)
    for i,left in enumerate(labels):
        for right in labels[i+1:]:
            paths=sorted(set(change_sets[left])&set(change_sets[right]))
            if paths:
                result.append({"left":left,"right":right,"overlapping_paths":paths,
                               "requires_semantic_merge":True})
    return result

def audit(repo:Path, sources=SOURCES, base_ref="origin/main")->dict:
    repo=Path(repo).resolve()
    base=git(repo,"rev-parse","--verify",base_ref+"^{commit}")
    refs=[];change_sets={};required_missing=[]
    for label,branch,required in sources:
        if not re.fullmatch(r"[a-z0-9_\-]+",label):
            raise ValueError("unsafe label")
        if not re.fullmatch(r"[A-Za-z0-9_./\-]+",branch) or ".." in branch:
            raise ValueError("unsafe source name")
        ref="refs/remotes/origin/"+branch
        sha=git(repo,"rev-parse","--verify",ref+"^{commit}",check=False)
        if not re.fullmatch(r"[a-f0-9]{40}",sha):
            refs.append({"label":label,"branch":branch,"required":required,
                         "state":"MISSING_REF"})
            if required:required_missing.append(label)
            continue
        paths=changes(repo,sha,base_ref)
        if any(UNSAFE_BYTES_PATTERN.search(p) for p in paths):
            # Paths only, never output source bytes; privacy risk is a STOP.
            raise RuntimeError("privacy-sensitive path in candidate "+label)
        change_sets[label]=paths
        refs.append({"label":label,"branch":branch,"required":required,
                     "sha":sha,"state":"FOUND_SOURCE",
                     "changed_paths_from_main":len(paths),
                     "paths":paths,
                     "integration_certified":False})
    required_coverage={}
    for capability,path in REQUIRED_AT_LEAST_ONE.items():
        supported=[]
        for item in refs:
            if item["state"]!="FOUND_SOURCE":continue
            # No blob bytes are opened. 'ls-tree' only lists tracked paths
            # in the branch's commit tree.
            if git(repo,"ls-tree","--name-only",item["sha"],path)==path:
                supported.append(item["label"])
        required_coverage[capability]={"path":path,"sources":supported,
                                      "available":bool(supported)}
        if not supported:required_missing.append(capability)
    cross=overlaps(change_sets)
    return {
        "schema":"neurocity.cross_chat_head_lineage.v1",
        "generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_ref":base_ref,"base_sha":base,
        "sources":refs,
        "overlaps":cross,
        "required_source_gaps":required_missing,
        "required_sources_available":not required_missing,
        "overlapping_paths_total":sum(len(x["overlapping_paths"]) for x in cross),
        "no_merges_or_deployments":True,
        "patient_or_private_bytes_read":False,
        "semantic_integration_certified":False,
        "note":"A common filename is not proof of compatible code. Only tests after an exact merge can certify compatibility."
    }

def markdown(report:dict)->str:
    out=["# NeuroCity — cruce real de ramas antes de desarrollar",
         "", "Base: `"+report['base_ref']+"` @ `"+report['base_sha'][:12]+"`.",
         "", "Este informe compara fuentes Git verificadas, no resultados narrados de chats.",
         "NO fusiona, despliega, lee datos privados ni acredita realismo.",
         ""]
    for item in report["sources"]:
        out.append("- **"+item["label"]+"**: "+item["state"]+
                   (" @ `"+item["sha"][:12]+"`" if "sha" in item else "")+
                   " ("+str(item.get("changed_paths_from_main",0))+" archivos cambiados).")
    out.extend(["","## Solapamientos que requieren decisión de ingeniería",""])
    for item in report["overlaps"]:
        out.append("### "+item["left"]+" × "+item["right"])
        out.extend("- `"+path+"`" for path in item["overlapping_paths"])
    if not report["overlaps"]:out.append("Sin rutas compartidas detectadas; NO equivale a integración validada.")
    out.extend(["","## Contratos y bloqueos",""])
    if report["required_source_gaps"]:
        out.append("FALTAN: "+", ".join(report["required_source_gaps"]))
    else:out.append("Fuentes requeridas presentes; siguen pendientes pruebas de integración semántica.")
    out.append("Siguiente acción: fusionar SOLO en workspace efímero, revisar conflictos línea a línea, ejecutar pruebas y QA WebGL. No publicar.")
    return "\n".join(out)+"\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    result=audit(a.repo)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/"CROSS_CHAT_LINEAGE.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    (a.output_dir/"CROSS_CHAT_LINEAGE.md").write_text(markdown(result),encoding="utf-8")
    print("NEUROCITY_CROSS_CHAT_LINEAGE",len(result["sources"]),"refs",
          len(result["overlaps"]),"overlap pairs",
          "required source gaps:",len(result["required_source_gaps"]))
    if result["required_source_gaps"]:raise SystemExit(2)

if __name__=="__main__":main()
