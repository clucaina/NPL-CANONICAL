#!/usr/bin/env python3
"""NeuroCity: provenance-aware quality gate for existing OSM/PNOA/Blender pipeline.
No personal data, external services, or credentials. Does not assert photorealism.
"""
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from glb_structure import inspect_glb

def valid_building_footprint(refs, nodes):
    """Require a closed, non-degenerate OSM polygon with real geographic nodes."""
    if len(refs) < 4 or refs[0] != refs[-1] or len(set(refs[:-1])) < 3:
        return False
    points = [nodes.get(ref) for ref in refs]
    if any(point is None for point in points) or len(set(points[:-1])) < 3:
        return False
    # Translate to the first point to avoid cancellation with absolute lat/lon.
    lat0, lon0 = points[0]
    twice_area = sum(
        (points[i][1] - lon0) * (points[i + 1][0] - lat0)
        - (points[i + 1][1] - lon0) * (points[i][0] - lat0)
        for i in range(1, len(points) - 2)
    )
    return abs(twice_area) > 1e-14

def audit(osm_file, manifest_file, scene_file, glb_file):
    manifest = json.loads(Path(manifest_file).read_text(encoding="utf-8"))
    scene = json.loads(Path(scene_file).read_text(encoding="utf-8"))
    xml = ET.parse(osm_file).getroot()
    # A node ID alone is not evidence of a usable geographic coordinate.
    nodes = {}
    for node in xml.findall("node"):
        try:
            lat, lon = float(node.attrib["lat"]), float(node.attrib["lon"])
            if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180:
                nodes[node.attrib["id"]] = (lat, lon)
        except (KeyError, TypeError, ValueError):
            continue
    buildings, explicit_heights, complete, roads = 0, 0, 0, 0
    for way in xml.findall("way"):
        tags = {t.attrib.get("k"): t.attrib.get("v") for t in way.findall("tag")}
        refs = [n.attrib["ref"] for n in way.findall("nd")]
        if tags.get("building") not in (None, "no"):
            buildings += 1
            if tags.get("height"):
                try:
                    h = float(str(tags["height"]).strip().removesuffix(" m"))
                    explicit_heights += int(math.isfinite(h) and 2 <= h <= 150)
                except ValueError:
                    pass
            complete += int(valid_building_footprint(refs, nodes))
        if tags.get("highway"):
            roads += 1
    data = Path(glb_file).read_bytes()
    geometry = inspect_glb(data)
    mesh_count = geometry["meshes"]
    width = manifest.get("bbox_local_m")
    errors = []
    if buildings == 0 or complete == 0: errors.append("No complete georeferenced building footprints")
    errors.extend(geometry["errors"])
    # Fail closed on malformed or non-finite coordinates: string/bool/NaN
    # values must never be mistaken for valid projected geometry.
    if (not isinstance(width, list) or len(width) != 4
            or any(type(value) not in (int, float) or abs(value) > 1e12 or not math.isfinite(value) for value in width)
            or width[2] <= width[0] or width[3] <= width[1]):
        errors.append("Invalid projected bounding box")
    exported = scene.get("real_osm_buildings")
    measured = scene.get("heights_directly_measured")
    # A missing, fractional, negative or boolean count is not OSM evidence.
    if type(exported) is not int or not 1 <= exported <= complete:
        errors.append("Scene building count lacks complete OSM footprint evidence")
    if (type(measured) is not int or not 0 <= measured <= explicit_heights
            or (type(exported) is int and measured > exported)):
        errors.append("Scene measured height count lacks OSM height-tag evidence")
    # bool("false") is True: never promote a textual flag to verified imagery.
    if type(manifest.get("real_orthophoto")) is not bool:
        errors.append("Orthophoto provenance flag must be boolean")
    if scene.get("facades_photogrammetric") or manifest.get("building_facades_photogrammetric"):
        errors.append("Unexpected unsupported photogrammetric facade claim")
    if scene.get("private_avatar_included"):
        errors.append("Private avatar must not be included in a public build")
    return {
        "gate": "FAIL" if errors else "PASS_PROVENANCE_ONLY",
        "errors": errors,
        "evidence": {"osm_building_ways": buildings, "closed_node_complete_ways": complete,
            "osm_explicit_height_tags_valid": explicit_heights, "osm_road_ways": roads,
            "scene_exported_buildings": scene.get("real_osm_buildings"),
            "height_data_coverage_ratio": round(explicit_heights / buildings, 4) if buildings else 0,
            "real_pnoa_ground": bool(manifest.get("real_orthophoto")),
            "glb_bytes": len(data), "glb_meshes": mesh_count,
            "glb_drawable_primitives": geometry["drawable_primitives"],
            "glb_position_vertices": geometry["position_vertices"],
            "glb_embedded_bin_bytes": geometry["bin_bytes"],
            "osm_buildings_with_no_valid_measured_height": buildings - explicit_heights},
        "limitations": ["Street facades are not photogrammetric",
            "Approximate road widths and estimated heights are not surveyed measurements",
            "GLB structural validity does not demonstrate navigability, FPS, visual realism or psychological validity",
            "NPL/Conflictometro runtime integration is NOT established by this report"],
        "next_actions": ["Benchmark interactive navigation, FPS and memory on desktop and mobile",
            "Integrate NPL and Conflictometro as verified, versioned independent data layers",
            "Investigate legally licensed real facade imagery and photogrammetry, then assess quality visually"]
    }

def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: city_quality.py input.osm manifest.json QA_source_report.json scene.glb quality.json")
    result = audit(*sys.argv[1:5])
    output = Path(sys.argv[5]); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["errors"]: raise SystemExit(1)

if __name__ == "__main__": main()
