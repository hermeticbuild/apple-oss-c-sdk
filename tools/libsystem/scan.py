"""Inventory C declarations and their Mach-O client references per public root."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from tools.header_manifest import read_header_manifest
from tools.qualify_headers.trace_includes import dependencies


LLVM_VERSION = "23.1.2"
LLVM_COMMIT = "85ac560262434c9ccfc0c183ec22d4138ed647fb"
PROFILES = {"default": (), "darwin": ("-D_DARWIN_C_SOURCE",)}
KINDS = {"FunctionDecl": "function", "VarDecl": "data", "TypedefDecl": "type",
         "RecordDecl": "type", "EnumDecl": "type"}
INSTALL_NAME = "/usr/lib/libsystem-scan.dylib"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(tool, flags, cwd):
    argv = [str(tool), *map(str, flags)]
    process = subprocess.run(argv, cwd=cwd, env={"LC_ALL": "C"},
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode:
        raise ValueError(f"{tool.name} exited {process.returncode}: {process.stderr.strip()}")
    return process.stdout


def dump_json(doc):
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"


def include(relative):
    name = Path(relative).relative_to("usr/include").as_posix()
    if not re.fullmatch(r"[a-zA-Z0-9_./+-]+", name):
        raise ValueError(f"unsupported include spelling: {relative}")
    return f"#include <{name}>\n"


def header_path(root, requested):
    path = Path(requested)
    if path.is_absolute():
        path = path.resolve().relative_to(root)
    elif not path.is_relative_to("usr/include"):
        path = Path("usr/include") / path
    if ".." in path.parts:
        raise ValueError(f"header must be inside usr/include: {requested}")
    relative = path.as_posix()
    include(relative)
    return relative


def header_receipt(root, files, relative):
    path = root / relative
    record = files.get(relative)
    if record is None:
        raise ValueError(f"header lacks C installation provenance: {relative}")
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError(f"header absent from C installation: {relative}")
    if digest(path) != record["sha256"]:
        raise ValueError(f"installed header differs from manifest: {relative}")
    return {"path": relative, **{key: record[key] for key in
                                 ("sha256", "owner", "origin", "selection", "transform", "inputs")
                                 if key in record}}


def source_locations(ast):
    """Recover Clang 23's elided physical file and line across the JSON stream."""
    file = None
    line = None

    def walk(value):
        nonlocal file, line
        if isinstance(value, dict):
            # JSONNodeDumper::writeBareSourceLocation omits repeated values,
            # including across ranges, macro locations and child nodes.
            if {"offset", "col", "tokLen"} <= value.keys():
                file = value.get("file", file)
                line = value.get("line", line)
                value["file"] = file
                value["line"] = line
                return
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(ast)


def read_declarations(ast, sources, root, resource):
    source_locations(ast)
    rows = []
    for node in ast["inner"]:
        kind = KINDS.get(node["kind"])
        if not kind or node.get("isImplicit"):
            continue
        location = node["loc"]
        # A macro-generated declaration belongs to its invocation header.
        location = location.get("expansionLoc", location)
        file = location.get("file")
        if not file or not Path(file).is_absolute():
            raise ValueError(f"missing physical declaration location for {node.get('name')}")
        path = Path(file).resolve()
        if path.is_relative_to(resource):
            continue
        if path not in sources:
            raise ValueError(f"declaration from an undeclared input: {file}")
        if node.get("tls"):
            kind = "tls"
        type_name = node.get("type", {}).get("qualType")
        if type_name:
            type_name = type_name.replace(str(root), "$C_INSTALL")
            type_name = type_name.replace(str(resource), "$LLVM_RESOURCE")
        attrs = [entry for entry in node.get("inner", []) if entry["kind"].endswith("Attr")]
        excluded = None
        if kind == "type":
            excluded = "type-declaration"
        elif node.get("storageClass") == "static":
            excluded = "internal-linkage"
        elif any(attr.get("visibility") not in (None, "default") for attr in attrs):
            excluded = "non-default-visibility"
        elif any(attr["kind"] == "UnavailableAttr" or (
                attr.get("platform") == "macos" and attr.get("unavailable")) for attr in attrs):
            excluded = "unavailable"
        rows.append({
            "header": sources[path],
            "line": location["line"],
            "column": location["col"],
            "offset": location["offset"],
            "c_name": node.get("name"),
            "kind": kind,
            "type": type_name,
            "ast_symbol": node.get("mangledName"),
            "inline": bool(node.get("inline") or any(attr["kind"] == "AlwaysInlineAttr"
                                                    for attr in attrs)),
            "excluded": excluded,
        })
    return rows


