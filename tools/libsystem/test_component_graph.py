import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.libsystem.component_graph import component_slots, inventory, read_source


class ComponentGraphTest(unittest.TestCase):
    def test_records_ordered_required_alternatives_and_optional_rows(self):
        entries = component_slots({"requiredlibs": "required_a\nsimulator device\n",
                                   "optionallibs": "optional_z\noptional_y\n"})
        self.assertEqual(entries, [
            {"required": True, "alternatives": ["required_a"], "source": {"path": "requiredlibs", "line": 1}},
            {"required": True, "alternatives": ["simulator", "device"], "source": {"path": "requiredlibs", "line": 2}},
            {"required": False, "alternatives": ["optional_z"], "source": {"path": "optionallibs", "line": 1}},
            {"required": False, "alternatives": ["optional_y"], "source": {"path": "optionallibs", "line": 2}},
        ])

    def test_rejects_duplicate_or_invalid_link_names(self):
        for optional in ("same\n", "has/path\n"):
            with self.subTest(optional=optional), self.assertRaisesRegex(ValueError, r"optionallibs:1:"):
                component_slots({"requiredlibs": "same\n", "optionallibs": optional})

    def test_build_recipe_keeps_unresolved_deployment_facts_open(self):
        config = """DYLIB_CURRENT_VERSION = $(CURRENT_VERSION_STRING_$(RC_XBS))
CURRENT_VERSION_STRING_ = 159
CURRENT_VERSION_STRING_YES = $(CURRENT_PROJECT_VERSION)
LD_DYLIB_INSTALL_NAME = $(DYLIB_INSTALL_NAME_BASE)/$(DYLIB_INSTALL_NAME_EXECUTABLE_PATH)
DYLIB_INSTALL_NAME_EXECUTABLE_PATH = $(DYLIB_INSTALL_NAME_EXECUTABLE_NAME)
"""
        sources = {"Libsystem.xcconfig": config, "requiredlibs": "required_lib\n", "optionallibs": "optional_lib\n"}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {}
            for key, text in sources.items():
                path = root / key
                path.write_text(text)
                files[key] = hashlib.sha256(path.read_bytes()).hexdigest()
            graph = inventory(root, {"sdk": "test", "project": {"files": files}})
        self.assertEqual(graph["scope"]["client_architectures"], ["arm64", "x86_64"])
        self.assertEqual([entry["link_mode"] for entry in graph["linker_rule"]["input_precedence"]],
                         ["reexport", "force_load"])
        self.assertIsNone(graph["umbrella"]["install_name"])
        self.assertIsNone(graph["umbrella"]["current_version"])
        self.assertIsNone(graph["umbrella"]["compatibility_version"])
        self.assertEqual(graph["umbrella"]["version_settings"]["CURRENT_VERSION_STRING_"], "159")
        self.assertEqual(graph["component_slots"][1]["alternatives"], ["optional_lib"])
        self.assertFalse(graph["component_slots"][1]["required"])

    def test_rejects_unpinned_source_bytes(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp).resolve()
            (source / "requiredlibs").write_text("different\n")
            with self.assertRaisesRegex(ValueError, "changed Libsystem source requiredlibs"):
                read_source(source, {"requiredlibs": hashlib.sha256(b"original\n").hexdigest()})


if __name__ == "__main__":
    unittest.main()
