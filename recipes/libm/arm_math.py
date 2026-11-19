"""Use the pinned Apple binary64 classifier in Darwin arm64 C clients."""

from pathlib import Path
import sys


def render(source):
    header = (source / "math.h").read_text()
    classifier = (source / "fpclassify.c").read_text()
    signature = "int __fpclassify( double x )"
    macro_start = "#define fpclassify(x)"
    macro_end = "\n\nextern int __fpclassifyf"
    call = "__fpclassify((double)(x))"
    if (classifier.count(signature) != 1 or classifier.count('#include "math.h"') != 1
            or header.count(macro_start) != 1 or header.count(macro_end) != 1):
        raise ValueError("Apple Libm classifier source changed")

    begin = header.index(macro_start)
    end = header.index(macro_end, begin)
    original = header[begin:end]
    if original.count(call) != 1:
        raise ValueError("Apple Libm binary64 dispatch changed")
    local = "__darwin_libm_classify_binary64"
    # math.h is being installed. Keep the C source's notice, stdint include
    # and implementation, giving the helper internal linkage in each client.
    helper = classifier.replace('#include "math.h"\n', "").replace(
        signature, f"static __inline__ int {local}(double x)")
    guard = ("#if defined(__arm64__) && defined(__ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__)"
             " && !defined(__cplusplus)")
    macro = original.replace(call, f"{local}((double)(x))")
    return header[:begin] + f"{guard}\n{helper}\n{macro}\n#else\n{original}\n#endif" + header[end:]


if __name__ == "__main__":
    Path(sys.argv[2]).write_text(render(Path(sys.argv[1])))
