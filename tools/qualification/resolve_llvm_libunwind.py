#!/usr/bin/env python3
"""Resolve pinned LLVM libunwind headers through hermetic-llvm's Bazel source."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = HERE / "data/llvm-libunwind-headers.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm-repo", required=True, type=Path)
    args = parser.parse_args()
    repo = args.llvm_repo.resolve()
    pin = json.loads(PIN.read_text())
    module = (repo / "MODULE.bazel").read_text()
    version = re.search(r'^LLVM_VERSION = "([^"]+)"$', module, re.MULTILINE)
    if not version or version.group(1) != pin["llvm_version"]:
        parser.error("hermetic-llvm selected a different LLVM source version")
    index = json.loads((repo / "llvm_versions.json").read_text())
    if pin["llvm_version"] not in index or not index[pin["llvm_version"]].get("sha256"):
        parser.error("LLVM source archive lacks a pinned SHA256")
    subprocess.run(["bazel", "fetch", "--config=remote", "@llvm-project//llvm:llvm"],
                   cwd=repo, check=True, stdout=subprocess.DEVNULL)
    output_base = subprocess.check_output(
        ["bazel", "info", "output_base", "--config=remote"],
        cwd=repo, text=True).strip()
    headers = Path(output_base) / "external/+llvm+llvm-project/libunwind/include"
    for name, expected in pin["sha256"].items():
        path = headers / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            parser.error(f"pinned LLVM libunwind header differs: {name}")
    print(headers)


if __name__ == "__main__":
    main()
