#include "zen_list.h"
#include "core/zen_ops.h"
#include <stdlib.h>
#include <stdarg.h>

ZenList* ZenList_new(void) {
    ZenList* list = malloc(sizeof(ZenList));
    list->items = NULL;
    list->count = 0;
    list->capacity = 0;
    return list;
}

ZenValue ZenList_make_from_arguments(int count, ...) {
    ZenList* list = ZenList_new();
    va_list args;
    va_start(args, count);
    for (int i = 0; i < count; i++) {
        ZenVariant item = va_arg(args, ZenVariant);
        if (list->count + 1 > list->capacity) {
            list->capacity = list->capacity < 4 ? 4 : list->capacity * 2;
            list->items = realloc(list->items, sizeof(ZenVariant) * list->capacity);
        }
        list->items[list->count++] = item;
    }
    va_end(args);
    ZenValue res = ZenValue_from_list(list);
    // printf("DEBUG: ZenList_make_from_arguments: returning type %d\n", res.type);
    return res;
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
        l->items = realloc(l->items, sizeof(ZenValue) * new_capacity);
        l->capacity = new_capacity;
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
        printf("DEBUG: ZenList_pop: type mismatch: %d != %d\n", list.type, ZEN_LIST);
        return ZenValue_make_nothing();
    }
    ZenList* l = list.as.list;
    if (!l) {
        printf("DEBUG: ZenList_pop: list is NULL\n");
        return ZenValue_make_nothing();
    }
    if (l->count == 0) {
        printf("DEBUG: ZenList_pop: count is 0\n");
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

    ZenList* out = ZenList_new();
    ZenValue out_v = ZenValue_from_list(out);
    for (long long i = start; i < src->count; i++) {
        ZenList_append_value(out_v, src->items[i]);
    }
    return out_v;
}

ZenValue ZenList_remove(ZenValue list, ZenValue item) {
    // Basic implementation: find index and remove_at
    if (list.type != ZEN_LIST) return ZenValue_make_nothing();
    for (int i = 0; i < list.as.list->count; i++) {
        if (ZenValue_equal(list.as.list->items[i], item).as.boolean) {
            return ZenList_remove_at_index(list, ZenValue_make_integer(i));
        }
    }
    return ZenValue_make_nothing();
}
