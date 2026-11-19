"""Apply two reviewed C compatibility changes to CarbonHeaders-18.1."""

from pathlib import Path
import sys


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError(f"CarbonHeaders source changed near {before!r}")
    return source.replace(before, after)


def install(mac_types, destination):
    assertions = destination / "AssertMacros.h"
    # Apple's comment at this guarded default announces the switch.
    # Keep the caller's ability to opt in to the unprefixed macros.
    data = replace_once(assertions.read_bytes(),
                        b"If we haven't set this yet, it defaults to on.  In the next release, this will default to off.",
                        b"Define the switch to 1 to enable unprefixed assertion macros.")
    switch = b"#define\t__ASSERT_MACROS_DEFINE_VERSIONS_WITHOUT_UNDERSCORES\t"
    assertions.write_bytes(replace_once(data, switch + b"1", switch + b"0"))

    data = mac_types.read_bytes()
    for callback in (b"CALLBACK_API_C( long , ProcPtr )", b"CALLBACK_API( void , Register68kProcPtr )"):
        data = replace_once(data, callback + b"();", callback + b"(void);")
    (destination / "MacTypes.h").write_bytes(data)


if __name__ == "__main__":
    install(Path(sys.argv[1]), Path(sys.argv[2]))
