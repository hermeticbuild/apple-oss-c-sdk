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

The Libm recipe includes the input-denormal exception in `FE_ALL_EXCEPT` on
both qualified macOS targets. On arm64, XNU's `FPSR_IDC` supplies bit 7 and
LLVM libc's Darwin implementation confirms the `FE_FLUSHTOZERO` spelling.
On x86_64, MXCSR.DE and the x87 status word supply bit 1, and consumer code confirms the
`FE_DENORMALOPERAND` spelling. Pinned Apple Libm supplies the five standard
exception bits on both targets. The two platform-specific names are absent
from those headers. These definitions add no linker symbols.
[XNU FPSR bits](https://github.com/apple-oss-distributions/xnu/blob/xnu-12377.121.6/osfmk/arm64/proc_reg.h#L815-L826)
· [LLVM libc Darwin fenv](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/libc/src/__support/FPUtil/aarch64/fenv_darwin_impl.h#L61-L72)
· [Apple x87 status word](https://github.com/apple-oss-distributions/architecture/blob/architecture-282/i386/fpu.h#L80-L99)
· [Intel SDM Volume 1, Figure 10-3](https://cdrdv2-public.intel.com/874240/325462-090-sdm-vol-1-2abcd-3abcd-4.pdf)
· [Clang MXCSR flags](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.2/clang/lib/Headers/xmmintrin.h#L3096-L3104)
· [Remill fenv mappings](https://github.com/lifting-bits/remill/blob/66c488c9911fd9b368e4d0c9647d74239f8bba8b/tests/X86/Run.cpp#L303-L330)

The XNU adapter reads public lists from the pinned XNU Makefiles it supports
and applies Apple's macOS public unifdef flags. The recipe also uses the
Libsyscall public MIG list and upstream attribute filter. Python is local to
XNU, Libm, CarbonHeaders, AvailabilityVersions, and dyld. Audit and
qualification tools live under `tools/`.
