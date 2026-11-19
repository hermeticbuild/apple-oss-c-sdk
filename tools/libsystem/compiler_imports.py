"""Generate target objects and inventory implicit imports of compiler fixtures."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from .emit import ARCHES, version


def collect(llvm, minimum, fixture, out):
    minimum = version(minimum)
    if out.exists():
        raise ValueError(f"choose a new output directory: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out.parent) as work:
        stage = Path(work) / "objects"
        stage.mkdir()
        rows = []
        for arch in ARCHES:
            for optimization in ("O0", "O2"):
                obj = stage / f"{arch}-{optimization}.o"
                subprocess.run([llvm / "bin/clang", "--no-default-config", "-target",
                                f"{arch}-apple-macos{minimum}", "-" + optimization,
                                "-nostdinc", "-std=c17", "-x", "c", "-c", "-", "-o", obj],
                               input=fixture.read_bytes(), env={"LC_ALL": "C"}, check=True)
                names = subprocess.check_output([llvm / "bin/llvm-nm", "-uj", obj], text=True)
                rows.append({"arch": arch, "optimization": optimization, "object": obj.name,
                             "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
                             "undefined": sorted(set(names.splitlines()))})
        report = {"schema": 1, "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
                  "minimum": minimum, "cases": rows}
        (stage / "imports.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        stage.rename(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm", required=True, type=Path)
    parser.add_argument("--minimum", required=True)
    parser.add_argument("--fixture", type=Path, default=Path(__file__).parent / "fixtures/division.c")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        collect(args.llvm.resolve(), args.minimum, args.fixture, args.out)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"compiler imports: {exc}\n")


if __name__ == "__main__":
    main()
