/* macOS scalar binary16 interfaces. See half_math.md for provenance. */
#if defined(__ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__) && \
    (defined(__arm64__) || defined(__x86_64__)) && defined(__FLT16_MANT_DIG__)
#include <Availability.h>
#ifdef __cplusplus
extern "C" {
#endif
extern _Float16 __ceilf16(_Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __copysignf16(_Float16, _Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __fabsf16(_Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __floorf16(_Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __fmaf16(_Float16, _Float16, _Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __fmaxf16(_Float16, _Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __fminf16(_Float16, _Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __hypotf16(_Float16, _Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __nextafterf16(_Float16, _Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __rintf16(_Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __roundf16(_Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __sqrtf16(_Float16) __API_AVAILABLE(macos(15.0));
extern _Float16 __truncf16(_Float16) __API_AVAILABLE(macos(15.0));
#ifdef __cplusplus
}
#endif
#endif
