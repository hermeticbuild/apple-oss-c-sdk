#!/usr/bin/env python3
"""Assemble the selected Apple OSS C header recipes into an empty sysroot."""

import argparse
import tempfile
from pathlib import Path

from recipes.c_profile import selected_paths
from recipes.assembly import Assembly
from recipes.availability_versions.headers import produce as produce_availability
from recipes.compat.headers import produce as produce_compat
from recipes.copies import produce as produce_copies
from recipes.libc.headers import produce as produce_libc
from recipes.libm.headers import produce as produce_libm
from recipes.xnu.headers import (produce_mig, produce_symbol_headers,
                                 produce_unifdef)


def assemble(mig: Path, clang: Path, out: Path) -> None:
    if out.exists():
        raise ValueError(f"output already exists: {out}")
    assembly = Assembly(set(selected_paths()))
    produce_copies(assembly)
    produce_libc(assembly)
    produce_libm(lambda path, data, origin, selection, inputs, transform:
                 assembly.add("Libm", path, data, origin, selection,
                              inputs=inputs, transform=transform))
    produce_compat(assembly)
    produce_unifdef(assembly)
    with tempfile.TemporaryDirectory(prefix="apple-oss-c-recipes-") as temporary:
        staging = Path(temporary)
        produce_availability(assembly, staging / "availability")
        produce_symbol_headers(assembly, staging / "xnu")
        # MIG preprocesses against the already selected public headers. The
        # pre-MIG tree is a private action input, never a released install.
        bootstrap = staging / "pre-mig"
        assembly.write(bootstrap, complete=False)
        produce_mig(assembly, mig, clang, bootstrap, staging)
    assembly.write(out, complete=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mig", type=Path, default=Path("/usr/bin/mig"),
                        help="macOS system mig (default: /usr/bin/mig)")
    parser.add_argument("--clang", type=Path, required=True,
                        help="clang from the pinned minimal LLVM prebuilt")
    args = parser.parse_args()
    assemble(args.mig.absolute(), args.clang.absolute(), args.out.absolute())
    print(args.out.absolute())


if __name__ == "__main__":
    main()
