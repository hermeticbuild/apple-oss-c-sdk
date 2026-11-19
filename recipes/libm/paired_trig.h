/* Paired trigonometric functions on 64-bit macOS. See paired_trig.md. */
#if defined(__ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__) && \
    (defined(__arm64__) || defined(__x86_64__))
#include <sys/cdefs.h>

#ifdef __cplusplus
extern "C" {
#endif

#if __ENVIRONMENT_MAC_OS_X_VERSION_MIN_REQUIRED__ >= 1090
struct __float2 {
    float __sinval;
    float __cosval;
};

struct __double2 {
    double __sinval;
    double __cosval;
};

extern struct __double2 __sincos_stret(double);
extern struct __float2 __sincosf_stret(float);
extern struct __double2 __sincospi_stret(double);
extern struct __float2 __sincospif_stret(float);

__header_always_inline void
__sincos(double angle, double *sine, double *cosine)
{
    struct __double2 pair = __sincos_stret(angle);
    *sine = pair.__sinval;
    *cosine = pair.__cosval;
}

__header_always_inline void
__sincosf(float angle, float *sine, float *cosine)
{
    struct __float2 pair = __sincosf_stret(angle);
    *sine = pair.__sinval;
    *cosine = pair.__cosval;
}

__header_always_inline void
__sincospi(double half_turns, double *sine, double *cosine)
{
    struct __double2 pair = __sincospi_stret(half_turns);
    *sine = pair.__sinval;
    *cosine = pair.__cosval;
}

__header_always_inline void
__sincospif(float half_turns, float *sine, float *cosine)
{
    struct __float2 pair = __sincospif_stret(half_turns);
    *sine = pair.__sinval;
    *cosine = pair.__cosval;
}
#else
__header_always_inline void
__sincos(double angle, double *sine, double *cosine)
{
    *sine = sin(angle);
    *cosine = cos(angle);
}

__header_always_inline void
__sincosf(float angle, float *sine, float *cosine)
{
    *sine = sinf(angle);
    *cosine = cosf(angle);
}
#endif

#ifdef __cplusplus
}
#endif
#endif
