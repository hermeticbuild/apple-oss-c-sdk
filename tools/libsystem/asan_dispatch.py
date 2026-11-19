"""Qualify the two private dispatch functions needed by Darwin AddressSanitizer."""

import json
from pathlib import Path
import re

from .component_graph import read_source
from .emit import ARCHES, version
from .sanitizer_abi import excerpt, qualify


RECORD = Path(__file__).parent / "data/macosx26.5/asan-dispatch.json"


def consumer_source(group, compiler_rt):
    interceptors = excerpt(compiler_rt, group["consumer_interceptors"])
    return "\n".join([
        excerpt(compiler_rt, group["consumer_types"]),
        # The Darwin interceptor declares the original with C linkage and takes
        # its address for interposition, even if the wrapper calls a different symbol.
        '#define INTERCEPTOR(ret, func, ...) extern "C" ret func(__VA_ARGS__);',
        re.sub(r" \{$", "", interceptors, flags=re.MULTILINE),
        "#undef INTERCEPTOR",
        *(f"decltype(&{name}) reference_{name} = &{name};" for name in group["c_names"]),
        "",
    ])


def install(sdk, compiler_rt, libdispatch, llvm, work, images, inventories, *, minimum):
    evidence = json.loads(RECORD.read_bytes())
    if sdk != evidence["sdk"]:
        raise ValueError(f"the reviewed ASan dispatch ABI applies only to {evidence['sdk']}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed ASan dispatch ABI covers macOS deployment minima 11.0–26.5")
    if set(inventories) != set(ARCHES):
        raise ValueError("ASan dispatch ABI requires both client inventories")

    consumer = read_source(compiler_rt.resolve(), evidence["sources"]["compiler-rt"]["files"])
    read_source(libdispatch.resolve(), evidence["sources"]["libdispatch"]["files"])
    group, = evidence["groups"]
    provider = group["provider"]
    kind = group["kind"]
    symbols = ["_" + name for name in group["c_names"]]
    owners = [image["slices"] for image in images if image["install_name"] == provider]
    if len(owners) != 1 or set(owners[0]) != set(ARCHES):
        raise ValueError("ASan dispatch ABI requires one libdispatch component with both target slices")

    for image in images:
        owner = image["install_name"]
        for arch, part in image["slices"].items():
            for symbol in symbols:
                if symbol in part.get("symbol_reexports", {}) or (
                    symbol in part["exports"] and (owner != provider or part["exports"][symbol] != kind)
                ):
                    raise ValueError(f"{arch}: conflicting ASan dispatch definition for {symbol} in {owner}")

    client = qualify(evidence, consumer_source(group, consumer), llvm, work, minimum)
    dispatch = owners[0]
    for arch in ARCHES:
        dispatch[arch]["exports"].update(dict.fromkeys(symbols, kind))
        inventories[arch].extend(
            {"symbol": symbol, "kind": "function", "header": group["consumer_interceptors"]["file"]}
            for symbol in symbols
        )
    return {**evidence, "minimum": minimum, "client": client}
