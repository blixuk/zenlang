#include "bootstrap_runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include <unistd.h> // For isatty

#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_BLUE    "\x1b[34m"
#define ANSI_COLOR_CYAN    "\x1b[36m"
#define ANSI_COLOR_RESET   "\x1b[0m"

ZenValue __builtin_output;
ZenValue __builtin_input;
ZenValue __builtin_file;
ZenValue __builtin_sys;
ZenValue __builtin_string;

const ZenValue Zen_nothing = {ZEN_NOTHING, {0}};

void zl_init_runtime() {
    __builtin_output = zen_val_object(NULL); // dummy for now
    __builtin_input = zen_val_object(NULL);
    __builtin_file = zen_val_object(NULL);
    __builtin_sys = zen_val_object(NULL);
    __builtin_string = zen_val_object(NULL);
}

/* Constructors */

ZenValue ZenList_from_args(int n, ...) {
    ZenList* list = ZenList_create();
    va_list args;
    va_start(args, n);
    for (int i = 0; i < n; i++) {
        ZenVariant item = va_arg(args, ZenVariant);
        ZenList_append(list, item);
    }
    va_end(args);
    return zen_val_list(list);
}

/* Macros in header handle basic constructors */

ZenValue zen_str(const char* s) {
    ZenValue z;
    z.type = ZEN_STRING;
    if (s == NULL) {
        z.as.string = NULL;
    } else {
        size_t len = strlen(s);
        char* res = malloc(len + 1);
        strcpy(res, s);
        z.as.string = res;
    }
    return z;
}

ZenValue zen_make_string(const char* s) { return zen_str(s); }
ZenValue zen_make_integer(long long v) { return zen_int(v); }
ZenValue zen_make_boolean(int v) { return zen_bool(v != 0); }
ZenValue zen_make_float(double v) { return zen_float(v); }

ZenValue zen_make_null(void) {
    ZenValue z;
    z.type = ZEN_NOTHING;
    return z;
}

ZenValue zen_val_list(ZenList* l) {
    ZenValue z;
    z.type = ZEN_LIST;
    z.as.list = l;
    return z;
}

ZenValue zen_val_object(void* o) {
    ZenValue z;
    z.type = ZEN_OBJECT;
    z.as.object = o;
    return z;
}

ZenValue zen_val_map(ZenMap* m) {
    ZenValue z;
    z.type = ZEN_MAP;
    z.as.map = m;
    return z;
}

ZenValue zen_val_arena(ZenArena* a) {
    ZenValue z;
    z.type = ZEN_ARENA;
    z.as.arena = a;
    return z;
}

ZenValue zen_error(ZenValue message) {
    ZenValue v = {ZEN_ERROR};
    v.as.string = ZenString_create(ZenString_str(message));
    return v;
}

ZenValue ZenValue_new_variant(ZenValue enum_name, ZenValue variant_name, int n_params, ...) {
    ZenVariantObject* v = zen_malloc(sizeof(ZenVariantObject));
    v->enum_name = enum_name;
    v->variant_name = variant_name;
    v->data = zen_val_list(ZenList_create());
    
    va_list args;
    va_start(args, n_params);
    for (int i = 0; i < n_params; i++) {
        ZenValue arg = va_arg(args, ZenValue);
        ZenList_append(v->data.as.list, arg);
    }
    va_end(args);
    
    ZenValue res;
    res.type = ZEN_VARIANT;
    res.as.variant = v;
    return res;
}

ZenValue ZenValue_is_variant(ZenValue val, ZenValue expected_enum, ZenValue expected_variant) {
    if (val.type != ZEN_VARIANT) return zen_bool(false);
    if (strcmp(val.as.variant->enum_name.as.string, expected_enum.as.string) == 0 &&
        strcmp(val.as.variant->variant_name.as.string, expected_variant.as.string) == 0) {
        return zen_bool(true);
    }
    return zen_bool(false);
}

ZenValue ZenValue_get_variant_name(ZenValue val) {
    if (val.type != ZEN_VARIANT) return zen_str("");
    return val.as.variant->variant_name;
}

ZenValue ZenValue_get_variant_data(ZenValue val, ZenValue index) {
    if (val.type != ZEN_VARIANT) return Zen_nothing;
    return ZenList_get(val.as.variant->data.as.list, (int)index.as.integer);
}

/* ZenList functions */

ZenList* ZenList_create() {
    ZenList* list = malloc(sizeof(ZenList));
    list->items = NULL;
    list->count = 0;
    list->capacity = 0;
    return list;
}

void ZenList_append(ZenList* list, ZenVariant item) {
    if (list->count + 1 > list->capacity) {
        list->capacity = list->capacity < 4 ? 4 : list->capacity * 2;
        list->items = realloc(list->items, sizeof(ZenVariant) * list->capacity);
    }
    list->items[list->count++] = item;
}

