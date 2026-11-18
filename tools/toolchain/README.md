# Pinned Clang

`resolve_clang.py` compares hermetic-llvm's minimal toolchain release and host
archive digest against [the checked-in pin](data/llvm-minimal-prebuilt.json),
fetches that target through Bazel, and prints the Clang path to stdout. Use
that path for Make and the C probes.

Run from the repository root with Bazel available and `LLVM_REPO` pointing
to a hermetic-llvm checkout whose minimal toolchain index matches the pin.

```sh
LLVM_CLANG=$(python3 -m tools.toolchain.resolve_clang --llvm-repo "$LLVM_REPO")
```
