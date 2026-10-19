#!/usr/bin/env python3
"""Acquire a SMALL, audited sample of authentic Poly Haven CC0 GLBs; NO deployment.
Never re-upload raw 3D assets into the public repository. Outputs CI artifact only.
No site login, no credit card, no personal files, no public write API.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen

BASE='https://api.polyhaven.com'
SLUGS=('street_lamp_01','modular_street_seating','painted_wooden_bench')
MAX_BYTES=16*1024*1024
MAX_TRIS=250_000
MAX_DECODED_BLEND_BYTES=64*1024*1024

def decode_blend(raw):
    """Poly Haven sometimes stores .blend as a full zstd frame.
    Stream-decompress under a hard cap, never unpickle or execute 3D content.
    """
    if raw.startswith(b'\x28\xb5\x2f\xfd'):
        import io
        import zstandard
        with zstandard.ZstdDecompressor().stream_reader(io.BytesIO(raw)) as stream:
            data=stream.read(MAX_DECODED_BLEND_BYTES+1)
    else:
        data=raw
    if len(data)>MAX_DECODED_BLEND_BYTES or not data.startswith(b'BLENDER'):
        raise ValueError('Not a bounded Blender source after decoding')
    return data

def permitted(url):
    try:
        p=urlsplit(url)
        return (p.scheme=='https' and p.hostname in {'dl.polyhaven.org','cdn.polyhaven.com'}
                and not p.username and not p.password and not p.fragment)
    except (ValueError,TypeError,AttributeError):
        return False

def collect_glbs(tree):
    """Poly Haven /files/{id} uses nested formats/resolutions; only direct GLB leaves."""
    result=[]
    def walk(obj):
        if isinstance(obj,dict):
            url=obj.get('url')
            size=obj.get('size')
            if (permitted(url) and isinstance(size,int) and not isinstance(size,bool)
                    and urlsplit(url).path.lower().endswith('.glb')):
                result.append({'url':url,'size':size,'md5':obj.get('md5')})
            for item in obj.values():
                if isinstance(item,(dict,list)):
                    walk(item)
        elif isinstance(obj,list):
            for item in obj:walk(item)
    walk(tree)
    return sorted([e for e in result if 1000<e['size']<=MAX_BYTES],
                  key=lambda e:(e['size'],e['url']))

def collect_blends(tree):
    out=[]
    def walk(obj):
        if isinstance(obj,dict):
            url=obj.get('url')
            size=obj.get('size')
            if (permitted(url) and isinstance(size,int) and not isinstance(size,bool)
                    and urlsplit(url).path.lower().endswith('.blend') and 1000<size<=MAX_BYTES):
                out.append({'url':url,'size':size,'md5':obj.get('md5')})
            for child in obj.values():
                if isinstance(child,(dict,list)):walk(child)
        elif isinstance(obj,list):
            for child in obj:walk(child)
    walk(tree)
    return sorted(out,key=lambda e:(e['size'],e['url']))

def describe_variants(tree):
    formats={}
    def walk(obj):
        if isinstance(obj,dict):
            url=obj.get('url')
            size=obj.get('size')
            if permitted(url) and isinstance(size,int) and not isinstance(size,bool):
                ext=Path(urlsplit(url).path).suffix.lower() or 'no_extension'
                entry=formats.setdefault(ext,{'count':0,'smallest_size':size})
                entry['count']+=1
                entry['smallest_size']=min(entry['smallest_size'],size)
            for v in obj.values():
                if isinstance(v,(dict,list)):walk(v)
        elif isinstance(obj,list):
            for v in obj:walk(v)
    walk(tree)
    return dict(sorted(formats.items()))

def validate_glb(raw):
    if len(raw)<24 or raw[:4]!=b'glTF' or len(raw)>MAX_BYTES:
        raise ValueError('Not bounded binary glTF')
    version,total=struct.unpack_from('<II',raw,4)
    if version!=2 or total!=len(raw):
        raise ValueError('Invalid glTF version/size')
    length,kind=struct.unpack_from('<I4s',raw,12)
    if kind!=b'JSON' or length<=0 or 20+length>len(raw):
        raise ValueError('Missing glTF JSON chunk')
    scene=json.loads(raw[20:20+length])
    meshes=scene.get('meshes',[])
    if not isinstance(meshes,list) or not meshes:
        raise ValueError('No geometry in asset')
    accessors=scene.get('accessors',[])
    tris=0
    for mesh in meshes:
        for prim in mesh.get('primitives',[]):
            if prim.get('mode',4)!=4:continue
            idx=prim.get('indices')
            if isinstance(idx,int) and 0<=idx<len(accessors):
                tris+=int(accessors[idx].get('count',0))//3
    if tris>MAX_TRIS:
        raise ValueError('Too many triangles for direct WebGL import')
    return {'mesh_count':len(meshes),'triangles_indexed':tris,'materials':len(scene.get('materials',[]))}

def request_bytes(url, max_bytes):
    req=Request(url,headers={'User-Agent':'NeuroCity-CC0-Audit/1.0 (clucaina/NPL-CANONICAL)'})
    with urlopen(req,timeout=45) as response:
        if not (response.url.startswith(BASE+'/files/') or permitted(response.url)):
            raise ValueError('Unapproved response host')
        if response.status!=200:raise RuntimeError('HTTP '+str(response.status))
        raw=response.read(max_bytes+1)
    if len(raw)>max_bytes:raise ValueError('Download over safe byte cap')
    return raw

def acquire(output,slugs=SLUGS):
    output.mkdir(parents=True,exist_ok=True)
    report={'schema':'neurocity.verified-cc0-glb.v1','provider':'Poly Haven',
        'source':'https://api.polyhaven.com','license':'CC0-1.0','deployed':False,
        'included_in_georeferenced_city':False,'models':[]}
    for slug in slugs:
        if not re.fullmatch(r'[a-z0-9_]{3,70}',slug):raise ValueError('Invalid slug')
        item={'id':slug,'source_url':'https://polyhaven.com/a/'+slug,'status':'NOT_CHECKED'}
        try:
            tree=json.loads(request_bytes(BASE+'/files/'+slug,1_500_000))
            variants=collect_glbs(tree)
            item['provider_formats']=describe_variants(tree)
            item['glb_variants_under_16mb']=len(variants)
            if not variants:
                blends=collect_blends(tree)
                item['blend_variants_under_16mb']=len(blends)
                if not blends:
                    item['status']='NO_DIRECT_LIGHTWEIGHT_3D_SOURCE'
                else:
                    chosen=blends[0]
                    raw=request_bytes(chosen['url'],MAX_BYTES)
                    if len(raw)!=chosen['size']:
                        raise ValueError('Provider file size mismatch')
                    packed=raw
                    raw=decode_blend(packed)
                    item['provider_encoded_sha256']=hashlib.sha256(packed).hexdigest()
                    item['provider_encoded_bytes']=len(packed)
                    md5=chosen.get('md5')
                    if isinstance(md5,str) and re.fullmatch(r'[0-9a-fA-F]{32}',md5):
                        if hashlib.md5(packed).hexdigest()!=md5.lower():
                            raise ValueError('Provider MD5 mismatch')
                    item['sha256']=hashlib.sha256(raw).hexdigest()
                    item['bytes']=len(raw)
                    item['file']=slug+'.blend'
                    (output/item['file']).write_bytes(raw)
                    item['status']='SOURCE_BLEND_DOWNLOADED_NEEDS_SANDBOX_CONVERSION'
            else:
                chosen=variants[0]
                raw=request_bytes(chosen['url'],MAX_BYTES)
                if chosen['size']!=len(raw):raise ValueError('Provider size mismatch')
                md5=chosen.get('md5')
                if isinstance(md5,str) and re.fullmatch(r'[0-9a-fA-F]{32}',md5):
                    if hashlib.md5(raw).hexdigest()!=md5.lower():raise ValueError('Provider MD5 mismatch')
                detail=validate_glb(raw)
                if detail['triangles_indexed']<1:
                    raise ValueError('No triangle index data; manual mesh audit required')
                item.update(detail)
                item['bytes']=len(raw)
                item['sha256']=hashlib.sha256(raw).hexdigest()
                item['status']='DOWNLOADED_VALIDATED_NOT_INTEGRATED'
                name=slug+'.glb'
                (output/name).write_bytes(raw)
                item['file']=name
        except Exception as e:
            item['status']='BLOCKED_REVIEW_REQUIRED'
            item['error']=type(e).__name__+': '+str(e)[:180]
        report['models'].append(item)
    report['blender_sources_downloaded']=sum(v['status']=='SOURCE_BLEND_DOWNLOADED_NEEDS_SANDBOX_CONVERSION' for v in report['models'])
    report['validated_downloads']=sum(v['status']=='DOWNLOADED_VALIDATED_NOT_INTEGRATED' for v in report['models'])
    (output/'MANIFEST.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    report=acquire(args.output)
    print(json.dumps(report,ensure_ascii=False,indent=2))
