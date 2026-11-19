"""Check the published CommonCrypto exports through the offline component builder."""

from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.sdk_review.libsystem_tbd import parse_v5

from .commoncrypto import IMAGE, install
from .emit import ARCHES, SYSTEM, resolve


SDK = "macosx26.5"
SOURCE_ENV = "LIBSYSTEM_TEST_COMMONCRYPTO"


def image(name, *edges):
    return {
        "install_name": name,
        "current_version": "1",
        "compatibility_version": "1",
        "slices": {arch: {"exports": {}, "reexports": list(edges)} for arch in ARCHES},
    }


class ScopeTests(unittest.TestCase):
    def test_rejects_unqualified_release_and_minimum(self):
        with self.assertRaisesRegex(ValueError, "only to macosx26.5"):
            install("macosx26.4", None, [], {}, minimum="11.0")
        with self.assertRaisesRegex(ValueError, "deployment minima"):
            install(SDK, None, [], {}, minimum="10.15")

    def test_rejects_changed_build_project(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            project = root / "CommonCrypto.xcodeproj/project.pbxproj"
            project.parent.mkdir()
            project.write_text("changed export selection")
            with self.assertRaisesRegex(ValueError, "project.pbxproj: expected"):
                install(SDK, root, [], {arch: [] for arch in ARCHES}, minimum="11.0")


@unittest.skipUnless(os.getenv(SOURCE_ENV), "requires pinned Apple CommonCrypto source")
class QualifiedTests(unittest.TestCase):
    def setUp(self):
        self.source = Path(os.environ[SOURCE_ENV])
        self.images = [image(SYSTEM, IMAGE), image(IMAGE)]
        self.inventories = {arch: [] for arch in ARCHES}

    def test_published_functions_and_data_resolve_to_commoncrypto(self):
        receipt = install(SDK, self.source, self.images, self.inventories, minimum="11.0")
        document, providers = resolve(self.images, self.inventories, "11.0")
        library = parse_v5(json.dumps(document)).libraries[IMAGE]
        expected_data = {"_CCrfc3394_iv", "_CCrfc3394_ivLen", "_kCCRandomDefault", "_kCCRandomDevRandom"}
        self.assertEqual(receipt["provider"], IMAGE)
        self.assertEqual(receipt["exports"]["_MD5Final"], "text.global")
        self.assertEqual(receipt["exports"]["_CCCryptorReset_binary_compatibility"], "text.global")
        self.assertEqual(len(providers), 490)
        for arch in ARCHES:
            with self.subTest(arch=arch):
                exports = library[f"{arch}-macos"].symbols
                self.assertEqual(len(exports), 245)
                self.assertTrue(all(entry["role"] == "export" and not entry["weak"] and not entry["thread_local"]
                                    for entry in exports.values()))
                self.assertEqual({name for (_, name), entry in exports.items() if entry["segment"] == "data"},
                                 expected_data)
                self.assertEqual({row["provider"] for row in providers if row["arch"] == arch}, {IMAGE})

    def test_rejects_conflicting_kind_before_installing_any_export(self):
        self.images[1]["slices"]["x86_64"]["exports"]["_kCCRandomDefault"] = "text.global"
        original = deepcopy(self.images)
        with self.assertRaisesRegex(ValueError, "x86_64: conflicting CommonCrypto definition for _kCCRandomDefault"):
            install(SDK, self.source, self.images, self.inventories, minimum="11.0")
        self.assertEqual(self.images, original)
        self.assertEqual(self.inventories, {"arm64": [], "x86_64": []})
