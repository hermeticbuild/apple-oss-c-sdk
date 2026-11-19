"""Derive the non-cancelable close alias from Apple's macOS syscall stubs."""

import json
from pathlib import Path
import re
import subprocess

from tools.sdk_composition import compose_libsystem

from .component_graph import read_source
from .emit import ARCHES, version
from .netname import KERNEL
from .scan import digest, run


RECORD = Path(__file__).parent / "data/macosx26.5/close-nocancel.json"
ALIAS = "_close$NOCANCEL"
IMPLEMENTATION = "___close_nocancel"


def assemble(source, files, llvm, c_install, minimum, work):
    # The Perl generator discovers custom stubs by filename. Give it only
    # the reviewed inputs, including its two mandatory copies from custom/.
    inputs = work / "xnu"
    for name, content in read_source(source.resolve(), files).items():
        path = inputs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    libsyscall = inputs / "libsyscall"
    generated = work / "generated"
    generated.mkdir()
    subprocess.run(
        ["perl", libsyscall / "xcodescripts/create-syscalls.pl", inputs / "bsd/kern/syscalls.master",
         libsyscall / "custom", libsyscall / "Platforms", "MacOSX", generated],
        env={"ARCHS": " ".join(ARCHES), "LC_ALL": "C"}, stdout=subprocess.DEVNULL, check=True,
    )
    stub = generated / (IMPLEMENTATION + ".s")
    # Use the same manifest-verified C header tree that SDK composition installs.
    headers = compose_libsystem.Plan()
    compose_libsystem.c_install(headers, c_install.resolve())
    sysroot = (work / "sysroot").resolve()
    headers.materialize(sysroot)
    targets = {}
    for arch in ARCHES:
        obj = work / (arch + ".o")
        flags = [
            "--no-default-config", "-target", f"{arch}-apple-macos{minimum}",
            "-nostdinc", "-isysroot", sysroot, "-I", inputs / "osfmk", "-I", sysroot / "usr/include",
            "-DPRIVATE", "-D__APPLE_API_PRIVATE", "-D__DARWIN_VERS_1050=1",
            "-x", "assembler-with-cpp", "-c", stub, "-o", obj,
        ]
        run(llvm / "bin/clang", flags, work)
        symbols = run(llvm / "bin/llvm-nm", ["-m", "--defined-only", "--extern-only", obj], work)
        definitions = re.findall(r"(?m)^([0-9a-fA-F]+) \(__TEXT,__text\) external (\S+)$", symbols)
        if ({name for _, name in definitions} != {ALIAS, IMPLEMENTATION}
                or len({offset for offset, _ in definitions}) != 1):
            raise ValueError(f"{arch}: XNU did not define {ALIAS} at {IMPLEMENTATION}")
        targets[arch] = {"object_sha256": digest(obj), "shared_text_offset": int(definitions[0][0], 16)}
    return {"assembly_sha256": digest(stub), "targets": targets}


def install(sdk, source, llvm, c_install, minimum, work, images, inventories):
    record = json.loads(RECORD.read_bytes())
    parts = tuple(map(int, version(minimum).split(".")))
    if sdk != record["sdk"] or not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed close alias covers macosx26.5 and deployment minima 11.0–26.5")
    owners = [image["slices"] for image in images if image["install_name"] == KERNEL]
    if len(owners) != 1 or set(owners[0]) != set(ARCHES) or set(inventories) != set(ARCHES):
        raise ValueError("the close alias requires libsystem_kernel and inventories for both client slices")
    for image in images:
        for arch, part in image["slices"].items():
            existing = part["exports"].get(ALIAS)
            if ALIAS in part.get("symbol_reexports", {}) or (existing is not None and
                    (image["install_name"] != KERNEL or existing != "text.global")):
                raise ValueError(f"{arch}: conflicting definition for {ALIAS} in {image['install_name']}")

    objects = assemble(source, record["source"]["files"], llvm, c_install, minimum, work)
    for arch in ARCHES:
        owners[0][arch]["exports"][ALIAS] = "text.global"
        inventories[arch].append({"symbol": ALIAS, "kind": "function",
                                  "header": f"libsyscall/Platforms/MacOSX/{arch}/syscall.map"})
    return {**record, "minimum": minimum, "provider": KERNEL, "kind": "text.global",
            "alias": ALIAS, "implementation": IMPLEMENTATION, **objects}
