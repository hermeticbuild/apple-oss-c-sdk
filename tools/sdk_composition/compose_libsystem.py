"""Compose an SDK from verified C headers, a generated libSystem and named SDK assets.

The output records selected files, symlinks and install-name providers in composition.json.
External aliases require their targets to be selected at the corresponding SDK paths.
"""

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

from tools.header_manifest import read_header_manifest
from tools.sdk_review.libsystem_tbd import read_install_names, read_json, read_stub


STUB = Path("usr/lib/libSystem.B.tbd")
ALIAS = Path("usr/lib/libSystem.tbd")
SYSTEM_INSTALL_NAME = "/usr/lib/libSystem.B.dylib"
FRAMEWORKS = Path("System/Library/Frameworks")
MACHO_MAGIC = {
    b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca",
}


def digest(path):
    sha256 = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def relative_path(value):
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts or path.as_posix() != value:
        raise ValueError(f"expected a canonical SDK-relative path: {value!r}")
    return path


def allowed_path(path):
    if path.is_relative_to("usr/include/c++") or path.suffix in {".a", ".dylib"}:
        raise ValueError(f"toolchain or binary asset cannot enter the composed SDK: {path}")


@dataclass(frozen=True)
class File:
    source: Path
    source_root: Path
    layer: str
    sha256: str | None
    symlink: str | None


class Plan:
    def __init__(self):
        self.files = {}
        self.directories = set()

    def directory(self, path):
        allowed_path(path)
        for destination in (path, *path.parents):
            if destination in self.files:
                raise ValueError(f"SDK path collision: {destination}")
            self.directories.add(destination)

    def file(self, destination, source, source_root, layer, sha256=None, *, symlink=None):
        allowed_path(destination)
        self.directory(destination.parent)
        if destination in self.files or destination in self.directories:
            raise ValueError(f"SDK path collision: {destination}")
        mode = source.lstat().st_mode
        if not (stat.S_ISREG(mode) or stat.S_ISLNK(mode)):
            raise ValueError(f"unsupported SDK file type: {source}")
        link = os.readlink(source) if stat.S_ISLNK(mode) else None
        if symlink is not None and link != symlink:
            raise ValueError(f"generated {destination} must be a relative alias to {symlink}")
        if link is not None and Path(link).is_absolute():
            raise ValueError(f"absolute symlink in SDK source: {source}")
        try:
            resolved = source.resolve(strict=True)
        except (OSError, RuntimeError) as err:
            raise ValueError(f"invalid SDK input path or symlink {source}: {err}") from err
        if not resolved.is_relative_to(source_root):
            raise ValueError(f"SDK source symlink escapes selected input: {source}")
        self.files[destination] = File(source, source_root, layer, sha256, link)

    def tree(self, destination, source, source_root, layer):
        self.directory(destination)
        for path in sorted(source.iterdir()):
            out = destination / path.name
            if path.is_dir() and not path.is_symlink():
                self.tree(out, path, source_root, layer)
            else:
                self.file(out, path, source_root, layer)

    def materialize(self, root):
        receipts = {}
        for path in sorted(self.directories):
            dest = root / path
            dest.mkdir(parents=True, exist_ok=True)
            dest.chmod(0o755)

        for path, file in sorted(self.files.items()):
            dest = root / path
            receipt = {"layer": file.layer, "source": file.source.relative_to(file.source_root).as_posix()}
            if file.symlink is not None:
                dest.symlink_to(file.symlink)
                receipt["symlink"] = file.symlink
            else:
                with file.source.open("rb") as stream, dest.open("xb") as output:
                    prefix = stream.read(8)
                    if prefix[:4] in MACHO_MAGIC or prefix in {b"!<arch>\n", b"!<thin>\n"}:
                        raise ValueError(f"binary or archive in SDK input: {path}")
                    output.write(prefix)
                    shutil.copyfileobj(stream, output)
                dest.chmod(0o644)
                receipt["sha256"] = digest(dest)
            receipts[path.as_posix()] = receipt

        for path, file in sorted(self.files.items()):
            dest = root / path
            if dest.is_symlink():
                try:
                    resolved = dest.resolve(strict=True)
                except (OSError, RuntimeError) as err:
                    raise ValueError(f"SDK symlink has no selected target: {path}") from err
                if not resolved.is_relative_to(root):
                    raise ValueError(f"SDK symlink escapes composed SDK: {path}")
                target = resolved.relative_to(root)
                source_target = file.source.resolve(strict=True)
                if resolved.is_dir():
                    # Framework version aliases must keep pointing within the
                    # selected framework. Header installs list individual files.
                    if file.layer not in {"sdk-gen-framework", "prepared-framework"} or not target.is_relative_to(
                            FRAMEWORKS / path.parts[len(FRAMEWORKS.parts)]):
                        raise ValueError(f"SDK directory alias escapes its selected framework: {path}")
                elif (target not in self.files or self.files[target].layer != file.layer or
                      self.files[target].source.resolve() != source_target):
                    raise ValueError(f"SDK symlink target differs from selected source: {path}")
                if path.suffix == ".tbd" and (not resolved.is_file() or target.suffix != ".tbd"):
                    raise ValueError(f"TBD alias does not resolve to a selected TBD: {path}")
            if file.sha256 is not None:
                if not dest.is_file() or digest(dest) != file.sha256:
                    raise ValueError(f"SDK file differs from its input manifest: {path}")
        return receipts


