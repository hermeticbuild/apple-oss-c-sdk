#!/usr/bin/env python3
"""Check C headers and semantic fixtures with only this sysroot and Clang."""

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

ROOT = Path(__file__).resolve().parent
FIXTURES = (
    ROOT / "tests/c/fenv_abi.c",
    ROOT / "tests/c/stdatomic_init.c",
    ROOT / "tests/c/target_conditionals.c",
    ROOT / "tests/c/corefoundation_types.c",
    ROOT / "tests/c/sandbox_signature.c",
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
    cases = [(header, "-", f"#include <{header}>\n") for header in HEADERS]
    cases.extend((fixture.relative_to(ROOT).as_posix(), str(fixture), None)
                 for fixture in FIXTURES)
    for arch in ("arm64", "x86_64"):
        command = [
            args.clang, "-target", f"{arch}-apple-macos14.0", "-isysroot",
            str(sdk), "-nostdinc", "-isystem", resource + "/include",
            "-isystem", str(sdk / "usr/include"),
            "-F", str(sdk / "System/Library/Frameworks"),
            "-std=c11", "-fsyntax-only", "-x", "c",
        ]
        for label, path, source in cases:
            result = subprocess.run([*command, path], input=source, text=True,
                                    capture_output=True)
            if result.returncode:
                errors = [line for line in result.stderr.splitlines()
                          if "error:" in line]
                failures.append((arch, label, errors[:2]))
    total = (len(HEADERS) + len(FIXTURES)) * 2
    print(f"{total - len(failures)}/{total} passes "
          f"({len(HEADERS)} header includes and {len(FIXTURES)} C fixtures per target)")
    for arch, label, lines in failures:
        print(f"FAIL {arch} {label}")
        print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
