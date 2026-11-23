# CoreFoundation

Copy the 40 paths in [headers.list](headers.list) verbatim from the pinned
Apple OSS CF Git objects. The list carries forward the qualified mapping
in `a717b3ba89aff56cc5b202cbab4df33bad8a0586:inputs/header-sources.tsv`.
The selected files carry Apple Public Source License notices. Preserve
the notices and use the pinned project's license for the distribution
inventory.
[Pinned CF source](https://github.com/apple-oss-distributions/CF/tree/dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3)
· [Project license](https://github.com/apple-oss-distributions/CF/blob/dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3/APPLE_LICENSE)

The input framework stub comes from the SDK Gen 0.0.4 macOS 27.0 release.
Its framework assembler generates the stub from its documentation symbol
inventory. The recipe adds `_CFRelease` and
`___CFConstantStringClassReference`, which are defined by Apple's pinned
`CFRuntime.c`. The checked input and output digests constrain the edit
to that specific released stub.
[SDK Gen framework assembler](https://github.com/apple-cross-toolchain/apple-sdk-gen/blob/0.0.4/tools/apple_sdk_gen/assembler/sdk_layout.py#L232-L241)
· [Apple definitions](https://github.com/apple-oss-distributions/CF/blob/dc54c6bb1c1e5e0b9486c1d26dd5bef110b20bf3/CFRuntime.c)

The released stub also leaves `CFRetain` unresolved. The bytes reproduced
by this recipe preserve that existing gap. The
[link probe](test.c) exercises the two amended exports.
