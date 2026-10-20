#!/usr/bin/env python3
"""Bounded nine-zone real Alicante WFS -> ephemeral Blender 3D coverage audit.

Per-run public outputs contain COUNTS, hashes and source availability only.
Neither GML nor a real-person/property-specific GLB is uploaded or published.
"""
import concurrent.futures
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from time import sleep
from pathlib import Path

from catastro_grid import compile_grid,source_plan
from catastro_live_probe import OSM,BBOX_OSM,CENTER,R,receive

PUBLIC_QA=Path('/tmp/neurocity-cadastre-public-evidence')
BUILD_SCRIPT=Path(__file__).resolve().parents[2]/'demos/npl-world/open_city_pipeline/build_blender.py'

def run():
    report={
      'schema':'neurocity.public-cadastre-grid-qa.v1',
      'source':'DG_CATASTRO_INSPIRE_BU_BUILDINGPART',
      'tile_strategy':'nine_UTM_25830_tiles_35m_overlap',
      'planned_tiles':9,
      'retrieved_tiles':0,
      'source_status':'UNTESTED',
      'actual_city_models_generated':0,
      'original_osm_modified':False,
      'source_gml_published':False,
      'source_glb_published':False,
      'height_is_surveyed':False,
      'height_method':'official_floors_times_3m_ESTIMATE',
    }
    with tempfile.TemporaryDirectory(prefix='neurocity_grid_') as tmp:
        p=Path(tmp)
        try:
            osm=p/'alicante.osm'
            report['osm_source_bytes']=receive(OSM,9*1024*1024,osm,'api.openstreetmap.org')
        except Exception as exc:
            report.update(source_status='BLOCKED_OSM',blocker_class=type(exc).__name__)
            return report
        initial_osm_sha=hashlib.sha256(osm.read_bytes()).hexdigest()
        center=[R*math.radians(CENTER[0]),R*math.log(math.tan(math.pi/4+math.radians(CENTER[1])/2))]
        source_manifest=p/'source_manifest.json'
        source_manifest.write_text(json.dumps({'bbox':BBOX_OSM,'center_mercator':center}))
        plan=source_plan(BBOX_OSM)
        folder=p/'catastro_grid_tiles';folder.mkdir()
        successes=[]
        failures={}
        def request(tile):
            target=folder/tile['name']
            try:
                count=receive(tile['url'],16*1024*1024,target,'ovc.catastro.meh.es')
                return tile,count,None
            except Exception as exc:
                target.unlink(missing_ok=True)
                return tile,0,type(exc).__name__
        # Limited to two official WFS connections, no third-party proxy,
        # no persistent requests, no unbounded retries, no data publication.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            for tile,count,error in pool.map(request,plan):
                if error:failures[tile['id']]=error
                else:successes.append((tile['id'],tile['url'],folder/tile['name']))
        report['initial_retrieved_tiles']=len(successes)
        # DG Catastro sometimes disconnects an otherwise valid WFS BBOX.
        # A second PASS only re-fetches missing cells, serially and politely;
        # no global retries, no infinite loop and no duplicates.
        recovered=[]
        for tile in plan:
            if tile['id'] not in failures:continue
            sleep(6)
            candidate,bytes_count,error=request(tile)
            if error:
                failures[tile['id']]=error
                continue
            successes.append((candidate['id'],candidate['url'],folder/candidate['name']))
            recovered.append(candidate['id'])
            del failures[candidate['id']]
        report['recovered_after_backoff']=recovered
        report['retrieved_tiles']=len(successes)
        report['unavailable_tile_ids']=sorted(failures)
        report['unavailable_by_error_type']={t:sum(1 for e in failures.values() if e==t) for t in set(failures.values())}
        if not successes:
            report['source_status']='BLOCKED_ALL_OFFICIAL_GRID_TILES'
            return report
        try:
            overlay=compile_grid(samples=successes,osm=osm,manifest=source_manifest)
        except Exception as exc:
            report.update(source_status='BLOCKED_GML_VALIDATION',blocker_class=type(exc).__name__)
            return report
        report.update({
          'source_status':'VERIFIED_OFFICIAL_GRID',
          'coverage_complete':overlay['coverage_complete'],
          'verified_source_tiles':overlay['verified_tile_count'],
          'official_raw_parts':overlay['source_candidate_parts'],
          'unique_candidate_parts':overlay['unique_candidate_parts'],
          'duplicate_parts_rejected':overlay['source_duplicates'],
          'conflicting_duplicates_rejected':overlay['conflicting_duplicates_rejected'],
          'total_osm_buildings':overlay['total_osm_buildings'],
          'matched_osm_buildings':overlay['matched_osm_count'],
          'matched_official_parts':overlay['matched_bu_part_count'],
          'native_official_parts_eligible':overlay['independent_official_part_count'],
          'native_official_exclusion_reasons':overlay['independent_official_selection_qa'],
          'ambiguous_osm_matches_rejected':overlay['matching']['ambiguous'],
          'source_metadata':[
             {'tile':x['tile_id'],'sha256':x['sha256'],
              'returned':x['returned'],'candidate_parts':x['candidates']}
             for x in overlay['source_tiles']
          ]
        })
        if overlay['matched_osm_count']==0:
            report['source_status']='NO_STRICT_MATCHED_BUILDINGS'
            return report
        work=p/'blender';data=work/'input';data.mkdir(parents=True);(work/'output').mkdir()
        shutil.copyfile(osm,data/'alicante.osm')
        shutil.copytree(folder,data/'catastro_grid_tiles')
        (data/'catastro_building_parts.json').write_text(json.dumps(overlay))
        west,south,east,north=BBOX_OSM
        def mercator(lon,lat):
            return (R*math.radians(lon),
                    R*math.log(math.tan(math.pi/4+math.radians(lat)/2)))
        minx,miny=mercator(west,south);maxx,maxy=mercator(east,north)
        manifest={'bbox':BBOX_OSM,'center_mercator':center,
                  'bbox_local_m':[minx-center[0],miny-center[1],maxx-center[0],maxy-center[1]],
                  'real_orthophoto':False}
        (data/'source_manifest.json').write_text(json.dumps(manifest))
        try:
            subprocess.run(['blender','-b','--factory-startup','-t','2',
                '--python-exit-code','1','-P',str(BUILD_SCRIPT)],
                cwd=work,check=True,timeout=180,capture_output=True)
            scene_qa=json.loads((work/'output/QA_source_report.json').read_text())
            glb=work/'output/Alicante_REAL_OSM_PNOA.glb'
            if (scene_qa['cadastre_original_osm_footprints_replaced']!=overlay['matched_osm_count']
                or scene_qa['cadastre_building_parts_geometry']!=overlay['matched_bu_part_count']
                or scene_qa['cadastre_native_official_parts_added']!=overlay['independent_official_part_count']
                or scene_qa['cadastre_verified_source_tiles']!=overlay['verified_tile_count']
                or scene_qa['cadastre_coverage_complete']!=overlay['coverage_complete']
                or not glb.is_file() or glb.stat().st_size<1000):
                raise ValueError('Real source and Blender model contract mismatch')
            report.update({
                'actual_city_models_generated':1,
                'actual_blender_3d_official_buildings':scene_qa['cadastre_original_osm_footprints_replaced'],
                'actual_blender_3d_building_parts':scene_qa['cadastre_building_parts_geometry'],
                'actual_blender_3d_native_parts':scene_qa['cadastre_native_official_parts_added'],
                'ephemeral_glb_bytes':glb.stat().st_size,
                'ephemeral_glb_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),
                'original_osm_modified':hashlib.sha256(osm.read_bytes()).hexdigest()!=initial_osm_sha
            })
            if report['original_osm_modified']:raise ValueError('OSM source unexpectedly changed')
        except Exception as exc:
            report['source_status']='BLOCKED_REAL_3D_EXPORT'
            report['export_blocker_class']=type(exc).__name__
    return report

if __name__=='__main__':
    report=run()
    PUBLIC_QA.mkdir(parents=True,exist_ok=True)
    (PUBLIC_QA/'OFFICIAL_WFS_3X3_GRID_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='source_metadata'},ensure_ascii=False,indent=2))
