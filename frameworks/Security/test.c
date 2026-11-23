#include <Security/Authorization.h>

_Static_assert(__builtin_types_compatible_p(AuthorizationRef, const struct AuthorizationOpaqueRef *),
               "AuthorizationRef");