ZenVariant ZenList_get(ZenList* list, int index) {
    if (index < 0 || index >= list->count) {
        return zen_make_null();
    }
    return list->items[index];
}

void ZenList_set(ZenList* list, int index, ZenVariant item) {
    if (index >= 0 && index < list->count) {
        list->items[index] = item;
    }
}

ZenValue ZenList_count(ZenList* list) {
    if (!list) return zen_int(0);
    return zen_int(list->count);
}

/* ZenMap functions */

ZenMap* ZenMap_create() {
    ZenMap* map = malloc(sizeof(ZenMap));
    map->entries = NULL;
    map->count = 0;
    map->capacity = 0;
    return map;
}

void ZenMap_set(ZenMap* map, ZenVariant key, ZenVariant value) {
    for (int i = 0; i < map->count; i++) {
        if (key.type == ZEN_STRING && map->entries[i].key.type == ZEN_STRING) {
            if (strcmp(key.as.string, map->entries[i].key.as.string) == 0) {
                map->entries[i].value = value;
                return;
            }
        }
    }

    if (map->count + 1 > map->capacity) {
        map->capacity = map->capacity < 4 ? 4 : map->capacity * 2;
        map->entries = realloc(map->entries, sizeof(ZenMapEntry) * map->capacity);
    }
    map->entries[map->count].key = key;
    map->entries[map->count].value = value;
    map->count++;
}

ZenValue ZenMap_from_args(int n, ...) {
    ZenMap* map = ZenMap_create();
    va_list args;
    va_start(args, n);
    for (int i = 0; i < n; i++) {
        ZenVariant key = va_arg(args, ZenVariant);
        ZenVariant value = va_arg(args, ZenVariant);
        ZenMap_set(map, key, value);
    }
    va_end(args);
    return zen_val_map(map);
}

ZenVariant ZenMap_get(ZenMap* map, ZenVariant key) {
    for (int i = 0; i < map->count; i++) {
        if (key.type == ZEN_STRING && map->entries[i].key.type == ZEN_STRING) {
            if (strcmp(key.as.string, map->entries[i].key.as.string) == 0) {
                return map->entries[i].value;
            }
        }
    }
    return zen_make_null();
}

ZenValue ZenMap_count(ZenMap* map) {
    if (!map) return zen_int(0);
    return zen_int(map->count);
}

/* ZenValue Operations */

ZenValue ZenValue_add(ZenValue a, ZenValue b) {
    if (a.type == ZEN_STRING || b.type == ZEN_STRING) {
        return ZenString_concat(a, b);
    }
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer + b.as.integer);
    if (a.type == ZEN_DECIMAL || b.type == ZEN_DECIMAL) {
        double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
        double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
        return zen_float(va + vb);
    }
    return zen_make_null();
}

ZenValue ZenValue_sub(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer - b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return zen_float(va - vb);
}

ZenValue ZenValue_mul(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer * b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return zen_float(va * vb);
}

ZenValue ZenValue_div(ZenValue a, ZenValue b) {
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    if (vb == 0) return zen_make_null();
    return zen_float(va / vb);
}

ZenValue ZenValue_not(ZenValue a) {
    return zen_bool(!a.as.boolean);
}

ZenValue ZenValue_mod(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer % b.as.integer);
    return zen_make_null();
}

ZenValue ZenValue_neg(ZenValue a) {
    if (a.type == ZEN_INTEGER) return zen_int(-a.as.integer);
    if (a.type == ZEN_DECIMAL) return zen_float(-a.as.decimal);
    return zen_make_null();
}

ZenValue ZenValue_pow(ZenValue a, ZenValue b) {
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return zen_float(pow(va, vb));
}

ZenValue ZenValue_less_than(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_bool(a.as.integer < b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return zen_bool(va < vb);
}

ZenValue ZenValue_greater_than(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_bool(a.as.integer > b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return zen_bool(va > vb);
}

ZenValue ZenValue_less_than_or_equal(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_bool(a.as.integer <= b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return zen_bool(va <= vb);
}

ZenValue ZenValue_greater_than_or_equal(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_bool(a.as.integer >= b.as.integer);
    double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
    double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
    return zen_bool(va >= vb);
}

ZenValue ZenValue_not_equals(ZenValue a, ZenValue b) {
    return ZenValue_not(ZenValue_equals(a, b));
}

ZenValue ZenValue_bitwise_and(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer & b.as.integer);
    return zen_make_null();
}

ZenValue ZenValue_bitwise_or(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer | b.as.integer);
    return zen_make_null();
}

ZenValue ZenValue_bitwise_xor(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer ^ b.as.integer);
    return zen_make_null();
}

ZenValue ZenValue_bitwise_not(ZenValue a) {
    if (a.type == ZEN_INTEGER) return zen_int(~a.as.integer);
    return zen_make_null();
}

ZenValue ZenValue_lshift(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer << b.as.integer);
    return zen_make_null();
}

