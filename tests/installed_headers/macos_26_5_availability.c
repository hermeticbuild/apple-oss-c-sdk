#include <Availability.h>

_Static_assert(__MAC_26_5 == 260500, "missing macOS 26.5 availability constant");
_Static_assert(__MAC_OS_X_VERSION_MAX_ALLOWED == 260500, "wrong macOS SDK availability ceiling");
_Static_assert(__MAC_OS_X_VERSION_MIN_REQUIRED == __ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__,
               "SDK availability ceiling changed the deployment minimum");
#ifdef __MAC_26_6
#error "macOS 26.5 headers expose a newer SDK's availability constant"
#endif
