#include "zen_bytes.h"
#include "collections/zen_list.h"
#include "collections/zen_map.h"
#include "collections/zen_string.h"
#include "zen_ops.h"
#include "zen_object.h"
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>

static const char* zen_cstr(ZenValue v) {
    if (v.type == ZEN_STRING) return ZenString_get_pointer(v);
    return NULL;
}

ZenValue ZenBytes_create_size(ZenValue size) {
    int n = 0;
    if (size.type == ZEN_INTEGER) n = (int)size.as.integer;
    if (n < 0) n = 0;
    ZenValue list = ZenList_make_from_arguments(0);
    for (int i = 0; i < n; i++) {
        ZenList_append_value(list, ZenValue_make_integer(0));
    }
    return list;
}

ZenValue ZenBytes_create_list(ZenValue list) {
    /* Copy list of integers as bytes */
    if (list.type != ZEN_LIST) return ZenList_make_from_arguments(0);
    ZenValue out = ZenList_make_from_arguments(0);
    ZenValue len_v = ZenList_get_length(list);
    int n = (len_v.type == ZEN_INTEGER) ? (int)len_v.as.integer : 0;
    for (int i = 0; i < n; i++) {
        ZenValue idx = ZenValue_make_integer(i);
        ZenValue b = ZenList_get_value_at_index(list, idx);
        int v = 0;
        if (b.type == ZEN_INTEGER) v = (int)b.as.integer & 0xFF;
        ZenList_append_value(out, ZenValue_make_integer(v));
    }
    return out;
}

ZenValue ZenBytes_string_to_bytes(ZenValue s) {
    const char* str = zen_cstr(s);
    ZenValue out = ZenList_make_from_arguments(0);
    if (!str) return out;
    for (const unsigned char* p = (const unsigned char*)str; *p; p++) {
        ZenList_append_value(out, ZenValue_make_integer((int)*p));
    }
    return out;
}

/* Layout must match generated `struct bytes_Bytes { ZenValue _data; }`. */
typedef struct ZenBytesBox {
    ZenValue _data;
} ZenBytesBox;

ZenValue ZenBytes_from_string(ZenValue s) {
    ZenValue data = ZenBytes_string_to_bytes(s);
    ZenBytesBox* box = (ZenBytesBox*)malloc(sizeof(ZenBytesBox));
    if (!box) return ZenValue_make_nothing();
    memset(box, 0, sizeof(ZenBytesBox));
    box->_data = data;
    return ZenValue_from_object(box);
}

ZenValue ZenBytes_bytes_to_string(ZenValue bytes) {
    if (bytes.type != ZEN_LIST) return ZenValue_make_string("");
    ZenValue len_v = ZenList_get_length(bytes);
    int n = (len_v.type == ZEN_INTEGER) ? (int)len_v.as.integer : 0;
    char* buf = malloc((size_t)n + 1);
    if (!buf) return ZenValue_make_string("");
    for (int i = 0; i < n; i++) {
        ZenValue b = ZenList_get_value_at_index(bytes, ZenValue_make_integer(i));
        buf[i] = (char)((b.type == ZEN_INTEGER) ? (b.as.integer & 0xFF) : 0);
    }
    buf[n] = '\0';
    ZenValue v = ZenValue_make_string(buf);
    free(buf);
    return v;
}

static int map_get_int(ZenValue map, const char* key) {
    ZenValue k = ZenValue_make_string(key);
    ZenValue v = ZenMap_get_value_at_key(map, k);
    if (v.type == ZEN_INTEGER) return (int)v.as.integer;
    if (v.type == ZEN_DECIMAL) return (int)v.as.decimal;
    return 0;
}

static const char* map_get_str(ZenValue map, const char* key) {
    ZenValue k = ZenValue_make_string(key);
    ZenValue v = ZenMap_get_value_at_key(map, k);
    return zen_cstr(v);
}