ZenValue ZenValue_rshift(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer >> b.as.integer);
    return zen_make_null();
}

ZenValue ZenValue_bitwise_mod(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer % b.as.integer);
    return zen_make_null();
}

ZenValue ZenValue_bitwise_nor(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(~(a.as.integer | b.as.integer));
    return zen_make_null();
}

ZenValue ZenValue_bitwise_nand(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(~(a.as.integer & b.as.integer));
    return zen_make_null();
}

ZenValue ZenValue_bitwise_xnor(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(~(a.as.integer ^ b.as.integer));
    return zen_make_null();
}

ZenValue ZenValue_and(ZenValue a, ZenValue b) {
    return zen_bool(a.as.boolean && b.as.boolean);
}

ZenValue ZenValue_or(ZenValue a, ZenValue b) {
    return zen_bool(a.as.boolean || b.as.boolean);
}

ZenValue ZenValue_xor(ZenValue a, ZenValue b) {
    return zen_bool((a.as.boolean || b.as.boolean) && !(a.as.boolean && b.as.boolean));
}

ZenValue ZenValue_nor(ZenValue a, ZenValue b) {
    return zen_bool(!(a.as.boolean || b.as.boolean));
}

ZenValue ZenValue_nand(ZenValue a, ZenValue b) {
    return zen_bool(!(a.as.boolean && b.as.boolean));
}

ZenValue ZenValue_xnor(ZenValue a, ZenValue b) {
    return zen_bool(a.as.boolean == b.as.boolean);
}

ZenValue ZenValue_equals(ZenValue a, ZenValue b) {
    if (a.type != b.type) {
        if (a.type == ZEN_INTEGER && b.type == ZEN_DECIMAL) return zen_bool((double)a.as.integer == b.as.decimal);
        if (a.type == ZEN_DECIMAL && b.type == ZEN_INTEGER) return zen_bool(a.as.decimal == (double)b.as.integer);
        return zen_bool(false);
    }
    switch (a.type) {
        case ZEN_NOTHING: return zen_bool(true);
        case ZEN_INTEGER: return zen_bool(a.as.integer == b.as.integer);
        case ZEN_DECIMAL: return zen_bool(a.as.decimal == b.as.decimal);
        case ZEN_BOOLEAN: return zen_bool(a.as.boolean == b.as.boolean);
        case ZEN_STRING: 
            if (a.as.string == b.as.string) return zen_bool(true);
            if (!a.as.string || !b.as.string) return zen_bool(false);
            return zen_bool(strcmp(a.as.string, b.as.string) == 0);
        case ZEN_LIST: return zen_bool(a.as.list == b.as.list);
        case ZEN_MAP: return zen_bool(a.as.map == b.as.map);
        case ZEN_OBJECT: return zen_bool(a.as.object == b.as.object);
        case ZEN_ARENA: return zen_bool(a.as.arena == b.as.arena);
        case ZEN_ERROR: return zen_bool(strcmp(a.as.string, b.as.string) == 0);
        case ZEN_VARIANT:
            if (a.as.variant == b.as.variant) return zen_bool(true);
            if (!a.as.variant || !b.as.variant) return zen_bool(false);
            if (strcmp(a.as.variant->enum_name.as.string, b.as.variant->enum_name.as.string) != 0) return zen_bool(false);
            if (strcmp(a.as.variant->variant_name.as.string, b.as.variant->variant_name.as.string) != 0) return zen_bool(false);
            return ZenValue_equals(a.as.variant->data, b.as.variant->data);
    }
    return zen_bool(false);
}

/* String functions */

ZenString ZenString_create(const char* s) {
    if (!s) return NULL;
    char* res = malloc(strlen(s) + 1);
    strcpy(res, s);
    return res;
}


ZenValue ZenString_count(ZenValue s_v) {
    const char* s = ZenString_ptr(s_v);
    if (!s) return zen_int(0);
    return zen_int((int)strlen(s));
}

ZenValue ZenString_at(ZenValue s_v, ZenValue index_v) {
    int index = (int)index_v.as.integer;
    const char* s = ZenString_ptr(s_v);
    if (!s || index < 0 || index >= (int)strlen(s)) return zen_str("");
    char* res = zen_malloc(2);
    res[0] = s[index];
    res[1] = '\0';
    return zen_str(res);
}


ZenValue ZenString_equals(ZenValue s1_v, ZenValue s2_v) {
    const char* s1 = ZenString_ptr(s1_v);
    const char* s2 = ZenString_ptr(s2_v);
    if (s1 == s2) return zen_bool(true);
    if (!s1 || !s2) return zen_bool(false);
    return zen_bool(strcmp(s1, s2) == 0);
}

