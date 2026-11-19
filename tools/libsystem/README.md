# libSystem tools

Start by preparing the [official LLVM bundle](../toolchain/README.md). Set `LLVM` to its verified directory and run the following from the repository root. Fixture names and records are independently authored. The first runnable build lock targets the fixture; the macOS 26.5 production lock and reviewed component evidence are pending.

```sh
fixture=tools/libsystem/fixtures/interface
work=$(mktemp -d)
python3 -m tools.libsystem build --llvm "$LLVM" --lock "$fixture/release.json" \
  --c-install "$fixture" --out "$work/package"
make -C tools/libsystem check-interface LLVM="$LLVM"
```

A build checks the official toolchain projection, the install manifest and every declared header digest. The fixture lock names public roots and pins component evidence by SHA-256. A component record includes its install name, dylib versions, edges and exports by architecture. The build scans each selected C root, resolves every eligible imported symbol to a reachable component with the required kind and emits an embedded-library TBD plus its relative alias. It also writes `manifest.json` and `providers.json`. A new output directory appears only after success.

The current resolver supports ordinary functions, data, weak definitions, TLS objects, symbol reexports and whole-library reexports. It rejects conflicting providers and unfamiliar evidence fields. This fixture build demonstrates the interface contract. A production release additionally needs source-based selection of public exports, coverage of non-header demands, approved deployment directives, complete target/profile qualification and reviewed provenance.

For macOS 26.5 the offline producer keeps three Apple Libc declarations out of the link interface. It verifies the SDK identity, source revision, installed header receipt and exact symbol names before exempting them from provider resolution. A provider record that exports one of those names fails the build and reopens review. The output manifest records the applied policy. [Reviewed exceptions](data/macosx26.5/expected-undefined.json) · [Reference qualification](../sdk_review/sdk_header_linkage.md)

A 26.5 release lock can set `libc_alias_source` to a relative directory containing the pinned Libc project inputs. The producer verifies `xcodescripts/libc.xcconfig` and `xcodescripts/alias.list`, then emits the public names in the libsystem_c symbol reexports for both targets. The provider receipt keeps the forwarded implementation name and image. The local runtime probes take `--libc-source` to check the same mapping on each deployed slice. [Apple's linker rule](https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/xcodescripts/libc.xcconfig#L85) · [Apple's 22 aliases](https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/xcodescripts/alias.list)

Use `libc_source` instead of the alias-only lock field to include the compiler's stack-protector ABI. The source tree must also contain `sys/OpenBSD/stack_protector.c` and `Libc.xcodeproj/project.pbxproj`. The offline build verifies both files and compiles a protected stack frame at O0 and O2 on each architecture. The receipt records the object hashes and the imported function and data names. [Apple implementation](https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/sys/OpenBSD/stack_protector.c) · [Compiler fixture](fixtures/stack_protector.c)

## Extract macOS deployment directives

Use the macOS 26.5 locked source tree and a C header installation.

```sh
python3 -m tools.libsystem.directives --llvm "$LLVM" --source-root "$SOURCE_ROOT" \
  --c-install "$C_INSTALL" --out "$work/directives.json"
```

