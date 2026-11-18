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
Each record contains the installed path, owner, origin, selection, transform,
and one or more repo-relative input paths. `stage.sh` can write these records
from installed files, explicit copies, and producer-supplied overrides.
The XNU and Libm generators record their own outputs inside their stages.

`merge.sh` combines sealed stages, checks paths and collisions, and hashes
the installed files. `manifests.awk` serializes the two JSON inventories from
those records and hashes. The merge uses the same operation before and after
MIG. The x86_64 MIG stage is used for comparison and the arm64 stage supplies
the shared public headers.

The XNU adapter reads public lists from the pinned XNU Makefiles it supports
and applies Apple's macOS public unifdef flags. The recipe also uses the
Libsyscall public MIG list and upstream attribute filter. Python is local to
XNU, Libm, CarbonHeaders, AvailabilityVersions, and dyld. Audit and
qualification tools live under `tools/`.
