"""Check the pinned XNU public lists used by the C installer."""

import unittest

from recipes.public_sources import public_xcode_selection
from recipes.xnu.headers import libsyscall_public_mach_headers, xnu_public_make_headers
from pathlib import Path


class XnuPublicHeadersTest(unittest.TestCase):
    def test_sys_list_excludes_private_kernel_headers(self):
        headers = set(xnu_public_make_headers("bsd/sys", "INSTALL_MI_LIST"))
        self.assertIn("socket.h", headers)
        self.assertIn("cdefs.h", headers)
        self.assertNotIn("proc_private.h", headers)
        self.assertNotIn("aio_kern.h", headers)

    def test_mach_and_os_lists_follow_public_install_variables(self):
        mach = set(xnu_public_make_headers("osfmk/mach", "INSTALL_MI_LIST"))
        os_headers = set(xnu_public_make_headers("libkern/os", "INSTALL_MI_LIST"))
        self.assertIn("mach_time.h", mach)
        self.assertNotIn("mach_time_private.h", mach)
        self.assertEqual(os_headers, {"atomic.h", "base.h", "overflow.h"})

    def test_selected_mach_public_lists(self):
        self.assertIn("ipc_info.h", xnu_public_make_headers(
            "osfmk/mach_debug", "INSTALL_MI_LIST"))
        self.assertEqual(len(libsyscall_public_mach_headers()), 10)
        self.assertIn("mach_init.h", libsyscall_public_mach_headers())

    def test_xcode_public_phase_selects_known_headers(self):
        root = Path(__file__).resolve().parents[2]
        self.assertEqual(public_xcode_selection(
            root / "sources/libpthread/include/pthread/pthread.h"),
            "libpthread/libpthread.xcodeproj/project.pbxproj:Public")
        self.assertIsNone(public_xcode_selection(
            root / "sources/libplatform/include/string_x86.h"))


if __name__ == "__main__":
    unittest.main()
