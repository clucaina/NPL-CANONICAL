#!/usr/bin/env python3
"""Neurohuerto: permanent, bounded PUBLIC DATA QA lane.

Ingest source candidates from explicit public allowlist only.
Metadata-only reports; never exports rows to public interfaces or declares
human fact checking complete. No database mutations, model calls, or private data.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date,datetime,timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import re

PERIOD=re.compile(r"^(?:19|20)\d{2}(?:-(?:Q[1-4]|0[1-9]|1[0-2]))?$")
GEO=re.compile(r"^ES(?:[0-9]{2})?$")
SAFE_ID=re.compile(r"^[A-Z0-9_-]{2,110}$")
MAX_BATCH=2_000_000
def audit_batch(batch,spec,as_of=date.today()):
    errors=Counter()
    observed=set()
    groups=set()
    values=0
    ids=0
    if not isinstance(batch,dict) or not isinstance(batch.get("observations"),list):
        return {"status":"REJECTED_FORMAT","rows":0,"flags":{"invalid_batch":1},"ready_for_publication":False}
    if batch.get("batch_id")!=spec.get("batch_id"):errors["unexpected_batch_id"]+=1
    if len(batch["observations"])>20000:errors["excessive_rows"]+=1
    new_indicators=batch.get("new_indicators",[])
    if not isinstance(new_indicators,list):new_indicators=[]
    for item in new_indicators:
        if isinstance(item,dict) and SAFE_ID.fullmatch(str(item.get("indicator_id",""))):
            ids+=1
    for row in batch["observations"][:20000]:
        if not isinstance(row,dict):
            errors["invalid_row"]+=1
            continue
        indicator=str(row.get("indicator_id",""))
        geo=str(row.get("geo_code",""))
        period=str(row.get("period",""))
        subgroup=str(row.get("subgroup",""))
        val=row.get("value")
        if not SAFE_ID.fullmatch(indicator):errors["invalid_indicator"]+=1
        if not GEO.fullmatch(geo):errors["invalid_geo"]+=1
        if not PERIOD.fullmatch(period):errors["invalid_period"]+=1
        if PERIOD.fullmatch(period) and int(period[:4])>as_of.year:errors["future_period"]+=1
        unit=row.get("unit")
        if not isinstance(unit,str) or not unit.strip():errors["no_unit"]+=1
        if not isinstance(subgroup,str) or not subgroup.strip():errors["population_undefined"]+=1
        if val is None:errors["missing_measurement"]+=1
        elif isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(val):
            errors["non_finite_measurement"]+=1
        else:values+=1
        source_url=str(row.get("source_url",""))
        if not source_url.startswith("https://"):errors["missing_https_source"]+=1
        if not row.get("source_id"):errors["missing_source_id"]+=1
        key=(indicator,geo,period,subgroup)
        if key in observed:errors["duplicate_indicator_geography_period_population"]+=1
        observed.add(key)
        groups.add(indicator)
    return {"status":"REVIEW_REQUIRED" if not errors else "CANDIDATE_ERRORS",
            "batch_id":spec["batch_id"],"rows":len(batch["observations"]),
            "numeric_values":values,"distinct_candidate_indicators":len(groups),
            "new_indicator_definitions":ids,
            "license_claim":spec.get("license","UNRESOLVED"),
            "source_family":spec.get("source_family","UNKNOWN"),
            "flags":dict(sorted(errors.items())),
            "ready_for_publication":False,
            "human_source_review_completed":False,
            "note":"Automated syntactic checks only, not verification of truth, originality, reuse rights, denominators, causality or clinical validity."}
def open_public_source(url,fetcher=urlopen):
    if not url.startswith("https://raw.githubusercontent.com/clucaina/psicologia-politica/"):
        raise ValueError("Public origin not allowlisted")
    req=Request(url,headers={"User-Agent":"Neurohuerto-PublicData/1.0","Accept":"application/json"})
    with fetcher(req,timeout=20) as stream:raw=stream.read(MAX_BATCH+1)
    if len(raw)>MAX_BATCH:raise ValueError("Source over 2 MB bound")
    return json.loads(raw.decode("utf-8")),sha256(raw).hexdigest()
def run(spec,fetcher=open_public_source):
    results=[]
    for item in spec["sources"]:
        try:
            batch,digest=fetcher(item["raw_url"])
            result=audit_batch(batch,item)
            result["source_sha256"]=digest
            result["source_path"]=item["public_path"]
        except (OSError,ValueError,UnicodeError,HTTPError,URLError,KeyError,TypeError) as exc:
            # Never expose raw source bytes or exception messages (could contain tokens).
            result={"status":"SOURCE_UNAVAILABLE","batch_id":item.get("batch_id",""),
                    "source_path":item.get("public_path",""),"error_type":type(exc).__name__,
                    "ready_for_publication":False}
        results.append(result)
    return {"schema":"neurohuerto.data_garden.v1","generated_utc":datetime.now(timezone.utc).isoformat(),
            "workstream":"DATA_VERIFICATION_CANDIDATES_ONLY","no_private_sources":True,
            "no_automatic_publication":True,"candidates":results,
            "sources_examined":len(results),
            "candidates_requiring_review":sum(x.get("status")=="REVIEW_REQUIRED" for x in results),
            "sources_with_errors":sum(x.get("status")!="REVIEW_REQUIRED" for x in results)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    catalog=json.loads(a.catalog.read_text(encoding="utf-8"))
    if catalog.get("schema")!="neurohuerto.data_source_catalog.v1":raise SystemExit("unsupported catalog")
    for item in catalog.get("sources",[]):
        if not re.fullmatch(r"database/[A-Z0-9_-]+\.json",item.get("public_path","")):
            raise SystemExit("Public source allowlist violated")
    result=run(catalog)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"qa.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Neurohuerto · circuito de datos público, solo candidatos","",
           "No es una base de verdad validada. No se publican valores ni identificadores personales.",
           ""]
    for c in result["candidates"]:
        lines.append("## "+c.get("batch_id","UNNAMED"))
        lines.append("- Estado: "+c["status"])
        lines.append("- Filas comprobadas: "+str(c.get("rows",0)))
        lines.append("- Errores: "+json.dumps(c.get("flags",{}),ensure_ascii=False))
        lines.append("- Publicación automática: **NO**")
    (a.out/"QA_RESUMEN.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"sources":result["sources_examined"],"issues":result["sources_with_errors"],
                      "candidates_for_human_review":result["candidates_requiring_review"]}))
if __name__=="__main__":main()
