# C header qualification

Run these commands from the repository root. Set `LLVM_CLANG` to the pinned
Clang executable and `C_INSTALL` to the generated installation.

```sh
python3 -m tools.qualify_headers.compile_probes --clang "$LLVM_CLANG" --sysroot "$C_INSTALL"
python3 -m tools.qualify_headers.trace_includes --probe tools/qualify_headers/fixtures/default_profile.c \
  --clang "$LLVM_CLANG" --sysroot "$C_INSTALL" \
  --out /tmp/c-install-closure.json
```

- `compile_probes.py` compiles the [shipping probe](fixtures/default_profile.c)
  as a whole and each include root in isolation. Both macOS 14 targets use
  C11 with `-nostdinc`, the pinned Clang resource headers, and the generated
  `usr/include`. [`make test`](../../tests/README.md) also supplies focused
  C fixtures using the repeatable `--fixture` option.
- `trace_includes.py` records the headers Clang opens and separates sysroot
  paths, resource headers, and lookup-only dependencies. Select the shipping
  fixture for routine qualification. Pass `--reference` with a saved SDK closure to check for
  missing paths. To collect a baseline, see [SDK review](../sdk_review/README.md).

The shipping probe is based on
[Zig's macOS C probe](https://codeberg.org/ziglang/zig/src/commit/47ff97b60b1a8215d4d15bb5870ee14b178558b9/tools/macos-headers.c).
The [discovery probe](fixtures/sdk_discovery.c) adds candidate roots for a
broader review and is the default for `trace_includes.py`.
