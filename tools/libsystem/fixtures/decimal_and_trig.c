double decimal_exp(double x) { return __builtin_pow(10.0, x); }
float decimal_expf(float x) { return __builtin_powf(10.0f, x); }

void sincos_pair(double x, double *restrict result) {
    result[0] = __builtin_sin(x);
    result[1] = __builtin_cos(x);
}

void sincos_pairf(float x, float *restrict result) {
    result[0] = __builtin_sinf(x);
    result[1] = __builtin_cosf(x);
}
