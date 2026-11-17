# Apple OSS macOS C headers (prototype)

Pinned Apple open-source inputs and a standalone macOS C-header installer for
arm64 and x86_64. `install_c.py` reads no Apple SDK or Apple SDK Gen headers.
Its only compiler-provided headers come from the selected Clang resource
directory; they are not copied into the installation.

## Build the C installation

```sh
git submodule update --init --recursive
cd tools/apple_mig && bazel build //:mig --config=remote && cd ../..
python3 install_c.py --mig tools/apple_mig/bazel-bin/mig --out /tmp/apple-oss-c-headers
python3 check_c_headers.py --sysroot /tmp/apple-oss-c-headers
python3 tests/fenv_runtime.py  # arm64 macOS host only
```

Requires Python 3, Perl, `unifdef`, `awk`, Clang, and Bazel. The installed tree
contains `usr/include` and the open-source CoreFoundation framework headers.
It does not contain Clang resource headers, libc++ headers, libraries, TBDs, or
SDK metadata. `check_c_headers.py` uses `-nostdinc`, then names only Clang's
resource directory and this installation; it checks both target architectures.

`inputs/header-sources.tsv` maps 161 installed header paths to pinned Apple
source or an Apple generation path. Other closure candidates come from the
explicit source groups and trees in `install_c.py`. Libc headers use
`Libc/xcodescripts/headers.sh`'s `strip-header.ed` and `unifdef` flags from
`generate_features.pl`. Availability headers use the pinned AvailabilityVersions
preprocessor. XNU's `make_symbol_aliasing.sh`, `make_posix_availability.sh`,
public `SINCFRAME_UNIFDEF` settings, and `mach_install_mig.sh`/`osfmk/mach/Makefile`
drive the generated sys and MIG headers. Both architecture-specific MIG runs
must produce identical public header bytes before installation.

## Local compatibility derivations

- `TargetConditionals.h`: CarbonHeaders' macOS template, with its Makefile's
  macOS substitutions, arm64 CPU detection, and modern macOS target aliases.
  The pinned Apple OSS template predates arm64. CF's same-named source header
  explicitly targets Linux and is unsuitable here.
- arm64 `fenv.h`: Libm's C API and XNU's FPSR/FPCR bits, with the 16-byte
  two-register layout checked against macOS libSystem at runtime. This is a
  local ABI declaration, not an Apple-published arm64 Libm header.
- `sandbox.h`: a small handwritten public C declaration set. No matching
  Apple OSS source header was located. This remains a provenance gap.
- Libm `complex.h` and `math.h`: add arm64 architecture branches to their
  pinned Apple OSS sources. dyld `mach-o/dyld.h` gets a default
  `DYLD_EXCLAVEKIT_UNAVAILABLE` macro required by the pinned source.
- AvailabilityInternal adds `xros` API macro aliases: its pinned DSL declares
  `cmd_aliases=xros`, but the preprocessor omits the API spelling used by the
  pinned libdispatch header.

These derivations are in `install_c.py` and `templates/`, with guarded source
matches so an upstream change cannot silently alter the output.

## LLVM composition proof

`compose_sdk.py` combines the C installation with only SDK Gen metadata and
TBD files, plus hermetic-llvm libc++ headers and a supplemental libc++ archive.
It copies no SDK Gen `usr/include` headers. Non-C framework headers require an
explicit `--framework-header` argument. The generated composition manifest
records every non-C file copied from the reference SDK.

`validate_llvm.py` packages either the restricted composition or the full
SDK Gen overlay and builds `@llvm-project//llvm:llvm` for both macOS targets.
It accepts the SDK Gen tree, LLVM libc++ inputs, and any TBD amendment as
explicit external paths; no SDK-derived TBD is stored in this repository.

Local qualification on 2026-11-17: 118/118 isolated C header probes passed;
the C smoke compiled to both Mach-O architectures with no SDK header in either
dependency file. LLVM 23.1.2 built for arm64 and x86_64 using the restricted
composition (419 TBDs, no SDK Gen headers); both binaries ran. Repeating both
builds with the C installation overlaid on the full SDK Gen tree also passed.
The restricted composition contains no headers beyond this C installation and
LLVM's libc++ headers. The path audit found 860 shared `usr/include` C paths,
795 byte-identical and 65 different, plus `float.h` and `tgmath.h` supplied by
Clang. These counts do not establish semantic parity.

TBD audit: the reference SDK has 419 `.tbd` files. Hermetic LLVM's default
`extensions/osx.bzl` include patterns select 17 `usr/lib` TBDs and five
framework TBDs from the restricted composition. No non-CoreFoundation
framework headers enter that composition. The inspected x86_64 LLVM link
action requests Foundation, CoreFoundation, `-lc++`, `-lm`, `-pthread`, and
`-ldl`, plus the LLVM 23 archive. Its Mach-O load commands name Foundation,
CoreFoundation, libSystem, libc++, libm, and libdl. The 22 selected TBDs are
the toolchain's available link surface; the six load commands are the direct
dependencies of this particular LLVM binary.

This composition is for local validation only. SDK Gen's TBD export provenance
and redistribution rights are outside this C-header recipe. The
`CoreFoundation.tbd` amendment is also a separately recorded link asset, not
part of the standalone C installation.
See [LICENSING.md](LICENSING.md) for the preliminary source and terms review.
The LLVM binaries currently load `/usr/lib/libc++.1.dylib`; the LLVM 23 archive
supplements it at link time. Hermetic LLVM's existing `libcxx.shared` target
currently cannot supply a macOS dylib: with duplicate libc++ headers removed
from the runtime build sysroot, its compile succeeds but `ld64.lld` rejects the
target's Linux-only `-soname` linker flag. This is a separate runtime gap; no
hermetic-llvm source change is included here.

## Current limits

The source-tree closure remains deliberately broad while LLVM qualification is
in progress; it includes private Apple OSS headers that should be excluded by
the projects' public installation manifests before release. A path comparison
against SDK Gen is only a path check: SDK Gen emits per-symbol CoreFoundation
headers, while this recipe installs Apple's 39 umbrella headers. It does not
establish equivalent API coverage. The `sandbox.h`, arm64 `fenv.h`, and modern
`TargetConditionals.h` derivations require upstream or ABI review before
distribution.
