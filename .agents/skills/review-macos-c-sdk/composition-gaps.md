# Qualify SDK Gen composition inputs

Use this evidence when a framework or stub from a new SDK Gen release changes. Check the result against the [consumer profile](../../../tools/sdk_composition/README.md#consumer-archive).

The [framework recipes](../../../frameworks/README.md) reproduce the
qualified CoreFoundation and audio framework replacements. Each directory
records its own provenance. The stock 27.0 CoreFoundation and AudioToolbox
umbrellas fail the C include checks for this composition.

For consumer qualification with SDK Gen 0.0.4, restrict `___divsc3`,
`___divdc3` and `___divxc3` to `x86_64-macos` in the
`/usr/lib/system/libcompiler_rt.dylib` document inside `usr/lib/libSystem.B.tbd`.
Apply this correction to a local SDK Gen input before composing. Runtime
symbol lookup on macOS 26.5.2 found all three on Intel and none on arm64,
which agrees with the SDK 26.5 target groups. The hermetic-llvm
`libomp_test` exercises the arm64 fallback to LLVM's static builtins.

Use `make -C frameworks test` on a new composition to run each replacement
framework's compile or link probe on both architectures. Audit any new
declaration or export against its own documented inputs.
