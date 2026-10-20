#!/usr/bin/env python3
"""Conservative feedback from PP's independent public source review to NPL.
A downstream rejection improves routing but NEVER approves or alters source rows.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
SAFE=re.compile(r"^T[0-9]{1,4}_[A-Za-z0-9_-]+$")
def reconcile(catalog,reviews):
    if catalog.get("schema")!="neurohuerto.candidate_ledger.v1":
        raise ValueError("Unknown upstream catalogue")
    if reviews.get("schema")!="neurohuerto.independent_reviewer.v1":
        raise ValueError("Unknown independent review evidence")
    opinions={x["id"]:x for x in reviews.get("reviews",[]) if isinstance(x,dict) and SAFE.fullmatch(str(x.get("id","")))}
    touched=0
    updated=[]
    for cand in catalog.get("candidates",[]):
        if not isinstance(cand,dict) or not SAFE.fullmatch(str(cand.get("id",""))):raise ValueError("Unsafe contract ID")
        c=dict(cand)
        independent=opinions.get(c["id"])
        if independent:
            same_blob=independent.get("source_blob_sha")==c.get("source_blob_sha")
            same_data=independent.get("upstream_sha256")==c.get("raw_sha256")
            if same_blob and same_data and isinstance(independent.get("independent_check"),dict):
                check=independent["independent_check"]
                original=c.get("cross_review_status")
                assessment=check.get("status","UNKNOWN")
                c["cross_review_status"]=assessment
                c["independent_source_checked"]=True
                if assessment=="BLOCK_FORMAT_OR_ID" and c.get("data_quality")=="REJECTED_FORMAT":
                    c["candidate_type"]="PUBLIC_RESEARCH_DOCUMENT_NOT_STATISTICAL_OBSERVATIONS"
                    c["routing"]="RESEARCH_REVIEW_NOT_DATA_IMPORT"
                elif assessment=="BLOCK_SOURCE_CHANGED":
                    c["routing"]="STOP_SOURCE_MISMATCH_RECHECK_ORIGINAL"
                elif assessment=="NEEDS_SOURCE_AND_LICENSE_REVIEW":
                    c["routing"]="METHODOLOGICAL_SOURCE_REVIEW_REQUIRED"
                else:
                    c["routing"]="QUARANTINE_UNTIL_REVIEW"
                touched+=int(original!=c["cross_review_status"])
            else:
                # A stale, changed or injected downstream review never approves nor
                # silently replaces a previous evidence-confirmed classification.
                c["feedback_warning"]="UPSTREAM_DIGEST_OR_BLOB_MISMATCH"
        c["review_state"]="NEEDS_INDEPENDENT_LICENSE_AND_METHOD_REVIEW" if c.get("review_state")!="INVESTIGATE_SOURCE" else c["review_state"]
        c["release_gate"]="NO_AUTO_IMPORT_NO_AUTO_DEPLOY"
        c["raw_values_copied"]=False
        updated.append(c)
    return {"schema":"neurohuerto.candidate_ledger.v1",
      "repository":catalog.get("repository"),
      "source_ref":catalog.get("source_ref"),
      "candidates":updated,"candidate_count":len(updated),
      "feedback_changed":touched,
      "publication_authorized":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ledger",type=Path,required=True)
    p.add_argument("--review",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    args=p.parse_args()
    if not args.review.is_file() or not args.ledger.is_file():
        print('No independent feedback available; no changes.');return
    try:
        reviews=json.loads(args.review.read_text(encoding="utf-8"))
    except (ValueError,UnicodeError,OSError):
        print('Independent review malformed; no changes.');return
    original=json.loads(args.ledger.read_text(encoding="utf-8"))
    result=reconcile(original,reviews)
    args.ledger.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    args.out_dir.mkdir(parents=True,exist_ok=True)
    for c in result["candidates"]:
        dest=args.out_dir/(c["id"]+".json")
        if dest.is_file():
            dest.write_text(json.dumps(c,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"public_candidates":len(result["candidates"]),
        "cross_reviews_newly_applied":result["feedback_changed"],"publication_authorized":False}))
if __name__=="__main__":main()
