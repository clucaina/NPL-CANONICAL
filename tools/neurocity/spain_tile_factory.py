#!/usr/bin/env python3
"""Plan independent, repeatable 500m 3D-city production batches nationwide.
This is an auditable WORK PLAN, not a fake generated city or a deployment.
Require explicit official-source permissions and vertical datum per region.
"""
from __future__ import annotations
import argparse,json,math,re
from pathlib import Path

ALLOWED_CRS={25828,25829,25830,25831,4083}
STAGES=('geodata_audit','terrain_and_roads','heights','facade_sources',
        '3d_scene','navigation','learning_world','visual_and_license_qa')
def require(condition,message):
    if not condition:raise ValueError(message)
def build_plan(spec:dict,*,tile_m:int=500,max_tiles:int=64)->dict:
    require(isinstance(spec,dict),'City specification is required')
    city=spec.get('city')
    crs=spec.get('crs')
    box=spec.get('bbox_projected_m')
    require(isinstance(city,str) and bool(re.fullmatch(r'[a-z0-9_-]{3,48}',city)),
            'City slug unsafe')
    require(isinstance(crs,int) and crs in ALLOWED_CRS,
            'Unsupported Spanish official projection')
    require(isinstance(box,list) and len(box)==4 and all(
        isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in box),
        'No trusted projected extent')
    require(box[0]<box[2] and box[1]<box[3],'Inverted projected extent')
    require(isinstance(tile_m,int) and tile_m in (250,500,1000),'Unsupported geospatial resolution')
    require(1<=max_tiles<=256,'Excessive batch budget')
    x0,y0,x1,y1=box
    # CRS/projected-metric UTM tiles, not WebMercator lat/long arithmetic.
    i0=math.floor(x0/tile_m);i1=math.ceil(x1/tile_m)
    j0=math.floor(y0/tile_m);j1=math.ceil(y1/tile_m)
    total=(i1-i0)*(j1-j0)
    require(total<=max_tiles,'Coverage exceeds batch cap, split into adjacent lots')
    source=spec.get('sources',{})
    require(isinstance(source,dict),'Source metadata missing')
    allowed={'osm','orthophoto','lidar','street_photos','interiors','verified_shop_names'}
    require(set(source)<=allowed,'Unexpected private source in build plan')
    def approved(k):
        x=source.get(k,{})
        if not isinstance(x,dict):return False
        return x.get('verified') is True and x.get('license_approved') is True and
            bool(re.fullmatch(r'[a-f0-9]{64}',str(x.get('sha256',''))))
    result=[]
    for i in range(i0,i1):
        for j in range(j0,j1):
            jobs=[]
            for stage in STAGES:
                prerequisites={
                    'geodata_audit':[],
                    'terrain_and_roads':['geodata_audit'],
                    'heights':['geodata_audit'],
                    'facade_sources':['geodata_audit'],
                    '3d_scene':['terrain_and_roads','heights'],
                    'navigation':['3d_scene'],
                    'learning_world':['navigation'],
                    'visual_and_license_qa':['learning_world']
                }[stage]
                source_require={
                    'geodata_audit':['osm'],
                    'terrain_and_roads':['osm','orthophoto'],
                    'heights':['lidar'],
                    'facade_sources':['street_photos'],
                    '3d_scene':['osm','orthophoto','lidar'],
                    'navigation':['osm'],
                    'learning_world':['osm'],
                    'visual_and_license_qa':['osm','orthophoto','lidar']
                }[stage]
                missing=[k for k in source_require if not approved(k)]
                jobs.append({'stage':stage,'requires':prerequisites,
                    'source_status':'READY_FOR_COMPUTE' if not missing else 'BLOCKED_UNVERIFIED_SOURCE',
                    'missing_verified_sources':missing})
            tid=f'{city}_z{crs}_x{i}_y{j}'
            result.append({'id':tid,
                 'bbox_projected_m':[i*tile_m,j*tile_m,(i+1)*tile_m,(j+1)*tile_m],
                 'tasks':jobs,
                 'mm_fidelity_claimed':False,'real_interior_claimed':False,
                 'real_employee_identities_present':False})
    return {'schema':'neurocity.spain-tiles-production-plan.v1','city':city,
        'crs':'EPSG:'+str(crs),'tile_m':tile_m,
        'tiles_planned':len(result),'stages_per_tile':len(STAGES),
        'savings_strategy':'content_hash_checkpoint_and_asset_reuse',
        'public_deployed':False,'models_generated':0,
        'original_files_modified':0,'tiles':result}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--city-spec',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-tiles',type=int,default=64)
    args=p.parse_args()
    report=build_plan(json.loads(args.city_spec.read_text(encoding='utf8')),max_tiles=args.max_tiles)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('TILES_PLANNED',report['tiles_planned'],'MODELS_GENERATED',report['models_generated'])
if __name__=='__main__':main()
