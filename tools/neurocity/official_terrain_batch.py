#!/usr/bin/env python3
"""One bounded official IGN MDT05 candidate batch for FOUR existing G19 source tiles.

Avoid speculative city mass-production. The UTM bbox is derived from the verified
G19 projection origin, not from arbitrary web maps. Every produced GLB is an
unapproved orthometric-terrain candidate, NEVER a replacement for private G19.
"""
from __future__ import annotations
import json
import pathlib
import argparse
from official_terrain_probe import probe, request_url, download_bounded

# Original archived G19 tile IDs; source origin E=719700,N=4248300.
# Grid 500m, local +X=east and +Z=south. Not newly minted sectors.
TILES=(
 ("r02_c00",(719700,4246800,720200,4247300)),
 ("r02_c01",(720200,4246800,720700,4247300)),
 ("r01_c01",(720200,4247300,720700,4247800)),
 ("r01_c02",(720700,4247300,721200,4247800)),
)
MAX_TILES=4

def run(output_dir, *, fetch=download_bounded):
    out=pathlib.Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    statuses=[]
    for tile,bbox in TILES:
        url=request_url(bbox)
        if len(statuses)>=MAX_TILES: raise RuntimeError("Batch limit violation")
        fn=lambda url=url:fetch(url)
        result=probe(out/tile/"OFFICIAL_TERRAIN_QA.json",
                     fetch=fn,mesh_output_dir=out/tile/"glb",
                     tile_id=tile,bbox=bbox)
        statuses.append({"tile":tile,"bbox":list(bbox),"status":result["status"],
                         "mesh_status":result.get("mesh_candidate_status","NOT_GENERATED"),
                         "valid_pixels":result.get("measured_valid_pixels",0),
                         "source_sha256":result.get("source_file_sha256"),
                         "models_created":result.get("mesh_candidate_lod_count",0),
                         "error":result.get("reason") or result.get("mesh_reason")})
    created=sum(x["models_created"] for x in statuses)
    ready=sum(x["models_created"]==3 for x in statuses)
    manifest={
      "schema":"neurocity.original-g19-four-tile-official-mdt05.v1",
      "actual_archived_G19_tile_count":len(TILES),
      "tiles_with_three_real_source_lods":ready,
      "mesh_candidates_created":created,
      "all_tiles_height_validated":ready==len(TILES),
      "vertical_reference_to_original_G19_approved":False,
      "existing_city_or_original_models_modified":False,
      "not_live_in_game":True,"models_private":False,
      "source_license":"CC-BY-4.0","notes":"Some ocean or unmeasured cells may be NODATA, never filled or called surveyed.",
      "results":statuses}
    (out/"FOUR_TILE_IGN_COVERAGE_QA.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    a=p.parse_args()
    summary=run(a.output)
    print(json.dumps(summary,indent=2))
    if summary["tiles_with_three_real_source_lods"]==0:
        raise SystemExit(3)
    # PARTIAL is documented but must not masquerade as four approved terrains.
    if not summary["all_tiles_height_validated"]:
        raise SystemExit(4)
