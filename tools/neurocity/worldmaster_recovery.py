#!/usr/bin/env python3
"""Audit and recover an EXISTING user-held NeuroCity world-master ZIP, without copying
assets into public GitHub or replacing gameplay. Input remains read-only.
Only public-safe aggregate metadata and checksums leave the process.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from zipfile import ZipFile

ROOT="NEUROCITY_WORLD_MASTER/"
EXPECTED_CRS="EPSG:25830"
MAX_ENTRIES=1200
MAX_ENTRY=90_000_000
MAX_TOTAL=550_000_000
HEX=re.compile(r"^[0-9a-f]{64}$")
SAFE_ASSET=re.compile(r"^(assets/(?:source/ASSETS/(?:tiles|G14|G15|G17)|selected|prefabs)/[a-zA-Z0-9_./-]+|geo/(?:data|CONTRATO|PHYSICS)/[a-zA-Z0-9_./-]+)$")
REJECT_PUBLIC=("person","patient","avatar","lucia","face","biometric","medical","fufu","rocketbox","private")

def glb_structural_qa(raw:bytes)->dict:
    if len(raw)<24 or raw[:4]!=b"glTF":
        raise ValueError("Missing binary glTF header")
    version,total=struct.unpack_from("<II",raw,4)
    if version!=2 or total!=len(raw):
        raise ValueError("GLB version or total length invalid")
    chunk_length,kind=struct.unpack_from("<I4s",raw,12)
    if kind!=b"JSON" or not (4<=chunk_length<=len(raw)-20):
        raise ValueError("Missing GLB JSON chunk")
    doc=json.loads(raw[20:20+chunk_length])
    if not isinstance(doc,dict) or not isinstance(doc.get("meshes"),list) or not doc["meshes"]:
        raise ValueError("GLB lacks meshes")
    accessors=doc.get("accessors",[])
    if not isinstance(accessors,list):
        raise ValueError("Invalid accessor metadata")
    draws=0
    for mesh in doc["meshes"]:
        if not isinstance(mesh,dict):continue
        for prim in mesh.get("primitives",[]):
            if not isinstance(prim,dict) or prim.get("mode",4)!=4:continue
            attrs=prim.get("attributes",{})
            pos=attrs.get("POSITION") if isinstance(attrs,dict) else None
            if isinstance(pos,int) and 0<=pos<len(accessors):
                n=accessors[pos].get("count",0)
                if isinstance(n,int) and n>=3:draws+=1
    if draws<1:raise ValueError("GLB has no drawable triangle primitives")
    return {"meshes":len(doc["meshes"]),"drawable_primitives":draws}

def sha_stream(z:ZipFile, name:str)->str:
    h=hashlib.sha256()
    with z.open(name) as stream:
        for block in iter(lambda:stream.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def inventory_zip(archive:Path)->dict:
    with ZipFile(archive) as z:
        files={i.filename:i for i in z.infolist() if not i.is_dir()}
        if len(files)>MAX_ENTRIES:raise ValueError("Too many archive entries")
        if any(not n.startswith(ROOT) or ".." in Path(n).parts or n.startswith("/") for n in files):
            raise ValueError("Archive paths leave expected project root")
        if any(x.file_size>MAX_ENTRY for x in files.values()) or sum(i.file_size for i in files.values())>MAX_TOTAL:
            raise ValueError("Archive uncompressed size exceeds audit budget")
        required=["world-master.json","source-hashes.json","README_WORLD_MASTER_ES.md","LICENCIAS_PROCEDENCIA_WORLD_MASTER.md"]
        if any(ROOT+n not in files for n in required):raise ValueError("Missing source manifest or license declaration")
        m=json.loads(z.read(ROOT+"world-master.json"))
        hashes=json.loads(z.read(ROOT+"source-hashes.json"))
        if m.get("geo",{}).get("crs")!=EXPECTED_CRS or m["geo"].get("vertical_datum") in ("",None):
            raise ValueError("World georeferencing or vertical disclaimer absent")
        if m.get("tile_ids")!=["r02_c00","r02_c01","r01_c01","r01_c02"]:
            raise ValueError("Unexpected world tile contract; requires review")
        if not isinstance(hashes,list):raise ValueError("Source hashes must be a list")
        errors=[];verified=0;glbs=[]
        for item in hashes:
            if not isinstance(item,dict):raise ValueError("Malformed source hash")
            relative=item.get("file")
            expected=item.get("sha256")
            if not isinstance(relative,str) or not SAFE_ASSET.fullmatch(relative) or any(x in relative.lower() for x in REJECT_PUBLIC):
                raise ValueError("Public-safe archive inventory contains forbidden file path")
            if not isinstance(expected,str) or not HEX.fullmatch(expected):
                raise ValueError("Invalid SHA256 in source manifest")
            path=ROOT+relative
            if path not in files:
                errors.append({"asset":relative,"reason":"MISSING"});continue
            if item.get("size")!=files[path].file_size:
                errors.append({"asset":relative,"reason":"SIZE_MISMATCH"});continue
            actual=sha_stream(z,path)
            if actual!=expected:
                errors.append({"asset":relative,"reason":"SHA256_MISMATCH"});continue
            verified+=1
            if relative.endswith(".glb"):
                try:
                    qa=glb_structural_qa(z.read(path))
                    glbs.append({"path":relative,"bytes":files[path].file_size,"sha256":actual,**qa})
                except Exception as e:
                    errors.append({"asset":relative,"reason":"GLB_INVALID_"+type(e).__name__})
        selected={}
        for group,prefix in {"mosaic":"assets/selected/Explanada_",
                             "palm_variants":"assets/source/ASSETS/G15/phoenix/",
                             "tiles":"assets/source/ASSETS/tiles/",
                             "facades":"assets/source/ASSETS/G15/frontage_",
                             "coastal":"assets/source/ASSETS/G17/",
                             "landmarks":"assets/source/ASSETS/G14/"}.items():
            selected[group]=sum(x["path"].startswith(prefix) for x in glbs)
        tiles={}
        for tid in m["tile_ids"]:
            names=[x for x in glbs if f"/tiles/{tid}/" in x["path"]]
            tiles[tid]={"verified_glb_count":len(names),
                        "bytes":sum(a["bytes"] for a in names),
                        "layers":sorted(x["path"].rsplit("/",1)[-1][:-4] for x in names)}
        return {
            "schema":"neurocity.recovered-worldmaster-audit.v1",
            "origin":"USER_OWNED_EXISTING_DRIVE_ARCHIVE",
            "asset_bytes_uploaded_to_public_repo":0,
            "source_archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
            "archive_bytes":archive.stat().st_size,
            "archive_file_entries":len(files),
            "source_hash_entries":len(hashes),
            "source_entries_verified":verified,
            "validated_glb_count":len(glbs),
            "selected_categories":selected,
            "tile_size_m":500,
            "tile_index":tiles,
            "coordinate_reference":m["geo"],
            "vertical_datum_verified":False,
            "photo_facades_verified":False,
            "license_cleared_for_public_redistribution":False,
            "physical_tile_count":sum(n.startswith(ROOT+"geo/data/physical_") for n in files),
            "errors":errors,
            "safe_glb_registry":glbs
        }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("zip_file",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=inventory_zip(args.zip_file)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in (
        "archive_file_entries","source_hash_entries","source_entries_verified",
        "validated_glb_count","selected_categories","physical_tile_count","errors"
    )},indent=2))
    if report["errors"]:raise SystemExit("FAILED: source hashes, data or GLBs invalid")

if __name__=="__main__":main()
