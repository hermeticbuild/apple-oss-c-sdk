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

`compose_libsystem.py` verifies a standalone libSystem package using the
supplied SHA-256 of `manifest.json`. A package's `symlinks` object lists
SDK-relative link paths and exact relative targets. The canonical
`usr/lib/libSystem.tbd` points to `libSystem.B.tbd`. Compatibility links such
as `usr/lib/libm.tbd` and `usr/lib/libdl.tbd` point to `libSystem.tbd`.
For older manifests without `symlinks`, the canonical link is implicit.

For macOS 26.5, a package with a C manifest digest verifies that its original
header installation was selected. The composer writes the macOS SDK version
and both supported architectures to `SDKSettings.json` so that Clang can
record the SDK version in the linked executable. Use
`--prepared-framework NAME /path/to/NAME.framework` for a separately
qualified framework. Its files receive the `prepared-framework` source label.

## Objective-C runtime headers

Pass `--objc4-source "$OBJC4_SOURCE"` to add the nine public Objective-C
headers qualified for the Clang and LLVM clients. Supply a checkout or source
archive of Apple objc4-951.7 at revision
`ebfe77e64331034c867285a95d3ac205203291d5`. The
[objc Xcode project](https://github.com/apple-oss-distributions/objc4/blob/ebfe77e64331034c867285a95d3ac205203291d5/objc.xcodeproj/project.pbxproj)
marks these files `Public` and installs them under `usr/include/objc`.

The composer checks each header against its pinned SHA-256 and records the
revision, source paths and resulting digests in `composition.json`, under
the `objc4-public-headers` layer. The C install's original header manifest
retains its C source inventory. Supply the Objective-C runtime's linker
stub and compatibility alias independently from the selected SDK Gen input.

```sh
python3 -m tools.sdk_composition.compose_libsystem \
  --c-install "$C_INSTALL" --libsystem "$PACKAGE" --llvm "$LLVM" \
  --libsystem-manifest-sha256 "$PACKAGE_MANIFEST_SHA256" \
  --objc4-source "$OBJC4_SOURCE" \
  --external-stub "usr/lib/libobjc.A.tbd=$SDK_GEN/usr/lib/libobjc.A.tbd" \
  --external-stub "usr/lib/libobjc.tbd=$SDK_GEN/usr/lib/libobjc.tbd" \
  --out "$NEW_SDK"
```

Run the CLI tests with the pinned source checkout to exercise the full layer.

```sh
LIBSYSTEM_TEST_OBJC4="$OBJC4_SOURCE" \
  python3 -m unittest tools.sdk_composition.test_compose_libsystem
```
