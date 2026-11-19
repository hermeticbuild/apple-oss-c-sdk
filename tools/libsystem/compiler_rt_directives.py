"""Extract macOS linker directives from pinned public compiler-rt source."""

import argparse
import hashlib
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from tools.header_manifest import read_header_manifest
from tools.qualify_headers.trace_includes import dependencies
from tools.toolchain.official_llvm import PIN, projection, read_lock, sha256
from .emit import ARCHES
from .scan import dump_json, header_receipt, run


SOURCE_PATH = "compiler-rt/lib/builtins/apple_versioning.c"
SOURCE_REVISION = "85ac560262434c9ccfc0c183ec22d4138ed647fb"
SOURCE_SHA256 = "c51e0fcbec808e1cc122a03192c3acb057830896ea6707006e46bdd5e19d5309"
COMPONENT = "/usr/lib/system/libcompiler_rt.dylib"
DIRECTIVE = re.compile(r"\$ld\$hide\$os[0-9]+\.[0-9]+\$_[A-Za-z0-9_]+")


def extract(llvm, c_install, source):
    source_bytes = source.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError(f"compiler-rt source SHA-256 mismatch: {source}")

    toolchain = read_lock(PIN)
    if toolchain["commit"] != SOURCE_REVISION:
        raise ValueError("review the compiler-rt source pin for the LLVM toolchain revision")
    projection(llvm, toolchain)
    tools = llvm / "bin"
    manifest, metadata = read_header_manifest(c_install)
    for path in metadata:
        if not path.resolve().is_relative_to(c_install):
            raise ValueError(f"manifest metadata outside the C installation: {path}")

    targets = {}
    with TemporaryDirectory(prefix="compiler-rt-directives-") as scratch:
        work = Path(scratch).resolve()
        input_file = work / Path(SOURCE_PATH).name
        input_file.write_bytes(source_bytes)
        for arch in ARCHES:
            target = f"{arch}-apple-macos11.0"
            obj = work / f"{arch}.o"
            depfile = work / f"{arch}.d"
            run(tools / "clang", (
                "--no-default-config", "-target", target, "-nostdinc", "-isysroot", c_install,
                "-isystem", c_install / "usr/include", "-std=c17", "-fvisibility=hidden",
                "-MD", "-MF", depfile, "-MT", "object", "-c", input_file, "-o", obj,
            ), work)
            headers = []
            for path in sorted(set(dependencies(depfile)) - {input_file}):
                if not path.is_relative_to(c_install):
                    raise ValueError(f"compiler-rt dependency outside the C installation: {path}")
                headers.append(header_receipt(c_install, manifest, path.relative_to(c_install).as_posix()))
            names = run(tools / "llvm-nm", ("--extern-only", "--defined-only",
                                           "--just-symbol-name", obj), work).splitlines()
            if (not names or len(set(names)) != len(names) or
                    any(not DIRECTIVE.fullmatch(name) for name in names)):
                raise ValueError(f"{target} produced an unexpected compiler-rt directive inventory")
            targets[arch] = {"target": target, "headers": headers, "directives": sorted(names)}

    return {
        "schema": 1,
        "component": COMPONENT,
        "source": {"repository": toolchain["repository"], "revision": SOURCE_REVISION,
                   "path": SOURCE_PATH, "sha256": SOURCE_SHA256},
        "toolchain_lock_sha256": sha256(PIN),
        "targets": targets,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("llvm", "c-install", "source"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        report = extract(args.llvm.resolve(), args.c_install.resolve(), args.source)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"compiler-rt directives: {exc}\n")
    print(dump_json(report), end="")


if __name__ == "__main__":
    main()
