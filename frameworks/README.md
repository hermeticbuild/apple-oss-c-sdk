# Framework recipes for the macOS consumer SDK

These recipes build the framework layers for the macOS 26.5 composition.
Each recipe lists its source and stages one `.framework` directory. The
Security layer supplies the authorization header used by SystemConfiguration.
The composer takes Foundation directly from the SDK Gen release.

From the repository root, set `C_INSTALL` to the generated C tree and
`LLVM` to the pinned LLVM projection containing `bin/clang` and
`bin/clang-installapi`.

```sh
make -C frameworks prepare
make -C frameworks install CLANG="$LLVM/bin/clang" C_INSTALL="$C_INSTALL" OUT="$PWD/build/frameworks"
```

`prepare` fetches the pinned CF, IOAudioFamily, OpenAL, Security and configd
commits into `build/framework-sources`. Set `SOURCE_ROOT` to an absolute
directory containing those Git repositories to use existing objects.
`install` reads the pinned objects offline and writes into a new output
directory. To stage a subset, pass `FRAMEWORKS="CoreFoundation OpenAL"`,
for example. SystemConfiguration also stages CoreFoundation and Security.

The recipes use Make, shell, Git, and standard tools. They take no
official SDK path. Each framework's `provenance.md` identifies its inputs,
the scope of the repair, and the available source evidence. The
[composition instructions](../tools/sdk_composition/README.md#consumer-archive)
use the resulting directories and check their digests against the
qualified archive.

```sh
make -C frameworks test CLANG="$LLVM/bin/clang" SDK="$NEW_SDK"
```

Each framework layer has a `test.c` beside its recipe. The probes check
signatures, record layouts, or linkage on arm64 and x86_64. CoreAudioTypes,
IOKit and Security run compile checks. SystemConfiguration compiles its
reachability header directly and links a separate client of the umbrella.
Use `test-OpenAL`, for example, to run a single framework's probe.

On a Mac that can run both target architectures, add `RUN=1` to execute
the linked probes. CoreFoundation, AudioToolbox and SystemConfiguration
call their tested APIs. The other linked probes exercise dynamic loading
and symbol binding.
