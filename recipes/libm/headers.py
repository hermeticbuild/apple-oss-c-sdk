"""Libm headers and guarded macOS arm64 derivations."""

import sys
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
Emit = Callable[[str, bytes, str, str, tuple[str, ...], str], None]


def produce(emit: Emit) -> None:
    complex_source = (ROOT / "sources/Libm/Source/complex.h").read_bytes()
    old = b"#elif defined(__arm__)\n#define __LIBMLDBL_COMPAT"
    new = b"#elif defined(__arm__) || defined(__arm64__) || defined(__aarch64__)\n#define __LIBMLDBL_COMPAT"
    if complex_source.count(old) != 1:
        raise ValueError("Libm complex.h architecture branch changed")
    emit("usr/include/complex.h", complex_source.replace(old, new),
         "generated:apple via recipes/libm/headers.py:complex.h",
         "recipes/libm/headers.py", ("sources/Libm/Source/complex.h",),
         "guarded arm64 branch")

    source = ROOT / "sources/Libm/Source/math.h"
    text = source.read_text()
    before = "#elif defined(__arm__)\n"
    if text.count(before) != 1:
        raise ValueError("Libm math.h architecture switch changed")
    emit("usr/include/math.h", text.replace(before,
         "#elif defined(__arm__) || defined(__arm64__)\n").encode(),
         "derived:sources/Libm/Source/math.h via recipes/libm/headers.py", "Libm derivation",
         ("sources/Libm/Source/math.h",), "guarded arm64 branch")

    source = ROOT / "sources/Libm/Source/fenv.h"
    text = source.read_text()
    before = "#elif defined(__arm__)\n#include \"architecture/arm/fenv.h\"\n"
    after = ("#elif defined(__arm64__)\n#include \"architecture/arm64/fenv.h\"\n"
             "#elif defined(__arm__)\n#include \"architecture/arm/fenv.h\"\n")
    if text.count(before) != 1:
        raise ValueError("Libm fenv.h architecture switch changed")
    emit("usr/include/fenv.h", text.replace(before, after).encode(),
         "derived:sources/Libm/Source/fenv.h via recipes/libm/headers.py", "Libm derivation",
         ("sources/Libm/Source/fenv.h",), "arm64 fenv include selection")
    emit("usr/include/architecture/arm64/fenv.h",
         (ROOT / "recipes/libm/arm64_fenv.h").read_bytes(),
         "recipes/libm/arm64_fenv.h", "Libm derivation",
         ("recipes/libm/arm64_fenv.h",), "local ABI declaration")


if __name__ == "__main__":
    stage = Path(sys.argv[1])

    def emit(path, data, origin, selection, inputs, transform):
        output = stage / "dst" / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        print(path, "Libm", origin, selection, transform, *inputs, sep="\t")

    produce(emit)
