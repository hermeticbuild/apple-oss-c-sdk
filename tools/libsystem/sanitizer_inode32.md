# Intel sanitizer inode compatibility imports

The x86_64 hermetic-llvm ASan and TSan runtime links require eight legacy
Darwin C entry points. Compiler-rt's Darwin interceptors take the original
entry point's address using a direct C declaration. Compiling against the
generated public C headers ordinarily selects the corresponding `$INODE64`
spellings on x86_64 and the unadorned spellings on arm64.

| Runtime component | Additional x86_64 imports |
| --- | --- |
| `libsystem_c.dylib` | `getmntinfo`, `opendir`, `readdir`, `readdir_r` |
| `libsystem_kernel.dylib` | `fstat`, `fstatfs`, `stat`, `statfs` |

The [bounded source record](data/macosx26.5/sanitizer-inode32.json) pins the
actual ASan/TSan interceptor declarations, the Libc `Variant_Inode32`
target and suffix rule, and the XNU syscall generator, syscall table and
architecture maps. The Libc variant compiles the three corresponding source
files as inode32 implementations on Intel. The XNU generator emits the four
legacy x86_64 syscall entry points, including stripping the internal
`sys_` prefix from `sys_fstat`. Its x86_64 map separately emits the
`$INODE64` aliases to the wider syscalls. The arm64 map uses the base
spellings for the wider syscalls.

The producer compiles a client from the pinned interceptor signature excerpts,
requires all eight strong function imports, and adds the eight x86_64
demands and component exports. It checks both existing component slices for
conflicts and verifies the strong arm64 bases and strong x86_64 `$INODE64`
exports before adding the legacy Intel names. No C header input is needed.

Runtime inspection on macOS build 25F84 found direct strong definitions
under the named components, with distinct x86_64 addresses for each base and
`$INODE64` spelling. Paired strict links at macOS 11.0 and 26.5 compare the
producer output to reference SDK build 25F70. The original x86_64 output
fails on exactly these eight strong imports. The selected producer resolves
all eight as two-level imports through libSystem. The original and selected
arm64 link results and the x86_64 `$INODE64` exports remain identical. The
runtime and reference SDK were used only for independent qualification.
