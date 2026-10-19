#!/usr/bin/env python3
"""Bounded public metadata harvest of Poly Haven CC0 models (never patients or private files).
Does not download binary models, publish a website, or alter NeuroCity's OSM/PNOA originals.
API: https://api.polyhaven.com/assets?t=models - official Poly Haven API, documented CC0 assets.
"""
from __future__ import annotations
import argparse
import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

API = "https://api.polyhaven.com/assets?t=models"
MAX_METADATA_BYTES = 16 * 1024 * 1024
KEYWORDS = {
    "tree": 3, "plant": 3, "palm": 6, "bush": 2, "shrub": 2,
    "bench": 6, "chair": 2, "table": 2, "street": 3, "urban": 3,
    "lantern": 3, "lamp": 2, "bicycle": 3, "bike": 3, "car": 2,
    "sidewalk": 3, "pavement": 2, "brick": 2, "door": 2,
    "window": 3, "facade": 4, "building": 2, "architecture": 2,
    "cafe": 2, "barrel": 1, "planter": 4, "furniture": 2,
    "marina": 2, "coast": 2, "boat": 2, "stone": 1
}
SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{1,90}$")
EXCLUDE = ("person", "human", "face", "body", "portrait", "medical", "patient", "weapon", "gun")

def rank_assets(payload: dict, *, limit: int = 120, now: int | None = None) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Provider must return a JSON object of asset metadata")
    if not 1 <= limit <= 500:
        raise ValueError("Candidate limit outside 1..500")
    if now is None:
        now = int(time.time())
    candidates = []
    for slug, metadata in payload.items():
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or not isinstance(metadata, dict):
            continue
        published = metadata.get("date_published")
        if not isinstance(published, (int, float)) or isinstance(published, bool) or published > now:
            continue  # exclude unreleased / future assets
        name = metadata.get("name", "")
        category = metadata.get("category", "")
        tags = metadata.get("tags")
        if not isinstance(name, str) or not isinstance(category, str) or not isinstance(tags, list):
            continue
        tags = [t for t in tags if isinstance(t, str)][:40]
        text = (name + " " + category + " " + " ".join(tags)).lower()
        if any(re.search(r"\b" + re.escape(block) + r"\b", text) for block in EXCLUDE):
            continue
        score = sum(weight for word, weight in KEYWORDS.items() if re.search(r"\b" + re.escape(word) + r"s?\b", text))
        if score <= 0:
            continue
        candidates.append({
            "id": slug, "title": name[:120], "category": category[:180],
            "tags": sorted(set(tags))[:24], "relevance_score": score,
            "url": "https://polyhaven.com/a/" + slug,
            "source": "Poly Haven Public API", "license": "CC0-1.0",
            "candidate_only": True, "binary_downloaded": False,
            "fit_for_alicante": "NOT_VERIFIED", "provenance": "provider_metadata"
        })
    candidates.sort(key=lambda x: (-x["relevance_score"], x["id"]))
    candidates = candidates[:limit]
    return {
        "schema": "neurocity.cc0-candidate-catalog.v1",
        "provider": "Poly Haven", "api": API,
        "license": "CC0-1.0", "source_metadata_obtained": True,
        "models_downloaded": 0, "licensing_note": "Poly Haven CC0 applies to assets; live API use has separate attribution terms.",
        "not_surveyed": True, "not_integrated_in_city": True,
        "count": len(candidates), "candidates": candidates
    }

def read_live():
    req = Request(API, headers={"User-Agent": "NeuroCity-Public-CC0-Catalog/1.0 (clucaina/NPL-CANONICAL)", "Accept": "application/json"})
    with urlopen(req, timeout=35) as response:
        if response.status != 200:
            raise RuntimeError("Provider status " + str(response.status))
        declared = response.headers.get("Content-Length", "")
        if declared and int(declared) > MAX_METADATA_BYTES:
            raise RuntimeError("Provider metadata exceeds safe limit")
        raw = response.read(MAX_METADATA_BYTES + 1)
    if len(raw) > MAX_METADATA_BYTES:
        raise RuntimeError("Provider metadata exceeds safe limit")
    return json.loads(raw)

def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--live", action="store_true", help="Fetch public API metadata")
    source.add_argument("--fixture", type=Path, help="Use local synthetic metadata only")
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = read_live() if args.live else json.loads(args.fixture.read_text(encoding="utf-8"))
    report = rank_assets(data, limit=args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Curated public metadata:", report["count"], "CC0 candidate assets; downloaded: 0")

if __name__ == "__main__":
    main()
