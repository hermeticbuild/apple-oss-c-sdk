"""Explicit file copies. The manifest is the resolved owner list for direct files."""

import csv
from pathlib import Path

from .assembly import Assembly
from .libc.headers import libc_public_headers
from .public_sources import architecture_public_headers, public_xcode_selection
from .xnu.headers import XNU_PUBLIC_MAKE_DIRS, xnu_public_make_headers, libsyscall_public_mach_headers


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "recipes/copies.tsv"


def produce(assembly: Assembly) -> None:
    libc_public = set(libc_public_headers())
    architecture_public = {path.as_posix() for path in architecture_public_headers()}
    xnu_public = {
        f"{source_dir}/Makefile:{list_name}": {
            f"usr/include/{target_dir}/{name}": f"sources/xnu/{source_dir}/{name}"
            for name in xnu_public_make_headers(source_dir, list_name)
        }
        for source_dir, target_dir, list_name in XNU_PUBLIC_MAKE_DIRS
    }
    mach_public = {f"usr/include/mach/{name}":
                   f"sources/xnu/libsyscall/mach/mach/{name}"
                   for name in libsyscall_public_mach_headers()}
    with MANIFEST.open(newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            path = row["install_path"]
            source = row["source"]
            if not source.startswith("sources/") or ".." in Path(source).parts:
                raise ValueError(f"invalid copy source: {source}")
            source_file = ROOT / source
            owner = Path(source).parts[1]
            selection = row["selection"]
            if selection == "Libc/xcodescripts/headers.sh:public":
                relative = path.removeprefix("usr/include/")
                if relative not in libc_public or source != f"sources/Libc/include/{relative}":
                    raise ValueError(f"Libc public list does not select {path}")
            elif selection in xnu_public:
                if xnu_public[selection].get(path) != source:
                    raise ValueError(f"XNU public list does not select {path}")
            elif selection == "xnu/libsyscall/xcodescripts/mach_install_mig.sh:MACH_HDRS":
                if mach_public.get(path) != source:
                    raise ValueError(f"Mach install list does not select {path}")
            elif selection == "architecture/Makefile:copyhdrs":
                relative = path.removeprefix("usr/include/architecture/")
                if (relative not in architecture_public or
                        source != f"sources/architecture/{relative}"):
                    raise ValueError(f"architecture install list does not select {path}")
            elif selection.endswith(":Public"):
                if selection != public_xcode_selection(source_file):
                    raise ValueError(f"Xcode public phase does not select {source}")
            assembly.add(owner, path, source_file.read_bytes(), source,
                         selection)
