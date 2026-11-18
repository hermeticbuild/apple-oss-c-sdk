# Header recipes

The root Makefile orders producer staging, the pre-MIG merge, both MIG runs,
their comparison, and final assembly. Each producer adds a dependency to
the Make target named `stage` and stages files in its own directory.
`make install` supplies a fresh work directory and removes it on exit.

Each producer owns its Makefile, patches, templates, flags, and generator
scripts. Makefiles call Apple's pinned install rules where possible.
Compatibility edits run inside the producer stage. CarbonHeaders drops its
three legacy availability headers there, since AvailabilityVersions supplies
those paths. AvailabilityVersions adds the xros aliases to its own output.

A stage has a `dst/usr/include` tree and a tab-separated `records` file.
Every file has one record with its installed path, owner, origin, selection,
transform, and one or more repo-relative input paths. Direct copies and
generators write those records as they stage their output. The
`record-installed.sh` helper enumerates public headers written by Apple
install scripts in a subtree named by the owning recipe.

`merge.sh` compares each stage's files with its records, checks paths and
collisions, and installs into a temporary tree. The pre-MIG operation
publishes just that tree. The final operation batch-hashes the headers and
writes a single path-sorted `header-manifest.tsv`. Each row begins with the
installed path and SHA-256, followed by the remaining producer fields.
The last field in the column header, `inputs...`, denotes one tab-separated
field per input path. The x86_64 MIG stage is used for comparison and the
arm64 stage supplies the shared public headers.

The XNU adapter reads public lists from the pinned XNU Makefiles it supports
and applies Apple's macOS public unifdef flags. The recipe also uses the
Libsyscall public MIG list and upstream attribute filter. Python is local to
XNU, Libm, CarbonHeaders, AvailabilityVersions, and dyld. Audit and
qualification tools live under `tools/`.
