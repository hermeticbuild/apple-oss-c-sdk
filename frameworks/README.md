# Framework recipes for the macOS consumer SDK

These recipes build the eight replacement frameworks in the qualified
macOS 26.5 composition. Each recipe lists its source and stages one
`.framework` directory. The composer takes Foundation directly from the
SDK Gen release.

From the repository root, set `SDK_GEN` to the absolute path of the
`MacOSX.sdk` extracted from Apple SDK Gen 0.0.4. The CoreFoundation recipe
checks the digest of the input TBD before amending it.

```sh
make -C frameworks prepare
make -C frameworks install SDK_GEN="$SDK_GEN" OUT="$PWD/build/frameworks"
```

`prepare` fetches the exact Apple OSS commits into
`build/framework-sources/{CF,IOAudioFamily,OpenAL}`. Set `SOURCE_ROOT` to
an absolute directory containing those Git repositories to use existing
objects. `install` reads those objects and the specified SDK Gen input
offline. Its output directory must be new. To stage a subset, pass
`FRAMEWORKS="CoreFoundation OpenAL"`, for example.

The recipes use Make, shell, Git, and standard tools. They take no
official SDK path. Each framework's `provenance.md` identifies its inputs,
the scope of the repair, and the available source evidence. The
[composition instructions](../tools/sdk_composition/README.md#consumer-archive)
use the resulting directories and check their digests against the
qualified archive.

```sh
make -C frameworks test CLANG="$LLVM/bin/clang" SDK="$NEW_SDK"
```

Each replacement framework has a `test.c` beside its recipe. The probes
check signatures, record layouts, or linkage on arm64 and x86_64.
CoreAudioTypes and IOKit run compile checks. The other six probes also
link against their respective frameworks. Use `test-OpenAL`, for example,
to run a single framework's probe.

On a Mac that can run both target architectures, add `RUN=1` to execute
the linked probes. CoreFoundation and AudioToolbox call their tested APIs.
The other linked probes exercise dynamic loading and symbol binding.
