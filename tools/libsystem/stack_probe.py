"""Install the macOS 26.5 Darwin stack-probe definition and forwarding alias."""

from copy import deepcopy

from .emit import ARCHES, version


PTHREAD = "/usr/lib/system/libsystem_pthread.dylib"
COMPILER_RT = "/usr/lib/system/libcompiler_rt.dylib"
IMPLEMENTATION = "____chkstk_darwin"
ALIAS = "___chkstk_darwin"
KIND = "text.global"
SDK = "macosx26.5"
REFERENCE_BUILD = "25F70"
HOST_BUILD = "25F84"
MINIMA = ("11.0", "26.5")
PTHREAD_SOURCE = {
    "project": "apple-oss-distributions/libpthread",
    "commit": "1f4f5265b319111142f1bf3a27d4484ef5a98314",
    "license": "APSL-2.0",
    "files": {
        "src/pthread_asm.s": "8b202ef657db0a949b3767a02cb0ade3e3a9912a36e01b000d2c0b35bf490b15",
        "libpthread.xcodeproj/project.pbxproj": "fc56c893f7af33c2900606bd554cf60764df45b292f9d028a78a2e075e94b6a8",
        "xcodescripts/pthread.xcconfig": "8de6fbcc5d3c719e6f23d5978f2f06070b1e016ff798f6a204a511ee383fed8a",
    },
    "definition_lines": {"arm64": 282, "x86_64": 60},
    "dylib_target_line": 1077,
    "dylib_source_phase_line": 1541,
}
RUNTIME = {
    "arm64": {
        "slice": "arm64e",
        "compiler_rt_uuid": "AA79151F-C19D-3C7C-92F8-B10F04D82C1C",
        "pthread_uuid": "4F33683C-18C8-39A1-800B-2E3BD43BCC13",
    },
    "x86_64": {
        "slice": "x86_64",
        "compiler_rt_uuid": "FC63EFD8-77F0-3FAF-BDF3-9872BEF083D7",
        "pthread_uuid": "87323FF7-EDDB-329C-A3BD-6521A131C864",
    },
}


def install(sdk, images, *, minimum="11.0"):
    if sdk != SDK:
        raise ValueError(f"the reviewed stack-probe rule applies only to {SDK}")
    parts = tuple(map(int, version(minimum).split(".")))
    if not (11, 0, 0) <= parts + (0,) * (3 - len(parts)) <= (26, 5, 0):
        raise ValueError("the reviewed stack-probe rule covers macOS deployment minima 11.0–26.5")

    components = {}
    for name in (PTHREAD, COMPILER_RT):
        owners = [image["slices"] for image in images if image["install_name"] == name]
        if len(owners) != 1 or set(owners[0]) != set(ARCHES):
            raise ValueError(f"stack probes require one {name} component with both target slices")
        components[name] = owners[0]

    forward = {"kind": KIND, "target_library": PTHREAD, "target_symbol": IMPLEMENTATION}
    symbols = {ALIAS, IMPLEMENTATION}
    for image in images:
        owner = image["install_name"]
        allowed_exports = {IMPLEMENTATION: KIND} if owner == PTHREAD else {}
        allowed_reexports = {ALIAS: forward} if owner == COMPILER_RT else {}
        for arch, part in image["slices"].items():
            for key, allowed in (("exports", allowed_exports), ("symbol_reexports", allowed_reexports)):
                existing = part.get(key, {})
                for symbol in sorted(symbols.intersection(existing)):
                    if symbol not in allowed or existing[symbol] != allowed[symbol]:
                        raise ValueError(f"{arch}: conflicting stack-probe {key} for {symbol} in {owner}")

    for arch in ARCHES:
        components[PTHREAD][arch]["exports"][IMPLEMENTATION] = KIND
        components[COMPILER_RT][arch].setdefault("symbol_reexports", {})[ALIAS] = forward.copy()

    return {
        "schema": 1,
        "sdk": sdk,
        "minimum": minimum,
        "source": deepcopy(PTHREAD_SOURCE),
        "definition": {"image": PTHREAD, "symbol": IMPLEMENTATION, "kind": KIND},
        "forwarding": {"image": COMPILER_RT, "symbol": ALIAS, **forward},
        "qualification": {
            "approved_by": "Corentin Kerisit",
            "reference_sdk_build": REFERENCE_BUILD,
            "reference_alias_role": "export",
            "runtime_build": HOST_BUILD,
            "runtime_targets": deepcopy(RUNTIME),
            "paired_link_minima": list(MINIMA),
            "reopen_on": ["changed pinned pthread source", "changed Apple reference role",
                          "changed runtime identity, provider or forwarding role", "changed two-level client link"],
        },
    }
