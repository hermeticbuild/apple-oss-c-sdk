#!/usr/bin/env python3
"""Install the pinned Apple OSS C-header snapshot into an empty sysroot.

This installer reads no Apple SDK Gen content. It applies pinned Apple OSS
header generation rules plus two explicitly documented local C declarations.
See README.md before treating the result as a release.
"""

import argparse
import csv
import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from generate_mig import generate as generate_mig

ROOT = Path(__file__).resolve().parent

EXTRAS = {
    "_bounds.h": "Libc:include/_bounds.h",
    "Block.h": "libdispatch:src/BlocksRuntime/Block.h",
    "net/net_kev.h": "xnu:bsd/net/net_kev.h",
    "sandbox.h": "template:sandbox.h",
}

# Provisional closure candidates. Replace broad walks with Apple's public
# installation manifests before claiming SDK header parity.
SOURCE_TREES = (
    ("Libc", "include", ""),
    ("xnu", "bsd/sys", "sys"),
    ("xnu", "bsd/machine", "machine"),
    ("xnu", "bsd/arm", "arm"),
    ("xnu", "bsd/i386", "i386"),
    ("xnu", "osfmk/mach", "mach"),
    # Public os/object.h is libdispatch's; XNU's same-named header is a
    # kernel shim that uses include_next to reach libdispatch.
    ("libdispatch", "os", "os"),
    ("xnu", "libkern/os", "os"),
    ("xnu", "EXTERNAL_HEADERS", ""),
    ("libpthread", "include", ""),
    ("libplatform", "include", ""),
    ("libmalloc", "include", ""),
    ("libdispatch", "dispatch", "dispatch"),
)

# XNU's EXTERNAL_HEADERS/Makefile lists these under KERNEL_FILES, not
# INSTALL_MI_LIST. The compiler's resource directory supplies them to C users.
# In particular, installing XNU stdatomic.h after Clang's resource header
# suppresses atomic_flag through their shared __CLANG_STDATOMIC_H guard.
XNU_KERNEL_ONLY_HEADERS = {
    "stdarg.h", "stdatomic.h", "stdbool.h", "stddef.h", "stdint.h",
    "ptrauth.h",
}

# Public headers present in the SDK Gen comparison tree and available from
# separate Apple OSS projects. These are explicit to avoid copying private
# source directories wholesale.
SOURCE_GROUPS = (
    ("CommonCrypto", "include", "CommonCrypto", (
        "CommonCrypto.h", "CommonCryptoError.h", "CommonCryptor.h",
        "CommonDigest.h", "CommonHMAC.h", "CommonKeyDerivation.h",
        "CommonRandom.h", "CommonSymmetricKeywrap.h")),
    ("CarbonHeaders", "", "", ("ConditionalMacros.h", "Endian.h", "MacTypes.h")),
    ("xnu", "bsd/net", "net", (
        "ethernet.h", "if.h", "if_dl.h", "if_types.h", "if_var.h",
        "if_var_status.h", "pfkeyv2.h")),
    ("xnu", "bsd/netinet", "netinet", (
        "icmp6.h", "in.h", "in_pcb.h", "in_systm.h", "ip.h", "ip6.h",
        "ip_icmp.h", "tcp.h", "tcp_timer.h", "tcp_var.h", "udp.h")),
    ("xnu", "bsd/netinet6", "netinet6", (
        "in6.h", "ipsec.h", "scope6_var.h")),
    ("objc4", "runtime", "objc", (
        "NSObjCRuntime.h", "NSObject.h", "message.h", "objc-api.h",
        "objc-auto.h", "objc-exception.h", "objc-sync.h", "objc.h",
        "runtime.h")),
    ("Libinfo", "rpc.subproj", "rpc", (
        "auth.h", "auth_unix.h", "clnt.h", "pmap_clnt.h", "pmap_prot.h",
        "pmap_rmt.h", "pmap_wakeup.h", "rpc.h", "rpc_msg.h", "svc.h",
        "svc_auth.h", "types.h", "xdr.h")),
    ("zlib", "zlib", "", ("zconf.h", "zlib.h")),
)

EXTRAS.update({
    "iconv.h": "libiconv:citrus/iconv.h",
    "ifaddrs.h": "Libinfo:gen.subproj/ifaddrs.h",
    "membership.h": "Libinfo:membership.subproj/membership.h",
    "netdb.h": "Libinfo:lookup.subproj/netdb.h",
    "nl_types.h": "Libc:include/FreeBSD/nl_types.h",
    "notify.h": "Libnotify:notify.h",
    "notify_keys.h": "Libnotify:notify_keys.h",
    "ntsid.h": "Libinfo:membership.subproj/ntsid.h",
    "removefile.h": "removefile:removefile.h",
    "xattr_flags.h": "copyfile:xattr_flags.h",
})


