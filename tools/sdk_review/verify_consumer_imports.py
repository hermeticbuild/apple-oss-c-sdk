"""Replay one macOS executable's two-level libSystem imports against two SDKs."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from tools.libsystem.emit import ARCHES, version
from .verify_libsystem_links import inspect, link


def references(imports):
    result = {}
    for line in imports:
        if not line.endswith(" (from libSystem)"):
            continue
        match = re.fullmatch(r"\(undefined\) (weak )?external ([A-Za-z0-9_$.]+) \(from libSystem\)", line)
        if not match:
            raise ValueError(f"unsupported consumer import: {line}")
        symbol = match[2]
        if symbol in result:
            raise ValueError(f"duplicate consumer import: {symbol}")
        result[symbol] = bool(match[1])
    if not result:
        raise ValueError("consumer has no two-level libSystem imports")
    return result


def verify(args):
    tools = args.llvm.resolve() / "bin"
    arches = subprocess.check_output([tools / "llvm-lipo", "-archs", args.binary], text=True).split()
    if arches != [args.arch]:
        raise ValueError(f"select a thin {args.arch} consumer executable; input slices: {arches}")
    metadata = inspect(args.binary, tools)
    platform = dict(metadata["platform"])
    if platform["platform"].lower() != "macos":
        raise ValueError(f"unexpected consumer platform: {platform}")
    args.minimum = version(args.minimum or platform["minos"])
    names = references(metadata["imports"])
    source = [".data", ".p2align 3"]
    for name, weak in sorted(names.items()):
        if weak:
            source.append(".weak_reference " + name)
        source.append(".quad " + name)
    with TemporaryDirectory() as work:
        root = Path(work).resolve()
        obj = root / "references.o"
        subprocess.run([tools / "clang", "--no-default-config", "-target",
                        f"{args.arch}-apple-macos{args.minimum}", "-x", "assembler", "-c", "-", "-o", obj],
                       input="\n".join(source) + "\n", text=True, check=True)
        digest = hashlib.sha256()
        with args.binary.open("rb") as binary:
            for chunk in iter(lambda: binary.read(1024 * 1024), b""):
                digest.update(chunk)
        report = {"schema": 1, "arch": args.arch, "binary": str(args.binary),
                  "consumer_sha256": digest.hexdigest(), "consumer_platform": platform,
                  "minimum": args.minimum, "imports": names}
        for side in ("reference", "candidate"):
            report[side] = link(getattr(args, side), obj, root / side, args)
        reference = report["reference"]["result"]
        if "imports" in reference:
            bound = references(reference["imports"])
            report["unverified_reference_bindings"] = sorted(name for name, weak in names.items()
                                                            if bound.get(name) != weak)
        report["pass"] = report.get("unverified_reference_bindings") == [] and reference == report["candidate"]["result"]
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        return report["pass"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("binary", "candidate", "reference", "llvm", "out"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--arch", choices=ARCHES, required=True)
    parser.add_argument("--minimum", help="default: original executable's LC_BUILD_VERSION minimum")
    parser.add_argument("--sdk-version", required=True)
    parser.set_defaults(builtins=[])
    args = parser.parse_args()
    try:
        passed = verify(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"consumer imports: {exc}\n")
    if not passed:
        parser.exit(1, f"consumer import differences: {args.out}\n")


if __name__ == "__main__":
    main()
