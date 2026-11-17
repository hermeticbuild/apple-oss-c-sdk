"""Check the pinned XNU public lists used by the C installer."""

import unittest

from install_c import (architecture_public_headers, libc_public_headers, libinfo_macos_headers,
                       libsyscall_public_mach_headers, libsyscall_public_os_headers,
                       libsyscall_public_server_headers,
                       libunwind_public_headers, openbsm_public_headers,
                       public_xcode_selection,
                       xnu_public_make_headers)
from pathlib import Path


class XnuPublicHeadersTest(unittest.TestCase):
    def test_architecture_make_installs_both_cpu_families(self):
        headers = {path.as_posix() for path in architecture_public_headers()}
        self.assertEqual(len(headers), 19)
        self.assertIn("byte_order.h", headers)
        self.assertIn("arm/cframe.h", headers)
        self.assertIn("i386/cpu.h", headers)

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

    def test_bsm_mach_debug_and_libsyscall_public_lists(self):
        self.assertIn("audit_domain.h", xnu_public_make_headers(
            "bsd/bsm", "INSTALL_MI_LIST"))
        self.assertIn("mach_debug.h", xnu_public_make_headers(
            "osfmk/mach_debug", "INSTALL_MI_LIST"))
        self.assertEqual(len(libsyscall_public_mach_headers()), 10)
        self.assertIn("mach_right.h", libsyscall_public_mach_headers())
        self.assertEqual(set(libsyscall_public_server_headers()), {
            "key_defs.h", "ls_defs.h", "netname_defs.h", "nm_defs.h"})
        self.assertEqual(libsyscall_public_os_headers(), ["proc.h"])
        self.assertEqual(xnu_public_make_headers("osfmk/atm", "INSTALL_MI_LIST"),
                         ["atm_types.h"])
        for arch in ("arm", "arm64", "i386"):
            self.assertEqual(xnu_public_make_headers(
                f"osfmk/mach/{arch}", "INSTALL_MD_GEN_LIST"), ["asm.h"])

    def test_xcode_public_phase_selects_known_headers(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(public_xcode_selection(
            root / "sources/Libnotify/notify.h"),
            "Libnotify/Libnotify.xcodeproj/project.pbxproj:Public")
        self.assertEqual(public_xcode_selection(
            root / "sources/libpthread/include/pthread/pthread.h"),
            "libpthread/libpthread.xcodeproj/project.pbxproj:Public")
        self.assertIsNone(public_xcode_selection(
            root / "sources/libplatform/include/string_x86.h"))
        self.assertEqual(public_xcode_selection(root / "sources/libresolv/dns.h"),
                         "libresolv/libresolv.xcodeproj/project.pbxproj:Public")
        self.assertEqual(public_xcode_selection(
            root / "sources/syslog/libsystem_asl.tproj/include/asl.h"),
            "syslog/syslog.xcodeproj/project.pbxproj:Public")

    def test_openbsm_macos_header_destination(self):
        self.assertEqual(set(openbsm_public_headers()), {
            "audit_filter.h", "audit_uevents.h", "libbsm.h"})

    def test_libunwind_copy_phase(self):
        self.assertEqual({path.name for path in libunwind_public_headers()}, {
            "__libunwind_config.h", "libunwind.h", "unwind.h"})


if __name__ == "__main__":
    unittest.main()
