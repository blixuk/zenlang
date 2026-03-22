#include "bootstrap_runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>

/* Constructors */

ZenList* ZenList_from_args(int n, ...) {
    ZenList* list = ZenList_create();
    va_list args;
    va_start(args, n);
    for (int i = 0; i < n; i++) {
        ZenVariant item = va_arg(args, ZenVariant);
        ZenList_append(list, item);
    }
    va_end(args);
    return list;
}

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

ZenValue ZenList_length(ZenList* list) {
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

ZenMap* ZenMap_from_args(int n, ...) {
    ZenMap* map = ZenMap_create();
    va_list args;
    va_start(args, n);
    for (int i = 0; i < n; i++) {
        ZenVariant key = va_arg(args, ZenVariant);
        ZenVariant value = va_arg(args, ZenVariant);
        ZenMap_set(map, key, value);
    }
    va_end(args);
    return map;
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

ZenValue ZenMap_length(ZenMap* map) {
    if (!map) return zen_int(0);
    return zen_int(map->count);
}

/* ZenValue Operations */

ZenValue ZenValue_add(ZenValue a, ZenValue b) {
    if (a.type == ZEN_INTEGER && b.type == ZEN_INTEGER) return zen_int(a.as.integer + b.as.integer);
    if (a.type == ZEN_DECIMAL || b.type == ZEN_DECIMAL) {
        double va = (a.type == ZEN_INTEGER) ? (double)a.as.integer : a.as.decimal;
        double vb = (b.type == ZEN_INTEGER) ? (double)b.as.integer : b.as.decimal;
        return zen_float(va + vb);
    }
    if (a.type == ZEN_STRING || b.type == ZEN_STRING) {
        ZenString s1 = ZenString_str(a);
        ZenString s2 = ZenString_str(b);
        ZenValue res = ZenString_concat(s1, s2);
        free(s1);
        free(s2);
        return res;
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

ZenValue ZenString_length(ZenString s) {
    if (!s) return zen_int(0);
    return zen_int((int)strlen(s));
}

ZenValue ZenString_at(ZenString s, int index) {
    if (!s || index < 0 || index >= (int)strlen(s)) return zen_str("");
    char* res = malloc(2);
    res[0] = s[index];
    res[1] = '\0';
    return zen_str(res);
}

ZenValue ZenString_equals(ZenString s1, ZenString s2) {
    if (s1 == s2) return zen_bool(true);
    if (!s1 || !s2) return zen_bool(false);
    return zen_bool(strcmp(s1, s2) == 0);
}

ZenValue ZenString_concat(ZenString s1, ZenString s2) {
    if (!s1) return zen_str(s2 ? s2 : "");
    if (!s2) return zen_str(s1);
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char* res = malloc(len1 + len2 + 1);
    strcpy(res, s1);
    strcat(res, s2);
    return zen_str(res);
}

ZenValue ZenString_replace(ZenString s, ZenString old_s, ZenString new_s) {
    if (!s || !old_s || !new_s) return zen_str(s);
    size_t old_len = strlen(old_s);
    if (old_len == 0) return zen_str(s);
    int count = 0;
    const char *tmp = s;
    while ((tmp = strstr(tmp, old_s))) {
        count++;
        tmp += old_len;
    }
    if (count == 0) return zen_str(s);
    size_t new_len = strlen(new_s);
    size_t res_len = strlen(s) + (new_len - old_len) * count;
    char *res = malloc(res_len + 1);
    char *dst = res;
    const char *src = s;
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

ZenString ZenString_str(ZenVariant x) {
    char buf[128];
    switch (x.type) {
        case ZEN_INTEGER: sprintf(buf, "%lld", x.as.integer); return ZenString_create(buf);
        case ZEN_DECIMAL: sprintf(buf, "%f", x.as.decimal); return ZenString_create(buf);
        case ZEN_BOOLEAN: return ZenString_create(x.as.boolean ? "true" : "false");
        case ZEN_STRING: return ZenString_create(x.as.string);
        case ZEN_NOTHING: return ZenString_create("Nothing");
        default: return ZenString_create("Object");
    }
}

ZenValue ZenValue_str(ZenValue v) {
    return zen_str(ZenString_str(v));
}

ZenValue ZenString_to_upper(ZenString s) {
    if (!s) return zen_make_null();
    char* res = ZenString_create(s);
    for (int i = 0; res[i]; i++) {
        if (res[i] >= 'a' && res[i] <= 'z') res[i] -= 32;
    }
    return zen_str(res);
}

ZenValue ZenString_to_lower(ZenString s) {
    if (!s) return zen_make_null();
    char* res = ZenString_create(s);
    for (int i = 0; res[i]; i++) {
        if (res[i] >= 'A' && res[i] <= 'Z') res[i] += 32;
    }
    return zen_str(res);
}

#include <ctype.h>
ZenValue ZenString_trim(ZenString s) {
    if (!s) return zen_make_null();
    int len = strlen(s);
    if (len == 0) return zen_str("");
    int start = 0;
    while (start < len && isspace((unsigned char)s[start])) start++;
    if (start == len) return zen_str("");
    int end = len - 1;
    while (end > start && isspace((unsigned char)s[end])) end--;
    int new_len = end - start + 1;
    char* res = malloc(new_len + 1);
    strncpy(res, s + start, new_len);
    res[new_len] = '\0';
    return zen_str(res);
}

ZenValue ZenString_index_of(ZenString s, ZenString sub) {
    if (!s || !sub) return zen_int(-1);
    char* pos = strstr(s, sub);
    if (!pos) return zen_int(-1);
    return zen_int((int)(pos - s));
}

/* IO functions */

ZenValue IO_write(ZenValue v) {
    ZenString s = ZenString_str(v);
    if (s) {
        printf("%s", s);
        free(s);
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
                char* next_str = ZenString_replace(final_str, buf, val_str).as.string;
                if (final_str != s) free(final_str);
                final_str = next_str;
                free(val_str);
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
ZenValue IO_error(ZenValue v) { 
    ZenString s = ZenString_str(v);
    if (s) fprintf(stderr, "Error: %s\n", s); 
    return zen_make_null();
}

ZenValue IO_write_file(ZenValue path_val, ZenValue content_val) {
    ZenString path = ZenString_str(path_val);
    ZenString content = ZenString_str(content_val);
    FILE* f = fopen(path, "w");
    if (f) { fprintf(f, "%s", content); fclose(f); }
    return zen_make_null();
}

ZenValue IO_read_file(ZenValue path_val) {
    ZenString path = ZenString_str(path_val);
    FILE* f = fopen(path, "r");
    if (!f) return zen_make_null();
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = malloc(len + 1);
    fread(buf, 1, len, f);
    buf[len] = '\0';
    fclose(f);
    return zen_str(buf);
}

ZenValue IO_file_exists(ZenValue path_val) {
    ZenString path = ZenString_str(path_val);
    FILE* f = fopen(path, "r");
    if (f) {
        fclose(f);
        return zen_bool(true);
    }
    return zen_bool(false);
}

/* Sys functions */

ZenValue Sys_exit(int code) { exit(code); return zen_make_null(); }
static ZenList* sys_args = NULL;
void _Sys_init_args(int argc, char** argv) {
    sys_args = ZenList_create();
    for (int i=0; i < argc; i++) {
        ZenList_append(sys_args, zen_str(ZenString_create(argv[i])));
    }
}
ZenValue Sys_get_args() { return zen_val_list(_Sys_get_args()); }
ZenList* _Sys_get_args() { return sys_args ? sys_args : ZenList_create(); }
ZenValue Sys_get_env(ZenString name) {
    char* val = getenv(name);
    return val ? zen_str(ZenString_create(val)) : zen_make_null();
}

ZenValue ZenString_starts_with(ZenString s, ZenString prefix) {
    if (!s || !prefix) return zen_bool(false);
    return zen_bool(strncmp(s, prefix, strlen(prefix)) == 0);
}

ZenValue ZenString_ends_with(ZenString s, ZenString suffix) {
    if (!s || !suffix) return zen_bool(false);
    int len_s = strlen(s);
    int len_sub = strlen(suffix);
    if (len_sub > len_s) return zen_bool(false);
    return zen_bool(strcmp(s + len_s - len_sub, suffix) == 0);
}

ZenValue ZenString_substring(ZenString s, int start, int end) {
    if (!s) return zen_str("");
    int len = strlen(s);
    if (start < 0) start = 0;
    if (end > len) end = len;
    if (start >= end) return zen_str("");
    char* res = malloc(end - start + 1);
    strncpy(res, s + start, end - start);
    res[end - start] = '\0';
    return zen_str(res);
}

ZenValue ZenString_split(ZenString s, ZenString sep) {
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

ZenValue ZenString_join(ZenList* parts, ZenString sep) {
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
