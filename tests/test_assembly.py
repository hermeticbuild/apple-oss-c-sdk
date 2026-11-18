"""Assembler boundaries that protect the standalone installation."""

import tempfile
import unittest
from pathlib import Path

from recipes.assembly import Assembly


class AssemblyTest(unittest.TestCase):
    def test_duplicate_owner_is_an_error_even_for_equal_bytes(self):
        assembly = Assembly({"usr/include/x.h"})
        assembly.add("Libc", "usr/include/x.h", b"x", "source-a", "rule-a",
                     inputs=("sources/Libm/Source/math.h",))
        with self.assertRaisesRegex(ValueError, "multiple owners"):
            assembly.add("xnu", "usr/include/x.h", b"x", "source-b", "rule-b",
                         inputs=("sources/Libm/Source/math.h",))

    def test_missing_profile_path_is_an_error(self):
        assembly = Assembly({"usr/include/x.h"})
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "profile missing"):
                assembly.write(Path(temporary) / "out", complete=True)


if __name__ == "__main__":
    unittest.main()
