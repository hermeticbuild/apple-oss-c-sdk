"""Trace independently identified client imports through a local dyld cache."""

import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from tools.libsystem.capture import capture
from tools.libsystem.emit import SYSTEM
from tools.libsystem.scan_roots import SCANNED, json_bytes


def inputs(scans, matrices, arch, findings):
    for path in scans:
        content = path.read_bytes()
        yield json.loads(content), hashlib.sha256(content).hexdigest()
    for directory in matrices:
        index = json.loads((directory / "inputs.json").read_bytes())
        identity = hashlib.sha256(json_bytes(index)).hexdigest()
        summary = json.loads((directory / "summary.json").read_bytes())
        if summary["schema"] != 1 or summary["identity_sha256"] != identity:
            raise ValueError(f"stale root scan {directory}")
        expected = {key for key, job in index["jobs"].items() if job["arch"] == arch}
        seen = set()
        for row in summary["roots"]:
            if row["arch"] != arch:
                continue
            job = {key: row[key] for key in ("arch", "profile", "path")}
            key = hashlib.sha256(json_bytes(job)).hexdigest()
            if key in seen or key not in expected or row["checkpoint"] != f"roots/{key}.json.gz":
                raise ValueError(f"unexpected root checkpoint {job}")
            seen.add(key)
            data = (directory / row["checkpoint"]).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest != row["checkpoint_sha256"]:
                raise ValueError(f"root checkpoint changed for {job}")
            checkpoint = json.loads(gzip.decompress(data))
            result = checkpoint["result"]
            if checkpoint["identity"] != identity or result["job"] != job or result["status"] != row["status"]:
                raise ValueError(f"root result changed for {job}")
            if row["status"] != "passed":
                findings.append({**job, "status": row["status"], "checkpoint_sha256": digest})
            if row["status"] in SCANNED:
                yield result["scan"], digest
        if not expected or expected != seen:
            raise ValueError(f"incomplete {arch} census scope in {directory}")


def collect(scans, matrices, client_arch):
    candidates = defaultdict(set)
    identities = []
    findings = []
    installation = None
    for scan, digest in inputs(scans, matrices, client_arch, findings):
        if scan["schema_version"] != 1 or scan["arch"] != client_arch:
            raise ValueError(f"unexpected scanner schema or target in receipt {digest}")
        if installation is not None and installation != scan["c_manifest"]:
            raise ValueError("client inputs came from different C installations")
        installation = scan["c_manifest"]
        identities.append({"sha256": digest,
                           "c_manifest": installation, "profile": scan["profile"], "minimum": scan["minimum"],
                           "unresolved_declarations": len(scan["unresolved"]),
                           "headers": [x["path"] for x in scan["headers"]]})
        for entry in scan["imports"]:
            candidates[entry["symbol"]].add((entry["kind"], entry["header"]))
    if not candidates:
        raise ValueError("scans supplied no client imports")
    return candidates, sorted(identities, key=lambda item: item["sha256"]), findings


def add_linker_demands(candidates, evidence, arch):
    recipe = Path(__file__).resolve().parents[1] / "libsystem/data/macosx26.5/dyld-linker-demands.json"
    record = json.loads(recipe.read_bytes())
    prefix = evidence / f"dyld-thread-local-helpers-{arch}"
    object_digest = hashlib.sha256(prefix.with_suffix(".o").read_bytes()).hexdigest()
    expected = record["assembly_objects_sha256"][arch]
    if object_digest != expected:
        raise ValueError(f"dyld assembly object digest mismatch for {arch}: expected {expected}, got {object_digest}")
    assembled = set(prefix.with_suffix(".symbols").read_text().splitlines())
    for demand in record["demands"]:
        if arch in demand["architectures"]:
            if demand["symbol"] not in assembled:
                raise ValueError(f"assembly receipt does not contain {demand['symbol']}")
            candidates[demand["symbol"]].add((demand["kind"], demand.get("url", record["url"])))
    record["object_sha256"] = object_digest
    return record


def match_export(image, symbol, line):
    parts = line.split()
    if len(parts) < 2 or parts[1] != symbol:
        raise ValueError(f"unexpected export record in {image}: {line}")
    if parts[0] == "[re-export]":
        return {"image": image, "role": "forwarder", "detail": " ".join(parts[2:])}
    if not re.fullmatch(r"0x[0-9A-Fa-f]+", parts[0]):
        raise ValueError(f"unexpected export record in {image}: {line}")
    return {"image": image, "role": "definition", "attributes": parts[2:]}


def probe(args):
    candidates, identities, findings = collect(args.scan, args.matrix, args.client_arch)
    linker = add_linker_demands(candidates, args.dyld_evidence, args.client_arch) if args.dyld_evidence else None
    if args.observed_arch not in (("arm64", "arm64e") if args.client_arch == "arm64" else ("x86_64",)):
        raise ValueError("incompatible client and cache architectures")
    if args.out.exists():
        raise ValueError(f"choose a new evidence directory: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.out.parent) as work:
        out = Path(work) / "result"
        pending = [SYSTEM]
        images = {}
        matches = defaultdict(list)
        while pending:
            name = pending.pop()
            if name in images:
                continue
            folder = out / "images" / hashlib.sha256(name.encode()).hexdigest()
            capture(name, args.observed_arch, args.inspector, args.cache, candidates, folder)
            receipt = json.loads((folder / "capture.json").read_bytes())
            images[name] = {"receipt": (folder / "capture.json").relative_to(out).as_posix(),
                            "uuid": receipt["image_uuid"], "reexports": receipt["reexports"]}
            for symbol, lines in receipt["requested_exports"].items():
                matches[symbol].extend(match_export(name, symbol, line) for line in lines)
            pending.extend(sorted(receipt["reexports"], reverse=True))
        rows = []
        for symbol, declarations in sorted(candidates.items()):
            hits = sorted(matches[symbol], key=lambda item: item["image"])
            status = ("absent" if not hits else
                      "unique-definition" if len(hits) == 1 and hits[0]["role"] == "definition"
                      else "needs-binding-review")
            rows.append({"symbol": symbol, "client_declarations": sorted(declarations),
                         "status": status, "matches": hits})
        report = {"schema": 1, "client_arch": args.client_arch, "observed_arch": args.observed_arch,
                  "scans": identities, "root_findings": findings, "linker_demands": linker,
                  "images": images, "symbols": rows}
        (out / "providers.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        out.rename(args.out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan", type=Path, action="append", default=[])
    parser.add_argument("--matrix", type=Path, action="append", default=[], help="completed scan_roots work directory")
    parser.add_argument("--client-arch", required=True, choices=("arm64", "x86_64"))
    parser.add_argument("--observed-arch", required=True, choices=("arm64", "arm64e", "x86_64"))
    parser.add_argument("--inspector", required=True, type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--dyld-evidence", type=Path, help="output of the pinned dyld assembly recipe")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        probe(args)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"runtime provider probe: {exc}\n")


if __name__ == "__main__":
    main()
