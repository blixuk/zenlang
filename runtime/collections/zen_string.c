#include "../bootstrap_runtime.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>

const char* ZenString_get_pointer(ZenValue value) {
    if (value.type != ZEN_STRING) return NULL;
    return value.as.string;
}

static char* internal_ZenString_new(const char* s) {
    if (!s) return NULL;
    char* res = malloc(strlen(s) + 1);
    strcpy(res, s);
    return res;
}

ZenValue ZenString_get_length(ZenValue string) {
    const char* s = ZenString_get_pointer(string);
    if (!s) return ZenValue_make_integer(0);
    return ZenValue_make_integer((int)strlen(s));
}

ZenValue ZenString_get_character_at_index(ZenValue string, ZenValue index) {
    if (string.type != ZEN_STRING) return ZenValue_make_nothing();
    int idx = (int)index.as.integer;
    const char* s = string.as.string;
    int len = (int)strlen(s);
    if (idx < 0) idx += len;
    if (idx < 0 || idx >= len) return ZenValue_make_nothing();
    char buf[2] = {s[idx], 0};
    return ZenValue_make_string(buf);
}

ZenValue ZenString_concatenate(ZenValue s1_v, ZenValue s2_v) {
    ZenValue s1_str = (s1_v.type == ZEN_STRING) ? s1_v : ZenValue_to_string(s1_v);
    ZenValue s2_str = (s2_v.type == ZEN_STRING) ? s2_v : ZenValue_to_string(s2_v);
    
    const char* s1 = s1_str.as.string;
    const char* s2 = s2_str.as.string;
    
    if (!s1) return ZenValue_make_string(s2 ? s2 : "");
    if (!s2) return ZenValue_make_string(s1);
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char* res = malloc(len1 + len2 + 1);
    strcpy(res, s1);
    strcat(res, s2);
    ZenValue z = ZenValue_make_string(res);
    free(res);
    return z;
}

ZenValue ZenString_replace(ZenValue string, ZenValue old_value, ZenValue new_value) {
    const char* s = ZenString_get_pointer(string);
    const char* old_s = ZenString_get_pointer(old_value);
    const char* new_s = ZenString_get_pointer(new_value);
    if (!s || !old_s || !new_s) return string;
    
    size_t old_len = strlen(old_s);
    if (old_len == 0) return string;
    int count = 0;
    const char *tmp = s;
    while ((tmp = strstr(tmp, old_s))) {
        count++;
        tmp += old_len;
    }
    if (count == 0) return string;
    size_t new_len = strlen(new_s);
    size_t res_len = strlen(s) + (new_len - old_len) * count;
    char* res = malloc(res_len + 1);
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
    ZenValue z = ZenValue_make_string(res);
    free(res);
    return z;
}

