# C installation tests

Run from the repository root with the generated C installation and the
same pinned Clang used by `make install`.

```sh
make test SDK="$SDK" CLANG="$LLVM_CLANG" OUT="$C_INSTALL"
```

- `recipes/` checks installed XNU headers and their source receipts, and
  exercises stage merging.
- `installed_headers/compile_probes.py` compiles each include root in
  `installed_headers/default_profile.c` individually, then compiles the full
  probe and the fixtures selected by Make. It targets macOS 14 for arm64
  with C11, using the installation and Clang resource headers.
- The fixture list in Make is explicit. The 26.5-specific availability and
  binary16 function signature cases only run for the 26.5 installation.
  The separate [binary16 runtime procedure](../.agents/skills/review-macos-c-sdk/scripts/sdk_review/headers/half_math_runtime.md)
  compiles a client object, links it and executes it on macOS.
- The arm64 macOS runtime check calls host libSystem to verify the 16-byte
  floating-point environment layout and FPCR rounding bits. It reports a skip
  on other hosts. The compile fixture checks the installed declaration.

Run the DNS-SD and resolver link probes against the composed tree.
On Apple Silicon, set `RUN=1` to execute
the probes. They exercise the DNS-SD name helper and the resolver's
initialization and cleanup without sending DNS queries.

```sh
make -C tests/composed_sdk test CLANG="$LLVM_CLANG" SDK="$NEW_SDK" RUN=1
```

Use the separate framework suite for an expanded composition. The probes
exercise Foundation macros and public graphics, security, networking and
model APIs. The AVRouting check imports the public header for a class
which macOS exposes in its SDK and marks unavailable.

```sh
make -k -C tests/composed_sdk test-frameworks CLANG="$LLVM_CLANG" SDK="$NEW_SDK" RUN=1
```

The [Bazel integration workspaces](../e2e/README.md) test the composed SDK archive.
