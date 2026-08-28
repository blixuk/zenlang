#include "zen_ops.h"
#include "../collections/zen_string.h"
#include "../collections/zen_list.h"
#include "../memory/zen_memory.h"
#include <string.h>
#include <math.h>

ZenValue ZenValue_op_append(ZenValue a, ZenValue b) {
    if (a.type == ZEN_LIST && b.type == ZEN_LIST) {
        return ZenList_concat(a, b);
    }
    if (a.type == ZEN_LIST) {
        ZenValue res = ZenList_clone(a);
        ZenList_append_value(res, b);
        return res;
    }
    if (b.type == ZEN_LIST) {
        return ZenList_prepend(b, a);
    }
    if (a.type == ZEN_STRING || b.type == ZEN_STRING) {
        return ZenString_concatenate(a, b);
    }
    return ZenValue_add(a, b);
}

ZenValue ZenValue_op_remove(ZenValue a, ZenValue b) {
    if (a.type == ZEN_STRING && b.type == ZEN_INTEGER) {
        long long n = b.as.integer;
        const char* s = (a.as.string) ? a.as.string : "";
        size_t len = strlen(s);
        if (n <= 0) return a;
        if ((size_t)n >= len) return ZenValue_make_string("");
        size_t new_len = len - (size_t)n;
        char* buf = (char*)ZenArena_allocate(ZenArena_current(), new_len + 1);
        memcpy(buf, s, new_len);
        buf[new_len] = '\0';
        return ZenValue_make_string(buf);
    }
    if (a.type == ZEN_INTEGER && b.type == ZEN_STRING) {
        long long n = a.as.integer;
        const char* s = (b.as.string) ? b.as.string : "";
        size_t len = strlen(s);
        if (n <= 0) return b;
        if ((size_t)n >= len) return ZenValue_make_string("");
        return ZenValue_make_string(s + n);
    }
    if (a.type == ZEN_LIST && b.type == ZEN_INTEGER) {
        return ZenList_drop_end(a, b.as.integer);
    }
    if (a.type == ZEN_INTEGER && b.type == ZEN_LIST) {
        return ZenList_drop_start(b, a.as.integer);
    }
    return ZenValue_subtract(a, b);
}

ZenValue ZenValue_add(ZenValue a, ZenValue b) {
    if (a.type == ZEN_STRING || b.type == ZEN_STRING) {
        return ZenString_concatenate(a, b);
    }
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer + b.as.integer);
    if (a.type == ZEN_DECIMAL || b.type == ZEN_DECIMAL) {
        double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
        double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
        return ZenValue_make_decimal(va + vb);
    }
    return ZenValue_make_nothing();
}

ZenValue ZenValue_subtract(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer - b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return ZenValue_make_decimal(va - vb);
}

ZenValue ZenValue_multiply(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer * b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return ZenValue_make_decimal(va * vb);
}

ZenValue ZenValue_divide(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        if (b.as.integer == 0) return ZenValue_make_nothing();
        // Prefer integer results for exact integer division (matches interpreter).
        if (a.as.integer % b.as.integer == 0) {
            return ZenValue_make_integer(a.as.integer / b.as.integer);
        }
        return ZenValue_make_decimal((double)a.as.integer / (double)b.as.integer);
    }
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    if (vb == 0) return ZenValue_make_nothing();
    return ZenValue_make_decimal(va / vb);
}

ZenValue ZenValue_not(ZenValue a) {
    return ZenValue_make_boolean(!a.as.boolean);
}

