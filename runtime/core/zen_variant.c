#include "zen_variant.h"
#include "collections/zen_list.h"
#include "memory/zen_memory.h"
#include <stdarg.h>
#include <string.h>

ZenValue ZenValue_make_variant(ZenValue enum_name, ZenValue variant_name, int n_params, ...) {
    ZenVariantObject* v = (ZenVariantObject*)ZenRuntime_allocate(sizeof(ZenVariantObject));
    v->enum_name = enum_name;
    v->variant_name = variant_name;
    v->data = ZenValue_from_list(ZenList_new());
    
    va_list args;
    va_start(args, n_params);
    for (int i = 0; i < n_params; i++) {
        ZenValue arg = va_arg(args, ZenValue);
        ZenList_append_value(v->data, arg);
    }
    va_end(args);
    
    ZenValue res;
    res.type = ZEN_VARIANT;
    res.as.variant = v;
    return res;
}

ZenValue ZenValue_is_variant(ZenValue val, ZenValue expected_enum, ZenValue expected_variant) {
    if (val.type != ZEN_VARIANT) return ZenValue_make_boolean(false);
    if (!val.as.variant) return ZenValue_make_boolean(false);
    const char* en = val.as.variant->enum_name.as.string;
    const char* exp_en = expected_enum.as.string;
    if (en != exp_en && (!en || !exp_en || strcmp(en, exp_en) != 0)) {
        return ZenValue_make_boolean(false);
    }
    const char* vn = val.as.variant->variant_name.as.string;
    const char* exp_vn = expected_variant.as.string;
    if (vn != exp_vn && (!vn || !exp_vn || strcmp(vn, exp_vn) != 0)) {
        return ZenValue_make_boolean(false);
    }
    return ZenValue_make_boolean(true);
}

ZenValue ZenValue_is_error(ZenValue v) {
    if (v.type == ZEN_ERROR) {
        return ZenValue_make_boolean(true);
    }
    if (v.type == ZEN_VARIANT && v.as.variant &&
        v.as.variant->enum_name.type == ZEN_STRING &&
        v.as.variant->enum_name.as.string) {
        const char* en = v.as.variant->enum_name.as.string;
        const char* vn = (v.as.variant->variant_name.type == ZEN_STRING && v.as.variant->variant_name.as.string)
            ? v.as.variant->variant_name.as.string
            : "";
        if (strcmp(en, "Error") == 0) {
            return ZenValue_make_boolean(true);
        }
        if (strcmp(en, "Result") == 0 && strcmp(vn, "Error") == 0) {
            return ZenValue_make_boolean(true);
        }
    }
    return ZenValue_make_boolean(false);
}

ZenValue ZenValue_is_type_name(ZenValue val, const char* expected_type) {
    if (!expected_type) return ZenValue_make_boolean(false);

    if (strcmp(expected_type, "Nothing") == 0) return ZenValue_make_boolean(val.type == ZEN_NOTHING);
    if (strcmp(expected_type, "Boolean") == 0 || strcmp(expected_type, "Bool") == 0) return ZenValue_make_boolean(val.type == ZEN_BOOLEAN);
    if (strcmp(expected_type, "Integer") == 0 || strcmp(expected_type, "Int") == 0) return ZenValue_make_boolean(val.type == ZEN_INTEGER);
    if (strcmp(expected_type, "Decimal") == 0 || strcmp(expected_type, "Float") == 0) return ZenValue_make_boolean(val.type == ZEN_DECIMAL);
    if (strcmp(expected_type, "String") == 0) return ZenValue_make_boolean(val.type == ZEN_STRING);
    if (strcmp(expected_type, "List") == 0) return ZenValue_make_boolean(val.type == ZEN_LIST);
    if (strcmp(expected_type, "Map") == 0) return ZenValue_make_boolean(val.type == ZEN_MAP);
    if (strcmp(expected_type, "Variant") == 0) return ZenValue_make_boolean(val.type == ZEN_VARIANT);
    if (strcmp(expected_type, "Error") == 0) {
        if (val.type == ZEN_ERROR) {
            return ZenValue_make_boolean(true);
        }
        return ZenValue_make_boolean(
            val.type == ZEN_VARIANT &&
            val.as.variant &&
            val.as.variant->enum_name.type == ZEN_STRING &&
            val.as.variant->enum_name.as.string &&
            (strcmp(val.as.variant->enum_name.as.string, "Error") == 0 ||
             (strcmp(val.as.variant->enum_name.as.string, "Result") == 0 &&
              val.as.variant->variant_name.type == ZEN_STRING &&
              val.as.variant->variant_name.as.string &&
              strcmp(val.as.variant->variant_name.as.string, "Error") == 0))
        );
    }

    return ZenValue_make_boolean(false);
}

ZenValue ZenValue_get_variant_name(ZenValue val) {
    if (val.type != ZEN_VARIANT) return ZenValue_make_string("");
    return val.as.variant->variant_name;
}

ZenValue ZenValue_get_variant_data(ZenValue val, ZenValue index) {
    if (val.type != ZEN_VARIANT) return ZenValue_make_nothing();
    return ZenList_get_value_at_index(val.as.variant->data, index);
}
