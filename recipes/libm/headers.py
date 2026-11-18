"""Libm headers and guarded macOS arm64 derivations."""

from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
Emit = Callable[[str, bytes, str, str], None]


def produce(emit: Emit) -> None:
    complex_source = (ROOT / "sources/Libm/Source/complex.h").read_bytes()
    old = b"#elif defined(__arm__)\n#define __LIBMLDBL_COMPAT"
    new = b"#elif defined(__arm__) || defined(__arm64__) || defined(__aarch64__)\n#define __LIBMLDBL_COMPAT"
    if complex_source.count(old) != 1:
        raise ValueError("Libm complex.h architecture branch changed")
    emit("usr/include/complex.h", complex_source.replace(old, new),
         "generated:apple via inputs/header-sources.tsv:complex.h",
         "header-sources.tsv")

    source = ROOT / "sources/Libm/Source/math.h"
    text = source.read_text()
    before = "#elif defined(__arm__)\n"
    if text.count(before) != 1:
        raise ValueError("Libm math.h architecture switch changed")
    emit("usr/include/math.h", text.replace(before,
         "#elif defined(__arm__) || defined(__arm64__)\n").encode(),
         "derived:sources/Libm/Source/math.h via install_math", "Libm derivation")
    emit("usr/include/architecture/arm/math.h",
         (ROOT / "sources/Libm/Source/ARM/math.h").read_bytes(),
         "sources/Libm/Source/ARM/math.h", "Libm derivation")
    emit("usr/include/architecture/i386/math.h",
         (ROOT / "sources/Libm/Source/Intel/math.h").read_bytes(),
         "sources/Libm/Source/Intel/math.h", "Libm derivation")

    source = ROOT / "sources/Libm/Source/fenv.h"
    text = source.read_text()
    before = "#elif defined(__arm__)\n#include \"architecture/arm/fenv.h\"\n"
    after = ("#elif defined(__arm64__)\n#include \"architecture/arm64/fenv.h\"\n"
             "#elif defined(__arm__)\n#include \"architecture/arm/fenv.h\"\n")
    if text.count(before) != 1:
        raise ValueError("Libm fenv.h architecture switch changed")
    emit("usr/include/fenv.h", text.replace(before, after).encode(),
         "derived:sources/Libm/Source/fenv.h via install_fenv", "Libm derivation")
    emit("usr/include/architecture/i386/fenv.h",
         (ROOT / "sources/Libm/Source/Intel/fenv.h").read_bytes(),
         "sources/Libm/Source/Intel/fenv.h", "Libm derivation")
    emit("usr/include/architecture/arm64/fenv.h",
         (ROOT / "templates/arm64_fenv.h").read_bytes(),
         "templates/arm64_fenv.h", "Libm derivation")
