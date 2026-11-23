# Compose a macOS consumer SDK

The composer combines a source-locked macOS 26.5 C installation, pinned
`objc4` headers, and named Apple SDK Gen assets. It copies the SDK Gen
libSystem TBD unchanged and records the source SDK name separately from the
generated SDK settings. Hermetic-llvm supplies the C++ headers; only the
dylib link stubs enter the SDK.

The composer restores the macOS compatibility names from Apple's Libsystem
install rule as links to the unchanged SDK Gen umbrella. This lets
`-ldl`, `-lm` and `-lpthread` bind through libSystem.
[Apple Libsystem install rule](https://github.com/apple-oss-distributions/Libsystem/blob/c23b51183e46e613375dc7639fb4bf11fbf59ba8/xcodescripts/create_dylib_symlinks.sh#L14-L31)

Use Python 3.11+, the [verified LLVM tools](../toolchain/README.md), and the
[C and Objective-C installations](../../locks/README.md). For SDK Gen 0.0.4,
verify `stub-sdks-27.0.tar.zst` before extracting it:

```text
sha256:e3ba6081bfcd23973dd80fe76b3c28ce8d3a98d9eb9cbc800225a649c5c07184
```

Set `SDK_GEN` to the extracted `MacOSX.sdk` and `NEW_SDK` to a new output
directory named `MacOSX.sdk`. The command below composes a smoke SDK.
For the three consumer gates, replace each broken SDK Gen framework with
its qualified directory using `--prepared-framework NAME DIRECTORY`, and
include the iconv/charset layer described below.

```bash
stubs=()
for name in libc++ libc++.1 libc++abi libobjc libobjc.A libz; do
  stubs+=(--external-stub "usr/lib/$name.tbd=$SDK_GEN/usr/lib/$name.tbd")
done
python3 -m tools.sdk_composition.compose_sdk \
  --c-install "$C_INSTALL" --objc4-install "$OBJC4_INSTALL" \
  --sdk-gen "$SDK_GEN" --llvm "$LLVM" --framework Foundation \
  "${stubs[@]}" --out "$NEW_SDK"
```

Use `--framework NAME` to select an unmodified SDK Gen framework, or
`--prepared-framework NAME DIRECTORY` to use a separately prepared one.
The earlier consumer proof used Apple OSS CoreFoundation headers and an
amended stub, plus the SDK Gen macOS C audio profile for AudioToolbox,
AudioUnit, CoreAudio, CoreAudioTypes, CoreMIDI, IOKit, and OpenAL. The stock
27.0 CoreFoundation and AudioToolbox umbrellas fail C inclusion; the smoke
archive alone does not qualify these consumers.
The composer rejects a framework or stub that shadows an SDK Gen libSystem provider.

For consumer qualification with SDK Gen 0.0.4, restrict `___divsc3`,
`___divdc3` and `___divxc3` to `x86_64-macos` in the
`/usr/lib/system/libcompiler_rt.dylib` document inside `usr/lib/libSystem.B.tbd`.
Apply this correction to a local SDK Gen input before composing. Runtime
symbol lookup on macOS 26.5.2 found all three on Intel and none on arm64,
which agrees with the SDK 26.5 target groups. The hermetic-llvm
`libomp_test` exercises the arm64 fallback to LLVM's static builtins.

### Prepare the consumer framework inputs

- **CoreFoundation:** Use the 40 `CoreFoundation.framework/Headers/` rows
  in `git show a717b3ba89aff56cc5b202cbab4df33bad8a0586:inputs/header-sources.tsv`.
  Each `CF:PATH` names a file to copy verbatim from Apple OSS CF commit
  `dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3` into the prepared framework's
  `Headers/`. Copy SDK Gen's `CoreFoundation.tbd` (SHA-256
  `2762fd6c1d1ca0b834460550df1b08bb6cf2218cf74525f443e7029861246fa1`),
  then restore `_CFRelease` and `___CFConstantStringClassReference` in its
  public symbol list. Both are defined in the pinned CF `CFRuntime.c`.
  The amended stub tested here has SHA-256
  `af6c182cb111f52124b56c037390acbe8a5b78f071c675507b6a035d8969b56c`.
- **Audio and IOKit:** Use the Apple SDK Gen checkout with the macOS C audio
  profile changes. The 0.0.4 archive does not contain those repairs. Generate
  the profile as documented in that checkout, or use its
  `install_macos_audio_profile` helper to stage just the seven frameworks.
  Use `tools/tests/check_macos_audio_profile.py` from that checkout to check
  the composed SDK. This profile still requires a separate source checkout.

For the consumer archive, keep SDK Gen Foundation and the stubs selected
above. Add the prepared framework directories and the iconv stubs:

