#!/usr/bin/env python3
"""Check the pinned LLVM libunwind layer in a composed macOS sysroot."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PIN = ROOT / "inputs/llvm-libunwind-headers.json"
TARGETS = ("arm64", "x86_64")
ROOTS = ("__libunwind_config.h", "libunwind.h", "unwind.h")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", required=True, type=Path)
    parser.add_argument("--sysroot", required=True, type=Path)
    args = parser.parse_args()
    sysroot = args.sysroot.resolve()
    pin = json.loads(PIN.read_text())
    provenance = json.loads((sysroot / "header-provenance.json").read_text())["files"]
    for name, expected in pin["sha256"].items():
        path = sysroot / "usr/include" / name
        record = provenance.get(f"usr/include/{name}", {})
        if (not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected or
                record.get("sha256") != expected or
                record.get("origin") !=
                f"llvm-libunwind:llvmorg-{pin['llvm_version']}/libunwind/include/{name}"):
            parser.error(f"LLVM libunwind header/provenance mismatch: {name}")
    resource = Path(subprocess.check_output(
        [str(args.clang), "-print-resource-dir"], text=True).strip()) / "include"
    if not resource.is_dir():
        parser.error("Clang resource headers missing")
    for arch in TARGETS:
        for name in ROOTS:
            command = [str(args.clang), "-target", f"{arch}-apple-macos14.0",
                       "-isysroot", str(sysroot), "-nostdinc", "-isystem", str(resource),
                       "-isystem", str(sysroot / "usr/include"), "-std=c11",
                       "-H", "-fsyntax-only", "-x", "c", "-"]
            result = subprocess.run(command, input=f"#include <{name}>\n",
                                    text=True, capture_output=True)
            if result.returncode:
                raise RuntimeError(f"{arch} {name}: {result.stderr}")
            opened = {line.lstrip(". ").strip() for line in result.stderr.splitlines()
                      if line.startswith(".")}
            if str(sysroot / "usr/include" / name) not in opened:
                raise RuntimeError(f"{arch} {name} did not open the pinned LLVM header")
            if (name == "unwind.h" and
                    str(sysroot / "usr/include/unwind_itanium.h") not in opened):
                raise RuntimeError(f"{arch} unwind.h did not include LLVM unwind_itanium.h")
    print(f"{len(TARGETS) * len(ROOTS)}/{len(TARGETS) * len(ROOTS)} LLVM libunwind probes passed")


if __name__ == "__main__":
    main()
