"""Verify the Libc interfaces that Clang imports for protected stack frames."""

import hashlib
import json
from pathlib import Path

from .compiler_imports import collect
from .emit import ARCHES
from .libc_aliases import LIBC, REVISION


SOURCE = "sys/OpenBSD/stack_protector.c"
FILES = {
    SOURCE: "6a1ec2ced39d5abe6a962dd155d830fdc46787c9136132c80edf99d72406d8df",
    "Libc.xcodeproj/project.pbxproj": "f17b1de720b7e8e608b6b4506405ead702644fbcf3824bb6d9878a94971c0e52",
}
SYMBOLS = {"___stack_chk_fail": "text.global", "___stack_chk_guard": "data.global"}
FIXTURE = Path(__file__).parent / "fixtures/stack_protector.c"
URL = f"https://github.com/apple-oss-distributions/Libc/blob/{REVISION}/{SOURCE}"


def check_source(source):
    for name, expected in FILES.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"review the changed Libc stack-protector input: {name}")


def install(source, llvm, minimum, work, images, inventories):
    check_source(source)
    collect(llvm, minimum, FIXTURE, work)
    evidence = json.loads((work / "imports.json").read_bytes())
    for case in evidence["cases"]:
        if set(case["undefined"]) != SYMBOLS.keys():
            raise ValueError(f"unexpected compiler stack-protector imports: {case}")
    owner, = (image for image in images if image["install_name"] == LIBC)
    for arch in ARCHES:
        exports = owner["slices"][arch]["exports"]
        for name, kind in SYMBOLS.items():
            if exports.setdefault(name, kind) != kind:
                raise ValueError(f"{arch}: conflicting Libc stack-protector kind for {name}")
            inventories[arch].append({"symbol": name, "kind": "function" if kind == "text.global" else "data",
                                      "header": URL})
    return {"commit": REVISION, "files": FILES, "compiler": evidence}
