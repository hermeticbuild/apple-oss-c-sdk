# SDK coverage review

Run this workflow when qualifying a new SDK version, updating Apple OSS pins,
or investigating a scope gap. It reads the SDK and the generated installation
and writes review reports. The Make installer has no dependency on the SDK
or these ledgers.

## Compare coverage with an official SDK

Set `LLVM_CLANG` to the pinned Clang, `SDK` to the reference macOS SDK, and
`C_INSTALL` to the generated installation. Run from the repository root.

```sh
python3 -m tools.qualify_headers.trace_includes --probe tools/qualify_headers/fixtures/default_profile.c \
  --clang "$LLVM_CLANG" --sysroot "$SDK" \
  --out /tmp/sdk-reference.json
python3 -m tools.qualify_headers.trace_includes --probe tools/qualify_headers/fixtures/default_profile.c \
  --clang "$LLVM_CLANG" --sysroot "$C_INSTALL" \
  --out /tmp/c-install-closure.json
python3 -m tools.sdk_review.audit_sdk_headers \
  --sdk "$SDK" --installation "$C_INSTALL" --clang "$LLVM_CLANG" \
  --reference /tmp/sdk-reference.json --generated-probe /tmp/c-install-closure.json \
  --baseline tools/sdk_review/inventories/macosx26.5.json \
  --out /tmp/sdk-audit.json --review-out /tmp/sdk-review.md
```

The commands above compare the shipping probe. For broader discovery, omit
`--probe` in both trace commands to use the default discovery fixture.
`audit_sdk_headers.py` inventories the full SDK `usr/include` even when a path
is outside the probe. Review new paths, unresolved source gaps, and decisions
that no longer match the SDK. Add `--require-decisions` when every decision must
be resolved. Preserve earlier inventories as baselines. The checked-in 26.5
inventory is a historical full-profile snapshot.

| Input | Meaning |
| --- | --- |
| [Header decisions](data/sdk-header-decisions.tsv) | Pattern, include or omit decision, reason, evidence, SDK name, and digest of the approved matching paths |
| [Review notes](data/sdk-review-notes.tsv) | Outstanding source gaps |
| [Scope approvals](data/sdk-scope-approvals.tsv) | Approved sets outside the package scope |
| [Installation-only decisions](data/installation-only-decisions.tsv) | Reviewed generated paths absent from the SDK |
Installed headers record their current source selections in the generated
manifest. See the [recipe documentation](../../recipes/README.md).

### Outstanding discovery coverage

The 26.5 discovery trace reached 16 `simd/*` and 11 `xpc/*` paths whose
first-party public source and install rules were unlocated in the earlier
Apple OSS review. Its
[macOS distribution submodule list](https://github.com/apple-oss-distributions/distribution-macOS/blob/main/.gitmodules)
provided no standalone SIMD or XPC component. Use the discovery trace for the
exact paths. Clang's resource `tgmath.h` fallback makes the shipping probe
compile. SDK `tgmath.h` API parity remains open.

The broad trace also found seven CoreFoundation framework gaps outside the
`usr/include` inventory. They are `CFAttributedString.h`, `CFCGTypes.h`,
`CFFileDescriptor.h`, `CFFileSecurity.h`, `CFNotificationCenter.h`,
`CFStringTokenizer.h`, and `CFURLEnumerator.h`. The pinned CF tree lacks those
headers. Historical swift-corelibs-foundation sources provide leads for
`CFAttributedString.h` and `CFNotificationCenter.h`, but its
[Swift 5.0 build script](https://github.com/swiftlang/swift-corelibs-foundation/blob/swift-5.0-RELEASE/build.py)
does not distinguish their public install status, and the latter header's
enum macros are incompatible with our pinned CF headers.

The discovery probe excludes five public architecture headers that failed at
least one target even against SDK 26.5: `architecture/alignment.h`,
`architecture/i386/pio.h`, and `architecture/arm/{asm_help,cframe,reg_help}.h`.
Apple's pinned `architecture/Makefile:copyhdrs` still installs all 19 public
headers.

The two probe files preserve their original bytes for saved closure digests.
Historical comments in the discovery fixture refer to the earlier audit.
Generate current review Markdown with `audit_sdk_headers --review-out`.

## Compare with Apple SDK Gen

For an investigation of overlaps and differences with Apple SDK Gen, run
`compare_sdk_gen_headers.py`. It reports path differences, byte-identical
matches and differences, and absent paths supplied by Clang. It also compares
CoreFoundation header trees when available.

```sh
python3 -m tools.sdk_review.compare_sdk_gen_headers \
  --c-root "$C_INSTALL" --reference-sdk "$SDK_GEN" --clang "$LLVM_CLANG"
python3 -m unittest discover -s tools/sdk_review
```