ZenValue ZenString_concat(ZenValue s1_v, ZenValue s2_v) {
    // Basic stringification for concat if needed
    const char* s1 = (s1_v.type == ZEN_STRING) ? s1_v.as.string : ZenString_str(s1_v);
    const char* s2 = (s2_v.type == ZEN_STRING) ? s2_v.as.string : ZenString_str(s2_v);
    
    if (!s1) return zen_str(s2 ? s2 : "");
    if (!s2) return zen_str(s1);
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char* res = zen_malloc(len1 + len2 + 1);
    strcpy(res, s1);
    strcat(res, s2);
    return zen_str(res);
}

ZenValue ZenString_replace(ZenValue s_v, ZenValue old_v, ZenValue new_v) {
    const char* s = ZenString_ptr(s_v);
    const char* old_s = ZenString_ptr(old_v);
    const char* new_s = ZenString_ptr(new_v);
    if (!s || !old_s || !new_s) return s_v;
    
    size_t old_len = strlen(old_s);
    if (old_len == 0) return s_v;
    int count = 0;
    const char *tmp = s;
    while ((tmp = strstr(tmp, old_s))) {
        count++;
        tmp += old_len;
    }
    if (count == 0) return s_v;
    size_t new_len = strlen(new_s);
    size_t res_len = strlen(s) + (new_len - old_len) * count;
    char* res = zen_malloc(res_len + 1);
    char* dst = res;
    const char* src = s;
    while ((tmp = strstr(src, old_s))) {
        size_t prefix_len = tmp - src;
        memcpy(dst, src, prefix_len);
        dst += prefix_len;
        memcpy(dst, new_s, new_len);
        dst += new_len;
        src = tmp + old_len;
    }
    strcpy(dst, src);
    return zen_str(res);
}

ZenString ZenString_str(ZenValue x) {
    char buf[128];
    switch (x.type) {
        case ZEN_INTEGER: sprintf(buf, "%lld", x.as.integer); return ZenString_create(buf);
        case ZEN_DECIMAL: sprintf(buf, "%f", x.as.decimal); return ZenString_create(buf);
        case ZEN_BOOLEAN: return ZenString_create(x.as.boolean ? "true" : "false");
        case ZEN_STRING: return ZenString_create(x.as.string);
        case ZEN_NOTHING: return ZenString_create("Nothing");
        case ZEN_ERROR: return ZenString_create("Error");
        case ZEN_ARENA: return ZenString_create("Arena");
        case ZEN_VARIANT: {
            if (!x.as.variant) return ZenString_create("Variant(null)");
            char buf_v[256];
            sprintf(buf_v, "%s.%s", x.as.variant->enum_name.as.string, x.as.variant->variant_name.as.string);
            return ZenString_create(buf_v);
        }
        case ZEN_LIST: {
            if (!x.as.list) return ZenString_create("[]");
            char* res = malloc(x.as.list->count * 32 + 3); // Heuristic
            strcpy(res, "[");
            for (int i = 0; i < x.as.list->count; i++) {
                char* s = ZenString_str(x.as.list->items[i]);
                strcat(res, s);
                if (i < x.as.list->count - 1) strcat(res, ", ");
                free(s);
            }
            strcat(res, "]");
            return res; // ZenString is char*
        }
        case ZEN_MAP: {
            if (!x.as.map) return ZenString_create("{}");
            char* res = malloc(x.as.map->count * 64 + 3); // Heuristic
            strcpy(res, "{");
            for (int i = 0; i < x.as.map->count; i++) {
                char* k = ZenString_str(x.as.map->entries[i].key);
                char* v = ZenString_str(x.as.map->entries[i].value);
                strcat(res, k);
                strcat(res, ": ");
                strcat(res, v);
                if (i < x.as.map->count - 1) strcat(res, ", ");
                free(k);
                free(v);
            }
            strcat(res, "}");
            return res;
        }
        default: return ZenString_create("Object");
    }
}

ZenValue ZenString_to_string(ZenValue v) {
    return ZenValue_str(v);
}

ZenValue ZenValue_str(ZenValue v) {
    return zen_str(ZenString_str(v));
}

ZenValue ZenString_to_upper(ZenValue s_v) {
    const char* s = ZenString_ptr(s_v);
    if (!s) return zen_make_null();
    char* res = ZenString_create(s);
    for (int i = 0; res[i]; i++) {
        if (res[i] >= 'a' && res[i] <= 'z') res[i] -= 32;
    }
    return zen_str(res);
}

ZenValue ZenString_to_lower(ZenValue s_v) {
    const char* s = ZenString_ptr(s_v);
    if (!s) return zen_make_null();
    char* res = ZenString_create(s);
    for (int i = 0; res[i]; i++) {
        if (res[i] >= 'A' && res[i] <= 'Z') res[i] += 32;
    }
    return zen_str(res);
}

