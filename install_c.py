#!/usr/bin/env python3
"""Install the selected Apple OSS C headers into an empty sysroot.

This installer reads no Apple SDK Gen content. It applies pinned Apple OSS
header generation rules plus one documented local arm64 `fenv.h` declaration.
See README.md before treating the result as a release.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path

from generate_mig import generate as generate_mig
from c_profile import selected_paths

ROOT = Path(__file__).resolve().parent
SELECTED = set(selected_paths())
INSTALL_ROOT: Path | None = None
PROVENANCE: dict[str, dict[str, str]] = {}

EXTRAS = {
    "_bounds.h": "Libc:include/_bounds.h",
    "Block.h": "libdispatch:src/BlocksRuntime/Block.h",
    "net/net_kev.h": "xnu:bsd/net/net_kev.h",
    "mach-o/fixup-chains.h": "xnu:EXTERNAL_HEADERS/mach-o/fixup-chains.h",
}

# Public source trees used by the selected C headers.
SOURCE_TREES = (
    ("libpthread", "include", ""),
    ("libplatform", "include", ""),
    ("libdispatch", "dispatch", "dispatch"),
)

# Exact public Xcode header-phase members used by this installation. The
# pinned project files must still mark each build file Public at install time.
XCODE_PUBLIC_HEADERS = {
    "sources/libpthread/include/pthread/pthread_impl.h": "libpthread/libpthread.xcodeproj/project.pbxproj",
    "sources/libpthread/include/pthread/pthread.h": "libpthread/libpthread.xcodeproj/project.pbxproj",
    "sources/libpthread/include/pthread/sched.h": "libpthread/libpthread.xcodeproj/project.pbxproj",
}


def public_xcode_selection(source: Path) -> str | None:
    try:
        relative = source.relative_to(ROOT).as_posix()
    except ValueError:
        return None
    project = XCODE_PUBLIC_HEADERS.get(relative)
    if project is None:
        return None
    marker = f"/* {source.name} in Headers */"
    lines = (ROOT / "sources" / project).read_text().splitlines()
    if not any(marker in line and "ATTRIBUTES = (Public," in line for line in lines):
        raise ValueError(f"public Xcode header phase changed: {relative}")
    return project + ":Public"


def architecture_public_headers() -> list[Path]:
    """Follow architecture/Makefile:copyhdrs for both supported CPU families."""
    makefile = (ROOT / "sources/architecture/Makefile").read_text()
    required = (
        "CANONICAL_ARCH_x86_64 = i386",
        "CANONICAL_ARCH_arm64 = arm",
        "DIRS = . $(ARCHS)",
        "EXPORT_DSTDIR=/usr/include/architecture",
        "copyhdrs: all DSTROOT",
        "install $(INSTALL_FLAGS) *.h $$DSTDIR",
    )
    if any(marker not in makefile for marker in required):
        raise ValueError("architecture public install rule changed")
    root = ROOT / "sources/architecture"
    paths = sorted(path.relative_to(root) for directory in (root, root / "arm", root / "i386")
                   for path in directory.glob("*.h"))
    if len(paths) != 19:
        raise ValueError(f"architecture public header list changed: {len(paths)}")
    return paths


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


# XNU's bsd/sys and bsd/sys/_types Makefiles use DATAFILES for the macOS
# usr/include installation. Their first EXTRA_DATAFILES branch is macOS;
# embedded targets take the else branch. Keep this small reader pinned to
# those Makefile shapes rather than interpreting arbitrary Make syntax.
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


# Explicit Apple OSS sources for the selected C headers. These avoid copying
# private source directories wholesale.
SOURCE_GROUPS = (
    # libdispatch's Xcode Install Headers phase copies these seven public
    # os/ inputs. XNU's public libkern/os Makefile supplies base.h.
    ("libdispatch", "os", "os", (
        "object.h", "workgroup.h", "workgroup_base.h",
        "workgroup_interval.h", "workgroup_object.h",
        "workgroup_parallel.h", "clock.h")),
    ("CommonCrypto", "include", "CommonCrypto", (
        "CommonCrypto.h", "CommonCryptoError.h", "CommonCryptor.h",
        "CommonDigest.h", "CommonHMAC.h", "CommonKeyDerivation.h",
        "CommonRandom.h", "CommonSymmetricKeywrap.h")),
    ("CarbonHeaders", "", "", (
        "AssertMacros.h", "ConditionalMacros.h", "MacTypes.h")),
    ("xnu", "bsd/net", "net", (
        "bpf.h", "dlil.h", "ethernet.h", "if.h", "if_arp.h", "if_dl.h",
        "if_llc.h", "if_media.h", "if_mib.h", "if_types.h", "if_utun.h",
        "if_var.h", "if_var_status.h", "kext_net.h", "ndrv.h",
        "pfkeyv2.h")),
    ("xnu", "libkern/libkern", "libkern", (
        "OSDebug.h", "OSKextLib.h", "OSReturn.h")),
    ("cctools", "include/mach-o", "mach-o", (
        "arch.h", "fat.h", "getsect.h", "ldsyms.h", "loader.h",
        "nlist.h", "ranlib.h", "reloc.h", "stab.h", "swap.h",
        "arm/reloc.h", "arm64/reloc.h", "x86_64/reloc.h")),
    ("hfs", "core", "hfs", (
        "hfs_format.h", "hfs_unistr.h")),
    ("libunwind", "libunwind/include/mach-o", "mach-o", (
        "compact_unwind_encoding.h",)),
    ("zlib", "zlib", "", ("zconf.h", "zlib.h")),
)

EXTRAS.update({
    "iconv.h": "libiconv:citrus/iconv.h",
    "ifaddrs.h": "Libinfo:gen.subproj/ifaddrs.h",
    "netdb.h": "Libinfo:lookup.subproj/netdb.h",
    "nl_types.h": "Libc:include/FreeBSD/nl_types.h",
    "mach-o/utils.h": "dyld:include/mach-o/utils.h",
})


def install(source: Path, destination: Path, origin: str | None = None,
            selection: str = "direct") -> None:
    public_selection = public_xcode_selection(source)
    if public_selection:
        selection = public_selection
    if origin is None:
        resolved = source.resolve()
        if not resolved.is_relative_to(ROOT):
            raise ValueError(f"source outside pinned inputs needs an origin: {source}")
        origin = resolved.relative_to(ROOT).as_posix()
    install_bytes(source.read_bytes(), destination, origin, selection)


def install_bytes(data: bytes, destination: Path, origin: str,
                  selection: str = "direct") -> None:
    if INSTALL_ROOT is None:
        raise ValueError("installation root is not set")
    relative = destination.relative_to(INSTALL_ROOT).as_posix()
    if relative not in SELECTED:
        raise ValueError(f"header outside default profile: {relative}")
    if destination.exists():
        if destination.read_bytes() != data:
            raise ValueError(f"header collision: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    PROVENANCE[relative] = {"origin": origin,
                            "selection": selection,
                            "sha256": hashlib.sha256(data).hexdigest()}


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


def destination_path(out: Path, relative: Path) -> Path:
    return out / "usr/include" / relative


def source_path(reference: str, relative: Path) -> Path:
    repo, path = reference.split(":", 1)
    return ROOT / "sources" / repo / path


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


def generated_apple_headers(temporary: Path, libc_flags: list[str]) -> dict[str, bytes]:
    availability = ROOT / "sources/AvailabilityVersions"
    xnu = ROOT / "sources/xnu"
    result = {}
    for name in ("Availability.h", "AvailabilityInternal.h",
                 "AvailabilityVersions.h", "os_availability.h"):
        output = temporary / name
        subprocess.run(["python3", str(availability / "availability"),
                        "--preprocess", str(availability / "templates" / name),
                        str(output)], check=True)
        result["os/availability.h" if name == "os_availability.h" else name] = output.read_bytes()

    # The pinned DSL explicitly declares cmd_aliases=xros for visionos, while
    # the API macro generator omits that spelling. Current libdispatch uses
    # API_AVAILABLE(..., xros(...)); preserve the documented alias there too.
    dsl = (availability / "availability.dsl").read_text()
    if "platform    visionos            visionOS    VISIONOS      min_max_define_name=VISION_OS   cmd_aliases=xros" not in dsl:
        raise ValueError("AvailabilityVersions xros alias changed")
    internal = result["AvailabilityInternal.h"].decode()
    anchor = "   #define __API_UNAVAILABLE_PLATFORM_visionos visionos,unavailable\n"
    aliases = (
        "   #define __API_AVAILABLE_PLATFORM_xros(x) visionos,introduced=x\n"
        "   #define __API_DEPRECATED_PLATFORM_xros(x,y) visionos,introduced=x,deprecated=y\n"
        "   #define __API_OBSOLETED_PLATFORM_xros(x,y,z) visionos,introduced=x,deprecated=y,obsoleted=z\n"
        "   #define __API_UNAVAILABLE_PLATFORM_xros visionos,unavailable\n"
    )
    if internal.count(anchor) != 1:
        raise ValueError("AvailabilityInternal.h visionos macros changed")
    result["AvailabilityInternal.h"] = internal.replace(anchor, anchor + aliases).encode()

    tool = temporary / "sdk/usr/local/libexec"
    tool.mkdir(parents=True)
    (tool / "availability.pl").symlink_to(availability / "availability")
    (tool / "availability.dsl").symlink_to(availability / "availability.dsl")
    symbol = temporary / "_symbol_aliasing.h"
    subprocess.run(["bash", str(xnu / "bsd/sys/make_symbol_aliasing.sh"),
                    str(temporary / "sdk"), str(symbol)], check=True)
    result["sys/_symbol_aliasing.h"] = symbol.read_bytes()
    posix = temporary / "_posix_availability.h"
    subprocess.run(["sh", str(xnu / "bsd/sys/make_posix_availability.sh"),
                    str(posix)], check=True)
    result["sys/_posix_availability.h"] = posix.read_bytes()

    cdefs = subprocess.run(["unifdef", *xnu_public_flags(),
                            str(xnu / "bsd/sys/cdefs.h")],
                           capture_output=True, check=False)
    if cdefs.returncode not in (0, 1):
        raise ValueError(f"XNU cdefs.h unifdef failed: {cdefs.stderr!r}")
    result["sys/cdefs.h"] = cdefs.stdout

    device = subprocess.run(["unifdef", *xnu_public_flags(), "-DIOKIT",
                             str(xnu / "osfmk/device/device_types.h")],
                            capture_output=True, check=False)
    if device.returncode not in (0, 1):
        raise ValueError(f"XNU device_types.h unifdef failed: {device.stderr!r}")
    result["device/device_types.h"] = device.stdout

    result["utmpx.h"] = libc_public_header(
        ROOT / "sources/Libc/include/NetBSD/utmpx.h", libc_flags)

    complex_source = (ROOT / "sources/Libm/Source/complex.h").read_bytes()
    old = b"#elif defined(__arm__)\n#define __LIBMLDBL_COMPAT"
    new = b"#elif defined(__arm__) || defined(__arm64__) || defined(__aarch64__)\n#define __LIBMLDBL_COMPAT"
    if complex_source.count(old) != 1:
        raise ValueError("Libm complex.h architecture branch changed")
    result["complex.h"] = complex_source.replace(old, new)
    result["grp.h"] = (ROOT / "sources/Libinfo/lookup.subproj/grp.h").read_bytes()
    result["pwd.h"] = (ROOT / "sources/Libinfo/lookup.subproj/pwd.h").read_bytes()
    dyld_source = (ROOT / "sources/dyld/include/mach-o/dyld.h").read_bytes()
    dyld_before = b"#endif\n\n\n/*\n * The following functions allow you to iterate"
    dyld_after = (b"#endif\n\n#ifndef DYLD_EXCLAVEKIT_UNAVAILABLE\n"
                  b"#define DYLD_EXCLAVEKIT_UNAVAILABLE\n#endif\n\n\n"
                  b"/*\n * The following functions allow you to iterate")
    if dyld_source.count(dyld_before) != 1:
        raise ValueError("dyld.h availability section changed")
    result["mach-o/dyld.h"] = dyld_source.replace(dyld_before, dyld_after)
    images = (ROOT / "sources/dyld/include/mach-o/dyld_images.h").read_bytes()
    image_anchor = b"#define _DYLD_IMAGES_\n"
    if images.count(image_anchor) != 1:
        raise ValueError("dyld_images.h guard changed")
    result["mach-o/dyld_images.h"] = images.replace(
        image_anchor, image_anchor + b"#include <stdint.h>\n#include <mach/mach.h>\n")
    return result


def target_conditionals() -> bytes:
    # CarbonHeaders/Makefile installs this template with the three CONFIG
    # placeholders set to zero for macOS. The pinned release predates arm64
    # and today's TARGET_OS aliases, so add those from compiler target macros.
    source = (ROOT / "sources/CarbonHeaders/TargetConditionals.h").read_text()
    for variable in ("CONFIG_EMBEDDED", "CONFIG_IPHONE", "CONFIG_IPHONE_SIMULATOR"):
        source = source.replace(f"@{variable}@", "0")
    arm = "     #elif defined(__arm__) \n"
    arm64 = ("     #elif defined(__arm64__) || defined(__aarch64__)\n"
             "        #define TARGET_CPU_PPC          0\n"
             "        #define TARGET_CPU_PPC64        0\n"
             "        #define TARGET_CPU_68K         0\n"
             "        #define TARGET_CPU_X86          0\n"
             "        #define TARGET_CPU_X86_64       0\n"
             "        #define TARGET_CPU_ARM          0\n"
             "        #define TARGET_CPU_MIPS         0\n"
             "        #define TARGET_CPU_SPARC        0\n"
             "        #define TARGET_CPU_ALPHA        0\n"
             "        #define TARGET_RT_MAC_CFM       0\n"
             "        #define TARGET_RT_MAC_MACHO     1\n"
             "        #define TARGET_RT_LITTLE_ENDIAN 1\n"
             "        #define TARGET_RT_BIG_ENDIAN    0\n"
             "        #define TARGET_RT_64_BIT        1\n")
    if source.count(arm) != 1:
        raise ValueError("CarbonHeaders ARM branch changed")
    source = source.replace(arm, arm64 + arm)
    source = source.replace("#define TARGET_OS_UNIX              0",
                            "#define TARGET_OS_UNIX              1")
    suffix = ("\n/* macOS aliases added after the CarbonHeaders release. */\n"
              "#define TARGET_OS_OSX 1\n"
              "#define TARGET_OS_IOS 0\n"
              "#define TARGET_OS_WATCH 0\n"
              "#define TARGET_OS_WATCHOS 0\n"
              "#define TARGET_OS_TV 0\n"
              "#define TARGET_OS_VISION 0\n"
              "#define TARGET_OS_SIMULATOR 0\n"
              "#define TARGET_OS_MACCATALYST 0\n"
              "#define TARGET_OS_DRIVERKIT 0\n"
              "#define TARGET_OS_WINDOWS 0\n"
              "#define TARGET_OS_LINUX 0\n"
              "#define TARGET_OS_NANO 0\n"
              "#if defined(__arm64__) || defined(__aarch64__)\n"
              "#define TARGET_CPU_ARM64 1\n"
              "#else\n#define TARGET_CPU_ARM64 0\n#endif\n")
    final = "\n#endif  /* __TARGETCONDITIONALS__ */\n"
    if source.count(final) != 1:
        raise ValueError("CarbonHeaders final guard changed")
    return source.replace(final, suffix + final).encode()


def install_math(out: Path) -> None:
    source = ROOT / "sources/Libm/Source/math.h"
    text = source.read_text()
    before = "#elif defined(__arm__)\n"
    if text.count(before) != 1:
        raise ValueError("Libm math.h architecture switch changed")
    text = text.replace(before, "#elif defined(__arm__) || defined(__arm64__)\n")
    target = out / "usr/include/math.h"
    install_bytes(text.encode(), target, "derived:sources/Libm/Source/math.h via install_math",
                  "Libm derivation")
    install(ROOT / "sources/Libm/Source/ARM/math.h",
            out / "usr/include/architecture/arm/math.h", selection="Libm derivation")
    install(ROOT / "sources/Libm/Source/Intel/math.h",
            out / "usr/include/architecture/i386/math.h", selection="Libm derivation")


def install_fenv(out: Path) -> None:
    source = ROOT / "sources/Libm/Source/fenv.h"
    text = source.read_text()
    before = "#elif defined(__arm__)\n#include \"architecture/arm/fenv.h\"\n"
    after = ("#elif defined(__arm64__)\n#include \"architecture/arm64/fenv.h\"\n"
             "#elif defined(__arm__)\n#include \"architecture/arm/fenv.h\"\n")
    if text.count(before) != 1:
        raise ValueError("Libm fenv.h architecture switch changed")
    target = out / "usr/include/fenv.h"
    install_bytes(text.replace(before, after).encode(), target,
                  "derived:sources/Libm/Source/fenv.h via install_fenv", "Libm derivation")
    install(ROOT / "sources/Libm/Source/Intel/fenv.h",
            out / "usr/include/architecture/i386/fenv.h", selection="Libm derivation")
    install(ROOT / "templates/arm64_fenv.h",
            out / "usr/include/architecture/arm64/fenv.h", selection="Libm derivation")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mig", type=Path, default=Path("/usr/bin/mig"),
                        help="macOS system mig (default: /usr/bin/mig)")
    parser.add_argument("--clang", type=Path, required=True,
                        help="clang from the pinned minimal LLVM prebuilt")
    args = parser.parse_args()
    out = args.out.absolute()
    if out.exists():
        parser.error("output already exists; choose an empty path")
    global INSTALL_ROOT
    INSTALL_ROOT = out

    libc_flags = libc_unifdef_flags()
    libc_public = set(libc_public_headers())

    with tempfile.TemporaryDirectory(prefix="apple-oss-generated-") as temporary:
        generated = generated_apple_headers(Path(temporary), libc_flags)
        with (ROOT / "inputs/header-sources.tsv").open(newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                relative = Path(row["install_path"])
                libc_source = ROOT / "sources/Libc/include" / relative
                reference = row["source"]
                if reference.startswith("generated:"):
                    if reference == "generated:libc":
                        if relative.as_posix() not in libc_public:
                            raise ValueError(f"generated Libc header not in public list: {relative}")
                        data = libc_public_header(libc_source, libc_flags)
                    else:
                        data = generated[str(relative)]
                    install_bytes(data, destination_path(out, relative),
                                  f"{reference} via inputs/header-sources.tsv:{relative}",
                                  ("Libc/xcodescripts/headers.sh:public"
                                   if reference == "generated:libc" else
                                   "header-sources.tsv"))
                    continue
                source = source_path(reference, relative)
                install(source, destination_path(out, relative),
                        selection="header-sources.tsv")

    install_math(out)
    install_fenv(out)
    for name in ("device/device_types.h", "mach-o/dyld_images.h", "utmpx.h"):
        install_bytes(generated[name], out / "usr/include" / name,
                      f"generated:{name} via install_c.py:generated_apple_headers",
                      "generated explicit")

    for relative, reference in EXTRAS.items():
        install(source_path(reference, Path(relative)), out / "usr/include" / relative,
                selection="EXTRAS")
    install_bytes(target_conditionals(), out / "usr/include/TargetConditionals.h",
                  "derived:sources/CarbonHeaders/TargetConditionals.h via target_conditionals",
                  "CarbonHeaders derivation")

    for repo, source_dir, target_dir in SOURCE_TREES:
        source_root = ROOT / "sources" / repo / source_dir
        for source in sorted(source_root.rglob("*.h")):
            destination = out / "usr/include" / target_dir / source.relative_to(source_root)
            if destination.relative_to(out).as_posix() not in SELECTED:
                continue
            if not destination.exists():
                install(source, destination, selection="SOURCE_TREES")

    for relative in sorted(libc_public &
                           {path.removeprefix("usr/include/") for path in SELECTED}):
        destination = out / "usr/include" / relative
        if not destination.exists():
            install(ROOT / "sources/Libc/include" / relative, destination,
                    selection="Libc/xcodescripts/headers.sh:public")

    for source_dir, target_dir, list_name in XNU_PUBLIC_MAKE_DIRS:
        for name in xnu_public_make_headers(source_dir, list_name):
            source = ROOT / "sources/xnu" / source_dir / name
            destination = out / "usr/include" / target_dir / name
            if destination.relative_to(out).as_posix() not in SELECTED:
                continue
            if not destination.exists():
                install(source, destination,
                        selection=f"{source_dir}/Makefile:{list_name}")

    for name in libsyscall_public_mach_headers():
        if f"usr/include/mach/{name}" not in SELECTED:
            continue
        install(ROOT / "sources/xnu/libsyscall/mach/mach" / name,
                out / "usr/include/mach" / name,
                selection="xnu/libsyscall/xcodescripts/mach_install_mig.sh:MACH_HDRS")

    for relative in architecture_public_headers():
        if f"usr/include/architecture/{relative.as_posix()}" not in SELECTED:
            continue
        install(ROOT / "sources/architecture" / relative,
                out / "usr/include/architecture" / relative,
                selection="architecture/Makefile:copyhdrs")

    for repo, source_dir, target_dir, names in SOURCE_GROUPS:
        for name in names:
            install(ROOT / "sources" / repo / source_dir / name,
                    out / "usr/include" / target_dir / name,
                    selection=("hfs Xcode Public Headers" if repo == "hfs"
                               else "SOURCE_GROUPS"))

    with tempfile.TemporaryDirectory(prefix="apple-oss-mig-") as temporary:
        mig_out = Path(temporary) / "generated"
        generate_mig(args.mig.absolute(), args.clang.absolute(), out, mig_out)
        # libsyscall/xcodescripts/mach_install_mig.sh is the user-level
        # installation recipe. XNU's MIG_USHDRS are kernel exports only.
        for source in sorted((mig_out / "arm64/mach").glob("*.h")):
            install(source, out / "usr/include/mach" / source.name,
                    f"generated:system-mig:{source.name} via generate_mig.py",
                    "xnu/libsyscall/xcodescripts/mach_install_mig.sh:public")

    if set(PROVENANCE) != SELECTED:
        missing = sorted(SELECTED - set(PROVENANCE))
        extra = sorted(set(PROVENANCE) - SELECTED)
        raise ValueError(f"profile mismatch: {len(missing)} missing, {len(extra)} extra; "
                         f"first missing={missing[:1]}, extra={extra[:1]}")

    (out / "header-provenance.json").write_text(json.dumps({
        "schema": 2, "files": dict(sorted(PROVENANCE.items()))
    }, indent=2, sort_keys=True) + "\n")

    print(out)


if __name__ == "__main__":
    main()
