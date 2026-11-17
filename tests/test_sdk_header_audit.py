"""Exercise the audit's scope and decision boundaries with a synthetic SDK."""

import tempfile
import unittest
from pathlib import Path

from audit_sdk_c_headers import audit, closure_paths


class SdkHeaderAuditTest(unittest.TestCase):
    def test_inventory_keeps_missing_resource_headers_and_review_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sdk, installation, resource = (root / name for name in
                                           ("sdk", "installation", "resource"))
            include = sdk / "usr/include"
            for name in ("base.h", "probe.h", "float.h", "unseen.h",
                         "vendor/api.h", "objc/objc.h", "c++/v1/vector",
                         "foo.modulemap"):
                path = include / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n")
            generated = installation / "usr/include/base.h"
            generated.parent.mkdir(parents=True)
            generated.write_text("\n")
            compiler = resource / "float.h"
            compiler.parent.mkdir()
            compiler.write_text("#  include_next <float.h>\n")
            framework = sdk / "System/Library/Frameworks/Tcl.framework/Headers/tcl.h"
            framework.parent.mkdir(parents=True)
            framework.write_text("\n")
            (include / "tcl.h").symlink_to(framework)

            report = audit(sdk, installation, resource, {"probe.h"}, {"float.h"},
                           [{"pattern": "vendor/*", "decision": "omit",
                             "reason": "separate vendor library"}])
            entries = {entry["path"]: entry for entry in report["entries"]}
            self.assertEqual(len(entries), 9)
            self.assertEqual(report["counts"]["installed"], 1)
            self.assertEqual(report["counts"]["missing"], 4)
            self.assertEqual(report["counts"]["decisions"],
                             {"include": 2, "omit": 5, "review": 2})
            self.assertEqual(entries["probe.h"]["decision"], "include")
            self.assertTrue(entries["float.h"]["compiler_uses_include_next"])
            self.assertTrue(entries["float.h"]["probe_lookup_candidate"])
            self.assertEqual(entries["float.h"]["decision"], "review")
            self.assertEqual(entries["vendor/api.h"]["decision"], "omit")
            self.assertEqual(entries["tcl.h"]["state"], "excluded")

    def test_probe_closure_rejects_another_sdk_version(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            closure_paths({"schema": 2, "sdk": {"Version": "26.4"}}, "26.5")


if __name__ == "__main__":
    unittest.main()
