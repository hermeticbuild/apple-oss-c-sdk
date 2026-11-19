"""Check the Intel-only sanitizer compatibility selection."""

from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from .emit import ARCHES, SYSTEM, resolve
from .sanitizer_inode32 import install
from .test_sanitizer_abi import LLVM_ENV, SOURCE_ENV, image


SDK = "macosx26.5"
LIBC_ENV = "LIBSYSTEM_TEST_INODE32_LIBC"
LIBC = "/usr/lib/system/libsystem_c.dylib"
KERNEL = "/usr/lib/system/libsystem_kernel.dylib"
KIND = "text.global"
LEGACY = {
    LIBC: ("_getmntinfo", "_opendir", "_readdir", "_readdir_r"),
    KERNEL: ("_fstat", "_fstatfs", "_stat", "_statfs"),
}


@unittest.skipUnless(os.getenv(SOURCE_ENV) and os.getenv(LLVM_ENV) and os.getenv(LIBC_ENV), "requires pinned sources and official LLVM")
class Inode32Tests(unittest.TestCase):
    def setUp(self):
        configured = json.loads(os.environ[SOURCE_ENV])
        required = {"xnu", "compiler-rt"}
        if not required <= configured.keys():
            self.skipTest("requires pinned Libc, XNU and compiler-rt sources")
        self.roots = {"libc": Path(os.environ[LIBC_ENV]), **{name: Path(configured[name]) for name in required}}
        self.llvm = Path(os.environ[LLVM_ENV]).resolve()
        self.images = [image(SYSTEM, LIBC, KERNEL), image(LIBC), image(KERNEL)]
        self.inventories = {arch: [] for arch in ARCHES}
        for component in self.images[1:]:
            for arch in ARCHES:
                suffix = "$INODE64" if arch == "x86_64" else ""
                for base in LEGACY[component["install_name"]]:
                    symbol = base + suffix
                    component["slices"][arch]["exports"][symbol] = KIND
                    self.inventories[arch].append({"symbol": symbol, "kind": "function", "header": "fixture.h"})

    def test_only_intel_base_exports_are_new(self):
        _, old = resolve(self.images, self.inventories, "11.0")
        with TemporaryDirectory() as temp:
            install(SDK, self.roots, self.llvm, Path(temp) / "objects",
                    self.images, self.inventories, minimum="11.0")
        _, new = resolve(self.images, self.inventories, "11.0")
        additions = [row for row in new if row not in old]
        self.assertEqual([row for row in new if row not in additions], old)
        self.assertEqual(
            {(row["arch"], row["symbol"], row["provider"], row["kind"]) for row in additions},
            {("x86_64", symbol, provider, KIND) for provider, symbols in LEGACY.items() for symbol in symbols},
        )

    def test_reject_reexport_conflict_before_mutating_components(self):
        self.images[1]["slices"]["x86_64"]["symbol_reexports"] = {"_fstat": {"provider": KERNEL}}
        original = deepcopy((self.images, self.inventories))
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "x86_64: conflicting sanitizer inode ABI export _fstat"):
                install(SDK, self.roots, self.llvm, Path(temp) / "objects",
                        self.images, self.inventories, minimum="11.0")
        self.assertEqual((self.images, self.inventories), original)
