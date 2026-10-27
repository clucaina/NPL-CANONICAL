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
    def test_position_accessor_must_reference_embedded_bytes(self):
        # A plausible accessor count is not evidence of drawable geometry
        # unless its actual FLOAT VEC3 bytes fit within the embedded BIN.
        cases = {
            "missing_view": lambda p: p["accessors"][0].pop("bufferView"),
            "view_out_of_range": lambda p: p["accessors"][0].update(bufferView=9),
            "view_buffer_external": lambda p: p["bufferViews"][0].update(buffer=1),
            "view_too_short": lambda p: p["bufferViews"][0].update(byteLength=24),
            "view_outside_buffer": lambda p: p["bufferViews"][0].update(byteOffset=16),
            "accessor_offset_outside": lambda p: p["accessors"][0].update(byteOffset=8),
            "invalid_stride": lambda p: p["bufferViews"][0].update(byteStride=8),
            "oversized_stride": lambda p: p["bufferViews"][0].update(byteStride=256),
            "wrong_component_type": lambda p: p["accessors"][0].update(componentType=5123),
            "external_uri": lambda p: p["buffers"][0].update(uri="https://example.invalid/private.bin"),
            "missing_bin": lambda p: p["buffers"][0].update(byteLength=40),
            "boolean_count": lambda p: p["accessors"][0].update(count=True),
            "invalid_attrs": lambda p: p["meshes"][0]["primitives"][0].update(attributes=[]),
            "missing_views": lambda p: p.pop("bufferViews"),
            "malformed_buffer_length": lambda p: p["buffers"][0].update(byteLength="36"),
        }
        for name, change in cases.items():
            with self.subTest(name=name):
                payload = valid_payload()
                change(payload)
                result = inspect_glb(pack(payload))
                self.assertEqual(result["drawable_primitives"], 0)
                self.assertTrue(result["errors"])
        interleaved = valid_payload()
        interleaved["bufferViews"][0].update(byteStride=16, byteLength=44)
        interleaved["buffers"][0]["byteLength"] = 44
        self.assertEqual(inspect_glb(pack(interleaved, b"\x00" * 44))["errors"], [])

    def test_bad_file_and_unsupported_version(self):
        self.assertFalse(inspect_glb(b"bad")["header_valid"])
        b=bytearray(pack(valid_payload()))
        b[4:8]=struct.pack("<I",1)
        self.assertFalse(inspect_glb(bytes(b))["header_valid"])
if __name__=="__main__":unittest.main()
