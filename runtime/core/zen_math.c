#include "../bootstrap_runtime.h"
#include <math.h>
#include <stdlib.h>

ZenValue ZenMath_sin(ZenValue x) { return ZenValue_make_decimal(sin(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_cos(ZenValue x) { return ZenValue_make_decimal(cos(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_sqrt(ZenValue x) { return ZenValue_make_decimal(sqrt(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_floor(ZenValue x) { return ZenValue_make_decimal(floor(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_ceil(ZenValue x) { return ZenValue_make_decimal(ceil(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_abs(ZenValue x) { return (x.type == ZEN_INTEGER) ? ZenValue_make_integer(llabs(x.as.integer)) : ZenValue_make_decimal(fabs(x.as.decimal)); }
ZenValue ZenMath_min(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        return (a.as.integer < b.as.integer) ? a : b;
    }
    double da = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double db = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return (da < db) ? a : b;
}

ZenValue ZenMath_max(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        return (a.as.integer > b.as.integer) ? a : b;
    }
    double da = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double db = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return (da > db) ? a : b;
}

ZenValue ZenMath_clamp(ZenValue x, ZenValue lo, ZenValue hi) {
    return ZenMath_max(lo, ZenMath_min(x, hi));
}

ZenValue ZenMath_round(ZenValue x) {
    if (x.type == ZEN_INTEGER) return x;
    return ZenValue_make_decimal(round(x.as.decimal));
}

ZenValue ZenMath_power(ZenValue x, ZenValue y) { 
    double dx = (x.type == ZEN_INTEGER) ? (double)x.as.integer : x.as.decimal;
    double dy = (y.type == ZEN_INTEGER) ? (double)y.as.integer : y.as.decimal;
    return ZenValue_make_decimal(pow(dx, dy)); 
}
