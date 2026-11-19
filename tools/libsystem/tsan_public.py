"""Replay the qualified public Darwin names directly referenced by TSan."""

import json
from pathlib import Path

from .component_graph import read_source
from .emit import ARCHES, version
from .sanitizer_abi import excerpt
from .scan import digest, run


HERE = Path(__file__).resolve().parent
RECORD = HERE / "data/macosx26.5/tsan-public.json"
FIXTURE = HERE / "fixtures/tsan_public.cpp"
PLATFORM = "/usr/lib/system/libsystem_platform.dylib"
LIBC = "/usr/lib/system/libsystem_c.dylib"
TEXT = "text.global"
CONTEXT_EXPORTS = {"_getcontext", "_setcontext", "_swapcontext", "_makecontext"}
CASES = (
    ("context", ["-DCHECK_CONTEXT", "-D_XOPEN_SOURCE=700"], CONTEXT_EXPORTS),
    ("realpath", ["-DCHECK_REALPATH", "-D_POSIX_C_SOURCE=200809L"], {"_realpath"}),
    ("darwin-realpath", ["-DCHECK_REALPATH", "-D_DARWIN_C_SOURCE"], {"_realpath$DARWIN_EXTSN"}),
    ("fileno", ["-DCHECK_FILENO"], {"_fileno_unlocked"}),
)


def qualify(compiler_rt, fileno_declaration, llvm, c_install, work, minimum):
    work.mkdir()
    (work / "compiler_rt_stdio.h").write_text(excerpt(compiler_rt, fileno_declaration) + "\n")
    clang = llvm / "bin/clang"
    resource = Path(run(clang, ["--no-default-config", "-print-resource-dir"], work).strip()).resolve() / "include"
    if not resource.is_dir() or not resource.is_relative_to(llvm):
        raise ValueError("unexpected Clang resource directory for TSan public linker inputs")
    result = {}
    for arch in ARCHES:
        result[arch] = {}
        for case, defines, expected in CASES:
            obj = work / f"{arch}-{case}.o"
            run(clang, ["--no-default-config", "-target", f"{arch}-apple-macos{minimum}", "-std=c++17",
                        "-nostdinc", "-isystem", resource, "-isystem", c_install / "usr/include", "-I", work,
                        "-Werror", "-Wno-deprecated-declarations", "-O2", "-fno-stack-protector", *defines,
                        "-c", FIXTURE, "-o", obj], work)
            imports = run(llvm / "bin/llvm-nm", ["-um", obj], work).splitlines()
            if {item.strip() for item in imports} != {f"(undefined) external {name}" for name in expected}:
                raise ValueError(f"{arch} {case}: changed TSan public imports: {imports}")
            result[arch][case] = {"object_sha256": digest(obj), "imports": sorted(expected)}
    return result


def install(sdk, source_roots, llvm, c_install, work, images, inventories, *, minimum):
    evidence = json.loads(RECORD.read_bytes())
    if sdk != evidence["sdk"]:
        raise ValueError(f"the TSan public linker review applies only to {evidence['sdk']}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the TSan public linker review covers macOS deployment minima 11.0–26.5")
    if set(source_roots) != set(evidence["sources"]) or set(inventories) != set(ARCHES):
        raise ValueError("TSan public linker inputs require pinned Libc, libplatform and compiler-rt, and both client slices")
    sources = {name: read_source(source_roots[name].resolve(), pin["files"])
               for name, pin in evidence["sources"].items()}
    slices = qualify(sources["compiler-rt"], evidence["fileno_declaration"], llvm.resolve(),
                     c_install.resolve(), work, minimum)
    libc_symbols = {"_realpath", "_fileno_unlocked"}
    platform = [item["slices"] for item in images if item["install_name"] == PLATFORM]
    libc = [item["slices"] for item in images if item["install_name"] == LIBC]
    if len(platform) != 1 or len(libc) != 1 or set(platform[0]) != set(ARCHES) or set(libc[0]) != set(ARCHES):
        raise ValueError("TSan public linker inputs require one libsystem_platform and libsystem_c provider on both slices")
    owners = {**dict.fromkeys(CONTEXT_EXPORTS, PLATFORM), **dict.fromkeys(libc_symbols, LIBC)}
    for image in images:
        name = image["install_name"]
        for arch, part in image["slices"].items():
            for symbol, owner in owners.items():
                existing = part["exports"].get(symbol)
                if symbol in part.get("symbol_reexports", {}) or (
                    existing is not None and (name != owner or existing != TEXT)
                ):
                    raise ValueError(f"{arch}: conflicting TSan public definition for {symbol} in {name}")
    for arch in ARCHES:
        platform[0][arch]["exports"].update(dict.fromkeys(CONTEXT_EXPORTS, TEXT))
        libc[0][arch]["exports"].update(dict.fromkeys(libc_symbols, TEXT))
        for symbol in sorted(owners):
            inventories[arch].append({"symbol": symbol, "kind": "function",
                                      "header": evidence["origins"][symbol]["client"]})
    return {**evidence, "minimum": minimum, "fixture_sha256": digest(FIXTURE), "slices": slices,
            "provider_by_symbol": dict(sorted(owners.items()))}
