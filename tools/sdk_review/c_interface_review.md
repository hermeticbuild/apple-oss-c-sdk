# Compare installed C interfaces

Use the generated C installation, the reference SDK for the same canonical
release and build, and the verified LLVM bundle. Run from the repository root.

```sh
python3 -m tools.sdk_review.compare_c_interfaces \
  --installation "$C_INSTALL" --sdk "$APPLE_SDK" --clang "$LLVM/bin/clang" \
  --out "$WORK/semantics.json"
```

The report verifies the manifest and every installed header, then accounts for
identical headers, divergent counterparts, and installation-only headers.
Every divergent counterpart gets a public include test. Check
`headers[].include_reached` for the actual per-side trace result, including when
an umbrella succeeds without including the changed header. The trace records
both the path used to include a symlink and its resolved target.

The two sides use the same Clang, resource headers, C11 with blocks,
deployment floor 14.0, and arm64 and x86_64 targets. The named C consumers
live in [fixtures/c_interfaces](fixtures/c_interfaces). `probe_differences`
lists target-specific mismatches for this matrix. The full diagnostics and
include traces live in `probe_details`. The compiler, resource-header,
manifest, source-lock, and SDK metadata identities appear at the top of
the report. Keep the report with review evidence outside the release package.

The report covers every installed path and the listed consumer cases. Run
the [SDK path audit](README.md) for missing SDK paths. A matching diagnostic
can be a control, and a passing syntax probe provides no link or runtime
evidence. Use the paired linker on the affected consumers before claiming
ABI or deployment compatibility.

## Inspect logging macro lowering

The same logging macro can emit different imports after a header change.
Build the checked-in call once against each explicit sysroot and inspect the
undefined names. This is a targeted header investigation.

```sh
RESOURCE=$("$LLVM/bin/clang" -print-resource-dir)/include
for arch in arm64 x86_64; do
  for side in reference installation; do
    case $side in
      reference) root="$APPLE_SDK" ;;
      installation) root="$C_INSTALL" ;;
    esac
    object="$WORK/os-log-error-$arch-$side.o"
    "$LLVM/bin/clang" -target "$arch-apple-macos14.0" -isysroot "$root" \
      -nostdinc -isystem "$RESOURCE" -isystem "$root/usr/include" \
      -std=c11 -fblocks -O2 -c tools/sdk_review/fixtures/c_codegen/os_log_error.c -o "$object"
    "$LLVM/bin/llvm-nm" -u "$object"
  done
done
```
