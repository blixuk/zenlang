#include "zen_variant.h"
#include "collections/zen_list.h"
#include "collections/zen_map.h"
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
    if (strcmp(expected_type, "Boolean") == 0) return ZenValue_make_boolean(val.type == ZEN_BOOLEAN);
    if (strcmp(expected_type, "Number") == 0) return ZenValue_make_boolean(val.type == ZEN_INTEGER || val.type == ZEN_DECIMAL);
    if (strcmp(expected_type, "Text") == 0) return ZenValue_make_boolean(val.type == ZEN_STRING);
    if (strcmp(expected_type, "Collection") == 0) return ZenValue_make_boolean(val.type == ZEN_LIST || val.type == ZEN_MAP || val.type == ZEN_SET || val.type == ZEN_AST_NODE || val.type == ZEN_TOKEN);
    if (strcmp(expected_type, "Container") == 0) return ZenValue_make_boolean(val.type == ZEN_MAP || val.type == ZEN_OBJECT || val.type == ZEN_VARIANT);
    if (strcmp(expected_type, "Integer") == 0 ||
        strcmp(expected_type, "Integer[64]") == 0 || strcmp(expected_type, "Integer[32]") == 0 ||
        strcmp(expected_type, "Integer[16]") == 0 || strcmp(expected_type, "Integer[8]") == 0 ||
        strcmp(expected_type, "Byte") == 0) return ZenValue_make_boolean(val.type == ZEN_INTEGER);
    if (strcmp(expected_type, "Decimal") == 0 || strcmp(expected_type, "Decimal[64]") == 0 || strcmp(expected_type, "Decimal[32]") == 0) return ZenValue_make_boolean(val.type == ZEN_DECIMAL);
    if (strcmp(expected_type, "String") == 0 || strncmp(expected_type, "String[", 7) == 0) return ZenValue_make_boolean(val.type == ZEN_STRING);
    if (strcmp(expected_type, "Rune") == 0) {
        return ZenValue_make_boolean(val.type == ZEN_STRING && val.as.string && strlen(val.as.string) == 1);
    }
    if (strcmp(expected_type, "Bytes") == 0) return ZenValue_make_boolean(val.type == ZEN_LIST || val.type == ZEN_STRING);
    if (strcmp(expected_type, "List") == 0 || strncmp(expected_type, "List<", 5) == 0 || strncmp(expected_type, "List[", 5) == 0 ||
        strcmp(expected_type, "Tuple") == 0 || strncmp(expected_type, "Tuple<", 6) == 0 || strncmp(expected_type, "Tuple[", 6) == 0 ||
        strcmp(expected_type, "Vector") == 0 || strncmp(expected_type, "Vector[", 7) == 0 || strncmp(expected_type, "Vector<", 7) == 0) return ZenValue_make_boolean(val.type == ZEN_LIST || val.type == ZEN_AST_NODE || val.type == ZEN_TOKEN);
    if (strcmp(expected_type, "AstNode") == 0) return ZenValue_make_boolean(val.type == ZEN_AST_NODE);
    if (strcmp(expected_type, "Token") == 0) return ZenValue_make_boolean(val.type == ZEN_TOKEN);
    if (strcmp(expected_type, "Set") == 0 || strncmp(expected_type, "Set<", 4) == 0 || strncmp(expected_type, "Set[", 4) == 0) return ZenValue_make_boolean(val.type == ZEN_SET);
    if (strcmp(expected_type, "Map") == 0 || strncmp(expected_type, "Map<", 4) == 0 || strncmp(expected_type, "Map[", 4) == 0) return ZenValue_make_boolean(val.type == ZEN_MAP);
    if (strcmp(expected_type, "Variant") == 0) return ZenValue_make_boolean(val.type == ZEN_VARIANT);
    if (strcmp(expected_type, "Error") == 0) {
        if (val.type == ZEN_ERROR) {
            return ZenValue_make_boolean(true);
        }
        if (val.type == ZEN_MAP) {
            ZenValue type_field = ZenMap_get_value_at_key(val, ZenValue_make_string("__type__"));
            if (type_field.type == ZEN_STRING && type_field.as.string && strcmp(type_field.as.string, "Error") == 0) {
                return ZenValue_make_boolean(true);
            }
            type_field = ZenMap_get_value_at_key(val, ZenValue_make_string("__type"));
            if (type_field.type == ZEN_STRING && type_field.as.string && strcmp(type_field.as.string, "Error") == 0) {
                return ZenValue_make_boolean(true);
            }
            ZenValue is_err = ZenMap_get_value_at_key(val, ZenValue_make_string("is_error"));
            if (is_err.type == ZEN_BOOLEAN && is_err.as.boolean) {
                return ZenValue_make_boolean(true);
            }
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

    if (val.type == ZEN_MAP) {
        ZenValue type_field = ZenMap_get_value_at_key(val, ZenValue_make_string("__type__"));
        if (type_field.type == ZEN_STRING && type_field.as.string) {
            if (strcmp(type_field.as.string, expected_type) == 0) return ZenValue_make_boolean(true);
            size_t elen = strlen(expected_type);
            if (strncmp(type_field.as.string, expected_type, elen) == 0 && type_field.as.string[elen] == '<') return ZenValue_make_boolean(true);
            size_t tlen = strlen(type_field.as.string);
            if (strncmp(expected_type, type_field.as.string, tlen) == 0 && expected_type[tlen] == '<') return ZenValue_make_boolean(true);
        }
        type_field = ZenMap_get_value_at_key(val, ZenValue_make_string("__type"));
        if (type_field.type == ZEN_STRING && type_field.as.string) {
            if (strcmp(type_field.as.string, expected_type) == 0) return ZenValue_make_boolean(true);
            size_t elen = strlen(expected_type);
            if (strncmp(type_field.as.string, expected_type, elen) == 0 && type_field.as.string[elen] == '<') return ZenValue_make_boolean(true);
            size_t tlen = strlen(type_field.as.string);
            if (strncmp(expected_type, type_field.as.string, tlen) == 0 && expected_type[tlen] == '<') return ZenValue_make_boolean(true);
        }
        type_field = ZenMap_get_value_at_key(val, ZenValue_make_string("kind"));
        if (type_field.type == ZEN_STRING && type_field.as.string) {
            if (strcmp(type_field.as.string, expected_type) == 0) return ZenValue_make_boolean(true);
            size_t elen = strlen(expected_type);
            if (strncmp(type_field.as.string, expected_type, elen) == 0 && type_field.as.string[elen] == '<') return ZenValue_make_boolean(true);
            size_t tlen = strlen(type_field.as.string);
            if (strncmp(expected_type, type_field.as.string, tlen) == 0 && expected_type[tlen] == '<') return ZenValue_make_boolean(true);
        }
    }

    if (val.type == ZEN_VARIANT && val.as.variant) {
        if (val.as.variant->enum_name.type == ZEN_STRING && val.as.variant->enum_name.as.string &&
            strcmp(val.as.variant->enum_name.as.string, expected_type) == 0) {
            return ZenValue_make_boolean(true);
        }
        if (val.as.variant->variant_name.type == ZEN_STRING && val.as.variant->variant_name.as.string &&
            strcmp(val.as.variant->variant_name.as.string, expected_type) == 0) {
            return ZenValue_make_boolean(true);
        }
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
