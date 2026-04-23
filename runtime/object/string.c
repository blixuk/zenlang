#include "zen_object.h"
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdio.h>

ZenValue ZenString_count(ZenValue s) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    if (!ps) return zen_int(0);
    return zen_int((int)strlen(ps));
}

ZenString ZenString_create(const char* s) {
    if (!s) return "";
    int len = strlen(s);
    char* res = (char*)zen_alloc(len + 1);
    strcpy(res, s);
    return res;
}

ZenValue ZenString_at(ZenValue s, ZenValue index) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    int idx = ZEN_UNBOX(index, (int)0);
    if (!ps || idx < 0 || idx >= (int)strlen(ps)) return zen_str("");
    char* res = (char*)zen_alloc(2);
    res[0] = ps[idx];
    res[1] = '\0';
    return zen_str(res);
}

ZenValue ZenString_substring(ZenValue s, ZenValue start, ZenValue end) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    int istart = ZEN_UNBOX(start, (int)0);
    int iend = ZEN_UNBOX(end, (int)0);
    if (!ps) return zen_str("");
    int len = (int)strlen(ps);
    if (istart < 0) istart = 0;
    if (iend > len) iend = len;
    if (istart >= iend) return zen_str("");

    int sub_len = iend - istart;
    char* res = (char*)zen_alloc(sub_len + 1);
    memcpy(res, ps + istart, sub_len);
    res[sub_len] = '\0';
    return zen_str(res);
}

ZenValue ZenString_split(ZenValue s, ZenValue sep) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    char* psep = ZEN_UNBOX(sep, (char*)0);
    ZenList* list = ZenList_create();
    if (!ps || !psep) return zen_val_list(list);
    
    char* copy = strdup(ps);
    char* token = strtok(copy, psep);
    while (token != NULL) {
        ZenList_append(list, zen_str(strdup(token)));
        token = strtok(NULL, psep);
    }
    free(copy);
    return zen_val_list(list);
}

ZenValue ZenString_join(ZenList* parts, ZenValue sep) {
    char* psep = ZEN_UNBOX(sep, (char*)0);
    if (!parts || parts->count == 0) return zen_str("");
    
    int sep_len = (int)strlen(psep);
    int total_len = 0;
    for (int i = 0; i < parts->count; i++) {
        total_len += strlen(parts->items[i].as.string);
        if (i < parts->count - 1) total_len += sep_len;
    }
    
    char* res = (char*)zen_alloc(total_len + 1);
    res[0] = '\0';
    for (int i = 0; i < parts->count; i++) {
        strcat(res, parts->items[i].as.string);
        if (i < parts->count - 1) strcat(res, psep);
    }
    return zen_str(res);
}

ZenValue ZenString_concat(ZenValue s1, ZenValue s2) {
    char* ps1 = ZEN_UNBOX(s1, (char*)0);
    char* ps2 = ZEN_UNBOX(s2, (char*)0);
    if (!ps1) return s2;
    if (!ps2) return s1;
    int len1 = strlen(ps1);
    int len2 = strlen(ps2);
    char* res = (char*)zen_alloc(len1 + len2 + 1);
    strcpy(res, ps1);
    strcat(res, ps2);
    return zen_str(res);
}

ZenValue ZenString_replace(ZenValue s, ZenValue old_s, ZenValue new_s) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    char* pold = ZEN_UNBOX(old_s, (char*)0);
    char* pnew = ZEN_UNBOX(new_s, (char*)0);
    if (!ps || !pold || !pnew) return s;
    char *result;
    int i, cnt = 0;
    int newlen = strlen(pnew);
    int oldlen = strlen(pold);
    for (i = 0; ps[i] != '\0'; i++) {
        if (strstr(&ps[i], pold) == &ps[i]) {
            cnt++;
            i += oldlen - 1;
        }
    }
    result = (char*)zen_alloc(i + cnt * (newlen - oldlen) + 1);
    i = 0;
    char* temp_s = ps;
    while (*temp_s) {
        if (strstr(temp_s, pold) == temp_s) {
            strcpy(&result[i], pnew);
            i += newlen;
            temp_s += oldlen;
        } else
            result[i++] = *temp_s++;
    }
    result[i] = '\0';
    return zen_str(result);
}

ZenValue ZenString_to_upper(ZenValue s) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    if (!ps) return zen_str("");
    int len = strlen(ps);
    char* res = (char*)zen_alloc(len + 1);
    for (int i = 0; i < len; i++) {
        res[i] = toupper(ps[i]);
    }
    res[len] = '\0';
    return zen_str(res);
}

ZenValue ZenString_str(ZenValue x) {
    char buf[128];
    switch (x.type) {
        case ZEN_INTEGER:
            sprintf(buf, "%lld", x.as.integer);
            return zen_str(strdup(buf));
        case ZEN_DECIMAL:
            sprintf(buf, "%f", x.as.decimal);
            return zen_str(strdup(buf));
        case ZEN_BOOLEAN:
            return zen_str(x.as.boolean ? "true" : "false");
        case ZEN_STRING:
            return x; 
        case ZEN_LIST: {
            ZenList* list = x.as.list;
            if (!list) return zen_str("[]");
            char* res = (char*)zen_alloc(1024); 
            strcpy(res, "[");
            for (int i=0; i < list->count; i++) {
                ZenValue item = list->items[i];
                ZenValue item_val = ZenString_str(item);
                char* item_str = ZEN_UNBOX(item_val, (char*)0);
                strcat(res, item_str);
                if (i < list->count - 1) strcat(res, ", ");
            }
            strcat(res, "]");
            return zen_str(res);
        }
        case ZEN_NOTHING:
            return zen_str("Nothing");
        default:
            return zen_str("Unknown");
    }
}

ZenValue ZenString_starts_with(ZenValue s, ZenValue prefix) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    char* ppre = ZEN_UNBOX(prefix, (char*)0);
    if (!ps || !ppre) return zen_bool(false);
    size_t len_s = strlen(ps);
    size_t len_p = strlen(ppre);
    if (len_p > len_s) return zen_bool(false);
    return zen_bool(strncmp(ps, ppre, len_p) == 0);
}

ZenValue ZenString_ends_with(ZenValue s, ZenValue suffix) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    char* psuf = ZEN_UNBOX(suffix, (char*)0);
    if (!ps || !psuf) return zen_bool(false);
    size_t len_s = strlen(ps);
    size_t len_p = strlen(psuf);
    if (len_p > len_s) return zen_bool(false);
    return zen_bool(strcmp(ps + len_s - len_p, psuf) == 0);
}

ZenValue ZenString_equals(ZenValue s1, ZenValue s2) {
    char* ps1 = ZEN_UNBOX(s1, (char*)0);
    char* ps2 = ZEN_UNBOX(s2, (char*)0);
    if (ps1 == ps2) return zen_bool(true);
    if (!ps1 || !ps2) return zen_bool(false);
    return zen_bool(strcmp(ps1, ps2) == 0);
}

ZenValue ZenString_index_of(ZenValue s, ZenValue sub) {
    char* ps = ZEN_UNBOX(s, (char*)0);
    char* psub = ZEN_UNBOX(sub, (char*)0);
    if (!ps || !psub) return zen_int(-1);
    char* pos = strstr(ps, psub);
    if (!pos) return zen_int(-1);
    return zen_int((int)(pos - ps));
}
