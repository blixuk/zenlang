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
ZenValue ZenValue_cast(ZenValue val, const char* target_type);
ZenValue ZenValue_coalesce(ZenValue a, ZenValue b);

// Fast primitive arithmetic, bitwise, and comparison helpers (inlined for AOT speed)
static inline ZenValue ZenValue_fast_add_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer + b.as.integer};
}
static inline ZenValue ZenValue_fast_sub_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer - b.as.integer};
}
static inline ZenValue ZenValue_fast_mul_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer * b.as.integer};
}
static inline ZenValue ZenValue_fast_div_int(ZenValue a, ZenValue b) {
    if (__builtin_expect(b.as.integer == 0, 0)) return (ZenValue){.type = ZEN_DECIMAL, .as.decimal = (double)a.as.integer / 0.0};
    if (a.as.integer % b.as.integer == 0) return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer / b.as.integer};
    return (ZenValue){.type = ZEN_DECIMAL, .as.decimal = (double)a.as.integer / (double)b.as.integer};
}
static inline ZenValue ZenValue_fast_mod_int(ZenValue a, ZenValue b) {
    if (__builtin_expect(b.as.integer == 0, 0)) return ZEN_NOTHING_VAL;
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer % b.as.integer};
}
static inline ZenValue ZenValue_fast_eq_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (a.as.integer == b.as.integer)};
}
static inline ZenValue ZenValue_fast_neq_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (a.as.integer != b.as.integer)};
}
static inline ZenValue ZenValue_fast_lt_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (a.as.integer < b.as.integer)};
}
static inline ZenValue ZenValue_fast_gt_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (a.as.integer > b.as.integer)};
}
static inline ZenValue ZenValue_fast_lte_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (a.as.integer <= b.as.integer)};
}
static inline ZenValue ZenValue_fast_gte_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (a.as.integer >= b.as.integer)};
}
static inline ZenValue ZenValue_fast_bitand_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer & b.as.integer};
}
static inline ZenValue ZenValue_fast_bitor_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer | b.as.integer};
}
static inline ZenValue ZenValue_fast_bitxor_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer ^ b.as.integer};
}
static inline ZenValue ZenValue_fast_shl_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer << b.as.integer};
}
static inline ZenValue ZenValue_fast_shr_int(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_INTEGER, .as.integer = a.as.integer >> b.as.integer};
}
static inline ZenValue ZenValue_fast_add_dec(ZenValue a, ZenValue b) {
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return (ZenValue){.type = ZEN_DECIMAL, .as.decimal = va + vb};
}
static inline ZenValue ZenValue_fast_sub_dec(ZenValue a, ZenValue b) {
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return (ZenValue){.type = ZEN_DECIMAL, .as.decimal = va - vb};
}
static inline ZenValue ZenValue_fast_mul_dec(ZenValue a, ZenValue b) {
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return (ZenValue){.type = ZEN_DECIMAL, .as.decimal = va * vb};
}
static inline ZenValue ZenValue_fast_eq_bool(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (a.as.boolean == b.as.boolean)};
}
static inline ZenValue ZenValue_fast_neq_bool(ZenValue a, ZenValue b) {
    return (ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (a.as.boolean != b.as.boolean)};
}

#endif // ZEN_OPS_H
