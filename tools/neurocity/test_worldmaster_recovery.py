import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).parent
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
recover=load('worldmaster_recovery')
exporter=load('export_local_worldmaster')

def tiny_glb():
    json_chunk=json.dumps({"asset":{"version":"2.0"},"meshes":[
        {"primitives":[{"mode":4,"attributes":{"POSITION":0}}]}],
        "accessors":[{"count":3,"componentType":5126,"type":"VEC3"}]},separators=(',',':')).encode()
    json_chunk+=b' '*((-len(json_chunk))%4)
    return b'glTF'+struct.pack('<II',2,20+len(json_chunk))+struct.pack('<I4s',len(json_chunk),b'JSON')+json_chunk

def fixture_zip(path,broken_hash=False,with_lamps=False):
    tids=['r02_c00','r02_c01','r01_c01','r01_c02']
    assets={}
    for t in tids:
        for name in ('terrain','architecture'):
            assets[f'assets/source/ASSETS/tiles/{t}/{name}.glb']=tiny_glb()
    for name in ('Explanada_v50_PBR_1024','MASTER_EXPLANADA_FURNITURE_V50','MASTER_BANCOS_G131_V50',
                 'r02_c01_G19_PUERTA_STONE_STREET','r01_c01_G19_BEACH_BASE_G05','r01_c02_G19_BEACH_BASE_G05'):
        assets[f'assets/selected/{name}.glb']=tiny_glb()
    if with_lamps:
        assets['assets/prefabs/Farola_Globo_Simple_4m.glb']=tiny_glb()
    model={'geo':{'crs':'EPSG:25830','vertical_datum':'G05_UNVERIFIED'},
           'version':'synthetic-test','tile_ids':tids,
           'existingTileAssets':{t:['terrain','architecture'] for t in tids},
           'monuments':[],'façade_selected_by_cv05':[],
           'coastalScenes':[],'palm_positions':[]}
    hashes=[{'file':k,'size':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in assets.items()]
    if broken_hash:hashes[0]['sha256']='0'*64
    with ZipFile(path,'w',compression=ZIP_DEFLATED) as z:
        for name,data in assets.items():z.writestr('NEUROCITY_WORLD_MASTER/'+name,data)
        if with_lamps:
            g16={'fixtures':[{'id':f'G16_lamp_{i}','ground':{'x':280.0+i*14,
                  'y':2.1,'z':1400.0-i*13},'yaw':0.0,
                  'position_confidence':'PROVISIONAL'} for i in range(5)]}
            z.writestr('NEUROCITY_WORLD_MASTER/geo/CONTRATO/G16_PHYSICAL_FIXTURES.json',json.dumps(g16))
        z.writestr('NEUROCITY_WORLD_MASTER/world-master.json',json.dumps(model))
        z.writestr('NEUROCITY_WORLD_MASTER/source-hashes.json',json.dumps(hashes))
        z.writestr('NEUROCITY_WORLD_MASTER/README_WORLD_MASTER_ES.md','Source revision synthetic fixture')
        z.writestr('NEUROCITY_WORLD_MASTER/LICENCIAS_PROCEDENCIA_WORLD_MASTER.md','Not licensed for redistribution')
    return len(assets)

class RecoveryTests(unittest.TestCase):
    def test_audit_real_glb_and_hashes_no_bytes_republished(self):
        with tempfile.TemporaryDirectory() as t:
            z=Path(t)/'existing.zip'
            n=fixture_zip(z)
            out=recover.inventory_zip(z)
            self.assertEqual(out['source_entries_verified'],n)
            self.assertEqual(out['validated_glb_count'],n)
            self.assertEqual(out['errors'],[])
            self.assertEqual(out['asset_bytes_uploaded_to_public_repo'],0)
            self.assertFalse(out['vertical_datum_verified'])
            self.assertFalse(out['license_cleared_for_public_redistribution'])
    def test_corruption_detected_without_rewriting_original(self):
        with tempfile.TemporaryDirectory() as t:
            z=Path(t)/'existing.zip';fixture_zip(z,broken_hash=True)
            initial=hashlib.sha256(z.read_bytes()).hexdigest()
            out=recover.inventory_zip(z)
            self.assertEqual(len(out['errors']),1)
            self.assertEqual(out['errors'][0]['reason'],'SHA256_MISMATCH')
            with self.assertRaises(ValueError):exporter.compile_manifest(z)
            self.assertEqual(hashlib.sha256(z.read_bytes()).hexdigest(),initial)
    def test_local_pack_has_mosaic_and_four_tiles_but_no_original_override(self):
        with tempfile.TemporaryDirectory() as t:
            z=Path(t)/'existing.zip';fixture_zip(z)
            root=Path(t)/'world-master'
            preview=exporter.build_local_pack(z,root,metadata_only=True)
            self.assertEqual(len(preview['tiles']),4)
            self.assertEqual(preview['crs'],'EPSG:25830')
            self.assertFalse(preview['public_redistribution_allowed'])
            self.assertEqual(preview['asset_count'],14)
            self.assertEqual(sum(x['role']=='mosaic' for t in preview['tiles'] for x in t['assets']),1)
            self.assertFalse((root/'assets').exists())
            full=exporter.build_local_pack(z,root,metadata_only=False)
            self.assertEqual(full['asset_count'],preview['asset_count'])
            self.assertTrue((root/'assets/selected/Explanada_v50_PBR_1024.glb').exists())
            self.assertTrue((root/'ORIGINAL_SOURCE_NOTICE.md').exists())
            self.assertFalse((root/'assets/maya.glb').exists())
    def test_original_g16_streetlamps_are_preserved_as_provisional_local_mobile_models(self):
        with tempfile.TemporaryDirectory() as t:
            z=Path(t)/'existing.zip';fixture_zip(z,with_lamps=True)
            m=exporter.compile_manifest(z)
            self.assertEqual(m['asset_count'],15)
            lamps=[a for tile in m['tiles'] for a in tile['assets'] if a['role']=='streetlamp']
            self.assertEqual(len(lamps),1)
            self.assertEqual(lamps[0]['path'],'assets/prefabs/Farola_Globo_Simple_4m.glb')
            self.assertEqual(len(lamps[0]['placements']),5)
            self.assertTrue(lamps[0]['source_hash_record'])
            self.assertNotIn('actual_shop',json.dumps(lamps))
    def test_invalid_binary_does_not_pass_as_real_3d(self):
        with self.assertRaises(ValueError):recover.glb_structural_qa(b'glTF')
        ok=tiny_glb()
        self.assertEqual(recover.glb_structural_qa(ok)['drawable_primitives'],1)
        with self.assertRaises(ValueError):recover.glb_structural_qa(ok[:-4])

if __name__=='__main__':unittest.main()
