"""Derive Libc's fortified imports from public clients and its FortifySource target."""

import json
from pathlib import Path
import re

from .emit import ARCHES
from .libc_aliases import LIBC, REVISION
from .scan import digest, run


LOCK = Path(__file__).parent / "data/macosx26.5/libc-fortify.json"
FIXTURE = Path(__file__).parent / "fixtures/fortify.c"


def install(source, llvm, c_install, minimum, work, images, inventories):
    files = json.loads(LOCK.read_bytes())
    for name, expected in files.items():
        if digest(source / name) != expected:
            raise ValueError(f"review changed FortifySource input: {name}")
    work.mkdir()
    clang = llvm / "bin/clang"
    nm = llvm / "bin/llvm-nm"
    resource = Path(run(clang, ["--no-default-config", "-print-resource-dir"], work).strip()).resolve() / "include"
    if not resource.is_dir() or not resource.is_relative_to(llvm):
        raise ValueError("Clang resource headers must come from the verified LLVM bundle")
    implementations = [name for name in sorted(files) if name.endswith(".c")]
    owner, = (image for image in images if image["install_name"] == LIBC)
    targets = {}
    for arch in ARCHES:
        flags = ["--no-default-config", "-target", f"{arch}-apple-macos{minimum}", "-nostdinc",
                 "-isysroot", c_install, "-isystem", resource, "-isystem", c_install / "usr/include"]
        client = work / f"{arch}-client.o"
        run(clang, [*flags, "-std=c17", "-O2", "-D_DARWIN_C_SOURCE", "-D_FORTIFY_SOURCE=2",
                    "-Werror", "-Wno-deprecated-declarations", "-c", FIXTURE, "-o", client], work)
        imports = set(run(nm, ["-uj", client], work).splitlines())
        confirmed = {}
        for name in implementations:
            obj = work / f"{arch}-{Path(name).stem}.o"
            run(clang, [*flags, "-c", name, "-o", obj], source)
            lines = run(nm, ["-m", "--defined-only", "--extern-only", obj], work).splitlines()
            for line in lines:
                match = re.fullmatch(r"[0-9a-fA-F]+ \(__TEXT,__text\) external (\S+)", line)
                if match and match[1] in imports:
                    symbol = match[1]
                    if symbol in confirmed:
                        raise ValueError(f"ambiguous FortifySource definition for {symbol} on {arch}")
                    confirmed[symbol] = {"source": name, "object_sha256": digest(obj)}
        unused = set(implementations) - {fact["source"] for fact in confirmed.values()}
        if unused or set(confirmed) != imports:
            raise ValueError(f"{arch}: FortifySource fixture and target disagree: "
                             f"unexercised sources {sorted(unused)}, unresolved imports {sorted(imports - confirmed.keys())}")
        exports = owner["slices"][arch]["exports"]
        for symbol, fact in sorted(confirmed.items()):
            if exports.setdefault(symbol, "text.global") != "text.global":
                raise ValueError(f"{arch}: conflicting Libc definition for {symbol}")
            url = f"https://github.com/apple-oss-distributions/Libc/blob/{REVISION}/{fact['source']}"
            inventories[arch].append({"symbol": symbol, "kind": "function", "header": url})
        targets[arch] = {"client_sha256": digest(client), "definitions": confirmed}
    return {"libc_commit": REVISION, "source_sha256": files, "fixture_sha256": digest(FIXTURE), "targets": targets}
