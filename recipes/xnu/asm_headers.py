"""Stage XNU's generated public Mach assembler headers for macOS clients."""

import os
from pathlib import Path
import re
import sys

from .headers import filter_public


MACH_ARCHES = ("arm64", "i386")


def assignments(makefile: Path) -> dict[str, tuple[str, str]]:
    # These component Makefiles use literal install fields and one VPATH
    # append. Read only the fields needed for the generated asm.h rule.
    lines = re.sub(r"\\\r?\n[ \t]*", " ", makefile.read_text()).splitlines()
    values = {}
    for line in lines:
        match = re.fullmatch(r"(INSTALL_MD_GEN_LIST|INSTALL_MD_DIR|VPATH)[ \t]*(:?=)[ \t]*(.*)",
                             line.split("#", 1)[0].rstrip())
        if match:
            name, operator, value = match.groups()
            if name in values:
                raise ValueError(f"{makefile}: duplicate {name}")
            values[name] = (operator, value)
    return values


def asm_rule(xnu: Path, arch: str) -> tuple[str, str, str]:
    component = xnu / "osfmk/mach" / arch
    makefile = component / "Makefile"
    values = assignments(makefile)
    generated = values.get("INSTALL_MD_GEN_LIST", ("", ""))
    destination = values.get("INSTALL_MD_DIR")
    vpath = values.get("VPATH", ("", ""))
    append = re.fullmatch(r"\$\(VPATH\):\$\(SOURCE\)/([a-zA-Z0-9_./-]+)", vpath[1])

    if generated[0] != "=" or "asm.h" not in generated[1].split():
        raise ValueError(f"{makefile}: asm.h missing from INSTALL_MD_GEN_LIST")
    if destination != ("=", f"mach/{arch}") or vpath[0] != ":=" or not append:
        raise ValueError(f"{makefile}: unsupported generated asm.h destination or VPATH")

    # MakeInc.def searches SOURCE before the component appends its machine
    # directory to VPATH. These asm.h prerequisites have no object directory
    # generator in the pinned rules.
    candidates = (component / "asm.h", component / append[1] / "asm.h")
    prerequisite = next((path for path in candidates if path.is_file()), None)
    if prerequisite is None:
        raise ValueError(f"{makefile}: missing asm.h VPATH prerequisite")
    source = prerequisite.resolve()
    if not source.is_relative_to(xnu):
        raise ValueError(f"{makefile}: out-of-tree VPATH prerequisite {source}")
    return (f"usr/include/{destination[1]}/asm.h",
            source.relative_to(xnu).as_posix(), makefile.relative_to(xnu).as_posix())


def stage_asm_headers(stage: Path, xnu: Path) -> None:
    for arch in MACH_ARCHES:
        destination, source, rule = asm_rule(xnu, arch)
        data = filter_public(xnu / source)
        # MakeInc.rule uses decomment only to decide whether to install the
        # unifdef output. Preserve the comments in the installed bytes.
        if not re.sub(rb"/\*.*?\*/|//[^\n]*", b"", data, flags=re.DOTALL).strip():
            continue
        header = stage / "dst" / destination
        header.parent.mkdir(parents=True, exist_ok=True)
        with header.open("xb") as output:
            output.write(data)
        inputs = (
            f"sources/xnu/{source}", f"sources/xnu/{rule}",
            "sources/xnu/makedefs/MakeInc.cmd",
            "sources/xnu/makedefs/MakeInc.def",
            "sources/xnu/makedefs/MakeInc.rule",
        )
        print(destination, "xnu", f"derived:{inputs[0]}", f"{rule}:INSTALL_MD_GEN_LIST",
              "XNU generated public header VPATH and macOS public unifdef", *inputs, sep="\t")


if __name__ == "__main__":
    stage_asm_headers(Path(sys.argv[1]), (Path(os.environ["SOURCE_ROOT"]) / "xnu").resolve())
