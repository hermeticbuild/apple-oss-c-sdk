/*
 * Curated macOS sandbox C declarations.
 *
 * Apple OSS clients (for example Security) use these APIs, but no public
 * sandbox.h source has been located in apple-oss-distributions. This is a
 * documented provenance gap, not an Apple OSS header.
 */
#ifndef _APPLE_OSS_C_SANDBOX_H_
#define _APPLE_OSS_C_SANDBOX_H_

#include <stdint.h>
#include <sys/types.h>

#define SANDBOX_NAMED 0x0001
#define SANDBOX_NAMED_EXTERNAL 0x0003

#ifdef __cplusplus
extern "C" {
#endif

int sandbox_init(const char *profile, uint64_t flags, char **errorbuf);
void sandbox_free_error(char *errorbuf);
int sandbox_check(pid_t pid, const char *operation, int type, ...);

#ifdef __cplusplus
}
#endif
#endif
