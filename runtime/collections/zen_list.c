#include "zen_list.h"
#include "core/zen_ops.h"
#include "memory/zen_memory.h"
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <stdio.h>

ZenList* ZenList_new(void) {
    ZenList* list = (ZenList*)ZenRuntime_allocate(sizeof(ZenList));
    if (!list) return NULL;
    list->items = NULL;
    list->count = 0;
    list->capacity = 0;
    return list;
}

ZenValue ZenList_make_from_arguments(int count, ...) {
    ZenList* list = (ZenList*)ZenRuntime_allocate(sizeof(ZenList));
    if (!list) return ZenValue_make_nothing();
    if (count > 0) {
        list->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)count);
        list->count = count;
        list->capacity = count;
        va_list args;
        va_start(args, count);
        for (int i = 0; i < count; i++) {
            list->items[i] = va_arg(args, ZenVariant);
        }
        va_end(args);
    } else {
        list->items = NULL;
        list->count = 0;
        list->capacity = 0;
    }
    return ZenValue_from_list(list);
}

ZenValue ZenList_get_length(ZenValue list) {
    if (list.type != ZEN_LIST) return ZenValue_make_integer(0);
    ZenList* l = list.as.list;
    if (!l) return ZenValue_make_integer(0);
    return ZenValue_make_integer(l->count);
}

ZenValue ZenList_get_value_at_index(ZenValue list, ZenValue index) {
    if (list.type != ZEN_LIST) return ZenValue_make_nothing();
    ZenList* l = list.as.list;
    if (!l) return ZenValue_make_nothing();
    int idx = (int)index.as.integer;
    if (idx < 0 || idx >= l->count) return ZenValue_make_nothing();
    return l->items[idx];
}

ZenValue ZenList_set_value_at_index(ZenValue list, ZenValue index, ZenValue value) {
    if (list.type != ZEN_LIST) return list;
    ZenList* l = list.as.list;
    if (!l) return list;
    int idx = (int)index.as.integer;
    if (idx < 0 || idx >= l->count) return list;
    l->items[idx] = value;
    return list;
}

ZenValue ZenList_append_value(ZenValue list, ZenValue value) {
    if (list.type != ZEN_LIST) return list;
    ZenList* l = list.as.list;
    if (!l) return list;
    if (l->count >= l->capacity) {
        int new_capacity = l->capacity == 0 ? 8 : l->capacity * 2;
        ZenArena* cur = ZenArena_current();
        if (cur) {
            ZenVariant* new_items = (ZenVariant*)ZenArena_allocate(cur, sizeof(ZenVariant) * (size_t)new_capacity);
            if (l->count > 0 && l->items) {
                memcpy(new_items, l->items, sizeof(ZenVariant) * (size_t)l->count);
            }
            l->items = new_items;
            l->capacity = new_capacity;
        } else {
            l->items = (ZenVariant*)realloc(l->items, sizeof(ZenVariant) * (size_t)new_capacity);
            l->capacity = new_capacity;
        }
    }
    l->items[l->count++] = value;
    return list;
}

ZenValue ZenList_remove_at_index(ZenValue list, ZenValue index) {
    if (list.type != ZEN_LIST) return ZenValue_make_nothing();
    ZenList* l = list.as.list;
    int idx = (int)index.as.integer;
    if (idx < 0 || idx >= l->count) return ZenValue_make_nothing();
    ZenValue removed = l->items[idx];
    for (int i = idx; i < l->count - 1; i++) {
        l->items[i] = l->items[i+1];
    }
    l->count--;
    return removed;
}

ZenValue ZenList_pop(ZenValue list) {
    if (list.type != ZEN_LIST) {
        return ZenValue_make_nothing();
    }
    ZenList* l = list.as.list;
    if (!l || l->count == 0) {
        return ZenValue_make_nothing();
    }
    return l->items[--l->count];
}

ZenValue ZenList_peek(ZenValue list) {
    if (list.type != ZEN_LIST) return ZenValue_make_nothing();
    ZenList* l = list.as.list;
    if (!l || l->count == 0) return ZenValue_make_nothing();
    return l->items[l->count - 1];
}

