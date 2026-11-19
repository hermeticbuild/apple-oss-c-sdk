#include <float.h>
#include <math.h>

#if defined(PROBE_FLOAT)
typedef float probe_type;
#define PROBE_TRUE_MIN FLT_TRUE_MIN
#elif defined(PROBE_DOUBLE)
typedef double probe_type;
#define PROBE_TRUE_MIN DBL_TRUE_MIN
#elif defined(PROBE_LONG_DOUBLE)
typedef long double probe_type;
#define PROBE_TRUE_MIN LDBL_TRUE_MIN
#else
#error "Select PROBE_FLOAT, PROBE_DOUBLE, or PROBE_LONG_DOUBLE"
#endif

int main(void) {
    volatile probe_type inputs[] = {-0.0, PROBE_TRUE_MIN, 1.0, INFINITY, NAN};
    const int expected[] = {FP_ZERO, FP_SUBNORMAL, FP_NORMAL, FP_INFINITE, FP_NAN};
    for (unsigned i = 0; i < sizeof(inputs) / sizeof(inputs[0]); ++i) {
        if (fpclassify(inputs[i]) != expected[i]) {
            return i + 1;
        }
    }
    return 0;
}
