"""Build a libSystem interface from a pinned release description."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from tempfile import TemporaryDirectory

from tools.header_manifest import read_header_manifest
from tools.toolchain.official_llvm import PIN, projection, read_lock
from .emit import ARCHES, fields, resolve
from .expected_undefined import filter_demands, policy_for, verify_header
from .libc_aliases import FILES as ALIAS_FILES, REVISION as LIBC_REVISION, install_aliases
from . import libc_compiler_abi


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_fields(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError(f"duplicate JSON key: {key}")
        data[key] = value
    return data


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=unique_fields)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def relative_file(root, name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not (root / path).resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path outside locked inputs: {name}")
    return root / path


def build(args):
    projection(args.llvm.resolve(), read_lock(PIN))
    lock = read_json(args.lock)
    lock_fields = {"schema", "sdk", "minimum", "headers", "sources", "manifest_sha256"}
    if "libc_alias_source" in lock:
        lock_fields.add("libc_alias_source")
    elif "libc_source" in lock:
        lock_fields.add("libc_source")
    fields(lock, lock_fields, "release lock")
    if lock["schema"] != 1 or not isinstance(lock["headers"], list) or not lock["headers"] or len(lock["headers"]) != len(set(lock["headers"])):
        raise ValueError("invalid release schema or header list")
    out = args.out.absolute()
    if os.path.lexists(out):
        raise ValueError(f"choose a new output path: {out}")
    if digest(args.c_install / "header-manifest.tsv") != lock["manifest_sha256"]:
        raise ValueError("C installation manifest digest mismatch")
    manifest, _ = read_header_manifest(args.c_install)
    for path, item in manifest.items():
        if digest(relative_file(args.c_install, path)) != item["sha256"]:
            raise ValueError(f"installed header digest mismatch: {path}")
    for name in lock["headers"]:
        if f"usr/include/{name}" not in manifest:
            raise ValueError(f"public header has no receipt: {name}")
    images = []
    for name, expected in sorted(lock["sources"].items()):
        source = relative_file(args.lock.parent, name)
        if digest(source) != expected:
            raise ValueError(f"component evidence digest mismatch: {name}")
        images.append(read_json(source))
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".libsystem-", dir=out.parent) as work:
        work = Path(work)
        package = work / "package"
        lib = package / "usr/lib"
        lib.mkdir(parents=True)
        inventories = {}
        receipt = {"sdk": lock["sdk"], "lock_sha256": digest(args.lock), "toolchain_lock_sha256": digest(PIN),
                   "images": lock["sources"], "scan_sha256": {}}
        if "libc_alias_source" in lock or "libc_source" in lock:
            source = relative_file(args.lock.parent, lock.get("libc_source", lock.get("libc_alias_source")))
            install_aliases(source, lock["sdk"], images)
            receipt["libc_alias_source"] = {"commit": LIBC_REVISION, "files": ALIAS_FILES}
        for arch in ARCHES:
            path = work / (arch + ".json")
            command = [sys.executable, "-m", "tools.libsystem.scan", "--llvm", args.llvm,
                       "--c-install", args.c_install, "--arch", arch, "--minimum", lock["minimum"], "--out", path]
            for name in sorted(lock["headers"]):
                command.extend(["--header", name])
            subprocess.run(command, check=True)
            scan = read_json(path)
            if scan["arch"] != arch or scan["unresolved"]:
                raise ValueError(f"{arch}: unresolved header scan: {scan['unresolved']}")
            inventories[arch] = scan["imports"]
            receipt["scan_sha256"][arch] = digest(path)
        if "libc_source" in lock:
            receipt["libc_compiler_abi"] = libc_compiler_abi.install(
                source, args.llvm.resolve(), lock["minimum"], work / "stack-protector", images, inventories)
        policy = policy_for(lock["sdk"])
        if policy:
            verify_header(policy, args.c_install, manifest)
            inventories = filter_demands(policy, images, inventories)
            receipt["expected_undefined"] = policy
        tbd, rows = resolve(images, inventories, lock["minimum"])
        stub = lib / "libSystem.B.tbd"
        write_json(stub, tbd)
        (lib / "libSystem.tbd").symlink_to(stub.name)
        receipt["tbd_sha256"] = digest(stub)
        write_json(package / "providers.json", rows)
        write_json(package / "manifest.json", receipt)
        package.rename(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("build")
    for name in ("lock", "llvm", "c-install", "out"):
        cmd.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        build(args)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"libsystem: {exc}\n")


if __name__ == "__main__":
    main()
