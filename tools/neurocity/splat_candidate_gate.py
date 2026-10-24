"""Offline structural QA for experimental 32-byte Gaussian .splat files.

Never loads original G19, archives, patient data, network resources or models.
The format contains six little-endian float32 (xyz + 3 scales) followed by
four RGBA and four rotation bytes. Structural inspection is NOT reconstruction.
"""
import argparse
import hashlib
import json
import math
import re
import struct
from pathlib import Path

SPLAT_BYTES = 32
MAX_BYTES = 16_000_000
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def inspect_splat(data, manifest):
    """Return minimal QA status; never include image pixels or 3D coordinates."""
    result = {
        "schema": "neurocity.splat-candidate-qa.v1",
        "status": "REJECTED",
        "runtime_admitted": False,
        "photorealism_verified": False,
        "geolocation_verified": False,
        "collision_mesh_verified": False,
        "browser_render_verified": False,
        "input_rights_verified": False,
        "license_verified": False,
        "generated_world_glbs": 0,
        "reasons": [],
    }
    issues = result["reasons"]
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES or len(data) % SPLAT_BYTES:
        issues.append("INVALID_SPLAT_BYTES_OR_SIZE")
        return result
    if not isinstance(manifest, dict):
        issues.append("MISSING_EVIDENCE_MANIFEST")
        return result
    digest = hashlib.sha256(data).hexdigest()
    result["sha256"] = digest
    result["splat_count"] = len(data) // SPLAT_BYTES
    if manifest.get("splat_sha256") != digest:
        issues.append("BYTE_HASH_MISMATCH")
    if manifest.get("format") != "antimatter15-splat32":
        issues.append("UNVERIFIED_SPLAT_FORMAT")
    if manifest.get("source_code_repo") != "https://github.com/localai-org/free-splatter.cpp":
        issues.append("PIPELINE_SOURCE_NOT_REVIEWED")
    hashes = manifest.get("source_image_sha256")
    if (not isinstance(hashes, list) or not 2 <= len(hashes) <= 8
            or any(not isinstance(x, str) or not SHA256.fullmatch(x) for x in hashes)
            or len(hashes) != len(set(hashes))):
        issues.append("INPUT_IMAGE_HASHES_NOT_VERIFIED")
    if manifest.get("rights_approved") is not True:
        issues.append("INPUT_RIGHTS_REVIEW_REQUIRED")
    modelhash = manifest.get("model_sha256")
    if (manifest.get("model_license_reviewed") is not True
            or not isinstance(modelhash, str) or not SHA256.fullmatch(modelhash)):
        issues.append("MODEL_WEIGHTS_LICENSE_AND_HASH_REVIEW_REQUIRED")
    if any(manifest.get(key) is True for key in ("runtime_admitted", "published", "collision_mesh_verified")):
        issues.append("FORBIDDEN_PRODUCT_CLAIM")
    has_visible_gaussian = False
    for off in range(0, len(data), SPLAT_BYTES):
        x, y, z, sx, sy, sz = struct.unpack_from("<6f", data, off)
        if not all(math.isfinite(v) for v in (x, y, z, sx, sy, sz)):
            issues.append("NONFINITE_POSITION_OR_SCALE")
            break
        if min(sx, sy, sz) <= 0 or max(sx, sy, sz) > 1_000_000:
            issues.append("INVALID_GAUSSIAN_SCALE")
            break
        if data[off + 27]:
            has_visible_gaussian = True
    if not has_visible_gaussian:
        issues.append("NO_VISIBLE_SPLAT")
    if issues:
        return result
    # Manifest flags are SELF-REPORTED: they never certify image ownership,
    # model licensing, georeferencing, performance, mesh fidelity or gameplay.
    result["status"] = "STRUCTURAL_ONLY_NOT_CITY_ASSET"
    return result


def main():
    parser = argparse.ArgumentParser(description="Bounded offline public-splat checker; no network")
    parser.add_argument("--splat", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    if (args.splat.suffix != ".splat" or args.splat.is_symlink()
            or not args.splat.is_file() or args.splat.stat().st_size > MAX_BYTES):
        raise SystemExit("Unsafe or missing splat file")
    if (args.manifest.is_symlink() or not args.manifest.is_file()
            or args.manifest.stat().st_size > 8192):
        raise SystemExit("Unsafe or missing manifest")
    report = inspect_splat(args.splat.read_bytes(), json.loads(args.manifest.read_text(encoding="utf8")))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(1 if report["status"] == "REJECTED" else 0)


if __name__ == "__main__":
    main()
