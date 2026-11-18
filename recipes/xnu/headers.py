"""Pinned XNU public lists, unifdef transformations, and user MIG headers."""

import re
import subprocess
from pathlib import Path

from recipes.assembly import Assembly
from .mig import generate as generate_mig

ROOT = Path(__file__).resolve().parents[2]

XNU_PUBLIC_MAKE_DIRS = (
    ("bsd/sys", "sys", "INSTALL_MI_LIST"),
    ("bsd/sys/_types", "sys/_types", "INSTALL_MI_LIST"),
    ("bsd/machine", "machine", "INSTALL_MI_LIST"),
    ("bsd/arm", "arm", "INSTALL_MD_LIST"),
    ("bsd/i386", "i386", "INSTALL_MD_LIST"),
    ("bsd/netinet", "netinet", "INSTALL_MI_LIST"),
    ("bsd/netinet6", "netinet6", "INSTALL_MI_LIST"),
    ("bsd/bsm", "bsm", "INSTALL_MI_LIST"),
    ("libkern/os", "os", "INSTALL_MI_LIST"),
    ("osfmk/mach", "mach", "INSTALL_MI_LIST"),
    ("osfmk/mach/machine", "mach/machine", "INSTALL_MI_LIST"),
    ("osfmk/mach/arm", "mach/arm", "INSTALL_MD_LIST"),
    ("osfmk/mach/i386", "mach/i386", "INSTALL_MD_LIST"),
    ("osfmk/mach_debug", "mach_debug", "INSTALL_MI_LIST"),
)



def xnu_public_make_headers(source_dir: str, list_name: str) -> list[str]:
    makefile = ROOT / "sources/xnu" / source_dir / "Makefile"
    assignments: dict[str, str] = {}
    lines = makefile.read_text().splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].split("#", 1)[0]
        match = re.match(r"^([A-Z_]+)\s*[:+?]?=\s*(.*)", line)
        if not match:
            index += 1
            continue
        name, value = match.groups()
        while value.rstrip().endswith("\\") and index + 1 < len(lines):
            index += 1
            value = value.rstrip()[:-1] + " " + lines[index].split("#", 1)[0]
        assignments.setdefault(name, value)
        index += 1

    def expand(value: str) -> str:
        pattern = r"\$[({]([A-Z_]+)[)}]"
        for _ in range(8):
            if not re.search(pattern, value):
                return value
            def substitute(match: re.Match[str]) -> str:
                variable = ("EMBEDDED_PRIVATE_DATAFILES" if match.group(1) == "EXTRA_DATAFILES"
                            else match.group(1))
                if ((source_dir == "osfmk/device" and variable == "_MIG_HDRS_") or
                        (source_dir == "osfmk/atm" and variable in {"MIG_TYPES", "MIG_DEFS"})):
                    # These pinned generated lists are empty for the public C files.
                    return ""
                return assignments[variable]
            value = re.sub(pattern, substitute, value)
        raise ValueError(f"unresolved XNU Makefile list: {makefile}")

    headers = sorted(set(re.findall(r"[\w./-]+\.h\b",
                                    expand(assignments[list_name]))))
    if not headers:
        raise ValueError(f"empty XNU public header list: {makefile}")
    return headers


