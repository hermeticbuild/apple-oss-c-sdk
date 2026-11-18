# C installation tests

Run from the repository root after initializing the Apple OSS submodules and
generating the C headers. Supply the same pinned Clang and output directory
used by `make install`.

```sh
make test CLANG="$LLVM_CLANG" OUT="$C_INSTALL"
```

- `recipes/` exercises XNU public header selection and stage merging.
- `installed_headers/` contains focused C fixtures. The [qualification tool](../tools/qualify_headers/README.md)
  compiles them and the shipping probe against the generated headers for both
  arm64 and x86_64.
- The arm64 macOS runtime check calls host libSystem to verify the 16-byte
  floating-point environment layout and FPCR rounding bits. It reports a skip
  on other hosts. The compile fixture checks the installed declaration on
  both target architectures.

The SDK audit has its own [tests and review workflow](../tools/sdk_review/README.md).
