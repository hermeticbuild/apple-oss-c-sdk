#ifndef SCAN_INCLUDE_CONTEXT
#error "context-only.h must be included through context-root.h"
#endif
#ifdef __OBJC__
#error "scan this header in C mode"
#endif

extern int scan_context_only(void);
