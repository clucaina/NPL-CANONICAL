#!/usr/bin/env python3
"""Read-only integration rehearsal of NeuroCity branches; commits exist only on the runner.

This script NEVER pushes/merges GitHub PRs. It makes disposable merges in a
detached CI checkout. Source origins stay separate; no local private GLBs are read.
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

CANDIDATES = (
    ("sea", "29"),
    ("cadastre", "36"),
    ("educational_gameplay", "33"),
)
PRIVATE_EXTS={".glb",".gltf",".zip",".p12",".pem",".key"}
SENSITIVE_HINTS=("patient", "case_", "peritado", "expediente", "dni", "clinical")


def run(*argv, cwd=None, check=False):
    result=subprocess.run(argv,cwd=cwd,encoding="utf8",capture_output=True,check=False)
    if check and result.returncode:
        raise RuntimeError("Command failed: "+str(argv[:3])+" "+(result.stderr or result.stdout)[-600:])
    return result


def suspicious_paths(paths):
    """Flag newly introduced risky paths, not source files already in the baseline."""
    out=[]
    for p in paths:
        low=p.lower()
        if pathlib.PurePosixPath(p).suffix.lower() in PRIVATE_EXTS or any(s in low for s in SENSITIVE_HINTS):
            out.append(p)
    return out


def outstanding_conflicts(repo):
    res=run("git","diff","--name-only","--diff-filter=U",cwd=repo,check=True)
    return [p for p in res.stdout.splitlines() if p]


def try_merge(repo, ref):
    res=run("git","-c","user.name=NeuroCity CI","-c",
            "user.email=neurocity-ci@users.noreply.github.com",
            "merge","--no-ff","--no-edit",ref,cwd=repo)
    data={"ref":ref,"clean":res.returncode==0,"conflicts":outstanding_conflicts(repo),
          "git_exit":res.returncode,"detail":(res.stderr or res.stdout)[-380:]}
    return data


def clean_checkout(repo, baseline):
    # Strictly local, isolated GitHub Actions checkout, no remote write.
    run("git","merge","--abort",cwd=repo)
    run("git","reset","--hard",baseline,cwd=repo,check=True)
    run("git","clean","-fd",cwd=repo,check=True)


def review(repo, report):
    cwd=pathlib.Path(repo).resolve()
    if not (cwd/".git").exists():
        raise ValueError("A fresh git checkout root is required")
    origin=run("git","remote","get-url","origin",cwd=cwd,check=True).stdout.strip()
    if origin and "clucaina/NPL-CANONICAL" not in origin:
        raise ValueError("Not the authoritative NeuroCity repository")
    dirty=run("git","status","--porcelain",cwd=cwd,check=True).stdout.strip()
    if dirty:
        raise ValueError("Refusing destructive rehearsal in a dirty checkout")
    baseline=run("git","rev-parse","HEAD",cwd=cwd,check=True).stdout.strip()
    digest=lambda s:hashlib.sha256(s.encode()).hexdigest()
    data={"schema":"neurocity.integration-rehearsal.v1","baseline":baseline,
          "never_push":True,"private_bytes_loaded":False,"origin_repo":"clucaina/NPL-CANONICAL",
          "isolated":[],"combined":[],"ready_for_merge":False,"runtime_webgl_verified":False,"ready_for_build":False}
    refs=[]
    for name,num in CANDIDATES:
        ref="refs/remotes/neurocity-ci/pr"+num
        fetched=run("git","fetch","--no-tags","origin",
                    "+refs/pull/"+num+"/head:"+ref,cwd=cwd)
        entry={"candidate":name,"pr":int(num),"fetched":fetched.returncode==0,
               "fetch_error":(fetched.stderr or "")[-220:]}
        data["isolated"].append(entry)
        if fetched.returncode!=0:
            continue
        refs.append((name,ref))
        merged=try_merge(cwd,ref)
        entry.update(merged)
        if merged["clean"]:
            diff=run("git","diff","--name-only",baseline+"..HEAD",cwd=cwd,check=True).stdout.splitlines()
            entry["file_count"]=len(diff)
            entry["risky_added_paths"]=suspicious_paths(diff)
            entry["changed_file_sha"]=digest("\n".join(sorted(diff)))
            entry["source_only_candidate"]=not entry["risky_added_paths"]
        clean_checkout(cwd,baseline)
    if len(refs)==len(CANDIDATES):
        # Apply the known compatible Gameplay candidate first, but never
        # claim the ocean/Catastro candidates succeeded when Git flags conflicts.
        accepted=[]
        review_pending=[]
        # Known source conflict from the first REAL merge rehearsal.
        # Do not invent a merge: preserve V50/G13 physical and coast safeguards
        # for a synthetic compilation trial, and mark human review mandatory.
        allowed_resolution={
            "demos/npl-world/visual_viewer/city_tiles.mjs",
            "demos/npl-world/visual_viewer/water_surface.mjs",
            "demos/npl-world/visual_viewer/tests/water_surface.test.mjs"
        }
        rank={"educational_gameplay":0,"sea":1,"cadastre":2}
        for name,ref in sorted(refs,key=lambda item:rank[item[0]]):
            outcome=try_merge(cwd,ref)
            outcome["candidate"]=name
            data["combined"].append(outcome)
            if not outcome["clean"]:
                conflicts=set(outcome["conflicts"])
                if name in ("sea","cadastre") and conflicts and conflicts<=allowed_resolution:
                    # TEMPORARY CI-only resolution, not a PR merge approval.
                    for filepath in sorted(conflicts):
                        run("git","checkout","--ours","--",filepath,cwd=cwd,check=True)
                        run("git","add","--",filepath,cwd=cwd,check=True)
                    result=run("git","-c","user.name=NeuroCity CI","-c",
                               "user.email=neurocity-ci@users.noreply.github.com",
                               "commit","--no-edit",cwd=cwd)
                    if result.returncode==0:
                        outcome["source_resolved_for_tests"]=True
                        outcome["human_review_required"]=sorted(conflicts)
                        review_pending+=sorted(conflicts)
                        accepted.append(name)
                        continue
                run("git","merge","--abort",cwd=cwd)
                continue
            accepted.append(name)
        changed=run("git","diff","--name-only",baseline+"..HEAD",cwd=cwd,check=True).stdout.splitlines()
        data["combined_changed_files"]=len(changed)
        data["risky_paths"]=suspicious_paths(changed)
        data["accepted_source_modules"]=accepted
        data["conflicts_resolved_only_for_qa"]=sorted(set(review_pending))
        data["ready_for_build"]=len(accepted)>0 and not data["risky_paths"]
        data["ready_for_merge"]=len(accepted)==len(CANDIDATES) and not data["risky_paths"] and not review_pending
    report=pathlib.Path(report)
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    # Leave clean source checkout for CI compilation even if a merge failed.
    # On a successful combined rehearsal, preserve unpushed HEAD for build/tests.
    print(json.dumps({"baseline":baseline[:12],"isolated":data["isolated"],
                      "combined":data["combined"],"ready_for_merge":data["ready_for_merge"]},
                     ensure_ascii=False))
    if not data["ready_for_merge"]:
        return 2
    return 0


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",default=".")
    p.add_argument("--report",required=True)
    args=p.parse_args()
    return review(args.repo,args.report)


if __name__=="__main__":
    sys.exit(main())
