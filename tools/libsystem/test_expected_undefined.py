import unittest

from .expected_undefined import filter_demands, policy_for


class ExpectedUndefined(unittest.TestCase):
    def test_only_approved_unistd_names_leave_the_demand_list(self):
        policy = policy_for("macosx26.5")
        names = ["_add_profil", "_profil", "_unwhiteout", "_getpid", "_profil_extra"]
        rows = [{"symbol": name, "header": "usr/include/unistd.h", "kind": "function"} for name in names]
        result = filter_demands(policy, [], {"arm64": rows})
        self.assertEqual([r["symbol"] for r in result["arm64"]], names[3:])
        self.assertIsNone(policy_for("macosx26.6"))

    def test_component_attempting_to_export_an_exempt_name_reopens_it(self):
        image = {"install_name": "/usr/lib/system/libexample.dylib",
                 "slices": {"x86_64": {"exports": {"_profil": "text.global"}}}}
        with self.assertRaisesRegex(ValueError, "reopen.*_profil"):
            filter_demands(policy_for("macosx26.5"), [image], {})

    def test_unrelated_declaration_reopens_the_decision(self):
        row = {"symbol": "_profil", "header": "usr/include/other.h", "kind": "data"}
        with self.assertRaisesRegex(ValueError, "new declaration of _profil"):
            filter_demands(policy_for("macosx26.5"), [], {"arm64": [row]})
