#include <fenv.h>

#ifdef __arm64__
_Static_assert(FE_ALL_EXCEPT == 159, "arm64 mask");
#else
_Static_assert(FE_ALL_EXCEPT == 63, "Intel mask");
#endif
