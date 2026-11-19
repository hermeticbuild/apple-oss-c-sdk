"""Resolve a reviewed macOS component graph and render a multi-library TBD v5."""

from collections import defaultdict
from pathlib import PurePosixPath
import re

ARCHES = ("arm64", "x86_64")
SYSTEM = "/usr/lib/libSystem.B.dylib"
KINDS = {
    "text.global": "function",
    "text.weak": "function",
    "data.global": "data",
    "data.weak": "data",
    "data.thread_local": "tls",
}


def fields(record, expected, context):
    if not isinstance(record, dict) or set(record) != set(expected):
        raise ValueError(f"{context}: expected fields {sorted(expected)}")


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,2}", value):
        raise ValueError(f"invalid version: {value!r}")
    return value


def library_document(image, minimum):
    fields(image, ("install_name", "current_version", "compatibility_version", "slices"), "image")
    name = image["install_name"]
    if not isinstance(name, str) or not name.startswith("/usr/lib/") or ".." in PurePosixPath(name).parts:
        raise ValueError(f"unsupported install name: {name!r}")
    slices = image["slices"]
    if not isinstance(slices, dict) or not slices or set(slices) - set(ARCHES):
        raise ValueError(f"{name}: unsupported target slices")
    document = {
        "install_names": [{"name": name}],
        "current_versions": [{"version": version(image["current_version"])}],
        "compatibility_versions": [{"version": version(image["compatibility_version"])}],
        "target_info": [],
    }
    edge_targets = defaultdict(list)
    for arch, target_slice in sorted(slices.items()):
        required = {"exports", "reexports"}
        if "symbol_reexports" in target_slice:
            required.add("symbol_reexports")
        fields(target_slice, required, f"{name} {arch}")
        target = arch + "-macos"
        document["target_info"].append({"target": target, "min_deployment": minimum})
        edges = target_slice["reexports"]
        if not isinstance(edges, list) or not all(isinstance(edge, str) for edge in edges) or len(edges) != len(set(edges)):
            raise ValueError(f"{name} {arch}: invalid or repeated reexport")
        for edge in edges:
            edge_targets[edge].append(target)
        for field, role in (("exports", "exported_symbols"), ("symbol_reexports", "reexported_symbols")):
            group = {"targets": [target]}
            symbols = target_slice.get(field, {})
            if not isinstance(symbols, dict):
                raise ValueError(f"{name} {arch}: {field} must map names to symbol kinds")
            for symbol, description in sorted(symbols.items()):
                kind = description
                if field == "symbol_reexports":
                    fields(description, ("kind", "target_library", "target_symbol"), f"{name} {arch} {symbol}")
                    kind = description["kind"]
                    if not isinstance(description["target_symbol"], str) or not description["target_symbol"]:
                        raise ValueError(f"{name} {arch}: missing forwarded implementation for {symbol}")
                if not symbol or kind not in KINDS:
                    raise ValueError(f"{name} {arch}: unsupported export {symbol!r} {kind!r}")
                section, flag = kind.split(".")
                group.setdefault(section, {}).setdefault(flag, []).append(symbol)
            if len(group) > 1:
                document.setdefault(role, []).append(group)
    # The v5 reader indexes each reexported name once. Group its target set.
    for edge, targets in sorted(edge_targets.items()):
        entry = {"names": [edge]}
        if len(targets) != len(slices):
            entry["targets"] = targets
        document.setdefault("reexported_libraries", []).append(entry)
    return document


def resolve(images, inventories, minimum):
    minimum = version(minimum)
    documents = {}
    by_name = {}
    for image in images:
        document = library_document(image, minimum)
        name = image["install_name"]
        if name in by_name:
            raise ValueError(f"duplicate install name: {name}")
        documents[name] = document
        by_name[name] = image
    if set(inventories) != set(ARCHES):
        raise ValueError("both client architectures need an inventory")
    rows = []
    for arch in ARCHES:
        providers = defaultdict(list)
        reached = set()
        active = set()

        def visit(name):
            if name in active:
                raise ValueError(f"{arch}: reexport cycle through {name}")
            if name in reached:
                return
            if name not in by_name or arch not in by_name[name]["slices"]:
                raise ValueError(f"{arch}: missing reexported image {name}")
            active.add(name)
            item = by_name[name]["slices"][arch]
            for edge in sorted(item["reexports"]):
                visit(edge)
            for symbol, kind in item["exports"].items():
                providers[symbol].append((name, kind, None))
            for symbol, forward in item.get("symbol_reexports", {}).items():
                providers[symbol].append((name, forward["kind"], forward))
            active.remove(name)
            reached.add(name)

        visit(SYSTEM)
        for name, image in by_name.items():
            if arch in image["slices"] and name not in reached:
                raise ValueError(f"{arch}: unreachable component {name}")
        for symbol, definitions in providers.items():
            if len(definitions) != 1:
                raise ValueError(f"{arch}: ambiguous provider for {symbol}: {definitions}")
            owner, kind, forward = definitions[0]
            if forward:
                destination = forward["target_library"]
                if destination not in reached or destination == owner:
                    raise ValueError(f"{arch}: invalid forwarding destination for {symbol}: {destination}")
                target = by_name[destination]["slices"][arch]
                implementation = forward["target_symbol"]
                if implementation in target.get("symbol_reexports", {}) or target["exports"].get(implementation, kind) != kind:
                    raise ValueError(f"{arch}: conflicting implementation for {symbol} in {destination}")
        for item in inventories[arch]:
            symbol = item["symbol"]
            if symbol not in providers:
                raise ValueError(f"{arch}: missing provider for {symbol} from {item['header']}")
            name, kind, forward = providers[symbol][0]
            if KINDS[kind] != item["kind"]:
                raise ValueError(f"{arch}: export kind mismatch for {symbol}: {kind} vs {item['kind']}")
            row = {"arch": arch, "symbol": symbol, "kind": kind, "provider": name, "header": item["header"]}
            if forward:
                row.update(role="reexport", target_library=forward["target_library"], target_symbol=forward["target_symbol"])
            rows.append(row)
    tbd = {"tapi_tbd_version": 5, "main_library": documents.pop(SYSTEM)}
    if documents:
        tbd["libraries"] = [documents[name] for name in sorted(documents)]
    return tbd, sorted(rows, key=lambda x: (x["arch"], x["symbol"], x["header"]))
