import json
import struct
import unittest
from glb_structure import inspect_glb

def pack(payload,binary=b"\x00"*36):
    source=json.dumps(payload,separators=(",",":")).encode("utf-8")
    source+=b" " * ((-len(source))%4)
    data=b"glTF"+struct.pack("<II",2,20+len(source)+8+len(binary))
    data+=struct.pack("<I4s",len(source),b"JSON")+source
    data+=struct.pack("<I4s",len(binary),b"BIN\x00")+binary
    return data

def valid_payload():
    return {"asset":{"version":"2.0"},"meshes":[{"primitives":[{"attributes":{"POSITION":0}}]}],
            "accessors":[{"type":"VEC3","count":3,"componentType":5126,"bufferView":0}],
            "bufferViews":[{"buffer":0,"byteLength":36}],
            "buffers":[{"byteLength":36}]}

class GLBQuality(unittest.TestCase):
    def test_drawable_geometry_is_distinct_from_syntactically_valid_header(self):
        real=inspect_glb(pack(valid_payload()))
        self.assertEqual(real["drawable_primitives"],1)
        self.assertEqual(real["position_vertices"],3)
        self.assertEqual(real["errors"],[])
        fake=valid_payload()
        fake["meshes"][0]["primitives"]=[]
        result=inspect_glb(pack(fake))
        self.assertEqual(result["meshes"],1)
        self.assertEqual(result["drawable_primitives"],0)
        self.assertTrue(result["errors"])
    def test_missing_bin_chunk_or_wrong_length_fails(self):
        b=pack(valid_payload())
        truncated=inspect_glb(b[:-11])
        self.assertFalse(truncated["header_valid"])
        fake=valid_payload()
        fake["buffers"][0]["byteLength"]=9999
        self.assertTrue(any("exceeds" in e for e in inspect_glb(pack(fake))["errors"]))
    def test_invalid_position_accessor_never_counts(self):
        fake=valid_payload()
        fake["meshes"][0]["primitives"][0]["attributes"]["POSITION"]=777
        self.assertEqual(inspect_glb(pack(fake))["drawable_primitives"],0)
    def test_non_triangle_mode_never_counts_as_building(self):
        fake=valid_payload()
        fake["meshes"][0]["primitives"][0]["mode"]=1
        self.assertEqual(inspect_glb(pack(fake))["drawable_primitives"],0)
    def test_bad_file_and_unsupported_version(self):
        self.assertFalse(inspect_glb(b"bad")["header_valid"])
        b=bytearray(pack(valid_payload()))
        b[4:8]=struct.pack("<I",1)
        self.assertFalse(inspect_glb(bytes(b))["header_valid"])
if __name__=="__main__":unittest.main()
