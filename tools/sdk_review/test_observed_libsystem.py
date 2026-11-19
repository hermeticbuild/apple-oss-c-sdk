from argparse import Namespace
from collections import defaultdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.libsystem.emit import ARCHES, SYSTEM
from .build_observed_libsystem import build, export_kind, match_components
from .probe_runtime_providers import add_linker_demands, match_export


class ObservedBindings(unittest.TestCase):
    def test_intel_math_resolver_is_a_callable_export(self):
        hit = match_export("libsystem_m", "___sinpif",
                           "0x00004000 ___sinpif [dynamic-resolver=0x00004100]")
        self.assertEqual(hit["role"], "definition")
        self.assertEqual(export_kind("function", hit["attributes"]), "text.global")
        self.assertIsNone(export_kind("data", hit["attributes"]))
        self.assertIsNone(export_kind("function", ["unknown-attribute"]))

    def test_forwarded_export_retains_its_target(self):
        hit = match_export("libParent", "_func", "[re-export] _func (from libChild)")
        self.assertEqual(hit, {"image": "libParent", "role": "forwarder", "detail": "(from libChild)"})

    def test_component_slot_does_not_guess_between_two_observed_alternatives(self):
        slot = {"alternatives": ["old", "new"], "required": True}
        edges = ["/usr/lib/system/libold.dylib", "/usr/lib/system/libnew.dylib"]
        with self.assertRaisesRegex(ValueError, "separate review"):
            match_components({"component_slots": [slot]}, edges)

    def test_symbol_sidecar_cannot_certify_a_different_object(self):
        with TemporaryDirectory() as temp:
            evidence = Path(temp)
            (evidence / "dyld-thread-local-helpers-arm64.symbols").write_text(
                "__tlv_bootstrap\ndyld_stub_binder\n")
            (evidence / "dyld-thread-local-helpers-arm64.o").write_bytes(b"different object")
            candidates = defaultdict(set)
            with self.assertRaisesRegex(ValueError, "dyld assembly object digest mismatch for arm64"):
                add_linker_demands(candidates, evidence, "arm64")
            self.assertEqual(candidates, {})

    def test_output_deployment_floor_must_agree_with_each_scan(self):
        with TemporaryDirectory() as temp:
            work = Path(temp)
            graph = work / "graph.json"
            graph.write_text(json.dumps({"umbrella": {"install_path": SYSTEM}, "component_slots": []}))
            for arch in ARCHES:
                observations = work / arch
                observations.mkdir()
                (observations / "capture.json").write_text(json.dumps({
                    "identity": {"name": SYSTEM, "cur-vers": "1.0", "compat-vers": "1.0"},
                    "observed_arch": arch, "image_uuid": "fixture", "reexports": [],
                    "requested_exports": {"_fixture": ["0x1 _fixture"]},
                }))
                (observations / "providers.json").write_text(json.dumps({
                    "client_arch": arch, "observed_arch": arch,
                    "scans": [{"minimum": "11.0", "c_manifest": ["fixture"]}],
                    "images": {SYSTEM: {"receipt": "capture.json", "uuid": "fixture", "reexports": []}},
                    "linker_demands": None,
                    "symbols": [{"symbol": "_fixture", "client_declarations": [["function", "fixture.h"]],
                                 "matches": [{"image": SYSTEM, "role": "definition", "attributes": []}]}],
                }))
            args = Namespace(graph=graph, arm64=work / "arm64", x86_64=work / "x86_64",
                             minimum="10.6", out=work / "out")
            with self.assertRaisesRegex(ValueError, "requested minimum 10.6 disagrees with scan minimum 11.0"):
                build(args)
            self.assertFalse(args.out.exists())
            args.minimum = "11.0.0"
            build(args)
            self.assertTrue((args.out / "usr/lib/libSystem.B.tbd").is_file())
