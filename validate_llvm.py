#!/usr/bin/env python3
"""Compose an SDK and build hermetic-llvm for both macOS architectures."""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "tests/llvm_consumer/MODULE.bazel.in"


def archive_sdk(sdk: Path, archive: Path) -> str:
    tar = subprocess.Popen(["tar", "-cf", "-", "-C", str(sdk.parent), sdk.name],
                           stdout=subprocess.PIPE)
    assert tar.stdout is not None
    try:
        zstd = subprocess.run(["zstd", "-T0", "-6", "-o", str(archive)],
                              stdin=tar.stdout, check=False)
    finally:
        tar.stdout.close()
    if tar.wait() != 0 or zstd.returncode != 0:
        raise RuntimeError("SDK archive creation failed")
    return hashlib.sha256(archive.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("c-root", "reference-sdk", "libcxx-headers", "libcxx-archive",
                 "libunwind-headers",
                 "corefoundation-tbd-override", "llvm-repo", "work"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--mode", choices=("restricted", "overlay"), required=True)
    parser.add_argument("--corefoundation-c-root", type=Path)
    parser.add_argument("--bazelrc", type=Path)
    args = parser.parse_args()
    paths = [args.c_root, args.reference_sdk, args.libcxx_headers,
             args.libunwind_headers,
             args.libcxx_archive, args.corefoundation_tbd_override,
             args.llvm_repo]
    if any(not path.exists() for path in paths):
        parser.error("one or more input paths do not exist")
    if args.corefoundation_c_root and not args.corefoundation_c_root.is_dir():
        parser.error("CoreFoundation C root does not exist")
    work = args.work.absolute()
    if work.exists():
        parser.error("work directory already exists")
    work.mkdir(parents=True)
    sdk = work / "MacOSX.sdk"
    command = [sys.executable, str(ROOT / "compose_sdk.py"),
               "--c-root", str(args.c_root.absolute()),
               "--reference-sdk", str(args.reference_sdk.absolute()),
               "--libcxx-headers", str(args.libcxx_headers.absolute()),
               "--libcxx-archive", str(args.libcxx_archive.absolute()),
               "--libunwind-headers", str(args.libunwind_headers.absolute()),
               "--corefoundation-tbd-override",
               str(args.corefoundation_tbd_override.absolute()),
               "--out", str(sdk)]
    if args.corefoundation_c_root:
        command.extend(("--corefoundation-c-root",
                        str(args.corefoundation_c_root.absolute())))
    if args.mode == "overlay":
        command.append("--overlay-reference")
    subprocess.run(command, check=True)
    archive = work / "MacOSX.sdk.tar.zst"
    digest = archive_sdk(sdk, archive)
    consumer = work / "consumer"
    consumer.mkdir()
    module = TEMPLATE.read_text().replace("@LLVM_REPO@", str(args.llvm_repo.resolve()))
    module = module.replace("@ARCHIVE@", str(archive)).replace("@SHA256@", digest)
    (consumer / "MODULE.bazel").write_text(module)
    print(f"archive={archive} sha256={digest}", flush=True)

    bazelrc = args.bazelrc or args.llvm_repo / ".bazelrc"
    linkopt = "external/llvm++osx+macos_sdk/sysroot/usr/lib/libc++_llvm23_full.a"
    for arch, platform in (("arm64", "macos_aarch64"),
                           ("x86_64", "macos_x86_64")):
        command = ["bazel", f"--bazelrc={bazelrc.absolute()}", "build",
                   "@llvm-project//llvm:llvm", "--config=remote",
                   f"--platforms=@llvm//platforms:{platform}",
                   f"--linkopt={linkopt}"]
        log = work / f"llvm-{arch}.log"
        with log.open("w") as stream:
            result = subprocess.run(command, cwd=consumer, stdout=stream,
                                    stderr=subprocess.STDOUT)
        print(f"{arch}: exit={result.returncode} log={log}", flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
