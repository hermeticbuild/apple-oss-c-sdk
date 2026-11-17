#include <sandbox.h>

int (*init_fn)(const char *, uint64_t, char **) = sandbox_init;
