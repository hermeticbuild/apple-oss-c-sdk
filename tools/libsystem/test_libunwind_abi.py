"""Check libunwind export classification with Mach-O object files."""

import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from .libunwind_abi import definitions


@unittest.skipUnless(os.environ.get("LLVM"), "set LLVM to the official release directory")
class LibunwindDefinitionsTest(unittest.TestCase):
    def setUp(self):
        work = TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.tools = Path(os.environ["LLVM"]).resolve() / "bin"

    def assemble(self, source, name="implementation"):
        obj = self.work / f"{name}.o"
        subprocess.run([self.tools / "clang", "--no-default-config",
                        "-target", "arm64-apple-macos11", "-x", "assembler",
                        "-c", "-", "-o", obj], input=source, text=True, check=True)
        return obj

    def test_classifies_cold_function_and_data(self):
        obj = self.assemble("""
            .text
            .globl __Unwind_Resume
            .desc __Unwind_Resume, 0x400
            __Unwind_Resume:
                ret
            .data
            .globl _unw_local_addr_space
            _unw_local_addr_space:
                .quad 0
        """)
        actual = definitions(self.tools / "llvm-nm", [obj],
                             {"__Unwind_Resume", "_unw_local_addr_space"}, self.work)
        self.assertEqual(actual, {
            "__Unwind_Resume": ("text.global", "implementation"),
            "_unw_local_addr_space": ("data.global", "implementation"),
        })

    def test_private_target_does_not_satisfy_a_public_reference(self):
        obj = self.assemble("""
            .text
            .private_extern ___unw_getcontext
            ___unw_getcontext:
                ret
        """)
        with self.assertRaisesRegex(ValueError, "missing libunwind definitions.*___unw_getcontext"):
            definitions(self.tools / "llvm-nm", [obj], {"___unw_getcontext"}, self.work)

    def test_duplicate_definition_is_rejected(self):
        source = """
            .text
            .globl __Unwind_Resume
            __Unwind_Resume:
                ret
        """
        first = self.assemble(source, "first")
        second = self.assemble(source, "second")
        with self.assertRaisesRegex(ValueError, "ambiguous or unsupported libunwind definition"):
            definitions(self.tools / "llvm-nm", [first, second], {"__Unwind_Resume"}, self.work)