The extractor verifies the LLVM projection, the three Apple OSS input
digests, and the installed `TargetConditionals.h` receipt. It compiles
`Libc/darwin/compatibility_hacks.c` directly. For libdispatch it compiles the
macro and macOS switch from `src/internal.h` with their invocations from
`src/init.c`. The compiler takes headers from the C installation and its
pinned resource directory. Both target objects are read with `llvm-nm`; the
extractor does not take an Apple SDK or cache path.
[Pinned Libc](https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/darwin/compatibility_hacks.c) ·
[Pinned libdispatch macro](https://github.com/apple-oss-distributions/libdispatch/blob/701f4d1a24ae9c6863901bbbb22624b7d1b87321/src/internal.h) ·
[Pinned libdispatch invocations](https://github.com/apple-oss-distributions/libdispatch/blob/701f4d1a24ae9c6863901bbbb22624b7d1b87321/src/init.c)

Schema 1 records the SDK, source SHA-256 values, toolchain lock SHA-256, and
the installed target header SHA-256. Each row records the generated target
`arm64-macos` or `x86_64-macos`, provider install name, complete directive
`name`, `kind`, exact `deployment` selector from the directive, and
affected Mach-O `symbol`. The rows describe static linker pseudo-symbols.
The production resolver can consume the receipt separately from ordinary
runtime export evidence.

| Provider | Kind | Exact selector | Mach-O symbols on each target |
| --- | --- | --- | --- |
| `/usr/lib/system/libsystem_c.dylib` | `weak` | 10.11 | `_basename_r`, `_clock_getres`, `_clock_gettime`, `_clock_settime`, `_dirname_r`, `_getentropy`, `_mkostemp`, `_mkostemps`, `_timingsafe_bcmp` |
| `/usr/lib/system/libsystem_c.dylib` | `weak` | 10.12 | `_utimensat` |
| `/usr/lib/system/libdispatch.dylib` | `hide` | 10.12 | `_dispatch_assert_queue`, `_dispatch_assert_queue_not`, `_dispatch_queue_create_with_target` |

Separate local review against macOS 26.5 SDK build 25F70 matched all ten
Libc and all three libdispatch names, with no additional directive names
in either provider on the two sampled SDK slices. The reference stores
both child libraries under `arm64e-macos` and `x86_64-macos`. Two
extractions with LLVM 23.1.2 produced byte-identical receipts.

Both deployment selector values precede the 11.0 deployment floor of the
production package. In reference links at x86_64 macOS 10.12,
`_dispatch_queue_create_with_target` was hidden with both pinned LLD and
Xcode 26.5's linker. The same reference bound the symbol at 10.13.
`_getentropy` imported strongly in the 10.11 and 10.12 reference probes
using an explicit strong object reference. LLD 23.1.2 handles `hide`
by exact selector equality and has no `weak` directive handler. Keep
the source-backed `weak` names as recorded policy without inferring client
weakness, introduction dates, or old-runtime availability from them.
Compiler-rt directives and non-macOS targets remain separate work.
[Pinned LLD directive handler](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/lld/MachO/InputFiles.cpp)

## Investigate one header or import

```sh
python3 -m tools.qualify_headers.census --clang "$LLVM/bin/clang" \
  --c-install "$C_INSTALL" --minimum 11.0 --header sys/stat.h --out "$work/census.json"
python3 -m tools.libsystem.scan --llvm "$LLVM" --c-install "$C_INSTALL" \
  --arch x86_64 --minimum 11.0 --header sys/stat.h --out "$work/stat.json" \
  --objects "$work/stat-objects"
python3 -m tools.libsystem.compiler_imports --llvm "$LLVM" --minimum 11.0 --out "$work/division"
```

The census records the public root, full command, diagnostics and entered sysroot headers. Omit `--header` to enumerate the install manifest. A context file can specify `root`, `before`, `language` or `defines` per manifest path and architecture. The scanner records object-backed imports and unresolved cases. The compiler fixture produces four Mach-O objects and an import inventory, usable by the paired verifier.

For a local provider question, name the image, actual slice and requested symbol. The resulting directory contains raw macOS evidence and belongs outside the release inputs.

```sh
python3 -m tools.libsystem.capture --inspector "$(xcrun --find dyld_info)" \
  --arch arm64e --image /usr/lib/system/libsystem_kernel.dylib \
  --symbol _getgroups --out "$work/kernel"
```

For x86_64 on Apple Silicon, pass the installed x86_64 cache using `--cache`. The receipt records the image UUID and the OS build of the capture host.

## Compare and link

Follow the [raw target comparison and backlog guide](../sdk_review/libsystem_review.md). To compare effective linker behavior, use the same client object for both sysroots:

```sh
python3 -m tools.sdk_review.verify_libsystem_links --llvm "$LLVM" \
  --reference "$APPLE_SDK" --candidate "$CANDIDATE" --arch x86_64 \
  --minimum 11.0 --sdk-version 26.5 --object "$work/division/x86_64-O0.o" \
  --out "$work/links.json"
```

The verifier records traced inputs, load commands and undefined imports with their bind-through library. Pass `--expect-undefined SYMBOL` for a deliberate negative link. Pass `--builtins ARCHIVE` only for fixtures that need that explicit static runtime on both sides. Unexpected differences exit 1. Invalid inputs or linker setup failures exit 2. The fixture suite also checks a successful link through the wrong provider.

See the [implementation journal](progress.md) for the latest qualified milestone, and the [specification](../sdk_composition/libsystem-spec.md) for outstanding release gates.

## Review a freshly installed header set

Start with a version-locked installation and the reference SDK with the same name and build. Run from the repository root with a fresh report directory. The tools use Python 3.10+ syntax. Set `PYTHON` on the Make command line if `python3` selects an older interpreter.

```sh
WORK=$(mktemp -d)
make -f tools/sdk_review/libsystem-headers.mk -j3 header-backlog \
  SDK=macosx26.5 LLVM="$LLVM" C_INSTALL="$C_INSTALL" APPLE_SDK="$APPLE_SDK" WORK="$WORK"
```

This runs the standalone census, shipping and discovery include traces, SDK path audit, and [paired semantic probes](../sdk_review/c_interface_review.md). Read `header-backlog.json` for path decisions, failed contexts, matched approvals and semantic differences. The two `discovery-*.json` files also preserve diagnostics for optional roots outside the shipping profile. A completed backlog with open findings deliberately fails the Make target. The underlying `tools.sdk_review.header_backlog` command exits 1 for findings and 2 for invalid inputs. A stale or missing input remains an explicit issue.

The [eventlink decision](../sdk_review/data/macosx26.5/standalone-context-approvals.json) applies to two specific standalone include contexts. Reproduce it with the reference SDK attached. Review the header's linker exports independently.

To run the [C11 complex constructor fixture](../../tests/installed_headers/complex_abi.c), use the same Make invocation with `complex-runtime` as the target. Compilation uses only the generated headers and Clang resource headers. The linker reads the reference libSystem stub. Running both executables on an Apple Silicon Mac requires Rosetta for the Intel executable. These tests exercise the host runtime on the installed OS build.

## Compose an integration sysroot

Supply the standalone C installation, generated libSystem package and its independently recorded manifest digest. Select each SDK Gen framework and additional link stub explicitly.

```sh
python3 -m tools.sdk_composition.compose_libsystem \
  --c-install "$C_INSTALL" --libsystem "$PACKAGE" --llvm "$LLVM" \
  --libsystem-manifest-sha256 "$PACKAGE_MANIFEST_SHA256" \
  --sdk-gen "$SDK_GEN" --framework CoreFoundation \
  --out "$WORK/composed.sdk"
```

The composer rejects additional providers of install names already supplied by libSystem. Its `composition.json` traces files and dylib providers to their layers. For a C++ workload, supply the Apple libc++ link stub and any alias via separate `--external-stub DESTINATION=SOURCE` arguments. The consumer toolchain supplies C++ headers.
