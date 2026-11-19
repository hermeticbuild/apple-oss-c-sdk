#include <TargetConditionals.h>

#if !TARGET_OS_MAC || TARGET_OS_LINUX || TARGET_OS_UNIX
#error wrong macOS target flags
#endif

#if defined(__aarch64__)
#if !TARGET_CPU_ARM64 || TARGET_CPU_X86_64
#error wrong arm64 target flags
#endif
#elif defined(__x86_64__)
#if TARGET_CPU_ARM64 || !TARGET_CPU_X86_64
#error wrong x86_64 target flags
#endif
#else
#error unsupported target architecture
#endif
