"""Derive the macOS libSystem link names from the pinned Apple install step."""

import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from .component_graph import LOCK, read_source


SCRIPT = "xcodescripts/create_dylib_symlinks.sh"
UMBRELLA = "libSystem.dylib"
VERSIONED = "libSystem.B.dylib"


def install_compat_links(libsystem_source: Path, stub_directory: Path) -> dict[str, str]:
    """Install the script's relative link names as TBD symlinks in usr/lib."""
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    script = read_source(libsystem_source.resolve(), {SCRIPT: lock["project"]["files"][SCRIPT]})[SCRIPT]
    with TemporaryDirectory(prefix="libsystem-compat-") as staging:
        result = subprocess.run(
            ["/bin/bash", "-s", "--", staging, "install", "normal"],
            input=script, encoding="utf-8", capture_output=True, cwd=staging,
            env={"PATH": "/usr/bin:/bin", "PLATFORM_NAME": "macosx"},
        )
        if result.returncode:
            raise ValueError(f"Libsystem compatibility link install failed: {result.stderr.strip()}")

        library = Path(staging) / "usr/lib"
        umbrella = library / UMBRELLA
        if not umbrella.is_symlink() or os.readlink(umbrella) != VERSIONED:
            raise ValueError(f"Libsystem script did not link {UMBRELLA} to {VERSIONED}")

        links = {}
        for path in sorted(library.iterdir()):
            expected = VERSIONED if path == umbrella else UMBRELLA
            if (not re.fullmatch(r"lib[A-Za-z0-9_.+-]+\.dylib", path.name) or
                    not path.is_symlink() or os.readlink(path) != expected):
                raise ValueError(f"unexpected output of Libsystem compatibility link install: {path.name}")
            links[path.with_suffix(".tbd").name] = Path(expected).with_suffix(".tbd").name

    for name in links:
        destination = stub_directory / name
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"Libsystem compatibility link would replace {destination}")
    for name, target in links.items():
        (stub_directory / name).symlink_to(target)
    return {f"usr/lib/{name}": target for name, target in links.items()}
