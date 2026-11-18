"""Pinned XNU public lists, unifdef transformations, and user MIG headers."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

XNU_PUBLIC_MAKE_DIRS = (
    ("bsd/sys", "sys", "INSTALL_MI_LIST"),
    ("bsd/sys/_types", "sys/_types", "INSTALL_MI_LIST"),
    ("bsd/machine", "machine", "INSTALL_MI_LIST"),
    ("bsd/arm", "arm", "INSTALL_MD_LIST"),
    ("bsd/i386", "i386", "INSTALL_MD_LIST"),
    ("bsd/uuid", "uuid", "INSTALL_MI_LIST"),
    ("osfmk/arm", "arm", "INSTALL_MD_LIST"),
    ("osfmk/i386", "i386", "INSTALL_MD_LIST"),
    ("libkern/libkern/arm", "libkern/arm", "INSTALL_MD_LIST"),
    ("libkern/libkern/i386", "libkern/i386", "INSTALL_MD_LIST"),
    ("bsd/net", "net", "INSTALL_MI_LIST"),
    ("libkern/libkern", "libkern", "INSTALL_MI_LIST"),
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


def public_copies():
    for source_dir, target_dir, list_name in XNU_PUBLIC_MAKE_DIRS:
        rule = f"{source_dir}/Makefile:{list_name}"
        for name in xnu_public_make_headers(source_dir, list_name):
            if (target_dir, name) == ("sys", "cdefs.h"):
                continue  # The filtered public variant is generated below.
            yield (f"usr/include/{target_dir}/{name}",
                   f"sources/xnu/{source_dir}/{name}", rule)
    for name in libsyscall_public_mach_headers():
        yield (f"usr/include/mach/{name}", f"sources/xnu/libsyscall/mach/mach/{name}",
               "xnu/libsyscall/xcodescripts/mach_install_mig.sh:MACH_HDRS")

    # Libsyscall.xcodeproj: public phases for gethostuuid and spawn; the
    # embedded-private copy phase resolves to /usr/include on macOS for libproc.
    for name, path in (
        ("gethostuuid.h", "gethostuuid.h"),
        ("spawn.h", "spawn/spawn.h"),
        ("libproc.h", "libproc/libproc.h"),
    ):
        yield (f"usr/include/{name}", f"sources/xnu/libsyscall/wrappers/{path}",
               "libsyscall/Libsyscall.xcodeproj/project.pbxproj:macosx")


def produce_public(emit) -> None:
    for path, source, rule in public_copies():
        data = filter_public(ROOT / source)
        if not re.sub(rb"/\*.*?\*/|//[^\n]*", b"", data, flags=re.DOTALL).strip():
            continue  # MakeInc.rule omits files that decomment finds empty.
        deps = ("sources/xnu/libsyscall/xcodescripts/mach_install_mig.sh"
                if rule.endswith(":MACH_HDRS") else "sources/xnu/" + rule.split(":")[0])
        emit("xnu", path, data, f"derived:{source}", rule,
                     inputs=(source, deps, "sources/xnu/makedefs/MakeInc.def",
                             "sources/xnu/makedefs/MakeInc.rule"),
                     transform="macOS public unifdef")


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

def filter_public(source: Path, extra: tuple[str, ...] = ()) -> bytes:
    result = subprocess.run(["unifdef", *xnu_public_flags(), *extra, str(source)],
                            capture_output=True, check=False)
    if result.returncode not in (0, 1):
        raise ValueError(f"XNU {source.name} unifdef failed: {result.stderr!r}")
    return result.stdout


def produce_unifdef(emit) -> None:
    xnu = ROOT / "sources/xnu"
    for name, source, extra in (
        ("sys/cdefs.h", xnu / "bsd/sys/cdefs.h", ()),
        ("device/device_types.h", xnu / "osfmk/device/device_types.h", ("-DIOKIT",)),
    ):
        if name == "sys/cdefs.h":
            origin = f"generated:apple via recipes/xnu/headers.py:{name}"
            selection = "recipes/xnu/headers.py"
        else:
            origin = f"generated:{name} via recipes/xnu/headers.py"
            selection = "generated explicit"
        emit("xnu", f"usr/include/{name}", filter_public(source, extra), origin, selection,
                     inputs=(source.relative_to(ROOT).as_posix(),),
                     transform="macOS public unifdef")


def produce_symbol_headers(emit, temporary: Path) -> None:
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
        emit("xnu", f"usr/include/{name}", source.read_bytes(),
                     f"generated:apple via recipes/xnu/headers.py:{name}",
                     "recipes/xnu/headers.py",
                     inputs=(("sources/xnu/bsd/sys/make_symbol_aliasing.sh",
                              "sources/AvailabilityVersions/availability",
                              "sources/AvailabilityVersions/availability.dsl")
                             if name == "sys/_symbol_aliasing.h" else
                             ("sources/xnu/bsd/sys/make_posix_availability.sh",)),
                     transform="XNU public header generator")



if __name__ == "__main__":
    stage = Path(sys.argv[1])

    def emit(owner, path, data, origin, selection, *, inputs, transform):
        destination = stage / "dst" / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as output:
            output.write(data)
        print(path, owner, origin, selection, transform, *inputs, sep="\t")

    produce_public(emit)
    produce_unifdef(emit)
    produce_symbol_headers(emit, stage)
