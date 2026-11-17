#!/usr/bin/env python3
"""Check C headers with no include path outside this sysroot and Clang."""

import argparse
import subprocess
from pathlib import Path

HEADERS = (
    "Availability.h", "assert.h", "checkint.h", "complex.h", "copyfile.h", "ctype.h",
    "device/device_port.h", "dlfcn.h", "dirent.h", "errno.h", "execinfo.h", "fcntl.h",
    "fenv.h", "float.h", "fnmatch.h", "glob.h", "hfs/hfs_mount.h", "inttypes.h",
    "langinfo.h", "limits.h", "locale.h", "math.h", "pthread.h",
    "pthread_impl.h", "pthread_spis.h",
    "pwd.h", "sched.h", "servers/key_defs.h", "servers/ls_defs.h",
    "servers/netname.h", "servers/netname_defs.h", "servers/nm_defs.h",
    "setjmp.h", "signal.h", "spawn.h",
    "stdarg.h", "stdatomic.h", "stdbool.h", "stddef.h", "stdint.h", "stdio.h",
    "stdlib.h", "string.h", "strings.h", "sandbox.h", "sys/cdefs.h", "sys/dirent.h",
    "sys/mman.h", "sys/param.h", "sys/resource.h", "sys/select.h",
    "sys/socket.h", "sys/stat.h", "sys/syscall.h", "sys/sysctl.h", "sys/time.h",
    "sys/types.h", "sys/uio.h", "sys/wait.h", "termios.h", "time.h",
    "tgmath.h", "TargetConditionals.h", "unistd.h", "wchar.h", "wctype.h", "mach/mach.h",
    "mach-o/dyld.h", "libkern/OSByteOrder.h", "CoreFoundation/CoreFoundation.h",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sysroot", required=True, type=Path)
    parser.add_argument("--clang", required=True,
                        help="clang from the pinned minimal LLVM prebuilt")
    args = parser.parse_args()
    sdk = args.sysroot.resolve()
    resource = subprocess.check_output([args.clang, "-print-resource-dir"], text=True).strip()
    failures = []
    for arch in ("arm64", "x86_64"):
        for header in HEADERS:
            source = f"#include <{header}>\n"
            if header == "fenv.h":
                source += '_Static_assert(sizeof(fenv_t) == 16, "ABI");\n'
            if header == "stdatomic.h":
                source += "atomic_flag flag = ATOMIC_FLAG_INIT;\n"
            if header == "TargetConditionals.h":
                source += "#if !TARGET_OS_MAC || TARGET_OS_LINUX\n#error wrong macOS target flags\n#endif\n"
                if arch == "arm64":
                    source += "#if !TARGET_CPU_ARM64 || TARGET_CPU_X86_64\n#error wrong arm64 target flags\n#endif\n"
                else:
                    source += "#if TARGET_CPU_ARM64 || !TARGET_CPU_X86_64\n#error wrong x86_64 target flags\n#endif\n"
            if header == "CoreFoundation/CoreFoundation.h":
                source += "CFBundleRef bundle = 0;\n"
            if header == "sandbox.h":
                source += "int (*init_fn)(const char *, uint64_t, char **) = sandbox_init;\n"
            command = [
                args.clang, "-target", f"{arch}-apple-macos14.0", "-isysroot",
                str(sdk), "-nostdinc", "-isystem", resource + "/include",
                "-isystem", str(sdk / "usr/include"),
                "-F", str(sdk / "System/Library/Frameworks"),
                "-std=c11", "-fsyntax-only", "-x", "c", "-",
            ]
            result = subprocess.run(command, input=source, text=True,
                                    capture_output=True)
            if result.returncode:
                errors = [line for line in result.stderr.splitlines()
                          if "error:" in line]
                failures.append((arch, header, errors[:2]))
    print(f"{len(HEADERS) * 2 - len(failures)}/{len(HEADERS) * 2} passes")
    for arch, header, lines in failures:
        print(f"FAIL {arch} {header}")
        print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
