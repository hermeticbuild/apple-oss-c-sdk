"""Checked-in C installation path selection."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT / "inputs/profiles/default-headers.txt"


def selected_paths(manifest: Path = DEFAULT) -> list[str]:
    paths = [line.strip() for line in manifest.read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("profile must contain unique header paths")
    for path in paths:
        if not path.startswith("usr/include/") or ".." in Path(path).parts:
            raise ValueError(f"invalid C header path: {path}")
    return paths
