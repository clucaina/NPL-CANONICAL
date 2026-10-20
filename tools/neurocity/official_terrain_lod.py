#!/usr/bin/env python3
"""Open IGN MDT05 500m -> three reversible, source-licensed GLB terrain LODs.

NEVER changes G19/V50/Geo historic models. Height vertical tie-in UNAPPROVED.
Keep raw COG transient; product attribution included. No proprietary models.
"""
from __future__ import annotations
import hashlib
import json
import math
import pathlib
import struct

ATTRIBUTION="Obra derivada del MDT05 (primera cobertura LiDAR) - IGN/CNIG, CC-BY 4.0 scne.es"
MAX_VERTICES=50000


def glb_bytes(vertices,faces,*,origin,source_hash,step):
    if not vertices or not faces or len(vertices)>MAX_VERTICES:
        raise ValueError("Empty or unbounded official terrain mesh")
    if any(len(v)!=3 or not all(math.isfinite(float(z)) for z in v) for v in vertices):
        raise ValueError("Nonfinite source terrain vertex")
    if any(len(f)!=3 or len(set(f))<3 or min(f)<0 or max(f)>=len(vertices) for f in faces):
        raise ValueError("Invalid source raster face")
    # Three.js is Y-up; G19 master tile is X east-positive and Z SOUTH-positive.
    # Dataset northing MUST be flipped to match G19's z=4248300-N.
    # The Gameplay vertical datum is NOT presumed aligned.
    normals=[[0.0,0.0,0.0] for _ in vertices]
    for a,b,c in faces:
        u=[vertices[b][i]-vertices[a][i] for i in range(3)]
        v=[vertices[c][i]-vertices[a][i] for i in range(3)]
        n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        for ix in (a,b,c):
            for d in range(3):normals[ix][d]+=n[d]
    for n in normals:
        m=math.sqrt(sum(v*v for v in n))
        if m==0:n[:]=[0.0,1.0,0.0]
        else:n[:]=[v/m for v in n]
    pos=b"".join(struct.pack("<3f",*p) for p in vertices)
    normal=b"".join(struct.pack("<3f",*n) for n in normals)
    inds=b"".join(struct.pack("<3I",*face) for face in faces)
    blob=pos+normal+inds
    lo=[min(p[i] for p in vertices) for i in range(3)]
    hi=[max(p[i] for p in vertices) for i in range(3)]
    gltf={"asset":{"version":"2.0","generator":"NeuroCity Official Terrain Candidate v1",
                    "copyright":ATTRIBUTION},
          "scene":0,"scenes":[{"nodes":[0]}],
          "nodes":[{"mesh":0,"name":"MDT05_OFFICIAL_REAL_ELEVATION_NOT_APPROVED"}],
          "meshes":[{"primitives":[{"attributes":{"POSITION":0,"NORMAL":1},
                                     "indices":2,"material":0,"mode":4}]}],
          "materials":[{"name":"MDT05_untextured_measurement_candidate",
                        "pbrMetallicRoughness":{"baseColorFactor":[0.44,0.45,0.42,1],
                                               "metallicFactor":0,"roughnessFactor":1}}],
          "buffers":[{"byteLength":len(blob)}],
          "bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":len(pos),"target":34962},
                         {"buffer":0,"byteOffset":len(pos),"byteLength":len(normal),"target":34962},
                         {"buffer":0,"byteOffset":len(pos)+len(normal),"byteLength":len(inds),"target":34963}],
          "accessors":[{"bufferView":0,"componentType":5126,"count":len(vertices),"type":"VEC3",
                        "min":lo,"max":hi},
                       {"bufferView":1,"componentType":5126,"count":len(vertices),"type":"VEC3"},
                       {"bufferView":2,"componentType":5125,"count":3*len(faces),"type":"SCALAR"}],
          "extras":{"source_file_sha256":source_hash,"source_crs_normalized":"EPSG:25830",
                    "local_origin_projected_m":[origin[0],origin[1]],"local_axes":"x=easting-minE; y=height; z=maxN-northing; G19 south-positive","step_source_pixels":step,
                    "vertical_datum_tie_to_G19_verified":False,
                    "architecture_source_unchanged":True,"public_source_attribution":ATTRIBUTION}}
    raw=json.dumps(gltf,separators=(",",":"),ensure_ascii=False).encode()
    raw+=b" " * ((-len(raw))%4)
    blob+=b"\x00"*((-len(blob))%4)
    total=12+8+len(raw)+8+len(blob)
    return struct.pack("<4sII",b"glTF",2,total)+struct.pack("<I4s",len(raw),b"JSON")+raw+struct.pack("<I4s",len(blob),b"BIN\x00")+blob


