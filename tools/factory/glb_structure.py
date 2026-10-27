#!/usr/bin/env python3
"""Pure read-only GLB structure audit; geometry counts != photographic realism.
Designed to reject GLB files with syntactically valid headers but no drawable 3D.
"""
import json
import struct

def _position_buffer_valid(accessor, views, buffers, bin_length):
    """Verify that FLOAT VEC3 positions actually fit inside an embedded GLB buffer."""
    if not isinstance(accessor, dict) or accessor.get("type") != "VEC3" or accessor.get("componentType") != 5126:
        return False
    count = accessor.get("count")
    view_id = accessor.get("bufferView")
    if type(count) is not int or count < 3 or type(view_id) is not int or not 0 <= view_id < len(views):
        return False
    view = views[view_id]
    if not isinstance(view, dict) or type(view.get("buffer")) is not int or view["buffer"] != 0:
        return False
    if len(buffers) != 1 or not isinstance(buffers[0], dict) or "uri" in buffers[0]:
        return False
    declared = buffers[0].get("byteLength")
    view_start, view_length = view.get("byteOffset", 0), view.get("byteLength")
    item_start, stride = accessor.get("byteOffset", 0), view.get("byteStride", 12)
    if any(type(v) is not int for v in (declared, view_start, view_length, item_start, stride)):
        return False
    if (declared < 0 or view_start < 0 or view_length < 12 or item_start < 0
            or view_start % 4 or item_start % 4 or stride < 12 or stride > 252 or stride % 4):
        return False
    last_byte = item_start + (count - 1) * stride + 12
    return (last_byte <= view_length and view_start + view_length <= declared
            and declared <= bin_length)

def _index_buffer_valid(accessor, views, buffers, bin_data, position_count, mode):
    """Check indexed triangle primitives against real embedded index bytes."""
    if not isinstance(accessor, dict) or accessor.get("type") != "SCALAR" or "sparse" in accessor:
        return False
    component = accessor.get("componentType")
    formats = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4)}
    if type(component) is not int or component not in formats:
        return False
    fmt, size = formats[component]
    count, view_id = accessor.get("count"), accessor.get("bufferView")
    if (type(count) is not int or count < 3 or (mode == 4 and count % 3)
            or type(view_id) is not int or not 0 <= view_id < len(views)):
        return False
    view = views[view_id]
    if (not isinstance(view, dict) or type(view.get("buffer")) is not int
            or view["buffer"] != 0 or "byteStride" in view):
        return False
    if len(buffers) != 1 or not isinstance(buffers[0], dict) or "uri" in buffers[0]:
        return False
    declared = buffers[0].get("byteLength")
    view_start, view_length = view.get("byteOffset", 0), view.get("byteLength")
    item_start = accessor.get("byteOffset", 0)
    if any(type(v) is not int for v in (declared, view_start, view_length, item_start)):
        return False
    byte_count = count * size
    if (declared < 0 or view_start < 0 or view_start % 4 or view_length < byte_count
            or item_start < 0 or item_start % size or item_start + byte_count > view_length
            or view_start + view_length > declared or declared > len(bin_data)):
        return False
    start = view_start + item_start
    raw = memoryview(bin_data)[start:start + byte_count]
    return all(index < position_count for (index,) in struct.iter_unpack("<" + fmt, raw))

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
            return result
        n,kind=struct.unpack_from("<I4s",data,offset)
        offset+=8
        if n%4 or offset+n>len(data):
            errors.append("Unaligned or truncated GLB chunk")
            return result
        raw=data[offset:offset+n];offset+=n
        # glTF 2.0 GLB: JSON must be first; at most one BIN may follow.
        # Unknown, repeated or out-of-order chunks invalidate the whole audit.
        if json_chunk is None and kind==b"JSON":
            json_chunk=raw
        elif json_chunk is not None and bin_chunk is None and kind==b"BIN\x00":
            bin_chunk=raw
        else:
            errors.append("Unexpected, duplicated or out-of-order GLB chunk")
            return result
    if json_chunk is None:
        errors.append("Missing GLB JSON chunk")
        return result
    try:
        gltf=json.loads(json_chunk.decode("utf-8"))
    except (UnicodeError,ValueError):
        errors.append("Malformed GLB JSON chunk")
        return result
    if not isinstance(gltf,dict) or not isinstance(gltf.get("asset"),dict):
        errors.append("Malformed GLB asset metadata")
        return result
    if gltf["asset"].get("version")!="2.0":
        errors.append("Unsupported or missing glTF 2.0 asset")
    else:
        result["json_valid"]=True
    meshes=gltf.get("meshes",[])
    accessors=gltf.get("accessors",[])
    buffers=gltf.get("buffers",[])
    views=gltf.get("bufferViews",[])
    if not all(isinstance(v,list) for v in (meshes,accessors,buffers,views)):
        errors.append("Malformed glTF mesh, accessor, buffer or view collections")
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
            attrs=primitive.get("attributes")
            if not isinstance(attrs,dict):continue
            pos=attrs.get("POSITION")
            if type(pos) is not int or not 0<=pos<len(accessors):continue
            accessor=accessors[pos]
            if not _position_buffer_valid(accessor,views,buffers,result["bin_bytes"]):continue
            # An indexed primitive must also have real, in-range embedded indices.
            # A plausible POSITION accessor cannot rescue a broken index stream.
            if "indices" in primitive:
                index_id = primitive["indices"]
                if type(index_id) is not int or not 0 <= index_id < len(accessors):
                    continue
                if not _index_buffer_valid(accessors[index_id], views, buffers,
                                           bin_chunk or b"", accessor["count"],
                                           primitive.get("mode", 4)):
                    continue
            result["drawable_primitives"]+=1
            result["position_vertices"]+=accessor["count"]
    if result["drawable_primitives"]==0:
        errors.append("GLB has no triangle geometry with valid POSITION accessors")
    if (len(buffers)!=1 or not isinstance(buffers[0],dict)
            or "uri" in buffers[0] or type(buffers[0].get("byteLength")) is not int
            or buffers[0]["byteLength"] < 0):
        errors.append("GLB must declare one valid embedded binary buffer")
    elif buffers[0]["byteLength"]>result["bin_bytes"]:
        errors.append("Declared binary buffer exceeds embedded GLB BIN chunk")
    return result
