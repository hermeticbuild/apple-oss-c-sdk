#ifdef SCAN_REENTER_ROOT
extern int scan_reentered(void);
#else
#define SCAN_REENTER_ROOT
#include <reentrant-root.h>
#undef SCAN_REENTER_ROOT
#define SCAN_INCLUDE_CONTEXT
#include <context-only.h>
#undef SCAN_INCLUDE_CONTEXT
#endif
