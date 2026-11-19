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

The current resolver supports ordinary functions, data, weak definitions, TLS objects and whole-library reexports. It rejects conflicting providers and unfamiliar evidence fields. This fixture build demonstrates the interface contract. A production release additionally needs source-based selection of public exports, coverage of non-header demands, approved deployment directives, complete target/profile qualification and reviewed provenance.

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

Start with a version-locked installation and the reference SDK with the same name and build. Run from the repository root with a fresh report directory.

```sh
WORK=$(mktemp -d)
make -f tools/sdk_review/libsystem-headers.mk -j3 header-backlog \
  SDK=macosx26.5 LLVM="$LLVM" C_INSTALL="$C_INSTALL" APPLE_SDK="$APPLE_SDK" WORK="$WORK"
```

This runs the standalone census, shipping and discovery include traces, SDK path audit, and [paired semantic probes](../sdk_review/c_interface_review.md). Read `header-backlog.json` for path decisions, failed contexts, matched approvals and semantic differences. The two `discovery-*.json` files also preserve diagnostics for optional roots outside the shipping profile. A completed backlog with open findings deliberately fails the Make target. The underlying `tools.sdk_review.header_backlog` command exits 1 for findings and 2 for invalid inputs. A stale or missing input remains an explicit issue.

The [eventlink decision](../sdk_review/data/macosx26.5/standalone-context-approvals.json) applies to two specific standalone include contexts. Reproduce it with the reference SDK attached. Review the header's linker exports independently.

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