/* Iterate map keys in insertion order if available. */
static void pack_field(ZenValue* out, const char* type_name, long long value) {
    if (!type_name) return;
    if (strcmp(type_name, "u8") == 0 || strcmp(type_name, "i8") == 0) {
        ZenList_append_value(*out, ZenValue_make_integer(value & 0xFF));
    } else if (strcmp(type_name, "u16") == 0 || strcmp(type_name, "i16") == 0) {
        ZenList_append_value(*out, ZenValue_make_integer(value & 0xFF));
        ZenList_append_value(*out, ZenValue_make_integer((value >> 8) & 0xFF));
    } else if (strcmp(type_name, "u32") == 0 || strcmp(type_name, "i32") == 0) {
        uint32_t u = (uint32_t)value;
        ZenList_append_value(*out, ZenValue_make_integer(u & 0xFF));
        ZenList_append_value(*out, ZenValue_make_integer((u >> 8) & 0xFF));
        ZenList_append_value(*out, ZenValue_make_integer((u >> 16) & 0xFF));
        ZenList_append_value(*out, ZenValue_make_integer((u >> 24) & 0xFF));
    }
}

ZenValue ZenBytes_pack_binary(ZenValue spec, ZenValue data) {
    ZenValue out = ZenList_make_from_arguments(0);
    if (spec.type != ZEN_MAP || data.type != ZEN_MAP) return out;
    ZenValue keys = ZenMap_get_keys(spec);
    ZenValue klen = ZenList_get_length(keys);
    int n = (klen.type == ZEN_INTEGER) ? (int)klen.as.integer : 0;
    for (int i = 0; i < n; i++) {
        ZenValue key = ZenList_get_value_at_index(keys, ZenValue_make_integer(i));
        ZenValue type_v = ZenMap_get_value_at_key(spec, key);
        const char* type_name = zen_cstr(type_v);
        ZenValue val = ZenMap_get_value_at_key(data, key);
        long long iv = 0;
        if (val.type == ZEN_INTEGER) iv = val.as.integer;
        else if (val.type == ZEN_DECIMAL) iv = (long long)val.as.decimal;
        pack_field(&out, type_name, iv);
    }
    return out;
}

static int read_u8(ZenValue bytes, int* idx) {
    ZenValue b = ZenList_get_value_at_index(bytes, ZenValue_make_integer(*idx));
    (*idx)++;
    return (b.type == ZEN_INTEGER) ? (int)(b.as.integer & 0xFF) : 0;
}

static int read_u16(ZenValue bytes, int* idx) {
    int lo = read_u8(bytes, idx);
    int hi = read_u8(bytes, idx);
    return lo | (hi << 8);
}

static long long read_u32(ZenValue bytes, int* idx) {
    long long b0 = read_u8(bytes, idx);
    long long b1 = read_u8(bytes, idx);
    long long b2 = read_u8(bytes, idx);
    long long b3 = read_u8(bytes, idx);
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24);
}

ZenValue ZenBytes_unpack_binary(ZenValue spec, ZenValue bytes) {
    ZenValue out = ZenMap_make_from_arguments(0);
    if (spec.type != ZEN_MAP || bytes.type != ZEN_LIST) return out;
    ZenValue keys = ZenMap_get_keys(spec);
    ZenValue klen = ZenList_get_length(keys);
    int n = (klen.type == ZEN_INTEGER) ? (int)klen.as.integer : 0;
    int idx = 0;
    for (int i = 0; i < n; i++) {
        ZenValue key = ZenList_get_value_at_index(keys, ZenValue_make_integer(i));
        ZenValue type_v = ZenMap_get_value_at_key(spec, key);
        const char* type_name = zen_cstr(type_v);
        long long val = 0;
        if (!type_name) continue;
        if (strcmp(type_name, "u8") == 0 || strcmp(type_name, "i8") == 0) {
            val = read_u8(bytes, &idx);
            if (type_name[0] == 'i' && val > 127) val -= 256;
        } else if (strcmp(type_name, "u16") == 0 || strcmp(type_name, "i16") == 0) {
            val = read_u16(bytes, &idx);
            if (type_name[0] == 'i' && val > 32767) val -= 65536;
        } else if (strcmp(type_name, "u32") == 0 || strcmp(type_name, "i32") == 0) {
            val = read_u32(bytes, &idx);
            if (type_name[0] == 'u') val = (long long)(uint32_t)val;
        }
        ZenMap_set_value_at_key(out, key, ZenValue_make_integer(val));
    }
    return out;
}