def installapi_exports(path, target, minimum):
    tbd = json.loads(path.read_text())
    if set(tbd) != {"main_library", "tapi_tbd_version"} or tbd["tapi_tbd_version"] != 5:
        raise ValueError("unexpected InstallAPI TBD document")
    library = tbd["main_library"]
    expected_fields = {"compatibility_versions", "current_versions", "exported_symbols",
                       "flags", "install_names", "target_info"}
    if library.keys() - expected_fields or library["install_names"] != [{"name": INSTALL_NAME}]:
        raise ValueError("unexpected InstallAPI library metadata")
    if library["target_info"] != [{"target": target, "min_deployment": minimum}]:
        raise ValueError(f"unexpected InstallAPI target, expected {target} at {minimum}")
    exports = {}
    for group in library.get("exported_symbols", []):
        if group.get("targets", [target]) != [target] or group.keys() - {"targets", "data", "text"}:
            raise ValueError(f"unsupported InstallAPI export group: {group}")
        for section, kind in (("text", "function"), ("data", "data")):
            categories = group.get(section, {})
            if categories.keys() - {"global", "weak", "thread_local"}:
                raise ValueError(f"unsupported InstallAPI symbol categories: {categories}")
            for category, names in categories.items():
                if category == "thread_local" and kind != "data":
                    raise ValueError("InstallAPI emitted TLS outside the data section")
                for name in names:
                    if name in exports:
                        raise ValueError(f"duplicate InstallAPI symbol: {name}")
                    exports[name] = ("tls" if category == "thread_local" else kind,
                                     category == "weak")
    return exports


def read_object(tools, cwd, path, symbol, kind):
    undefined = {}
    nm = run(tools / "llvm-nm", ("-m", "-u", path), cwd)
    for line in nm.splitlines():
        match = re.fullmatch(r"\s*\(undefined\) (weak )?external (.+)", line)
        if not match:
            raise ValueError(f"unrecognized llvm-nm undefined symbol: {line}")
        weak, name = match.groups()
        if name in undefined:
            raise ValueError(f"duplicate llvm-nm undefined symbol: {name}")
        undefined[name] = bool(weak)
    if set(undefined) != {symbol}:
        return None, f"expected one undefined symbol {symbol!r}, saw {sorted(undefined)}"

    relocations = []
    section = None
    objdump = run(tools / "llvm-objdump", ("-r", path), cwd)
    for line in objdump.splitlines():
        record = re.fullmatch(r"RELOCATION RECORDS FOR \[(.+)\]:", line)
        if record:
            section = record[1]
        match = re.fullmatch(r"([0-9a-f]+)\s+(\S+)\s+(.+)", line)
        if section and match and (match[3] == symbol or
                                 (match[2] == "X86_64_RELOC_TLV" and match[3] == f"{symbol}@TLVP")):
            relocations.append({"section": section, "offset": int(match[1], 16), "type": match[2]})
    if not relocations:
        return None, "missing client relocation"
    tls_types = {"X86_64_RELOC_TLV", "ARM64_RELOC_TLVP_LOAD_PAGEOFF12", "ARM64_RELOC_TLVP_LOAD_PAGE21"}
    tls_relocation = any(entry["type"] in tls_types for entry in relocations)
    if tls_relocation != (kind == "tls"):
        return None, "TLS classification disagrees with client relocation"
    return {"weak_import": undefined[symbol], "relocations": relocations}, None


def declaration_key(row):
    return (row["header"], row["offset"], row["c_name"] or "", row["kind"])


