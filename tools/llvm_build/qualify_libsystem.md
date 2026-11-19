# Qualify a generated libSystem with macOS consumers

Run on Apple Silicon with Rosetta available for Intel test executables.
Use the same composed archive for all three consumers. The [composer](../sdk_composition/README.md)
records file digests, symlinks and providers. Keep the archive SHA-256 and the
digest of its `usr/lib/libSystem.B.tbd` with the build logs. The [qualification
journal](../libsystem/progress.md) records the candidates actually exercised.

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
directory, `C_SDK_REPO` to this checkout, `LLVM` to the pinned qualification
tools, and `SDK` to the extracted composition. Give each consumer its own output base
if running them concurrently. Keep remote caching enabled where configured.
The scratch rules_rs remote-execution configuration selects a Linux host.

```bash
export BAZEL_MACOS_EXPERIMENTAL_INCLUDE_ALL_SDK_LIBS=1
sdk_flags=(--repo_env=BAZEL_MACOS_EXPERIMENTAL_INCLUDE_ALL_SDK_LIBS
           --repo_env=BAZEL_MACOS_FRAMEWORKS)
export BAZEL_MACOS_FRAMEWORKS=CoreFoundation,Foundation

cd "$HERMETIC_LLVM"
for cpu in arm64 x86_64; do
  bootstrap=(--config=release --extra_execution_platforms=@platforms//host
             "--platforms=//platforms:macos_$cpu" --//config:macos_libcxx_headers=llvm
             "${sdk_flags[@]}")
  bazel build "${bootstrap[@]}" //toolchain/bootstrap/stage2:llvm || exit 1
  bazel aquery "${bootstrap[@]}" --output=text --include_commandline \
    'inputs("llvm/lib/IR/LLVMContext[.]cpp$", mnemonic("CppCompile", deps(//toolchain/bootstrap/stage2:llvm)))' \
    > "$REPORTS/bootstrap-$cpu.actions" || exit 1
  mkdir -p "$REPORTS/$cpu/bin"
  cp -L bazel-bin/toolchain/bootstrap/stage2/llvm "$REPORTS/$cpu/bin/clang"
  resource=$("$LLVM/bin/clang" --no-default-config -print-resource-dir) || exit 1
  /usr/bin/arch "-$cpu" "$REPORTS/$cpu/bin/clang" --no-default-config \
    -target "$cpu-apple-macos11" -nostdinc -isysroot "$SDK" \
    -isystem "$resource/include" -isystem "$SDK/usr/include" \
    -c "$C_SDK_REPO/tools/llvm_build/fixtures/stage2_client.c" \
    -o "$REPORTS/$cpu/client.o" || exit 1
  "$LLVM/bin/ld64.lld" -t -Z -arch "$cpu" -platform_version macos 11 26.5 \
    -syslibroot "$SDK" -L"$SDK/usr/lib" "$REPORTS/$cpu/client.o" -lSystem \
    -o "$REPORTS/$cpu/client" > "$REPORTS/$cpu/client.link-trace" 2>&1 || exit 1
  grep -Fx "$SDK/usr/lib/libSystem.tbd(/usr/lib/libSystem.B.dylib)" \
    "$REPORTS/$cpu/client.link-trace" || exit 1
  /usr/bin/arch "-$cpu" "$REPORTS/$cpu/client" || exit 1
  "$LLVM/bin/llvm-nm" -um "$REPORTS/$cpu/client" | grep -F '_getpid (from libSystem)' || exit 1
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

Check the bootstrap action
for each target. A Stage 2 C++ compile must execute
`stage1_macos_aarch64/bin/clang++` on the macOS host. The action that builds
Stage 1 uses the minimal Darwin compiler. Both must pass the archive's
extracted sysroot. Hash its `usr/lib/libSystem.B.tbd` against the composition
receipt, inspect the produced Mach-O architecture, and use the resulting
Clang to compile and run a client on the corresponding architecture.

To establish which stubs linked Stage 1 itself, use the native compiler
link's Bazel response file from the execution root. Identify the matching
configuration by comparing the built `llvm.stripped` with the Stage 1
`bin/clang++` in the Stage 2 action. Copy the response file to the report
directory, insert `-Wl,-t`, and redirect its `-o` to a fresh directory,
retaining the filename `llvm`. Run it from the execution root with the
original link driver. Require the replay to match the unstripped Bazel
`llvm` byte for byte and the trace to name the composed sysroot's
`usr/lib/libSystem.B.tbd`. Save the trace, both comparisons and the stub
digest. The executable's load commands show the runtime install name;
the linker trace identifies the build-time stub.

Record cached versus executed tests, incompatible targets, and failures.
The macOS rules_rs command covers 39 tests in the pinned snapshot. Its
explicitly excluded target transitions over every Rust target triple and
requires a separate Windows MSVC license decision. A pass here establishes
the macOS consumer scope. For host shell scripts the test PATH selects
macOS bash and retains the user's Bazel executable for nested tests.

## Cross-link the C client on Linux

Use a scratch Bazel module pointing to the same hermetic-llvm checkout,
with its toolchains registered and the composition pinned by archive digest.
Copy [stage2_client.c](fixtures/stage2_client.c) into this module. Define
this target so that the final executable retains only the dylibs it uses.

```starlark
load("@rules_cc//cc:cc_binary.bzl", "cc_binary")

