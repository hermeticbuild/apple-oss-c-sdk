# LLVM cross-build proof

Run this after changes that could affect the composed macOS SDK. It exercises
the C header tree against LLVM's C++ build and links an LLVM binary for each
macOS target.

The [SDK composer](../sdk_composition/README.md) builds the test SDK. The restricted mode used by
`build_llvm.py` takes SDK metadata and link stubs from Apple SDK Gen, the
generated C installation, explicitly selected framework headers, and a
separate LLVM libc++ header tree and archive. Overlay mode starts with the
full SDK Gen header tree and replaces overlapping paths. Use restricted mode
for the primary test of our installation.

`build_llvm.py` packs the test SDK, sets up a Bazel consumer using the checked-in
[template](fixtures/MODULE.bazel.in), and builds `@llvm-project//llvm:llvm`
for arm64 and x86_64. It leaves the archive, composition log, and one build
log per architecture in the new work directory.

Set the inputs to absolute paths and run from the repository root on a host
with Bazel, tar, and zstd available. The libc++ paths point to the headers
and archive prepared from hermetic-llvm. SDK Gen 27.0's CoreFoundation
umbrella currently requires a missing Objective-C header. For this proof,
use an installation generated from Git tag
`archive/full-c-installation-2026-11-17`. After checking out the tag separately
and initializing its submodules, run
`python3 install_c.py --clang "$LLVM_CLANG" --out "$CF_INSTALL"` there.
Point `CF_TBD` at the external CoreFoundation stub amendment.

```sh
python3 -m tools.llvm_build.build_llvm --mode restricted \
  --c-root "$C_INSTALL" --reference-sdk "$SDK_GEN" \
  --libcxx-headers "$LIBCXX_HEADERS" --libcxx-archive "$LIBCXX_ARCHIVE" \
  --corefoundation-c-root "$CF_INSTALL" --corefoundation-tbd-override "$CF_TBD" \
  --llvm-repo "$LLVM_REPO" --work "$NEW_WORK_DIR"
```

The build wrapper invokes the composer with these inputs. Its SDK layout and
provenance files are described in the [composition docs](../sdk_composition/README.md).
