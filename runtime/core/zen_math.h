#ifndef ZEN_MATH_H
#define ZEN_MATH_H

#include "zen_value.h"

ZenValue ZenMath_sin(ZenValue x);
ZenValue ZenMath_cos(ZenValue x);
ZenValue ZenMath_tan(ZenValue x);
ZenValue ZenMath_asin(ZenValue x);
ZenValue ZenMath_acos(ZenValue x);
ZenValue ZenMath_atan(ZenValue x);
ZenValue ZenMath_atan2(ZenValue y, ZenValue x);
ZenValue ZenMath_exp(ZenValue x);
ZenValue ZenMath_log(ZenValue x);
ZenValue ZenMath_sqrt(ZenValue x);
ZenValue ZenMath_floor(ZenValue x);
ZenValue ZenMath_ceil(ZenValue x);
ZenValue ZenMath_abs(ZenValue x);
ZenValue ZenMath_min(ZenValue a, ZenValue b);
ZenValue ZenMath_max(ZenValue a, ZenValue b);
ZenValue ZenMath_clamp(ZenValue x, ZenValue lo, ZenValue hi);
ZenValue ZenMath_round(ZenValue x);
ZenValue ZenMath_power(ZenValue x, ZenValue y);

#endif
