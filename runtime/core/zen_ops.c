#include "zen_ops.h"
#include "zen_variant.h"
#include "../collections/zen_string.h"
#include "../collections/zen_list.h"
#include "../collections/zen_map.h"
#include "../collections/zen_set.h"
#include "../memory/zen_memory.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
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

static inline int64_t zen_to_int64(ZenValue v) {
    if (v.type == ZEN_INTEGER) return v.as.integer;
    if (v.type == ZEN_DECIMAL) return (int64_t)v.as.decimal;
    if (v.type == ZEN_BOOLEAN) return v.as.boolean ? 1 : 0;
    if (v.type == ZEN_STRING && v.as.string) return atoll(v.as.string);
    return 0;
}

ZenValue ZenValue_bitwise_and(ZenValue a, ZenValue b) {
    if ((a.type == ZEN_INTEGER || a.type == ZEN_DECIMAL) && (b.type == ZEN_INTEGER || b.type == ZEN_DECIMAL)) {
        return ZenValue_make_integer(zen_to_int64(a) & zen_to_int64(b));
    }
    return ZenValue_make_nothing();
}

ZenValue ZenValue_bitwise_or(ZenValue a, ZenValue b) {
    if ((a.type == ZEN_INTEGER || a.type == ZEN_DECIMAL) && (b.type == ZEN_INTEGER || b.type == ZEN_DECIMAL)) {
        return ZenValue_make_integer(zen_to_int64(a) | zen_to_int64(b));
    }
    return ZenValue_make_nothing();
}

ZenValue ZenValue_bitwise_xor(ZenValue a, ZenValue b) {
    if ((a.type == ZEN_INTEGER || a.type == ZEN_DECIMAL) && (b.type == ZEN_INTEGER || b.type == ZEN_DECIMAL)) {
        return ZenValue_make_integer(zen_to_int64(a) ^ zen_to_int64(b));
    }
    return ZenValue_make_nothing();
}

ZenValue ZenValue_bitwise_not(ZenValue a) {
    if (a.type == ZEN_INTEGER || a.type == ZEN_DECIMAL) {
        return ZenValue_make_integer(~zen_to_int64(a));
    }
    return ZenValue_make_nothing();
}

ZenValue ZenValue_left_shift(ZenValue a, ZenValue b) {
    if ((a.type == ZEN_INTEGER || a.type == ZEN_DECIMAL) && (b.type == ZEN_INTEGER || b.type == ZEN_DECIMAL)) {
        return ZenValue_make_integer(zen_to_int64(a) << zen_to_int64(b));
    }
    return ZenValue_make_nothing();
}

ZenValue ZenValue_right_shift(ZenValue a, ZenValue b) {
    if ((a.type == ZEN_INTEGER || a.type == ZEN_DECIMAL) && (b.type == ZEN_INTEGER || b.type == ZEN_DECIMAL)) {
        return ZenValue_make_integer(zen_to_int64(a) >> zen_to_int64(b));
    }
    return ZenValue_make_nothing();
}