ZenValue ZenValue_to_string(ZenValue value) {
    char buf[128];
    switch (value.type) {
        case ZEN_INTEGER: sprintf(buf, "%lld", value.as.integer); return ZenValue_make_string(buf);
        case ZEN_DECIMAL: sprintf(buf, "%f", value.as.decimal); return ZenValue_make_string(buf);
        case ZEN_BOOLEAN: return ZenValue_make_string(value.as.boolean ? "true" : "false");
        case ZEN_STRING: return value;
        case ZEN_NOTHING: return ZenValue_make_string("Nothing");
        case ZEN_DEFAULT: return ZenValue_make_string("Default");
        case ZEN_ERROR: return ZenValue_make_string("Error");
        case ZEN_ARENA: return ZenValue_make_string("Arena");
        case ZEN_SET: {
            if (!value.as.set) return ZenValue_make_string("Set([])");
            ZenValue l = ZenSet_to_list(value);
            ZenValue s = ZenValue_to_string(l);
            char buf_s[256];
            snprintf(buf_s, sizeof(buf_s), "Set(%s)", (s.type == ZEN_STRING && s.as.string) ? s.as.string : "[]");
            return ZenValue_make_string(buf_s);
        }
        case ZEN_AST_NODE: {
            if (!value.as.ast_node) return ZenValue_make_string("AstNode(null)");
            char buf_a[128];
            snprintf(buf_a, sizeof(buf_a), "AstNode(kind=%d, line=%d, col=%d)",
                     (int)value.as.ast_node->kind, (int)value.as.ast_node->line, (int)value.as.ast_node->col);
            return ZenValue_make_string(buf_a);
        }
        case ZEN_TOKEN: {
            if (!value.as.token) return ZenValue_make_string("Token(null)");
            char buf_t[128];
            snprintf(buf_t, sizeof(buf_t), "Token(kind=%d, line=%d, col=%d, len=%d)",
                     (int)value.as.token->kind, (int)value.as.token->line, (int)value.as.token->col, (int)value.as.token->length);
            return ZenValue_make_string(buf_t);
        }
        case ZEN_VARIANT: {
            if (!value.as.variant) return ZenValue_make_string("Variant(null)");
            char buf_v[256];
            sprintf(buf_v, "%s.%s", value.as.variant->enum_name.as.string, value.as.variant->variant_name.as.string);
            return ZenValue_make_string(buf_v);
        }
        case ZEN_LIST: {
            if (!value.as.list) return ZenValue_make_string("[]");
            // Generous buffer for nested stringification
            size_t cap = (size_t)value.as.list->count * 64 + 8;
            if (cap < 16) cap = 16;
            char* res = malloc(cap);
            size_t len = 0;
            res[len++] = '[';
            res[len] = '\0';
            for (int i = 0; i < value.as.list->count; i++) {
                ZenValue item = value.as.list->items[i];
                ZenValue s_v = ZenValue_to_string(item);
                const char* s = (s_v.type == ZEN_STRING && s_v.as.string) ? s_v.as.string : "";
                int need_quotes = (item.type == ZEN_STRING);
                size_t add = strlen(s) + (need_quotes ? 2 : 0) + 2;
                if (len + add + 1 >= cap) {
                    cap = (len + add + 1) * 2;
                    res = realloc(res, cap);
                }
                if (need_quotes) res[len++] = '\'';
                memcpy(res + len, s, strlen(s));
                len += strlen(s);
                if (need_quotes) res[len++] = '\'';
                if (i < value.as.list->count - 1) {
                    res[len++] = ',';
                    res[len++] = ' ';
                }
                res[len] = '\0';
            }
            res[len++] = ']';
            res[len] = '\0';
            ZenValue z = ZenValue_make_string(res);
            free(res);
            return z;
        }
        case ZEN_MAP: {
            if (!value.as.map) return ZenValue_make_string("{}");
            size_t cap = (size_t)value.as.map->count * 64 + 16;
            if (cap < 16) cap = 16;
            char* res = malloc(cap);
            size_t len = 0;
            res[len++] = '{';
            res[len] = '\0';
            for (int i = 0; i < value.as.map->count; i++) {
                ZenValue k_v = ZenValue_to_string(value.as.map->entries[i].key);
                ZenValue v_v = ZenValue_to_string(value.as.map->entries[i].value);
                const char* ks = (k_v.type == ZEN_STRING && k_v.as.string) ? k_v.as.string : "";
                const char* vs = (v_v.type == ZEN_STRING && v_v.as.string) ? v_v.as.string : "";
                size_t add = strlen(ks) + strlen(vs) + 4;
                if (len + add + 1 >= cap) {
                    cap = (len + add + 1) * 2;
                    res = realloc(res, cap);
                }
                memcpy(res + len, ks, strlen(ks));
                len += strlen(ks);
                res[len++] = ':';
                res[len++] = ' ';
                memcpy(res + len, vs, strlen(vs));
                len += strlen(vs);
                if (i < value.as.map->count - 1) {
                    res[len++] = ',';
                    res[len++] = ' ';
                }
                res[len] = '\0';
            }
            res[len++] = '}';
            res[len] = '\0';
            ZenValue z = ZenValue_make_string(res);
            free(res);
            return z;
        }
        default: return ZenValue_make_string("Object");
    }
}

ZenValue ZenString_to_uppercase(ZenValue string) {
    const char* s = ZenString_get_pointer(string);
    if (!s) return ZenValue_make_nothing();
    char* res = internal_ZenString_new(s);
    for (int i = 0; res[i]; i++) {
        if (res[i] >= 'a' && res[i] <= 'z') res[i] -= 32;
    }
    ZenValue z = ZenValue_make_string(res);
    free(res);
    return z;
}

ZenValue ZenString_to_lowercase(ZenValue string) {
    const char* s = ZenString_get_pointer(string);
    if (!s) return ZenValue_make_nothing();
    char* res = internal_ZenString_new(s);
    for (int i = 0; res[i]; i++) {
        if (res[i] >= 'A' && res[i] <= 'Z') res[i] += 32;
    }
    ZenValue z = ZenValue_make_string(res);
    free(res);
    return z;
}

ZenValue ZenString_trim(ZenValue string) {
    const char* s = ZenString_get_pointer(string);
    if (!s) return ZenValue_make_nothing();
    int len = strlen(s);
    if (len == 0) return ZenValue_make_string("");
    int start = 0;
    while (start < len && isspace((unsigned char)s[start])) start++;
    if (start == len) return ZenValue_make_string("");
    int end = len - 1;
    while (end > start && isspace((unsigned char)s[end])) end--;
    int new_len = end - start + 1;
    char* res = malloc(new_len + 1);
    strncpy(res, s + start, new_len);
    res[new_len] = '\0';
    ZenValue z = ZenValue_make_string(res);
    free(res);
    return z;
}

