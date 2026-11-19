"""Verify the pinned compiler's implicit Darwin calls before installing their reviewed providers."""

import json
from pathlib import Path

from .emit import ARCHES
from .scan import digest, run


HERE = Path(__file__).parent
RECORD = HERE / "data/macosx26.5/compiler-clients.json"


def install(sdk, llvm, c_install, minimum, work, images, inventories):
    evidence = json.loads(RECORD.read_bytes())
    if sdk != evidence["sdk"]:
        raise ValueError(f"no qualified compiler client evidence for {sdk}")
    by_name = {image["install_name"]: image for image in images}
    work.mkdir()
    for index, case in enumerate(evidence["clients"]):
        owner = by_name.get(case.get("provider"))
        if case["text_exports"] and owner is None:
            raise ValueError(f"missing reviewed compiler ABI provider: {case['provider']}")
        folder = HERE / "fixtures"
        options = []
        if case.get("installed_header_client"):
            folder = HERE.parents[1] / "tests/installed_headers"
            resource = Path(run(llvm / "bin/clang", ["--no-default-config", "-print-resource-dir"], work).strip())
            includes = resource.resolve() / "include"
            if not includes.is_dir() or not includes.is_relative_to(llvm):
                raise ValueError("unexpected Clang resource directory for installed-header client")
            options.extend(["-std=c17", "-isysroot", c_install, "-isystem", includes,
                            "-isystem", c_install / "usr/include", *case.get("defines", [])])
        fixture = folder / case["fixture"]
        case["fixture_sha256"] = digest(fixture)
        for arch in ARCHES:
            part = case["slices"][arch]
            obj = work / f"{index}-{fixture.stem}-{arch}.o"
            run(llvm / "bin/clang", ["--no-default-config", "-target", f"{arch}-apple-macos{minimum}",
                                     "-nostdinc", "-O2", *options, "-c", fixture, "-o", obj], work)
            observed = set(run(llvm / "bin/llvm-nm", ["-uj", obj], work).splitlines())
            expected = set(case["text_exports"]) | set(part["additional_imports"])
            if observed != expected:
                raise ValueError(f"{arch} {fixture.name}: review changed compiler imports "
                                 f"(new {sorted(observed - expected)}, absent {sorted(expected - observed)})")
            part["object_sha256"] = digest(obj)
            for symbol in case["text_exports"]:
                exports = owner["slices"][arch]["exports"]
                if exports.setdefault(symbol, "text.global") != "text.global":
                    raise ValueError(f"{arch}: conflicting compiler ABI definition for {symbol}")
                inventories[arch].append({"symbol": symbol, "kind": "function", "header": case["source"][0]})
            for symbol in part["additional_imports"]:
                # ld supplies the image-local DSO handle. Other imports still need an ordinary provider.
                if symbol != "___dso_handle":
                    inventories[arch].append({"symbol": symbol, "kind": "function", "header": case["source"][0]})
    return evidence
