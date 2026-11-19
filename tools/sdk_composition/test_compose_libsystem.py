"""Exercise exact SDK selections and provider uniqueness via the composer CLI."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.header_manifest import COLUMNS


PARENT = "/usr/lib/libSystem.B.dylib"
CHILD = "/usr/lib/system/libsystem_fixture.dylib"
FRAMEWORK = "System/Library/Frameworks/Example.framework"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return hashlib.sha256(content.encode()).hexdigest()


def library(name):
    return {"install_names": [{"name": name}], "target_info": [{"target": "arm64-macos"}]}


def tbd(name, *children):
    return json.dumps({
        "tapi_tbd_version": 5,
        "main_library": library(name),
        "libraries": list(map(library, children)),
    })


class ComposeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.c = self.work / "c-install"
        self.package = self.work / "package"
        self.gen = self.work / "sdk-gen"
        self.out = self.work / "out.sdk"
        self.framework = self.gen / FRAMEWORK
        digest = write(self.c / "usr/include/fixture.h", "typedef int fixture_type;\n")
        write(self.c / "header-manifest.tsv", "\t".join(COLUMNS) + "\n" + "\t".join([
            "usr/include/fixture.h", digest, "fixture", "source", "selection", "copy", "input",
        ]) + "\n")
        write(self.c / "uninstalled-scratch.txt", "outside the manifest\n")
        digest = write(self.package / "usr/lib/libSystem.B.tbd", tbd(PARENT, CHILD))
        (self.package / "usr/lib/libSystem.tbd").symlink_to("libSystem.B.tbd")
        self.manifest_sha256 = write(self.package / "manifest.json", json.dumps({"tbd_sha256": digest}))

    def declare_compat_alias(self, path, target):
        manifest = self.package / "manifest.json"
        record = json.loads(manifest.read_text())
        record["symlinks"] = {"usr/lib/libSystem.tbd": "libSystem.B.tbd", path: target}
        self.manifest_sha256 = write(manifest, json.dumps(record))

    def compose(self, *extra):
        return subprocess.run([
            sys.executable, "-m", "tools.sdk_composition.compose_libsystem",
            "--c-install", self.c, "--libsystem", self.package,
            "--libsystem-manifest-sha256", self.manifest_sha256,
            "--llvm", os.getenv("LIBSYSTEM_TEST_LLVM", str(self.work)),
            "--sdk-gen", self.gen, "--out", self.out, *extra,
        ], text=True, capture_output=True)

    def test_selected_assets_and_relative_framework_aliases(self):
        write(self.framework / "Versions/A/Headers/Example.h", "#define EXAMPLE 1\n")
        example = "/System/Library/Frameworks/Example.framework/Versions/A/Example"
        write(self.framework / "Versions/A/Example.tbd", tbd(example))
        (self.framework / "Versions/Current").symlink_to("A")
        (self.framework / "Headers").symlink_to("Versions/Current/Headers")
        (self.framework / "Example.tbd").symlink_to("Versions/Current/Example.tbd")
        write(self.gen / "System/Library/Frameworks/Unselected.framework/unused.h", "\n")
        write(self.gen / "usr/lib/libSystem.B.tbd", tbd(PARENT))
        write(self.gen / "usr/include/c++/v1/vector", "\n")
        external = self.work / "support" / "libexample.tbd"
        write(external, tbd("/usr/lib/libexample.dylib"))

        result = self.compose("--framework", "Example", "--external-stub",
                              f"usr/lib/libexample.tbd={external}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.out / FRAMEWORK / "Headers/Example.h").read_text(),
                         "#define EXAMPLE 1\n")
        self.assertEqual(os.readlink(self.out / FRAMEWORK / "Example.tbd"),
                         "Versions/Current/Example.tbd")
        self.assertEqual(os.readlink(self.out / "usr/lib/libSystem.tbd"), "libSystem.B.tbd")
        self.assertEqual((self.out / "usr/include/fixture.h").read_bytes(),
                         (self.c / "usr/include/fixture.h").read_bytes())
        self.assertFalse((self.out / "uninstalled-scratch.txt").exists())
        self.assertFalse((self.out / "usr/include/c++").exists())
        self.assertFalse((self.out / "System/Library/Frameworks/Unselected.framework").exists())

        manifest = json.loads((self.out / "composition.json").read_text())
        self.assertEqual(manifest["libsystem_manifest_sha256"], self.manifest_sha256)
        self.assertEqual(manifest["providers"], {
            PARENT: ["usr/lib/libSystem.B.tbd"], CHILD: ["usr/lib/libSystem.B.tbd"],
            example: [f"{FRAMEWORK}/Versions/A/Example.tbd"],
            "/usr/lib/libexample.dylib": ["usr/lib/libexample.tbd"],
        })

    def test_renamed_external_stub_with_embedded_child_shadows_generated_provider(self):
        external = self.work / "moved.tbd"
        write(external, tbd("/usr/lib/libUnrelated.dylib", CHILD))
        result = self.compose("--external-stub", f"usr/lib/renamed.tbd={external}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"usr/lib/renamed.tbd shadows generated libSystem install name {CHILD}",
                      result.stderr)
        self.assertFalse(self.out.exists())

    @unittest.skipUnless(os.getenv("LIBSYSTEM_TEST_LLVM"), "requires the official llvm-readtapi")
    def test_v4_framework_stub_checks_child_with_a_different_slice(self):
        visible = "/System/Library/Frameworks/Example.framework/Example"
        write(self.framework / "ArbitraryName.tbd", f"""--- !tapi-tbd
