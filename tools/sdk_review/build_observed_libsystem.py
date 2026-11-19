"""Build a local partial TBD to qualify observed client bindings against a reference SDK."""

import argparse
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from tools.libsystem.emit import ARCHES, SYSTEM, resolve, version
from .probe_runtime_providers import match_export


def read(path):
    return json.loads(path.read_bytes())


def export_kind(kind, attributes):
    # LLVM TextAPI's Mach-O reader carries weakness and TLS into the stub.
    # A callable stub with a dynamic resolver is still a text export.
    if kind not in ("function", "data"):
        return None
    remaining = list(attributes)
    if kind == "function":
        remaining = [x for x in remaining if not re.fullmatch(r"\[dynamic-resolver=0x[0-9A-Fa-f]+\]", x)]
    if remaining not in ([], ["[weak-def]"]):
        return None
    section = "text" if kind == "function" else "data"
    return section + (".weak" if remaining else ".global")


def match_components(graph, edges):
    remaining = set(edges)
    selected = []
    for slot in graph["component_slots"]:
        candidates = [f"/usr/lib/system/lib{name}.dylib" for name in slot["alternatives"]]
        matches = [name for name in candidates if name in remaining]
        if len(matches) != 1:
            raise ValueError(f"component slot requires separate review: {slot}, observed={matches}")
        remaining.remove(matches[0])
        selected.append(matches[0])
    if remaining:
        raise ValueError(f"unmatched deployed reexports: {sorted(remaining)}")
    return selected


def deployment_version(value):
    parts = tuple(map(int, version(value).split(".")))
    return parts + (0,) * (3 - len(parts))


def build(args):
    if args.out.exists():
        raise ValueError(f"choose a new output directory: {args.out}")
    graph = read(args.graph)
    if graph["umbrella"]["install_path"] != SYSTEM:
        raise ValueError("unexpected umbrella in the Apple source inventory")
    images = {}
    clients = {}
    installation = None
    minimum = deployment_version(args.minimum)
    review = {"qualification": "local-partial", "targets": {}}
    for arch in ARCHES:
        root = getattr(args, arch)
        report = read(root / "providers.json")
        if report["client_arch"] != arch:
            raise ValueError(f"client architecture mismatch in {root}")
        if not report["scans"]:
            raise ValueError(f"no client scan receipts for {arch}")
        for scan in report["scans"]:
            scan_minimum = scan["minimum"]
            if deployment_version(scan_minimum) != minimum:
                raise ValueError(f"{arch}: requested minimum {args.minimum} disagrees with scan minimum {scan_minimum}")
            if installation is not None and scan["c_manifest"] != installation:
                raise ValueError("provider observations used different C installations")
            installation = scan["c_manifest"]
        edges = match_components(graph, report["images"][SYSTEM]["reexports"])
        if set(report["images"]) != {SYSTEM, *edges}:
            raise ValueError("additional component levels require review")
        omitted = []
        count = 0
        clients[arch] = []
        observed = {}
        for name, evidence in report["images"].items():
            receipt = read(root / evidence["receipt"])
            identity = receipt["identity"]
            if (identity["name"] != name or receipt["image_uuid"] != evidence["uuid"]
                    or receipt["observed_arch"] != report["observed_arch"]
                    or receipt["reexports"] != evidence["reexports"]):
                raise ValueError(f"receipt mismatch for {name}")
            current, compatible = identity["cur-vers"], identity["compat-vers"]
            image = images.setdefault(name, {"install_name": name, "current_version": current,
                                              "compatibility_version": compatible, "slices": {}})
            if (image["current_version"], image["compatibility_version"]) != (current, compatible):
                raise ValueError(f"versions vary by slice for {name}")
            image["slices"][arch] = {"exports": {}, "reexports": receipt["reexports"]}
            for symbol, lines in receipt["requested_exports"].items():
                observed.setdefault(symbol, []).extend(match_export(name, symbol, line) for line in lines)
        for row in report["symbols"]:
            kinds = {kind for kind, _ in row["client_declarations"]}
            hits = row["matches"]
            if hits != sorted(observed[row["symbol"]], key=lambda item: item["image"]):
                raise ValueError(f"provider receipts disagree on {row['symbol']}")
            if len(hits) != 1 or hits[0]["role"] != "definition" or len(kinds) != 1:
                omitted.append(row)
                continue
            kind = kinds.pop()
            encoding = export_kind(kind, hits[0]["attributes"])
            if encoding is None:
                omitted.append(row)
                continue
            images[hits[0]["image"]]["slices"][arch]["exports"][row["symbol"]] = encoding
            count += 1
            for _, header in row["client_declarations"]:
                clients[arch].append({"symbol": row["symbol"], "header": header, "kind": kind})
        review["targets"][arch] = {"observed_arch": report["observed_arch"], "scans": report["scans"],
                                  "root_findings": report.get("root_findings", []),
                                  "linker_demands": report["linker_demands"],
                                  "included_symbols": count, "omitted_demands": omitted, "edges": edges}
    interface, _ = resolve(images.values(), clients, args.minimum)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.out.parent) as tmp:
        package = Path(tmp) / "result"
        lib = package / "usr/lib"
        lib.mkdir(parents=True)
        (lib / "libSystem.B.tbd").write_text(json.dumps(interface, indent=2, sort_keys=True) + "\n")
        (lib / "libSystem.tbd").symlink_to("libSystem.B.tbd")
        (package / "local-review.json").write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
        package.rename(args.out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("graph", *ARCHES, "out"):
        parser.add_argument("--" + key, required=True, type=Path)
    parser.add_argument("--minimum", required=True)
    args = parser.parse_args()
    try:
        build(args)
    except (KeyError, ValueError, OSError) as exc:
        parser.exit(1, f"local libSystem diagnostic: {exc}\n")


if __name__ == "__main__":
    main()