def c_install(plan, root):
    files, metadata = read_header_manifest(root)
    for name, receipt in sorted(files.items()):
        path = relative_path(name)
        if not path.is_relative_to("usr/include") or path == Path("usr/include"):
            raise ValueError(f"C header manifest path outside usr/include: {path}")
        plan.file(path, root / path, root, "c-install", receipt["sha256"])
    for source in sorted(metadata):
        if source.is_symlink():
            raise ValueError(f"C installation manifest is a symlink: {source}")
        plan.file(source.relative_to(root), source, root, "c-install", digest(source))


def libsystem_layer(plan, root, expected):
    manifest = root / "manifest.json"
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError(f"missing regular libSystem layer manifest: {manifest}")
    # Hash and parse the same bytes, then validate the stub and each link against it.
    data = manifest.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("libSystem layer manifest digest mismatch")
    record = read_json(data)
    if not isinstance(record, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("tbd_sha256"))):
        raise ValueError("libSystem layer manifest has no valid TBD digest")
    links = record.get("symlinks", {ALIAS.as_posix(): STUB.name})
    if not isinstance(links, dict) or links.get(ALIAS.as_posix()) != STUB.name:
        raise ValueError(f"libSystem layer manifest must declare {ALIAS} as an alias to {STUB.name}")
    symlinks = {}
    for name, target in links.items():
        path = relative_path(name)
        if (path == STUB or path.parent != STUB.parent or
                not re.fullmatch(r"lib[A-Za-z0-9_.+-]+\.tbd", path.name)):
            raise ValueError(f"unexpected declared libSystem symlink path: {path}")
        if path != ALIAS and target != ALIAS.name:
            raise ValueError(f"unexpected declared libSystem symlink target for {path}: {target!r}")
        symlinks[path] = target

    usr = root / "usr"
    library = root / STUB.parent
    if any(path.is_symlink() or not path.is_dir() for path in (usr, library)):
        raise ValueError("generated libSystem payload requires real usr and usr/lib directories")
    files = {path.relative_to(root) for path in usr.iterdir() if path != library}
    files.update(path.relative_to(root) for path in library.iterdir())
    if files != {STUB, *symlinks}:
        raise ValueError(f"unexpected generated libSystem payload: {sorted(str(path) for path in files)}")
    if (root / STUB).is_symlink() or not (root / STUB).is_file():
        raise ValueError(f"generated libSystem must be a regular TBD: {STUB}")
    plan.file(STUB, root / STUB, root, "generated-libsystem", record["tbd_sha256"])
    for path, target in sorted(symlinks.items()):
        plan.file(path, root / path, root, "generated-libsystem", symlink=target)
    return record


def sdk_settings(package, sdk, receipts):
    if "c_header_manifest_sha256" not in package:
        return  # Older qualification packages carried only the stub digest.
    if receipts.get("header-manifest.tsv", {}).get("sha256") != package["c_header_manifest_sha256"]:
        raise ValueError("selected C installation differs from the one used to generate libSystem")
    if package.get("sdk") != "macosx26.5":
        return
    settings = {"CanonicalName": "macosx26.5", "Version": "26.5", "MaximumDeploymentTarget": "26.5",
                "SupportedTargets": {"macosx": {"Archs": ["arm64", "x86_64"], "LLVMTargetTripleVendor": "apple",
                                                 "LLVMTargetTripleSys": "macosx"}}}
    path = sdk / "SDKSettings.json"
    path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n")
    receipts[path.name] = {"layer": "sdk-settings", "source": "libsystem:macosx26.5", "sha256": digest(path)}