tbd-version: 4
targets: [ arm64-macos ]
install-name: '{visible}'
reexported-libraries:
  - targets: [ arm64-macos ]
    libraries:
      - '{CHILD}'
...
--- !tapi-tbd
tbd-version: 4
targets: [ x86_64-macos ]
install-name: '{CHILD}'
...
""")
        result = self.compose("--framework", "Example")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"ArbitraryName.tbd shadows generated libSystem install name {CHILD}",
                      result.stderr)
        self.assertFalse(self.out.exists())

    def test_external_alias_preserves_its_explicitly_selected_target(self):
        target = self.work / "libextra.1.tbd"
        write(target, tbd("/usr/lib/libextra.1.dylib"))
        alias = self.work / "libextra.tbd"
        alias.symlink_to(target.name)
        result = self.compose("--external-stub", f"usr/lib/libextra.tbd={alias}",
                              "--external-stub", f"usr/lib/libextra.1.tbd={target}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(os.readlink(self.out / "usr/lib/libextra.tbd"), target.name)
        report = json.loads((self.out / "composition.json").read_text())
        self.assertEqual(report["providers"]["/usr/lib/libextra.1.dylib"],
                         ["usr/lib/libextra.1.tbd"])

    def test_framework_can_only_link_to_its_own_selected_members(self):
        write(self.gen / "System/Library/Frameworks/Unselected.framework/H.h", "\n")
        self.framework.mkdir()
        (self.framework / "Escape.h").symlink_to("../Unselected.framework/H.h")
        result = self.compose("--framework", "Example")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SDK source symlink escapes selected input", result.stderr)
        self.assertFalse(self.out.exists())

    def test_external_file_cannot_replace_libsystem_alias(self):
        external = self.work / "other.tbd"
        write(external, tbd("/usr/lib/other.dylib"))
        result = self.compose("--external-stub", f"usr/lib/libSystem.tbd={external}")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SDK path collision: usr/lib/libSystem.tbd", result.stderr)
        self.assertFalse(self.out.exists())

    def test_generated_stub_has_to_match_the_pinned_package_receipt(self):
        write(self.package / "usr/lib/libSystem.B.tbd", tbd(PARENT))
        result = self.compose()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SDK file differs from its input manifest: usr/lib/libSystem.B.tbd",
                      result.stderr)
        self.assertFalse(self.out.exists())

    def test_generated_compatibility_alias_keeps_its_declared_relative_target(self):
        path = "usr/lib/libm.tbd"
        self.declare_compat_alias(path, "libSystem.tbd")
        (self.package / path).symlink_to("libSystem.tbd")

        result = self.compose()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(os.readlink(self.out / path), "libSystem.tbd")
        manifest = json.loads((self.out / "composition.json").read_text())
        self.assertEqual(manifest["files"][path]["symlink"], "libSystem.tbd")
        self.assertEqual(manifest["providers"][PARENT], ["usr/lib/libSystem.B.tbd"])

    def test_legacy_package_rejects_an_undeclared_compatibility_alias(self):
        (self.package / "usr/lib/libm.tbd").symlink_to("libSystem.tbd")

        result = self.compose()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected generated libSystem payload", result.stderr)
        self.assertFalse(self.out.exists())

    def test_generated_compatibility_alias_rejects_a_different_link_to_the_same_stub(self):
        path = "usr/lib/libm.tbd"
        self.declare_compat_alias(path, "libSystem.tbd")
        (self.package / path).symlink_to("libSystem.B.tbd")

        result = self.compose()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"generated {path} must be a relative alias to libSystem.tbd", result.stderr)
        self.assertFalse(self.out.exists())

    def test_generated_compatibility_alias_manifest_cannot_escape_usr_lib(self):
        self.declare_compat_alias("usr/lib/../libm.tbd", "libSystem.tbd")

        result = self.compose()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected a canonical SDK-relative path", result.stderr)
        self.assertFalse(self.out.exists())

    def test_generated_compatibility_alias_manifest_rejects_escaping_target(self):
        path = "usr/lib/libm.tbd"
        self.declare_compat_alias(path, "../../libSystem.tbd")
        (self.package / path).symlink_to("../../libSystem.tbd")

        result = self.compose()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"unexpected declared libSystem symlink target for {path}", result.stderr)
        self.assertFalse(self.out.exists())

    def test_named_framework_cannot_embed_a_static_archive(self):
        write(self.framework / "toolchain.a", "!<arch>\n")
        result = self.compose("--framework", "Example")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("toolchain or binary asset cannot enter the composed SDK", result.stderr)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