ZenValue ZenList_contains_value(ZenValue list, ZenValue value) {
    ZenList* l = list.as.list;
    if (!l) return ZenValue_make_boolean(false);
    for (int i = 0; i < l->count; i++) {
        if (ZenValue_equal(l->items[i], value).as.boolean) {
            return ZenValue_make_boolean(true);
        }
    }
    return ZenValue_make_boolean(false);
}

ZenValue ZenList_slice_from(ZenValue list, ZenValue start_index) {
    if (list.type != ZEN_LIST || !list.as.list) {
        return ZenValue_from_list(ZenList_new());
    }
    ZenList* src = list.as.list;
    long long start = 0;
    if (start_index.type == ZEN_INTEGER) start = start_index.as.integer;
    if (start < 0) start = 0;
    if (start > src->count) start = src->count;

    long long count = src->count - start;
    ZenList* out = (ZenList*)ZenRuntime_allocate(sizeof(ZenList));
    if (count > 0 && src->items) {
        out->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)count);
        out->count = (int)count;
        out->capacity = (int)count;
        memcpy(out->items, src->items + start, sizeof(ZenVariant) * (size_t)count);
    } else {
        out->items = NULL;
        out->count = 0;
        out->capacity = 0;
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_remove(ZenValue list, ZenValue item) {
    if (list.type != ZEN_LIST) return ZenValue_make_nothing();
    for (int i = 0; i < list.as.list->count; i++) {
        if (ZenValue_equal(list.as.list->items[i], item).as.boolean) {
            return ZenList_remove_at_index(list, ZenValue_make_integer(i));
        }
    }
    return ZenValue_make_nothing();
}

ZenValue ZenList_clone(ZenValue list) {
    if (list.type != ZEN_LIST || !list.as.list) {
        return ZenValue_from_list(ZenList_new());
    }
    ZenList* src = list.as.list;
    ZenList* out = (ZenList*)ZenRuntime_allocate(sizeof(ZenList));
    if (src->count > 0 && src->items) {
        out->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)src->count);
        out->count = src->count;
        out->capacity = src->count;
        memcpy(out->items, src->items, sizeof(ZenVariant) * (size_t)src->count);
    } else {
        out->items = NULL;
        out->count = 0;
        out->capacity = 0;
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_concat(ZenValue a, ZenValue b) {
    int ca = (a.type == ZEN_LIST && a.as.list) ? a.as.list->count : 0;
    int cb = (b.type == ZEN_LIST && b.as.list) ? b.as.list->count : 0;
    int total = ca + cb;

    ZenList* out = (ZenList*)ZenRuntime_allocate(sizeof(ZenList));
    if (total > 0) {
        out->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)total);
        out->count = total;
        out->capacity = total;
        if (ca > 0 && a.as.list->items) {
            memcpy(out->items, a.as.list->items, sizeof(ZenVariant) * (size_t)ca);
        }
        if (cb > 0 && b.as.list->items) {
            memcpy(out->items + ca, b.as.list->items, sizeof(ZenVariant) * (size_t)cb);
        }
    } else {
        out->items = NULL;
        out->count = 0;
        out->capacity = 0;
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_prepend(ZenValue list, ZenValue item) {
    int count = (list.type == ZEN_LIST && list.as.list) ? list.as.list->count : 0;
    int total = count + 1;

    ZenList* out = (ZenList*)ZenRuntime_allocate(sizeof(ZenList));
    out->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)total);
    out->count = total;
    out->capacity = total;
    out->items[0] = item;
    if (count > 0 && list.as.list->items) {
        memcpy(out->items + 1, list.as.list->items, sizeof(ZenVariant) * (size_t)count);
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_drop_end(ZenValue list, long long n) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_from_list(ZenList_new());
    ZenList* src = list.as.list;
    if (n <= 0) return ZenList_clone(list);
    long long remaining = src->count - n;
    if (remaining <= 0) return ZenValue_from_list(ZenList_new());

    ZenList* out = (ZenList*)ZenRuntime_allocate(sizeof(ZenList));
    out->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)remaining);
    out->count = (int)remaining;
    out->capacity = (int)remaining;
    memcpy(out->items, src->items, sizeof(ZenVariant) * (size_t)remaining);
    return ZenValue_from_list(out);
}

ZenValue ZenList_drop_start(ZenValue list, long long n) {
    return ZenList_slice_from(list, ZenValue_make_integer(n));
}
