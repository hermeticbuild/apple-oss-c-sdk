# SDK coverage review

Run this workflow when qualifying a new SDK version, updating Apple OSS pins,
or investigating a scope gap. It reads the SDK and the generated installation
and writes review reports. The Make installer has no dependency on the SDK
or these ledgers.

## Agent workflow

Start with a fresh installation and a reference SDK matching the lock's
version and build. Use the pinned LLVM tools and an empty report directory.

```sh
make -f tools/sdk_review/headers.mk -j3 header-backlog \
  SDK=macosx26.5 LLVM="$LLVM" C_INSTALL="$C_INSTALL" APPLE_SDK="$SDK" WORK="$WORK"
```

Read `header-backlog.json` for path decisions, failed inclusion contexts,
and semantic differences. Read `discovery-reference.json` and
`discovery-generated.json` separately for optional roots. A completed backlog
with open findings exits nonzero; distinguish open findings from failed tools
or stale inputs. Keep the previous inventory and decisions when changing pins.

1. Reproduce one affected root or client. Record both architectures, feature
   flags, deployment target, source lock, compiler, and the reference result.
2. Trace the installed path to its manifest receipt and Apple's pinned rule.
   A link failure also needs the exact Mach-O spelling and its provider; use
   [TBD lookup](lookup_tbd_symbols.md) and [compare client links](diagnose_links.md).
3. Fix the owning recipe or document the proposed omission. Keep local patches
   and their source evidence beside the recipe. Treat an SDK Gen framework or
   link asset issue as a composition finding.
4. Ask Corentin before adopting an unproven private or public source, making
   a local departure from an upstream rule, guessing ABI or availability,
   changing package scope or an approved omission, or weakening a test.
   Give the path or gap ID, reproducer, evidence, recommendation, and effect
   of leaving the gap open. Keep working on unrelated gaps.
5. Rerun the failing case on both applicable targets, regenerate the affected
   reports, and record the result or accepted exception in the existing ledger.
   Keep the reason and reopening condition. Passing consumer builds do not
   close unexplained header differences.

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
`--probe` to use the discovery fixture. A discovery reference records which
paths were reached and keeps existing scope decisions. Use the shipping fixture
with `--require-decisions`. Add `--report-only` when tracing discovery against
the generated installation to record failed roots.
`audit_sdk_headers.py` inventories the full SDK `usr/include` even when a path
is outside the probe. Review new paths, unresolved source gaps, and decisions
that no longer match the SDK. Add `--require-decisions` when every decision must
be resolved. Preserve earlier inventories as baselines. The checked-in 26.5
inventory is a historical full-profile snapshot. The auditor selects default
decision files by the reference SDK's `CanonicalName`. A version without
checked-in ledgers starts with no manual approvals. When the installation
contains a source lock, use a matching SDK and a newly traced installation
closure if an older trace has no lock digest. Supply explicit ledger
paths to review changes before checking in a new version's decisions.

| Input | Meaning |
| --- | --- |
| [Header decisions](data/macosx26.5/sdk-header-decisions.tsv) | Pattern, include or omit decision, reason, evidence, SDK name, and digest of the approved matching paths |
| [Review notes](data/macosx26.5/sdk-review-notes.tsv) | Outstanding source gaps |
| [Scope approvals](data/macosx26.5/sdk-scope-approvals.tsv) | Approved sets outside the package scope |
| [Installation-only decisions](data/macosx26.5/installation-only-decisions.tsv) | Reviewed generated paths absent from the SDK |
Installed headers record their current source selections in the generated
manifest. See the [recipe documentation](../../recipes/README.md).

### Outstanding discovery coverage

The 26.5 discovery trace reaches 16 `simd/*` and 11 `xpc/*` paths approved
for omission while a simple public Apple OSS source is unavailable. It also
reaches all 15 legacy RPC service headers approved for omission. Apple OSS
Librpcsvc can generate those headers for consumers that need them.
Clang's resource `tgmath.h` fallback makes the shipping probe compile. SDK
`tgmath.h` API parity remains open. See the [source findings](data/macosx26.5/header-source-candidates.md).

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

Each saved closure records the probe's exact digest. Regenerate discovery
closures after updating the fixture. Generate current review Markdown with
`audit_sdk_headers --review-out`.

## Compare with Apple SDK Gen

For an investigation of overlaps and differences with Apple SDK Gen, run
`compare_sdk_gen_headers.py`. It reports path differences, byte-identical
matches and differences, and absent paths supplied by Clang. It also compares
CoreFoundation header trees when available.

```sh
python3 -m tools.sdk_review.compare_sdk_gen_headers \
  --c-root "$C_INSTALL" --reference-sdk "$SDK_GEN" --clang "$LLVM_CLANG"
python3 -m unittest discover -s tools/sdk_review -t .
```
