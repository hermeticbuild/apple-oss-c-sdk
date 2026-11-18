"""Exercise the shell merge against real staged files and provenance records."""

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = "usr/include/example.h"
RULE = "recipes/libm/Makefile"
SOURCE = "sources/Libm/Source/math.h"


class MergeTest(unittest.TestCase):
    def stage(self, root: Path, owner: str, path: str = HEADER) -> Path:
        target = root / owner / "dst" / HEADER
        target.parent.mkdir(parents=True)
        target.write_bytes(b"example\n")
        target.chmod(0o444)
        receipt = root / owner / "records"
        receipt.write_text("\t".join((path, owner, SOURCE, RULE, "copy", RULE, SOURCE)) + "\n")
        return receipt

    def merge(self, output: Path, *receipts: Path):
        return subprocess.run(
            ["/bin/sh", "recipes/merge.sh", str(output), *map(str, receipts)],
            cwd=ROOT, capture_output=True, text=True,
        )

    def test_install_records_the_header_and_its_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "out"
            result = self.merge(output, self.stage(root, "Libm"))
            self.assertEqual(result.returncode, 0, result.stderr)
            data = (output / HEADER).read_bytes()
            self.assertEqual(data, b"example\n")
            self.assertEqual((output / HEADER).stat().st_mode & 0o777, 0o644)
            provenance = json.loads((output / "header-provenance.json").read_text())
            self.assertEqual(provenance["files"][HEADER]["sha256"], hashlib.sha256(data).hexdigest())

    def test_duplicate_paths_fail_before_any_output_is_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "out"
            result = self.merge(output, self.stage(root, "Libm"), self.stage(root, "other"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("multiple owners", result.stderr)
            self.assertFalse(output.exists())

    def test_paths_cannot_escape_the_public_include_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "out"
            result = self.merge(output, self.stage(root, "Libm", "usr/include/../x.h"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid header record", result.stderr)
            self.assertFalse(output.exists())
