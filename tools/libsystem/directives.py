"""Extract macOS linker directives from the pinned Libc and libdispatch sources."""

import argparse
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from tools.header_manifest import read_header_manifest
from tools.toolchain.official_llvm import PIN, check_digest, projection, read_lock, sha256
from .__main__ import relative_file, write_json
from .emit import ARCHES


LIBC = "Libc/darwin/compatibility_hacks.c"
DISPATCH_HEADER = "libdispatch/src/internal.h"
DISPATCH_INIT = "libdispatch/src/init.c"
SOURCE_DIGESTS = {
    LIBC: "57675388f063c3b2d644d1ae90e760242eb4c13727dcdb884a9675b7c90eb384",
    DISPATCH_HEADER: "8cdbf3141fa3bd023b546fde72a990db8851c37ad370254e7a220a9528071054",
    DISPATCH_INIT: "57f7174ee0ea702fbe8b5cc76d5b05a089c8b6f81657dfe44389701f40ad0861",
}
DIRECTIVE = re.compile(r"\$ld\$(weak|hide)\$os([0-9]+\.[0-9]+)\$(_[A-Za-z0-9_]+)")


def dispatch_translation_unit(header, init):
    # init.c also needs private build headers. Compile just the source macro
    # and its macOS switch, followed by the invocations from the pinned file.
    start = "#define __DISPATCH_HIDE_SYMBOL("
    end = "#ifndef DISPATCH_STATIC_GLOBAL"
    if header.count(start) != 1 or header.count(end) != 1:
        raise ValueError("libdispatch directive macro boundaries changed")
    macro = header.split(start, 1)[1].split(end, 1)[0]
    calls = re.findall(r"^DISPATCH_HIDE_SYMBOL\([^\n]+\);$", init, re.MULTILINE)
    if not calls or len(calls) != len(re.findall(r"^\s*DISPATCH_HIDE_SYMBOL\b", init, re.MULTILINE)):
        raise ValueError("libdispatch directive invocation layout changed")
    return "#include <TargetConditionals.h>\n" + start + macro + "\n".join(calls) + "\n"


def extract(llvm, source_root, c_install):
    lock = read_lock(PIN)
    projection(llvm, lock)
    paths = {name: relative_file(source_root, name) for name in SOURCE_DIGESTS}
    for name, path in paths.items():
        check_digest(path, SOURCE_DIGESTS[name])

    c_manifest, _ = read_header_manifest(c_install)
    target_header = "usr/include/TargetConditionals.h"
    receipt = c_manifest.get(target_header)
    if not receipt:
        raise ValueError(f"C installation has no receipt for {target_header}")
    check_digest(relative_file(c_install, target_header), receipt["sha256"])

    directives = []
    with TemporaryDirectory(prefix="libsystem-directives-") as temporary:
        work = Path(temporary)
        dispatch = work / "dispatch.c"
        dispatch.write_text(dispatch_translation_unit(paths[DISPATCH_HEADER].read_text(),
                                                       paths[DISPATCH_INIT].read_text()))
        resource = llvm / lock["resource_headers"]["path"]
        arch_environment = {"LC_ALL": "C"}
        inputs = (
            ("/usr/lib/system/libdispatch.dylib", "hide", dispatch),
            ("/usr/lib/system/libsystem_c.dylib", "weak", paths[LIBC]),
        )
        for provider, expected_kind, source in inputs:
            for arch in ARCHES:
                obj = work / f"{expected_kind}-{arch}.o"
                target = f"{arch}-apple-macos11.0"
                subprocess.run(
                    [llvm / "bin/clang", "--no-default-config", "-target", target,
                     "-isysroot", c_install, "-nostdinc", "-isystem", resource,
                     "-isystem", c_install / "usr/include", "-c", source, "-o", obj],
                    env=arch_environment, check=True,
                )
                names = subprocess.check_output(
                    [llvm / "bin/llvm-nm", "--extern-only", "--defined-only", "--just-symbol-name", obj],
                    env=arch_environment, text=True,
                ).splitlines()
                selected = [name for name in names if name.startswith("$ld$")]
                if not selected or len(selected) != len(set(selected)):
                    raise ValueError(f"{provider} {arch}: missing or duplicate linker directives")
                for name in sorted(selected):
                    match = DIRECTIVE.fullmatch(name)
                    if not match or match[1] != expected_kind:
                        raise ValueError(f"{provider} {arch}: unsupported linker directive {name!r}")
                    kind, deployment, symbol = match.groups()
                    directives.append({
                        "target": arch + "-macos", "provider": provider, "name": name,
                        "kind": kind, "deployment": deployment, "symbol": symbol,
                    })

    return {
        "schema": 1,
        "sdk": "macosx26.5",
        "source_sha256": SOURCE_DIGESTS,
        "toolchain_lock_sha256": sha256(PIN),
        "target_conditionals_sha256": receipt["sha256"],
        "directives": directives,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("llvm", "source-root", "c-install", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        if os.path.lexists(args.out):
            raise ValueError(f"choose a new output path: {args.out}")
        result = extract(args.llvm.resolve(), args.source_root.resolve(), args.c_install.resolve())
        write_json(args.out, result)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"libsystem directives: {exc}\n")


if __name__ == "__main__":
    main()
