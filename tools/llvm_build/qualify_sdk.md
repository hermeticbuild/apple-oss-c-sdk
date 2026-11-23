# Qualify the composed SDK with macOS consumers

Run on Apple Silicon with Rosetta available for Intel test executables.
Use the same composed archive for all three consumers. The [composer](../sdk_composition/README.md)
records file digests, symlinks and providers. Keep the archive SHA-256 and the
digest of its `usr/lib/libSystem.B.tbd` with the build logs.

## Consumer inputs

The 26.5 experiment used hermetic-llvm scratch revision
`d92a9764364584c8f342db198c6d8cbd312e0e51`, which accepts a framework from
any of its three Apple archive locations. That revision is in the local
`cerisier/sdk-framework-locations` branch. Its parent is
`190fc9f5df9c86ed0f1db77e408381f427dcb829`. The rules_rs test sources match
revision `e7d9e55555762e56b87454e7f17d70584f8968d8`. Use scratch consumer
checkouts for module configuration and keep the test sources intact.

In hermetic-llvm's root module, replace the macOS SDK archive tag. In the
hermetic-llvm e2e/rules_cc and rules_rs/test root modules, point the same
extension at the same archive. Use `//extensions:osx.bzl` inside hermetic-llvm
and `@llvm//extensions:osx.bzl` from consumers. Retain the e2e module's
existing LLVM override. In rules_rs/test add a `local_path_override` for
`llvm` pointing to the tested hermetic-llvm checkout. The tar archive tag
has the following form.

```starlark
osx = use_extension("@llvm//extensions:osx.bzl", "osx")
osx.from_archive(
    urls = ["file:///absolute/path/MacOSX.sdk.tar.zst"],
    sha256 = "<archive SHA-256>",
    strip_prefix = "MacOSX.sdk",
    type = "tar.zst",
)
```

## Execute the three gates

The commands below use Bash arrays. Set `REPORTS` to an existing absolute
directory. Give each consumer its own output base
if running them concurrently. Keep remote caching enabled where configured.
The scratch rules_rs remote-execution configuration selects a Linux host.

```bash
export BAZEL_MACOS_EXPERIMENTAL_INCLUDE_ALL_SDK_LIBS=1
sdk_flags=(--repo_env=BAZEL_MACOS_EXPERIMENTAL_INCLUDE_ALL_SDK_LIBS
           --repo_env=BAZEL_MACOS_FRAMEWORKS)
export BAZEL_MACOS_FRAMEWORKS=CoreFoundation,Foundation

cd "$HERMETIC_LLVM"
for cpu in arm64 x86_64; do
  bootstrap=(-c opt --extra_toolchains=//toolchain:all
             --extra_execution_platforms=@platforms//host
             --//toolchain:bootstrap_stage=stage1_from_source
             "--platforms=//platforms:macos_$cpu" --//config:macos_libcxx_headers=llvm
             "${sdk_flags[@]}")
  bazel build "${bootstrap[@]}" //tools:clang || exit 1
  bazel aquery "${bootstrap[@]}" --output=text --include_commandline \
    'inputs(".*llvm/lib/IR/LLVMContext[.]cpp$", mnemonic("CppCompile", deps(//tools:clang)))' \
    > "$REPORTS/bootstrap-$cpu.actions" || exit 1
  grep -Fx "action 'Compiling llvm/lib/IR/LLVMContext.cpp'" "$REPORTS/bootstrap-$cpu.actions" || exit 1

done

cd "$HERMETIC_LLVM/e2e/rules_cc"
for cpu in arm64 x86_64; do
  darwin=("${sdk_flags[@]}"
          --extra_execution_platforms=@platforms//host,@llvm//platforms:macos_x86_64
          "--platforms=@llvm//platforms:macos_$cpu" --@llvm//config:macos_libcxx_headers=llvm)
  bazel test --nocache_test_results --keep_going "${darwin[@]}" //... || exit 1
  bazel test --nocache_test_results "${darwin[@]}" //:main_default \
    //header_order:precedence //header_order:libcxx_c_wrappers \
    //header_order:search_c_macos_x86_64_test //header_order:search_cxx_macos_x86_64_test || exit 1
  bazel build "${darwin[@]}" //:tsan_fail //:lsan_fail \
    @llvm//tests/cxxstdlib_settings:{defaults,headers_only,libraries_only,both} || exit 1
  ./coverage_lcov_test.sh --nocache_test_results "${darwin[@]}" || exit 1
  cp "$(bazel info output_path)/_coverage/_coverage_report.dat" \
    "$REPORTS/coverage-$cpu.lcov" || exit 1
done

cd "$RULES_RS/test"
export BAZEL_MACOS_FRAMEWORKS=CoreFoundation,Foundation,AudioToolbox,AudioUnit,CoreAudio,CoreAudioTypes,CoreMIDI,IOKit,OpenAL
for cpu in arm64 x86_64; do
  platform=()
  if [[ "$cpu" == x86_64 ]]; then
    platform=(--platforms=@rules_rs//rs/platforms:x86_64-apple-darwin
              --extra_execution_platforms=@platforms//host,@llvm//platforms:macos_x86_64)
  fi
  bazel test --nocache_test_results --keep_going --build_tests_only --test_env="PATH=/bin:$PATH" \
    "${sdk_flags[@]}" "${platform[@]}" --@llvm//config:macos_libcxx_headers=llvm \
    -- //... -//:target_triple_constraints_test || exit 1
done
```

The bootstrap gate is `//tools:clang` with `stage1_from_source`. The alias
selects Stage 1, which the seed compiler builds from source using the composed
SDK. Inspect a compile action and its sysroot, and match the extracted archive
to the digest under test. Rebuilding LLVM with that compiler is Stage 2 and is
outside this gate.

Record cached versus executed tests, incompatible targets, and failures.
The macOS rules_rs command covers 39 tests in the pinned snapshot. Its
explicitly excluded target transitions over every Rust target triple and
requires a separate Windows MSVC license decision. A pass here establishes
the macOS consumer scope. For host shell scripts the test PATH selects
macOS bash and retains the user's Bazel executable for nested tests.
