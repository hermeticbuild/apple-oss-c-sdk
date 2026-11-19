# Scalar binary16 math on macOS

The 26.5 Libm recipe adds thirteen C declarations when the compiler
supports `_Float16` on macOS arm64 or x86_64. The return and argument
types come from the pinned LLVM libc functions of the same base name.
Darwin prefixes the C names with two underscores. The linker spellings
come from compiling the installed declarations with Clang.
[LLVM libc signatures](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/libc/include/math.yaml)

The availability check compares Apple's macOS 14.7 (23H124) and initial
15.0 (24A335) full OTA releases. Identify the OS builds from the OTA
metadata, reconstruct the system cryptex from the OTA member for each
architecture, mount read-only, locate `/usr/lib/system/libsystem_m.dylib`,
then query its Mach-O export trie for the thirteen candidate names. Use
`_ceil`, `_fma`, `_rint` and `_sqrt` as positive controls on each image.
Independent inspection of the current runtime supplies the 26.5.2 control.
[Apple 14.7 OTA](https://updates.cdn-apple.com/2024FallFCS/patches/062-78774/AC2D502C-ACE3-495C-8BF3-1ABEBFE7237A/com_apple_MobileAsset_MacSoftwareUpdate/c4f586faec1ab75e54765aec2f70846c4c6d1528.zip) · [Apple 15.0 OTA](https://updates.cdn-apple.com/2024FallFCS/patches/062-78498/22C3E101-2A4E-4B47-B5AC-7C8A2D7B85F1/com_apple_MobileAsset_MacSoftwareUpdate/7d763b0793c8e214f2d9bb078a0cba7b470e57e2.zip)

| Runtime cache | 14.7 / 23H124 libm UUID (0 of 13) | 15.0 / 24A335 libm UUID (13 of 13 strong) |
| --- | --- | --- |
| Apple Silicon arm64e | `39e9dc0c-ec48-34b8-9b19-9d87f51f4e63` | `a9f7fdc9-bc69-3406-bfc0-7278591fb060` |
| Rosetta x86_64 | `5e2516f7-0c28-34c5-bd5d-43bab390df63` | `63aac0f4-3b29-34d6-9ff1-1005868112fe` |
| Intel x86_64h | `eab4229a-72c0-3e27-8acc-2d8b0ed63ec0` | `6ab6bcc3-f24d-3299-a596-e5c28497aa08` |

During offline generation the normal header scanner processes `math.h`.
The family-specific check matches the compiled spellings and AST types to
the digest of the independently reviewed ABI and assigns the strong exports
to the libsystem_m child. The digest covers sorted UTF-8 lines of the form
`<Mach-O name><TAB><LLVM C return type> (<parameter types>)<LF>`.
The scanner records the declarations, imports and header ownership. Inputs
consist of the installed C headers, the LLVM bundle and the checked-in
provider evidence. The reference SDK serves only as a qualification control.

The [runtime fixture](../../tests/installed_headers/libm_half_runtime.c)
checks each C function type, calls all thirteen functions, verifies the
provider address with `dladdr`, and prints the binary16 result bits for
comparison with the same client built using the reference SDK. Use the
following commands with `T` set to a target such as `x86_64-apple-macos15.0`.
Set `C_INSTALL` and `STUBS` to the respective generated roots.

```sh
clang="$LLVM/bin/clang"
resource=$("$clang" -print-resource-dir)
"$clang" --no-default-config -target "$T" -nostdinc -isystem "$resource/include" \
    -isystem "$C_INSTALL/usr/include" -std=c11 -D_DARWIN_C_SOURCE -fno-builtin \
    -O2 -Werror=unguarded-availability-new -c tests/installed_headers/libm_half_runtime.c -o half.o
"$LLVM/bin/llvm-nm" -mu half.o
"$clang" --no-default-config -target "$T" -nostdlib -fuse-ld=lld \
    -isysroot "$STUBS" half.o -lSystem -o half
./half
```

At minima 11.0 and 14.7 the strict compile must diagnose unguarded uses.
Repeat with `-Wno-unguarded-availability-new` to inspect all thirteen weak
imports. The imports are strong at minima 15.0 and 26.5. Both targets produced
SDK-identical objects and runtime outputs at all four minima on macOS 26.5.2.
Rosetta's deployed `__rintf16(1.25)` returned 1.25 in the control and
candidate. Historical cache inspection establishes export presence only.

With `-DTEST_HALF_WIDEN` the Intel client also imports the compiler helper
`__extendhfsf2` to print a floating-point result. The reference SDK resolves
this helper. Our generated libSystem leaves it to the compiler runtime.
The installed hermetic-llvm Intel builtins archive satisfied it at 15.0
and 26.5. The archive's minimum is 14.0. For 11.0 the pinned LLVM
`extendhfsf2.c` compiled at 11.0 satisfied the same link with fatal linker
warnings enabled. Both variants ran under Rosetta. This separate compiler
binding remains a difference for clients linking with `-nostdlib`.
[LLVM implementation](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/compiler-rt/lib/builtins/extendhfsf2.c)
