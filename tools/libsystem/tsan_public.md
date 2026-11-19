# Public Darwin linker names required by TSan

On macOS, compiler-rt builds TSan's context and file interceptors against
plain C bindings. The LLVM 23.1.2 TSan dylib link reported five undefined
names in the offline libSystem stub. Source and consumer evidence also
support `makecontext` from the same Apple public header. All six are
strong function exports on arm64 and x86_64.
[TSan context interceptor](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/compiler-rt/lib/tsan/rtl/tsan_interceptors_mac.cpp#L450-L473) ·
[TSan file declaration](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/compiler-rt/lib/tsan/rtl/tsan_interceptors_posix.cpp#L98-L104) ·
[compiler-rt realpath interceptor](https://github.com/llvm/llvm-project/blob/85ac560262434c9ccfc0c183ec22d4138ed647fb/compiler-rt/lib/sanitizer_common/sanitizer_common_interceptors.inc#L4073-L4094)

| Mach-O names | Provider | Source and client behavior |
| --- | --- | --- |
| `_getcontext`, `_makecontext`, `_setcontext`, `_swapcontext` | `libsystem_platform` | The Apple build loads the architecture-specific ucontext archives. The installed `ucontext.h` exposes the deprecated declarations when the caller defines `_XOPEN_SOURCE`. |
| `_realpath` | `libsystem_c` | Libc selects its base-name implementation separately from the Darwin extension variant. A POSIX-mode public `stdlib.h` consumer emits the base name. |
| `_fileno_unlocked` | `libsystem_c` | Libc implements the function explicitly. The public Darwin `stdio.h` supplies an inline macro for ordinary callers. TSan provides its own C declaration for the external function. |

[Apple ucontext header](https://github.com/apple-oss-distributions/libplatform/blob/b7ed7cf5cf7dd12b98672435db2225a860f199d8/include/ucontext.h#L30-L53) ·
[Apple archive and link selection](https://github.com/apple-oss-distributions/libplatform/blob/b7ed7cf5cf7dd12b98672435db2225a860f199d8/xcodeconfig/libplatform.xcconfig#L71-L98) ·
[Libc realpath declarations](https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/include/_stdlib.h#L287-L307) ·
[Libc realpath build flag](https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/Libc.xcodeproj/project.pbxproj#L731) ·
[Libc variants](https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/xcodescripts/variants.xcconfig) ·
[Libc fileno implementation](https://github.com/apple-oss-distributions/Libc/blob/4e34d0559e3a1b081afeb8604d9e204a1f31321d/stdio/FreeBSD/fileno.c#L38-L65)

The recipe verifies the reviewed Apple build inputs and the pinned
compiler-rt source files, then compiles the installed-header probes
with Clang. It extracts the fileno declaration straight from
compiler-rt. The source fixture compiles in context, POSIX realpath,
Darwin realpath, and fileno modes and verifies the exact strong
imports by architecture. The Darwin realpath mode requires
`_realpath$DARWIN_EXTSN`. The package adds the base name while the
existing header-derived variant stays available. The header installation
already provides all modes exercised here.
[Input digests and implementation paths](data/macosx26.5/tsan-public.json) ·
[Compile and executable fixture](fixtures/tsan_public.cpp)

## Qualification

At deployment minima 11.0 and 26.5, the original package had six
unresolved symbols across the three relevant strict link probes.
Pinned LLD 23.1.2 linked the repaired package and macOS 26.5 SDK (25F70)
with the same strong imports, dependencies and deployment metadata.
The Darwin realpath probe linked identically on the original package,
the repaired package and the reference. Both C header trees compile
the `fileno_unlocked` macro without an external import.

The fixture's executable mode ran on macOS 26.5.2 (25F84) on native arm64
and Rosetta x86_64. It creates, swaps and explicitly restores a
context, resolves the root path with the POSIX realpath binding, and
checks that the fileno function and macro report the same descriptor.
Local `dyld_info` found all six exports in their named providers.

| Provider | arm64e UUID | x86_64 UUID |
| --- | --- | --- |
| `libsystem_platform` | `160FD864-8D15-36FC-9E97-9725388CFAFE` | `F3F23067-F027-32D5-9EE5-F93879D69602` |
| `libsystem_c` | `694B7881-1BF3-3D0F-8F19-B50AE4E8EF8A` | `29997E25-BF1B-37BB-8801-AFD1054B8639` |
