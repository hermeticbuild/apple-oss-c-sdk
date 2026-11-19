# SDK composition

Review the [libSystem specification and implementation plan](libsystem-spec.md)
for the independent link-stub producer, Apple SDK Gen framework composition,
agent gap-review workflow and release gate.

See [Generating macOS SDK assets without the Xcode SDK](generating_sdk_assets.md)
for the source, documentation and runtime inputs for producing a standalone
release. It includes the verified Apple DocC index URLs and example commands
for the C, OSS framework and documentation-derived surfaces.

`compose_sdk.py` produces an SDK directory from explicit inputs. In
restricted mode it combines the standalone C installation, SDK Gen metadata
and link stubs, explicitly requested framework headers, and LLVM libc++.
Pass `--overlay-reference` for the secondary proof that starts with the
full SDK Gen tree and replaces overlapping C headers.

Run from the repository root with the paths set to your inputs and a new
output directory:

```sh
python3 -m tools.sdk_composition.compose_sdk \
  --c-root "$C_INSTALL" --reference-sdk "$SDK_GEN" \
  --libcxx-headers "$LIBCXX_HEADERS" --libcxx-archive "$LIBCXX_ARCHIVE" \
  --out "$NEW_SDK"
```

The composer preserves the standalone inventory as `c-header-manifest.tsv`
(or `c-header-owners.json` for archived inputs with a JSON owner index).
It writes the combined header provenance inside the SDK and the composition
TSV beside it. The [LLVM proof](../llvm_build/README.md) supplies the
CoreFoundation inputs, archives the composed SDK, and runs Bazel for both
architectures.

The current restricted mode copies every SDK Gen `.tbd` in the library and
framework directories and requires libc++. A lightweight shipping profile
would need its own asset selection and link validation.