#include <ctype.h>
ZenValue ZenString_trim(ZenValue s_v) {
    const char* s = ZenString_ptr(s_v);
    if (!s) return zen_make_null();
    int len = strlen(s);
    if (len == 0) return zen_str("");
    int start = 0;
    while (start < len && isspace((unsigned char)s[start])) start++;
    if (start == len) return zen_str("");
    int end = len - 1;
    while (end > start && isspace((unsigned char)s[end])) end--;
    int new_len = end - start + 1;
    char* res = zen_malloc(new_len + 1);
    strncpy(res, s + start, new_len);
    res[new_len] = '\0';
    return zen_str(res);
}

ZenValue ZenString_index_of(ZenValue s_v, ZenValue sub_v) {
    const char* s = ZenString_ptr(s_v);
    const char* sub = ZenString_ptr(sub_v);
    if (!s || !sub) return zen_int(-1);
    char* pos = strstr(s, sub);
    if (!pos) return zen_int(-1);
    return zen_int((int)(pos - s));
}

/* IO functions */

ZenValue ZenIO_write(ZenValue v) {
    ZenString s = ZenString_str(v);
    if (s) {
        printf("%s", s);
        fflush(stdout);
        // free((void*)s); // Potential crash point
    }
    return zen_make_null();
}

/* out_write is called by some built-ins */
ZenValue out_write(ZenString s, void* data) {
    if (data && s) {
        ZenMap* map = (ZenMap*)data;
        char* final_str = ZenString_create(s);
        for (int i = 0; i < map->count; i++) {
            if (map->entries[i].key.type == ZEN_STRING) {
                char buf[128];
                sprintf(buf, "{%s}", map->entries[i].key.as.string);
                ZenString val_str = ZenString_str(map->entries[i].value);
                char* next_str = ZenString_replace(zen_str(final_str), zen_str(buf), zen_str(val_str)).as.string;
                // if (final_str != s) free(final_str);
                final_str = next_str;
                // free(val_str);
            }
        }
        IO_write(zen_str(final_str));
        if (final_str != s) free(final_str);
    } else {
        IO_write(zen_str(s));
    }
    return zen_make_null();
}

ZenValue IO_write_int(long long v) { 
    printf("%lld", v); 
    return zen_make_null();
}

static void print_color_prefix(const char* color, const char* prefix, FILE* stream) {
    if (isatty(fileno(stream))) {
        fprintf(stream, "%s%s%s ", color, prefix, ANSI_COLOR_RESET);
    } else {
        fprintf(stream, "%s ", prefix);
    }
}

ZenValue ZenIO_info(ZenValue v) {
    ZenString s = ZenString_str(v);
    if (s) {
        print_color_prefix(ANSI_COLOR_BLUE, "[INFO]", stdout);
        printf("%s\n", s);
        fflush(stdout);
    }
    return zen_make_null();
}

ZenValue ZenIO_warn(ZenValue v) {
    ZenString s = ZenString_str(v);
    if (s) {
        print_color_prefix(ANSI_COLOR_YELLOW, "[WARN]", stdout);
        printf("%s\n", s);
        fflush(stdout);
    }
    return zen_make_null();
}

ZenValue ZenIO_debug(ZenValue v) {
    ZenString s = ZenString_str(v);
    if (s) {
        print_color_prefix(ANSI_COLOR_CYAN, "[DEBUG]", stdout);
        printf("%s\n", s);
        fflush(stdout);
    }
    return zen_make_null();
}

ZenValue ZenIO_error(ZenValue v) { 
    ZenString s = ZenString_str(v);
    if (s) {
        print_color_prefix(ANSI_COLOR_RED, "[ERROR]", stderr);
        fprintf(stderr, "%s\n", s);
    }
    return zen_make_null();
}

ZenValue ZenIO_write_file(ZenValue path_val, ZenValue content_val) {
    ZenString path = ZenString_str(path_val);
    ZenString content = ZenString_str(content_val);
    FILE* f = fopen(path, "w");
    if (f) { fprintf(f, "%s", content); fclose(f); }
    return zen_make_null();
}

ZenValue ZenIO_read_file(ZenValue path_val) {
    ZenString path = ZenString_str(path_val);
    FILE* f = fopen(path, "r");
    if (!f) return zen_error(zen_str("File not found"));
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = malloc(len + 1);
    fread(buf, 1, len, f);
    buf[len] = '\0';
    fclose(f);
    return zen_str(buf);
}

ZenValue ZenIO_file_exists(ZenValue path_val) {
    ZenString path = ZenString_str(path_val);
    FILE* f = fopen(path, "r");
    if (f) {
        fclose(f);
        return zen_bool(true);
    }
    return zen_bool(false);
}

ZenValue ZenIO_write(ZenValue self, ZenValue v) {
    zl_print_begin();
    ZenValue_str(v);
    zl_print_end();
    return Zen_nothing;
}

ZenValue ZenIO_info(ZenValue self, ZenValue v) {
    if (v.type == ZEN_STRING) printf(ANSI_COLOR_CYAN "[INFO] " ANSI_COLOR_RESET "%s\n", v.as.string);
    else { zl_print_begin(); printf(ANSI_COLOR_CYAN "[INFO] " ANSI_COLOR_RESET); ZenValue_str(v); zl_print_end(); }
    return Zen_nothing;
}

