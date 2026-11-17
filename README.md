# Apple OSS macOS C headers (prototype)

Pinned Apple open-source inputs and a standalone macOS C-header installer for
arm64 and x86_64. `install_c.py` reads no Apple SDK or Apple SDK Gen headers.
Its only compiler-provided headers come from the selected Clang resource
directory; they are not copied into the installation.

## Build the C installation

This qualification runs on macOS. The installer defaults to the system
`/usr/bin/mig`; an explicit `--mig` path is available for other hosts but is
not qualified here.

```sh
LLVM_REPO=/absolute/path/to/hermetic-llvm
LLVM_CLANG=$(python3 resolve_llvm_clang.py --llvm-repo "$LLVM_REPO")

git submodule update --init --recursive
python3 install_c.py --clang "$LLVM_CLANG" --out /tmp/apple-oss-c-headers
python3 check_c_headers.py --clang "$LLVM_CLANG" --sysroot /tmp/apple-oss-c-headers
python3 tests/fenv_runtime.py  # arm64 macOS host only
```

Clang and its resource headers come from the same SHA256-verified `@llvm`
minimal prebuilt. `resolve_llvm_clang.py` checks hermetic-llvm's index against
`inputs/llvm-minimal-prebuilt.json` before fetching LLVM 23.1.2 release 2.
Keep the `bin/clang` symlink name: the prebuilt is a multicall executable.
Python 3, Perl, `unifdef`, `awk`, Bazel, and macOS `/usr/bin/mig` are allowed
host bootstrap tools. System `mig` receives `-cc "$LLVM_CLANG"`, so it uses
the pinned prebuilt as its C preprocessor. No host compiler or Homebrew headers
are inputs. The installed tree contains
`usr/include` and the open-source CoreFoundation framework headers.
It also contains `header-provenance.json`, recording each installed file's
pinned source selection and SHA256. The C-only recipe omits Objective-C headers.
It does not contain Clang resource headers, libc++ headers, libraries, TBDs, or
SDK metadata. `check_c_headers.py` uses `-nostdinc`, then names only Clang's
resource directory and this installation; it checks both target architectures.

## C coverage reference

