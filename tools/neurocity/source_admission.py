#!/usr/bin/env python3
"""Pure metadata admission gate. Zero network, zero assets, never publish private files."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "neurocity.public-source-discovery.v1"
KINDS = {"geodata", "asset", "tool"}
LICENSES = {"CC0-1.0", "CC-BY-4.0", "MIT", "Apache-2.0", "GPL-2.0", "UNVERIFIED"}
HOSTS = {"pnoa.ign.es", "centrodedescargas.cnig.es", "kenney.nl",
         "polyhaven.com", "github.com", "api-coverages.idee.es"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[a-z][a-z0-9_]{2,70}$")


def trusted_url(url):
    if not isinstance(url, str) or len(url) > 800:
        return False
    try:
        u = urlsplit(url)
        return (u.scheme == "https" and u.hostname in HOSTS and not u.username
                and not u.password and not u.fragment and not u.query
                and not u.path.startswith("//"))
    except ValueError:
        return False


def evaluate(record):
    """Conservative status: metadata discovery never implies runtime integration."""
    errors = []
    if not isinstance(record, dict):
        raise ValueError("Resource record must be a dictionary")
    if not isinstance(record.get("id"), str) or not ID.fullmatch(record["id"]):
        errors.append("UNSAFE_ID")
    if record.get("kind") not in KINDS:
        errors.append("UNKNOWN_KIND")
    kind = record.get("kind")
    if record.get("license") not in LICENSES:
        errors.append("UNKNOWN_LICENSE")
    scope = "software" if kind == "tool" else "data" if kind == "geodata" else "asset"
    if record.get("license_scope") != scope:
        errors.append("LICENSE_SCOPE_MISMATCH")
    for key in ("source_url", "license_evidence_url"):
        if not trusted_url(record.get(key)):
            errors.append("UNTRUSTED_" + key.upper())
    if record.get("binary_imported") is not False:
        errors.append("UNVERIFIED_BINARY_IMPORT")
    if record.get("license_evidence_verified") is not True or record.get("license") == "UNVERIFIED":
        errors.append("LICENSE_REVIEW_REQUIRED")
    if record.get("license") == "CC-BY-4.0" and not str(record.get("attribution", "")).strip():
        errors.append("ATTRIBUTION_REQUIRED")
    digest = record.get("artifact_sha256")
    if digest is None:
        errors.append("SOURCE_FILE_SHA256_MISSING")
    elif not isinstance(digest, str) or not SHA256.fullmatch(digest):
        errors.append("SOURCE_FILE_SHA256_INVALID")
    # An asset can only become a precisely placed Alicante asset with measured evidence.
    if kind in ("geodata", "asset") and record.get("spatial_placement_verified") is not True:
        errors.append("UNVERIFIED_GEOGRAPHIC_PLACEMENT")
    if kind == "geodata":
        if record.get("crs") != "EPSG:25830":
            errors.append("ALICANTE_ETRS89_CRS_UNVERIFIED")
        if record.get("vertical_datum") != "ORTHOMETRIC_VERIFIED":
            errors.append("VERTICAL_DATUM_UNVERIFIED")
        if not isinstance(record.get("survey_year"), int) or not 2000 <= record["survey_year"] <= 2026:
            errors.append("SURVEY_DATE_UNVERIFIED")
    return {"id":record.get("id"), "kind":kind,
            "runtime_admitted":not errors, "reasons":sorted(set(errors))}


def validate_registry(payload):
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError("Noncanonical source registry")
    if payload.get("metadata_only") is not True or payload.get("private_assets_never_public") is not True:
        raise ValueError("Private source firewall must be explicit")
    entries = payload.get("records")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError("Source registry out of bounded range")
    seen = set()
    reports = []
    for item in entries:
        r = evaluate(item)
        if r["id"] in seen:
            raise ValueError("Duplicate source id " + str(r["id"]))
        seen.add(r["id"])
        reports.append(r)
        # Invalid record is a hard schema error; a missing SHA/license is an
        # expected honest discovery blocker rather than a broken registry.
        bad = {"UNSAFE_ID", "UNKNOWN_KIND", "UNKNOWN_LICENSE", "LICENSE_SCOPE_MISMATCH",
               "UNTRUSTED_SOURCE_URL", "UNTRUSTED_LICENSE_EVIDENCE_URL",
               "UNVERIFIED_BINARY_IMPORT", "SOURCE_FILE_SHA256_INVALID"}
        if bad.intersection(r["reasons"]):
            raise ValueError("Malformed source " + str(r["id"]) + ": " + str(r["reasons"]))
    return {"schema":"neurocity.public-source-admission-report.v1",
            "discovered":len(reports), "admitted":sum(x["runtime_admitted"] for x in reports),
            "not_in_city":True, "generated_world_glbs":0, "records":reports}


def profile_preexisting_kenney(data, limit=18):
    """Summarize existing 1,883 Drive-indexed GLB LOCATORS, no bytes/URLs exported."""
    if not isinstance(data, list) or len(data) > 5000 or not 1 <= limit <= 100:
        raise ValueError("Bad bounded Kenney catalogue")
    counts = collections.Counter()
    result = []
    tags = ("palm", "bench", "trashcan", "road-sign", "street", "tree",
            "bike", "lamp", "bollard", "fence", "bush", "flower")
    seen = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        ident = item.get("id")
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", ident):
            continue
        if ident in seen:
            raise ValueError("Repeated Kenney model locator")
        seen.add(ident)
        counts[ident.split("/")[0]] += 1
        if item.get("status") != "located_only":
            continue
        if not isinstance(item.get("bytes_declared"), int) or item["bytes_declared"] <= 0:
            continue
        hits = [tag for tag in tags if tag in ident]
        if hits:
            result.append({"id":ident, "declared_bytes":item["bytes_declared"],
                           "match_tags":hits, "admitted":False, "geometry_loaded":False,
                           "location_verified":False, "license_binary_verified":False})
    result.sort(key=lambda x:(-len(x["match_tags"]), x["declared_bytes"], x["id"]))
    return {"schema":"neurocity.kenney-legacy-candidates.v1",
            "located":len(seen), "packs":dict(sorted(counts.items())),
            "matching_street_assets":len(result), "sample":result[:limit],
            "new_models_downloaded":0, "models_placed":0,
            "mirror_license_not_verified":True, "source":"OWNER_ARCHIVED_DRIVE_INDEX"}


def run(registry, output, kenney_catalog=None):
    report=validate_registry(json.loads(Path(registry).read_text(encoding="utf8")))
    if kenney_catalog is not None:
        report["legacy_kenney"]=profile_preexisting_kenney(
            json.loads(Path(kenney_catalog).read_text(encoding="utf8")))
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return report


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--registry",type=Path,default=Path(__file__).with_name("public_free_sources_20261020.json"))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--kenney-catalog",type=Path)
    a=p.parse_args()
    r=run(a.registry,a.output,a.kenney_catalog)
    print("NeuroCity sources discovered:",r["discovered"],"runtime admitted:",r["admitted"])
