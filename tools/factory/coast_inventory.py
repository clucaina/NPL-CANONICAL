#!/usr/bin/env python3
"""Audita la presencia de datos OSM reales del litoral en el área de trabajo.
Una entidad OSM ≠ una malla 3D construida, ni una posición de barco en tiempo real.
No fabrica geometría, embarcaciones, agua ni datos de seguimiento.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

CATEGORIES={
 "coastline": lambda t:t.get("natural")=="coastline",
 "water_polygon":lambda t:t.get("natural")=="water" or t.get("water") in ("sea","basin","harbour"),
 "pier":lambda t:t.get("man_made") in ("pier","quay","breakwater"),
 "marina":lambda t:t.get("leisure")=="marina" or t.get("harbour") is not None,
 "pedestrian":lambda t:t.get("highway") in ("pedestrian","footway","path","steps"),
 "asphalt_hint":lambda t:t.get("surface")=="asphalt",
 "fence_or_barrier":lambda t:t.get("barrier") in ("fence","wall","guard_rail","handrail"),
 "vegetation":lambda t:t.get("natural") in ("tree","tree_row","scrub","wood") or t.get("landuse") in ("grass","forest"),
 "boat_source":lambda t:t.get("seamark:type") in ("vessel","buoy","harbour") or t.get("waterway")=="fuel"
}
def audit(osm_path:Path,manifest:dict)->dict:
 root=ET.parse(osm_path).getroot()
 bbox=manifest.get("bbox")
 if not isinstance(bbox,list) or len(bbox)!=4:
  raise ValueError("Missing geographic bbox")
 categories={key:{"objects":0,"with_nodes":0} for key in CATEGORIES}
 complete_nodes={x.attrib.get("id") for x in root.findall("node")}
 total=0
 for obj in root:
  if obj.tag not in ("node","way","relation"):continue
  tags={t.attrib.get("k"):t.attrib.get("v") for t in obj.findall("tag")}
  if not tags:continue
  total+=1
  refs=[n.attrib.get("ref") for n in obj.findall("nd")]
  all_nodes=all(r in complete_nodes for r in refs)
  for category,fn in CATEGORIES.items():
   if fn(tags):
    categories[category]["objects"]+=1
    if refs and all_nodes:categories[category]["with_nodes"]+=1
 exposure={
  "sea_surface_mesh":False,
  "boats_meshes":False,
  "asphalt_meshes_not_assessed":True,
  "harbor_meshes":False,
  "fences_meshes":False
 }
 return {"schema":"neurocity.osm_coast_provenance.v1",
  "bbox_lonlat":bbox,"tagged_osm_objects_scanned":total,
  "coverage_counts":categories,
  "coastline_geometry_source_available":categories["coastline"]["with_nodes"]>0,
  "piers_source_available":categories["pier"]["with_nodes"]>0,
  "coastal_rendering_verified":False,
  "maritime_boats_verified":False,
  "manual_source_expansion_review_required":not(categories["coastline"]["with_nodes"]>0 and categories["pier"]["with_nodes"]>0),
  "visual_assets_actually_created":exposure,
  "limitations":["Counts only tagged OSM objects inside the downloaded bounding box",
   "An OSM object does not prove a rendered, correctly positioned 3D asset",
   "Vessels and sea dynamics require separate contemporary licensed data",
   "Presence or absence may be affected by map coverage and incomplete metadata"]}
def main():
 a=argparse.ArgumentParser()
 a.add_argument("--osm",type=Path,required=True)
 a.add_argument("--manifest",type=Path,required=True)
 a.add_argument("--output",type=Path,required=True)
 x=a.parse_args()
 data=audit(x.osm,json.loads(x.manifest.read_text(encoding="utf-8")))
 x.output.parent.mkdir(parents=True,exist_ok=True)
 x.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"counts":{k:v["objects"] for k,v in data["coverage_counts"].items()},
   "coast_visual_verified":data["coastal_rendering_verified"],
   "source_review_required":data["manual_source_expansion_review_required"]}))
if __name__=="__main__":main()
