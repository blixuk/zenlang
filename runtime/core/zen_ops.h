#ifndef ZEN_OPS_H
#define ZEN_OPS_H

#include "zen_value.h"

ZenValue ZenValue_equal(ZenValue a, ZenValue b);
ZenValue ZenValue_not_equal(ZenValue a, ZenValue b);
ZenValue ZenValue_not(ZenValue a);
ZenValue ZenValue_negate(ZenValue a);
ZenValue ZenValue_add(ZenValue a, ZenValue b);
ZenValue ZenValue_subtract(ZenValue a, ZenValue b);
ZenValue ZenValue_multiply(ZenValue a, ZenValue b);
ZenValue ZenValue_divide(ZenValue a, ZenValue b);
ZenValue ZenValue_modulo(ZenValue a, ZenValue b);
ZenValue ZenValue_power(ZenValue a, ZenValue b);
ZenValue ZenValue_less_than(ZenValue a, ZenValue b);
ZenValue ZenValue_greater_than(ZenValue a, ZenValue b);
ZenValue ZenValue_less_than_or_equal(ZenValue a, ZenValue b);
ZenValue ZenValue_greater_than_or_equal(ZenValue a, ZenValue b);
ZenValue ZenValue_and(ZenValue a, ZenValue b);
ZenValue ZenValue_or(ZenValue a, ZenValue b);
ZenValue ZenValue_xor(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_and(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_or(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_xor(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_not(ZenValue a);
ZenValue ZenValue_left_shift(ZenValue a, ZenValue b);
ZenValue ZenValue_right_shift(ZenValue a, ZenValue b);
ZenValue ZenValue_op_append(ZenValue a, ZenValue b);
ZenValue ZenValue_op_remove(ZenValue a, ZenValue b);

#endif // ZEN_OPS_H
