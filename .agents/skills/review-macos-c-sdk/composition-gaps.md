# Qualify SDK Gen composition inputs

Use this evidence when a framework or stub from a new SDK Gen release changes. Check the result against the [consumer profile](../../../tools/sdk_composition/README.md#consumer-archive).

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
