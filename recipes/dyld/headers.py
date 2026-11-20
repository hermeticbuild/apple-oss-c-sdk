"""Guarded compatibility edits to the public dyld headers."""

import os
import sys
from pathlib import Path

SOURCES = Path(os.environ["SOURCE_ROOT"]).absolute()


def patch(destination: Path) -> None:
    dyld = SOURCES / "dyld/include/mach-o"
    source = (dyld / "dyld.h").read_bytes()
    before = b"#endif\n\n\n/*\n * The following functions allow you to iterate"
    after = (b"#endif\n\n#ifndef DYLD_EXCLAVEKIT_UNAVAILABLE\n"
             b"#define DYLD_EXCLAVEKIT_UNAVAILABLE\n#endif\n\n\n"
             b"/*\n * The following functions allow you to iterate")
    if source.count(before) != 1:
        raise ValueError("dyld.h availability section changed")
    (destination / "dyld.h").write_bytes(source.replace(before, after))
    images = (dyld / "dyld_images.h").read_bytes()
    anchor = b"#define _DYLD_IMAGES_\n"
    if images.count(anchor) != 1:
        raise ValueError("dyld_images.h guard changed")
    (destination / "dyld_images.h").write_bytes(
        images.replace(anchor, anchor + b"#include <stdint.h>\n#include <mach/mach.h>\n"))


if __name__ == "__main__":
    patch(Path(sys.argv[1]))
