"""Derive the Darwin libunwind linker interface and verified compatibility exports."""

import json
from pathlib import Path
import re

from .component_graph import read_source
from .emit import ARCHES, KINDS, version
from .scan import digest, run


HERE = Path(__file__).resolve().parent
RECORD = HERE / "data/macosx26.5/libunwind-abi.json"
PUBLIC = HERE / "fixtures/libunwind_public.c"
CLEANUP = HERE / "fixtures/libunwind_cleanup.cpp"
RELATIVE_BASES = HERE / "fixtures/libunwind_relative_bases.S"
RELATIVE_BASE_SYMBOLS = {"__Unwind_GetDataRelBase", "__Unwind_GetTextRelBase"}
PROVIDER = "/usr/lib/system/libunwind.dylib"
RESUME = "__Unwind_Resume"
LOCAL_ADDRESS_SPACE = "_unw_local_addr_space"
IMPLEMENTATIONS = {
    "UnwindLevel1.c": ("-std=c99",),
    "UnwindLevel1-gcc-ext.c": ("-std=c99",),
    # Probe native definitions. The published tree lacks the ARM32 constants
    # required to compile the CMake cache's cross-unwind configuration.
    "libunwind.cpp": ("-std=c++11", "-D_LIBUNWIND_IS_NATIVE_ONLY"),
    "UnwindRegistersSave.S": (),
}
EXTERNAL = re.compile(r"\((__\w+),(__\w+)\) (weak )?external (?:\[cold func\] )?(\S+)$")
SECTIONS = {("__TEXT", "__text"): "text.global", ("__DATA", "__data"): "data.global"}


def definitions(nm, objects, symbols, work):
    result = {}
    for obj in objects:
        for line in run(nm, ["-gUm", obj], work).splitlines():
            match = EXTERNAL.search(line)
            if not match or match[4] not in symbols:
                continue
            segment, section, weak, symbol = match.groups()
            kind = SECTIONS.get((segment, section))
            if symbol in result or weak or not kind:
                raise ValueError(f"ambiguous or unsupported libunwind definition for {symbol}: {line}")
            result[symbol] = kind, obj.stem
    if set(result) != symbols:
        raise ValueError(f"missing libunwind definitions: {sorted(symbols - set(result))}")
    return result


def derive(source, llvm, c_install, minimum, work, expected_count):
    clang = llvm / "bin/clang"
    nm = llvm / "bin/llvm-nm"
    work.mkdir()
    resource = Path(run(clang, ["--no-default-config", "-print-resource-dir"], work).strip()).resolve() / "include"
    if not resource.is_dir() or not resource.is_relative_to(llvm):
        raise ValueError("unexpected Clang resource directory for libunwind")
    result = {}
    for arch in ARCHES:
        target = f"{arch}-apple-macos{minimum}"
        base = ["--no-default-config", "-target", target, "-nostdinc", "-O2", "-fno-stack-protector"]
        includes = ["-I", source / "include", "-isystem", resource, "-isystem", c_install / "usr/include"]
        public = work / f"{arch}-public.o"
        cleanup = work / f"{arch}-cleanup.o"
        relative_bases = work / f"{arch}-relative-bases.o"
        run(clang, [*base, *includes, "-std=c11", "-c", PUBLIC, "-o", public], work)
        run(clang, [*base, "-std=c++17", "-fexceptions", "-c", CLEANUP, "-o", cleanup], work)
        run(clang, [*base, "-c", RELATIVE_BASES, "-o", relative_bases], work)
        symbols = set(run(nm, ["-uj", public], work).splitlines())
        compatibility = set(run(nm, ["-uj", relative_bases], work).splitlines())
        if compatibility != RELATIVE_BASE_SYMBOLS or symbols & compatibility:
            raise ValueError(f"{arch}: unexpected libunwind compatibility references")
        imports = sorted(set(run(nm, ["-uj", cleanup], work).splitlines()))
        if len(symbols) != expected_count or not {RESUME, LOCAL_ADDRESS_SPACE} <= symbols or RESUME not in imports:
            raise ValueError(f"{arch}: changed public libunwind or compiler cleanup surface")
        objects = []
        for name, flags in IMPLEMENTATIONS.items():
            obj = work / f"{arch}-{name}.o"
            run(clang, [*base, *includes, *flags, "-U__STRICT_ANSI__", "-DNDEBUG",
                        "-fno-exceptions", "-funwind-tables", "-c", source / "src" / name, "-o", obj], work)
            objects.append(obj)
        owned = definitions(nm, objects, symbols | compatibility, work)
        # The public libunwind.h fixture names one object. Its other imports
        # and all supported unwind.h entries are functions. The separately
        # selected compatibility symbols are functions as well.
        kinds = {name: "data.global" if name == LOCAL_ADDRESS_SPACE else "text.global"
                 for name in symbols | compatibility}
        if {name: definition[0] for name, definition in owned.items()} != kinds:
            raise ValueError(f"{arch}: libunwind definition kinds differ from the selected interface")
        result[arch] = {name: (kind, owned[name][1]) for name, kind in kinds.items()}, imports
    return result


def install(sdk, source, llvm, c_install, minimum, work, images, inventories):
    evidence = json.loads(RECORD.read_bytes())
    if sdk != evidence["sdk"]:
        raise ValueError(f"the reviewed libunwind recipe applies only to {evidence['sdk']}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed libunwind recipe covers macOS deployment minima 11.0–26.5")
    source = source.resolve()
    read_source(source, evidence["source"]["files"])
    owners = [image["slices"] for image in images if image["install_name"] == PROVIDER]
    if len(owners) != 1 or set(owners[0]) != set(ARCHES) or set(inventories) != set(ARCHES):
        raise ValueError("the libunwind recipe requires one provider and inventory for both client slices")
    slices = owners[0]
    results = derive(source / "libunwind", llvm.resolve(), c_install.resolve(), minimum,
                     work, evidence["public_count"])
    receipt = {}
    for arch, (exports, imports) in results.items():
        for image in images:
            owner = image["install_name"]
            part = image["slices"].get(arch, {})
            for symbol, (kind, _) in exports.items():
                existing = part.get("exports", {}).get(symbol)
                if symbol in part.get("symbol_reexports", {}) or (
                    existing is not None and (owner != PROVIDER or existing != kind)
                ):
                    raise ValueError(f"{arch}: conflicting libunwind definition for {symbol} in {owner}")
        receipt[arch] = {"compiler_cleanup_imports": imports, "exports": {}, "compatibility_exports": {}}
        for symbol, (kind, obj) in sorted(exports.items()):
            slices[arch]["exports"][symbol] = kind
            rel = "libunwind/src/" + obj.removeprefix(f"{arch}-")
            inventories[arch].append({"symbol": symbol, "kind": KINDS[kind], "header": f"libunwind/{rel}"})
            scope = "compatibility_exports" if symbol in RELATIVE_BASE_SYMBOLS else "exports"
            receipt[arch][scope][symbol] = {"kind": kind, "source": rel}
    return {**evidence, "minimum": minimum, "provider": PROVIDER, "slices": receipt,
            "client_sha256": {path.name: digest(path) for path in (PUBLIC, CLEANUP, RELATIVE_BASES)}}
