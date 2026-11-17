"""Check the pinned XNU public lists used by the C installer."""

import unittest

from install_c import (libc_public_headers, libinfo_macos_headers,
                       xnu_public_make_headers)


class XnuPublicHeadersTest(unittest.TestCase):
    def test_libc_script_lists_public_paths_and_moves_asm_private(self):
        headers = set(libc_public_headers())
        self.assertIn("stdio.h", headers)
        self.assertIn("arpa/inet.h", headers)
        self.assertIn("sys/rbtree.h", headers)
        self.assertNotIn("asm.h", headers)
        self.assertNotIn("authentication.h", headers)

    def test_libinfo_macos_destination_includes_rpc_and_rpcsvc(self):
        headers = dict(libinfo_macos_headers())
        self.assertEqual(headers["rpc/pmap_clnt.h"], "rpc.subproj/pmap_clnt.h")
        self.assertEqual(headers["rpcsvc/yp_prot.h"], "nis.subproj/yp_prot.h")
        self.assertNotIn("configuration_profile.h", headers)

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
        device = set(xnu_public_make_headers("osfmk/device", "INSTALL_MI_LIST"))
        self.assertEqual(device, {"device_port.h", "device_types.h"})


if __name__ == "__main__":
    unittest.main()
