#!/usr/bin/env python3
"""Compose standalone Apple OSS C headers with selected SDK Gen link assets.

Only SDKSettings metadata and .tbd files cross from the reference SDK by
default. Other framework headers must be named explicitly. This script never
copies reference usr/include headers.
"""

import argparse
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


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
    parser.add_argument("--corefoundation-tbd-override", type=Path,
                        help="optional external CoreFoundation link-stub amendment")
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
    for path in (c_root, base, args.libcxx_headers):
        if not path.is_dir():
            parser.error(f"directory not found: {path}")
    if not args.libcxx_archive.is_file():
        parser.error("libc++ archive not found")

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
    for name in args.framework_header:
        if name == "CoreFoundation":
            parser.error("CoreFoundation headers are owned by the C installation")
        relative = Path("System/Library/Frameworks") / f"{name}.framework/Headers"
        if not (base / relative).is_dir():
            parser.error(f"framework headers not found: {relative}")
        shutil.copytree(base / relative, out / relative)

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
    shutil.copytree(args.libcxx_headers, out / "usr/include/c++/v1")
    copy_file(args.libcxx_archive,
              out / "usr/lib/libc++_llvm23_full.a", log, "hermetic-llvm-libcxx")

    manifest = out.parent / (out.name + ".composition.tsv")
    with manifest.open("w") as stream:
        stream.write("destination\tprovenance\tsha256\n")
        for destination, provenance, digest in log:
            stream.write(f"{destination}\t{provenance}\t{digest}\n")
    print(f"{out}: {len(log)} copied SDK Gen metadata/TBD and libc++ files")


if __name__ == "__main__":
    main()
