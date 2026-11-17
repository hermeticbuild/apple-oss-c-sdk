"""Exercise the audit's scope and decision boundaries with a synthetic SDK."""

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from audit_sdk_c_headers import audit, closure_paths, path_digest


class SdkHeaderAuditTest(unittest.TestCase):
    def test_inventory_keeps_missing_resource_headers_and_review_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sdk, installation, resource = (root / name for name in
                                           ("sdk", "installation", "resource"))
            sdk.mkdir()
            (sdk / "SDKSettings.json").write_text(json.dumps(
                {"CanonicalName": "macosx26.5", "Version": "26.5"}))
            include = sdk / "usr/include"
            for name in ("base.h", "probe.h", "float.h", "unseen.h",
                         "vendor/api.h", "vendor/old.h", "objc/objc.h", "c++/v1/vector",
                         "foo.modulemap"):
                path = include / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n")
            generated = installation / "usr/include/base.h"
            generated.parent.mkdir(parents=True)
            generated.write_text("\n")
            objc = installation / "usr/include/objc/objc.h"
            objc.parent.mkdir(parents=True)
            objc.write_text("\n")
            extra = installation / "usr/include/extra.h"
            extra.write_text("\n")
            (installation / "header-provenance.json").write_text(json.dumps({
                "schema": 2, "files": {
                    name: {"origin": "sources/Libc/include/" + name,
                           "selection": "SOURCE_TREES",
                           "sha256": hashlib.sha256(b"\n").hexdigest()}
                    for name in ("usr/include/base.h", "usr/include/objc/objc.h",
                                 "usr/include/extra.h")}}))
            compiler = resource / "float.h"
            compiler.parent.mkdir()
            compiler.write_text("#  include_next <float.h>\n")
            framework = sdk / "System/Library/Frameworks/Tcl.framework/Headers/tcl.h"
            framework.parent.mkdir(parents=True)
            framework.write_text("\n")
            (include / "tcl.h").symlink_to(framework)

            known = {"base.h", "probe.h", "float.h", "unseen.h", "objc/objc.h",
                     "c++/v1/vector", "foo.modulemap", "tcl.h", "removed.h",
                     "vendor/old.h"}
            report = audit(sdk, installation, resource, {"probe.h"}, {"float.h"},
                           [{"pattern": "vendor/*", "decision": "omit",
                             "reason": "separate vendor library", "evidence": "reviewed path",
                             "reviewed_sdk": "macosx26.5",
                             "approved_paths_sha256": path_digest(
                                 ["vendor/api.h", "vendor/old.h"])}], known)
            entries = {entry["path"]: entry for entry in report["entries"]}
            self.assertEqual(len(entries), 10)
            self.assertEqual(report["counts"]["installed"], 1)
            self.assertEqual(report["counts"]["missing"], 5)
            self.assertEqual(report["counts"]["decisions"],
                             {"include": 2, "omit": 6, "review": 2})
            self.assertEqual(entries["probe.h"]["decision"], "include")
            self.assertTrue(entries["float.h"]["compiler_uses_include_next"])
            self.assertTrue(entries["float.h"]["probe_lookup_candidate"])
            self.assertEqual(entries["float.h"]["decision"], "review")
            self.assertEqual(entries["vendor/api.h"]["decision"], "omit")
            self.assertEqual(entries["vendor/api.h"]["review_status"], "pending")
            self.assertEqual(entries["vendor/old.h"]["review_status"], "approved")
            self.assertEqual(report["new_paths"], ["vendor/api.h"])
            self.assertEqual(report["removed_paths"], ["removed.h"])
            self.assertEqual(report["missing_required"], ["probe.h"])
            self.assertEqual(entries["base.h"]["review_status"], "pending")
            self.assertEqual(entries["base.h"]["provenance_status"], "verified")
            self.assertEqual(report["counts"]["installed_without_provenance"], 0)
            self.assertEqual(entries["probe.h"]["review_status"], "approved")
            self.assertEqual(entries["tcl.h"]["state"], "excluded")
            self.assertEqual(report["installed_out_of_scope"], ["objc/objc.h"])
            self.assertEqual([entry["path"] for entry in report["installation_only"]],
                             ["extra.h"])
            reached = audit(sdk, installation, resource, {"probe.h"}, set(),
                            [], known, generated_closure={"extra.h"})
            self.assertEqual(reached["installation_only"][0]["review_status"],
                             "approved")
            stale_rule = {"pattern": "vendor/*", "decision": "omit",
                          "reason": "separate vendor library", "evidence": "reviewed path",
                          "reviewed_sdk": "macosx26.5",
                          "approved_paths_sha256": path_digest(["vendor/old.h"])}
            repeated = audit(sdk, installation, resource, {"probe.h"}, set(),
                             [stale_rule], known | {"vendor/api.h"})
            stale_entries = {entry["path"]: entry for entry in repeated["entries"]}
            self.assertEqual(repeated["new_paths"], [])
            self.assertEqual(stale_entries["vendor/api.h"]["review_status"], "pending")
            self.assertEqual(stale_entries["vendor/old.h"]["review_status"], "pending")
            (include / "c++/v1/newheader").write_text("\n")
            stale_scope = {"c++": {"reviewed_sdk": "macosx26.5",
                                   "evidence": "LLVM owns C++ headers",
                                   "approved_paths_sha256": path_digest(["c++/v1/vector"])}}
            repeated = audit(sdk, installation, resource, {"probe.h"}, set(),
                             [stale_rule], known | {"vendor/api.h", "c++/v1/newheader"},
                             stale_scope)
            stale_entries = {entry["path"]: entry for entry in repeated["entries"]}
            self.assertEqual(stale_entries["c++/v1/vector"]["review_status"], "pending")
            self.assertEqual(stale_entries["c++/v1/newheader"]["review_status"], "pending")
            generated.write_text("tampered\n")
            with self.assertRaisesRegex(ValueError, "differs from provenance"):
                audit(sdk, installation, resource, {"probe.h"}, {"float.h"}, [], known)

    def test_probe_closure_rejects_another_sdk_version(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            closure_paths({"schema": 2, "sdk": {"Version": "26.4"}}, "26.5")


if __name__ == "__main__":
    unittest.main()