ZenValue ZenIO_warn(ZenValue self, ZenValue v) {
    if (v.type == ZEN_STRING) printf(ANSI_COLOR_YELLOW "[WARN] " ANSI_COLOR_RESET "%s\n", v.as.string);
    else { zl_print_begin(); printf(ANSI_COLOR_YELLOW "[WARN] " ANSI_COLOR_RESET); ZenValue_str(v); zl_print_end(); }
    return Zen_nothing;
}

ZenValue ZenIO_error(ZenValue self, ZenValue v) {
    if (v.type == ZEN_STRING) printf(ANSI_COLOR_RED "[ERROR] " ANSI_COLOR_RESET "%s\n", v.as.string);
    else { zl_print_begin(); printf(ANSI_COLOR_RED "[ERROR] " ANSI_COLOR_RESET); ZenValue_str(v); zl_print_end(); }
    return Zen_nothing;
}

ZenValue ZenIO_debug(ZenValue self, ZenValue v) {
    if (v.type == ZEN_STRING) printf(ANSI_COLOR_MAGENTA "[DEBUG] " ANSI_COLOR_RESET "%s\n", v.as.string);
    else { zl_print_begin(); printf(ANSI_COLOR_MAGENTA "[DEBUG] " ANSI_COLOR_RESET); ZenValue_str(v); zl_print_end(); }
    return Zen_nothing;
}

ZenValue ZenIO_out_write(ZenValue self, ZenValue s) {
    const char* str = ZenString_ptr(s);
    if (str) fputs(str, stdout);
    return Zen_nothing;
}

ZenValue ZenIO_write_int(ZenValue self, long long v) {
    printf("%lld", v);
    return Zen_nothing;
}

ZenValue ZenIO_read(ZenValue self, ZenValue prompt) {
    if (prompt.type == ZEN_STRING) printf("%s", prompt.as.string);
    char buf[1024];
    if (fgets(buf, sizeof(buf), stdin)) {
        size_t len = strlen(buf);
        if (len > 0 && buf[len-1] == '\n') buf[len-1] = '\0';
        return zen_str(buf);
    }
    return zen_str("");
}

ZenValue ZenIO_file_exists(ZenValue self, ZenValue path_val) {
    const char* path = ZenString_ptr(path_val);
    if (!path) return zen_bool(false);
    FILE* f = fopen(path, "r");
    if (f) { fclose(f); return zen_bool(true); }
    return zen_bool(false);
}

ZenValue ZenIO_read_file(ZenValue self, ZenValue path_val) {
    const char* path = ZenString_ptr(path_val);
    if (!path) return zen_str("");
    FILE* f = fopen(path, "r");
    if (!f) return zen_str("");
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = malloc(size + 1);
    fread(buf, 1, size, f);
    buf[size] = '\0';
    fclose(f);
    ZenValue res = zen_str(buf);
    free(buf);
    return res;
}

ZenValue ZenIO_write_file(ZenValue self, ZenValue path_val, ZenValue content_val) {
    const char* path = ZenString_ptr(path_val);
    const char* content = ZenString_ptr(content_val);
    if (!path || !content) return zen_bool(false);
    FILE* f = fopen(path, "w");
    if (!f) return zen_bool(false);
    fputs(content, f);
    fclose(f);
    return zen_bool(true);
}

/* Sys functions */

ZenValue ZenSys_exit(ZenValue self, ZenValue code_val) {
    int code = (int)code_val.as.integer;
    exit(code);
    return Zen_nothing;
}

static ZenList* sys_args = NULL;
void _ZenSys_init_args(int argc, char** argv) {
    sys_args = ZenList_create();
    for (int i=0; i < argc; i++) {
        ZenList_append(sys_args, zen_str(ZenString_create(argv[i])));
    }
}
ZenValue ZenSys_get_args(ZenValue self) {
    ZenList* list = ZenList_create();
    for (int i=0; i < zen_argc; i++) {
        ZenList_append(list, zen_str(zen_argv[i]));
    }
    return zen_val_list(list);
}

ZenValue ZenSys_get_env(ZenValue self, ZenValue name_val) {
    const char* name = ZenString_ptr(name_val);
    if (!name) return zen_make_null();
    char* val = getenv(name);
    return val ? zen_str(val) : zen_make_null();
}

ZenValue ZenSys_get_cwd(ZenValue self) {
    char buf[1024];
    if (getcwd(buf, sizeof(buf))) return zen_str(buf);
    return zen_str("");
}

ZenValue ZenSys_platform(ZenValue self) {
    return zen_str("linux"); // Heuristic for now
}

ZenValue ZenSys_version(ZenValue self) {
    return zen_str("0.1.0");
}
ZenValue __builtin_error(ZenValue msg) {
    zen_raise(msg);
    return zen_make_null();
}
ZenValue __builtin_error_literal(ZenValue msg) {
    return zen_error(msg);
}

