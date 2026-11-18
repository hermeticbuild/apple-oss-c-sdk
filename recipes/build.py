"""Assemble the staged public headers and the explicitly generated headers."""

import argparse
import json
from pathlib import Path

from recipes.assembly import Assembly
from recipes.compat.headers import produce as produce_compat
from recipes.libm.headers import produce as produce_libm
from recipes.upstream import collect
from recipes.xnu.headers import collect_mig, produce_public, produce_symbol_headers, produce_unifdef


def prepare(staging: Path, out: Path) -> None:
    assembly = Assembly()
    collect(assembly, staging)
    produce_public(assembly)
    produce_libm(lambda path, data, origin, selection, inputs, transform:
                 assembly.add("Libm", path, data, origin, selection,
                              inputs=inputs, transform=transform))
    produce_compat(assembly)
    produce_unifdef(assembly)
    produce_symbol_headers(assembly, staging / "xnu")
    assembly.write(out)


def assemble(staging: Path, out: Path) -> None:
    bootstrap = staging / "pre-mig"
    owners = json.loads((bootstrap / "header-owners.json").read_text())["files"]
    assembly = Assembly()
    for path, record in owners.items():
        assembly.add(path=path, data=(bootstrap / path).read_bytes(), **record)
    collect_mig(assembly, staging / "mig-arm64")
    assembly.write(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("pre-mig", "assemble"))
    parser.add_argument("staging", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    action = prepare if args.action == "pre-mig" else assemble
    action(args.staging, args.out)


if __name__ == "__main__":
    main()