def framework(plan, sdk_gen, name, *, prepared=None):
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.+-]*", name):
        raise ValueError(f"invalid SDK Gen framework name: {name}")
    relative = FRAMEWORKS / f"{name}.framework"
    source = prepared if prepared is not None else sdk_gen / relative
    if (source.name != relative.name or source.is_symlink() or not source.is_dir()
            or (prepared is None and not source.resolve().is_relative_to(sdk_gen))):
        raise ValueError(f"missing or escaped framework: {relative}")
    source = source.resolve()
    plan.tree(relative, source, source, "prepared-framework" if prepared is not None else "sdk-gen-framework")


def external_stub(plan, spec):
    destination, separator, source = spec.partition("=")
    if not separator or not source:
        raise ValueError("--external-stub requires SDK/relative/path.tbd=/source/path.tbd")
    path = relative_path(destination)
    source = Path(source).absolute()
    if not path.is_relative_to("usr/lib") or path.suffix != ".tbd":
        raise ValueError(f"external stub destination must be a .tbd under usr/lib: {path}")
    if source.suffix != ".tbd" or not source.is_file():
        raise ValueError(f"external stub source must resolve to a regular .tbd file: {source}")
    source_root = source.parent.resolve()
    plan.file(path, source_root / source.name, source_root, "external-stub")


def providers(plan, root, llvm):
    reader = llvm / "bin/llvm-readtapi"
    generated = read_stub((root / STUB).read_text(encoding="utf-8"), reader)
    if generated.main != SYSTEM_INSTALL_NAME or generated.format != 5:
        raise ValueError("generated libSystem umbrella must have the expected install name and v5 format")
    locations = defaultdict(list, {name: [STUB.as_posix()] for name in generated.libraries})
    for path in sorted(plan.files):
        source = root / path
        if path == STUB or source.is_symlink():
            continue
        content = source.read_bytes()
        start = content.lstrip()
        if (path.suffix != ".tbd" and not start.startswith(b"--- !tapi-tbd") and
                not (start.startswith(b"{") and b'"tapi_tbd_version"' in content)):
            continue
        try:
            names = read_install_names(content.decode("utf-8"), reader)
        except (ValueError, OSError) as err:
            raise ValueError(f"cannot account for TBD providers in {path}: {err}") from err
        for name in names:
            if name in generated.libraries:
                raise ValueError(f"{path} shadows generated libSystem install name {name} in {STUB}")
            locations[name].append(path.as_posix())
    return locations


def compose(args):
    out = args.out.parent.resolve() / args.out.name
    if os.path.lexists(out):
        raise ValueError(f"output already exists: {out}")
    plan = Plan()
    c_install(plan, args.c_install.resolve())
    package = libsystem_layer(plan, args.libsystem.resolve(), args.libsystem_manifest_sha256)
    for name in args.framework:
        framework(plan, args.sdk_gen.resolve(), name)
    for name, source in args.prepared_framework:
        framework(plan, None, name, prepared=Path(source))
    for spec in args.external_stub:
        external_stub(plan, spec)

    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".compose-libsystem-", dir=out.parent) as temporary:
        sdk = Path(temporary) / "SDK"
        sdk.mkdir()
        receipts = plan.materialize(sdk)
        sdk_settings(package, sdk, receipts)
        composition = {
            "schema": 1,
            "libsystem_manifest_sha256": args.libsystem_manifest_sha256,
            "files": receipts,
            "providers": providers(plan, sdk, args.llvm.resolve()),
        }
        manifest = sdk / "composition.json"
        manifest.write_text(json.dumps(composition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest.chmod(0o644)
        if os.path.lexists(out):
            raise ValueError(f"output already exists: {out}")
        sdk.rename(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("c-install", "libsystem", "llvm", "out"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--libsystem-manifest-sha256", required=True,
                        help="expected SHA-256 of the libSystem package's manifest.json")
    parser.add_argument("--sdk-gen", type=Path, help="SDK Gen root containing System/Library/Frameworks")
    parser.add_argument("--framework", action="append", default=[], help="public SDK Gen framework name")
    parser.add_argument("--prepared-framework", nargs=2, action="append", default=[], metavar=("NAME", "DIRECTORY"),
                        help="select a previously qualified framework layer and record its files separately")
    parser.add_argument("--external-stub", action="append", default=[], metavar="DESTINATION=SOURCE",
                        help="select one .tbd or relative alias at a path below usr/lib")
    args = parser.parse_args()
    if args.framework and not args.sdk_gen:
        parser.error("--framework requires --sdk-gen")
    try:
        compose(args)
    except (OSError, ValueError, KeyError) as err:
        parser.exit(1, f"compose-libsystem: {err}\n")


if __name__ == "__main__":
    main()
