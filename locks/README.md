# Apple OSS source locks

Each JSON file resolves the selected projects for one canonical SDK name.
Both current locks use the macOS header recipes. The SDK version and reference
SDK build describe qualification, while the distribution tag and peeled
commit identify Apple's operating-system source snapshot. Deployment targets
are chosen separately by the qualification commands.

## Prepare and install

From the repository root:

```sh
SDK=macosx26.5
python3 -m tools.sources.locked_sources prepare --sdk "$SDK"
make install SDK="$SDK" CLANG="$LLVM_CLANG" OUT="$C_INSTALL"
make test SDK="$SDK" CLANG="$LLVM_CLANG" OUT="$C_INSTALL"
```

Preparation fetches only the locked commits into a Git cache under
`build/source-cache` and checks them out in `build/sources/$SDK`. Pass
`--offline` to prepare from a populated cache without contacting a remote.
Pass `--cache` to share a cache across checkouts. For a different checkout
directory, pass the same absolute path as `--source-root` to preparation
and `SOURCE_ROOT` to Make.
Prepare into a new directory when replacing or refreshing a tree. Each
version can build independently from its own prepared tree.

Make checks that the source tree matches the lock and that the project
checkouts are clean. Installation itself requires no network. The output
includes `source-lock.json` beside `header-manifest.tsv`.

Run the cache and checkout tests with `python3 -m unittest discover -s tools/sources`.

The optional Objective-C layer has its own lock and checkout under
`build/sources/macosx26.5-objc4`. It never enters the standalone C installation.

```sh
python3 -m tools.sources.locked_sources prepare --sdk macosx26.5 --profile objc4
make install-objc4 SDK=macosx26.5 OUT="$OBJC4_INSTALL"
```

## Add a version

1. Find the intended Apple [source release](https://opensource.apple.com/releases/)
   and resolve its exact distribution tag to a commit. Read that commit's
   `release.json`, `.gitmodules` and Git tree without checking out the projects
   recursively. Take each selected project's commit from its gitlink.
2. Include only projects required by the recipes. The `projects` map records
   the checkout name, URL, full commit SHA, tag for provenance, and why that
   pin was selected. A `selection` of `distribution` means the pin matches
   the recorded distribution snapshot. Explain standalone releases and
   overrides in that field.
3. Record the reference SDK's canonical name, platform, version and build
   in `sdk`. Prepare, install and run `make test` for the new lock. Use the
   [SDK review tools](../tools/sdk_review/README.md) to check reference
   coverage. Qualify a new platform's install rules and target environments
   before enabling it in the source-lock tool.

The two macOS versions use the same Make recipes. The SDK identifier selects
the locked sources and scopes review data.
