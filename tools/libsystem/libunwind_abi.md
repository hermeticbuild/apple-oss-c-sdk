# Public macOS libunwind linker interface

Clang lowers an exception cleanup landing pad to a call to `_Unwind_Resume`.
On Mach-O the compiler emits the undefined name `__Unwind_Resume` even
in translation units that omit the unwind headers. The rules_rs bootstrap process wrapper
hit this failure when the stand-alone libSystem stub had an empty libunwind
component.
[Itanium exception-handling ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi-eh.html) ·
[LLVM landing-pad lowering](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/llvm/lib/CodeGen/DwarfEHPrepare.cpp#L208-L269)

Apple libunwind-201 selects the shared build for each XBS architecture
and installs its dylib in `/usr/lib/system`. The shared cache selects the
Apple system configuration. Its CMake rules generate the dylib from
the source definitions and their visibility. The subsequent strip step
removes debug symbols. The build also copies the source include tree for
its public clients.
[Apple install script](https://github.com/apple-oss-distributions/libunwind/blob/f709eccad023ec32db53d40146d07805cf3e4ee0/libunwind/apple-install-libunwind.sh) ·
[Shared build cache](https://github.com/apple-oss-distributions/libunwind/blob/f709eccad023ec32db53d40146d07805cf3e4ee0/libunwind/cmake/caches/Apple-shared.cmake) ·
[Shared library rules](https://github.com/apple-oss-distributions/libunwind/blob/f709eccad023ec32db53d40146d07805cf3e4ee0/libunwind/src/CMakeLists.txt)

The release lock's `libunwind_source` directory contains the pinned Apple
input. The producer compiles a typed client of the reviewed public
`unwind.h` and `libunwind.h` declarations with each macOS target and
uses that object's exact Mach-O imports to select the names. The
compiler cleanup fixture independently exercises the implicit
`__Unwind_Resume` reference. The producer verifies the selected exports
and their section kinds against compiled Apple source definitions. It
preserves the libSystem reexport graph and records the implementation
source of every selected name. The pinned headers are build inputs to
the recipe. The C header installation remains unchanged.
[Pinned source inputs](data/macosx26.5/libunwind-abi.json) ·
[Typed public client](fixtures/libunwind_public.c) ·
[Compiler cleanup client](fixtures/libunwind_cleanup.cpp)

The `libunwind.cpp` compilation is a native definition probe. Apple's
XBS cache enables cross-unwind, but the published source header lacks
the ARM32 compact-unwind constants that the cross-unwind build uses.
An independent build of unchanged Apple sources with the pinned LLVM
LLDB decoder's enum supplied separately produced the same public
symbol names and kinds on both targets. The LLVM ARM emitter uses a
different floating-point register-count mask from LLDB. ARM32
cross-unwind behavior remains unqualified. The installed product is
the link stub.
[Apple cross-unwind setting](https://github.com/apple-oss-distributions/libunwind/blob/f709eccad023ec32db53d40146d07805cf3e4ee0/libunwind/cmake/caches/Apple.cmake#L3-L11) ·
[LLDB ARM32 decoder](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/lldb/source/Symbol/CompactUnwindInfo.cpp#L116-L137) ·
[LLVM ARM emitter](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/llvm/lib/Target/ARM/MCTargetDesc/ARMAsmBackend.cpp#L1150-L1172)

## Qualification

The macOS 26.5 SDK (25F70) and host caches (26.5.2, 25F84) each expose
43 names from libunwind on both architecture slices. The baseline
provided zero and failed to resolve all 32 public fixture references.
The public fixture selects 31 strong functions and one strong data symbol
(`_unw_local_addr_space`) per target. All 32 were found in
`/usr/lib/system/libunwind.dylib` in the arm64e image
`FC8F0C4E-6FB0-3E27-ABEF-B0FA720CD5E4` and Rosetta x86_64 image
`694AECEA-E97F-3DEA-B1FE-406E42893B86`. The SDK and both caches agree on all names selected by the fixture.

With pinned LLD 23.1.2 at deployment minima 11.0 and 26.5, the
candidate and reference links agreed on strict imports, dependencies, and
deployment metadata. The C++ executable linked and ran on both native
arm64 and Rosetta x86_64 against each stub, using a separate libc++ stub.
The negative controls `___unw_getcontext` and `___register_frame_info`
were undefined against both candidate and reference.

## Relative-base binary compatibility

Rust's panic personality keeps relocations for both
`__Unwind_GetDataRelBase` and `__Unwind_GetTextRelBase`. It calls the
corresponding closures only when decoding data-relative or text-relative DWARF
addresses. Darwin does not support those encodings. Apple's installed
`unwind.h` marks both functions unavailable and the implementations abort if
called. The separate [compatibility fixture](fixtures/libunwind_relative_bases.S)
emits address relocations, and the recipe verifies their strong text
definitions in the pinned Apple source. The build receipt lists these two in
`compatibility_exports` alongside the 32 supported exports.
[Rust 1.96.1 personality](https://github.com/rust-lang/rust/blob/31fca3adb283cc9dfd56b49cdee9a96eb9c96ffd/library/std/src/sys/personality/gcc.rs) ·
[Rust pointer-encoding dispatch](https://github.com/rust-lang/rust/blob/31fca3adb283cc9dfd56b49cdee9a96eb9c96ffd/library/std/src/sys/personality/dwarf/eh.rs) ·
[Apple header and source](https://github.com/apple-oss-distributions/libunwind/blob/f709eccad023ec32db53d40146d07805cf3e4ee0/libunwind/include/unwind.h#L349-L355) ·
[Apple compatibility definitions](https://github.com/apple-oss-distributions/libunwind/blob/f709eccad023ec32db53d40146d07805cf3e4ee0/libunwind/src/UnwindLevel1-gcc-ext.c#L67-L84)

Strict links at deployment minima 11.0, 14.0, and 26.5 confirm that both
names bind via libSystem on arm64 and x86_64 with the generated stub and
SDK 26.5. The baseline lacked both exports. Disassembly of both 25F84
runtime images confirms that both functions end in a call to `abort`.
The probes link the relocations without calling either function.

Nine reference exports remain open per target.

- `__ZN9libunwind25findDynamicUnwindSectionsEPvP27unw_dynamic_unwind_sections`
- `___unw_add_dynamic_eh_frame_section` and `___unw_remove_dynamic_eh_frame_section`
- `___unw_add_dynamic_fde` and `___unw_remove_dynamic_fde`
- `___unw_add_find_dynamic_unwind_sections` and `___unw_remove_find_dynamic_unwind_sections`
- `_unw_iterate_dwarf_unwind_cache` and `_unw_resume_with_frames_walked`
