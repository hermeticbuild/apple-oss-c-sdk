"""Read the public macOS 26.5 Libc linker alias list and its consuming rule."""

import hashlib
import re

from .emit import ARCHES

LIBC = "/usr/lib/system/libsystem_c.dylib"
PLATFORM = "/usr/lib/system/libsystem_platform.dylib"
REVISION = "4e34d0559e3a1b081afeb8604d9e204a1f31321d"
FILES = {
    "xcodescripts/alias.list": "6084b660412cd5a37a8a8bf6f765b17d516c93b401e055246c5cb3210e9731f8",
    "xcodescripts/libc.xcconfig": "eddf64eace5e2d6c84fd10bdb87bf23eb97bd809cde6212b6f729fbe489f2200",
}


def read_aliases(source):
    for name, expected in FILES.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"review the changed Libc alias rule or input: {name}")
    result = {}
    for line in (source / "xcodescripts/alias.list").read_text().splitlines():
        implementation, public = line.split()
        if public in result or not all(re.fullmatch(r"_\w+", n) for n in (public, implementation)):
            raise ValueError(f"invalid Libc alias: {line}")
        result[public] = implementation
    return result


def forwarding_record(implementation):
    return {"kind": "text.global", "target_library": PLATFORM, "target_symbol": implementation}


def install_aliases(source, sdk, images):
    if sdk != "macosx26.5":
        raise ValueError("the reviewed Libc alias rule applies only to macOS 26.5")
    aliases = read_aliases(source)
    owners = [image for image in images if image["install_name"] == LIBC]
    if len(owners) != 1 or set(owners[0]["slices"]) != set(ARCHES):
        raise ValueError("Libc aliases require the libsystem_c component on both targets")
    for part in owners[0]["slices"].values():
        forwarded = part.setdefault("symbol_reexports", {})
        for public, implementation in aliases.items():
            record = forwarding_record(implementation)
            if public in part["exports"] or forwarded.get(public, record) != record:
                raise ValueError(f"component evidence conflicts with Libc linker alias {public}")
            forwarded[public] = record
