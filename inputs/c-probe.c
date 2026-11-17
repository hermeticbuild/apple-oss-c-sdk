// C coverage roots. Compile once as a whole and once per include, for both targets.
// Seed: https://codeberg.org/ziglang/zig/src/commit/6b0a1d8b426a9b60f999358d4b7f57aa0b231777/tools/macos-headers.c
// Zig seed differences: omit five objc/* roots (outside this C-only scope) and
// net/ipsec_offload.h (absent from macOS 26.5 SDK); add sandbox.h,
// TargetConditionals.h, and CoreFoundation/CoreFoundation.h.
// ucontext.h requires _XOPEN_SOURCE; _DARWIN_C_SOURCE retains Darwin extensions.
//
// Header-inclusion coverage (179 unique roots, not API conformance):
// Inventory editions are fixed here; newer C/POSIX editions are not counted.
//   ISO C11 (WG14 N1570, 7.1.2): 27/29; absent: threads.h, uchar.h.
//   ANSI C89 (subset of C11): 15/15.
//   POSIX.1-2017 Issue 7 (Base Definitions, Ch. 13): 79/82;
//     absent: mqueue.h, stropts.h, trace.h. 24 POSIX roots overlap C11.
//   macOS/BSD, frameworks, and other extensions: 97 additional roots.
// The five absent standard roots are absent from both the macOS 26.5 SDK and
// our pinned Clang resource headers; POSIX counts include optional facilities.
// See COVERAGE_GAPS.md for roots included here but missing from our installation.
// Clang resource headers remain compiler-owned; the counts classify requested
// include names, irrespective of whether Clang or the sysroot provides them.
// ISO C11: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf
// ANSI C89 / ISO C90: https://www.iso.org/standard/17782.html
// POSIX: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/contents.html
#define _XOPEN_SOURCE 700
#define _DARWIN_C_SOURCE 1

// ISO C11: 27/29 roots (includes all 15 ANSI C89 headers).
// https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf
// https://www.iso.org/standard/17782.html
// Unseeded: threads.h (conditional C11 feature), uchar.h. Neither is in the
// macOS 26.5 SDK or pinned Clang resource directory.
#include <assert.h>
#include <complex.h>
#include <ctype.h>
#include <errno.h>
#include <fenv.h>
#include <float.h>
#include <inttypes.h>
#include <iso646.h>
#include <limits.h>
#include <locale.h>
#include <math.h>
#include <setjmp.h>
#include <signal.h>
#include <stdalign.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdnoreturn.h>
#include <string.h>
#include <tgmath.h>
#include <time.h>
#include <wchar.h>
#include <wctype.h>

// POSIX.1-2017 Issue 7: 55 additional roots; 24 also appear above (79/82).
// https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/contents.html
// Unseeded: mqueue.h, stropts.h, trace.h. All three are specified in Chapter
// 13 but absent from the macOS 26.5 SDK and pinned Clang resource directory.
#include <aio.h>
#include <arpa/inet.h>
#include <cpio.h>
#include <dirent.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <fmtmsg.h>
#include <fnmatch.h>
#include <ftw.h>
#include <glob.h>
#include <grp.h>
#include <iconv.h>
#include <langinfo.h>
#include <libgen.h>
#include <monetary.h>
#include <ndbm.h>
#include <net/if.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <nl_types.h>
#include <poll.h>
#include <pthread.h>
#include <pwd.h>
#include <regex.h>
#include <sched.h>
#include <search.h>
#include <semaphore.h>
#include <spawn.h>
#include <strings.h>
#include <sys/ipc.h>
#include <sys/mman.h>
#include <sys/msg.h>
#include <sys/resource.h>
#include <sys/select.h>
#include <sys/sem.h>
#include <sys/shm.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/time.h>
#include <sys/times.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <sys/un.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <syslog.h>
#include <tar.h>
#include <termios.h>
#include <ulimit.h>
#include <unistd.h>
#include <utime.h>
#include <utmpx.h>
#include <wordexp.h>

// macOS/BSD, frameworks, and other extensions: 97 roots.
// Zig seed: https://codeberg.org/ziglang/zig/src/commit/6b0a1d8b426a9b60f999358d4b7f57aa0b231777/tools/macos-headers.c
// Unseeded Zig roots: objc/NSObjCRuntime.h, objc/NSObject.h, objc/message.h,
// objc/objc-runtime.h, objc/objc.h (outside C-only scope); net/ipsec_offload.h
// (absent from macOS 26.5 SDK). Three additional roots are listed above.
#include <AssertMacros.h>
#include <Block.h>
#include <CommonCrypto/CommonCrypto.h>
#include <CommonCrypto/CommonRandom.h>
#include <CoreFoundation/CoreFoundation.h>
#include <MacTypes.h>
#include <TargetConditionals.h>
#include <ar.h>
#include <copyfile.h>
#include <crt_externs.h>
#include <db.h>
#include <device/device_types.h>
#include <dispatch/dispatch.h>
#include <err.h>
#include <execinfo.h>
#include <fts.h>
#include <getopt.h>
#include <hfs/hfs_format.h>
#include <hfs/hfs_unistr.h>
#include <ifaddrs.h>
#include <libkern/OSAtomic.h>
#include <libkern/OSAtomicQueue.h>
#include <libkern/OSByteOrder.h>
#include <libkern/OSCacheControl.h>
#include <libkern/OSDebug.h>
#include <libkern/OSKextLib.h>
#include <libkern/OSReturn.h>
#include <libkern/OSThermalNotification.h>
#include <libkern/OSTypes.h>
#include <libproc.h>
#include <mach-o/arch.h>
#include <mach-o/arm/reloc.h>
#include <mach-o/arm64/reloc.h>
#include <mach-o/compact_unwind_encoding.h>
#include <mach-o/dyld.h>
#include <mach-o/dyld_images.h>
#include <mach-o/fat.h>
#include <mach-o/fixup-chains.h>
#include <mach-o/getsect.h>
#include <mach-o/ldsyms.h>
#include <mach-o/loader.h>
#include <mach-o/nlist.h>
#include <mach-o/ranlib.h>
#include <mach-o/reloc.h>
#include <mach-o/stab.h>
#include <mach-o/swap.h>
#include <mach-o/utils.h>
#include <mach-o/x86_64/reloc.h>
#include <mach/clock.h>
#include <mach/exception.h>
#include <mach/mach.h>
#include <mach/mach_time.h>
#include <mach/thread_state.h>
#include <mach/vm_param.h>
#include <malloc/malloc.h>
#include <memory.h>
#include <net/bpf.h>
#include <net/dlil.h>
#include <net/ethernet.h>
#include <net/if_arp.h>
#include <net/if_dl.h>
#include <net/if_llc.h>
#include <net/if_media.h>
#include <net/if_mib.h>
#include <net/if_types.h>
#include <net/if_utun.h>
#include <net/if_var.h>
#include <net/if_var_status.h>
#include <net/kext_net.h>
#include <net/ndrv.h>
#include <net/net_kev.h>
#include <net/pfkeyv2.h>
#include <net/route.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <os/lock.h>
#include <os/os_sync_wait_on_address.h>
#include <paths.h>
#include <sandbox.h>
#include <simd/simd.h>
#include <sys/acl.h>
#include <sys/attr.h>
#include <sys/clonefile.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/param.h>
#include <sys/paths.h>
#include <sys/random.h>
#include <sys/sysctl.h>
#include <sys/timex.h>
#include <sysexits.h>
#include <ucontext.h>
#include <vis.h>
#include <xlocale.h>
#include <xpc/xpc.h>
#include <zlib.h>

int main(void) { return 0; }