ZenValue ZenString_starts_with(ZenValue s_v, ZenValue prefix_v) {
    const char* s = ZenString_ptr(s_v);
    const char* prefix = ZenString_ptr(prefix_v);
    if (!s || !prefix) return zen_bool(false);
    return zen_bool(strncmp(s, prefix, strlen(prefix)) == 0);
}

ZenValue ZenString_ends_with(ZenValue s_v, ZenValue suffix_v) {
    const char* s = ZenString_ptr(s_v);
    const char* suffix = ZenString_ptr(suffix_v);
    if (!s || !suffix) return zen_bool(false);
    int len_s = strlen(s);
    int len_sub = strlen(suffix);
    if (len_sub > len_s) return zen_bool(false);
    return zen_bool(strcmp(s + len_s - len_sub, suffix) == 0);
}

ZenValue ZenString_substring(ZenValue s_v, ZenValue start_v, ZenValue end_v) {
    int start = (int)start_v.as.integer;
    int end = (int)end_v.as.integer;
    const char* s = ZenString_ptr(s_v);
    if (!s) return zen_str("");
    int len = strlen(s);
    if (start < 0) start = 0;
    if (end > len) end = len;
    if (start >= end) return zen_str("");
    char* res = zen_malloc(end - start + 1);
    strncpy(res, s + start, end - start);
    res[end - start] = '\0';
    return zen_str(res);
}

ZenValue ZenString_split(ZenValue s_v, ZenValue sep_v) {
    const char* s = ZenString_ptr(s_v);
    const char* sep = ZenString_ptr(sep_v);
    ZenList* list = ZenList_create();
    if (!s || !sep) return zen_val_list(list);
    char* str = strdup(s);
    int sep_len = strlen(sep);
    char* p = str;
    char* match;
    while ((match = strstr(p, sep)) != NULL) {
        *match = '\0';
        ZenList_append(list, zen_str(ZenString_create(p)));
        p = match + sep_len;
    }
    ZenList_append(list, zen_str(ZenString_create(p)));
    free(str);
    return zen_val_list(list);
}

ZenValue ZenString_join(ZenList* parts, ZenValue sep_v) {
    const char* sep = ZenString_ptr(sep_v);
    if (!parts || parts->count == 0) return zen_str("");
    int total_len = 0;
    int sep_len = sep ? strlen(sep) : 0;
    for (int i=0; i < parts->count; i++) {
        ZenValue item = parts->items[i];
        if (item.type == ZEN_STRING) total_len += strlen(item.as.string);
    }
    total_len += sep_len * (parts->count - 1);
    char* res = malloc(total_len + 1);
    res[0] = '\0';
    for (int i=0; i < parts->count; i++) {
        ZenValue item = parts->items[i];
        if (item.type == ZEN_STRING) strcat(res, item.as.string);
        if (i < parts->count - 1 && sep) strcat(res, sep);
    }
    return zen_str(res);
}

/* Debug Print */

static bool zl_print_first = true;
void zl_print_begin(void) { zl_print_first = true; }
void zl_print_sep(void) { if (!zl_print_first) fputc(' ', stdout); zl_print_first = false; }
void zl_print_end(void) { fputc('\n', stdout); fflush(stdout); }
void zl_print_int(long long v) { zl_print_sep(); printf("%lld", v); }
void zl_print_float(double v) { zl_print_sep(); printf("%g", v); }
void zl_print_string(const char *v) { zl_print_sep(); if (v == NULL) printf("Nothing"); else printf("%s", v); }
void zl_print_bool(bool v) { zl_print_sep(); printf(v ? "true" : "false"); }

/* Exception and Defer handling */

ZenValue zen_last_exception;
#define MAX_EXCEPTIONS 100
static ZenExceptionContext *exception_stack[MAX_EXCEPTIONS];
static int exception_stack_ptr = 0;
static ZenDeferNode *defer_stack = NULL;
static int current_defer_depth = 0;

void zen_exception_push(ZenExceptionContext *ctx) { if (exception_stack_ptr < MAX_EXCEPTIONS) exception_stack[exception_stack_ptr++] = ctx; }
void zen_exception_pop(void) { if (exception_stack_ptr > 0) exception_stack_ptr--; }

void zen_raise(ZenValue val) {
    zen_last_exception = val;
    if (exception_stack_ptr > 0) {
        ZenExceptionContext *ctx = exception_stack[exception_stack_ptr - 1];
        zen_defer_run_to(ctx->defer_depth);
        longjmp(ctx->buf, 1);
    } else {
        fprintf(stderr, "Unhandled exception: %s\n", ZenString_str(val));
        exit(1);
    }
}

void zen_defer_push(void (*func)(void*), void *data) {
    ZenDeferNode *node = malloc(sizeof(ZenDeferNode));
    node->func = func; node->data = data; node->next = defer_stack;
    defer_stack = node; current_defer_depth++;
}

