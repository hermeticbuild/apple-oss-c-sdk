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
