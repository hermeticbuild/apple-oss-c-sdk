"""Checkpoint object-backed public-root scans from a verified header census."""

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
import errno
import fcntl
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

from tools import header_manifest
from tools.libsystem import scan
from tools.qualify_headers import census, trace_includes
from tools.toolchain.official_llvm import PIN, projection, read_lock, sha256


SCANNED = {"passed", "unresolved-imports"}
UNSCANNED = {"census-failed", "unsupported-context", "scan-failed"}


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_checkpoint(path, value, compressed=False):
    with TemporaryDirectory(dir=path.parent, prefix=".checkpoint-") as temp:
        staged = Path(temp) / path.name
        if compressed:
            with staged.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as packed:
                with io.TextIOWrapper(packed, encoding="utf-8") as stream:
                    json.dump(value, stream, sort_keys=True, separators=(",", ":"))
                    stream.write("\n")
        else:
            staged.write_bytes(json_bytes(value))
        staged.replace(path)


@contextmanager
def exclusive(work):
    with (work / ".lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(f"scan already running in {work}") from exc
        yield


def install_identity(root):
    files, manifests = header_manifest.read_header_manifest(root)
    for name in sorted(files):
        if scan.header_path(root, name) != name or not name.startswith("usr/include/"):
            raise ValueError(f"manifest path outside usr/include: {name}")
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root) or sha256(path) != files[name]["sha256"]:
            raise ValueError(f"installed header differs from receipt: {name}")
    installed = {path.relative_to(root).as_posix() for path in (root / "usr/include").rglob("*")
                 if not path.is_dir() or path.is_symlink()}
    if installed != files.keys():
        raise ValueError(f"unexpected paths under usr/include: {sorted(installed - files.keys())}")
    if any(path.is_symlink() or not path.resolve().is_relative_to(root) for path in manifests):
        raise ValueError("manifest outside C installation")
    return files, {path.name: sha256(path) for path in sorted(manifests)}


def census_jobs(report, root, files, manifests, headers, arches, profiles):
    minimum = report["minimum"]
    if report["schema"] != 1 or report["manifest_digests"] != manifests or report["installed"] != len(files):
        raise ValueError("header census does not describe this installed manifest")
    if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", minimum):
        raise ValueError(f"invalid census deployment target: {minimum}")
    rows = {}
    for row in report["rows"]:
        key = (row["arch"], row["path"])
        if (key in rows or row["arch"] not in census.ARCHES or row["path"] not in files
                or row["status"] not in {"passed", "compile-failed", "header-not-reached"}):
            raise ValueError(f"invalid or duplicate census row: {key}")
        rows[key] = row
    paths = {path for _, path in rows}
    if len(paths) != report["selected"] or rows.keys() != {(arch, path) for arch in census.ARCHES for path in paths}:
        raise ValueError("header census omits expected architecture/path rows")
    paths = {scan.header_path(root, header) for header in headers} if headers else paths
    if not paths or any((arch, path) not in rows for path in paths for arch in arches):
        raise ValueError("selected public root has no matching census row")

    jobs = {}
    for arch in sorted(arches):
        for profile in sorted(profiles):
            for path in sorted(paths):
                job = {"arch": arch, "profile": profile, "path": path}
                key = hashlib.sha256(json_bytes(job)).hexdigest()
                jobs[key] = (job, rows[arch, path])
    return minimum, jobs


def check_context(root, row, profile):
    if row["status"] != "passed":
        return None, "census-failed", row["diagnostic"]
    context = row["context"]
    census.options(context)
    if context.get("language", "c") != "c" or context.get("before"):
        return None, "unsupported-context", "scanner requires a C root without pre-includes"
    if any("-D" + name not in scan.PROFILES[profile] for name in context.get("defines", [])):
        return None, "unsupported-context", "scanner profile omits census context feature macros"
    public_root = scan.header_path(root, context.get("root", row["path"]))
    return public_root, None, None


def probe_job(llvm, root, minimum, work, job, row):
    record = {"job": job, "census": row}
    public_root, status, diagnostic = check_context(root, row, job["profile"])
    if status:
        return {**record, "status": status, "diagnostic": diagnostic}
    with TemporaryDirectory(dir=work, prefix=".root-") as temp:
        scratch = Path(temp)

        def normalize(message):
            return (message.replace(str(scratch), "$SCAN_WORK").replace(str(root), "$C_INSTALL")
                    .replace(str(llvm), "$LLVM"))

        try:
            result = scan.scan(llvm, root, job["arch"], minimum, job["profile"], [public_root], scratch)
            reached = {header["path"] for context in result["contexts"] for header in context["headers"]}
            if job["path"] not in reached:
                raise ValueError(f"{public_root} did not reach census header {job['path']} in the scan profile")
            for finding in result["unresolved"]:
                if "probe" in finding:
                    log = (scratch / finding["probe"]).with_suffix(".log")
                    if log.is_file():
                        finding["diagnostic"] = normalize(log.read_text())
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            if isinstance(exc, OSError) and exc.errno in {errno.ENOSPC, errno.EDQUOT}:
                raise
            return {**record, "status": "scan-failed", "diagnostic": normalize(f"{type(exc).__name__}: {exc}")}
    return {**record, "status": "unresolved-imports" if result["unresolved"] else "passed", "scan": result}


