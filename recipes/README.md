# Header recipes

`install_c.py` gives [upstream.mk](upstream.mk) a fresh staging directory.
Make calls the pinned architecture, CarbonHeaders and AvailabilityVersions
install targets and the Libc and Libinfo install scripts. Each project has
its own destination. The merger takes `.h` files from `usr/include` and
rejects overlapping owners. CarbonHeaders' legacy availability headers
give way to AvailabilityVersions, and the compatibility recipe adapts
`TargetConditionals.h` to both targets.

The XNU adapter reads public machine-independent and machine-dependent lists
from the pinned XNU Makefiles it supports and applies the macOS public
`unifdef` flags. It follows the Libsyscall script's public Mach header and
MIG lists. MIG runs after the initial merge, with the staged headers as the
sysroot. The resulting 17 public user headers must agree between the two
Apple machine settings. The XNU adapter implements this subset of Apple's
install rules without requiring the SDK and internal tools expected by the
full upstream build.

`copies.tsv` lists fallback copies from the remaining producers. Each row
names an installed path, an upstream source path, and the selection evidence.
The Libm arm64 declarations, AvailabilityVersions xros alias, CarbonHeaders
target macros, and dyld repairs remain explicit compatibility recipes.

The final tree includes two generated indexes. `header-owners.json` records
the producer, rule, and direct inputs. `header-provenance.json` records each
header's hash and origin. For native staged files the provenance identifies
the upstream install rule and output path. Git submodules pin the source
revisions. Review changes to the generated inventory when updating pins.
