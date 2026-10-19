import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('photogrammetry_probe',Path(__file__).with_name('photogrammetry_probe.py'))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SfMSafetyTests(unittest.TestCase):
    def feature(self,i,sequence='seq_public'):
        return {'id':f'image_{i}','collection':sequence,'type':'Feature',
                'geometry':{'type':'Point','coordinates':[-0.4832+i*0.00001,38.344]},
                'properties':{'datetime':f'2026-01-01T11:{i:02d}:00Z'},
                'links':[{'rel':'license','href':'https://creativecommons.org/licenses/by-sa/4.0/'}],
                'assets':{'sd':{'href':f'https://panoramax.openstreetmap.fr/api/pictures/img{i}/sd.jpg'}}}
    def test_only_approved_images_chosen_from_one_track(self):
        items=[self.feature(i) for i in range(20)]
        bad=self.feature(44,'private_sequence')
        bad['links']=[{'rel':'license','href':'https://example.net/copyright'}]
        items.append(bad)
        images,meta=mod.choose_sequence({'features':items},photo_limit=8)
        self.assertEqual(len(images),8)
        self.assertEqual(meta['longest_sequence_available'],20)
        self.assertEqual(meta['eligible_sources'],20)
        self.assertEqual(len({i['image_id'] for i in images}),8)
        self.assertEqual([i['image_id'] for i in images],[f'image_{i}' for i in range(6,14)])
        self.assertFalse(any('private' in i['url'] for i in images))
    def test_allowlist_for_photo_only(self):
        for u in ['https://panoramax.openstreetmap.fr/api/pictures/abc/sd.jpg',
                  'https://api.panoramax.xyz/api/pictures/abc/sd.jpg']:
            self.assertTrue(mod.safe_image_url(u))
        for u in ['http://panoramax.openstreetmap.fr/img.jpg',
                  'https://example.com/abc.jpg',
                  'https://api.panoramax.xyz.evil.com/foo.jpg',
                  'https://api.panoramax.xyz/a.png',
                  'https://user:pass@api.panoramax.xyz/photo.jpg']:
            self.assertFalse(mod.safe_image_url(u))
    def test_nonphoto_urls_do_not_qualify(self):
        data={'features':[self.feature(1)]}
        data['features'][0]['assets']['sd']['href']='https://bad.test/a.jpg'
        a,_=mod.choose_sequence(data)
        self.assertEqual(a,[])
    def test_requires_real_camera_overlap_not_catalog_count(self):
        items=[self.feature(1)]
        out,meta=mod.choose_sequence({'features':items})
        self.assertEqual(len(out),1)
        self.assertLess(len(out),8)
        self.assertEqual(meta['longest_sequence_available'],1)

if __name__=='__main__':unittest.main()
