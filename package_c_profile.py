#!/usr/bin/env python3
"""Package the checked-in minimal C-header profile from a full OSS installation."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT / "inputs/profiles/default-headers.txt"


def selected_paths(manifest: Path) -> list[str]:
    paths = [line.strip() for line in manifest.read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("profile must contain unique header paths")
    for path in paths:
        if not path.startswith("usr/include/") or ".." in Path(path).parts:
            raise ValueError(f"invalid C header path: {path}")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installation", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--profile", type=Path, default=DEFAULT)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists")
    source = args.installation.resolve()
    provenance = json.loads((source / "header-provenance.json").read_text())
    files = {}
    for relative in selected_paths(args.profile):
        src = source / relative
        if not src.is_file() or relative not in provenance["files"]:
            parser.error(f"missing source or provenance: {relative}")
        record = provenance["files"][relative]
        if hashlib.sha256(src.read_bytes()).hexdigest() != record["sha256"]:
            parser.error(f"source differs from provenance: {relative}")
        dst = args.out / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        files[relative] = record
    (args.out / "header-provenance.json").write_text(
        json.dumps({"schema": provenance["schema"], "files": files},
                   indent=2, sort_keys=True) + "\n")
    print(f"{args.out}: {len(files)} C headers")


if __name__ == "__main__":
    main()
