"""Recheck the source, reference, runtime and client links for the stack-probe alias."""

import argparse
import json
from pathlib import Path
import plistlib
import re
import subprocess
from types import SimpleNamespace

from tools.sdk_review.libsystem_tbd import read_stub
from tools.sdk_review.verify_libsystem_links import link
from tools.toolchain.official_llvm import PIN, projection, read_lock

from .capture import capture
from .emit import ARCHES, SYSTEM
from .scan import digest, run
from .stack_probe import (ALIAS, COMPILER_RT, HOST_BUILD, IMPLEMENTATION, MINIMA, PTHREAD,
                          PTHREAD_SOURCE, REFERENCE_BUILD, RUNTIME)


FIXTURE = Path(__file__).parent / "fixtures/stack_probe_names.c"


def check_roles(root, llvm, alias_role, segment):
    stub = read_stub((root / "usr/lib/libSystem.tbd").read_text(), llvm / "bin/llvm-readtapi")
    for arch in ARCHES:
        target = arch + "-macos"
        actual = {
            (image, encoding, symbol): info
            for image, slices in stub.libraries.items() if target in slices
            for (encoding, symbol), info in slices[target].symbols.items()
            if symbol in (ALIAS, IMPLEMENTATION)
        }
        expected = {
            (COMPILER_RT, "global", ALIAS):
                {"role": alias_role, "weak": False, "thread_local": False, "segment": segment},
            (PTHREAD, "global", IMPLEMENTATION):
                {"role": "export", "weak": False, "thread_local": False, "segment": segment},
        }
        if actual != expected:
            raise ValueError(f"{root}: {arch} stack-probe TBD roles changed: {actual}")


def check_runtime(arch, cache, inspector, out):
    runtime = RUNTIME[arch]
    observed = runtime["slice"]
    pairs = ((COMPILER_RT, "compiler_rt_uuid"), (PTHREAD, "pthread_uuid"))
    records = {}
    for image, uuid in pairs:
        path = out / Path(image).stem
        capture(image, observed, inspector, cache, (ALIAS, IMPLEMENTATION), path)
        record = json.loads((path / "capture.json").read_text())
        if record["host_os_build"] != HOST_BUILD or record["image_uuid"] != runtime[uuid]:
            raise ValueError(f"{arch}: changed stack-probe runtime identity for {image}")
        records[image] = record["requested_exports"]

    expected = f"[re-export] {ALIAS} ({IMPLEMENTATION} from libsystem_pthread)"
    definition = records[PTHREAD][IMPLEMENTATION]
    if (records[COMPILER_RT] != {ALIAS: [expected], IMPLEMENTATION: []}
            or records[PTHREAD][ALIAS] or len(definition) != 1
            or not re.fullmatch(rf"0x[0-9A-Fa-f]+\s+{IMPLEMENTATION}", definition[0])):
        raise ValueError(f"{arch}: changed stack-probe runtime provider or forwarding record: {records}")


def check_links(arch, llvm, reference, candidate, out):
    nm = llvm / "bin/llvm-nm"
    for minimum in MINIMA:
        obj = out / f"{minimum}.o"
        run(llvm / "bin/clang", ["--no-default-config", "-target", f"{arch}-apple-macos{minimum}",
                                "-nostdinc", "-O2", "-fno-stack-protector", "-c", FIXTURE, "-o", obj], out)
        if set(run(nm, ["-uj", obj], out).splitlines()) != {ALIAS, IMPLEMENTATION}:
            raise ValueError(f"{arch} {minimum}: stack-probe client imports changed")
        options = SimpleNamespace(llvm=llvm, arch=arch, minimum=minimum, sdk_version="26.5", builtins=[])
        records = {side: link(root, obj, out / f"{minimum}-{side}.dylib", options)
                   for side, root in (("reference", reference), ("candidate", candidate))}
        report = {"object_sha256": digest(obj), **records}
        (out / f"{minimum}.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        expected = {
            "dependencies": [["LC_LOAD_DYLIB", SYSTEM, "1356.0.0", "1.0.0"]],
            "imports": sorted(f"(undefined) external {symbol} (from libSystem)"
                              for symbol in (ALIAS, IMPLEMENTATION, "dyld_stub_binder")),
            "platform": [("platform", "macos"), ("sdk", "26.5"), ("minos", minimum)],
        }
        differences = {side: item["result"] for side, item in records.items() if item["result"] != expected}
        if differences:
            raise ValueError(f"{arch} {minimum}: changed stack-probe client link: {differences}")


def qualify(args):
    llvm = args.llvm.resolve(strict=True)
    projection(llvm, read_lock(PIN))
    for name, expected in PTHREAD_SOURCE["files"].items():
        if digest(args.source / name) != expected:
            raise ValueError(f"pinned pthread source changed: {name}")

    version = args.reference / "System/Library/CoreServices/SystemVersion.plist"
    reference_build = plistlib.loads(version.read_bytes())["ProductBuildVersion"]
    if reference_build != REFERENCE_BUILD:
        raise ValueError(f"stack-probe reference build {reference_build} differs from {REFERENCE_BUILD}")

    check_roles(args.reference, llvm, "export", None)
    check_roles(args.candidate, llvm, "reexport", "text")
    out = args.out.resolve()
    out.mkdir(parents=True)
    caches = {"arm64": args.arm64_cache, "x86_64": args.x86_64_cache}
    for arch in ARCHES:
        check_runtime(arch, caches[arch], args.inspector, out / arch / "runtime")
        check_links(arch, llvm, args.reference, args.candidate, out / arch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("llvm", "source", "reference", "candidate", "inspector", "arm64-cache", "x86-64-cache", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        qualify(args)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"stack-probe qualification needs review: {exc}\n")


if __name__ == "__main__":
    main()
