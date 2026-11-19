"""Derive the linker interface from Apple's exported Libnotify declarations."""

import hashlib
import json
from pathlib import Path
import re

from .component_graph import read_source
from .emit import ARCHES, KINDS, version


RECORD = Path(__file__).parent / "data/macosx26.5/libnotify.json"
IMAGE = "/usr/lib/system/libsystem_notify.dylib"
KIND = "text.global"
EXPORT = re.compile(r"^OS_EXPORT (?:uint32_t|bool|void) (_?notify_[A-Za-z0-9_]+)\(")


def export_headers(source, evidence):
    contents = read_source(source.resolve(), evidence["source"]["files"])
    headers = {}
    for header, expected in evidence["qualification"]["exports_by_header"].items():
        declarations = [line for line in contents[header].splitlines() if line.startswith("OS_EXPORT ")]
        if len(declarations) != expected:
            raise ValueError(f"unexpected number of exported declarations in {header}")
        for line in declarations:
            match = EXPORT.match(line)
            if not match or "_" + match[1] in headers:
                raise ValueError(f"unexpected exported declaration in {header}: {line}")
            headers["_" + match[1]] = header
    canonical = json.dumps(dict.fromkeys(headers, KIND), sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest() != evidence["qualification"]["runtime_symbol_kinds_sha256"]:
        raise ValueError("Libnotify source declarations differ from qualified runtime exports")
    return headers


def install(sdk, notify_source, images, inventories, *, minimum):
    evidence = json.loads(RECORD.read_bytes())
    if sdk != evidence["sdk"]:
        raise ValueError(f"the reviewed Libnotify interface applies only to {evidence['sdk']}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed Libnotify interface covers macOS deployment minima 11.0–26.5")
    if set(inventories) != set(ARCHES):
        raise ValueError("Libnotify requires both client inventories")

    headers = export_headers(notify_source, evidence)
    exports = dict.fromkeys(sorted(headers), KIND)
    owners = [image["slices"] for image in images if image["install_name"] == IMAGE]
    if len(owners) != 1 or set(owners[0]) != set(ARCHES):
        raise ValueError("Libnotify requires one component with both target slices")

    for image in images:
        owner = image["install_name"]
        for arch, part in image["slices"].items():
            forwards = part.get("symbol_reexports", {})
            for name in exports:
                if name in forwards or (name in part["exports"] and
                                        (owner != IMAGE or part["exports"][name] != KIND)):
                    raise ValueError(f"{arch}: conflicting Libnotify definition for {name} in {owner}")

    for arch in ARCHES:
        owners[0][arch]["exports"].update(exports)
        inventories[arch].extend(
            {"symbol": name, "kind": KINDS[KIND], "header": "Libnotify/" + headers[name]}
            for name in exports
        )
    return {**evidence, "minimum": minimum, "provider": IMAGE, "exports": exports}
