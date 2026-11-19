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
    anchor = b"#define I _Complex_I\n"
    if complex_source.count(anchor) != 1 or b"CMPLX" in complex_source:
        raise ValueError("Libm complex.h complex constructor definitions changed")
    # Use direct component construction to preserve signed zero and infinity.
    # WG14 N1570 section 7.3.9.3.
    # https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf
    constructors = (
        b"\n/* C11 complex constructors, ISO/IEC 9899 7.3.9.3. */\n"
        b"#if !defined(__cplusplus) && defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L \\\n"
        b"    && __has_builtin(__builtin_complex)\n"
        b"#define CMPLX(x, y)  __builtin_complex((double)(x), (double)(y))\n"
        b"#define CMPLXF(x, y) __builtin_complex((float)(x), (float)(y))\n"
        b"#define CMPLXL(x, y) __builtin_complex((long double)(x), (long double)(y))\n"
        b"#endif\n"
    )
    complex_header = complex_source.replace(old, new).replace(anchor, anchor + constructors)
    emit("usr/include/complex.h", complex_header,
         "generated:apple via recipes/libm/headers.py:complex.h",
         "recipes/libm/headers.py", ("sources/Libm/Source/complex.h", "recipes/libm/headers.py"),
         "guarded arm64 branch and C11 complex constructors")

    source = ROOT / "sources/Libm/Source/math.h"
    text = source.read_text()
    before = "#elif defined(__arm__)\n"
    after = "#elif defined(__arm__) || defined(__arm64__)\n"
    if text.count(before) != 1:
        raise ValueError("Libm math.h architecture switch changed")
    anchor = "#endif /* __MATH_H__ */"
    if text.count(anchor) != 1 or "__sinpi" in text:
        raise ValueError("Libm math.h declaration insertion point changed")
    declarations = (
        "#if defined(__ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__) && \\\n"
        "    (defined(__arm64__) || defined(__x86_64__))\n"
        "#include <Availability.h>\n"
        "\n"
        "#ifdef __cplusplus\n"
        'extern "C" {\n'
        "#endif\n"
        "extern double __sinpi(double) __API_AVAILABLE(macos(10.9));\n"
        "extern float __sinpif(float) __API_AVAILABLE(macos(10.9));\n"
        "#ifdef __cplusplus\n"
        "}\n"
        "#endif\n"
        "#endif\n"
        "\n"
    )
    math_header = text.replace(before, after).replace(anchor, declarations + anchor)
    emit("usr/include/math.h", math_header.encode(),
         "derived:sources/Libm/Source/math.h via recipes/libm/headers.py", "Libm derivation",
         ("sources/Libm/Source/math.h", "recipes/libm/headers.py", "recipes/libm/sinpi.md"),
         "guarded arm64 branch and macOS sine-pi declarations")

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
         ("recipes/libm/arm64_fenv.h", "sources/Libm/Source/ARM/fenv.h",
          "sources/xnu/osfmk/arm64/proc_reg.h"), "local ABI declaration and FPSR exception flags")

    intel_fenv = "sources/Libm/Source/Intel/fenv.h"
    text = (source.parent / "Intel/fenv.h").read_bytes()
    before = b"#define FE_ALL_EXCEPT       0x003D\n"
    after = (b"#define FE_DENORMALOPERAND  (1 << 1) /* MXCSR and x87 denormal operand flag */\n"
             b"#define FE_ALL_EXCEPT       (0x003D | FE_DENORMALOPERAND)\n")
    if text.count(before) != 1 or b"FE_DENORMALOPERAND" in text:
        raise ValueError("Libm Intel fenv.h exception definitions changed")
    emit("usr/include/architecture/i386/fenv.h", text.replace(before, after),
         f"derived:{intel_fenv} via recipes/libm/headers.py", "Libm derivation",
         (intel_fenv, "recipes/libm/headers.py", "sources/architecture/i386/fpu.h"),
         "include Intel denormal operand in FE_ALL_EXCEPT")


if __name__ == "__main__":
    stage = Path(sys.argv[1])

    def emit(path, data, origin, selection, inputs, transform):
        output = stage / "dst" / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        print(path, "Libm", origin, selection, transform, *inputs, sep="\t")

    produce(emit)
