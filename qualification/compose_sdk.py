#!/usr/bin/env python3
"""Compose standalone Apple OSS C headers with selected SDK Gen link assets.

Only SDKSettings metadata and .tbd files cross from the reference SDK by
default. Other framework headers must be named explicitly. This script never
copies reference usr/include headers.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def copy_file(source: Path, destination: Path, log: list[tuple[str, str, str]],
              provenance: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    log.append((str(destination), provenance + ":" + str(source),
                hashlib.sha256(destination.read_bytes()).hexdigest()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c-root", required=True, type=Path)
    parser.add_argument("--reference-sdk", required=True, type=Path)
    parser.add_argument("--libcxx-headers", required=True, type=Path)
    parser.add_argument("--libcxx-archive", required=True, type=Path)
    parser.add_argument("--libunwind-headers", required=True, type=Path,
                        help="pinned LLVM source libunwind/include directory")
    parser.add_argument("--corefoundation-tbd-override", type=Path,
                        help="optional external CoreFoundation link-stub amendment")
    parser.add_argument("--corefoundation-c-root", type=Path,
                        help="full Apple OSS C installation supplying CoreFoundation headers")
    parser.add_argument("--overlay-reference", action="store_true",
                        help="secondary proof: overlay C headers onto the full reference SDK")
    parser.add_argument("--framework-header", action="append", default=[],
                        help="non-C framework name whose generated headers are needed")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    c_root = args.c_root.resolve()
    base = args.reference_sdk.resolve()
    out = args.out.absolute()
    if out.exists():
        parser.error("output already exists")
    for path in (c_root, base, args.libcxx_headers, args.libunwind_headers):
        if not path.is_dir():
            parser.error(f"directory not found: {path}")
    if not args.libcxx_archive.is_file():
        parser.error("libc++ archive not found")
    unwind_lock = json.loads((ROOT / "inputs/llvm-libunwind-headers.json").read_text())
    for name, expected in unwind_lock["sha256"].items():
        source = args.libunwind_headers / name
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            parser.error(f"LLVM libunwind header differs from pinned source: {name}")

    if args.overlay_reference:
        # Exclude the reference's C++ headers so only the supplied LLVM libc++
        # headers can satisfy C++ includes in the secondary composition.
        def ignore_reference_cxx(directory: str, names: list[str]) -> set[str]:
            if Path(directory) == base / "usr/include":
                return {"c++"} & set(names)
            return set()

        shutil.copytree(base, out, symlinks=True, ignore=ignore_reference_cxx)
        shutil.copytree(c_root, out, symlinks=True, dirs_exist_ok=True)
    else:
        shutil.copytree(c_root, out, symlinks=True)
    # The owner index covers the standalone C installation only. The composed
    # provenance below also covers CoreFoundation and LLVM runtime headers.
    c_owner_index = out / "header-owners.json"
    if c_owner_index.is_file():
        c_owner_index.rename(out / "c-header-owners.json")
    log: list[tuple[str, str, str]] = []
    for name in ("SDKSettings.json", "SDKSettings.plist"):
        if (base / name).is_file():
            copy_file(base / name, out / name, log, "sdk-gen-metadata")

    for relative_root in ("usr/lib", "System/Library/Frameworks"):
        for source in sorted((base / relative_root).rglob("*.tbd")):
            relative = source.relative_to(base)
            copy_file(source, out / relative, log, "sdk-gen-tbd")

    if args.overlay_reference and args.framework_header:
        parser.error("--framework-header is for restricted composition only")
    if args.corefoundation_c_root and "CoreFoundation" in args.framework_header:
        parser.error("choose one CoreFoundation header source")
    for name in args.framework_header:
        relative = Path("System/Library/Frameworks") / f"{name}.framework/Headers"
        if not (base / relative).is_dir():
            parser.error(f"framework headers not found: {relative}")
        for source in sorted((base / relative).rglob("*")):
            if source.is_file():
                copy_file(source, out / source.relative_to(base), log,
                          "sdk-gen-framework-header")

    if args.corefoundation_c_root:
        cf_root = args.corefoundation_c_root.resolve()
        relative = Path("System/Library/Frameworks/CoreFoundation.framework/Headers")
        source = cf_root / relative
        if not source.is_dir():
            parser.error(f"Apple OSS CoreFoundation headers not found: {source}")
        cf_manifest = json.loads((cf_root / "header-provenance.json").read_text())
        expected = {name for name in cf_manifest["files"]
                    if name.startswith(relative.as_posix() + "/")}
        present = {path.relative_to(cf_root).as_posix()
                   for path in source.rglob("*") if path.is_file() or path.is_symlink()}
        if not expected or present != expected:
            parser.error("CoreFoundation file set differs from provenance")
        if any(path.is_symlink() for path in source.rglob("*")):
            parser.error("CoreFoundation source contains a symlink")
        shutil.copytree(source, out / relative, dirs_exist_ok=True)

    # hermetic-llvm's osx extension requests both public and private glob
    # patterns for each default framework. SDK Gen has no private framework
    # trees; a non-header marker lets bsdtar match those empty patterns.
    for name in ("CoreFoundation", "Foundation", "Kernel", "OSLog", "Security",
                 "SystemConfiguration"):
        for category in ("Frameworks", "PrivateFrameworks"):
            framework = (out / "System/Library" / category /
                         f"{name}.framework")
            if not framework.exists():
                framework.mkdir(parents=True)
                (framework / ".empty-for-bsdtar").write_text("")

    if args.corefoundation_tbd_override:
        if not args.corefoundation_tbd_override.is_file():
            parser.error("CoreFoundation TBD override not found")
        copy_file(args.corefoundation_tbd_override,
                  out / "System/Library/Frameworks/CoreFoundation.framework/CoreFoundation.tbd",
                  log, "external-tbd-amendment")

    # Keep unwind headers as an explicit LLVM runtime layer. The Apple C tree
    # remains independently reproducible, while the composed SDK uses one
    # coherent libunwind header set from the LLVM source already fetched by
    # hermetic-llvm.
    c_provenance = out / "header-provenance.json"
    provenance = json.loads(c_provenance.read_text())
    if args.corefoundation_c_root:
        for relative, record in cf_manifest["files"].items():
            if relative.startswith("System/Library/Frameworks/CoreFoundation.framework/Headers/"):
                copied = out / relative
                if not copied.is_file() or hashlib.sha256(copied.read_bytes()).hexdigest() != record["sha256"]:
                    parser.error(f"CoreFoundation differs from provenance: {relative}")
                provenance["files"][relative] = record
    for name, expected in unwind_lock["sha256"].items():
        source = args.libunwind_headers / name
        relative = f"usr/include/{name}"
        copy_file(source, out / relative, log, "llvm-libunwind")
        provenance["files"][relative] = {
            "origin": f"llvm-libunwind:llvmorg-{unwind_lock['llvm_version']}/libunwind/include/{name}",
            "selection": "inputs/llvm-libunwind-headers.json",
            "sha256": expected,
        }
    c_provenance.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    shutil.copytree(args.libcxx_headers, out / "usr/include/c++/v1")
    copy_file(args.libcxx_archive,
              out / "usr/lib/libc++_llvm23_full.a", log, "hermetic-llvm-libcxx")

    manifest = out.parent / (out.name + ".composition.tsv")
    with manifest.open("w") as stream:
        stream.write("destination\tprovenance\tsha256\n")
        for destination, provenance, digest in log:
            stream.write(f"{destination}\t{provenance}\t{digest}\n")
    print(f"{out}: {len(log)} copied SDK Gen link assets and LLVM runtime files")


if __name__ == "__main__":
    main()
