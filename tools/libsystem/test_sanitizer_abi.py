"""Check the pinned sanitizer recipe through the offline component builder."""

from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from .emit import ARCHES, SYSTEM, resolve
from .sanitizer_abi import install


KERNEL = "/usr/lib/system/libsystem_kernel.dylib"
MALLOC = "/usr/lib/system/libsystem_malloc.dylib"
DYLD = "/usr/lib/system/libdyld.dylib"
SDK = "macosx26.5"
SOURCE_ENV = "LIBSYSTEM_TEST_SANITIZER_SOURCES"
LLVM_ENV = "LIBSYSTEM_TEST_LLVM"


def image(name, *edges):
    return {
        "install_name": name,
        "current_version": "1",
        "compatibility_version": "1",
        "slices": {
            arch: {"exports": {}, "reexports": list(edges)}
            for arch in ARCHES
        },
    }


class ScopeTests(unittest.TestCase):
    def test_reject_unqualified_release_and_minimum(self):
        with self.assertRaisesRegex(ValueError, "only to macosx26.5"):
            install("macosx26.4", {}, None, None, [], {}, minimum="11.0")
        with self.assertRaisesRegex(ValueError, "deployment minima"):
            install(SDK, {}, None, None, [], {}, minimum="10.15")

    def test_reject_changed_compiler_rt_input(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "lib/sanitizer_common/sanitizer_internal_defs.h"
            source.parent.mkdir(parents=True)
            source.write_text("#define SANITIZER_WEAK_ATTRIBUTE\n")
            roots = {name: root for name in ("compiler-rt", "dyld", "libmalloc", "xnu")}
            inventories = {arch: [] for arch in ARCHES}
            with self.assertRaisesRegex(ValueError, "sanitizer_internal_defs.h: expected"):
                install(SDK, roots, None, root / "objects", [], inventories, minimum="11.0")
            self.assertEqual(inventories, {"arm64": [], "x86_64": []})


@unittest.skipUnless(os.getenv(SOURCE_ENV) and os.getenv(LLVM_ENV), "requires pinned sources and official LLVM")
class QualifiedTests(unittest.TestCase):
    def setUp(self):
        self.roots = {name: Path(path) for name, path in json.loads(os.environ[SOURCE_ENV]).items()}
        self.llvm = Path(os.environ[LLVM_ENV]).resolve()
        self.images = [image(SYSTEM, KERNEL, MALLOC, DYLD), image(KERNEL), image(MALLOC), image(DYLD)]
        self.inventories = {arch: [] for arch in ARCHES}

    def test_both_slices_resolve_functions_and_data_to_deployed_owners(self):
        with TemporaryDirectory() as temp:
            receipt = install(SDK, self.roots, self.llvm, Path(temp) / "objects",
                              self.images, self.inventories, minimum="11.0")
            _, providers = resolve(self.images, self.inventories, "11.0")

        expected = {
            "___fork": (KERNEL, "text.global", "function", True),
            "___mmap": (KERNEL, "text.global", "function", True),
            "___munmap": (KERNEL, "text.global", "function", True),
            "__dyld_get_image_slide": (DYLD, "text.global", "function", False),
            "__dyld_get_shared_cache_range": (DYLD, "text.global", "function", False),
            "__dyld_get_shared_cache_uuid": (DYLD, "text.global", "function", False),
            "_dyld_shared_cache_iterate_text": (DYLD, "text.global", "function", False),
            "_malloc_num_zones": (MALLOC, "data.global", "data", False),
            "_malloc_zones": (MALLOC, "data.global", "data", False),
        }
        for arch in ARCHES:
            with self.subTest(arch=arch):
                self.assertEqual(
                    {row["symbol"]: (row["provider"], row["kind"]) for row in providers if row["arch"] == arch},
                    {name: (owner, kind) for name, (owner, kind, _, _) in expected.items()},
                )
                self.assertEqual(
                    receipt["client"]["slices"][arch]["imports"],
                    {name: {"kind": kind, "weak_import": weak} for name, (_, _, kind, weak) in expected.items()},
                )

    def test_reject_existing_wrong_export_kind_without_mutating_any_image(self):
        self.images[2]["slices"]["x86_64"]["exports"]["_malloc_num_zones"] = "text.global"
        original = deepcopy(self.images)
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "x86_64: conflicting sanitizer ABI export _malloc_num_zones"):
                install(SDK, self.roots, self.llvm, Path(temp) / "objects",
                        self.images, self.inventories, minimum="11.0")
        self.assertEqual(self.images, original)
        self.assertEqual(self.inventories, {"arm64": [], "x86_64": []})
