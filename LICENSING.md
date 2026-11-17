# Distribution provenance review (2026-11-17)

This is a source and terms inventory for the prototype, not a legal clearance.

## Standalone C installation

The installer reads pinned Apple OSS submodules, Apple OSS build generators,
and the two local declarations in `templates/`. It reads no Xcode SDK or
Apple SDK Gen header. Apple's [APSL 2.0 text](https://opensource.apple.com/apsl/)
permits use and external distribution of covered source for commercial or
noncommercial purposes without a hardware condition in that license. It
requires retention of notices and the license text; distributing modifications
adds change notices and source availability duties. Apple's own page cautions
that the actual license is determined by each project's included license and
file header. For example, `Libm/Source/fenv.h` identifies APSL 1.1, so APSL
2.0 alone is not a sufficient inventory for this output.

Before publishing generated headers: inventory the exact file-level licenses,
include their texts and notices, mark the modified Apple headers and make the
generation source available as required, and review the local `fenv.h`,
`TargetConditionals.h`, and `sandbox.h` declarations. The current repository
only pins sources and records transformations; it does not yet package a
complete license bundle for a generated installation.

## LLVM proof composition

The reference Apple SDK Gen project's [README](https://github.com/apple-cross-toolchain/apple-sdk-gen/blob/main/README.md)
says its libSystem, libobjc, and libc++ stub symbol lists are refreshed from
an installed Xcode by
[`extract-darwin-libs.py`](https://github.com/apple-cross-toolchain/apple-sdk-gen/blob/main/tools/extract-darwin-libs.py).
The local CoreFoundation TBD amendment is kept outside this repository. The
generator's Apache 2.0 code license does not by itself establish rights to
redistribute its Xcode-derived export data or documentation-derived content.

Apple's [Xcode and Apple SDKs Agreement](https://www.apple.com/legal/sla/docs/xcode.pdf)
limits Apple Software use to Apple-branded macOS hardware and restricts
separate SDK use and redistribution, while acknowledging rights that may be
conferred by open-source component licenses. Apple's
[Website Terms](https://www.apple.com/legal/internet-services/terms/site.html)
restrict copying and automated acquisition of site content. How those terms
apply to generated symbol facts and API declarations needs qualified review.
Do not treat the local composed SDK archive as cleared for public distribution
or non-Apple hardware use on the basis of this prototype.
