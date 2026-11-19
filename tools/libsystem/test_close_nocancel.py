"""Check the non-cancelable close import and its kernel provider."""

from copy import deepcopy
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from .close_nocancel import ALIAS, KERNEL, install
from .emit import ARCHES, SYSTEM, resolve
from .scan import run


CLIENT = Path(__file__).parent / "fixtures/close_nocancel.S"


class CloseNocancelTests(unittest.TestCase):
    def setUp(self):
        self.images = [
            {"install_name": owner, "current_version": "1", "compatibility_version": "1",
             "slices": {arch: {"exports": {}, "reexports": edges} for arch in ARCHES}}
            for owner, edges in [(SYSTEM, [KERNEL]), (KERNEL, [])]
        ]
        self.inventories = {arch: [] for arch in ARCHES}

    def test_rejects_conflicting_definition_before_adding_either_slice(self):
        for owner, kind in [(SYSTEM, "text.global"), (KERNEL, "text.weak")]:
            with self.subTest(owner=owner):
                images = deepcopy(self.images)
                image, = (image for image in images if image["install_name"] == owner)
                image["slices"]["x86_64"]["exports"][ALIAS] = kind
                before = deepcopy(images)
                with self.assertRaisesRegex(ValueError, "x86_64: conflicting definition"):
                    install("macosx26.5", None, None, None, "11.0", None, images, self.inventories)
                self.assertEqual(before, images)
                self.assertEqual(self.inventories, {arch: [] for arch in ARCHES})

    @unittest.skipUnless(all(os.getenv(key) for key in ("LLVM", "LIBSYSTEM_TEST_XNU", "LIBSYSTEM_TEST_C_INSTALL")),
                         "requires pinned LLVM, XNU and the qualified C installation")
    def test_client_relocation_resolves_to_only_the_qualified_kernel_alias(self):
        llvm = Path(os.environ["LLVM"]).resolve()
        source = Path(os.environ["LIBSYSTEM_TEST_XNU"]).resolve()
        c_install = Path(os.environ["LIBSYSTEM_TEST_C_INSTALL"]).resolve()
        with TemporaryDirectory() as temp:
            work = Path(temp)
            install("macosx26.5", source, llvm, c_install, "11.0", work, self.images, self.inventories)
            _, providers = resolve(self.images, self.inventories, "11.0")
            for arch in ARCHES:
                obj = work / (arch + "-client.o")
                run(llvm / "bin/clang", ["--no-default-config", "-target", f"{arch}-apple-macos11",
                                         "-c", CLIENT, "-o", obj], work)
                imports = run(llvm / "bin/llvm-nm", ["-uj", obj], work).splitlines()
                self.assertEqual(imports, [ALIAS])
                self.assertEqual(self.images[1]["slices"][arch]["exports"], {imports[0]: "text.global"})
                self.assertEqual([(row["symbol"], row["provider"]) for row in providers if row["arch"] == arch],
                                 [(imports[0], KERNEL)])

    @unittest.skipUnless(all(os.getenv(key) for key in ("LLVM", "LIBSYSTEM_TEST_XNU", "LIBSYSTEM_TEST_C_INSTALL")),
                         "requires pinned LLVM, XNU and the qualified C installation")
    def test_unlisted_c_header_cannot_shadow_the_pinned_private_header(self):
        llvm = Path(os.environ["LLVM"]).resolve()
        source = Path(os.environ["LIBSYSTEM_TEST_XNU"]).resolve()
        c_install = Path(os.environ["LIBSYSTEM_TEST_C_INSTALL"]).resolve()
        with TemporaryDirectory() as temp:
            work = Path(temp)
            copied = work / "c-install"
            shutil.copytree(c_install, copied)
            clean = install("macosx26.5", source, llvm, copied, "11.0", work / "clean",
                            self.images, self.inventories)
            shadow = copied / "usr/include/mach/i386/syscall_sw.h"
            self.assertFalse(shadow.exists())
            shadow.parent.mkdir(parents=True, exist_ok=True)
            shadow.write_text('#error "picked up an unlisted C header"\n')
            with_shadow = install("macosx26.5", source, llvm, copied, "11.0", work / "shadow",
                                  self.images, self.inventories)
            self.assertEqual(with_shadow["targets"], clean["targets"])

            # The installed syscall.h is still on disk. Removing its receipt
            # must leave the assembler with no way to include it.
            manifest = copied / "header-manifest.tsv"
            lines = manifest.read_text().splitlines(keepends=True)
            manifest.write_text("".join(line for line in lines if not line.startswith("usr/include/sys/syscall.h\t")))
            with self.assertRaisesRegex(ValueError, "'sys/syscall.h' file not found"):
                install("macosx26.5", source, llvm, copied, "11.0", work / "omitted",
                        self.images, self.inventories)
