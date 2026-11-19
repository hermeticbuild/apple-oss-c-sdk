"""Adapt the pinned CarbonHeaders template to both macOS targets."""

import sys
from pathlib import Path

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


if __name__ == "__main__":
    Path(sys.argv[1]).write_bytes(target_conditionals())