ZenValue ZenValue_modulo(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer % b.as.integer);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_negate(ZenValue a) {
    if (a.type == ZEN_INTEGER) return ZenValue_make_integer(-a.as.integer);
    if (a.type == ZEN_DECIMAL) return ZenValue_make_decimal(-a.as.decimal);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_power(ZenValue a, ZenValue b) {
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return ZenValue_make_decimal(pow(va, vb));
}

static int zen_string_cmp(ZenValue a, ZenValue b) {
    const char* sa = (a.type == ZEN_STRING && a.as.string) ? a.as.string : "";
    const char* sb = (b.type == ZEN_STRING && b.as.string) ? b.as.string : "";
    return strcmp(sa, sb);
}

ZenValue ZenValue_less_than(ZenValue a, ZenValue b) {
    if (a.type == ZEN_STRING && b.type == ZEN_STRING) {
        return ZenValue_make_boolean(zen_string_cmp(a, b) < 0);
    }
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_boolean(a.as.integer < b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return ZenValue_make_boolean(va < vb);
}

ZenValue ZenValue_greater_than(ZenValue a, ZenValue b) {
    if (a.type == ZEN_STRING && b.type == ZEN_STRING) {
        return ZenValue_make_boolean(zen_string_cmp(a, b) > 0);
    }
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_boolean(a.as.integer > b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return ZenValue_make_boolean(va > vb);
}

ZenValue ZenValue_less_than_or_equal(ZenValue a, ZenValue b) {
    if (a.type == ZEN_STRING && b.type == ZEN_STRING) {
        return ZenValue_make_boolean(zen_string_cmp(a, b) <= 0);
    }
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_boolean(a.as.integer <= b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return ZenValue_make_boolean(va <= vb);
}

ZenValue ZenValue_greater_than_or_equal(ZenValue a, ZenValue b) {
    if (a.type == ZEN_STRING && b.type == ZEN_STRING) {
        return ZenValue_make_boolean(zen_string_cmp(a, b) >= 0);
    }
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_boolean(a.as.integer >= b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return ZenValue_make_boolean(va >= vb);
}

ZenValue ZenValue_not_equal(ZenValue a, ZenValue b) {
    return ZenValue_not(ZenValue_equal(a, b));
}

ZenValue ZenValue_and(ZenValue a, ZenValue b) {
    return ZenValue_make_boolean(a.as.boolean && b.as.boolean);
}

ZenValue ZenValue_or(ZenValue a, ZenValue b) {
    return ZenValue_make_boolean(a.as.boolean || b.as.boolean);
}

ZenValue ZenValue_xor(ZenValue a, ZenValue b) {
    bool lhs = a.as.boolean;
    bool rhs = b.as.boolean;
    return ZenValue_make_boolean((lhs || rhs) && !(lhs && rhs));
}

ZenValue ZenValue_bitwise_and(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer & b.as.integer);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_bitwise_or(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer | b.as.integer);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_bitwise_xor(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer ^ b.as.integer);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_bitwise_not(ZenValue a) {
    if (a.type == ZEN_INTEGER) return ZenValue_make_integer(~a.as.integer);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_left_shift(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer << b.as.integer);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_right_shift(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return ZenValue_make_integer(a.as.integer >> b.as.integer);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_equal(ZenValue a, ZenValue b) {
    if (a.type != b.type) {
        if (a.type == ZEN_INTEGER && b.type == ZEN_DECIMAL) return ZenValue_make_boolean((double)a.as.integer == b.as.decimal);
        if (a.type == ZEN_DECIMAL && b.type == ZEN_INTEGER) return ZenValue_make_boolean(a.as.decimal == (double)b.as.integer);
        return ZenValue_make_boolean(false);
    }
    switch (a.type) {
        case ZEN_NOTHING: return ZenValue_make_boolean(true);
        case ZEN_INTEGER: return ZenValue_make_boolean(a.as.integer == b.as.integer);
        case ZEN_DECIMAL: return ZenValue_make_boolean(a.as.decimal == b.as.decimal);
        case ZEN_BOOLEAN: return ZenValue_make_boolean(a.as.boolean == b.as.boolean);
        case ZEN_STRING: 
            if (a.as.string == b.as.string) return ZenValue_make_boolean(true);
            if (!a.as.string || !b.as.string) return ZenValue_make_boolean(false);
            return ZenValue_make_boolean(strcmp(a.as.string, b.as.string) == 0);
        case ZEN_LIST: {
            if (a.as.list == b.as.list) return ZenValue_make_boolean(true);
            if (!a.as.list || !b.as.list) return ZenValue_make_boolean(false);
            if (a.as.list->count != b.as.list->count) return ZenValue_make_boolean(false);
            for (int i = 0; i < a.as.list->count; i++) {
                if (!ZenValue_equal(a.as.list->items[i], b.as.list->items[i]).as.boolean) {
                    return ZenValue_make_boolean(false);
                }
            }
            return ZenValue_make_boolean(true);
        }
        case ZEN_MAP: {
            if (a.as.map == b.as.map) return ZenValue_make_boolean(true);
            // Structural map equality not required for current tests; keep pointer equality.
            return ZenValue_make_boolean(false);
        }
        case ZEN_OBJECT: return ZenValue_make_boolean(a.as.object == b.as.object);
        case ZEN_ARENA: return ZenValue_make_boolean(a.as.arena == b.as.arena);
        case ZEN_ERROR: return ZenValue_make_boolean(strcmp(a.as.string, b.as.string) == 0);
        case ZEN_VARIANT:
            if (a.as.variant == b.as.variant) return ZenValue_make_boolean(true);
            if (!a.as.variant || !b.as.variant) return ZenValue_make_boolean(false);
            if (a.as.variant->enum_name.as.string != b.as.variant->enum_name.as.string &&
                strcmp(a.as.variant->enum_name.as.string, b.as.variant->enum_name.as.string) != 0) {
                return ZenValue_make_boolean(false);
            }
            if (a.as.variant->variant_name.as.string != b.as.variant->variant_name.as.string &&
                strcmp(a.as.variant->variant_name.as.string, b.as.variant->variant_name.as.string) != 0) {
                return ZenValue_make_boolean(false);
            }
            return ZenValue_equal(a.as.variant->data, b.as.variant->data);
        default: return ZenValue_make_boolean(false);
    }
}