```bash
frameworks=(--prepared-framework CoreFoundation "$CF_FRAMEWORK")
for name in AudioToolbox AudioUnit CoreAudio CoreAudioTypes CoreMIDI IOKit OpenAL; do
  frameworks+=(--prepared-framework "$name" "$AUDIO_FRAMEWORKS/$name.framework")
done
for name in libiconv libiconv.2 libcharset libcharset.1; do
  stubs+=(--external-stub "usr/lib/$name.tbd=$STUBS/usr/lib/$name.tbd")
done
python3 -m tools.sdk_composition.compose_sdk \
  --c-install "$C_INSTALL" --objc4-install "$OBJC4_INSTALL" \
  --sdk-gen "$SDK_GEN" --llvm "$LLVM" --framework Foundation \
  "${frameworks[@]}" "${stubs[@]}" --out "$NEW_SDK"
```

Keep the SDK Gen pin, hashes for prepared inputs, and `composition.json` with
the archive. Run the [three macOS gates](../llvm_build/qualify_sdk.md)
against that archive on both architectures.

## Packing release archives

Run the packer on the composed SDK. Each command prints
the SHA-256 of the compressed archive. The output directory must already exist
outside the source tree. The archive root name stays the same across builds in
different source directories.

```sh
python3 -m tools.sdk_composition.pack_archive --source "$NEW_SDK" \
  --root-name MacOSX.sdk --output "$DIST/MacOSX.sdk.tar.zst"
```

The packer writes sorted POSIX pax tar entries with epoch timestamps and
numeric owner and group zero. It keeps file bytes, empty directories and
symlink target strings. Regular files use mode 0644 or 0755 according to
their executable bits, and hard-linked files each carry their own bytes.
Extended attributes and AppleDouble sidecars are omitted. Compression uses
the local `zstd --single-thread -6`. Use the same zstd version for both builds
when comparing release hashes.

## libiconv and libcharset

Generate the two separate libraries before composing the SDK. The producer
reads the pinned Git objects for Apple's libiconv-115.120.2, the standalone
C header installation, and the pinned macOS arm64 LLVM projection. macOS
`plutil` reads the Xcode project. The compiler uses a temporary sysroot
containing only C headers verified against the installation manifest.

```sh
python3 -m tools.sdk_composition.iconv_stubs \
  --source "$ICONV_SOURCE" --c-install "$C_INSTALL" --llvm "$LLVM" --out "$STUBS"
```

Both dylibs use the Release target's public and private header phases, product
names and versions. For libiconv the TAPI configuration supplies `-DIN_TAPI`,
the Citrus include path and the reexport of the freshly generated libcharset.
The install script specifies the two unversioned symlinks. The generated
`manifest.json` records the source revision, tool and C manifest digests,
registered headers and output digests.
[Project](https://github.com/apple-oss-distributions/libiconv/blob/7fb0198429570d3b6aa562d228a6ea5936d15c05/libiconv.xcodeproj/project.pbxproj)
· [TAPI configuration](https://github.com/apple-oss-distributions/libiconv/blob/7fb0198429570d3b6aa562d228a6ea5936d15c05/xcodeconfig/libiconv.xcconfig)
· [Install aliases](https://github.com/apple-oss-distributions/libiconv/blob/7fb0198429570d3b6aa562d228a6ea5936d15c05/xcodescripts/dest_cleanup.sh)

Append these four arguments to `compose_sdk`.

```sh
--external-stub "usr/lib/libiconv.2.tbd=$STUBS/usr/lib/libiconv.2.tbd" \
--external-stub "usr/lib/libiconv.tbd=$STUBS/usr/lib/libiconv.tbd" \
--external-stub "usr/lib/libcharset.1.tbd=$STUBS/usr/lib/libcharset.1.tbd" \
--external-stub "usr/lib/libcharset.tbd=$STUBS/usr/lib/libcharset.tbd"
```

For qualification, export `ICONV_SOURCE`, `C_INSTALL` and `LLVM` and run
`python3 -m unittest -v tools.sdk_composition.test_iconv_stubs`. The tests
check reproducibility, link a client against `-liconv` alone for arm64 and
x86_64, and inspect the two-level bindings for `iconv_open` and `locale_charset`.

Setting `ICONV_REFERENCE_SDK` additionally compares the products with the macOS
26.5 SDK. All 95 direct iconv exports and both charset exports match, including
the reexport edge and dylib versions. The producer targets macOS arm64 and
x86_64 with a deployment floor of 11.0. The reference uses arm64e and x86_64,
and also includes Catalyst. Upstream LLVM emits `not_app_extension_safe` for
these project settings. App-extension compatibility remains unqualified.
