# Blocks runtime pointer bounds

The macOS 26.5 recipe derives `Block.h` from the pinned libdispatch
`src/BlocksRuntime/Block.h`. The upstream header declares the copy and
release operations on a single block and preserves the caller's block type in
the wrappers. Its license notice is retained. The libclosure public header
contains an unresolved license placeholder and is excluded from the recipe.

Under Clang bounds checking, a raw copy accepts a single block pointer and
returns a single pointer. A raw release takes a single pointer. The typed
wrappers form the boundary where the block is explicitly converted. The local
patch uses Clang's documented pointer annotations and forge operation. The
ordinary compiler path still evaluates the argument once and emits the same
calls. [Clang bounds safety](https://clang.llvm.org/docs/BoundsSafety.html)

For qualification, compile the fixture in Apple Clang C11 with `-fblocks
-fbounds-safety -Werror`. The default case must compile. Adding
`-DTEST_UNSAFE_RAW_RELEASE` must diagnose the unsafe conversion. Run each
case against the installation and separately against the reference SDK for
arm64 and x86_64. [Qualification fixture](../../tests/installed_headers/block_pointer_bounds.c)
