# Reviewing the libSystem stub locally

Use the verified LLVM bundle from the release lock. A comparison takes the
matching Apple SDK and a candidate install directory or two explicit TBD
files. Put the comparison outside any release package.

```sh
python3 -m tools.sdk_review.libsystem compare-libsystem --sdk macosx26.5 \
  --reference "$APPLE_SDK" --candidate "$PACKAGE" --llvm "$LLVM" --out "$WORK/diff"
python3 -m tools.sdk_review.libsystem backlog --work "$WORK"
python3 -m tools.sdk_review.libsystem explain-libsystem --work "$WORK" \
  --symbol getgroups --arch x86_64 --minimum 11.0 --profile darwin
```

A completed comparison or backlog exits zero by default. Pass `--check` to
require zero differences or zero open findings and stale decisions,
respectively. An input or tool error exits 2. The routine writes
`libsystem-diff.json` and the separate `llvm-readtapi-compare.txt` into the
comparison directory. Backlog writes `libsystem-backlog.json`. Explain also
accepts `--gap ID`, prints the matching findings, and supplies a paired-link
command template for macOS clients. Fill in the client object and, for a
file-only comparison, the corresponding sysroots. Keep the independently
compiled client object and actual link receipt with the investigation.

## Coverage

### Build a local candidate from probed clients

Start with the Apple OSS [component selection graph](../libsystem/component_graph.md).
For each client architecture run the header scanner and provider probe. The
example covers four roots under the default C profile.

```sh
make -f tools/libsystem/dyld-assembly.mk dyld-assembly SOURCE_ROOT="$SOURCE_ROOT" \
  LLVM="$LLVM" C_INSTALL="$C_INSTALL" WORK="$WORK/dyld-evidence"
python3 -m tools.libsystem.scan --llvm "$LLVM" --c-install "$C_INSTALL" \
  --arch "$ARCH" --minimum 11.0 --header stdio.h --header unistd.h \
  --header sys/stat.h --header math.h --out "$WORK/scan-$ARCH.json"
python3 -m tools.sdk_review.probe_runtime_providers --client-arch "$ARCH" \
  --scan "$WORK/scan-$ARCH.json" --observed-arch "$CACHE_ARCH" \
  --inspector "$(xcrun --find dyld_info)" --cache "$CACHE" \
  --dyld-evidence "$WORK/dyld-evidence" --out "$WORK/providers-$ARCH"
python3 -m tools.sdk_review.build_observed_libsystem --graph "$WORK/component-graph.json" \
  --arm64 "$WORK/providers-arm64" --x86_64 "$WORK/providers-x86_64" \
  --minimum 11.0 --out "$WORK/stubs"
```

Use the observed cache slice, such as arm64e for an arm64 client. Omit
`--cache` for the host's default cache. The provider probe retains local raw
observations and the exact sources of client demands. The candidate retains
only supported client demands with unambiguous providers; inspect
`local-review.json` for omissions and the scope of the scans. A function
exported through a dynamic resolver remains callable under its public symbol.
The LLVM reader preserves export role and weakness independently of the
resolver address. [LLVM's Mach-O reader](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/llvm/lib/TextAPI/BinaryReader/DylibReader.cpp#L248-L277)

Compile [the smoke client](libsystem_fixtures/client.c) against the C
installation. Use that exact object on both sides of the comparison.

```sh
"$LLVM/bin/clang" --no-default-config -target "$ARCH-apple-macos11" \
  -nostdinc -isysroot "$C_INSTALL" -isystem "$("$LLVM/bin/clang" -print-resource-dir)/include" \
  -isystem "$C_INSTALL/usr/include" -c tools/sdk_review/libsystem_fixtures/client.c -o "$WORK/client-$ARCH.o"
python3 -m tools.sdk_review.verify_libsystem_links --llvm "$LLVM" --reference "$APPLE_SDK" \
  --candidate "$WORK/stubs" --arch "$ARCH" --minimum 11.0 --sdk-version 26.5 \
  --object "$WORK/client-$ARCH.o" --out "$WORK/paired-$ARCH.json"
```

The differential link checks the bind-through name, weakness, load commands
and platform metadata. Run a separate executable link when qualifying the
runtime. Keep raw observations and partial candidates in the local review
directory. The release builder requires independently reviewed, locked inputs.

For a wider inventory supply a completed `scan_roots` directory to the
provider probe using `--matrix`. Repeat for each profile. The probe checks
each compressed checkpoint against its summary digest and input identity and
preserves failed contexts in `root_findings`.

### What the SDK comparator checks

- Raw keys are the install name, exact architecture and platform label, and
  symbol encoding and spelling. Both the main document and all children are
  read, including slices absent from the main document. The report enumerates
  document and slice coverage. It compares symbol roles, weakness, TLS,
  Objective-C encodings, literal linker directives, image metadata, library
  reexport edges, and changes in exact-target reachable providers.
- The reader supports canonical TBD v4 and JSON TBD v5 with
  arm64, arm64e, x86_64, and x86_64h macOS and Mac Catalyst labels. Unsupported
  fields and layouts fail with an error. V4 requires flow-style target lists
  and omits text/data classification from comparisons involving v4. Use
  directory inputs on both sides to compare the filesystem alias.
- V4 normalization projects each document to its own raw target before the
  official `llvm-readtapi` extraction. LLVM's interface model can combine
  symbols with different flags before ordinary architecture extraction.
  Conversion uses the flat-namespace serialization path to carry v4
  undefined-symbol rows, then restores the actual flag in the normalized
  result. The separate whole-stub comparison uses the unchanged input bytes.
  [LLVM v4 mapping](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/llvm/lib/TextAPI/TextStub.cpp)
  · [LLVM v5 mapping](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/llvm/lib/TextAPI/TextStubV5.cpp)
- Effective deployment, linker directives, and client bind-through behavior
  require actual client links. Use the same compiled object on both sides.
  The exact-target raw report does not resolve external reexports from disk
  or simulate architecture fallback.

## Review decisions

The optional `backlog --decisions FILE` ledger is JSON with `schema: 1`,
`sdk`, `reference_sha256`, and a `decisions` array. Each decision has an
`id`, nonempty `members` array of stable gap IDs, `member_sha256`,
`evidence`, `impact`, `approver`, and `revisit`. The member digest is
SHA-256 over the chosen findings sorted by ID and encoded as compact JSON
with sorted object keys. Explain prints that digest for its selection.
A changed SDK, reference hash, member list, or member finding reopens the
decision. New findings outside its exact member list are open. The ledger
is a maintainer input. Comparison and backlog never write to it.

Run the synthetic suite with the verified reader:

```sh
LIBSYSTEM_TEST_LLVM="$LLVM" python3 -m unittest tools.sdk_review.test_libsystem
```
