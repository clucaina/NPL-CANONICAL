#!/usr/bin/env python3
"""Pure read-only GLB structure audit; geometry counts != photographic realism.
Designed to reject GLB files with syntactically valid headers but no drawable 3D.
"""
import json
import struct

def inspect_glb(data):
    result={"header_valid":False,"json_valid":False,"meshes":0,
            "drawable_primitives":0,"position_vertices":0,
            "bin_bytes":0,"errors":[]}
    errors=result["errors"]
    if len(data)<20 or data[:4]!=b"glTF":
        errors.append("GLB signature or minimum header invalid")
        return result
    version,claimed=struct.unpack_from("<II",data,4)
    if version!=2 or claimed!=len(data):
        errors.append("GLB version or declared file length invalid")
        return result
    result["header_valid"]=True
    offset=12
    json_chunk=None
    bin_chunk=None
    while offset<len(data):
        if offset+8>len(data):
            errors.append("Truncated GLB chunk header")
            break
        n,kind=struct.unpack_from("<I4s",data,offset)
        offset+=8
        if n%4 or offset+n>len(data):
            errors.append("Unaligned or truncated GLB chunk")
            break
        raw=data[offset:offset+n];offset+=n
        if kind==b"JSON" and json_chunk is None:
            json_chunk=raw
        elif kind==b"BIN\x00" and bin_chunk is None:
            bin_chunk=raw
    if json_chunk is None:
        errors.append("Missing GLB JSON chunk")
        return result
    try:
        gltf=json.loads(json_chunk.decode("utf-8"))
    except (UnicodeError,ValueError):
        errors.append("Malformed GLB JSON chunk")
        return result
    if gltf.get("asset",{}).get("version")!="2.0":
        errors.append("Unsupported or missing glTF 2.0 asset")
    else:
        result["json_valid"]=True
    meshes=gltf.get("meshes",[])
    accessors=gltf.get("accessors",[])
    buffers=gltf.get("buffers",[])
    if not isinstance(meshes,list) or not isinstance(accessors,list) or not isinstance(buffers,list):
        errors.append("Malformed glTF mesh, accessor or buffer collections")
        return result
    result["meshes"]=len(meshes)
    result["bin_bytes"]=len(bin_chunk) if bin_chunk is not None else 0
    for mesh in meshes:
        if not isinstance(mesh,dict):continue
        primitives=mesh.get("primitives",[])
        if not isinstance(primitives,list):continue
        for primitive in primitives:
            if not isinstance(primitive,dict):continue
            # mode absent means TRIANGLES in glTF 2.0. Only count geometry we
            # could draw as triangles. Points/lines do not count as buildings.
            if primitive.get("mode",4) not in (4,5,6):continue
            pos=primitive.get("attributes",{}).get("POSITION")
            if not isinstance(pos,int) or isinstance(pos,bool) or not 0<=pos<len(accessors):continue
            accessor=accessors[pos]
            if not isinstance(accessor,dict):continue
            count=accessor.get("count",0)
            if not isinstance(count,int) or count<3:continue
            if accessor.get("type")!="VEC3":continue
            result["drawable_primitives"]+=1
            result["position_vertices"]+=count
    if result["drawable_primitives"]==0:
        errors.append("GLB has no triangle geometry with valid POSITION accessors")
    if buffers:
        total=sum(int(b.get("byteLength",0)) for b in buffers if isinstance(b,dict))
        # A public standalone GLB must contain its binary geometry, not depend
        # on external URI assets or absent private files.
        if total>result["bin_bytes"]:
            errors.append("Declared binary buffer exceeds embedded GLB BIN chunk")
    elif result["drawable_primitives"]:
        errors.append("Drawable primitives have no binary buffer")
    return result
