# macOS SDK integration tests

Build the [composed SDK](../tools/sdk_composition/README.md) and run
`make sdk-archive` at the repository root. Bazel reads
`build/sdk/MacOSX.sdk.tar.zst` directly. Bazel watches the archive file and
refreshes the SDK repository when it changes.

## Stage 1 Clang

Run with Bazel 9.3.2 and a configured `remote_default` in your Bazel rc.
The shared [remote configuration](remote.bazelrc) selects Linux workers.
It builds a macOS Clang with the seed compiler.

```sh
(
  cd e2e/llvm-stage1
  export USE_BAZEL_VERSION=9.3.2
  for cpu in arm64 x86_64; do
    bazel --bazelrc=../remote.bazelrc build --config=remote -c opt \
      --platforms="@llvm//platforms:macos_$cpu" \
      --@llvm//toolchain:bootstrap_stage=stage1_from_source \
      --@llvm//config:macos_libcxx_headers=llvm @llvm//tools:clang || exit 1
  done
)
```

## Local consumer suites

Run from this directory on Apple Silicon macOS with Rosetta available to
exercise both target architectures.

```sh
USE_BAZEL_VERSION=9.3.2 bazel test //:hermetic_llvm
USE_BAZEL_VERSION=9.3.2 bazel test //:rules_rs
```

Bazel fetches both pinned source trees and the child Bazel binaries. Each
upstream test workspace runs as its own root, with an SDK repository
override pointing to the extracted root-build archive. Each suite runs
arm64 and x86_64 locally. Run `//:libomp` for a focused check of the SDK
handoff.

The LLVM suite includes the manual header-order checks and sanitizer
builds. The Rust suite excludes the all-platform target-triple matrix.
Run the [LCOV report-content check](coverage.md) separately.