def probe_references(tools, flags, work, public_root, declarations, exports):
    imports = []
    unresolved = []
    by_symbol = defaultdict(list)
    symbols_by_name = defaultdict(set)
    for row in declarations:
        symbol = row["ast_symbol"]
        if row["excluded"] is None and symbol in exports:
            by_symbol[symbol].append(row)
            symbols_by_name[row["c_name"]].add(symbol)
        elif row["excluded"] is None:
            row["excluded"] = "not-exported-by-installapi"

    for symbol, (kind, weak_definition) in sorted(exports.items()):
        rows = by_symbol[symbol]
        if not rows:
            unresolved.append({"symbol": symbol, "reason": "no matching C AST declaration"})
        by_name = defaultdict(list)
        for row in rows:
            by_name[row["c_name"]].append(row)
        for name, redeclarations in sorted(by_name.items()):
            context = {"symbol": symbol, "c_name": name, "kind": kind, "public_root": public_root}
            if (not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", name) or
                    symbols_by_name[name] != {symbol} or
                    any(row["kind"] != kind for row in redeclarations) or
                    (len(by_name) > 1 and any(row["inline"] for row in redeclarations))):
                unresolved.append({**context, "reason": "unsupported or ambiguous C declaration"})
                continue

            probe_id = hashlib.sha256(f"{symbol}\0{name}".encode()).hexdigest()[:24]
            source = work / f"{probe_id}.c"
            obj = work / f"{probe_id}.o"
            address = f"&({name})"
            signature = f"static __typeof__({address}) __attribute__((used)) __libsystem_scan_reference"
            if kind == "tls":
                code = f"{signature}(void) {{ return {address}; }}\n"
            else:
                code = f"{signature} = {address};\n"
            source.write_text(include(public_root) + code)
            try:
                run(tools / "clang", (*flags, "-O0", "-fno-stack-protector", "-c", source,
                                      "-o", obj), work)
            except ValueError as err:
                (work / f"{probe_id}.log").write_text(str(err) + "\n")
                unresolved.append({**context, "reason": "client reference compilation failed",
                                   "probe": f"{work.name}/{source.name}"})
                continue
            observed, error = read_object(tools, work, obj, symbol, kind)
            if error:
                unresolved.append({**context, "reason": error, "probe": f"{work.name}/{source.name}"})
                continue
            object_digest = digest(obj)
            for row in redeclarations:
                imports.append({**context, **observed, "header": row["header"],
                                "declaration_offset": row["offset"],
                                "installapi_weak_definition": weak_definition,
                                "object": f"{work.name}/{obj.name}", "object_sha256": object_digest})
    return imports, unresolved


def scan_root(tools, flags, target, minimum, root, resource, files, public_root, work):
    source = work / "root.c"
    depfile = work / "root.d"
    source.write_text(include(public_root))
    ast_flags = (*flags, "-Xclang", "-ast-dump=json", "-fsyntax-only")
    ast = json.loads(run(tools / "clang", (*ast_flags, "-MD", "-MF", depfile,
                                          "-MT", "scan", source), work))
    sources = {}
    receipts = []
    for path in sorted(set(dependencies(depfile)) - {source}):
        if path.is_relative_to(resource):
            continue
        if not path.is_relative_to(root):
            raise ValueError(f"dependency outside the declared LLVM and C installations: {path}")
        relative = path.relative_to(root).as_posix()
        receipts.append(header_receipt(root, files, relative))
        sources[path] = relative
    if public_root not in sources.values():
        raise ValueError(f"public root did not resolve to its manifest path: {public_root}")
    declarations = read_declarations(ast, sources, root, resource)

    # InstallAPI only visits registered headers. Register declaring headers
    # reached from this root and check that the added includes preserve the AST
    # declaration inventory. The ordinary client probe still includes only the root.
    registered = [public_root, *sorted({row["header"] for row in declarations
                                        if row["excluded"] is None} - {public_root})]
    if len(registered) > 1:
        registered_source = work / "registered.c"
        registered_source.write_text("".join(map(include, registered)))
        registered_ast = json.loads(run(tools / "clang", (*ast_flags, registered_source), work))
        if read_declarations(registered_ast, sources, root, resource) != declarations:
            raise ValueError(f"registering transitive headers changes the declaration "
                             f"inventory of {public_root}")

    header_list = work / "headers.json"
    header_list.write_text(dump_json({
        "version": "3",
        "headers": [{"type": "public", "path": str(root / relative)} for relative in registered],
    }))
    tbd = work / "installapi.tbd"
    run(tools / "clang-installapi", (*flags, "-dynamiclib", "-install_name", INSTALL_NAME,
                                    "--filetype=tbd-v5", header_list, "-o", tbd), work)
    exports = installapi_exports(tbd, target, minimum)
    imports, unresolved = probe_references(tools, flags, work, public_root, declarations, exports)
    for row in declarations:
        row["public_root"] = public_root
        row["eligibility"] = row.pop("excluded") or "installapi-export"
    for row in unresolved:
        row["public_root"] = public_root
    return receipts, sorted(declarations, key=declaration_key), imports, unresolved


