#include <stdarg.h>
#include <stdio.h>
#include <string.h>

static char destination[128];

/* A known destination size and unknown input lengths exercise Darwin's
 * fortified wrappers without a reference to a private helper in the client. */
void *fortify_copy(const char *src, size_t n) { return memcpy(destination, src, n); }
void *fortify_move(const char *src, size_t n) { return memmove(destination, src, n); }
void *fortify_fill(int byte, size_t n) { return memset(destination, byte, n); }
void *fortify_copy_until(const char *src, int c, size_t n) { return memccpy(destination, src, c, n); }
char *fortify_strcpy(const char *src) { return strcpy(destination, src); }
char *fortify_strncpy(const char *src, size_t n) { return strncpy(destination, src, n); }
char *fortify_strcat(const char *src) { return strcat(destination, src); }
char *fortify_strncat(const char *src, size_t n) { return strncat(destination, src, n); }
char *fortify_stpcpy(const char *src) { return stpcpy(destination, src); }
char *fortify_stpncpy(const char *src, size_t n) { return stpncpy(destination, src, n); }
size_t fortify_strlcpy(const char *src, size_t n) { return strlcpy(destination, src, n); }
size_t fortify_strlcat(const char *src, size_t n) { return strlcat(destination, src, n); }
int fortify_sprintf(const char *src) { return sprintf(destination, "%s!", src); }
int fortify_snprintf(size_t n, const char *src) { return snprintf(destination, n, "%s!", src); }
int fortify_vsprintf(const char *format, va_list args) { return vsprintf(destination, format, args); }
int fortify_vsnprintf(size_t n, const char *format, va_list args) { return vsnprintf(destination, n, format, args); }
