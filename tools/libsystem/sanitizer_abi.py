"""Qualify the pinned Darwin compiler-rt imports and install their reviewed providers."""

import json
from pathlib import Path
import re

from .component_graph import read_source
from .emit import ARCHES, KINDS, version
from .scan import digest, run


RECORD = Path(__file__).parent / "data/macosx26.5/sanitizer-abi.json"
TSAN_RECORD = RECORD.with_name("sanitizer-tsan-locks.json")
FUZZER_RECORD = RECORD.with_name("sanitizer-fuzzer.json")
UNDEFINED = re.compile(r"\s*\(undefined\) (weak )?external (\w+)")


def locked_evidence(include_tsan, *, include_fuzzer=False):
    evidence = json.loads(RECORD.read_bytes())
    if include_tsan:
        extension = json.loads(TSAN_RECORD.read_bytes())
        evidence["sources"]["compiler-rt"]["files"].update(extension["compiler_rt_files"])
        evidence["sources"]["libplatform"] = extension["libplatform"]
        evidence["groups"].append(extension["group"])
    if include_fuzzer:
        extension = json.loads(FUZZER_RECORD.read_bytes())
        evidence["sources"]["compiler-rt"]["files"].update(extension["compiler_rt_files"])
        evidence["sources"]["dyld"]["files"].update(extension["dyld_files"])
        evidence["groups"].append(extension["group"])
    return evidence


def excerpt(source, span):
    lines = source[span["file"]].splitlines()
    return "\n".join(line for start, end in span["lines"] for line in lines[start - 1:end])


def consumer_source(evidence, compiler_rt):
    source = [
        "using size_t = __SIZE_TYPE__;",
        "using intptr_t = __INTPTR_TYPE__;",
        "using off_t = __INT64_TYPE__;",
        "using pid_t = __INT32_TYPE__;",
        "using uuid_t = unsigned char[16];",
        "struct _malloc_zone_t;",
        "using malloc_zone_t = _malloc_zone_t;",
        "struct mach_header;",
        "struct dyld_shared_cache_dylib_text_info;",
        excerpt(compiler_rt, evidence["consumer_weak_attribute"]),
        'extern "C" {',
    ]
    references = []
    for group in evidence["groups"]:
        kind = KINDS[group["kind"]]
        declaration = group["consumer_declarations"]
        lines = excerpt(compiler_rt, declaration)
        if declaration.get("form") == "tsan_interceptor":
            # The pinned Darwin expansion declares the original with C linkage before interposing it.
            source.extend([
                "struct os_unfair_lock_s;",
                "using os_unfair_lock_t = os_unfair_lock_s *;",
                "using u32 = __UINT32_TYPE__;",
                "#define TSAN_INTERCEPTOR(ret, func, ...) ret func(__VA_ARGS__);",
                lines.replace(" {", ""),
                "#undef TSAN_INTERCEPTOR",
            ])
        else:
            source.append(lines)
        for name in group["c_names"]:
            expected = "true" if kind == "function" else "false"
            references.extend([
                f"static_assert(__is_function(decltype({name})) == {expected});",
                f"decltype(&{name}) reference_{name} = &{name};",
            ])
    return "\n".join([*source, "}", *references, ""])


def qualify(evidence, source, llvm, work, minimum):
    expected = {
        "_" + name: {"kind": KINDS[group["kind"]], "weak_import": group["weak_import"]}
        for group in evidence["groups"] for name in group["c_names"]
    }
    expected_weak = {symbol: record["weak_import"] for symbol, record in expected.items()}
    work.mkdir()
    client = work / "client.cpp"
    client.write_text(source, encoding="utf-8")
    results = {}
    for arch in ARCHES:
        obj = work / f"{arch}.o"
        run(llvm / "bin/clang",
            ["--no-default-config", "-target", f"{arch}-apple-macos{minimum}", "-std=c++17",
             "-nostdinc", "-fblocks", "-Werror", "-c", client, "-o", obj], work)
        imports = {}
        for line in run(llvm / "bin/llvm-nm", ["-um", obj], work).splitlines():
            match = UNDEFINED.fullmatch(line)
            if not match or match[2] in imports:
                raise ValueError(f"{arch}: unexpected sanitizer import record {line!r}")
            imports[match[2]] = bool(match[1])
        if imports != expected_weak:
            raise ValueError(f"{arch}: changed sanitizer imports: {imports!r}")
        results[arch] = {"object_sha256": digest(obj), "imports": expected}
    return {"source_sha256": digest(client), "slices": results}


def install(sdk, source_roots, llvm, work, images, inventories, *, minimum, include_fuzzer=False):
    evidence = locked_evidence("libplatform" in source_roots, include_fuzzer=include_fuzzer)
    if sdk != evidence["sdk"]:
        raise ValueError(f"the reviewed sanitizer ABI applies only to {evidence['sdk']}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed sanitizer ABI covers macOS deployment minima 11.0–26.5")
    if set(source_roots) != set(evidence["sources"]):
        raise ValueError(f"sanitizer ABI requires pinned sources for {', '.join(evidence['sources'])}")
    if set(inventories) != set(ARCHES):
        raise ValueError("sanitizer ABI requires both client inventories")

    sources = {
        name: read_source(source_roots[name].resolve(), pin["files"])
        for name, pin in evidence["sources"].items()
    }
    symbols = {
        "_" + name: (group["provider"], group["kind"], group["consumer_declarations"]["file"])
        for group in evidence["groups"] for name in group["c_names"]
    }
    components = {}
    for group in evidence["groups"]:
        name = group["provider"]
        owners = [image["slices"] for image in images if image["install_name"] == name]
        if len(owners) != 1 or set(owners[0]) != set(ARCHES):
            raise ValueError(f"sanitizer ABI requires one {name} component with both target slices")
        components[name] = owners[0]

    for image in images:
        owner = image["install_name"]
        for arch, part in image["slices"].items():
            for symbol, (provider, kind, _) in symbols.items():
                if symbol in part.get("symbol_reexports", {}) or (
                    symbol in part["exports"] and (owner != provider or part["exports"][symbol] != kind)
                ):
                    raise ValueError(f"{arch}: conflicting sanitizer ABI export {symbol} in {owner}")

    client = qualify(evidence, consumer_source(evidence, sources["compiler-rt"]), llvm, work, minimum)
    for arch in ARCHES:
        for symbol, (provider, kind, source) in symbols.items():
            components[provider][arch]["exports"][symbol] = kind
            inventories[arch].append({"symbol": symbol, "kind": KINDS[kind], "header": source})
    return {**evidence, "minimum": minimum, "client": client}
