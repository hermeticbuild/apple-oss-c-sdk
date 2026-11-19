"""Qualify the legacy Intel Darwin imports used by ASan and TSan."""

import json
from pathlib import Path

from .component_graph import read_source
from .emit import ARCHES, version
from .sanitizer_abi import excerpt, qualify


RECORD = Path(__file__).parent / "data/macosx26.5/sanitizer-inode32.json"
INTEL = "x86_64"
KIND = "text.global"


def consumer_source(evidence, compiler_rt):
    # Darwin INTERCEPTOR declares the original with C linkage, then takes its
    # address for interposition. The declaration has no system-header alias.
    source = [
        "struct __sanitizer_dirent;",
        '#define INTERCEPTOR(ret, name, ...) extern "C" ret name(__VA_ARGS__);',
        "#define TSAN_INTERCEPTOR INTERCEPTOR",
    ]
    for item in evidence["interceptors"]:
        source.append("\n".join(line.removesuffix(" {") for line in excerpt(compiler_rt, item).splitlines()))
    for group in evidence["groups"]:
        source.extend(f"decltype(&{name}) reference_{name} = &{name};" for name in group["c_names"])
    return "\n".join([*source, ""])


def install(sdk, source_roots, llvm, work, images, inventories, *, minimum):
    evidence = json.loads(RECORD.read_bytes())
    if sdk != evidence["sdk"]:
        raise ValueError(f"the reviewed sanitizer inode ABI applies only to {evidence['sdk']}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed sanitizer inode ABI covers macOS deployment minima 11.0–26.5")
    if set(source_roots) != set(evidence["sources"]) or set(inventories) != set(ARCHES):
        raise ValueError("sanitizer inode ABI requires pinned Libc, XNU and compiler-rt, and both client slices")
    sources = {name: read_source(source_roots[name].resolve(), pin["files"])
               for name, pin in evidence["sources"].items()}

    providers = {}
    for group in evidence["groups"]:
        provider = group["provider"]
        components = [image["slices"] for image in images if image["install_name"] == provider]
        if len(components) != 1 or set(components[0]) != set(ARCHES):
            raise ValueError(f"sanitizer inode ABI requires one {provider} component with both target slices")
        for name in group["c_names"]:
            symbol = "_" + name
            for arch, suffix in (("arm64", ""), (INTEL, "$INODE64")):
                if components[0][arch]["exports"].get(symbol + suffix) != KIND:
                    raise ValueError(f"{arch}: missing existing sanitizer inode ABI export {symbol}{suffix} in {provider}")
            providers[symbol] = (provider, components[0][INTEL]["exports"])
    for image in images:
        owner = image["install_name"]
        for arch, part in image["slices"].items():
            for symbol, (provider, _) in providers.items():
                for spelling in ([symbol, symbol + "$INODE64"] if arch == INTEL else [symbol]):
                    existing = part["exports"].get(spelling)
                    if spelling in part.get("symbol_reexports", {}) or (
                        existing is not None and (owner != provider or existing != KIND)
                    ):
                        raise ValueError(f"{arch}: conflicting sanitizer inode ABI export {spelling} in {owner}")

    client = qualify(evidence, consumer_source(evidence, sources["compiler-rt"]), llvm, work, minimum)
    for declaration in evidence["interceptors"]:
        for name in declaration["c_names"]:
            symbol = "_" + name
            providers[symbol][1][symbol] = KIND
            inventories[INTEL].append({"symbol": symbol, "kind": "function", "header": declaration["file"]})
    return {**evidence, "minimum": minimum, "client": client}