def verify_checkpoint(path, identity, job, row):
    if path.is_symlink():
        raise ValueError(f"refusing symlink checkpoint: {path}")
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        checkpoint = json.load(stream)
    result = checkpoint["result"]
    if (checkpoint["identity"] != identity or result["job"] != job or result["census"] != row
            or result["status"] not in SCANNED | UNSCANNED or ("scan" in result) != (result["status"] in SCANNED)):
        raise ValueError(f"checkpoint does not match pinned job: {path}")
    return result


def scanner_identity():
    modules = (scan, header_manifest, trace_includes, census)
    return {
        "tools.libsystem.scan_roots": sha256(Path(__file__)),
        **{module.__name__: sha256(Path(module.__file__)) for module in modules},
    }


def run(args, llvm, root, work):
    files, manifests = install_identity(root)
    raw_census = args.census.read_bytes()
    minimum, jobs = census_jobs(json.loads(raw_census), root, files, manifests,
                                args.header, args.arch, args.profile)
    projection(llvm, read_lock(PIN))
    identity = {
        "schema": 1,
        "census_sha256": hashlib.sha256(raw_census).hexdigest(),
        "c_manifest": manifests,
        "minimum": minimum,
        "llvm_lock_sha256": sha256(PIN),
        "implementation": scanner_identity(),
        "jobs": {key: job for key, (job, _) in jobs.items()},
    }
    source_lock = root / "source-lock.json"
    if source_lock.is_file():
        if source_lock.is_symlink():
            raise ValueError("C source lock must be a regular file")
        identity["source_lock_sha256"] = sha256(source_lock)

    state = work / "inputs.json"
    scans = work / "roots"
    if state.exists() or state.is_symlink():
        if state.is_symlink() or state.read_bytes() != json_bytes(identity):
            raise ValueError(f"input identity changed; choose a new work directory: {state}")
    else:
        if scans.exists() or (work / "summary.json").exists():
            raise ValueError(f"missing pinned input identity in existing work directory: {work}")
        write_checkpoint(state, identity)
    scans.mkdir(exist_ok=True)
    if scans.is_symlink():
        raise ValueError(f"refusing symlink checkpoint directory: {scans}")
    identity_sha = hashlib.sha256(json_bytes(identity)).hexdigest()

    counts = Counter()
    symbols = defaultdict(set)
    outcomes = []
    resumed = 0
    for key, (job, row) in jobs.items():
        path = scans / f"{key}.json.gz"
        if path.exists() or path.is_symlink():
            result = verify_checkpoint(path, identity_sha, job, row)
            resumed += 1
        else:
            result = probe_job(llvm, root, minimum, work, job, row)
            write_checkpoint(path, {"identity": identity_sha, "result": result}, compressed=True)
            print(f"{job['arch']} {job['profile']} {job['path']}: {result['status']}", flush=True)
        status = result["status"]
        counts[status] += 1
        outcome = {**job, "status": status, "checkpoint": path.relative_to(work).as_posix(),
                   "checkpoint_sha256": sha256(path)}
        if "scan" in result:
            imports = result["scan"]["imports"]
            target = (job["arch"], job["profile"])
            symbols[target].update((entry["symbol"], entry["kind"], entry["weak_import"]) for entry in imports)
            outcome["imports"] = len(imports)
            outcome["unresolved"] = len(result["scan"]["unresolved"])
        outcomes.append(outcome)

    write_checkpoint(work / "summary.json", {
        "schema": 1,
        "identity_sha256": identity_sha,
        "status_counts": counts,
        "roots": outcomes,
        "symbols": [{"arch": arch, "profile": profile,
                     "imports": [{"symbol": symbol, "kind": kind, "weak_import": weak}
                                 for symbol, kind, weak in sorted(imports)]}
                    for (arch, profile), imports in sorted(symbols.items())],
    })
    print(f"{counts['passed']}/{len(jobs)} roots passed; {resumed} checkpoints reused")
    return 0 if args.report_only or counts["passed"] == len(jobs) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("llvm", "c-install", "census", "work"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--header", action="append", default=[], help="restrict to named census roots")
    parser.add_argument("--arch", action="append", choices=census.ARCHES, help="default: both")
    parser.add_argument("--profile", action="append", choices=scan.PROFILES, help="default: both")
    parser.add_argument("--report-only", action="store_true", help="allow completion with recorded findings")
    args = parser.parse_args()
    args.arch = set(args.arch or census.ARCHES)
    args.profile = set(args.profile or scan.PROFILES)
    try:
        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=True)
        with exclusive(work):
            return run(args, args.llvm.resolve(), args.c_install.resolve(), work)
    except (OSError, ValueError, KeyError, TypeError, EOFError) as exc:
        parser.exit(2, f"root scans: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
