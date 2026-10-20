#!/usr/bin/env python3
"""Recover ORIGINAL but previously ignored WorldMaster 3D sidecars to LOCAL ONLY.
Keeps 2-metre physical map rasters, interaction anchors, PBR stone/water/sand,
four true old prefabs, selected unverified interiors and original tile palms.
No user/patient/employee identity should ever be inferred or published.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from zipfile import ZipFile
from worldmaster_recovery import ROOT

SAFE_PATH=re.compile(
  r"^(?:geo/data/physical_r[0-9]{2}_(?:c[0-9]{2}|cm[0-9]{2})\.json"
  r"|geo/(?:CONTRATO|PHYSICS)/[A-Za-z0-9_]+\.json"
  r"|assets/prefabs/(?:Banco_Modular_185cm|Farola_Globo_Simple_4m|Bolardo_Hierro_095m|CafeSet_terrazas)\.glb"
  r"|assets/source/ASSETS/G15/pbr/(?:limestone|sand|water)_(?:basecolor|normal)\.png"
  r"|assets/source/ASSETS/tiles/r[0-9]{2}_c[0-9]{2}/palms\.glb"
  r"|assets/source/ASSETS/G14/G14_(?:hotel_lobby_interpretative|terrace_functional_provisional)\.glb)$")
BLOCKED_TERMS=("patient","biometric","employee","client","lucia","private","case_")
def permitted(path):
    return isinstance(path,str) and SAFE_PATH.fullmatch(path) is not None and not any(
        k in path.lower() for k in BLOCKED_TERMS)

def category(path):
    if path.startswith("geo/data/"):return "provisional_collision_grid"
    if path.startswith("geo/"):return "synthetic_interaction_contract"
    if "/pbr/" in path:return "original_pbr_material"
    if "/prefabs/" in path:return "archived_3d_prefab"
    if path.endswith("/palms.glb"):return "archived_older_palm_geometry_dont_duplicate"
    if "hotel_lobby" in path:return "fictional_demo_interior_not_actual_business"
    if "terrace_functional" in path:return "fictional_demo_terrace_not_actual_business"
    raise ValueError("Missing source classification")

def sidecar_inventory(archive:Path,current_active_paths:set[str]):
    result={"schema":"neurocity.original-sidecars-local-only.v1",
        "source":"user_owned_archived_worldmaster",
        "redistribution_approved":False,"original_files_modified":0,
        "source_vertical_datum_verified":False,"physical_rasters_not_official_MDT":True,
        "modelled_real_employee_present":False,
        "records":[],"count_by_category":{},"collision_grid_count":0}
    with ZipFile(archive) as z:
        hashes=json.loads(z.read(ROOT+"source-hashes.json"))
        if not isinstance(hashes,list):raise ValueError("Unexpected original hash manifest")
        for row in hashes:
            path=row.get("file")
            if path in current_active_paths:continue
            if not permitted(path):raise ValueError("Sidecar source not permitted: "+str(path)[:80])
            content=z.read(ROOT+path)
            digest=hashlib.sha256(content).hexdigest()
            if digest!=row.get("sha256") or len(content)!=row.get("size"):
                raise ValueError("Source sidecar hash/size mismatch: "+path)
            detail={"path":path,"sha256":digest,"bytes":len(content),
                "category":category(path),"status":"RECOVERED_UNREVIEWED_FOR_PUBLIC_USE"}
            if detail["category"]=="provisional_collision_grid":
                record=json.loads(content)
                if record.get("step")!=2.0 or record.get("count")!=251:
                    raise ValueError("Unknown raster spacing or extent")
                if len(record.get("surface",[]))!=251 or len(record.get("height",[]))!=251:
                    raise ValueError("Malformed physical map raster")
                detail.update({"spacing_m":2,"rows":251,"cols":251,
                               "tile":record.get("tile"),"official_elevation":False})
                result["collision_grid_count"]+=1
            result["records"].append(detail)
            cat=detail["category"]
            result["count_by_category"][cat]=result["count_by_category"].get(cat,0)+1
    return result

def recover(archive:Path,worldmaster:Path,metadata_only=False):
    m=json.loads((worldmaster/"manifest.json").read_text())
    current=set(m.get("asset_hashes",{}))
    report=sidecar_inventory(archive,current)
    worldmaster.mkdir(parents=True,exist_ok=True)
    if not metadata_only:
        with ZipFile(archive) as z:
            for item in report["records"]:
                p=worldmaster/item["path"]
                p.parent.mkdir(parents=True,exist_ok=True)
                data=z.read(ROOT+item["path"])
                if hashlib.sha256(data).hexdigest()!=item["sha256"]:
                    raise ValueError("Original sidecar changed after audit")
                p.write_bytes(data)
    report["files_copied_to_local_only"]=0 if metadata_only else len(report["records"])
    report["asset_publication_not_authorized"]=True
    (worldmaster/"SOURCE_SIDECARS_INDEX.json").write_text(
      json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("zip_file",type=Path)
    p.add_argument("--local-worldmaster",type=Path,required=True)
    p.add_argument("--metadata-only",action="store_true")
    args=p.parse_args()
    report=recover(args.zip_file,args.local_worldmaster,args.metadata_only)
    print(json.dumps({"preserved":report["files_copied_to_local_only"],
     "2m_physical_grids":report["collision_grid_count"],
     "categories":report["count_by_category"],
     "license_clearance":"NOT_APPROVED"},indent=2))
