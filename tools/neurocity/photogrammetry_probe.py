#!/usr/bin/env python3
"""Bounded REAL photo -> SfM probe on a CC-BY-SA Panoramax street sequence.
Public photos are temporary, not distributed. Only a numerical QA report leaves the job.
No faces/patients/biometric models, no privileged datasets, no deployment.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request,urlopen
from open_imagery_inventory import (
    FEDERATION, ALICANTE_BBOX, load_public_api, license_audit
)

LIMIT=100
MAX_IMAGE_BYTES=6*1024*1024
MAX_PHOTOS=30

def safe_image_url(url):
    if not isinstance(url,str) or len(url)>2048:return False
    try:
        p=urlsplit(url)
        host=(p.hostname or '').lower()
        return (p.scheme=='https' and not p.username and not p.password and
                (host in ('api.panoramax.xyz','panoramax.openstreetmap.fr','panoramax.ign.fr')
                 or host.endswith('.panoramax.fr')) and
                p.path.lower().endswith(('.jpeg','.jpg')) and not p.fragment)
    except ValueError:return False

def choose_sequence(payload,photo_limit=MAX_PHOTOS):
    audit=license_audit(payload.get('features',[]))
    permitted={(x['sequence_id'],x['id']) for x in audit['items']}
    sequences=collections.defaultdict(list)
    for feat in payload.get('features',[]):
        if not isinstance(feat,dict):continue
        sid,iid=feat.get('collection'),feat.get('id')
        if (sid,iid) not in permitted:continue
        assets=feat.get('assets')
        if not isinstance(assets,dict):continue
        entry=assets.get('sd') or assets.get('hd')
        if not isinstance(entry,dict):continue
        url=entry.get('href')
        if not safe_image_url(url):continue
        when=feat.get('properties',{}).get('datetime','')
        sequences[sid].append({'url':url,'image_id':iid,'date':when or ''})
    if not sequences:return [],{'eligible_sources':audit['license_link_approved_count'],
                                 'eligible_with_safe_image_url':0}
    # One continuous track is necessary for viable parallax, not 20 unrelated photos.
    sid,ordered=max(sequences.items(),key=lambda pair:len(pair[1]))
    ordered.sort(key=lambda x:(x['date'],x['image_id']))
    if len(ordered)>photo_limit:
        # COLMAP requires abundant parallax/overlap. Widely spaced photos were
        # observed to yield no initial pair in the first real Alicante run.
        start=(len(ordered)-photo_limit)//2
        ordered=ordered[start:start+photo_limit]
    return ordered,{'eligible_sources':audit['license_link_approved_count'],
                    'longest_sequence_available':len(sequences[sid]),
                    'sequence_id':sid,'sample_size':len(ordered)}

def photo_bytes(url):
    if not safe_image_url(url):raise ValueError('Image host or format is not allowed')
    req=Request(url,headers={'User-Agent':'NeuroCity-Open-COLMAP/1.0',
                             'Accept':'image/jpeg'})
    with urlopen(req,timeout=18) as response:
        # The original source is authorized; reject redirects to unapproved binary hosts.
        if not safe_image_url(response.url):raise ValueError('Unapproved image redirect')
        if response.status!=200:raise ValueError('Image source HTTP '+str(response.status))
        content=response.read(MAX_IMAGE_BYTES+1)
    if len(content)>MAX_IMAGE_BYTES or not content.startswith(b'\xff\xd8\xff'):
        raise ValueError('File is not a bounded JPEG')
    return content

def prepare_photos(items,image_dir):
    from PIL import Image,ImageOps,UnidentifiedImageError
    from io import BytesIO
    successes=0
    errors=collections.Counter()
    aspect={'panorama_2to1':0,'regular_landscape':0,'portrait':0}
    for item in items:
        if successes>=MAX_PHOTOS:break
        try:
            raw=photo_bytes(item['url'])
            with Image.open(BytesIO(raw)) as image:
                if image.width<400 or image.height<300 or image.width*image.height>32_000_000:
                    raise ValueError('Unsafe or undersized image geometry')
                ratio=image.width/image.height
                key='panorama_2to1' if ratio>=1.85 else ('regular_landscape' if ratio>=1 else 'portrait')
                aspect[key]+=1
                # Save RGB downsample without EXIF/GPS and without emitting originals.
                converted=ImageOps.exif_transpose(image).convert('RGB')
                converted.thumbnail((1400,1050))
                output=image_dir/f'frame_{successes:03d}.jpg'
                converted.save(output,'JPEG',quality=84,exif=b'')
            successes+=1
        except Exception as exc:
            errors[type(exc).__name__]+=1
    return successes,dict(errors),aspect

def colmap_sparse(image_dir,work_dir):
    report={'attempted':False,'registered_images':0,'sparse_points':0}
    if shutil.which('colmap') is None:
        report['status']='COLMAP_NOT_INSTALLED'
        return report
    db=work_dir/'recon.db'
    models=work_dir/'models'
    models.mkdir()
    commands=[
      ['colmap','feature_extractor','--database_path',str(db),'--image_path',str(image_dir),
       '--ImageReader.single_camera','1','--SiftExtraction.use_gpu','0',
       '--SiftExtraction.max_image_size','1400','--SiftExtraction.max_num_features','5000'],
      ['colmap','exhaustive_matcher','--database_path',str(db),
       '--SiftMatching.use_gpu','0'],
      ['colmap','mapper','--database_path',str(db),'--image_path',str(image_dir),
       '--output_path',str(models)]
    ]
    report['attempted']=True
    for n,cmd in enumerate(commands):
        try:
            p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,timeout=240,check=False)
        except subprocess.TimeoutExpired:
            report['status']='COLMAP_STAGE_TIMEOUT_'+str(n)
            return report
        report['stage_'+str(n)+'_exit']=p.returncode
        if p.returncode!=0:
            report['status']='COLMAP_STAGE_FAILED_'+str(n)
            report['log_tail']=p.stdout[-400:].replace(str(work_dir),'<ephemeral>')
            return report
    for model in models.iterdir():
        if not model.is_dir():continue
        images=model/'images.bin'
        points=model/'points3D.bin'
        if not images.exists() or not points.exists() or images.stat().st_size<8 or points.stat().st_size<8:
            continue
        import struct
        nimg=struct.unpack('<Q',images.read_bytes()[:8])[0]
        npts=struct.unpack('<Q',points.read_bytes()[:8])[0]
        report['registered_images']=max(report['registered_images'],nimg)
        report['sparse_points']=max(report['sparse_points'],npts)
    report['status']='SPARSE_RECONSTRUCTION_MEASURED' if report['registered_images']>=5 and report['sparse_points']>=100 else 'INSUFFICIENT_CAMERA_REGISTRATION'
    return report

def run(output):
    report={
        'schema':'neurocity.public-photo-sfm-experiment.v1',
        'input_area':'Alicante_explanada_bbox',
        'license':'CC-BY-SA-4.0_photos_only',
        'provenance':'Panoramax STAC per-photo licence links',
        'uses_google_street_view':False,
        'private_or_patient_data':False,
        'images_published':0,
        'model_published':False,
        'original_osm_or_npl_modified':False}
    try:
        url=FEDERATION+'/search?'+urlencode({'bbox':','.join(map(str,ALICANTE_BBOX)),'limit':LIMIT})
        raw=load_public_api(url,'api.panoramax.xyz')
        if not isinstance(raw,dict) or not isinstance(raw.get('features'),list):raise ValueError('STAC schema')
        items,meta=choose_sequence(raw)
        report['eligibility']=meta
        report['candidate_frame_count']=len(items)
        if len(items)<8:
            report['status']='BLOCKED_NO_8_CONTIGUOUS_LICENSED_FRAME_URLS'
        else:
            with tempfile.TemporaryDirectory(prefix='neurocity-stac-photo-') as temp:
                root=Path(temp)
                images=root/'images';images.mkdir()
                count,failures,aspects=prepare_photos(items,images)
                report['ephemeral_photos_processed']=count
                report['input_photo_aspect_distribution']=aspects
                report['download_error_types']=failures
                if count<8:
                    report['status']='BLOCKED_INSUFFICIENT_VERIFIED_PHOTO_BYTES'
                else:
                    report['colmap']=colmap_sparse(images,root)
                    report['status']=report['colmap']['status']
    except Exception as exc:
        report['status']='SOURCE_BLOCKER'
        report['error_type']=type(exc).__name__
        report['error_summary']=str(exc)[:150]
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    outcome=run(a.output)
    print('OPEN_PHOTO_SFM_STATUS',outcome.get('status'))
    print('IMAGES_PROCESSED_EPHEMERALLY',outcome.get('ephemeral_photos_processed',0))
    print('REGISTERED_CAMERAS',outcome.get('colmap',{}).get('registered_images',0))
    print('TRIANGULATED_3D_POINTS',outcome.get('colmap',{}).get('sparse_points',0))