ZenValue ZenString_find_index(ZenValue string, ZenValue substring) {
    const char* s = ZenString_get_pointer(string);
    const char* sub = ZenString_get_pointer(substring);
    if (!s || !sub) return ZenValue_make_integer(-1);
    char* pos = strstr(s, sub);
    if (!pos) return ZenValue_make_integer(-1);
    return ZenValue_make_integer((int)(pos - s));
}

ZenValue ZenString_index_of(ZenValue string, ZenValue substring) {
    return ZenString_find_index(string, substring);
}

ZenValue ZenString_at(ZenValue string, ZenValue index) {
    return ZenString_get_character_at_index(string, index);
}

ZenValue ZenString_byte_at(ZenValue string, ZenValue index) {
    const char* s = ZenString_get_pointer(string);
    if (!s || index.type != ZEN_INTEGER) return ZenValue_make_integer(-1LL);
    long long idx = index.as.integer;
    if (idx < 0 || idx >= (long long)strlen(s)) return ZenValue_make_integer(-1LL);
    return ZenValue_make_integer((long long)((unsigned char)s[idx]));
}

ZenValue ZenString_contains(ZenValue string, ZenValue substring) {
    ZenValue index = ZenString_find_index(string, substring);
    return ZenValue_make_boolean(index.as.integer != -1);
}

ZenValue ZenString_starts_with(ZenValue string, ZenValue prefix) {
    const char* s = ZenString_get_pointer(string);
    const char* pre = ZenString_get_pointer(prefix);
    if (!s || !pre) return ZenValue_make_boolean(false);
    return ZenValue_make_boolean(strncmp(s, pre, strlen(pre)) == 0);
}

ZenValue ZenString_ends_with(ZenValue string, ZenValue suffix) {
    const char* s = ZenString_get_pointer(string);
    const char* suf = ZenString_get_pointer(suffix);
    if (!s || !suf) return ZenValue_make_boolean(false);
    int len_s = strlen(s);
    int len_sub = strlen(suf);
    if (len_sub > len_s) return ZenValue_make_boolean(false);
    return ZenValue_make_boolean(strcmp(s + len_s - len_sub, suf) == 0);
}

ZenValue ZenString_get_substring(ZenValue string, ZenValue start_v, ZenValue end_v) {
    const char* s = ZenString_get_pointer(string);
    if (!s) return ZenValue_make_string("");
    int len = strlen(s);
    int start = (start_v.type == ZEN_INTEGER) ? (int)start_v.as.integer : 0;
    int end = (end_v.type == ZEN_INTEGER) ? (int)end_v.as.integer : len;
    if (start < 0) start = 0;
    if (end > len) end = len;
    if (start >= end) return ZenValue_make_string("");
    char* res = malloc(end - start + 1);
    strncpy(res, s + start, end - start);
    res[end - start] = '\0';
    ZenValue z = ZenValue_make_string(res);
    free(res);
    return z;
}

ZenValue ZenString_split(ZenValue string, ZenValue separator) {
    const char* s = ZenString_get_pointer(string);
    const char* sep = ZenString_get_pointer(separator);
    ZenList* list = ZenList_new();
    if (!s || !sep) return ZenValue_from_list(list);
    char* str = strdup(s);
    int sep_len = strlen(sep);
    char* p = str;
    char* match;
    while ((match = strstr(p, sep)) != NULL) {
        *match = '\0';
        ZenList_append_value(ZenValue_from_list(list), ZenValue_make_string(p));
        p = match + sep_len;
    }
    ZenList_append_value(ZenValue_from_list(list), ZenValue_make_string(p));
    free(str);
    return ZenValue_from_list(list);
}

ZenValue ZenString_join(ZenValue list_v, ZenValue separator) {
    if (list_v.type != ZEN_LIST) return ZenValue_make_string("");
    ZenList* list = list_v.as.list;
    const char* sep = ZenString_get_pointer(separator);
    if (!list || list->count == 0) return ZenValue_make_string("");
    int total_len = 0;
    int sep_len = sep ? strlen(sep) : 0;
    for (int i = 0; i < list->count; i++) {
        ZenValue item_str = ZenValue_to_string(list->items[i]);
        total_len += strlen(item_str.as.string);
    }
    total_len += sep_len * (list->count - 1);
    char* res = malloc(total_len + 1);
    res[0] = '\0';
    for (int i = 0; i < list->count; i++) {
        ZenValue item_str = ZenValue_to_string(list->items[i]);
        strcat(res, item_str.as.string);
        if (i < list->count - 1 && sep) strcat(res, sep);
    }
    ZenValue z = ZenValue_make_string(res);
    free(res);
    return z;
}
