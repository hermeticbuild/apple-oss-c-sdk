"""Collect local dyld_info evidence for a named image and specific candidate symbols."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory


def capture(image, arch, inspector, cache, symbols, out):
    if not image.startswith("/usr/lib/") or ".." in Path(image).parts:
        raise ValueError("expected an installed /usr/lib image name")
    if out.exists():
        raise ValueError(f"choose a new evidence directory: {out}")
    command = [str(inspector), "-arch", arch]
    if cache:
        command.extend(["-dyld_cache_path", str(cache.resolve(strict=True))])
    command.extend(["-uuid", "-load_commands", "-exports", image])
    output = subprocess.check_output(command, text=True)
    if output.splitlines()[0].strip() != f"{image} [{arch}]:":
        raise ValueError("inspected image or observed slice differs from request")
    uuid = re.search(r"(?m)^\s*-uuid:\s+([A-Fa-f0-9-]{36})$", output)
    if not uuid:
        raise ValueError("missing image UUID")
    sections = re.split(r"(?m)^\s+-(exports|load_commands):\s*$", output)
    content = dict(zip(sections[1::2], sections[2::2]))
    if set(content) != {"exports", "load_commands"}:
        raise ValueError("missing load commands or export inventory")
    edges = []
    identity = None
    for block in re.split(r"(?m)^Load command #\d+$", content["load_commands"]):
        cmd = re.search(r"(?m)^\s*cmd: (LC_(?:ID|REEXPORT)_DYLIB)$", block)
        if not cmd:
            continue
        attrs = dict(re.findall(r'(?m)^\s*(name|cur-vers|compat-vers):\s+"?([^"\n]+?)"?$', block))
        if len(attrs) != 3:
            raise ValueError(f"missing dylib metadata in {cmd[1]}")
        if cmd[1] == "LC_ID_DYLIB":
            identity = attrs
        else:
            edges.append(attrs["name"])
    if not identity or identity["name"] != image:
        raise ValueError("unexpected LC_ID_DYLIB")
    matches = {symbol: [] for symbol in sorted(set(symbols))}
    for line in content["exports"].splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] in matches:
            matches[fields[1]].append(line.strip())
        elif any(word in matches for word in fields):
            raise ValueError(f"unrecognized export record: {line}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out.parent) as work:
        evidence = Path(work) / "evidence"
        evidence.mkdir()
        (evidence / "dyld_info.txt").write_text(output)
        receipt = {"schema": 1, "argv": command, "observed_arch": arch, "image_uuid": uuid[1],
                   "host_os_build": subprocess.check_output(["/usr/bin/sw_vers", "-buildVersion"], text=True).strip(),
                   "identity": identity, "reexports": sorted(edges), "requested_exports": matches,
                   "inspector_sha256": hashlib.sha256(inspector.read_bytes()).hexdigest(),
                   "raw_sha256": hashlib.sha256(output.encode()).hexdigest()}
        (evidence / "capture.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        evidence.rename(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspector", required=True, type=Path)
    parser.add_argument("--arch", required=True, choices=("arm64", "arm64e", "x86_64"))
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--image", required=True)
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        capture(args.image, args.arch, args.inspector.resolve(strict=True), args.cache, args.symbol, args.out)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"capture: {exc}\n")


if __name__ == "__main__":
    main()
