# dyld assembly evidence for macOS 26.5

Build the two Mach-O objects from the offline source tree and generated C
installation. Supply the verified LLVM toolchain, the dyld and XNU source
root, and a local output directory.

```sh
make -f tools/libsystem/dyld-assembly.mk dyld-assembly \
  SOURCE_ROOT="$SOURCE_ROOT" LLVM="$LLVM" C_INSTALL="$C_INSTALL" WORK="$WORK"
```

The [source digests](data/macosx26.5/dyld-assembly.sha256) pin
[dyld-1378](https://github.com/apple-oss-distributions/dyld/blob/fd8d0c4d52320ebf64db34f3cb280310d905c5ae/libdyld/threadLocalHelpers.s)
and the private CPU-capability headers from
[XNU](https://github.com/apple-oss-distributions/xnu/tree/ac9718fb1af618d5ce8678d0dc6e8a58f252216f/osfmk).
The recipe maps the private `System/` include path to XNU's `osfmk` directory.
It compiles for macOS 11.0 arm64 and x86_64, verifies the Mach-O architecture
and checks that `__tlv_bootstrap` and `dyld_stub_binder` are external text
definitions. Only these two definitions appear in the symbol receipts. They
are object-level evidence. Confirm final install name, linkage and reexports
independently before using them as provider facts.

`TARGET_OS_EXCLAVEKIT=0` selects the ordinary macOS assembly path in this
dyld build. The Xcode 26.5 public `TargetConditionals.h` leaves that macro
undefined on both arm64 and x86_64. A reference-only reproduction is below.

```sh
for arch in arm64 x86_64; do
  "$LLVM/bin/clang" --no-default-config -target "$arch-apple-macos11.0" \
    -isysroot "$APPLE_SDK" -nostdinc -isystem "$APPLE_SDK/usr/include" \
    -x c -include TargetConditionals.h -E -dM - </dev/null >"$WORK/$arch-target-macros.txt" || exit
  grep '^#define TARGET_OS_OSX 1$' "$WORK/$arch-target-macros.txt" || exit
  if grep -q '^#define TARGET_OS_EXCLAVEKIT\b' "$WORK/$arch-target-macros.txt"; then
    exit 1
  fi
done
```
