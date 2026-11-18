# Apple OSS macOS C headers (prototype)

This repository installs a minimal, standalone C header tree for macOS arm64
and x86_64 cross-compilation. Its normal output is exactly the 535 paths in
[`recipes/default-headers.txt`](recipes/default-headers.txt).
The installer reads pinned Apple OSS submodules and local derivations; it does
not read or copy headers from Xcode or Apple SDK Gen. Clang resource headers,
libc++, libunwind runtime headers, libraries, SDK metadata, TBDs, and framework
headers are outside this C installation.
The retained Apple OSS `libunwind` submodule supplies only
`mach-o/compact_unwind_encoding.h`, a Mach-O format header named by Zig's C
probe. The installer does not publish `unwind.h`, `libunwind.h`, or
`__libunwind_config.h`; those remain toolchain-owned.

## Generate the C installation

Run from the repository root on macOS. The installer uses Python 3, Perl,
`unifdef`, `awk`, system MIG, and Clang. Supply the pinned LLVM 23.1.2 minimal
prebuilt Clang. The resolver command below uses hermetic-llvm and Bazel.

```sh
LLVM_REPO=/absolute/path/to/hermetic-llvm
LLVM_CLANG=$(python3 -m tools.qualification.resolve_llvm_clang --llvm-repo "$LLVM_REPO")

git submodule update --init --recursive
python3 install_c.py --clang "$LLVM_CLANG" --out /tmp/apple-oss-c-headers
```

The output directory must be new. The installer checks Apple source install
lists where available, applies the recipes, and compares MIG output across both
targets. It emits `header-provenance.json` with source selections and hashes and
`header-owners.json` with each header's producer, inputs, and transformation.
See [the recipes](recipes/README.md) for the production steps.

## Tools

- [SDK coverage audit](tools/audit/README.md) contains the SDK inventory,
  include/omit decisions, and reference probes.
- [Qualification and LLVM composition](tools/qualification/README.md) contains
  the C checks and the two macOS LLVM builds.

This is a local qualification prototype. See [licensing](LICENSING.md) for
outstanding redistribution questions.