def scan(llvm, root, arch, minimum, profile, headers, work):
    tools = llvm / "bin"
    version = run(tools / "clang", ("--version",), work).splitlines()[0]
    if not (version.startswith(f"clang version {LLVM_VERSION} ") and LLVM_COMMIT in version):
        raise ValueError(f"expected LLVM {LLVM_VERSION} ({LLVM_COMMIT}), got {version}")
    resource = Path(run(tools / "clang", ("--no-default-config", "-print-resource-dir"),
                        work).strip()).resolve() / "include"
    if not resource.is_relative_to(llvm) or not resource.is_dir():
        raise ValueError("Clang resource headers are missing from the supplied LLVM bundle")
    files, metadata = read_header_manifest(root)
    for path in metadata:
        if not path.resolve().is_relative_to(root):
            raise ValueError(f"manifest metadata outside the C installation: {path}")
    flags = ("--no-default-config", "-x", "c", "-nostdinc", "-isysroot", root,
             "-isystem", resource, "-isystem", root / "usr/include",
             "-target", f"{arch}-apple-macos{minimum}", *PROFILES[profile])
    report = {
        "schema_version": 1,
        "arch": arch,
        "minimum": minimum,
        "profile": profile,
        "llvm_version": LLVM_VERSION,
        "llvm_commit": LLVM_COMMIT,
        "c_manifest": [{"path": path.relative_to(root).as_posix(), "sha256": digest(path)}
                       for path in sorted(metadata)],
        "headers": [],
        "contexts": [],
        "declarations": [],
        "imports": [],
        "unresolved": [],
    }
    for public_root in sorted({header_path(root, header) for header in headers}):
        report["headers"].append(header_receipt(root, files, public_root))
        work_root = work / hashlib.sha256(public_root.encode()).hexdigest()[:24]
        work_root.mkdir()
        receipts, declarations, imports, unresolved = scan_root(
            tools, flags, f"{arch}-macos", minimum, root, resource, files, public_root, work_root)
        report["contexts"].append({"public_root": public_root, "headers": receipts})
        report["declarations"].extend(declarations)
        report["imports"].extend(imports)
        report["unresolved"].extend(unresolved)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm", required=True, type=Path, help="verified official bundle root")
    parser.add_argument("--c-install", required=True, type=Path)
    parser.add_argument("--arch", required=True, choices=("arm64", "x86_64"))
    parser.add_argument("--minimum", required=True)
    parser.add_argument("--profile", choices=PROFILES, default="default")
    parser.add_argument("--header", required=True, action="append", help="public C include root")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--objects", type=Path,
                        help="new scratch directory to retain InstallAPI and client object evidence")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", args.minimum):
        parser.error("--minimum must be a macOS deployment version such as 11.0")

    def inventory(work):
        return scan(args.llvm.resolve(), args.c_install.resolve(), args.arch,
                    args.minimum, args.profile, args.header, work.resolve())

    try:
        if args.objects:
            args.objects.mkdir(parents=True)
            report = inventory(args.objects)
        else:
            with tempfile.TemporaryDirectory(prefix="libsystem-scan-") as work:
                report = inventory(Path(work))
        with tempfile.NamedTemporaryFile(mode="w", dir=args.out.parent, delete=False) as stream:
            stream.write(dump_json(report))
        Path(stream.name).replace(args.out)
    except (OSError, ValueError, KeyError) as err:
        parser.exit(1, f"scan: {err}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
