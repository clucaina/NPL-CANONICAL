#!/usr/bin/env python3
"""Neurohuerto / public data: bounded, repeatable candidate discovery.

Reads only the explicitly permitted public GitHub database directory.
Writes versioned metadata contracts into an isolated factory branch, never raw
observations or production code.  The second project may independently consume
these contracts, but NO source becomes approved or published automatically.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError, URLError
from data_garden import audit_batch,open_public_source

REPO="clucaina/psicologia-politica"
REF="integracion/v78-maestro-sin-despliegue"
DIR_API="https://api.github.com/repos/"+REPO+"/contents/database?ref="+REF.replace("/","%2F")
RAW_PREFIX="https://raw.githubusercontent.com/"+REPO+"/"+REF+"/"
FILENAME=re.compile(r"^database/(T[0-9]{1,4}_[A-Za-z0-9_-]+)\.json$")
MAX_BYTES=1_900_000
LIMIT=4
def source_listing(fetch_json):
    items=fetch_json(DIR_API)
    if not isinstance(items,list):raise ValueError("Unexpected source directory listing")
    safe={}
    for entry in items:
        if not isinstance(entry,dict) or entry.get("type")!="file":continue
        path=str(entry.get("path",""))
        match=FILENAME.fullmatch(path)
        size=entry.get("size",0)
        if not match or type(size)!=int or size<100 or size>MAX_BYTES:continue
        safe[match.group(1)]={"path":path,"source_blob_sha":str(entry.get("sha",""))}
    return safe
def discover(catalog,existing,fetch_json,fetch_batch,limit=LIMIT):
    if not isinstance(existing,dict):raise ValueError("Previous ledger must be a JSON object")
    if type(limit)!=int or not 1<=limit<=8:raise ValueError("Batch must contain 1..8 sources")
    curated={Path(x.get("public_path","")).stem for x in catalog.get("sources",[])}
    choices=source_listing(fetch_json)
    # Rotating source work is driven by stable previously preserved IDs; changing
    # source content is reported in the Data Garden, but not silently approved.
    waiting=sorted(set(choices)-curated-set(existing),
                   key=lambda v:(int(v.split("_")[0][1:]),v))
    chosen=waiting[:limit]
    new={}
    for stem in chosen:
        file=choices[stem]
        url=RAW_PREFIX+file["path"]
        try:
            data,digest=fetch_batch(url)
            spec={"batch_id":stem,"license":"NOT_VERIFIED_FOR_AUTOMATIC_REUSE",
                  "source_family":"UNREVIEWED_PUBLIC_RESEARCH",
                  "public_path":file["path"]}
            quality=audit_batch(data,spec)
            new[stem]={
                "schema":"neurohuerto.public_source_candidate.v1",
                "id":stem,"source_repository":REPO,"source_ref":REF,
                "source_path":file["path"],"source_blob_sha":file["source_blob_sha"],
                "raw_sha256":digest,"data_quality":quality["status"],
                "candidate_kind":"DOCUMENT_ONLY" if quality["status"]=="REJECTED_FORMAT" else "STATISTICAL_CANDIDATE",
                "independent_statistical_review_allowed":quality["status"]!="REJECTED_FORMAT",
                "rows_automatically_examined":quality["rows"],
                "quality_flags":quality.get("flags",{}),
                "review_state":"DOCUMENT_EXCLUDED" if quality["status"]=="REJECTED_FORMAT" else "NEEDS_INDEPENDENT_LICENSE_AND_METHOD_REVIEW",
                "release_gate":"NO_AUTO_IMPORT_NO_AUTO_DEPLOY",
                "raw_values_copied":False,
                "source_exists_in_catalog":False
            }
        except (OSError,ValueError,TypeError,HTTPError,URLError,KeyError,UnicodeError):
            new[stem]={"schema":"neurohuerto.public_source_candidate.v1",
                "id":stem,"source_repository":REPO,"source_ref":REF,
                "source_path":file["path"],"source_blob_sha":file["source_blob_sha"],
                "data_quality":"SOURCE_UNAVAILABLE",
                "review_state":"INVESTIGATE_SOURCE","release_gate":"NO_AUTO_IMPORT_NO_AUTO_DEPLOY",
                "raw_values_copied":False,"source_exists_in_catalog":False}
    return {
        "schema":"neurohuerto.source_discovery.v1",
        "public_source_count":len(choices),"curated_count":len(curated),
        "existing_candidates":len(existing),"new_candidates":len(new),
        "remaining_unexamined":len(waiting)-len(new),
        "candidates":new,
        "safety":"METADATA_ONLY_NOT_HUMAN_VERIFIED"
    }
def web_json(url):
    if url!=DIR_API:raise ValueError("Listing URL not allowlisted")
    req=Request(url,headers={"User-Agent":"Neurohuerto-Discovery/1.0","Accept":"application/vnd.github+json"})
    with urlopen(req,timeout=20) as response:
        raw=response.read(800_000)
        if response.read(1):raise ValueError("Overlong GitHub listing")
    return json.loads(raw)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--catalog",type=Path,required=True)
    ap.add_argument("--prior",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--limit",type=int,default=LIMIT)
    args=ap.parse_args()
    catalog=json.loads(args.catalog.read_text(encoding="utf-8"))
    old={}
    if args.prior.is_file():
        previous=json.loads(args.prior.read_text(encoding="utf-8"))
        for c in previous.get("candidates",[]):
            if isinstance(c,dict) and FILENAME.fullmatch(str(c.get("source_path",""))):
                old[c["id"]]=c
    result=discover(catalog,old,web_json,open_public_source,args.limit)
    args.out.mkdir(parents=True,exist_ok=True)
    for id,contract in result["candidates"].items():
        (args.out/(id+".json")).write_text(json.dumps(contract,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    merged={**old,**result["candidates"]}
    # No volatile timestamp: only commit if discovery genuinely changes source review state.
    index={"schema":"neurohuerto.candidate_ledger.v1","repository":REPO,
           "source_ref":REF,"candidates":[merged[k] for k in sorted(merged)],
           "publication_authorized":False,
           "candidate_count":len(merged)}
    args.prior.parent.mkdir(parents=True,exist_ok=True)
    args.prior.write_text(json.dumps(index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:result[key] for key in
        ("public_source_count","curated_count","existing_candidates","new_candidates","remaining_unexamined")},ensure_ascii=False))
if __name__=="__main__":main()
