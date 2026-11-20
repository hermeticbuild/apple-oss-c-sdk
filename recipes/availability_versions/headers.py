"""Compatibility adjustment to the Apple AvailabilityVersions output."""

import os
import sys
from pathlib import Path

SOURCES = Path(os.environ["SOURCE_ROOT"]).absolute()


def add_xros_alias(data: bytes) -> bytes:
    availability = SOURCES / "AvailabilityVersions"
    # The pinned DSL declares xros as a visionOS alias, but its API
    # macro generator omits the spelling used by libdispatch.
    dsl = (availability / "availability.dsl").read_text()
    if "platform    visionos            visionOS    VISIONOS      min_max_define_name=VISION_OS   cmd_aliases=xros" not in dsl:
        raise ValueError("AvailabilityVersions xros alias changed")
    anchor = "   #define __API_UNAVAILABLE_PLATFORM_visionos visionos,unavailable\n"
    aliases = (
        "   #define __API_AVAILABLE_PLATFORM_xros(x) visionos,introduced=x\n"
        "   #define __API_DEPRECATED_PLATFORM_xros(x,y) visionos,introduced=x,deprecated=y\n"
        "   #define __API_OBSOLETED_PLATFORM_xros(x,y,z) visionos,introduced=x,deprecated=y,obsoleted=z\n"
        "   #define __API_UNAVAILABLE_PLATFORM_xros visionos,unavailable\n"
    )
    text = data.decode()
    if text.count(anchor) != 1:
        raise ValueError("AvailabilityInternal.h visionos macros changed")
    return text.replace(anchor, anchor + aliases).encode()


if __name__ == "__main__":
    output = Path(sys.argv[1])
    output.write_bytes(add_xros_alias(output.read_bytes()))
