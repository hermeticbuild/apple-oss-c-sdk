"""Exercise real census inputs, resumable scans and their failure reports."""

import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from tools.libsystem.test_scan import LLVM, install_fixtures


@unittest.skipUnless(LLVM, "set LIBSYSTEM_TEST_LLVM to the verified official bundle root")
class PublicRootScanTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.root = self.temp / "c-install"
        self.census = self.temp / "census.json"
        self.work = self.temp / "scan"
        install_fixtures(self.root)

    def command(self, module, *args):
        return subprocess.run([sys.executable, "-m", module, *args], text=True, capture_output=True)

    def run_census(self):
        result = self.command("tools.qualify_headers.census", "--clang", Path(LLVM) / "bin/clang",
                              "--c-install", self.root, "--out", self.census, "--minimum", "11.0",
                              "--report-only")
        self.assertEqual(result.returncode, 0, result.stderr)

    def run_scan(self, *args):
        return self.command("tools.libsystem.scan_roots", "--llvm", LLVM, "--c-install", self.root,
                            "--census", self.census, "--work", self.work, *args)

    def summary(self):
        return json.loads((self.work / "summary.json").read_text())

    def test_resumes_portably_and_rejects_changed_input(self):
        self.run_census()
        options = ("--header", "surface.h", "--profile", "default")
        first = self.run_scan(*options)
        self.assertEqual(first.returncode, 0, first.stderr)
        summary = self.summary()
        self.assertEqual(summary["status_counts"], {"passed": 2})
        for target in summary["symbols"]:
            self.assertIn({"symbol": "_scan_function", "kind": "function", "weak_import": False},
                          target["imports"])

        checkpoint = self.work / summary["roots"][0]["checkpoint"]
        modified = checkpoint.stat().st_mtime_ns
        again = self.run_scan(*options)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("2 checkpoints reused", again.stdout)
        self.assertEqual(modified, checkpoint.stat().st_mtime_ns)
        self.assertEqual(summary, self.summary())

        self.census.write_text(self.census.read_text() + "\n")
        rejected = self.run_scan(*options)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("input identity changed", rejected.stderr)
        self.assertEqual(summary, self.summary())

    def test_records_census_and_scan_failures_without_losing_other_roots(self):
        include = self.root / "usr/include"
        manifest = self.root / "header-manifest.tsv"
        details = include / "details.h"
        original = hashlib.sha256(details.read_bytes()).hexdigest()
        details.write_text("extern int scan_unguarded(void);\n")
        updated = hashlib.sha256(details.read_bytes()).hexdigest()
        broken = include / "broken.h"
        broken.write_text("#error deliberate census failure\n")
        digest = hashlib.sha256(broken.read_bytes()).hexdigest()
        manifest.write_text(manifest.read_text().replace(original, updated) +
                            f"usr/include/broken.h\t{digest}\tfixture\tbroken.h\tinstall\tcopy\tbroken.h\n")

        self.run_census()
        options = ("--header", "surface.h", "--header", "broken.h", "--header", "zero.h",
                   "--arch", "arm64", "--profile", "darwin")
        first = self.run_scan(*options)
        self.assertEqual(first.returncode, 1, first.stderr)
        summary = self.summary()
        self.assertEqual(summary["status_counts"], {"census-failed": 1, "passed": 1, "scan-failed": 1})
        expected = {"census-failed": "deliberate census failure",
                    "scan-failed": "registering transitive headers changes the declaration inventory"}
        for root in summary["roots"]:
            if root["status"] in expected:
                with gzip.open(self.work / root["checkpoint"], "rt", encoding="utf-8") as stream:
                    record = json.load(stream)["result"]
                self.assertIn(expected[root["status"]], record["diagnostic"])
        self.assertEqual(list(self.work.glob(".root-*")), [])
        resumed = self.run_scan(*options, "--report-only")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertIn("3 checkpoints reused", resumed.stdout)
        self.assertEqual(summary, self.summary())


if __name__ == "__main__":
    unittest.main()
