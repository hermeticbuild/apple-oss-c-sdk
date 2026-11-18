# Apple OSS macOS C headers (prototype)

This repository installs a minimal, standalone C header tree for macOS arm64
and x86_64 cross-compilation. Its normal output is exactly the 535 paths in
[`inputs/profiles/default-headers.txt`](inputs/profiles/default-headers.txt).
The installer reads pinned Apple OSS submodules and local derivations; it does
not read or copy headers from Xcode or Apple SDK Gen. Clang resource headers,
libc++, libunwind runtime headers, libraries, SDK metadata, TBDs, and framework
headers are outside this C installation.
The retained Apple OSS `libunwind` submodule supplies only
`mach-o/compact_unwind_encoding.h`, a Mach-O format header named by Zig's C
probe. The installer does not publish `unwind.h`, `libunwind.h`, or
`__libunwind_config.h`; those remain toolchain-owned.

The previous full 898-file installer, its 40 Apple OSS CoreFoundation headers,
and its source submodules are preserved at the local Git tag
`archive/full-c-installation-2026-11-17`. The active installer does not
generate those stashed headers. The checked-in SDK inventory and audit ledgers
remain available to revisit scope; they describe the earlier full snapshot
until regenerated against the current installation.

## Build and check

Run on macOS. Python 3, Perl, `unifdef`, `awk`, Bazel, and `/usr/bin/mig` are
allowed host bootstrap tools. The compiler and its resource headers come from
the same SHA256-verified LLVM 23.1.2 minimal prebuilt, never Homebrew or the
host compiler.

```sh
LLVM_REPO=/absolute/path/to/hermetic-llvm
LLVM_CLANG=$(python3 resolve_llvm_clang.py --llvm-repo "$LLVM_REPO")

git submodule update --init --recursive
python3 install_c.py --clang "$LLVM_CLANG" --out /tmp/apple-oss-c-headers
python3 check_c_profile.py --clang "$LLVM_CLANG" \
  --sysroot /tmp/apple-oss-c-headers
python3 tests/fenv_runtime.py  # arm64 macOS host only
python3 -m unittest discover -s tests -p 'test_*.py'
```

`install_c.py` checks the official Apple source install lists where available,
applies guarded derivations, runs system MIG for the 11 selected public user
headers on both architectures, and writes `header-provenance.json` with source
selection and SHA256 for every installed file. It fails if any selected path
is missing or an unselected path is installed. `check_c_profile.py` compiles
the 174 checked-in C roots individually and together for both architectures,
then compiles the semantic C fixtures. It uses `-nostdinc` with only the pinned
Clang resource directory and the generated C installation.

The roots in [`inputs/profiles/default-roots.txt`](inputs/profiles/default-roots.txt)
are derived from [Zig's macOS C probe](https://codeberg.org/ziglang/zig/src/commit/47ff97b60b1a8215d4d15bb5870ee14b178558b9/tools/macos-headers.c),
excluding Objective-C, unavailable SIMD/XPC, and `net/ipsec_offload.h`.
The 535-path manifest is the union of both target include closures, including
12 `xlocale` headers reached by the combined translation unit. The C probe
is a maintained scope test, not a promise of complete SDK API parity.

## SDK coverage audit

[`inputs/c-probe.c`](inputs/c-probe.c) is a wider reference probe.
`audit/probe_c_closure.py` compiles it against an explicit local Xcode SDK as a
path-only coverage oracle; no SDK header content enters the installer.
`audit/sdk_c_headers.py` inventories every SDK C header path and its recorded
include/omit/review decision. See [`audit/README.md`](audit/README.md) for the
current minimal-profile audit command and its pending review status.

## LLVM composition gate

`compose_sdk.py` combines the C installation with Apple SDK Gen metadata and
TBD link stubs, LLVM libc++ headers and archive, and pinned LLVM libunwind
headers. Those remain separate inputs. LLVM currently also needs a working
CoreFoundation framework header layer. Apple SDK Gen 27.0's generated
CoreFoundation umbrella fails a direct include on both targets because its
AudioToolbox dependency requests missing `ObjectiveC/ObjectiveC.h`.
For this local LLVM proof, pass the archived Apple OSS full installation as
`--corefoundation-c-root`; its CF headers are copied only into the composed
SDK and never into the standalone C installation. Repairing Apple SDK Gen's
framework closure would let that separate layer replace this temporary input.
`--framework-header CoreFoundation` selects SDK Gen's generated framework
headers for an explicit test; the composition manifest records their origin.

`validate_llvm.py --mode restricted` composes and archives the SDK, then builds
`@llvm-project//llvm:llvm` for both macOS targets with hermetic-llvm's Bazel
toolchains. It also requires a separately recorded CoreFoundation TBD
amendment. See `python3 validate_llvm.py --help` for the explicit input paths.
The LLVM gate does not imply that SDK Gen's generated framework headers work
without the temporary Apple OSS CF layer.

The installer emits `header-provenance.json` and `header-owners.json`. The
former records hashes and legacy audit provenance; the latter records the
single owner, exact pinned inputs, selection rule, and transformation for each
path. See [`recipes/README.md`](recipes/README.md) for the production graph.
The 2026-11-18 refactor retained all 535 installed header bytes and all 535
legacy provenance records byte for byte against the 2026-11-17 baseline. The
selected C profile passed 356/356 compiler probes.

This is a local qualification prototype. The source licenses, generated
declarations, SDK Gen TBD provenance, and redistribution rights need release
review; see [`LICENSING.md`](LICENSING.md).
