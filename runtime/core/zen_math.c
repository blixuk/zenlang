#include "../bootstrap_runtime.h"
#include <math.h>
#include <stdlib.h>

ZenValue ZenMath_sin(ZenValue x) { return ZenValue_make_decimal(sin(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_cos(ZenValue x) { return ZenValue_make_decimal(cos(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_sqrt(ZenValue x) { return ZenValue_make_decimal(sqrt(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_floor(ZenValue x) { return ZenValue_make_decimal(floor(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_ceil(ZenValue x) { return ZenValue_make_decimal(ceil(x.type == ZEN_INTEGER ? (double)x.as.integer : x.as.decimal)); }
ZenValue ZenMath_abs(ZenValue x) { return (x.type == ZEN_INTEGER) ? ZenValue_make_integer(llabs(x.as.integer)) : ZenValue_make_decimal(fabs(x.as.decimal)); }
ZenValue ZenMath_power(ZenValue x, ZenValue y) { 
    double dx = (x.type == ZEN_INTEGER) ? (double)x.as.integer : x.as.decimal;
    double dy = (y.type == ZEN_INTEGER) ? (double)y.as.integer : y.as.decimal;
    return ZenValue_make_decimal(pow(dx, dy)); 
}
