#!/usr/bin/env python3
"""Compile the checked-in default C probe with only Clang and its C package."""

import argparse
import re
import subprocess
from pathlib import Path

from recipes.c_profile import selected_paths


HERE = Path(__file__).resolve().parent


ROOTS = HERE / "fixtures/default-roots.txt"
COMBINED = HERE / "fixtures/c/default_profile.c"
FIXTURES = (HERE / "fixtures/c/fenv_abi.c",
            HERE / "fixtures/c/stdatomic_init.c",
            HERE / "fixtures/c/target_conditionals.c")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clang", required=True, type=Path)
    parser.add_argument("--sysroot", required=True, type=Path)
    args = parser.parse_args()
    sysroot = args.sysroot.resolve()
    roots = [line for line in ROOTS.read_text().splitlines()
             if line and not line.startswith("#")]
    combined_roots = re.findall(r"^#include <([^>]+)>",
                                COMBINED.read_text(), re.MULTILINE)
    if combined_roots != roots:
        parser.error("combined C fixture differs from the selected roots")
    missing = [path for path in selected_paths()
               if not (sysroot / path).is_file()]
    if missing:
        parser.error(f"{len(missing)} manifest paths absent; first: {missing[0]}")
    resource = subprocess.check_output(
        [str(args.clang), "-print-resource-dir"], text=True).strip()
    failures = []
    for arch in ("arm64", "x86_64"):
        base = [str(args.clang), "-target", f"{arch}-apple-macos14.0",
                "-isysroot", str(sysroot), "-nostdinc",
                "-isystem", resource + "/include",
                "-isystem", str(sysroot / "usr/include"),
                "-std=c11", "-fsyntax-only", "-x", "c"]
        for name in roots + ["__combined__"] + [str(path) for path in FIXTURES]:
            command = base.copy()
            if name == "__combined__":
                command.append(str(COMBINED))
                source = None
            elif name.startswith(str(HERE / "fixtures/c/")):
                command.append(name)
                source = None
            else:
                if name == "ucontext.h":
                    command.append("-D_XOPEN_SOURCE=700")
                command.append("-")
                source = f"#include <{name}>\n"
            result = subprocess.run(command, input=source, text=True,
                                    capture_output=True)
            if result.returncode:
                failures.append((arch, name, result.stderr.splitlines()[-3:]))
    total = (len(roots) + 1 + len(FIXTURES)) * 2
    print(f"{total - len(failures)}/{total} default C profile probes passed")
    for arch, name, lines in failures:
        print(f"FAIL {arch} {name}: {'; '.join(lines)}")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