def install(source: Path, destination: Path) -> None:
    install_bytes(source.read_bytes(), destination)


def install_bytes(data: bytes, destination: Path) -> None:
    if destination.exists():
        if destination.read_bytes() != data:
            raise ValueError(f"header collision: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)


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
    if relative.parts[0] == "CoreFoundation.framework":
        return out / "System/Library/Frameworks" / relative
    return out / "usr/include" / relative


def source_path(reference: str, relative: Path) -> Path:
    if reference.startswith("template:"):
        return ROOT / "templates" / reference.split(":", 1)[1]
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


def generated_apple_headers(temporary: Path) -> dict[str, bytes]:
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
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    install(ROOT / "sources/Libm/Source/ARM/math.h",
            out / "usr/include/architecture/arm/math.h")
    install(ROOT / "sources/Libm/Source/Intel/math.h",
            out / "usr/include/architecture/i386/math.h")


def install_fenv(out: Path) -> None:
    source = ROOT / "sources/Libm/Source/fenv.h"
    text = source.read_text()
    before = "#elif defined(__arm__)\n#include \"architecture/arm/fenv.h\"\n"
    after = ("#elif defined(__arm64__)\n#include \"architecture/arm64/fenv.h\"\n"
             "#elif defined(__arm__)\n#include \"architecture/arm/fenv.h\"\n")
    if text.count(before) != 1:
        raise ValueError("Libm fenv.h architecture switch changed")
    target = out / "usr/include/fenv.h"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text.replace(before, after))
    install(ROOT / "sources/Libm/Source/ARM/fenv.h",
            out / "usr/include/architecture/arm/fenv.h")
    install(ROOT / "sources/Libm/Source/Intel/fenv.h",
            out / "usr/include/architecture/i386/fenv.h")
    install(ROOT / "templates/arm64_fenv.h",
            out / "usr/include/architecture/arm64/fenv.h")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mig", type=Path, required=True,
                        help="built tools/apple_mig/bazel-bin/mig executable")
    parser.add_argument("--clang", type=Path,
                        default=Path("/opt/homebrew/opt/llvm/bin/clang"))
    args = parser.parse_args()
    out = args.out.absolute()
    if out.exists():
        parser.error("output already exists; choose an empty path")

    libc_flags = libc_unifdef_flags()

    with tempfile.TemporaryDirectory(prefix="apple-oss-generated-") as temporary:
        generated = generated_apple_headers(Path(temporary))
        with (ROOT / "inputs/header-sources.tsv").open(newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                relative = Path(row["install_path"])
                libc_source = ROOT / "sources/Libc/include" / relative
                reference = row["source"]
                if reference.startswith("generated:"):
                    if reference == "generated:libc":
                        data = libc_public_header(libc_source, libc_flags)
                    else:
                        data = generated[str(relative)]
                    install_bytes(data, destination_path(out, relative))
                    continue
                source = source_path(reference, relative)
                install(source, destination_path(out, relative))

    install_math(out)
    install_fenv(out)

    for relative, reference in EXTRAS.items():
        install(source_path(reference, Path(relative)), out / "usr/include" / relative)
    install_bytes(target_conditionals(), out / "usr/include/TargetConditionals.h")

    for repo, source_dir, target_dir in SOURCE_TREES:
        source_root = ROOT / "sources" / repo / source_dir
        for source in sorted(source_root.rglob("*.h")):
            if repo == "xnu" and source_dir == "EXTERNAL_HEADERS" and source.parent == source_root and source.name in XNU_KERNEL_ONLY_HEADERS:
                continue
            destination = out / "usr/include" / target_dir / source.relative_to(source_root)
            if not destination.exists():
                install(source, destination)

    for repo, source_dir, target_dir, names in SOURCE_GROUPS:
        for name in names:
            install(ROOT / "sources" / repo / source_dir / name,
                    out / "usr/include" / target_dir / name)

    with tempfile.TemporaryDirectory(prefix="apple-oss-mig-") as temporary:
        mig_out = Path(temporary) / "generated"
        generate_mig(args.mig.absolute(), args.clang.resolve(), out, mig_out)
        for source in sorted((mig_out / "arm64/mach").glob("*.h")):
            install(source, out / "usr/include/mach" / source.name)

    print(out)


if __name__ == "__main__":
    main()
