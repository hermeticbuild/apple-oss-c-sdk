#ifndef SCAN_SURFACE_H
#define SCAN_SURFACE_H
#include <details.h>

extern int scan_function(void);
extern int scan_data;
extern _Thread_local int scan_tls;
extern int scan_alias(void) __asm("_scan_macho_alias");
extern int scan_weak(void) __attribute__((weak_import));
extern int scan_later(void) __attribute__((availability(macos, introduced=12.0)));

static inline int scan_static_inline(void) { return 0; }
inline int scan_c_inline(void) { return scan_function(); }
extern int scan_hidden(void) __attribute__((visibility("hidden")));
extern int scan_unavailable(void) __attribute__((availability(macos, unavailable)));

#ifdef _DARWIN_C_SOURCE
extern int scan_profile(void) __asm("_scan_profile$DARWIN_EXTSN");
#else
extern int scan_profile(void);
#endif
#endif