def candidate_lods(cog_bytes,output_dir,official_report):
    import rasterio
    from rasterio.io import MemoryFile
    if official_report.get("status")!="OFFICIAL_RASTER_PIXELS_VALIDATED_DATUM_PENDING":
        raise ValueError("No verified source pixel QA")
    digest=hashlib.sha256(cog_bytes).hexdigest()
    if digest!=official_report.get("source_file_sha256"):
        raise ValueError("Official GeoTIFF SHA mismatch")
    from official_terrain_probe import BBOX
    out=pathlib.Path(output_dir)
    out.mkdir(parents=True,exist_ok=True)
    published=[]
    with MemoryFile(cog_bytes) as inp:
        with inp.open() as ds:
            band=ds.read(1,masked=True)
            import numpy as np
            nodata_mask=np.ma.getmaskarray(band)
            for step in (1,2,4):
                rows=list(range(0,ds.height,step))
                cols=list(range(0,ds.width,step))
                if rows[-1]!=ds.height-1:rows.append(ds.height-1)
                if cols[-1]!=ds.width-1:cols.append(ds.width-1)
                verts=[];mapping={}
                for ri,row in enumerate(rows):
                    for ci,col in enumerate(cols):
                        if bool(nodata_mask[row,col]) or not math.isfinite(float(band[row,col])):
                            continue
                        E,N=ds.xy(row,col)
                        mapping[ri,ci]=len(verts)
                        verts.append((float(E-BBOX[0]),float(band[row,col]),float(BBOX[3]-N)))
                faces=[]
                for ri in range(len(rows)-1):
                    for ci in range(len(cols)-1):
                        pts=[mapping.get((ri,ci)),mapping.get((ri,ci+1)),
                             mapping.get((ri+1,ci)),mapping.get((ri+1,ci+1))]
                        if any(q is None for q in pts):continue
                        a,b,c,d=pts
                        # +X then +Z has -Y normal; reverse winding for true +Y.
                        faces.extend(((a,c,b),(b,c,d)))
                if len(verts)<40 or len(faces)<30:
                    raise ValueError("Official source too sparse for requested LOD")
                glb=glb_bytes(verts,faces,origin=(BBOX[0],BBOX[3]),
                              source_hash=digest,step=step)
                label="MDT05_ALICANTE_r01_c02_LOD"+str({1:0,2:1,4:2}[step])+"_UNAPPROVED.glb"
                f=out/label
                f.write_bytes(glb)
                published.append({"file":label,"file_sha256":hashlib.sha256(glb).hexdigest(),
                                  "bytes":len(glb),"vertices_real":len(verts),
                                  "triangles_real":len(faces),"sample_step_pixels":step})
    manifest={"schema":"neurocity.official-500m-terrain-candidates.v1",
              "source":"IGN/CNIG MDT05 via IDEE OGC","source_sha256":digest,
              "license":"CC-BY-4.0","attribution":ATTRIBUTION,
              "bbox_epsg_25830":list(BBOX),"terrain_elevation_from_real_pixels":True,
              "baseline_G19_ground_alignment_verified":False,
              "G19_horizontal_axis_convention_used":True,
              "source_vertical_datum_local_control_verified":False,
              "private_G19_assets_included":False,"built_from_open_source_only":True,
              "not_live_in_game":True,"not_deployed":True,"lods":published}
    (out/"SOURCE_LICENSE_QA.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    return manifest


def validate_glb_header(payload):
    if not isinstance(payload,bytes) or len(payload)<28:
        raise ValueError("Invalid GLB")
    magic,ver,total=struct.unpack_from("<4sII",payload)
    jlen,jtag=struct.unpack_from("<I4s",payload,12)
    if magic!=b"glTF" or ver!=2 or total!=len(payload) or jtag!=b"JSON":
        raise ValueError("Invalid GLB header")
    meta=json.loads(payload[20:20+jlen])
    return {"vertices":meta["accessors"][0]["count"],
            "indices":meta["accessors"][2]["count"],
            "attribution":meta["asset"]["copyright"],
            "not_approved":not meta["extras"]["vertical_datum_tie_to_G19_verified"]}
