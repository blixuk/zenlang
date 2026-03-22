#include "zen_object.h"
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdio.h>

int ZenString_length(ZenString s) {
    if (!s) return 0;
    return (int)strlen(s);
}

ZenString ZenString_create(const char* s) {
    if (!s) return "";
    int len = strlen(s);
    char* res = (char*)zen_alloc(len + 1);
    strcpy(res, s);
    return res;
}

ZenString ZenString_at(ZenString s, int index) {
    if (!s || index < 0 || index >= (int)strlen(s)) return "";
    char* res = (char*)zen_alloc(2);
    res[0] = s[index];
    res[1] = '\0';
    return res;
}

ZenString ZenString_substring(ZenString s, int start, int end) {
    if (!s) return "";
    int len = (int)strlen(s);
    if (start < 0) start = 0;
    if (end > len) end = len;
    if (start >= end) return "";

    int sub_len = end - start;
    char* res = (char*)zen_alloc(sub_len + 1);
    memcpy(res, s + start, sub_len);
    res[sub_len] = '\0';
    return res;
}

ZenList* ZenString_split(ZenString s, ZenString sep) {
    ZenList* list = ZenList_create();
    if (!s) return list;
    
    char* copy = strdup(s); // standard libc, maybe replace later if we want total control
    char* token = strtok(copy, sep);
    while (token != NULL) {
        ZenList_append(list, zen_str(strdup(token)));
        token = strtok(NULL, sep);
    }
    // Note: copy is malloced by strdup, so we should free it.
    // Also strdup uses standard malloc. Ideally we should have zen_strdup.
    free(copy); // Using standard free because strdup used standard malloc
    return list;
}

ZenString ZenString_join(ZenList* parts, ZenString sep) {
    if (!parts || parts->count == 0) return "";
    
    int sep_len = (int)strlen(sep);
    int total_len = 0;
    for (int i = 0; i < parts->count; i++) {
        // Assert type is STRING or convert?
        // For now assume string
        total_len += strlen(parts->items[i].as.string);
        if (i < parts->count - 1) total_len += sep_len;
    }
    
    char* res = (char*)zen_alloc(total_len + 1);
    res[0] = '\0';
    for (int i = 0; i < parts->count; i++) {
        strcat(res, parts->items[i].as.string);
        if (i < parts->count - 1) strcat(res, sep);
    }
    return res;
}

ZenString ZenString_concat(ZenString s1, ZenString s2) {
    if (!s1) return s2 ? s2 : "";
    if (!s2) return s1;
    int len1 = strlen(s1);
    int len2 = strlen(s2);
    char* res = (char*)zen_alloc(len1 + len2 + 1);
    strcpy(res, s1);
    strcat(res, s2);
    return res;
}

ZenString ZenString_replace(ZenString s, ZenString old_s, ZenString new_s) {
    if (!s || !old_s || !new_s) return s;
    char *result;
    int i, cnt = 0;
    int newlen = strlen(new_s);
    int oldlen = strlen(old_s);
    for (i = 0; s[i] != '\0'; i++) {
        if (strstr(&s[i], old_s) == &s[i]) {
            cnt++;
            i += oldlen - 1;
        }
    }
    result = (char*)zen_alloc(i + cnt * (newlen - oldlen) + 1);
    i = 0;
    while (*s) {
        if (strstr(s, old_s) == s) {
            strcpy(&result[i], new_s);
            i += newlen;
            s += oldlen;
        } else
            result[i++] = *s++;
    }
    result[i] = '\0';
    return result;
}

ZenString ZenString_to_upper(ZenString s) {
    if (!s) return "";
    int len = strlen(s);
    char* res = (char*)zen_alloc(len + 1);
    for (int i = 0; i < len; i++) {
        res[i] = toupper(s[i]);
    }
    res[len] = '\0';
    return res;
}

ZenString ZenString_str(ZenVariant x) {
    char buf[128];
    switch (x.type) {
        case ZEN_INTEGER:
            sprintf(buf, "%lld", x.as.integer);
            return ZenString_create(buf);
        case ZEN_DECIMAL:
            sprintf(buf, "%f", x.as.decimal);
            return ZenString_create(buf);
        case ZEN_BOOLEAN:
            return ZenString_create(x.as.boolean ? "true" : "false");
        case ZEN_STRING:
            return ZenString_create(x.as.string ? x.as.string : "null");
        case ZEN_LIST: {
            ZenList* list = x.as.list;
            if (!list) return ZenString_create("[]");
            
            // Initial implementation: join elements
            // Note: This is inefficient but functional for now
            // Need a StringBuilder in future
            char* res = (char*)zen_alloc(1024); // simplistic
            strcpy(res, "[");
            
            for (int i=0; i < list->count; i++) {
                ZenVariant item = list->items[i];
                ZenString item_str = ZenString_str(item);
                strcat(res, item_str);
                
                if (i < list->count - 1) {
                    strcat(res, ", ");
                }
            }
            strcat(res, "]");
            return res;
        }
        case ZEN_NOTHING:
            return ZenString_create("Nothing");
        default:
            return ZenString_create("Unknown");
    }
}

int ZenString_starts_with(ZenString s, ZenString prefix) {
    if (!s || !prefix) return 0;
    size_t len_s = strlen(s);
    size_t len_p = strlen(prefix);
    if (len_p > len_s) return 0;
    return strncmp(s, prefix, len_p) == 0;
}

int ZenString_ends_with(ZenString s, ZenString suffix) {
    if (!s || !suffix) return 0;
    size_t len_s = strlen(s);
    size_t len_p = strlen(suffix);
    if (len_p > len_s) return 0;
    return strcmp(s + len_s - len_p, suffix) == 0;
}

int ZenString_equals(ZenString s1, ZenString s2) {
    if (s1 == s2) return 1;
    if (!s1 || !s2) return 0;
    return strcmp(s1, s2) == 0;
}

int ZenString_index_of(ZenString s, ZenString sub) {
    if (!s || !sub) return -1;
    char* pos = strstr(s, sub);
    if (!pos) return -1;
    return (int)(pos - s);
}
