"""Preprocess the pinned Apple AvailabilityVersions templates."""

import subprocess
from pathlib import Path

from recipes.assembly import Assembly


ROOT = Path(__file__).resolve().parents[2]


def produce(assembly: Assembly, temporary: Path) -> None:
    availability = ROOT / "sources/AvailabilityVersions"
    temporary.mkdir(parents=True)
    for name in ("Availability.h", "AvailabilityInternal.h",
                 "AvailabilityVersions.h", "os_availability.h"):
        output = temporary / name
        subprocess.run(["python3", str(availability / "availability"),
                        "--preprocess", str(availability / "templates" / name),
                        str(output)], check=True)
        target = "os/availability.h" if name == "os_availability.h" else name
        data = output.read_bytes()
        if name == "AvailabilityInternal.h":
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
            data = text.replace(anchor, anchor + aliases).encode()
        assembly.add("AvailabilityVersions", f"usr/include/{target}", data,
                     f"generated:apple via inputs/header-sources.tsv:{target}",
                     "header-sources.tsv")
