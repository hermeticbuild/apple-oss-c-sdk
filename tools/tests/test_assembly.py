"""Assembler boundaries that protect the standalone installation."""

import unittest

from recipes.assembly import Assembly


class AssemblyTest(unittest.TestCase):
    def test_duplicate_owner_is_an_error_even_for_equal_bytes(self):
        assembly = Assembly()
        assembly.add("Libc", "usr/include/x.h", b"x", "source-a", "rule-a",
                     inputs=("sources/Libm/Source/math.h",))
        with self.assertRaisesRegex(ValueError, "multiple owners"):
            assembly.add("xnu", "usr/include/x.h", b"x", "source-b", "rule-b",
                         inputs=("sources/Libm/Source/math.h",))

    def test_output_stays_in_public_include_tree(self):
        with self.assertRaisesRegex(ValueError, "invalid C header path"):
            Assembly().add("Libc", "usr/include/../../x.h", b"x", "source", "rule")


if __name__ == "__main__":
    unittest.main()
