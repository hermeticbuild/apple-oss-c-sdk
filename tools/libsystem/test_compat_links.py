"""Qualify the compatibility links emitted by the pinned Libsystem install step."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.libsystem.compat_links import install_compat_links


class CompatLinksTests(unittest.TestCase):
    def test_changed_script_is_rejected_before_execution(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "source/xcodescripts/create_dylib_symlinks.sh"
            script.parent.mkdir(parents=True)
            marker = root / "executed"
            script.write_text('touch "' + str(marker) + '"\n')
            lib = root / "package/usr/lib"
            lib.mkdir(parents=True)

            with self.assertRaisesRegex(ValueError, "changed Libsystem source"):
                install_compat_links(root / "source", lib)
            self.assertFalse(marker.exists())
            self.assertEqual(list(lib.iterdir()), [])

    @unittest.skipUnless(os.getenv("LIBSYSTEM_TEST_SOURCE"), "requires pinned Apple Libsystem source")
    def test_pinned_macos_source_installs_and_receipts_compatibility_links(self):
        with TemporaryDirectory() as temporary:
            lib = Path(temporary) / "usr/lib"
            lib.mkdir(parents=True)
            (lib / "libSystem.B.tbd").touch()

            links = install_compat_links(Path(os.environ["LIBSYSTEM_TEST_SOURCE"]), lib)
            self.assertEqual(links, {
                "usr/lib/libSystem.tbd": "libSystem.B.tbd",
                "usr/lib/libc.tbd": "libSystem.tbd",
                "usr/lib/libdbm.tbd": "libSystem.tbd",
                "usr/lib/libdl.tbd": "libSystem.tbd",
                "usr/lib/libgcc_s.1.tbd": "libSystem.tbd",
                "usr/lib/libinfo.tbd": "libSystem.tbd",
                "usr/lib/libm.tbd": "libSystem.tbd",
                "usr/lib/libpoll.tbd": "libSystem.tbd",
                "usr/lib/libproc.tbd": "libSystem.tbd",
                "usr/lib/libpthread.tbd": "libSystem.tbd",
                "usr/lib/librpcsvc.tbd": "libSystem.tbd",
            })
            self.assertEqual({f"usr/lib/{path.name}": os.readlink(path) for path in lib.iterdir()
                              if path.is_symlink()}, links)


if __name__ == "__main__":
    unittest.main()
