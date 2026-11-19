"""End-to-end test of the offline interface tools on an authored two-image fixture."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from tools.libsystem.emit import ARCHES

FIXTURE = Path(__file__).parent / "fixtures/interface"
CLIENT = FIXTURE / "link.c"


@unittest.skipUnless(os.environ.get("LLVM"), "set LLVM to the official release directory")
class InterfaceTest(unittest.TestCase):
    def setUp(self):
        work = TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name)
        self.llvm = Path(os.environ["LLVM"]).resolve()
        self.inputs = self.work / "inputs"
        shutil.copytree(FIXTURE, self.inputs)

    def run_cli(self, module, *args, expect=0):
        run = subprocess.run([sys.executable, "-m", module, *args], text=True, capture_output=True)
        self.assertEqual(run.returncode, expect, run.stderr)
        return run

    def build(self, destination, expect=0):
        return self.run_cli("tools.libsystem", "build", "--lock", self.inputs / "release.json",
                            "--c-install", self.inputs, "--llvm", self.llvm, "--out", destination, expect=expect)

    def change_provider(self, rename):
        lock = json.loads((self.inputs / "release.json").read_text())
        for name in lock["sources"]:
            path = self.inputs / name
            data = json.loads(path.read_text())
            for part in data["slices"].values():
                if rename:
                    data["install_name"] = data["install_name"].replace("/system/", "/")
                    part["reexports"] = [s.replace("/system/", "/") for s in part["reexports"]]
                else:
                    part["exports"].pop("_example_call", None)
            path.write_text(json.dumps(data))
            lock["sources"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        (self.inputs / "release.json").write_text(json.dumps(lock))

    def test_clean_build_and_bindings(self):
        good = self.work / "good"
        repeat = self.work / "second"
        self.build(good)
        self.build(repeat)
        self.assertEqual(sorted(p.relative_to(good) for p in good.rglob("*")),
                         sorted(p.relative_to(repeat) for p in repeat.rglob("*")))
        for path in good.rglob("*"):
            other = repeat / path.relative_to(good)
            if path.is_symlink():
                self.assertEqual(path.readlink(), other.readlink())
            elif path.is_file():
                self.assertEqual(path.read_bytes(), other.read_bytes(), path.name)
        reference = self.work / "reference/usr/lib"
        reference.mkdir(parents=True)
        shutil.copyfile(self.inputs / "reference.tbd", reference / "libSystem.tbd")
        wrong = self.work / "wrong-provider"
        self.change_provider(rename=True)
        self.build(wrong)
        for arch in ARCHES:
            obj = self.work / (arch + ".o")
            subprocess.run([self.llvm / "bin/clang", "-target", arch + "-apple-macos11",
                            "-nostdinc", "-isystem", self.inputs / "usr/include",
                            "-c", CLIENT, "-o", obj], check=True)
            for candidate, expected in ((good, 0), (wrong, 1)):
                report = self.work / "links.json"
                self.run_cli("tools.sdk_review.verify_libsystem_links", "--llvm", self.llvm,
                             "--reference", reference.parents[1], "--candidate", candidate,
                             "--arch", arch, "--minimum", "11", "--sdk-version", "26.5",
                             "--object", obj, "--out", report, expect=expected)
                data = json.loads(report.read_text())
                self.assertEqual(data["pass"], candidate == good)
                for side in ("candidate", "reference"):
                    self.assertIn("imports", data[side]["result"])  # both linked successfully
                self.assertTrue(any("_example_call (from libSystem)" in line
                                    for line in data["reference"]["result"]["imports"]))

    def test_missing_provider_cannot_install(self):
        self.change_provider(rename=False)
        destination = self.work / "incomplete"
        result = self.build(destination, expect=1)
        self.assertIn("missing provider for _example_call", result.stderr)
        self.assertFalse(destination.exists())