`inputs/c-probe.c` is the checked-in, extensible translation unit, seeded
from [Zig's `tools/macos-headers.c`](https://codeberg.org/ziglang/zig/src/commit/6b0a1d8b426a9b60f999358d4b7f57aa0b231777/tools/macos-headers.c).
Its 179 roots are grouped by their first matching inventory: 27 of 29
[ISO C11 standard headers](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)
(including all 15 [ANSI C89 / ISO C90](https://www.iso.org/standard/17782.html)
headers), 55 additional
[POSIX.1-2017 Issue 7 headers](https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/contents.html),
and 97 macOS/BSD, framework, or other extension headers. Counting the 24
C11/POSIX overlaps, the probe covers 79 of the 82 POSIX header entries.
The five unseeded standard roots (`threads.h`, `uchar.h`, `mqueue.h`,
`stropts.h`, `trace.h`) are absent from the macOS 26.5 SDK reference. These
are header-name coverage counts, not claims of API or standards conformance.
Newer standard editions are outside this inventory.
The probe also records its Zig seed differences: five `objc/*` roots are
outside its C-only scope, and `net/ipsec_offload.h` is absent from the SDK;
`sandbox.h`, `TargetConditionals.h`, and `CoreFoundation/CoreFoundation.h` are
added. See `COVERAGE_GAPS.md` for included roots that our installation still
lacks.
The reference run requires an explicit, locally installed macOS SDK, used only
to observe header paths and compile the probes. No SDK file is copied into the
C installation.

```sh
python3 probe_c_closure.py --clang "$LLVM_CLANG" \
  --sysroot /absolute/path/to/MacOSX26.5.sdk \
  --out /tmp/apple-c-reference-26.5.json
python3 probe_c_closure.py --clang "$LLVM_CLANG" \
  --sysroot /tmp/apple-oss-c-headers \
  --reference /tmp/apple-c-reference-26.5.json \
  --out /tmp/apple-c-generated-26.5.json
```

The probe compiles that single C file and then each include independently for
arm64 and x86_64 with only the
minimal prebuilt's resource headers and the chosen sysroot on the include
path. Its manifest records compiler and resource-header hashes, SDK version
when available, actual include closure from Clang `-H`, and dependency-only
lookup candidates from `-MD`. The latter can include a header queried by
`__has_include_next` without actually opening it. Comparison requires every
actual SDK header path to exist in our installation, plus a successful compile
of the combined file and every root. The combined run reached 12 `xlocale/*`
headers that the independent runs did not. Resource headers stay compiler-owned. The local reference
manifest is validation evidence, not a generation input.

## Full SDK C-header inventory

Run this read-only path audit periodically with the same pinned Clang and a
freshly built C installation:

```sh
python3 audit_sdk_c_headers.py --clang "$LLVM_CLANG" \
  --sdk /absolute/path/to/MacOSX26.5.sdk \
  --installation /tmp/apple-oss-c-headers \
  --reference /tmp/apple-c-reference-26.5.json \
  --generated-probe /tmp/apple-c-generated-26.5.json \
  --baseline inventories/macosx26.5.json \
  --out inventories/macosx26.5.json \
  --review-out inventories/macosx26.5-review.md
```

The checked-in `inventories/macosx26.5.json` is a versioned path database of
every file entry under SDK `usr/include`. Each path records whether it is
installed, absent, or outside this C-header scope, plus an `include`, `omit`,
or `review` proposed disposition, its source, approval status, evidence, and
reason. `include` means retain in
this installation; it does not assert that every consumer needs the header.
The script excludes `c++/`, `objc/`,
non-`.h` files, and symlinks into frameworks from C-installation candidates;
their paths and reasons remain visible in the database. Reviewed directory
rules in `inputs/sdk-header-decisions.tsv` omit bundled libraries and SDK
module shims from the core C installation. A rule has an SDK-specific review
stamp, evidence, and a hash of its reviewed path set. Scope exclusions have
the same protection in `inputs/sdk-scope-approvals.tsv`. A newly added or
removed member invalidates the approval even after the inventory is updated.
`--baseline` also reports added and removed SDK paths. The current 26.5
snapshot has 482 pending approvals: 205 installed paths outside the probe
closure whose need/scope is unsettled, plus 277 absent candidates. The other
532 installed SDK paths are reached by the probe and have verified installer
provenance. Another 28 probe-required paths are absent from the
installation. The reverse audit also finds 342 installed C headers without a
matching 26.5 SDK path. Five are reached by the generated C probe; the other
337 remain pending, including headers from broad XNU source-tree walks.
`--require-decisions` requires a baseline and both probe manifests, then
fails on pending approvals, missing required paths, unexplained removals,
unreviewed installation-only headers, or out-of-scope installed paths. The checked-in
`inventories/macosx26.5-review.md` groups pending paths for human review.

The report flags Clang resource overlaps and `#include_next` use; it never
silently treats a compiler overlap as installed. An optional `--reference`
marks paths reached by the C probe or queried during preprocessing, after
checking the SDK version. Directory totals help prioritize review. The
snapshot records paths and counts, never SDK header contents. Re-run it for
each SDK version and review the diff; a path's presence alone does not prove
that it is needed or that its contents are licensed for redistribution.
Compilation and API behavior remain the job of the C probe and LLVM build.

`inputs/header-sources.tsv` maps 162 installed header paths to pinned Apple
source or an Apple generation path. Other closure candidates come from the
explicit source groups and trees in `install_c.py`. Libc headers use
`Libc/xcodescripts/headers.sh`'s `strip-header.ed` and `unifdef` flags from
`generate_features.pl`. Availability headers use the pinned AvailabilityVersions
preprocessor. XNU's `make_symbol_aliasing.sh`, `make_posix_availability.sh`,
public `SINCFRAME_UNIFDEF` settings, and `mach_install_mig.sh`/`osfmk/mach/Makefile`
drive the generated sys and MIG headers. Both architecture-specific MIG runs
must produce identical public header bytes before installation.
The expanded coverage uses XNU's public `DATAFILES`/`INSTALL_MI_LIST` for
`device/`, `libkern/`, and `net/`; cctools' public Xcode header phase for
`mach-o/`; hfs' public header phase; launchd's public `launch.h`; and
libunwind's open-source compact-unwind header. The pinned XNU
`osfmk/device/Makefile` calls for `-DIOKIT` when installing
`device_types.h`, which the installer applies. Swift CoreFoundation is pinned
only to investigate a modern header gap; it supplies no installed header.
The macOS system `mig` (`bootstrap_cmds-138` in this qualification) generated
32 Mach headers byte-identical to the previous `apple_mig` output.

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
  The pinned dyld `mach-o/dyld_images.h` omits includes for its `uintptr_t`
  and `mach_port_t` uses; add `stdint.h` and `mach/mach.h`.
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
Clang when comparing with SDK Gen. These counts do not establish semantic parity.

Expanded qualification with the pinned LLVM minimal prebuilt and official
macOS 26.5 SDK: 360/360 reference C probes compile. The current generated C
installation compiles 354/360; the combined probe stops at SIMD and the
individual SIMD and XPC roots fail on both
architectures. The reference include closure has 35 distinct header paths
absent from the standalone installation; see [COVERAGE_GAPS.md](COVERAGE_GAPS.md).
After the Apple OSS header additions, the restricted SDK Gen composition
again built LLVM 23.1.2 for arm64 and x86_64. Both Mach-O binaries ran
`readelf --version` successfully. The prebuilt compiler and its resource
headers were used for the C installation and all probes.

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
The broader C coverage probe also has the explicit unresolved paths in
[COVERAGE_GAPS.md](COVERAGE_GAPS.md); passing LLVM does not close them.
