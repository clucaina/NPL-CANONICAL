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

    def test_indexed_triangle_requires_real_in_range_indices(self):
        payload = valid_payload()
        payload["meshes"][0]["primitives"][0]["indices"] = 1
        payload["accessors"].append({
            "type": "SCALAR", "count": 3, "componentType": 5123, "bufferView": 1
        })
        payload["bufferViews"].append({"buffer": 0, "byteOffset": 36, "byteLength": 6})
        payload["buffers"][0]["byteLength"] = 42
        binary = b"\x00" * 36 + struct.pack("<3H", 0, 1, 2) + b"\x00" * 2
        good = inspect_glb(pack(payload, binary))
        self.assertEqual(good["drawable_primitives"], 1)
        self.assertEqual(good["errors"], [])
        bad_binary = b"\x00" * 36 + struct.pack("<3H", 0, 1, 3) + b"\x00" * 2
        bad = inspect_glb(pack(payload, bad_binary))
        self.assertEqual(bad["drawable_primitives"], 0)
        self.assertTrue(bad["errors"])

    def test_malformed_index_accessors_never_count_as_drawable(self):
        cases = {
            "index_id_out_of_range": lambda p: p["meshes"][0]["primitives"][0].update(indices=9),
            "wrong_index_type": lambda p: p["accessors"][1].update(type="VEC3"),
            "float_indices": lambda p: p["accessors"][1].update(componentType=5126),
            "short_index_view": lambda p: p["bufferViews"][1].update(byteLength=4),
            "misaligned_index_offset": lambda p: p["accessors"][1].update(byteOffset=1),
            "external_index_view": lambda p: p["bufferViews"][1].update(buffer=1),
            "sparse_index": lambda p: p["accessors"][1].update(sparse={"count": 1}),
            "non_triangle_index_count": lambda p: p["accessors"][1].update(count=4),
            "boolean_index_count": lambda p: p["accessors"][1].update(count=True),
            "index_view_stride": lambda p: p["bufferViews"][1].update(byteStride=2),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                payload = valid_payload()
                payload["meshes"][0]["primitives"][0]["indices"] = 1
                payload["accessors"].append({
                    "type": "SCALAR", "count": 3, "componentType": 5123, "bufferView": 1
                })
                payload["bufferViews"].append({"buffer": 0, "byteOffset": 36, "byteLength": 6})
                payload["buffers"][0]["byteLength"] = 42
                mutate(payload)
                binary = b"\x00" * 36 + struct.pack("<3H", 0, 1, 2) + b"\x00" * 2
                self.assertEqual(inspect_glb(pack(payload, binary))["drawable_primitives"], 0)

    def test_glb_chunk_order_duplicates_and_trailing_corruption(self):
        valid = pack(valid_payload())
        json_size = struct.unpack_from("<I", valid, 12)[0]
        json_chunk = valid[12:20 + json_size]
        bin_chunk = valid[20 + json_size:]
        unknown_chunk = struct.pack("<I4s", 4, b"XTRA") + b"\x00" * 4

        def from_chunks(chunks):
            body = b"".join(chunks)
            return b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body

        cases = {
            "bin_before_json": [bin_chunk, json_chunk],
            "duplicate_json": [json_chunk, json_chunk, bin_chunk],
            "duplicate_bin": [json_chunk, bin_chunk, bin_chunk],
            "unknown_chunk": [json_chunk, unknown_chunk, bin_chunk],
        }
        for name, chunks in cases.items():
            with self.subTest(name=name):
                outcome = inspect_glb(from_chunks(chunks))
                self.assertEqual(outcome["drawable_primitives"], 0)
                self.assertTrue(outcome["errors"])
        trailing = bytearray(valid + b"\x01")
        struct.pack_into("<I", trailing, 8, len(trailing))
        outcome = inspect_glb(bytes(trailing))
        self.assertEqual(outcome["drawable_primitives"], 0)
        self.assertTrue(outcome["errors"])

    def test_glb_json_root_and_asset_must_be_objects(self):
        for payload in ([], {"asset": []}, {"asset": None}):
            with self.subTest(payload=payload):
                outcome = inspect_glb(pack(payload))
                self.assertEqual(outcome["drawable_primitives"], 0)
                self.assertTrue(outcome["errors"])

    def test_bin_chunk_rejects_four_unaccounted_trailing_bytes(self):
        payload = valid_payload()
        # A GLB BIN chunk may only contain up to 3 padding bytes beyond
        # buffers[0].byteLength. Four zero bytes are not valid padding.
        excess = inspect_glb(pack(payload, b"\x00" * 40))
        self.assertEqual(excess["drawable_primitives"], 0)
        self.assertTrue(any("padding" in error for error in excess["errors"]))
        self.assertEqual(inspect_glb(pack(payload, b"\x00" * 36))["errors"], [])

    def test_bin_padding_must_be_zero_even_within_three_byte_allowance(self):
        payload = valid_payload()
        payload["buffers"][0]["byteLength"] = 37
        valid = inspect_glb(pack(payload, b"\x00" * 40))
        self.assertEqual(valid["drawable_primitives"], 1)
        self.assertEqual(valid["errors"], [])
        corrupted = inspect_glb(pack(payload, b"\x00" * 39 + b"\x01"))
        self.assertEqual(corrupted["drawable_primitives"], 0)
        self.assertTrue(any("padding" in error for error in corrupted["errors"]))

    def test_bad_file_and_unsupported_version(self):
        self.assertFalse(inspect_glb(b"bad")["header_valid"])
        b=bytearray(pack(valid_payload()))
        b[4:8]=struct.pack("<I",1)
        self.assertFalse(inspect_glb(bytes(b))["header_valid"])
if __name__=="__main__":unittest.main()
