"""Import public header outputs from the upstream Make staging steps."""

from pathlib import Path

from recipes.assembly import Assembly
from recipes.availability_versions.headers import add_xros_alias

# The generated AvailabilityVersions headers supersede CarbonHeaders' versions.
# TargetConditionals comes from the separate arm64 compatibility recipe.
CARBON_REPLACEMENTS = {
    "Availability.h", "AvailabilityInternal.h", "AvailabilityMacros.h",
    "TargetConditionals.h",
}


def collect(assembly: Assembly, staging: Path) -> None:
    for receipt in sorted(staging.glob("*/rule")):
        owner = receipt.parent.name
        rule = receipt.read_text().strip()
        include = receipt.parent / "dst/usr/include"
        direct = {}
        index = receipt.with_name("direct-copies")
        if index.is_file():
            for line in index.read_text().splitlines():
                relative, source = line.split("\t")
                path = Path(relative).as_posix()
                if path in direct:
                    raise ValueError(f"{owner} copied {path} more than once")
                direct[path] = source
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
            transform = ("Apple public header install" if rule.startswith("sources/")
                         else "producer header install recipe")
            inputs = (rule,)
            origin = f"staged:{owner}:{relative}"
            if relative in direct:
                origin = direct.pop(relative)
                inputs += (origin,)
                transform = "copy"
            if owner == "AvailabilityVersions":
                inputs += ("sources/AvailabilityVersions/Makefile",
                           "sources/AvailabilityVersions/availability",
                           "sources/AvailabilityVersions/availability.dsl")
                if relative == "AvailabilityInternal.h":
                    data = add_xros_alias(data)
                    transform += " and add xros aliases"
            assembly.add(owner, f"usr/include/{relative}", data,
                         origin, rule,
                         inputs=inputs, transform=transform)
        if direct:
            raise ValueError(f"{owner} is missing direct-copy outputs: {sorted(direct)}")