void zen_defer_run_to(int target_depth) {
    while (current_defer_depth > target_depth && defer_stack != NULL) {
        ZenDeferNode *node = defer_stack;
        defer_stack = node->next; current_defer_depth--;
        node->func(node->data); free(node);
    }
}

int zen_defer_depth(void) { return current_defer_depth; }

/* Arena stack */
#define MAX_ARENAS 128
static ZenArena* arena_stack[MAX_ARENAS];
static int arena_stack_ptr = 0;

void zen_arena_push(ZenArena* arena) {
    if (arena_stack_ptr < MAX_ARENAS) {
        arena_stack[arena_stack_ptr++] = arena;
    }
}

void zen_arena_pop(void) {
    if (arena_stack_ptr > 0) {
        arena_stack_ptr--;
    }
}

void* zen_malloc(size_t size) {
    if (arena_stack_ptr > 0) {
        void* p = zen_arena_alloc(arena_stack[arena_stack_ptr - 1], size);
        return p;
    }
    return malloc(size);
}

/* Arena management */

struct ZenArena {
    void* buffer;
    size_t size;
    size_t offset;
};

ZenArena* zen_arena_create(size_t size) {
    if (size == 0) size = 1024 * 1024; // Default 1MB
    ZenArena* arena = (ZenArena*)malloc(sizeof(ZenArena));
    arena->buffer = malloc(size);
    arena->size = size;
    arena->offset = 0;
    return arena;
}

void* zen_arena_alloc(ZenArena* arena, size_t size) {
    if (!arena) return malloc(size);
    // Align to 8 bytes for safety
    size = (size + 7) & ~7;
    if (arena->offset + size > arena->size) {
        // Fallback to malloc if arena is full for the bootstrap compiler
        return malloc(size);
    }
    void* ptr = (char*)arena->buffer + arena->offset;
    arena->offset += size;
    return ptr;
}

void zen_arena_reset(ZenArena* arena) {
    if (arena) arena->offset = 0;
}

void zen_arena_free(ZenArena* arena) {
    if (arena) {
        if (arena->buffer) {
            memset(arena->buffer, 0xCC, arena->size);
            free(arena->buffer);
        }
        free(arena);
    }
}

/* Memory Module Functions */

ZenValue Memory_create_arena(ZenValue size) {
    size_t s = 0;
    if (size.type == ZEN_INTEGER) s = (size_t)size.as.integer;
    return zen_val_arena(zen_arena_create(s));
}

ZenValue Memory_free_arena(ZenValue arena) {
    if (arena.type == ZEN_ARENA) {
        zen_arena_free(arena.as.arena);
    }
    return Zen_nothing;
}

ZenValue Memory_reset_arena(ZenValue arena) {
    if (arena.type == ZEN_ARENA) {
        zen_arena_reset(arena.as.arena);
    }
    return Zen_nothing;
}

ZenValue Memory_push_arena(ZenValue arena) {
    if (arena.type == ZEN_ARENA) {
        zen_arena_push(arena.as.arena);
    }
    return Zen_nothing;
}

ZenValue Memory_pop_arena(void) {
    zen_arena_pop();
    return Zen_nothing;
}

ZenValue ZenValue_get_index(ZenValue obj, ZenValue index) {
    if (obj.type == ZEN_LIST) {
        return ZenList_get(obj.as.list, (int)index.as.integer);
    } else if (obj.type == ZEN_MAP) {
        return ZenMap_get(obj.as.map, index);
    }
    return zen_make_null();
}

void ZenValue_set_index(ZenValue obj, ZenValue index, ZenValue value) {
    if (obj.type == ZEN_LIST) {
        ZenList_set(obj.as.list, (int)index.as.integer, value);
    } else if (obj.type == ZEN_MAP) {
        ZenMap_set(obj.as.map, index, value);
    }
}
ZenValue ZenValue_is_type_name(ZenValue val, const char* tn) {
    if (strcmp(tn, "Error") == 0) return zen_bool(val.type == ZEN_ERROR);
    if (strcmp(tn, "String") == 0) return zen_bool(val.type == ZEN_STRING);
    if (strcmp(tn, "Integer") == 0) return zen_bool(val.type == ZEN_INTEGER);
    if (strcmp(tn, "Decimal") == 0) return zen_bool(val.type == ZEN_DECIMAL);
    if (strcmp(tn, "Boolean") == 0) return zen_bool(val.type == ZEN_BOOLEAN);
    if (strcmp(tn, "List") == 0) return zen_bool(val.type == ZEN_LIST);
    if (strcmp(tn, "Map") == 0) return zen_bool(val.type == ZEN_MAP);
    if (strcmp(tn, "Nothing") == 0) return zen_bool(val.type == ZEN_NOTHING);
    
    return zen_bool(false);
}
