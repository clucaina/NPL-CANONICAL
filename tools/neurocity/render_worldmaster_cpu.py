#!/usr/bin/env python3
"""Render EXISTING worldmaster glTF meshes with software VTK/Xvfb (no browser).
Not a live-game screenshot, surveyed reconstruction, or permission to redistribute.
On Linux: xvfb-run -a python3 tools/neurocity/render_worldmaster_cpu.py
                  --pack /path/to/local/world-master --output /path/to/qa.png
Never commits/exports original GLB bytes or faces. Only a still for owner review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

SAFE_ROLES={"terrain","urban","geo","architecture","mosaic","furniture",
            "landmark","coast","palm_variants"}
MAX_FILES=35
MAX_SOURCE_BYTES=90_000_000
MAX_POSES=100

def select_qa_assets(manifest,sector="r02_c00"):
    if not isinstance(manifest,dict) or manifest.get("schema")!="neurocity.local-worldmaster-tiles.v1":
        raise ValueError("Wrong original-world contract")
    if manifest.get("public_redistribution_allowed") is not False:
        raise ValueError("Refuse pack with unverified publication rights")
    tile=next((t for t in manifest.get("tiles",[]) if t.get("id")==sector),None)
    if tile is None:raise ValueError("Recovered 500m sector absent")
    picked=[a for a in tile["assets"] if a.get("role") in SAFE_ROLES and
            a.get("role")!="landmark" or False]
    # Restore exactly three source-identified landmarks and the original
    # source six Phoenix geometries, never inferred 3D staff or private avatars.
    picked=[a for a in tile["assets"] if a.get("role") in SAFE_ROLES]
    if len(picked)>MAX_FILES:raise ValueError("Unsafe scene asset count")
    return picked

def audit_file(pack:Path,asset:dict)->Path:
    value=asset.get("path")
    if not isinstance(value,str) or len(value)>200 or not value.endswith(".glb"):
        raise ValueError("Unexpected model file path")
    parts=Path(value).parts
    if parts[0]!="assets" or ".." in parts or value.startswith("/"):
        raise ValueError("Path escape")
    if any(s in value.lower() for s in ("private","avatar","patient","face","lucia","fufu")):
        raise ValueError("Cannot render protected characters")
    path=pack/value
    length=asset.get("bytes")
    if not isinstance(length,int) or length<1 or length>MAX_SOURCE_BYTES or path.stat().st_size!=length:
        raise ValueError("Source file byte mismatch")
    if hashlib.sha256(path.read_bytes()).hexdigest()!=asset.get("sha256"):
        raise ValueError("Source GLB SHA256 mismatch")
    return path

def run(pack:Path,output:Path,sector="r02_c00"):
    manifest=json.loads((pack/"manifest.json").read_text(encoding="utf-8"))
    selected=select_qa_assets(manifest,sector)
    audited=[(asset,audit_file(pack,asset)) for asset in selected]
    import vtk
    ren=vtk.vtkRenderer()
    ren.SetBackground(0.59,0.75,0.87)
    ren.SetBackground2(0.9,0.94,0.98)
    ren.GradientBackgroundOn()
    rw=vtk.vtkRenderWindow();rw.SetSize(1500,900)
    rw.OffScreenRenderingOn();rw.AddRenderer(ren)
    refs=[];entries=[]
    row=int(sector[1:3]);col=int(sector[-2:])
    for asset,path in audited:
        internal=vtk.vtkRenderWindow();internal.OffScreenRenderingOn()
        importer=vtk.vtkGLTFImporter()
        importer.SetFileName(str(path));importer.SetRenderWindow(internal)
        importer.Update()
        original=internal.GetRenderers().GetFirstRenderer().GetActors()
        original.InitTraversal()
        nodes=0
        while True:
            actor=original.GetNextActor()
            if actor is None:break
            nodes+=1
            poses=asset.get("placements") or []
            if len(poses)>MAX_POSES:raise ValueError("Excessively many authored palms")
            if poses:
                for pose in poses:
                    if any(not math.isfinite(float(pose[key])) for key in ("x","y","z","rotation","scale")):
                        raise ValueError("Non-finite original position")
                    duplicate=vtk.vtkActor();duplicate.ShallowCopy(actor)
                    transform=vtk.vtkTransform()
                    transform.Translate(pose["x"],pose["y"],pose["z"])
                    transform.RotateY(math.degrees(pose["rotation"]))
                    transform.Scale(pose["scale"],pose["scale"],pose["scale"])
                    duplicate.SetUserMatrix(transform.GetMatrix())
                    ren.AddActor(duplicate);refs.append(duplicate)
            else:
                copy=vtk.vtkActor();copy.ShallowCopy(actor)
                if asset.get("local"):copy.AddPosition(col*500,0,row*500)
                ren.AddActor(copy);refs.append(copy)
        refs.extend([importer,internal])
        entries.append({"file":asset["path"],"role":asset["role"],
                        "meshes_imported":nodes,"place_count":len(asset.get("placements") or [])})
    camera=ren.GetActiveCamera()
    if sector=="r02_c00":
        camera.SetPosition(170,76,1572);camera.SetFocalPoint(254,7,1353)
    else:
        camera.SetPosition(col*500+170,90,row*500+450)
        camera.SetFocalPoint(col*500+250,6,row*500+250)
    camera.SetViewUp(0,1,0);camera.SetViewAngle(54)
    ren.ResetCameraClippingRange()
    rw.Render()
    pixels=vtk.vtkWindowToImageFilter()
    pixels.SetInput(rw);pixels.SetInputBufferTypeToRGB()
    pixels.ReadFrontBufferOff();pixels.Update()
    output.parent.mkdir(parents=True,exist_ok=True)
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(output))
    writer.SetInputConnection(pixels.GetOutputPort());writer.Write()
    result={"schema":"neurocity.authentic-cpu-render-qa.v1",
            "is_live_game_render":False,
            "source":"PRIVATE_USER_OWNED_G19_WORLD_MASTER",
            "source_asset_hashes_verified":len(audited),
            "engine":"VTK GLTFImporter offscreen",
            "source_geom_triangles_measured":False,
            "license_publication_approved":False,
            "fidelity_to_alicante_certified":False,
            "original_terrain_material_issues_still_possible":True,
            "assets":entries}
    output.with_suffix(".json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--pack",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--tile",default="r02_c00")
    args=parser.parse_args()
    outcome=run(args.pack,args.output,args.tile)
    print(json.dumps({"render":"generated","models":outcome["source_asset_hashes_verified"],
                      "live_game_certified":False},indent=2))
