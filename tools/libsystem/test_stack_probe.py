"""Exercise the approved stack-probe rule without local Apple SDK inputs."""

from copy import deepcopy
import unittest

from .emit import resolve
from .stack_probe import ALIAS, COMPILER_RT, IMPLEMENTATION, PTHREAD, SDK, install


def image(name, *edges):
    return {
        "install_name": name,
        "current_version": "1",
        "compatibility_version": "1",
        "slices": {
            arch: {"exports": {}, "reexports": list(edges)}
            for arch in ("arm64", "x86_64")
        },
    }


class StackProbeTests(unittest.TestCase):
    def setUp(self):
        self.pthread = image(PTHREAD)
        self.compiler_rt = image(COMPILER_RT)
        self.libsystem = image("/usr/lib/libSystem.B.dylib", COMPILER_RT, PTHREAD)
        self.images = [self.libsystem, self.pthread, self.compiler_rt]

    def test_emit_definition_and_renamed_reexport_on_both_targets(self):
        receipt = install(SDK, self.images)
        tbd, providers = resolve(self.images, {
            arch: [{"symbol": ALIAS, "kind": "function", "header": "stack-probe"}]
            for arch in ("arm64", "x86_64")
        }, "11.0")

        compiler_rt, pthread = tbd["libraries"]
        self.assertEqual(compiler_rt["reexported_symbols"], [
            {"targets": ["arm64-macos"], "text": {"global": [ALIAS]}},
            {"targets": ["x86_64-macos"], "text": {"global": [ALIAS]}},
        ])
        self.assertEqual(pthread["exported_symbols"], [
            {"targets": ["arm64-macos"], "text": {"global": [IMPLEMENTATION]}},
            {"targets": ["x86_64-macos"], "text": {"global": [IMPLEMENTATION]}},
        ])
        self.assertEqual(providers[0]["target_library"], PTHREAD)
        self.assertEqual(providers[0]["target_symbol"], IMPLEMENTATION)
        self.assertEqual(install(SDK, self.images), receipt)

    def test_reject_conflicting_forwarding_without_mutating_slices(self):
        self.compiler_rt["slices"]["x86_64"]["symbol_reexports"] = {
            ALIAS: {"kind": "text.global", "target_library": PTHREAD, "target_symbol": "_different"},
        }
        original = deepcopy(self.images)

        with self.assertRaisesRegex(ValueError, "x86_64: conflicting stack-probe symbol_reexports"):
            install(SDK, self.images)

        self.assertEqual(self.images, original)

    def test_reject_alias_listed_as_definition(self):
        self.compiler_rt["slices"]["arm64"]["exports"][ALIAS] = "text.global"

        with self.assertRaisesRegex(ValueError, "arm64: conflicting stack-probe exports"):
            install(SDK, self.images)

    def test_reject_missing_component_slice(self):
        self.pthread["slices"].pop("arm64")

        with self.assertRaisesRegex(ValueError, "both target slices"):
            install(SDK, self.images)

    def test_reject_other_release(self):
        with self.assertRaisesRegex(ValueError, "only to macosx26.5"):
            install("macosx26.4", self.images)

    def test_reject_deployment_before_reviewed_scope(self):
        with self.assertRaisesRegex(ValueError, "deployment minima"):
            install(SDK, self.images, minimum="10.15")


if __name__ == "__main__":
    unittest.main()
