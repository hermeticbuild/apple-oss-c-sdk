"""Qualify the scanned binary16 math imports against the reviewed libm export set."""

import hashlib
import re


HEADER = "usr/include/math.h"
RECIPE = "recipes/libm/half_math.h"
PROVIDER = "/usr/lib/system/libsystem_m.dylib"
# Sorted Mach-O names from libm joined to function types from LLVM libc math.yaml.
ABI_SHA256 = "3272d6721f36fe10f2d003069afd7be7e49e357745e34aad840eee4d2c59710c"


def install(arch, scan, images):
    rows = [row for row in scan["imports"]
            if row["public_root"] == HEADER and row["header"] == HEADER
            and re.fullmatch(r"__[a-z]+f16", row["c_name"])]
    names = sorted(row["symbol"] for row in rows)
    types = {decl["offset"]: decl["type"] for decl in scan["declarations"]
             if decl["public_root"] == HEADER and decl["header"] == HEADER}
    entries = sorted(f"{row['symbol']}\t{types[row['declaration_offset']]}\n" for row in rows)
    digest = hashlib.sha256("".join(entries).encode()).hexdigest()
    if digest != ABI_SHA256 or any(row["kind"] != "function" for row in rows):
        raise ValueError(f"{arch}: review changed math.h binary16 imports: {names}")
    before_introduction = int(scan["minimum"].split(".")[0]) < 15
    if any(row["weak_import"] != before_introduction for row in rows):
        raise ValueError(f"{arch}: unexpected binary16 import strength at macOS {scan['minimum']}")

    image = next((image for image in images if image["install_name"] == PROVIDER), None)
    if image is None or arch not in image["slices"]:
        raise ValueError(f"{arch}: missing binary16 provider {PROVIDER}")
    exports = image["slices"][arch]["exports"]
    for name in names:
        if exports.setdefault(name, "text.global") != "text.global":
            raise ValueError(f"{arch}: conflicting binary16 definition for {name}")
    return rows