ZenValue ZenValue_equal(ZenValue a, ZenValue b) {
    if (a.type == ZEN_DEFAULT && b.type == ZEN_DEFAULT) return ZenValue_make_boolean(true);
    if (a.type == ZEN_DEFAULT) {
        switch (b.type) {
            case ZEN_INTEGER: return ZenValue_make_boolean(b.as.integer == 0);
            case ZEN_DECIMAL: return ZenValue_make_boolean(b.as.decimal == 0.0);
            case ZEN_BOOLEAN: return ZenValue_make_boolean(b.as.boolean == false);
            case ZEN_STRING:  return ZenValue_make_boolean(!b.as.string || b.as.string[0] == '\0');
            case ZEN_LIST:    return ZenValue_make_boolean(!b.as.list || b.as.list->count == 0);
            case ZEN_MAP:     return ZenValue_make_boolean(!b.as.map || b.as.map->count == 0);
            default: return ZenValue_make_boolean(false);
        }
    }
    if (b.type == ZEN_DEFAULT) {
        switch (a.type) {
            case ZEN_INTEGER: return ZenValue_make_boolean(a.as.integer == 0);
            case ZEN_DECIMAL: return ZenValue_make_boolean(a.as.decimal == 0.0);
            case ZEN_BOOLEAN: return ZenValue_make_boolean(a.as.boolean == false);
            case ZEN_STRING:  return ZenValue_make_boolean(!a.as.string || a.as.string[0] == '\0');
            case ZEN_LIST:    return ZenValue_make_boolean(!a.as.list || a.as.list->count == 0);
            case ZEN_MAP:     return ZenValue_make_boolean(!a.as.map || a.as.map->count == 0);
            default: return ZenValue_make_boolean(false);
        }
    }
    if (a.type != b.type) {
        if (a.type == ZEN_INTEGER && b.type == ZEN_DECIMAL) return ZenValue_make_boolean((double)a.as.integer == b.as.decimal);
        if (a.type == ZEN_DECIMAL && b.type == ZEN_INTEGER) return ZenValue_make_boolean(a.as.decimal == (double)b.as.integer);
        return ZenValue_make_boolean(false);
    }
    switch (a.type) {
        case ZEN_DEFAULT: return ZenValue_make_boolean(true);
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
            if (!a.as.map || !b.as.map) return ZenValue_make_boolean(false);
            if (a.as.map->count != b.as.map->count) return ZenValue_make_boolean(false);
            for (int i = 0; i < a.as.map->count; i++) {
                ZenValue k = a.as.map->entries[i].key;
                ZenValue v_a = a.as.map->entries[i].value;
                int idx_b = -1;
                for (int j = 0; j < b.as.map->count; j++) {
                    if (ZenValue_equal(b.as.map->entries[j].key, k).as.boolean) {
                        idx_b = j;
                        break;
                    }
                }
                if (idx_b < 0) return ZenValue_make_boolean(false);
                if (!ZenValue_equal(v_a, b.as.map->entries[idx_b].value).as.boolean) {
                    return ZenValue_make_boolean(false);
                }
            }
            return ZenValue_make_boolean(true);
        }
        case ZEN_SET: {
            if (a.as.set == b.as.set) return ZenValue_make_boolean(true);
            if (!a.as.set || !b.as.set) return ZenValue_make_boolean(false);
            return ZenValue_equal(a.as.set->list, b.as.set->list);
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

ZenValue ZenValue_cast(ZenValue val, const char* target_type) {
    if (!target_type) return val;
    
    /* 1. Target: Integer / Int */
    if (strcmp(target_type, "Integer") == 0 || strcmp(target_type, "Int") == 0 ||
        strcmp(target_type, "Int64") == 0 || strcmp(target_type, "Int32") == 0 ||
        strcmp(target_type, "Int16") == 0 || strcmp(target_type, "Int8") == 0 ||
        strcmp(target_type, "Byte") == 0) {
        if (val.type == ZEN_INTEGER) return val;
        if (val.type == ZEN_DECIMAL) return ZenValue_make_integer((long long)val.as.decimal);
        if (val.type == ZEN_BOOLEAN) return ZenValue_make_integer(val.as.boolean ? 1 : 0);
        if (val.type == ZEN_STRING) {
            if (!val.as.string || val.as.string[0] == '\0') return ZenValue_make_integer(0);
            const char* s = val.as.string;
            while (*s == ' ' || *s == '\t') s++;
            if (*s == '\0') return ZenValue_make_integer(0);
            char* endptr = NULL;
            long long res = strtoll(s, &endptr, 0);
            if (endptr == s) {
                /* Single character codepoint */
                if (strlen(s) == 1) return ZenValue_make_integer((unsigned char)s[0]);
                return ZenValue_make_integer(0);
            }
            return ZenValue_make_integer(res);
        }
        if (val.type == ZEN_LIST) return ZenValue_make_integer(val.as.list ? val.as.list->count : 0);
        if (val.type == ZEN_MAP) return ZenValue_make_integer(val.as.map ? val.as.map->count : 0);
        if (val.type == ZEN_SET) return ZenValue_make_integer(ZenSet_get_count(val));
        if (val.type == ZEN_NOTHING) return ZenValue_make_integer(0);
        return ZenValue_make_integer(0);
    }
    
    /* 2. Target: Decimal / Float / Double */
    if (strcmp(target_type, "Decimal") == 0 || strcmp(target_type, "Float") == 0 ||
        strcmp(target_type, "Double") == 0) {
        if (val.type == ZEN_DECIMAL) return val;
        if (val.type == ZEN_INTEGER) return ZenValue_make_decimal((double)val.as.integer);
        if (val.type == ZEN_BOOLEAN) return ZenValue_make_decimal(val.as.boolean ? 1.0 : 0.0);
        if (val.type == ZEN_STRING) {
            if (!val.as.string) return ZenValue_make_decimal(0.0);
            return ZenValue_make_decimal(strtod(val.as.string, NULL));
        }
        if (val.type == ZEN_NOTHING) return ZenValue_make_decimal(0.0);
        return ZenValue_make_decimal(0.0);
    }
    
    /* 3. Target: String / Str */
    if (strcmp(target_type, "String") == 0 || strcmp(target_type, "Str") == 0) {
        if (val.type == ZEN_STRING) return val;
        if (val.type == ZEN_INTEGER) {
            char buf[64];
            snprintf(buf, sizeof(buf), "%lld", val.as.integer);
            return ZenValue_make_string(buf);
        }
        if (val.type == ZEN_DECIMAL) {
            char buf[64];
            snprintf(buf, sizeof(buf), "%.6g", val.as.decimal);
            return ZenValue_make_string(buf);
        }
        if (val.type == ZEN_BOOLEAN) {
            return ZenValue_make_string(val.as.boolean ? "True" : "False");
        }
        if (val.type == ZEN_NOTHING) {
            return ZenValue_make_string("");
        }
        if (val.type == ZEN_LIST) {
            if (val.as.list && val.as.list->count > 0) {
                bool all_bytes = true;
                for (int i = 0; i < val.as.list->count; i++) {
                    if (val.as.list->items[i].type != ZEN_INTEGER) {
                        all_bytes = false;
                        break;
                    }
                }
                if (all_bytes) {
                    char* buf = (char*)malloc(val.as.list->count + 1);
                    for (int i = 0; i < val.as.list->count; i++) {
                        buf[i] = (char)val.as.list->items[i].as.integer;
                    }
                    buf[val.as.list->count] = '\0';
                    ZenValue res = ZenValue_make_string(buf);
                    free(buf);
                    return res;
                }
            }
            return ZenValue_make_string("[]");
        }
        return ZenValue_make_string("");
    }
    
    /* 4. Target: Boolean / Bool */
    if (strcmp(target_type, "Boolean") == 0 || strcmp(target_type, "Bool") == 0) {
        if (val.type == ZEN_BOOLEAN) return val;
        if (val.type == ZEN_INTEGER) return ZenValue_make_boolean(val.as.integer != 0);
        if (val.type == ZEN_DECIMAL) return ZenValue_make_boolean(val.as.decimal != 0.0);
        if (val.type == ZEN_STRING) {
            if (!val.as.string || val.as.string[0] == '\0') return ZenValue_make_boolean(false);
            if (strcmp(val.as.string, "True") == 0 || strcmp(val.as.string, "true") == 0 ||
                strcmp(val.as.string, "1") == 0) {
                return ZenValue_make_boolean(true);
            }
            return ZenValue_make_boolean(false);
        }
        if (val.type == ZEN_LIST) return ZenValue_make_boolean(val.as.list && val.as.list->count > 0);
        if (val.type == ZEN_MAP) return ZenValue_make_boolean(val.as.map && val.as.map->count > 0);
        if (val.type == ZEN_SET) return ZenValue_make_boolean(ZenSet_get_count(val) > 0);
        if (val.type == ZEN_NOTHING) return ZenValue_make_boolean(false);
        return ZenValue_make_boolean(true);
    }
    
    /* 5. Target: Rune / Char / Glyph */
    if (strcmp(target_type, "Rune") == 0 || strcmp(target_type, "Char") == 0 ||
        strcmp(target_type, "Glyph") == 0) {
        if (val.type == ZEN_STRING) {
            if (!val.as.string || val.as.string[0] == '\0') return ZenValue_make_string("");
            char buf[2] = { val.as.string[0], '\0' };
            return ZenValue_make_string(buf);
        }
        if (val.type == ZEN_INTEGER) {
            char buf[5] = {0};
            if (val.as.integer < 128) {
                buf[0] = (char)val.as.integer;
                buf[1] = '\0';
            } else if (val.as.integer < 0x800) {
                buf[0] = (char)(0xC0 | (val.as.integer >> 6));
                buf[1] = (char)(0x80 | (val.as.integer & 0x3F));
                buf[2] = '\0';
            } else {
                buf[0] = (char)(0xE0 | (val.as.integer >> 12));
                buf[1] = (char)(0x80 | ((val.as.integer >> 6) & 0x3F));
                buf[2] = (char)(0x80 | (val.as.integer & 0x3F));
                buf[3] = '\0';
            }
            return ZenValue_make_string(buf);
        }
        return ZenValue_make_string("");
    }
    
    /* 6. Target: Bytes / Buffer */
    if (strcmp(target_type, "Bytes") == 0 || strcmp(target_type, "Buffer") == 0) {
        if (val.type == ZEN_STRING) {
            ZenList* list = ZenList_new();
            if (val.as.string) {
                size_t len = strlen(val.as.string);
                for (size_t i = 0; i < len; i++) {
                    ZenList_append_value(ZenValue_from_list(list), ZenValue_make_integer((unsigned char)val.as.string[i]));
                }
            }
            return ZenValue_from_list(list);
        }
        if (val.type == ZEN_LIST) return val;
        if (val.type == ZEN_INTEGER) {
            ZenList* list = ZenList_new();
            ZenList_append_value(ZenValue_from_list(list), val);
            return ZenValue_from_list(list);
        }
        return ZenValue_from_list(ZenList_new());
    }
    
    /* 7. Target: List */
    if (strcmp(target_type, "List") == 0) {
        if (val.type == ZEN_LIST) return val;
        if (val.type == ZEN_SET) return ZenSet_to_list(val);
        if (val.type == ZEN_MAP) return ZenMap_get_keys(val);
        if (val.type == ZEN_STRING) {
            ZenList* list = ZenList_new();
            if (val.as.string) {
                size_t len = strlen(val.as.string);
                for (size_t i = 0; i < len; i++) {
                    char buf[2] = { val.as.string[i], '\0' };
                    ZenList_append_value(ZenValue_from_list(list), ZenValue_make_string(buf));
                }
            }
            return ZenValue_from_list(list);
        }
        ZenList* list = ZenList_new();
        ZenList_append_value(ZenValue_from_list(list), val);
        return ZenValue_from_list(list);
    }
    
    /* 8. Target: Set */
    if (strcmp(target_type, "Set") == 0) {
        if (val.type == ZEN_SET) return val;
        if (val.type == ZEN_LIST) return ZenSet_from_list(val);
        if (val.type == ZEN_STRING) {
            ZenValue list_val = ZenValue_cast(val, "List");
            return ZenSet_from_list(list_val);
        }
        ZenList* list = ZenList_new();
        ZenList_append_value(ZenValue_from_list(list), val);
        return ZenSet_from_list(ZenValue_from_list(list));
    }
    
    /* 9. Target: Map */
    if (strcmp(target_type, "Map") == 0) {
        if (val.type == ZEN_MAP) return val;
        return ZenValue_from_map(ZenMap_new());
    }

    /* 10. Target: Default */
    if (strcmp(target_type, "Default") == 0 || strcmp(target_type, "default") == 0) {
        return ZEN_DEFAULT_VAL;
    }

    /* 11. Target: Nothing */
    if (strcmp(target_type, "Nothing") == 0 || strcmp(target_type, "nothing") == 0) {
        return ZEN_NOTHING_VAL;
    }
    
    return val;
}
