"""Fallback copies for producers without a qualified install step."""

import csv
from pathlib import Path

from .assembly import Assembly
from .public_sources import public_xcode_selection


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "recipes/copies.tsv"


def produce(assembly: Assembly) -> None:
    with MANIFEST.open(newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            path = row["install_path"]
            source = row["source"]
            if not source.startswith("sources/") or ".." in Path(source).parts:
                raise ValueError(f"invalid copy source: {source}")
            source_file = ROOT / source
            owner = Path(source).parts[1]
            selection = row["selection"]
            if selection.endswith(":Public"):
                if selection != public_xcode_selection(source_file):
                    raise ValueError(f"Xcode public phase does not select {source}")
            assembly.add(owner, path, source_file.read_bytes(), source,
                         selection)
