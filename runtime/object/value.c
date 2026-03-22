#include "zen_object.h"

ZenValue zen_int(long long v) {
    ZenValue z;
    z.type = ZEN_INTEGER;
    z.as.integer = v;
    return z;
}

ZenValue zen_float(double v) {
    ZenValue z;
    z.type = ZEN_DECIMAL;
    z.as.decimal = v;
    return z;
}

ZenValue zen_bool(bool v) {
    ZenValue z;
    z.type = ZEN_BOOLEAN;
    z.as.boolean = v;
    return z;
}

ZenValue zen_str(const char* s) {
    ZenValue z;
    z.type = ZEN_STRING;
    z.as.string = (char*)s; // Assuming string literals or managed strings
    return z;
}

ZenValue zen_val_list(ZenList* l) {
    ZenValue z;
    z.type = ZEN_LIST;
    z.as.list = l;
    return z;
}

ZenValue ZenValue_and(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        return zen_int(a.as.integer & b.as.integer);
    }
    return Zen_nothing;
}

ZenValue ZenValue_or(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        return zen_int(a.as.integer | b.as.integer);
    }
    return Zen_nothing;
}

ZenValue ZenValue_xor(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        return zen_int(a.as.integer ^ b.as.integer);
    }
    return Zen_nothing;
}

ZenValue ZenValue_not(ZenValue a) {
    if (a.type == ZEN_INTEGER) {
        return zen_int(~a.as.integer);
    }
    return Zen_nothing;
}

ZenValue ZenValue_lshift(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        return zen_int(a.as.integer << b.as.integer);
    }
    return Zen_nothing;
}

ZenValue ZenValue_rshift(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        return zen_int(a.as.integer >> b.as.integer);
    }
    return Zen_nothing;
}

ZenValue ZenValue_mod(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) {
        return zen_int(a.as.integer % b.as.integer);
    }
    return Zen_nothing;
}
