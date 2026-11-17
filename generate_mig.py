#!/usr/bin/env python3
"""Generate public Mach user/server headers from pinned XNU .defs files."""

import argparse
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
XNU = ROOT / "sources/xnu"


def names_from_apple_manifests() -> tuple[list[str], list[str]]:
    libsyscall = (XNU / "libsyscall/xcodescripts/mach_install_mig.sh").read_text()
    user_block = re.search(r'^MIGS="(.*?)"', libsyscall, re.M | re.S)
    if user_block is None:
        raise ValueError("XNU Libsyscall MIGS list changed")
    user = re.findall(r"([A-Za-z0-9_]+)\.defs", user_block.group(1))
    if 'MIGS="$MIGS mach_vm.defs"' not in libsyscall:
        raise ValueError("XNU macOS mach_vm.defs selection changed")
    user.append("mach_vm")

    osfmk = (XNU / "osfmk/mach/Makefile").read_text()
    server_block = osfmk.split("MIG_USHDRS =", 1)[1].split("MIG_UUHDRS =", 1)[0]
    server = re.findall(r"([A-Za-z0-9_]+)_server\.h", server_block)
    if len(user) != 17 or len(server) != 15:
        raise ValueError(f"unexpected Apple MIG manifest: {len(user)} user, {len(server)} server")
    return user, server


def generate(mig: Path, clang: Path, sysroot: Path, out: Path) -> None:
    user_names, server_names = names_from_apple_manifests()
    env = os.environ.copy()
    env["MIGCC"] = str(clang)
    for arch, mig_arch in (("arm64", "armv7"), ("x86_64", "i386")):
        destination = out / arch / "mach"
        destination.mkdir(parents=True)
        common = [str(mig), "-novouchers", "-arch", mig_arch,
                  "-isysroot", str(sysroot), "-I" + str(XNU / "osfmk")]
        for name in user_names:
            header = destination / f"{name}.h"
            command = common + ["-DLIBSYSCALL_INTERFACE", "-user", "/dev/null",
                                "-server", "/dev/null", "-header", str(header),
                                str(XNU / "libsyscall/mach" / f"{name}.defs")]
            subprocess.run(command, env=env, check=True)
            filtered = subprocess.check_output([
                "awk", "-f", str(XNU / "libsyscall/xcodescripts/filter_mig.awk"),
                str(XNU / "libsyscall/mach/add_attributes_to_mig.txt"), str(header)])
            header.write_bytes(filtered)
        for name in server_names:
            header = destination / f"{name}_server.h"
            command = common + ["-user", "/dev/null", "-server", "/dev/null",
                                "-header", "/dev/null", "-sheader", str(header),
                                str(XNU / "osfmk/mach" / f"{name}.defs")]
            subprocess.run(command, env=env, check=True)

    arm = out / "arm64/mach"
    intel = out / "x86_64/mach"
    mismatched = [p.name for p in arm.glob("*.h")
                  if p.read_bytes() != (intel / p.name).read_bytes()]
    if mismatched:
        raise ValueError(f"architecture-specific MIG output: {mismatched}")
    print(f"generated {len(user_names)} user + {len(server_names)} server headers per architecture")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mig", required=True, type=Path)
    parser.add_argument("--clang", default="/opt/homebrew/opt/llvm/bin/clang", type=Path)
    parser.add_argument("--sysroot", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists")
    # Keep Bazel's `bazel-bin/mig` symlink path: mig.sh finds its runfiles
    # relative to the invoked path, not the resolved source script.
    generate(args.mig.absolute(), args.clang.resolve(), args.sysroot.resolve(), args.out.absolute())


if __name__ == "__main__":
    main()
