"""Import public header outputs from the upstream Make staging steps."""

from pathlib import Path

from recipes.assembly import Assembly
from recipes.availability_versions.headers import add_xros_alias

RULES = {
    "architecture": "sources/architecture/Makefile",
    "AvailabilityVersions": "sources/AvailabilityVersions/CMakeLists.txt",
    "CarbonHeaders": "sources/CarbonHeaders/Makefile",
    "Libc": "sources/Libc/xcodescripts/headers.sh",
    "Libinfo": "sources/Libinfo/xcodescripts/install_files.sh",
}

# The generated AvailabilityVersions headers supersede CarbonHeaders' versions.
# TargetConditionals comes from the separate arm64 compatibility recipe.
CARBON_REPLACEMENTS = {
    "Availability.h", "AvailabilityInternal.h", "AvailabilityMacros.h",
    "TargetConditionals.h",
}


def collect(assembly: Assembly, staging: Path) -> None:
    for owner, rule in RULES.items():
        include = staging / owner / "dst/usr/include"
        public = sorted(include.rglob("*.h"))
        if not public:
            raise ValueError(f"{owner} staged no public headers")
        for header in public:
            relative = header.relative_to(include).as_posix()
            if owner == "CarbonHeaders" and relative in CARBON_REPLACEMENTS:
                continue
            if not header.is_file() or not header.resolve().is_relative_to(include.resolve()):
                raise ValueError(f"invalid staged public header: {owner}/{relative}")
            data = header.read_bytes()
            transform = "Apple public header install"
            inputs = (rule,)
            if owner == "AvailabilityVersions":
                inputs += ("sources/AvailabilityVersions/Makefile",
                           "sources/AvailabilityVersions/availability",
                           "sources/AvailabilityVersions/availability.dsl")
                if relative == "AvailabilityInternal.h":
                    data = add_xros_alias(data)
                    transform += " and add xros aliases"
            assembly.add(owner, f"usr/include/{relative}", data,
                         f"staged:{owner}:{relative}", rule,
                         inputs=inputs, transform=transform)
