"""Integration tests for the scanner and official LLVM's two Mach-O clients."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools.header_manifest import COLUMNS


FIXTURES = Path(__file__).with_name("fixtures") / "scan"
LLVM = os.getenv("LIBSYSTEM_TEST_LLVM")


def install_fixtures(root):
    include = root / "usr/include"
    include.mkdir(parents=True)
    rows = [COLUMNS]
    for path in sorted(FIXTURES.glob("*.h")):
        shutil.copyfile(path, include / path.name)
        origin = f"fixtures/scan/{path.name}"
        rows.append([f"usr/include/{path.name}", hashlib.sha256(path.read_bytes()).hexdigest(),
                     "fixture", origin, "fixture install", "copy", origin])
    (root / "header-manifest.tsv").write_text("".join("\t".join(row) + "\n" for row in rows))


@unittest.skipUnless(LLVM, "set LIBSYSTEM_TEST_LLVM to the verified official bundle root")
class ScanTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.root = self.work / "original" / "sysroot"
        install_fixtures(self.root)

    def scan(self, root, arch, out, *extra):
        return subprocess.run([
            sys.executable, "-m", "tools.libsystem.scan", "--llvm", LLVM, "--c-install", root,
            "--arch", arch, "--minimum", "11.0", "--header", "surface.h",
            "--header", "zero.h", "--out", out, *extra,
        ], text=True, capture_output=True)

    def test_client_relocations_and_eligibility_on_both_architectures(self):
        for arch, tls_relocations in (
            ("arm64", {"ARM64_RELOC_TLVP_LOAD_PAGEOFF12", "ARM64_RELOC_TLVP_LOAD_PAGE21"}),
            ("x86_64", {"X86_64_RELOC_TLV"}),
        ):
            with self.subTest(arch=arch):
                out = self.work / f"{arch}.json"
                objects = self.work / arch
                result = self.scan(self.root, arch, out, "--objects", objects)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(out.read_text())
                self.assertEqual(report["unresolved"], [])
                self.assertEqual([row["path"] for row in report["headers"]],
                                 ["usr/include/surface.h", "usr/include/zero.h"])
                imports = {row["symbol"]: row for row in report["imports"]}
                self.assertEqual({symbol: (row["kind"], row["weak_import"])
                                  for symbol, row in imports.items()}, {
                    "_scan_data": ("data", False),
                    "_scan_function": ("function", False),
                    "_scan_later": ("function", True),
                    "_scan_macho_alias": ("function", False),
                    "_scan_profile": ("function", False),
                    "_scan_tls": ("tls", False),
                    "_scan_transitive": ("function", False),
                    "_scan_weak": ("function", True),
                })
                self.assertEqual({row["type"] for row in imports["_scan_tls"]["relocations"]},
                                 tls_relocations)
                self.assertEqual(imports["_scan_transitive"]["header"], "usr/include/details.h")
                self.assertEqual(imports["_scan_transitive"]["public_root"], "usr/include/surface.h")
                self.assertEqual(
                    [row["header"] for row in report["imports"] if row["symbol"] == "_scan_function"],
                    ["usr/include/details.h", "usr/include/surface.h"])
                self.assertEqual(
                    {row["c_name"]: row["eligibility"] for row in report["declarations"]
                     if row["eligibility"] != "installapi-export"},
                    {"scan_static_inline": "internal-linkage",
                     "scan_c_inline": "not-exported-by-installapi",
                     "scan_hidden": "non-default-visibility",
                     "scan_unavailable": "unavailable", "scan_typedef": "type-declaration"})
                for row in report["imports"]:
                    obj = objects / row["object"]
                    self.assertEqual(hashlib.sha256(obj.read_bytes()).hexdigest(),
                                     row["object_sha256"])

    def test_darwin_profile_and_independent_roots_are_reproducible(self):
        moved = self.work / "moved installation"
        shutil.copytree(self.root, moved)
        first = self.work / "first.json"
        second = self.work / "second.json"
        result = self.scan(self.root, "x86_64", first, "--profile", "darwin")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.scan(moved, "x86_64", second, "--profile", "darwin")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        symbols = {row["symbol"] for row in json.loads(first.read_text())["imports"]}
        self.assertIn("_scan_profile$DARWIN_EXTSN", symbols)
        self.assertNotIn("_scan_profile", symbols)

    def test_transitive_digest_mismatch_prevents_inventory(self):
        path = self.root / "usr/include/details.h"
        path.write_text(path.read_text() + "\n")
        out = self.work / "scan.json"
        result = self.scan(self.root, "arm64", out)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("installed header differs from manifest: usr/include/details.h", result.stderr)
        self.assertFalse(out.exists())

    def test_macro_replacement_cannot_be_mistaken_for_the_ast_symbol(self):
        out = self.work / "scan.json"
        result = self.scan(self.root, "arm64", out, "--header", "macro-shadow.h")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(out.read_text())
        self.assertNotIn("_scan_shadowed", {row["symbol"] for row in report["imports"]})
        self.assertEqual([row["symbol"] for row in report["unresolved"]], ["_scan_shadowed"])
        self.assertIn("_scan_replacement", report["unresolved"][0]["reason"])

    def test_unguarded_transitive_declarations_cannot_change_the_context(self):
        path = self.root / "usr/include/details.h"
        original = hashlib.sha256(path.read_bytes()).hexdigest()
        path.write_text("extern int scan_unguarded(void);\n")
        manifest = self.root / "header-manifest.tsv"
        manifest.write_text(manifest.read_text().replace(
            original, hashlib.sha256(path.read_bytes()).hexdigest()))
        out = self.work / "scan.json"
        result = self.scan(self.root, "arm64", out)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("registering transitive headers changes the declaration inventory",
                      result.stderr)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
