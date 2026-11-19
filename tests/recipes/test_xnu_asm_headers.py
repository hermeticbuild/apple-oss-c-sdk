"""Exercise the public Mach asm.h install rule with synthetic XNU inputs."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class XnuAsmHeadersTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)
        self.sources = self.work / "sources"
        self.xnu = self.sources / "xnu"
        self.staged = self.work / "stage"

    def write(self, path, contents):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)

    def component(self, arch, vpath, source):
        makefile = self.xnu / "osfmk/mach" / arch / "Makefile"
        self.write(makefile, f"""VPATH := $(VPATH):$(SOURCE)/../../{vpath}
INSTALL_MD_GEN_LIST = \\
  asm.h
INSTALL_MD_DIR = mach/{arch}
""")
        self.write(self.xnu / "osfmk" / vpath / "asm.h", source)
        return makefile

    def run_stage(self, stage):
        return subprocess.run(
            [sys.executable, "-m", "recipes.xnu.asm_headers", stage], cwd=ROOT,
            env={**os.environ, "SOURCE_ROOT": str(self.sources)}, capture_output=True, text=True,
        )

    def test_vpath_inputs_are_filtered_and_recorded_for_both_public_headers(self):
        self.component("arm64", "fixture-arm64", """/* Public header comment */
#if XNU_PLATFORM_MacOSX
#define PUBLIC 1
#endif
#ifdef XNU_KERNEL_PRIVATE
#include <private_kernel_header.h>
#endif
#if defined(__arm64__)
#define TARGET_ASM 1
#endif
""")
        self.component("i386", "fixture-i386", "#define INTEL_ASM 1\n")
        # A path guessed from the component's architecture would be wrong.
        self.write(self.xnu / "osfmk/arm64/asm.h", "#error unexpected source\n")

        result = self.run_stage(self.staged)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.staged / "dst/usr/include/mach/arm64/asm.h").read_text(),
            """/* Public header comment */
#define PUBLIC 1
#if defined(__arm64__)
#define TARGET_ASM 1
#endif
""",
        )
        self.assertEqual((self.staged / "dst/usr/include/mach/i386/asm.h").read_text(),
                         "#define INTEL_ASM 1\n")
        fields = [row.split("\t") for row in result.stdout.splitlines()]
        self.assertEqual([row[0] for row in fields],
                         ["usr/include/mach/arm64/asm.h", "usr/include/mach/i386/asm.h"])
        self.assertIn("sources/xnu/osfmk/fixture-arm64/asm.h", fields[0][5:])
        self.assertIn("sources/xnu/osfmk/mach/arm64/Makefile", fields[0][5:])
        self.assertIn("sources/xnu/makedefs/MakeInc.rule", fields[0][5:])
        self.assertEqual(fields[0][3], "osfmk/mach/arm64/Makefile:INSTALL_MD_GEN_LIST")

        repeat = self.run_stage(self.work / "repeat")
        self.assertEqual(repeat.returncode, 0, repeat.stderr)
        self.assertEqual(repeat.stdout, result.stdout)

    def test_comment_only_public_output_is_omitted(self):
        self.component("arm64", "arm64", "/* Just a comment. */\n")
        self.component("i386", "i386", "#define INTEL_ASM 1\n")
        result = self.run_stage(self.staged)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("usr/include/mach/arm64/asm.h", result.stdout)
        self.assertFalse((self.staged / "dst/usr/include/mach/arm64/asm.h").exists())
        self.assertIn("usr/include/mach/i386/asm.h", result.stdout)

    def test_source_directory_precedes_the_appended_vpath(self):
        self.component("arm64", "arm64", "#define ARM_ASM 1\n")
        self.component("i386", "i386", "#define INTEL_ASM 1\n")
        self.write(self.xnu / "osfmk/mach/arm64/asm.h", "#define ARM_ASM 2\n")

        result = self.run_stage(self.staged)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.staged / "dst/usr/include/mach/arm64/asm.h").read_text(),
                         "#define ARM_ASM 2\n")
        self.assertIn("derived:sources/xnu/osfmk/mach/arm64/asm.h", result.stdout)

    def test_withdrawn_public_rule_fails_even_if_source_exists(self):
        makefile = self.component("arm64", "arm64", "#define ARM_ASM 1\n")
        makefile.write_text(makefile.read_text().replace("  asm.h", "  other.h"))
        result = self.run_stage(self.staged)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("asm.h missing from INSTALL_MD_GEN_LIST", result.stderr)
        self.assertFalse((self.staged / "dst/usr/include/mach/arm64/asm.h").exists())


if __name__ == "__main__":
    unittest.main()
