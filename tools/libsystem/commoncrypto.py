"""Install link metadata for the published macOS CommonCrypto export list."""

import hashlib
import json
from pathlib import Path
import re

from .component_graph import read_source
from .emit import ARCHES, KINDS, version


RECORD = Path(__file__).parent / "data/macosx26.5/commoncrypto.json"
IMAGE = "/usr/lib/system/libcommonCrypto.dylib"
EXPORTS = "exports.exp-in"
EXPORT_NAME = re.compile(r"_[A-Za-z0-9_]+")
DATA_DEFINITION = re.compile(r"(?m)^const [^\n=]+? ([A-Za-z_][A-Za-z0-9_]*) = ")


def published_exports(source, evidence):
    contents = read_source(source.resolve(), evidence["source"]["files"])
    # In this pinned revision the Xcode export preprocessor sees only
    # unconditional names. Reject any unexpected syntax instead of guessing
    # what an upgraded project's build settings would do.
    names = contents[EXPORTS].splitlines()
    expected = evidence["qualification"]["exports_per_slice"]
    if len(names) != expected or len(set(names)) != expected or not all(map(EXPORT_NAME.fullmatch, names)):
        raise ValueError("invalid pinned CommonCrypto published export list")

    data = set()
    for path in evidence["source"]["data_definition_files"]:
        data.update("_" + name for name in DATA_DEFINITION.findall(contents[path]))
    if len(data) != evidence["qualification"]["data_exports_per_slice"] or not data.issubset(names):
        raise ValueError("unexpected CommonCrypto global data definitions")
    exports = {name: "data.global" if name in data else "text.global" for name in sorted(names)}
    canonical = json.dumps(exports, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest() != evidence["qualification"]["runtime_symbol_kinds_sha256"]:
        raise ValueError("CommonCrypto source classification differs from the qualified runtime symbol kinds")
    return exports


def install(sdk, commoncrypto_source, images, inventories, *, minimum):
    evidence = json.loads(RECORD.read_bytes())
    if sdk != evidence["sdk"]:
        raise ValueError(f"the reviewed CommonCrypto export list applies only to {evidence['sdk']}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed CommonCrypto list covers macOS deployment minima 11.0–26.5")
    if set(inventories) != set(ARCHES):
        raise ValueError("CommonCrypto requires both client inventories")

    exports = published_exports(commoncrypto_source, evidence)
    owners = [image["slices"] for image in images if image["install_name"] == IMAGE]
    if len(owners) != 1 or set(owners[0]) != set(ARCHES):
        raise ValueError("CommonCrypto requires one component with both target slices")

    for image in images:
        owner = image["install_name"]
        for arch, part in image["slices"].items():
            forwards = part.get("symbol_reexports", {})
            if owner == IMAGE and (forwards or part["exports"].keys() - exports.keys()):
                raise ValueError(f"{arch}: extra definition in the CommonCrypto component")
            for name, kind in exports.items():
                if name in forwards or (name in part["exports"] and
                                        (owner != IMAGE or part["exports"][name] != kind)):
                    raise ValueError(f"{arch}: conflicting CommonCrypto definition for {name} in {owner}")

    for arch in ARCHES:
        owners[0][arch]["exports"].update(exports)
        inventories[arch].extend(
            {"symbol": name, "kind": KINDS[kind], "header": "CommonCrypto/" + EXPORTS}
            for name, kind in exports.items()
        )
    return {**evidence, "minimum": minimum, "provider": IMAGE, "exports": exports}
