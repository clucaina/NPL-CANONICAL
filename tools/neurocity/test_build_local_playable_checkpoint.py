import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

path=Path(__file__).with_name('build_local_playable_checkpoint.py')
spec=importlib.util.spec_from_file_location('build_local_playable_checkpoint',path)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CheckpointIntegrationTests(unittest.TestCase):
 def setup_sources(self,root:Path,*,bad_original=False):
  old=root/'old_v5.zip';runtime=root/'runtime.zip';geo=root/'new_geo.zip'
  originals={}
  with ZipFile(old,'w') as z:
   for i in range(71):
    content=(b'glTF'+str(i).encode()+b'EXISTING_SOURCE')
    rel=f'assets/source/ASSETS/tiles/r02_c00/{i:03d}.glb'
    originals[rel]={'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
    z.writestr('world-master/'+rel,content)
   if bad_original:
    originals['assets/source/ASSETS/tiles/r02_c00/001.glb']['sha256']='0'*64
   z.writestr('world-master/manifest.json',json.dumps({
     'crs':'EPSG:25830','public_redistribution_allowed':False,
     'asset_hashes':originals,'source_archive_sha256':'f'*64
   }))
   for k in range(12):
    z.writestr(f'world-master/geo/data/physical_r{k:02d}_c00.json','{}')
   z.writestr('assets/conflictometro_public_verified.json','{"original":"never overwrite"}')
   z.writestr('ABRIR_NEUROCITY_MUNDO_RECUPERADO_WINDOWS.bat',
     'start http://127.0.0.1:8766/?worldmaster=1')
   z.writestr('index.html','old text panel')
  with ZipFile(runtime,'w') as z:
   z.writestr('index.html','<html><body><canvas id="nplBrainCanvas"></canvas>'+
              '<details id="nplMethods"></details><script src="./game.js"></script></body></html>')
   z.writestr('game.js','NPL_BRAIN3D brainActivityMeasured '+'x'*60000)
  with ZipFile(geo,'w') as z:
   z.writestr('output/Alicante_REAL_OSM_PNOA.glb',b'glTF'+b'SOURCE'+b'0'*65000)
   z.writestr('output/QA_source_report.json',json.dumps({
      'private_avatar_included':False,'facades_photogrammetric':False,
      'coastal_and_vegetation_visual_objects':{
        'mapped_tree_nodes':164,'rounded_tree_canopy_lobes':492,
        'shrub_clusters_within_osm_polygon':65
      }
   }))
   z.writestr('output/QA_independent_provenance.json','{"QA":"SOURCE_ONLY"}')
  return old,runtime,geo
 def test_g19_launcher_flag_and_all_original_archived_assets_survive(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);old,runtime,geo=self.setup_sources(root)
   output=root/'fixed-v6-local.zip'
   qa=mod.build_private_local_checkpoint(old,runtime,geo,output)
   self.assertTrue(qa['actual_loader_flag_before_game_js'])
   self.assertEqual(qa['private_source_GLBs_verified'],71)
   self.assertEqual(qa['G13_signed_2m_grid_count'],12)
   self.assertFalse(qa['independent_3d_browser_validation_with_all_76_private_glbs'])
   with ZipFile(output) as z:
    page=z.read('index.html').decode()
    self.assertIn(mod.FLAG,page)
    self.assertEqual(page.count(mod.FLAG),1)
    self.assertLess(page.index(mod.FLAG),page.index(mod.SCRIPT))
    self.assertEqual(z.read('assets/conflictometro_public_verified.json'),
                     b'{"original":"never overwrite"}')
    self.assertEqual(z.read('assets/alicante.glb')[:4],b'glTF')
    self.assertIn('G19',z.read('LEER_NEUROCITY_NPL3D_V6.txt').decode())
 def test_bad_existing_asset_is_not_silently_copied_to_new_zip(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);old,runtime,geo=self.setup_sources(root,bad_original=True)
   output=root/'should_not_exist.zip'
   with self.assertRaisesRegex(ValueError,'checksum changed'):
    mod.build_private_local_checkpoint(old,runtime,geo,output)
   self.assertFalse(output.exists())
 def test_bad_public_flag_or_missing_runtime_is_rejected(self):
  self.assertEqual(mod.make_public_entrypoint(
     ('<html>'+mod.FLAG+mod.SCRIPT+'</html>').encode()).decode().count(mod.FLAG),1)
  with self.assertRaises(ValueError):mod.make_public_entrypoint(b'<html></html>')
if __name__=='__main__':unittest.main()
