"""Guarded derivations for older Apple OSS C headers."""

from pathlib import Path

from recipes.assembly import Assembly

ROOT = Path(__file__).resolve().parents[2]


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


def produce(assembly: Assembly) -> None:
    assembly.add("CarbonHeaders", "usr/include/TargetConditionals.h",
                 target_conditionals(),
                 "derived:sources/CarbonHeaders/TargetConditionals.h via target_conditionals",
                 "CarbonHeaders derivation")
    for name in ("grp.h", "pwd.h"):
        source = ROOT / "sources/Libinfo/lookup.subproj" / name
        assembly.add("Libinfo", f"usr/include/{name}", source.read_bytes(),
                     f"generated:apple via inputs/header-sources.tsv:{name}",
                     "header-sources.tsv")
    dyld = ROOT / "sources/dyld/include/mach-o"
    source = (dyld / "dyld.h").read_bytes()
    before = b"#endif\n\n\n/*\n * The following functions allow you to iterate"
    after = (b"#endif\n\n#ifndef DYLD_EXCLAVEKIT_UNAVAILABLE\n"
             b"#define DYLD_EXCLAVEKIT_UNAVAILABLE\n#endif\n\n\n"
             b"/*\n * The following functions allow you to iterate")
    if source.count(before) != 1:
        raise ValueError("dyld.h availability section changed")
    assembly.add("dyld", "usr/include/mach-o/dyld.h", source.replace(before, after),
                 "generated:apple via inputs/header-sources.tsv:mach-o/dyld.h",
                 "header-sources.tsv")
    images = (dyld / "dyld_images.h").read_bytes()
    anchor = b"#define _DYLD_IMAGES_\n"
    if images.count(anchor) != 1:
        raise ValueError("dyld_images.h guard changed")
    assembly.add("dyld", "usr/include/mach-o/dyld_images.h",
                 images.replace(anchor, anchor + b"#include <stdint.h>\n#include <mach/mach.h>\n"),
                 "generated:mach-o/dyld_images.h via install_c.py:generated_apple_headers",
                 "generated explicit")
