# Qualification and LLVM composition

`check_c_profile.py` compiles the 174 checked-in roots individually and
together, plus semantic fixtures, for arm64 and x86_64 with `-nostdinc`. Only
the pinned Clang resource directory and the produced C installation are
visible. `check_libunwind_headers.py` verifies separately supplied LLVM
runtime headers. `compose_sdk.py` joins the C installation with Apple SDK Gen
link assets and framework headers, LLVM libc++, LLVM libunwind, and the
temporary archived CoreFoundation header layer. `validate_llvm.py` archives
that composition and builds `@llvm-project//llvm:llvm` on both macOS targets.
The composition preserves the standalone inventory as `c-header-manifest.tsv`
(or `c-header-owners.json` for older inputs). Its combined
`header-provenance.json` also covers the additional CoreFoundation and LLVM
libunwind headers.

The [174 include roots](fixtures/c/default_profile.c) come from
[Zig's macOS C probe](https://codeberg.org/ziglang/zig/src/commit/47ff97b60b1a8215d4d15bb5870ee14b178558b9/tools/macos-headers.c),
with Objective-C, SIMD, XPC, and `net/ipsec_offload.h` excluded. The same fixture supplies the roots for individual and combined probes.

Run these commands from the repository root after setting `LLVM_CLANG` and
`C_INSTALL` to absolute paths:

```sh
python3 -m tools.qualification.check_c_profile --clang "$LLVM_CLANG" --sysroot "$C_INSTALL"
python3 tools/qualification/fixtures/fenv_runtime.py  # arm64 macOS host
python3 -m unittest discover -s tools/tests
python3 -m tools.qualification.validate_llvm --help
```

Use `validate_llvm --mode restricted` with the explicit SDK Gen, LLVM runtime,
and CoreFoundation inputs. SDK Gen 27.0's CoreFoundation umbrella depends on a
missing ObjectiveC header. The local LLVM proof uses Apple OSS CoreFoundation
headers from the installation preserved at Git tag
`archive/full-c-installation-2026-11-17`, plus an amended CoreFoundation TBD.
