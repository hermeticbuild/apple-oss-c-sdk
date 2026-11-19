"""Install the qualified macOS NetName MIG client interface."""

import json
from pathlib import Path
import re

from .component_graph import read_source
from .emit import ARCHES, version


RECORD = Path(__file__).parent / "data/macosx26.5/netname.json"
DEFINITIONS = "libsyscall/mach/servers/netname.defs"
KERNEL = "/usr/lib/system/libsystem_kernel.dylib"
KIND = "text.global"


def install(sdk, xnu_source, images, inventories, *, minimum):
    evidence = json.loads(RECORD.read_bytes())
    if sdk != evidence["sdk"]:
        raise ValueError(f"the reviewed NetName recipe applies only to {evidence['sdk']}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed NetName recipe covers macOS deployment minima 11.0–26.5")

    contents = read_source(xnu_source.resolve(), evidence["source"]["files"])
    # The pinned definitions specify only a server prefix. MIG keeps the client names verbatim.
    names = re.findall(r"(?m)^routine (netname_[a-z_]+)\(", contents[DEFINITIONS])
    if len(set(names)) != 4 or len(names) != 4:
        raise ValueError("expected all four NetName MIG client routines")
    symbols = sorted("_" + name for name in names)

    owners = [image["slices"] for image in images if image["install_name"] == KERNEL]
    if len(owners) != 1 or set(owners[0]) != set(ARCHES):
        raise ValueError("NetName requires one libsystem_kernel component with both target slices")

    if set(inventories) != set(ARCHES):
        raise ValueError("NetName requires an inventory for both target slices")

    for image in images:
        owner = image["install_name"]
        for arch, part in image["slices"].items():
            for symbol in symbols:
                if symbol in part.get("symbol_reexports", {}) or (
                    symbol in part["exports"] and (owner != KERNEL or part["exports"][symbol] != KIND)
                ):
                    raise ValueError(f"{arch}: conflicting NetName definition for {symbol} in {owner}")

    kernel_slices = owners[0]
    for arch in ARCHES:
        kernel_slices[arch]["exports"].update(dict.fromkeys(symbols, KIND))
        inventories[arch].extend(
            {"symbol": symbol, "kind": "function", "header": evidence["source"]["generated_public_header"]}
            for symbol in symbols
        )
    return {**evidence, "minimum": minimum, "provider": KERNEL, "kind": KIND, "symbols": symbols}
