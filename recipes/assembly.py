"""Collect independent header recipes, then install one unambiguous owner per path."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Header:
    data: bytes
    owner: str
    origin: str
    selection: str


class Assembly:
    def __init__(self, selected: set[str]):
        self.selected = selected
        self.files: dict[str, Header] = {}

    def add(self, owner: str, path: str, data: bytes, origin: str,
            selection: str) -> None:
        if path not in self.selected:
            raise ValueError(f"header outside default profile: {path}")
        previous = self.files.get(path)
        if previous is not None:
            raise ValueError(f"multiple owners for {path}: {previous.owner}, {owner}")
        self.files[path] = Header(data, owner, origin, selection)

    def write(self, root: Path, *, complete: bool) -> None:
        if complete and set(self.files) != self.selected:
            missing = sorted(self.selected - set(self.files))
            raise ValueError(f"profile missing {len(missing)} headers: {missing[:3]}")
        if root.exists():
            raise ValueError(f"output already exists: {root}")
        for path, header in sorted(self.files.items()):
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(header.data)
        if complete:
            (root / "header-provenance.json").write_text(json.dumps({
                "schema": 2,
                "files": {path: {
                    "origin": header.origin,
                    "selection": header.selection,
                    "sha256": hashlib.sha256(header.data).hexdigest(),
                } for path, header in sorted(self.files.items())},
            }, indent=2, sort_keys=True) + "\n")
            (root / "header-owners.json").write_text(json.dumps({
                "schema": 1,
                "files": {path: {
                    "owner": header.owner,
                    "origin": header.origin,
                    "selection": header.selection,
                } for path, header in sorted(self.files.items())},
            }, indent=2, sort_keys=True) + "\n")
