#include <libDER/DERItem.h>
#include <xpc/xpc.h>

_Static_assert(__builtin_types_compatible_p(xpc_object_t, void *), "XPC C object type");
_Static_assert(sizeof(DERItem) == 16, "DER item layout");
