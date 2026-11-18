# Header recipes

The root Makefile runs the producers, assembles the bootstrap sysroot, runs
the two MIG targets, compares their outputs, and assembles the installation.
`make install` supplies a fresh work directory and removes it on exit.

[upstream.mk](upstream.mk) calls Apple's pinned architecture, CarbonHeaders
and AvailabilityVersions install targets and the Libc and Libinfo install
scripts. The other producers have a `Makefile` beside their recipes. These
call Apple scripts when feasible and mirror the relevant public header phase
when it is part of an Xcode project. Comments identify the upstream rule and
call out compatibility copies. Each producer stages into a separate root.

The merger takes the staged `.h` files in `usr/include` and rejects competing
owners. Each direct copy records its precise source. CarbonHeaders' legacy
availability headers give way to AvailabilityVersions, and the compatibility
recipe adapts `TargetConditionals.h` to both targets.

The XNU adapter reads public machine-independent and machine-dependent lists
from supported pinned XNU Makefiles and applies the macOS public `unifdef`
flags. It also covers the three public Libsyscall wrapper headers with
project-specific install rules. The MIG shell step reads the upstream
Libsyscall list, preprocesses against the bootstrap sysroot, and runs the
upstream attribute filter. Make requires the public user headers to match
across both Apple machine settings.

Python still handles merging and provenance, reading XNU's Makefile lists,
and guarded transformations for Libm, CarbonHeaders, AvailabilityVersions,
and dyld. The final `header-owners.json` records each producer, rule, and
direct inputs. `header-provenance.json` records hashes and origins. Git
submodules pin the source revisions. Review changes to the generated
inventory when updating pins.
