"""Libc's public header install rule and selected unifdef outputs."""

import csv
import os
import re
import shlex
import subprocess
from pathlib import Path

from recipes.assembly import Assembly

ROOT = Path(__file__).resolve().parents[2]



def libc_public_headers() -> list[str]:
    script = (ROOT / "sources/Libc/xcodescripts/headers.sh").read_text()
    macos = script.split("else # DRIVERKITSDK", 1)[0]
    groups = (
        ("INC_INSTHDRS", ""), ("INC_ARPA_INSTHDRS", "arpa/"),
        ("INC_PROTO_INSTHDRS", "protocols/"),
        ("INC_SECURE_INSTHDRS", "secure/"),
        ("INC_XLOCALE_INSTHDRS", "xlocale/"),
        ("TYPES_INSTHDRS", "_types/"),
        ("SYS_INSTHDRS", "sys/"),
    )
    paths = set()
    for variable, prefix in groups:
        matches = re.findall(r"^" + variable + r"=\((.*?)\)",
                             macos, re.MULTILINE | re.DOTALL)
        if not matches:
            raise ValueError(f"Libc public list missing: {variable}")
        # SYS_INSTHDRS is redefined later in the macOS branch.
        body = matches[-1] if variable == "SYS_INSTHDRS" else matches[0]
        for token in re.findall(r"[\w./${}-]+\.h\b", body):
            paths.add(prefix + Path(token).name)
    # macOS and enabled legacy branches of INC_INSTHDRS; the therm header is
    # selected by FEATURE_THERM_NOTIFICATION_APIS in this pinned source.
    paths.update(("ar.h", "rune.h", "utmp.h", "libkern/OSThermalNotification.h"))
    # headers.sh moves asm.h from usr/include into System.framework private
    # machine headers after installation.
    paths.remove("asm.h")
    if len(paths) != 140:
        raise ValueError(f"Libc public header list changed: {len(paths)}")
    return sorted(paths)


def libc_unifdef_flags() -> list[str]:
    libc = ROOT / "sources/Libc"
    env = os.environ.copy()
    env.update(ARCHS="arm64 x86_64", VARIANT_PLATFORM_NAME="macosx",
               SRCROOT=str(libc), DERIVED_FILES_DIR=str(ROOT / "build/features"))
    output = subprocess.check_output(
        ["perl", str(libc / "xcodescripts/generate_features.pl"), "--unifdef"],
        env=env, text=True)
    return shlex.split(output) + ["-U_USE_EXTENDED_LOCALES_"]


def libc_public_header(source: Path, flags: list[str]) -> bytes:
    # Libc/xcodescripts/headers.sh runs strip-header.ed, then unifdef with
    # generate_features.pl --unifdef on selected public headers.
    original = source.read_text()
    lines = []
    dropping = False
    for line in original.splitlines(keepends=True):
        if line.rstrip("\n") == "//Begin-Libc":
            dropping = True
            continue
        if line.rstrip("\n") == "//End-Libc":
            dropping = False
            continue
        if not dropping:
            lines.append(line)
    if dropping:
        raise ValueError(f"unclosed Begin-Libc marker: {source}")
    text = "".join(lines)
    if any(token in text for token in ("UNIFDEF", "OPEN_SOURCE", "_USE_EXTENDED_LOCALES_")):
        result = subprocess.run(["unifdef", *flags], input=text,
                                text=True, capture_output=True)
        if result.returncode not in (0, 1):
            raise ValueError(f"unifdef failed: {source}: {result.stderr}")
        text = result.stdout
    return text.encode()

def produce(assembly: Assembly) -> None:
    flags = libc_unifdef_flags()
    public = set(libc_public_headers())
    with (ROOT / "inputs/header-sources.tsv").open(newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            relative = row["install_path"]
            if row["source"] != "generated:libc":
                continue
            if relative not in public:
                raise ValueError(f"generated Libc header not in public list: {relative}")
            data = libc_public_header(ROOT / "sources/Libc/include" / relative, flags)
            assembly.add("Libc", f"usr/include/{relative}", data,
                         f"generated:libc via inputs/header-sources.tsv:{relative}",
                         "Libc/xcodescripts/headers.sh:public",
                         inputs=(f"sources/Libc/include/{relative}",
                                 "sources/Libc/xcodescripts/headers.sh",
                                 "sources/Libc/xcodescripts/generate_features.pl"),
                         transform="strip Libc regions and unifdef")
    relative = "utmpx.h"
    data = libc_public_header(ROOT / "sources/Libc/include/NetBSD/utmpx.h", flags)
    assembly.add("Libc", f"usr/include/{relative}", data,
                 "generated:utmpx.h via install_c.py:generated_apple_headers",
                 "generated explicit",
                 inputs=("sources/Libc/include/NetBSD/utmpx.h",
                         "sources/Libc/xcodescripts/generate_features.pl"),
                 transform="strip Libc regions and unifdef")
