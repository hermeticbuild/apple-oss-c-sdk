"""Compare effective macOS libSystem bindings for the two supported client architectures."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from tools.header_manifest import read_header_manifest
from .classify_sdk_header_links import probe_bindings, run
from .libsystem import write_json
from .libsystem_tbd import read_stub
from .lookup_tbd_symbols import OBJC_PREFIXES


# Input slices supply candidate spellings. The linker chooses which slice a
# client can actually use. A subtype in this list is never a client target.
SLICES = {"arm64": ("arm64-macos", "arm64e-macos"), "x86_64": ("x86_64-macos", "x86_64h-macos")}


def spellings(stub, arch):
    owners = defaultdict(set)
    for library, slices in stub.libraries.items():
        for target in SLICES[arch]:
            if target not in slices:
                continue
            for (encoding, name), attrs in slices[target].symbols.items():
                if attrs["role"] == "undefined" or name.startswith("$ld$"):
                    continue
                for prefix in OBJC_PREFIXES.get(encoding, ("",)):
                    owners[prefix + name].add(library)
    return owners


def resolves_without_libraries(tools, directory, arch, minimum, version, name):
    """Require a real relocation and a strict, library-free dylib link."""
    if not re.fullmatch(r"[_A-Za-z][_A-Za-z0-9.$]*", name):
        return False
    obj = directory / "relocation.o"
    dylib = directory / "relocation.dylib"
    run([tools / "clang", "--no-default-config", "-target", f"{arch}-apple-macos{minimum}",
         "-isysroot", directory, "-x", "assembler", "-c", "-", "-o", obj],
        input=f".data\n.quad {name}\n")
    if run([tools / "llvm-nm", "-uj", obj]).splitlines() != [name]:
        return False
    try:
        run([tools / "ld64.lld", "-Z", "-dylib", "-arch", arch, "-platform_version", "macos",
             minimum, version, "-syslibroot", directory, "-undefined", "error", "-fixup_chains",
             obj, "-o", dylib])
    except ValueError as error:
        if f"ld64.lld: error: undefined symbol: {name}" in str(error).splitlines():
            return False
        raise
    return not run([tools / "llvm-nm", "-uj", dylib]).strip()


def coverage(args):
    tools = args.llvm.resolve(strict=True) / "bin"
    roots = {"reference": args.reference.resolve(strict=True), "candidate": args.candidate.resolve(strict=True)}
    settings = (roots["reference"] / "SDKSettings.json").read_bytes()
    version = json.loads(settings)["Version"]
    survey = json.loads(args.survey.read_bytes())
    if survey["sdk"]["settings_sha256"] != hashlib.sha256(settings).hexdigest():
        raise ValueError("header survey was collected from a different reference SDK")
    manifest, _ = read_header_manifest(args.c_install)
    stubs = {}
    hashes = {}
    for side, root in roots.items():
        data = (root / "usr/lib/libSystem.tbd").read_bytes()
        hashes[side] = hashlib.sha256(data).hexdigest()
        stubs[side] = read_stub(data.decode(), tools / "llvm-readtapi")
    cases = []
    for arch in SLICES:
        sources = {side: spellings(stub, arch) for side, stub in stubs.items()}
        headers = survey["symbols"][arch]
        declared = set(headers)
        installed = {name for name in declared if manifest.keys() & headers[name]["headers"]}
        names = sources["reference"].keys() | sources["candidate"].keys() | declared
        for minimum in dict.fromkeys(args.minimum or ("11.0", version)):
            with TemporaryDirectory() as tmp:
                work = Path(tmp)
                bindings = {side: probe_bindings(tools, root, arch, minimum, version, names, work)
                            for side, root in roots.items()}
                undecoded = {name for group in bindings.values() for name, provider in group.items()
                             if provider == "requires-individual-link"}
                local = {name for name in undecoded
                         if all(group[name] == "requires-individual-link" for group in bindings.values())
                         and resolves_without_libraries(tools, work, arch, minimum, version, name)}
            bound = {side: {name for name, provider in group.items() if provider == "libSystem"}
                     for side, group in bindings.items()}
            ref, cand = bound["reference"], bound["candidate"]
            missing = ref - cand
            cases.append({
                "arch": arch, "minimum": minimum, "reference": len(ref), "candidate": len(cand),
                "missing": sorted(missing), "extra": sorted(cand - ref),
                "resolved_without_libraries": sorted(local),
                "requires_individual_link": sorted(undecoded - local),
                "survey_reference": len(ref & declared), "survey_missing": sorted(missing & declared),
                "installed_reference": len(ref & installed), "installed_missing": sorted(missing & installed),
                "missing_by_library": {name: sorted(sources["reference"].get(name, ())) for name in sorted(missing)},
            })
    return {"schema": 1, "sdk_version": version, "stub_sha256": hashes,
            "survey_minimum": survey["minimum"], "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("llvm", "reference", "candidate", "c-install", "survey", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--minimum", action="append", help="repeat to test additional deployment minima")
    args = parser.parse_args()
    try:
        report = coverage(args)
        write_json(args.out, report)
    except (KeyError, OSError, ValueError) as exc:
        parser.exit(2, f"client coverage: {exc}\n")
    for case in report["cases"]:
        print(f"{case['arch']} macOS {case['minimum']}: {len(case['missing'])} missing, "
              f"{len(case['extra'])} extra, {len(case['requires_individual_link'])} require individual links")


if __name__ == "__main__":
    main()
