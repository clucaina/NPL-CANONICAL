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
    """Require a closed, non-degenerate, non-self-intersecting OSM polygon."""
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
    if abs(twice_area) <= 1e-14:
        return False

    # Nonzero signed area alone cannot exclude self-crossing building walls.
    # Reject intersections between nonadjacent edges, including shared points.
    def orientation(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a, b, c):
        return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0])
                and min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))

    def intersects(a, b, c, d):
        if (max(a[0], b[0]) < min(c[0], d[0])
                or max(c[0], d[0]) < min(a[0], b[0])
                or max(a[1], b[1]) < min(c[1], d[1])
                or max(c[1], d[1]) < min(a[1], b[1])):
            return False
        ab_c, ab_d = orientation(a, b, c), orientation(a, b, d)
        cd_a, cd_b = orientation(c, d, a), orientation(c, d, b)
        if ((ab_c == 0 and on_segment(a, b, c))
                or (ab_d == 0 and on_segment(a, b, d))
                or (cd_a == 0 and on_segment(c, d, a))
                or (cd_b == 0 and on_segment(c, d, b))):
            return True
        return (ab_c > 0) != (ab_d > 0) and (cd_a > 0) != (cd_b > 0)

    vertices = points[:-1]
    n = len(vertices)
    for i in range(n):
        a, b = vertices[i], vertices[(i + 1) % n]
        if a == b:
            return False
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue  # The first and last edges share a legal endpoint.
            if intersects(a, b, vertices[j], vertices[(j + 1) % n]):
                return False
    return True

def audit(osm_file, manifest_file, scene_file, glb_file):
    manifest = json.loads(Path(manifest_file).read_text(encoding="utf-8"))
    scene = json.loads(Path(scene_file).read_text(encoding="utf-8"))
    xml = ET.parse(osm_file).getroot()
    # A node ID alone is not evidence of a usable geographic coordinate.
    nodes = {}
    for node in xml.findall("node"):
        node_id = node.attrib.get("id")
        if not node_id or not node_id.strip():
            continue  # Missing OSM IDs cannot support a georeferenced footprint.
        try:
            lat, lon = float(node.attrib["lat"]), float(node.attrib["lon"])
            if math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180:
                nodes[node_id] = (lat, lon)
        except (KeyError, TypeError, ValueError):
            continue
    buildings, explicit_heights, complete, roads = 0, 0, 0, 0
    for way in xml.findall("way"):
        tags = {t.attrib.get("k"): t.attrib.get("v") for t in way.findall("tag")}
        # Missing nd refs are invalid geometry, not an exception that aborts QA.
        refs = [n.attrib.get("ref") for n in way.findall("nd")]
        if tags.get("building") not in (None, "no"):
            buildings += 1
            # Height tags on unusable footprints are not evidence for exported buildings.
            footprint_valid = valid_building_footprint(refs, nodes)
            complete += int(footprint_valid)
            if footprint_valid and tags.get("height"):
                try:
                    h = float(str(tags["height"]).strip().removesuffix(" m"))
                    explicit_heights += int(math.isfinite(h) and 2 <= h <= 150)
                except ValueError:
                    pass
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
    # Provenance/privacy flags must be explicit booleans: 0, null and empty
    # containers are not evidence that a private asset is absent.
    if (scene.get("facades_photogrammetric") is not False
            or manifest.get("building_facades_photogrammetric", False) is not False):
        errors.append("Unexpected or unverifiable photogrammetric facade claim")
    if scene.get("private_avatar_included") is not False:
        errors.append("Private avatar absence must be explicitly verified")
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
