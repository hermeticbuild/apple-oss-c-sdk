# macOS 26.5 libSystem component selection

The [source lock](data/macosx26.5/libsystem-source.json) follows the `Libsystem`
[gitlink in Apple's macOS 26.5 distribution](https://github.com/apple-oss-distributions/distribution-macOS/tree/83390100289cedfe669c31a96c94326d31afa1ed).
It pins the Libsystem-1356 project and the exact bytes of its version and
linker inputs. Review the upstream
[component selector](https://github.com/apple-oss-distributions/Libsystem/blob/c23b51183e46e613375dc7639fb4bf11fbf59ba8/xcodescripts/linker_arguments.sh),
[Xcode project](https://github.com/apple-oss-distributions/Libsystem/blob/c23b51183e46e613375dc7639fb4bf11fbf59ba8/Libsystem.xcodeproj/project.pbxproj)
and [build settings](https://github.com/apple-oss-distributions/Libsystem/blob/c23b51183e46e613375dc7639fb4bf11fbf59ba8/Libsystem.xcconfig).

Materialize the locked project in a separate checkout before running offline.

```sh
git clone https://github.com/apple-oss-distributions/Libsystem.git "$WORK/Libsystem"
git -C "$WORK/Libsystem" checkout --detach c23b51183e46e613375dc7639fb4bf11fbf59ba8

python3 -m tools.libsystem.component_graph \
  --source "$WORK/Libsystem" --out "$WORK/component-graph.json"
```

The same command accepts just the locked files under their original paths. It
verifies every SHA-256 before writing the graph. The extraction reads only
those public source files and the checked-in lock. No Xcode SDK, local runtime
or upstream shell-script execution is necessary.

The graph covers the normal macOS variant for arm64 and x86_64 clients. Each
source line is one slot with ordered alternative linker names. A required slot
needs at least one selected candidate on each configured build architecture.
For a slot, Apple's selector looks in `/usr/lib/system` for the first alternative
with the requested slice and reexports it. Otherwise it selects a compatible
static archive under `/usr/local/lib/system` and force-loads it. Optional slots
can be absent. The public project does not establish the exact contents of
Apple's internal build SDK. A linker short name also cannot determine the
selected binary's install name. The source-configured current version has
distinct local and Apple build values, and the effective compatibility version
depends on inherited settings.

## Resolve deployed edges and versions

1. Capture the umbrella image on the matching deployed OS build with
   `python3 -m tools.libsystem.capture`. Use the actual observed cache slice,
   such as arm64e, and keep that slice separate from the arm64 client target.
   Capture x86_64 independently. Record the runtime build and image UUID from
   the capture receipt.
2. Match each direct reexport's exact install name to the source slot by
   independently establishing the component's linker name from its public
   build rules or a matching observed image. An absent optional edge remains
   unresolved until evidence establishes its role or absence. An observed
   runtime reexport list cannot distinguish an omitted component from a
   private static archive folded into the umbrella. Keep any unmatched
   runtime edge open for review.
3. On each slice, independently verify the umbrella and component versions,
   explicit install names, symbol-forwarding relationships and nested
   reexports. Supply reviewed facts with these evidence pointers to the
   production resolver. The source graph is an input to this decision and
   cannot stand in for resolved component records. Use reference SDK
   differences to identify additional questions during qualification.
