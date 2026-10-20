#!/usr/bin/env python3
"""Bounded official IGN MDT05 500m probe: evidence-only, NEVER patch original 3D."""
from __future__ import annotations
import hashlib
import json
import math
import os
import pathlib
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

COLLECTION = "https://api-coverages.idee.es/collections/EL.ElevationGridCoverage_25830_5_PB"
TILE="r01_c02"
BBOX=(720700,4247300,721200,4247800)
MAX_BYTES=20_000_000
URL=(COLLECTION+"/coverage?bbox="+",".join(map(str,BBOX))+"&bbox-crs=25830&f=COG")


def inspect_raster(raw):
    """Check real GeoTIFF EPSG/bbox/nodata/pixel samples; fail on mislabeled HTML."""
    if not isinstance(raw,bytes) or not (raw[:4] in (b"II*\x00",b"MM\x00*")):
        raise ValueError("Downloaded response is not TIFF")
    import rasterio
    from rasterio.io import MemoryFile
    with MemoryFile(raw) as source:
        with source.open() as ds:
            epsg=ds.crs.to_epsg() if ds.crs else None
            if epsg not in (25830,3042):
                raise ValueError("Unexpected CRS: "+str(ds.crs)+"; bounds="+str(tuple(round(v,2) for v in (ds.bounds.left,ds.bounds.bottom,ds.bounds.right,ds.bounds.top)))+"; shape="+str((ds.height,ds.width)))
            # EPSG:3042 is officially ETRS89/UTM 30N with N,E axis metadata,
            # while EPSG:25830 uses preferred E,N ordering. GDAL raster affine
            # fields are X/Y. Do NOT relabel blindly: prove a stable coordinate
            # transform for five corners/centre with pyproj always_xy.
            from pyproj import Transformer
            transform=Transformer.from_crs(ds.crs,"EPSG:25830",always_xy=True)
            b=ds.bounds
            samples=((b.left,b.bottom),(b.left,b.top),(b.right,b.bottom),
                     (b.right,b.top),((b.left+b.right)/2,(b.bottom+b.top)/2))
            for x,y in samples:
                u,v=transform.transform(x,y)
                if not math.isfinite(u) or not math.isfinite(v) or math.hypot(u-x,v-y)>0.1:
                    raise ValueError("COG axis transform is not identity in verified ETRS89/UTM 30N")

            if not (abs(b.left-BBOX[0])<=12 and abs(b.bottom-BBOX[1])<=12 and
                    abs(b.right-BBOX[2])<=12 and abs(b.top-BBOX[3])<=12):
                raise ValueError("Raster does not represent requested Alicante tile")
            if ds.count<1 or ds.width<20 or ds.height<20 or ds.width*ds.height>2_000_000:
                raise ValueError("Unexpected raster band/dimensions")
            resolution=(abs(ds.transform.a),abs(ds.transform.e))
            if not all(1<=r<=10 for r in resolution):
                raise ValueError("Implausible raster cell resolution")
            data=ds.read(1,masked=True)
            valid=data.compressed()
            if len(valid)<max(200,int(ds.width*ds.height*.1)):
                raise ValueError("Insufficient real elevation pixels")
            lo=float(valid.min());hi=float(valid.max())
            if not math.isfinite(lo) or not math.isfinite(hi) or lo < -100 or hi > 3500:
                raise ValueError("Altitude values out of plausible Spanish mainland range")
            return {"epsg":25830,"source_epsg":epsg,\n                    "utm_axis_mapping_verified":True,"bounds_m":list(map(float,(b.left,b.bottom,b.right,b.top))),
                    "pixel_size_m":list(resolution),"raster_shape":[ds.height,ds.width],
                    "measured_valid_pixels":len(valid),"valid_fraction":round(len(valid)/data.size,4),
                    "elevation_min_m_ortho_candidate":round(lo,3),
                    "elevation_max_m_ortho_candidate":round(hi,3),
                    "source_file_sha256":hashlib.sha256(raw).hexdigest(),
                    "vertical_datum_validated_against_local_benchmark":False,
                    "no_buildings_or_foundations_modified":True}


def download_bounded():
    req=Request(URL,headers={"Accept":"image/tiff,application/octet-stream",
                             "User-Agent":"NeuroCity-Official-DEM-Probe/1.0"})
    with urlopen(req,timeout=27) as reply:
        if reply.status!=200:
            raise RuntimeError("Official OGC returned non-success")
        final=urlsplit(reply.url)
        if final.scheme!="https" or final.hostname!="api-coverages.idee.es":
            raise RuntimeError("Unapproved external redirect")
        declared=reply.headers.get("Content-Length")
        if declared and int(declared)>MAX_BYTES:
            raise ValueError("Official raster exceeds cap")
        raw=reply.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ValueError("Official raster exceeds cap")
    return raw


def probe(output, fetch=download_bounded):
    result={"schema":"neurocity.ign-real-terrain-probe.v1","tile":TILE,
            "official_collection":COLLECTION,"bbox_epsg_25830":list(BBOX),
            "licensed_as":"IGN/CNIG source family CC-BY 4.0; exact tile attribution pending",
            "source_data_archived_publicly":False,
            "game_runtime_modified":False,"liDAR_high_fidelity_claimed":False}
    try:
        raster=fetch()
        result.update(inspect_raster(raster))
        result["status"]="OFFICIAL_RASTER_PIXELS_VALIDATED_DATUM_PENDING"
    except Exception as e:
        result["status"]="BLOCKED_REAL_SOURCE_NOT_VALIDATED"
        result["reason_type"]=type(e).__name__
        result["reason"]=str(e)[:180]
    dest=pathlib.Path(output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return result

if __name__=="__main__":
    target=os.environ.get("NEUROCITY_TERRAIN_REPORT","_neurocity_source_qa/real_terrain_r01_c02.json")
    report=probe(target)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["status"]!="OFFICIAL_RASTER_PIXELS_VALIDATED_DATUM_PENDING":
        raise SystemExit(3)
