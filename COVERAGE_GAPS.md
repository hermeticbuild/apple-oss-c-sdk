# C coverage gaps against macOS SDK 26.5

Reference: `inputs/c-probe-headers.txt`, LLVM 23.1.2 minimal prebuilt
`llvm-23.1.2-2` for Darwin arm64, `-target arm64-apple-macos14.0` and
`x86_64-apple-macos14.0`, `-std=c11`. The reference uses an official SDK only
as a local compile/coverage oracle. No SDK header content enters the installer.

Both architecture reference runs pass all 179 roots (358 probes). The current
Apple OSS installation passes 354/358; `simd/simd.h` and `xpc/xpc.h` fail on
both architectures. The path comparison reports 35 unique absent files:

| Group | Missing paths | Source status |
| --- | ---: | --- |
| CoreFoundation | 7 | Pinned `apple-oss-distributions/CF` lacks them. Current `swiftlang/swift-corelibs-foundation` offers `CFNotificationCenter.h`, but its modern `CF_ENUM`/`CF_EXTENSIBLE_STRING_ENUM` contract does not compile with the pinned CF header set; no macOS public install rule was identified there. Keep unresolved. |
| SIMD | 16 | No first-party Apple OSS source or public install rule identified. Keep unresolved. |
| XPC | 11 | No `apple-oss-distributions/libxpc` or `xpc` repository identified. Keep unresolved. |
| `tgmath.h` | 1 | Clang's resource `tgmath.h` uses `#include_next` on hosted Apple targets. The generated installation compiles using its fallback, but no independent Apple OSS source for the SDK's extra header was located. Keep as API parity gap. |

Final source sweep: the current `apple-oss-distributions` repository inventory
has `CF` and `Libm`, but no named SIMD or XPC source repository; its
[`distribution-macOS` submodule manifest](https://github.com/apple-oss-distributions/distribution-macOS/blob/main/.gitmodules)
also has no SIMD or XPC component. The current `CF`, `Libm`, and `Libc`
source trees do not contain the absent header basenames. Historical
`swift-corelibs-foundation` tags do contain `CFAttributedString.h` and
`CFNotificationCenter.h`, but their [Swift 5.0 build script](https://github.com/swiftlang/swift-corelibs-foundation/blob/swift-5.0-RELEASE/build.py)
states that it does not distinguish public and private CoreFoundation
headers. `CFAttributedString.h` compiles with this older CF set in isolation;
`CFNotificationCenter.h` does not because the CF enum macros differ. Those
historical sources are leads for a compatible derivation, not proof that
they were the macOS SDK's installed headers. The search remains open for
every missing path.

CoreFoundation paths: `CFAttributedString.h`, `CFCGTypes.h`,
`CFFileDescriptor.h`, `CFFileSecurity.h`, `CFNotificationCenter.h`,
`CFStringTokenizer.h`, `CFURLEnumerator.h`, each under
`System/Library/Frameworks/CoreFoundation.framework/Headers/`.

SIMD paths, each under `usr/include/simd/`: `base.h`, `common.h`,
`conversion.h`, `extern.h`, `geometry.h`, `logic.h`, `math.h`, `matrix.h`,
`matrix_types.h`, `packed.h`, `quaternion.h`, `simd.h`, `types.h`, `vector.h`,
`vector_make.h`, `vector_types.h`.

XPC paths, each under `usr/include/xpc/`: `activity.h`, `availability.h`,
`base.h`, `connection.h`, `debug.h`, `endpoint.h`, `listener.h`,
`peer_requirement.h`, `rich_error.h`, `session.h`, `xpc.h`.

`float.h` is **not** an absent required SDK header. Clang's resource
`float.h` is the only one opened by the reference compilation. `-MD` also
lists the SDK `float.h` because Clang tests its existence with
`__has_include_next`; the `-H` include trace shows it is not opened on these
targets. The manifest records that path as a lookup candidate, not as an
installed-header requirement. `SDKSettings.json` is likewise SDK metadata,
not a C header.

Zig's `net/ipsec_offload.h` root is not present in the macOS 26.5 SDK and is
excluded from this version's active probe. The `ucontext.h` root uses
`_XOPEN_SOURCE=700`, as required by the reference header.

These are gaps relative to this probe and SDK version. They are not a claim
that no first-party source exists anywhere. Revisit every group before a
completeness or distribution claim, and keep the local provenance derivations
in `README.md` under review.
