#!/usr/bin/env python3
"""Convert previously-created Drive WORLD_MASTER into a LOCAL-ONLY optional 3D
tilepack for the modern NeuroCity renderer. Never uploads third-party assets,
private archives, labels, people or original NPL data to a public repository.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
from worldmaster_recovery import inventory_zip, glb_structural_qa, ROOT

SCHEMA="neurocity.local-worldmaster-tiles.v1"
SUPPORTED=("r02_c00","r02_c01","r01_c01","r01_c02")
ROLES=("terrain","geo","urban","environment","driving","beach",
        "architecture","lod","palm_variants","facade","landmark",
        "coast","mosaic","furniture","street")
PREFAB="assets/source/ASSETS/G15/phoenix/Phoenix_DatePalm_Variant_{:02d}.glb"

def compile_manifest(archive:Path):
    audit=inventory_zip(archive)
    if audit["errors"]:raise ValueError("Source archive has verification failures")
    with ZipFile(archive) as z:
        original=json.loads(z.read(ROOT+"world-master.json"))
        hashinfo={x["file"]:x for x in json.loads(z.read(ROOT+"source-hashes.json"))}
        seen={}
        def register(path,role,local=False,placements=None):
            if role not in ROLES:raise ValueError("Unrecognized 3D role")
            if not re.fullmatch(r"assets/[a-zA-Z0-9_./-]+\.glb",path) or ".." in Path(path).parts:
                raise ValueError("Forbidden asset path")
            if path not in seen:
                raw=z.read(ROOT+path)
                qa=glb_structural_qa(raw)
                digest=hashlib.sha256(raw).hexdigest()
                h=hashinfo.get(path)
                if h and (h["sha256"]!=digest or h["size"]!=len(raw)):
                    raise ValueError("Inherited source mismatch")
                seen[path]={"sha256":digest,"bytes":len(raw),
                    "source_hash_record":bool(h),"drawable_primitives":qa["drawable_primitives"]}
            asset={"role":role,"path":path,**seen[path]}
            if local:asset["local"]=True
            if placements:
                if len(placements)>150:raise ValueError("Excessive prop placements")
                asset["placements"]=[{
                    "x":float(p["x"]),"y":float(p["y"]),"z":float(p["z"]),
                    "scale":float(p.get("scale",1)),"rotation":float(p.get("rotation",0))
                } for p in placements]
            return asset
        tiles=[]
        for tile in SUPPORTED:
            assets=[]
            base=f"assets/source/ASSETS/tiles/{tile}/"
            for name in original["existingTileAssets"][tile]:
                # Existing archive names palmera tile layer 'palms'; it is distinct
                # from the six original Phoenix prefabs with approximate points.
                if name=="palms":continue
                role=name if name in ROLES else "urban"
                assets.append(register(base+name+".glb",role,local=name in ("terrain","geo")))
            if tile=="r02_c00":
                assets.append(register("assets/selected/Explanada_v50_PBR_1024.glb","mosaic"))
                assets.append(register("assets/selected/MASTER_EXPLANADA_FURNITURE_V50.glb","furniture"))
                assets.append(register("assets/selected/MASTER_BANCOS_G131_V50.glb","furniture"))
            if tile=="r02_c01":
                assets.append(register("assets/selected/r02_c01_G19_PUERTA_STONE_STREET.glb","street",local=True))
            if tile in ("r01_c01","r01_c02"):
                assets.append(register(f"assets/selected/{tile}_G19_BEACH_BASE_G05.glb","beach",local=True))
            for tag in original["monuments"]:
                if tag["tile"]==tile:assets.append(register(tag["path"],"landmark"))
            for item in original["façade_selected_by_cv05"]:
                if item["tile"]==tile:assets.append(register(item["path"],"facade"))
            for item in original["coastalScenes"]:
                if item["tile"]==tile:
                    assets.append(register(item["path"],"coast",local=item.get("local") is True))
            placements=[p for p in original["palm_positions"] if p["tile"]==tile]
            for variant in sorted({int(p["variant"]) for p in placements}):
                if variant<1 or variant>6:raise ValueError("Unknown palm version")
                assets.append(register(PREFAB.format(variant),"palm_variants",
                    placements=[p for p in placements if p["variant"]==variant]))
            # Stable deterministic priorities managed by the viewer.
            tiles.append({"id":tile,"assets":assets,
                          "source_grid":"UTM 500m tiles, mostly interpreted details",
                          "physical_grid_available":True})
        return {
            "schema":SCHEMA,"crs":"EPSG:25830",
            "viewer_crs":"EPSG:3857",
            "vertical_datum_verified":False,
            "facades_photogrammetric":False,
            "public_redistribution_allowed":False,
            "source_archive_sha256":audit["source_archive_sha256"],
            "source_manifest_entries_verified":audit["source_entries_verified"],
            "world_master_version":original["version"],
            "asset_count":len(seen),"tile_size_m":500,"tiles":tiles,
            "asset_hashes":seen,
            "attribution":"See original LICENSES/PROCEDENCIA files; do NOT deploy without a file-by-file rights review"
        }

def build_local_pack(archive:Path, out:Path, metadata_only=False):
    m=compile_manifest(archive)
    out.mkdir(parents=True,exist_ok=True)
    (out/"manifest.json").write_text(json.dumps(m,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (out/"REVIEW_BEFORE_SHARING.txt").write_text(
       "LOCAL NEUROCITY ASSETS FROM THE USER'S ORIGINAL GOOGLE DRIVE.\n"
       "NOT approved for public redistribution or publication.\n"
       "Some facades/terrain/palm positions and all store interiors are NOT surveyed.\n"
       "The vertical datum is unverified and the EPSG25830->3857 bridge is approximate.\n"
       "Never append private avatars, case data, real employee identities or unverified brands.\n",
       encoding="utf-8")
    if not metadata_only:
        with ZipFile(archive) as z:
            for path in sorted(m["asset_hashes"]):
                target=out/path
                target.parent.mkdir(parents=True,exist_ok=True)
                raw=z.read(ROOT+path)
                if hashlib.sha256(raw).hexdigest()!=m["asset_hashes"][path]["sha256"]:
                    raise ValueError("Bytes changed after audit: "+path)
                target.write_bytes(raw)
        # Source notice is NOT a rights grant.
        with ZipFile(archive) as z:
            (out/"ORIGINAL_SOURCE_NOTICE.md").write_bytes(
                z.read(ROOT+"LICENCIAS_PROCEDENCIA_WORLD_MASTER.md"))
    return m

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("archive",type=Path)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--metadata-only",action="store_true")
    args=parser.parse_args()
    m=build_local_pack(args.archive,args.output_dir,args.metadata_only)
    print(json.dumps({"tiles":len(m["tiles"]),"asset_count":m["asset_count"],
       "asset_bytes":sum(a["bytes"] for a in m["asset_hashes"].values()),
       "copied_to_local_only":not args.metadata_only,"rights_cleared":False},indent=2))
