"""Inventory the normal macOS component selection policy from pinned Apple OSS."""

import argparse
import hashlib
import json
from pathlib import Path
import re


LOCK = Path(__file__).resolve().parent / "data" / "macosx26.5" / "libsystem-source.json"
LINK_NAME = re.compile(r"[a-zA-Z0-9_]+")


def read_source(source, files):
    contents = {}
    for name, expected in sorted(files.items()):
        path = (source / name).resolve()
        if not path.is_relative_to(source):
            raise ValueError(f"source path leaves the Libsystem tree: {name}")
        data = path.read_bytes()
        found = hashlib.sha256(data).hexdigest()
        if found != expected:
            raise ValueError(f"changed Libsystem source {name}: expected {expected}, got {found}")
        contents[name] = data.decode("utf-8")
    return contents


def component_slots(contents):
    slots = []
    owners = {}
    for path, required in (("requiredlibs", True), ("optionallibs", False)):
        for line, row in enumerate(contents[path].splitlines(), 1):
            alternatives = row.split()
            if not alternatives or any(not LINK_NAME.fullmatch(name) for name in alternatives):
                raise ValueError(f"{path}:{line}: invalid component row: {row!r}")
            for name in alternatives:
                if name in owners:
                    raise ValueError(f"{path}:{line}: duplicate link name {name} (first seen at {owners[name]})")
                owners[name] = f"{path}:{line}"
            slots.append({
                "required": required,
                "alternatives": alternatives,
                "source": {"path": path, "line": line},
            })
    return slots


def config_setting(config, name):
    matches = re.findall(rf"(?m)^{name} = (.+)$", config)
    if len(matches) != 1:
        raise ValueError(f"expected one {name} assignment in Libsystem.xcconfig")
    return matches[0]


def inventory(source, lock):
    contents = read_source(source.resolve(), lock["project"]["files"])
    config = contents["Libsystem.xcconfig"]
    return {
        "schema": 1,
        "scope": {
            "sdk": lock["sdk"],
            "platform": "macos",
            "build_variant": "normal",
            "client_architectures": ["arm64", "x86_64"],
        },
        "source": lock,
        "umbrella": {
            "product": "libSystem.B.dylib",
            "install_path": "/usr/lib/libSystem.B.dylib",
            "install_name": None,
            "runtime_alias": {"path": "/usr/lib/libSystem.dylib", "target": "libSystem.B.dylib"},
            "current_version": None,
            "compatibility_version": None,
            "version_settings": {
                name: config_setting(config, name)
                for name in ("DYLIB_CURRENT_VERSION", "CURRENT_VERSION_STRING_", "CURRENT_VERSION_STRING_YES")
            },
            "install_name_settings": {
                name: config_setting(config, name)
                for name in ("LD_DYLIB_INSTALL_NAME", "DYLIB_INSTALL_NAME_EXECUTABLE_PATH")
            },
        },
        "linker_rule": {
            "source": "xcodescripts/linker_arguments.sh",
            "input_precedence": [
                {
                    "directory": "/usr/lib/system",
                    "extensions": ["dylib", "tbd", "api", "spi"],
                    "link_mode": "reexport",
                },
                {
                    "directory": "/usr/local/lib/system",
                    "extensions": ["a"],
                    "link_mode": "force_load",
                },
            ],
            "select_first_alternative_with_slice": True,
            "require_all_required_rows": True,
        },
        "component_slots": component_slots(contents),
        "unresolved": [
            "Build input presence and the selected alternatives and link modes for each architecture.",
            "Selected dynamic install names and the deployed reexport edges for each architecture.",
            "The deployed umbrella install name, current version and compatibility version.",
            "Component versions, nested reexports and symbol export specifications.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="materialized Libsystem-1356 source root")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        lock = json.loads(LOCK.read_text())
        result = inventory(args.source, lock)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"component graph: {exc}\n")


if __name__ == "__main__":
    main()
