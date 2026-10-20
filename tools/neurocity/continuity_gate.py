#!/usr/bin/env python3
"""Stop loss of working NeuroCity modules across independent chat branches.
Every criterion checks REAL source committed in this branch, not historical
assistant prose. Source-only; never reads patients, avatars, private Drive files.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

CONTRACTS={
 'public_city_osm':('demos/npl-world/open_city_pipeline/build_blender.py',[
   'real_osm_buildings','OSM_mapped_piers_width_estimated',
   'OSM_mapped_fences_height_estimated',
   'OSM_tree_positions_with_illustrative_foliage']),
 'recovered_v50_geography':('demos/npl-world/visual_viewer/world_master_loader.mjs',[
   'RecoveredMasterTiles','SHA256 mismatch','instantiateMasterPalms','onCoverage']),
 'precise_tile_projection':('demos/npl-world/visual_viewer/geo_alignment.mjs',[
   'EPSG:25830','EPSG:3857','matrixElementsForTile']),
 'archive_export_local_only':('tools/neurocity/export_local_worldmaster.py',[
   'NEUROCITY','source_archive_sha256','public_redistribution_allowed']),
 'asphalt_from_osm':('demos/npl-world/visual_viewer/road_surfaces.mjs',[
   'enhanceMappedOSMRoads','SURFACE_SOURCE']),
 'mediterranean_hedges':('demos/npl-world/visual_viewer/hedge_layer.mjs',[
   'InstancedMesh','HEDGE_SOURCE']),
 'G13_signed_walking_physics':('demos/npl-world/visual_viewer/world_physics.mjs',[
   'PHYSICAL_TILES','canOccupy','SHA256 mismatch','PHYSICAL_WALKABLE']),
 'mediterranean_water_optics_from_peer_branch':('demos/npl-world/visual_viewer/water_surface.mjs',[
   'enhanceSourceMappedWater','VERIFIED_WATER_NAME','addedSeaPlanes:0',
   'reducedMotion']),
 'coast_osm_source_audit':('tools/factory/coast_inventory.py',[
   'coastline_geometry_source_available','piers_source_available',
   'coastal_rendering_verified']),
 'coast_osm_audit_tests':('tools/factory/test_coast_inventory.py',[
   'test_does_not_invent_sea_or_boats']),
 'NPL_conflictometro_bounded':('demos/npl-world/visual_viewer/app.js',[
   'loadNPLOpenData','inspectDataset','RecoveredPhysicalAtlas',
   'makeSourceComparisonControl']),
 'professional_trencadis_mosaic':('demos/npl-world/visual_viewer/explanada_mosaic.mjs',[
   'paintMosaic','irregularGrout','historicalV50PreferredWhenAvailable']),
 'alternating_palm_geometries':('demos/npl-world/visual_viewer/urban_kit.mjs',[
   'palm_canopies_','leafletCount','InstancedMesh']),
 'facades_source_stucco':('demos/npl-world/visual_viewer/facade_stucco.mjs',[
   'enhanceMappedBuildingFacades','geometricFootprintsPreserved','shopsFabricated:0']),
 'functional_interactive_3d_brain':('demos/npl-world/visual_viewer/npl_brain3d.mjs',[
   'buildBrainModel','mountBrain3D','raycaster','onSelect']),
 'npl_observed_behavior_not_biometric':('demos/npl-world/visual_viewer/npl_behavior.mjs',[
   'sampleBehavior','LOCAL_GAME_ACTIONS_ONLY_NOT_NEURAL_MEASUREMENT','patientData:false']),
 'no_fake_real_people':('docs/NEUROCITY_RECUPERACION_MUNDO_Y_FABRICA_ESPANA.md',[
   'interiores ficticios','consentimiento'])
}
def verify(root:Path)->dict:
    root=root.resolve()
    results=[]
    for capability,(rel,needles) in CONTRACTS.items():
        path=root/rel
        # Each path in the manifest is a literal path beneath the source tree.
        if path.resolve()!=root/rel or not path.is_file():
            results.append({'capability':capability,'status':'MISSING_SOURCE','path':rel});continue
        data=path.read_text(encoding='utf-8')
        missing=[needle for needle in needles if needle not in data]
        results.append({'capability':capability,
            'status':'PASS_SOURCE_PRESENT' if not missing else 'REGRESSION',
            'missing_contract_markers':missing,'path':rel})
    private_tree=root/'demos/npl-world/visual_viewer/world-master'
    if private_tree.exists():
        results.append({'capability':'private_drive_assets_not_published',
            'status':'PRIVATE_ARCHIVE_IN_PUBLIC_SOURCE','path':str(private_tree.relative_to(root))})
    else:
        results.append({'capability':'private_drive_assets_not_published',
            'status':'PASS_SOURCE_PRESENT'})
    passed=sum(x['status']=='PASS_SOURCE_PRESENT' for x in results)
    return {'schema':'neurocity.cross-chat-source-continuity.v1',
        'checks':len(results),'passed':passed,'failed':len(results)-passed,
        'source_only':True,'source_bytes_not_republished':True,
        'checks_by_capability':results,
        'non_certifications':[
          'This does not certify visual realism, geometry location accuracy or gameplay polish',
          'This does not mean private G19 world assets have been published or approved',
          'No verified real interiors, employee avatars, real-time MMO or 3D photos'
        ]}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo-root',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    report=verify(args.repo_root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('NEUROCITY_CROSS_CHAT_SOURCE_CONTINUITY',report['passed'],'/',report['checks'])
    if report['failed']:raise SystemExit(2)
if __name__=='__main__':main()
