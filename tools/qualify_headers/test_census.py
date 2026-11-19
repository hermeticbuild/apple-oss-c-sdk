"""A passing umbrella translation unit must reach the installed header under test."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from tools.header_manifest import COLUMNS


@unittest.skipUnless(os.environ.get("LLVM"), "set LLVM to the official release directory")
class CensusTest(unittest.TestCase):
    def test_reachable_and_unreachable_umbrella(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            include = root / "usr/include"
            include.mkdir(parents=True)
            headers = {"leaf.h": "#ifndef VIA_ROOT\n#error use the umbrella\n#endif\n",
                       "umbrella.h": "#define VIA_ROOT\n#include <leaf.h>\n", "empty.h": ""}
            rows = [COLUMNS]
            for name, body in headers.items():
                (include / name).write_text(body)
                rows.append(["usr/include/" + name, hashlib.sha256(body.encode()).hexdigest(),
                             "fixture", name, "fixture", "copy", name])
            (root / "header-manifest.tsv").write_text("".join("\t".join(row) + "\n" for row in rows))
            contexts = root / "contexts.json"
            contexts.write_text(json.dumps({"usr/include/leaf.h": {"arm64": {"root": "umbrella.h"},
                                                                   "x86_64": {"root": "empty.h"}}}))
            report = root / "report.json"
            cmd = [sys.executable, "-m", "tools.qualify_headers.census", "--clang", Path(os.environ["LLVM"]) / "bin/clang",
                   "--c-install", root, "--minimum", "11.0", "--header", "leaf.h", "--contexts", contexts, "--out", report]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            data = json.loads(report.read_text())
            self.assertEqual([r["status"] for r in data["rows"]], ["passed", "header-not-reached"])
