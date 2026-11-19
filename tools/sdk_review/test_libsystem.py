import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


FIXTURES = Path(__file__).resolve().with_name("libsystem_fixtures")
ROOT = FIXTURES.parents[2]
LLVM = os.environ.get("LIBSYSTEM_TEST_LLVM")


@unittest.skipUnless(LLVM, "set LIBSYSTEM_TEST_LLVM to the verified LLVM bundle")
class LibsystemReviewTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)

    def run_command(self, *args, exit_code=0):
        result = subprocess.run(
            [sys.executable, "-m", "tools.sdk_review.libsystem", *map(str, args)],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, exit_code, result.stdout + result.stderr)
        return result

    def compare(self, reference, candidate, *, exit_code=0):
        return self.run_command(
            "compare-libsystem", "--sdk", "macosx26.5", "--reference", FIXTURES / reference,
            "--candidate", FIXTURES / candidate, "--llvm", LLVM, "--out", self.work / "diff",
            "--check", exit_code=exit_code,
        )

    def read_report(self):
        return json.loads((self.work / "diff/libsystem-diff.json").read_bytes())

    def test_dylib_header_resolves_without_a_system_library_while_getpid_requires_one(self):
        from tools.sdk_review.libsystem_client_coverage import resolves_without_libraries

        tools = Path(LLVM) / "bin"
        for arch in ("arm64", "x86_64"):
            with self.subTest(arch=arch):
                self.assertTrue(resolves_without_libraries(tools, self.work, arch, "11.0", "26.5",
                                                           "__mh_dylib_header"))
                self.assertFalse(resolves_without_libraries(tools, self.work, arch, "11.0", "26.5",
                                                            "_getpid"))

    def test_v4_v5_preserve_mixed_platform_flags_and_child_only_targets(self):
        self.compare("raw-targets.tbd", "raw-targets-v5.tbd")
        report = self.read_report()

        self.assertEqual(report["gaps"], [])
        self.assertFalse(report["comparison_limits"]["symbol_segments"])
        self.assertNotIn("arm64-macos", {row["target"] for row in report["reference"]["slices"]
                                       if row["library"] == "/usr/lib/libSystem.B.dylib"})
        self.assertIn(
            {"library": "/usr/lib/system/libRawTargetFixture.dylib", "reexports": 0,
             "symbols": {"export": 4, "undefined": 1}, "target": "arm64-macos"},
            report["reference"]["slices"],
        )

    def test_compare_backlog_explain_and_close_seeded_gaps(self):
        self.compare("original-provider-v5.tbd", "moved-provider-v5.tbd", exit_code=1)
        report = self.read_report()
        missing = [gap for gap in report["gaps"] if gap["symbol"] == "_missing"]
        self.assertEqual({gap["target"] for gap in missing}, {"arm64-macos", "x86_64-macos"})
        self.assertEqual({gap["kind"] for gap in missing}, {"missing-export"})
        self.assertEqual(report["counts"]["changed-reachable-provider"], 2)

        self.run_command("backlog", "--work", self.work, "--check", exit_code=1)
        backlog = json.loads((self.work / "libsystem-backlog.json").read_bytes())
        self.assertEqual(backlog["counts"], {"open": len(report["gaps"])})

        explained = self.run_command("explain-libsystem", "--work", self.work,
                                     "--symbol", "moved", "--arch", "arm64")
        explanation = json.loads(explained.stdout)
        provider_gap, = [gap for gap in explanation["gaps"]
                         if gap["kind"] == "changed-reachable-provider"]
        self.assertEqual(provider_gap["reference"], ["/usr/lib/system/libProviderFixture.dylib"])
        self.assertEqual(provider_gap["candidate"], ["/usr/lib/libProviderFixture.dylib"])
        self.assertEqual(provider_gap["target"], "arm64-macos")
        self.assertIn("compare-libsystem", explanation["compare_command"])
        self.assertIn("verify_libsystem_links", explanation["paired_link_command_templates"]["arm64"])
        self.assertTrue(Path(explanation["independent_diff"]).is_file())

        explained = self.run_command("explain-libsystem", "--work", self.work,
                                     "--gap", provider_gap["id"])
        self.assertEqual(json.loads(explained.stdout)["gaps"], [provider_gap])

        self.compare("original-provider-v5.tbd", "moved-provider-v5.tbd", exit_code=1)
        self.assertEqual(self.read_report(), report)

        self.compare("original-provider-v5.tbd", "original-provider-v5.tbd")
        self.run_command("backlog", "--work", self.work, "--check")
        self.assertEqual(self.read_report()["gaps"], [])

    def test_catalyst_only_change_is_visible_outside_macos_gate(self):
        fixture = "raw-targets-v5.tbd"
        candidate = json.loads((FIXTURES / fixture).read_text())
        private_slice = candidate["libraries"][0]["exported_symbols"][1]
        self.assertTrue(all(target.endswith("-maccatalyst") for target in private_slice["targets"]))
        private_slice["text"]["weak"].append("_fixtureCatalystOnly")
        path = self.work / "candidate.tbd"
        path.write_text(json.dumps(candidate))
        self.compare(fixture, path, exit_code=1)
        self.run_command("backlog", "--work", self.work, "--check")
        result = json.loads((self.work / "libsystem-backlog.json").read_text())
        self.assertEqual(result["counts"], {"outside-client-platform": 2})

    def test_approved_member_set_reopens_when_a_member_disappears(self):
        self.compare("original-provider-v5.tbd", "moved-provider-v5.tbd", exit_code=1)
        report = self.read_report()
        explained = self.run_command("explain-libsystem", "--work", self.work, "--symbol", "missing")
        explanation = json.loads(explained.stdout)
        ledger = self.work / "decisions.json"
        ledger.write_text(json.dumps({
            "schema": 1,
            "reference_sha256": report["reference"]["sha256"],
            "sdk": report["sdk"],
            "decisions": [{
                "id": "fixture-review",
                "members": [gap["id"] for gap in explanation["gaps"]],
                "member_sha256": explanation["member_sha256"],
                "evidence": "synthetic fixture", "impact": "synthetic fixture",
                "approver": "fixture maintainer", "revisit": "fixture revision",
            }],
        }))

        self.run_command("backlog", "--work", self.work, "--decisions", ledger)
        backlog = json.loads((self.work / "libsystem-backlog.json").read_bytes())
        self.assertEqual(backlog["counts"]["approved"], 2)

        partial = self.work / "partial-v5.tbd"
        candidate = json.loads((FIXTURES / "original-provider-v5.tbd").read_bytes())
        candidate["libraries"][0]["exported_symbols"] = [
            {"text": {"global": ["_moved"]}},
            {"targets": ["arm64-macos"], "text": {"global": ["_missing"]}},
        ]
        partial.write_text(json.dumps(candidate))
        self.compare("original-provider-v5.tbd", partial, exit_code=1)
        self.run_command("backlog", "--work", self.work, "--decisions", ledger, "--check", exit_code=1)
        backlog = json.loads((self.work / "libsystem-backlog.json").read_bytes())
        self.assertEqual(backlog["counts"], {"open": 1})
        self.assertEqual(backlog["stale_decisions"], [
            {"id": "fixture-review", "reason": "one or more decision members disappeared"},
        ])

    def test_rejects_unknown_targets_and_unsupported_linkage_fields(self):
        candidate = json.loads((FIXTURES / "raw-targets-v5.tbd").read_bytes())
        path = self.work / "unsupported.tbd"
        candidate["libraries"][0]["exported_symbols"][0]["targets"] = ["arm64-ios"]
        path.write_text(json.dumps(candidate))
        result = self.compare("raw-targets-v5.tbd", path, exit_code=2)
        self.assertIn("undeclared or empty targets", result.stderr)
        self.assertFalse((self.work / "diff/libsystem-diff.json").exists())

        del candidate["libraries"][0]["exported_symbols"][0]["targets"]
        candidate["libraries"][0]["forwarding_aliases"] = []
        path.write_text(json.dumps(candidate))
        result = self.compare("raw-targets-v5.tbd", path, exit_code=2)
        self.assertIn("unsupported fields ['forwarding_aliases']", result.stderr)

    def test_empty_ledger_reports_a_different_reference_digest(self):
        self.compare("original-provider-v5.tbd", "original-provider-v5.tbd")
        path = self.work / "ledger.json"
        path.write_text(json.dumps({
            "schema": 1, "sdk": "macosx26.5", "reference_sha256": "0" * 64, "decisions": [],
        }))

        result = self.run_command("backlog", "--work", self.work, "--decisions", path,
                                  "--check", exit_code=1)
        backlog = json.loads((self.work / "libsystem-backlog.json").read_bytes())
        self.assertFalse(backlog["decision_baseline_matches"])
        self.assertIn("reference digest differs", result.stderr)

    def test_rejects_unsupported_v4_targets_before_llvm_can_drop_them(self):
        path = self.work / "invalid.tbd"
        fixture = (FIXTURES / "raw-targets.tbd").read_text()
        path.write_text(fixture.replace("arm64-maccatalyst", "arm64-unknown", 1))
        result = self.compare("raw-targets-v5.tbd", path, exit_code=2)
        self.assertIn("unsupported, empty or duplicated TBD v4 targets", result.stderr)
        self.assertFalse((self.work / "diff/libsystem-diff.json").exists())


if __name__ == "__main__":
    unittest.main()