def libsyscall_public_mach_headers() -> list[str]:
    script = (ROOT / "sources/xnu/libsyscall/xcodescripts/mach_install_mig.sh").read_text()
    match = re.search(r'^MACH_HDRS="(.*?)"$', script, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError("libsyscall public Mach header list missing")
    headers = match.group(1).split()
    if len(headers) != 10 or len(set(headers)) != 10:
        raise ValueError(f"libsyscall public Mach header list changed: {headers}")
    return headers


def xnu_public_flags() -> list[str]:
    # xnu/makedefs/MakeInc.cmd SUPPORTED_PLATFORMS and MakeInc.def
    # SINCFRAME_UNIFDEF: macOS public installhdrs variant.
    other_platforms = (
        "DriverKit ExclaveKit ExclaveCore iPhoneOS iPhoneOSNano tvOS "
        "AppleTVOS WatchOS XROS BridgeOS iPhoneSimulator "
        "iPhoneNanoSimulator tvSimulator AppleTVSimulator WatchSimulator "
        "XRSimulator"
    ).split()
    private = (
        "MACH_KERNEL_PRIVATE BSD_KERNEL_PRIVATE IOKIT_KERNEL_PRIVATE "
        "LIBKERN_KERNEL_PRIVATE LIBSA_KERNEL_PRIVATE "
        "PEXPERT_KERNEL_PRIVATE XNU_KERNEL_PRIVATE KERNEL_PRIVATE KERNEL "
        "PRIVATE DRIVERKIT EXCLAVEKIT EXCLAVECORE SCHED_TEST_HARNESS"
    ).split()
    return (["-DXNU_PLATFORM_MacOSX"] +
            [f"-UXNU_PLATFORM_{name}" for name in other_platforms] +
            [f"-U{name}" for name in private] +
            ["-DMODULES_SUPPORTED", "-D_OPEN_SOURCE_", "-D__OPEN_SOURCE__"])

def produce_unifdef(assembly: Assembly) -> None:
    xnu = ROOT / "sources/xnu"
    for name, source, extra in (
        ("sys/cdefs.h", xnu / "bsd/sys/cdefs.h", []),
        ("device/device_types.h", xnu / "osfmk/device/device_types.h", ["-DIOKIT"]),
    ):
        result = subprocess.run(["unifdef", *xnu_public_flags(), *extra, str(source)],
                                capture_output=True, check=False)
        if result.returncode not in (0, 1):
            raise ValueError(f"XNU {name} unifdef failed: {result.stderr!r}")
        if name == "sys/cdefs.h":
            origin = f"generated:apple via inputs/header-sources.tsv:{name}"
            selection = "header-sources.tsv"
        else:
            origin = f"generated:{name} via install_c.py:generated_apple_headers"
            selection = "generated explicit"
        assembly.add("xnu", f"usr/include/{name}", result.stdout, origin, selection,
                     inputs=(source.relative_to(ROOT).as_posix(),),
                     transform="macOS public unifdef")


def produce_symbol_headers(assembly: Assembly, temporary: Path) -> None:
    xnu = ROOT / "sources/xnu"
    availability = ROOT / "sources/AvailabilityVersions"
    tool = temporary / "sdk/usr/local/libexec"
    tool.mkdir(parents=True)
    (tool / "availability.pl").symlink_to(availability / "availability")
    (tool / "availability.dsl").symlink_to(availability / "availability.dsl")
    symbol = temporary / "_symbol_aliasing.h"
    subprocess.run(["bash", str(xnu / "bsd/sys/make_symbol_aliasing.sh"),
                    str(temporary / "sdk"), str(symbol)], check=True)
    posix = temporary / "_posix_availability.h"
    subprocess.run(["sh", str(xnu / "bsd/sys/make_posix_availability.sh"),
                    str(posix)], check=True)
    for name, source in (("sys/_symbol_aliasing.h", symbol),
                         ("sys/_posix_availability.h", posix)):
        assembly.add("xnu", f"usr/include/{name}", source.read_bytes(),
                     f"generated:apple via inputs/header-sources.tsv:{name}",
                     "header-sources.tsv",
                     inputs=(("sources/xnu/bsd/sys/make_symbol_aliasing.sh",
                              "sources/AvailabilityVersions/availability.dsl")
                             if name == "sys/_symbol_aliasing.h" else
                             ("sources/xnu/bsd/sys/make_posix_availability.sh",)),
                     transform="XNU public header generator")


def produce_mig(assembly: Assembly, mig: Path, clang: Path,
                sysroot: Path, temporary: Path) -> None:
    out = temporary / "mig"
    generate_mig(mig, clang, sysroot, out)
    for source in sorted((out / "arm64/mach").glob("*.h")):
        assembly.add("xnu", f"usr/include/mach/{source.name}", source.read_bytes(),
                     f"generated:system-mig:{source.name} via generate_mig.py",
                     "xnu/libsyscall/xcodescripts/mach_install_mig.sh:public",
                     inputs=(f"sources/xnu/libsyscall/mach/{source.stem}.defs",
                             "sources/xnu/libsyscall/xcodescripts/filter_mig.awk"),
                     transform="system MIG for arm64 and x86_64, then filter")
