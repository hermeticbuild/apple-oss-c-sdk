#pragma once

#ifndef CGFLOAT_DEFINED
#define CGFLOAT_DEFINED 1
#if __LP64__
typedef double CGFloat;
#else
typedef float CGFloat;
#endif
#endif

typedef struct CGPoint {
    CGFloat x;
    CGFloat y;
} CGPoint;
