"""Stage the pinned Apple generator with the macOS 26.5 version supplement."""

import hashlib
from pathlib import Path
import sys


BASE_DSL_SHA256 = "1d09c3e8d7c6b69fa8d5aa7645cc024075f9d1de097cf28c105524314c67fa65"
SUPPLEMENT = Path(__file__).with_name("macosx26.5.dsl")


def stage_generator(source, destination):
    source = source.resolve(strict=True)
    dsl = (source / "availability.dsl").read_bytes()
    if hashlib.sha256(dsl).hexdigest() != BASE_DSL_SHA256:
        raise ValueError("macosx26.5 supplement requires the AvailabilityVersions-157.2 DSL")

    destination.mkdir()
    for name in ("Makefile", "CMakeLists.txt", "availability", "templates"):
        (destination / name).symlink_to((source / name).resolve(strict=True))
    (destination / "availability.dsl").write_bytes(dsl + b"\n" + SUPPLEMENT.read_bytes())


if __name__ == "__main__":
    try:
        stage_generator(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError) as error:
        sys.exit(str(error))