cc_binary(
    name = "getpid",
    srcs = ["stage2_client.c"],
    linkopts = ["-Wl,-dead_strip_dylibs"],
)
```

With hermetic-llvm's remote configuration imported and the same SDK
repository environment as the e2e gate, run the following from the scratch
module on the Mac. The remote platform should select a Linux worker.

```bash
for cpu in arm64 x86_64; do
  bazel build --config=remote "--platforms=@llvm//platforms:macos_$cpu" \
    --@llvm//config:macos_libcxx_headers=llvm "${sdk_flags[@]}" \
    "--execution_log_json_file=$REPORTS/linux-$cpu.json" //:getpid || exit 1
  cp -L bazel-bin/getpid "$REPORTS/linux-$cpu" || exit 1
  /usr/bin/arch "-$cpu" "$REPORTS/linux-$cpu" || exit 1
  "$LLVM/bin/llvm-nm" -um "$REPORTS/linux-$cpu" || exit 1
  otool -L "$REPORTS/linux-$cpu" || exit 1
done
```

Check the client compile and link entries in each execution log. Inspect
the runner, cache status, OSFamily and input digest for
`sysroot/usr/lib/libSystem.B.tbd`. Record the Mach-O imports and dylib
dependencies. This experiment exercises a C-only client of the complete
SDK with the normal hermetic-llvm driver.

### Isolate the standalone package

The same Linux worker can test only the standalone package and the C
installation. Give the action the unpacked archive, the generated headers,
Linux Clang and LLD, and Clang's resource headers. Use the [close
fixture](../libsystem/fixtures/close_nocancel_runtime.c) to exercise a symbol
required by the Intel Rust standard library. These commands also work in a
Linux shell with `LLVM`, `WORK`, `C_INSTALL`, `LIBSYSTEM_ARCHIVE` and
`C_SDK_REPO` set to absolute paths. Use a new work directory.

```bash
tar -xf "$LIBSYSTEM_ARCHIVE" -C "$WORK" || exit 1
sysroot="$WORK/libSystem"
cp -R "$C_INSTALL/usr/include" "$sysroot/usr/" || exit 1
resource=$("$LLVM/bin/clang" --no-default-config -print-resource-dir) || exit 1
for cpu in arm64 x86_64; do
  "$LLVM/bin/clang" --no-default-config -target "$cpu-apple-macos11" \
    -nostdinc -isysroot "$sysroot" -isystem "$resource/include" \
    -isystem "$sysroot/usr/include" -c \
    "$C_SDK_REPO/tools/libsystem/fixtures/close_nocancel_runtime.c" \
    -o "$WORK/close-$cpu.o" || exit 1
  "$LLVM/bin/ld64.lld" -Z -arch "$cpu" -platform_version macos 11 26.5 \
    -syslibroot "$sysroot" -L"$sysroot/usr/lib" "$WORK/close-$cpu.o" \
    -lSystem -o "$WORK/close-$cpu" || exit 1
done
```

On the Mac, execute each resulting binary with `/usr/bin/arch -arm64`
or `/usr/bin/arch -x86_64` and inspect the binding to `_close$NOCANCEL`
with `llvm-nm -um`.
