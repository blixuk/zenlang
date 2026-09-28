#include "zen_list.h"
#include "zen_map.h"
#include "core/zen_ops.h"
#include "core/zen_dispatch.h"
#include "memory/zen_memory.h"
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <stdio.h>

static inline ZenList* zen_list_alloc(void) {
    ZenList* list = (ZenList*)ZenRuntime_allocate(sizeof(ZenList));
    if (!list) return NULL;
    ZenHeapHeader_init(&list->header, ZEN_LIST, ZEN_FLAG_CONTAINER);
    return list;
}

ZenList* ZenList_new(void) {
    ZenList* list = zen_list_alloc();
    if (!list) return NULL;
    list->items = NULL;
    list->count = 0;
    list->capacity = 0;
    return list;
}

void ZenList_destroy(ZenList* list) {
    if (!list) return;
    
    // Cascade release to all child elements
    for (int i = 0; i < list->count; i++) {
        ZenValue_release(list->items[i]);
    }
    
    // If allocated in an arena, the chunk frees it in O(1) bulk.
    // If standard heap, free the buffers explicitly:
    if (list->header.ref_count != ZEN_REF_PINNED) {
        if (list->items) {
            free(list->items);
        }
        free(list);
    }
}

ZenValue ZenList_make_from_arguments(int count, ...) {
    ZenList* list = zen_list_alloc();
    if (!list) return ZenValue_make_nothing();
    if (count > 0) {
        list->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)count);
        list->count = count;
        list->capacity = count;
        va_list args;
        va_start(args, count);
        for (int i = 0; i < count; i++) {
            ZenVariant item = va_arg(args, ZenVariant);
            list->items[i] = ZenValue_write_barrier_target(&list->header, item);
        }
        va_end(args);
    } else {
        list->items = NULL;
        list->count = 0;
        list->capacity = 0;
    }
    return ZenValue_from_list(list);
}

ZenList* ZenList_deep_clone(ZenList* list) {
    if (!list) return NULL;
    ZenList* new_list = ZenList_new();
    if (!new_list) return NULL;
    zen_clone_register((void*)list, ZenValue_from_list(new_list));
    if (list->count > 0 && list->items) {
        new_list->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)list->count);
        new_list->capacity = list->count;
        for (int i = 0; i < list->count; i++) {
            new_list->items[i] = ZenValue_write_barrier_target(&new_list->header, list->items[i]);
        }
        new_list->count = list->count;
    }
    return new_list;
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
    if (idx < 0) idx += l->count;
    if (idx < 0 || idx >= l->count) return ZenValue_make_nothing();
    return l->items[idx];
}

ZenValue ZenList_set_value_at_index(ZenValue list, ZenValue index, ZenValue value) {
    if (list.type != ZEN_LIST) return list;
    ZenList* l = list.as.list;
    if (!l) return list;
    int idx = (int)index.as.integer;
    if (idx < 0) idx += l->count;
    if (idx < 0 || idx >= l->count) return list;
    ZenValue old = l->items[idx];
    l->items[idx] = ZenValue_write_barrier_target(&l->header, value);
    ZenValue_release(old);
    return list;
}

ZenValue ZenList_append_value(ZenValue list, ZenValue value) {
    if (list.type != ZEN_LIST) return list;
    ZenList* l = list.as.list;
    if (!l) return list;
    if (l->count >= l->capacity) {
        int new_capacity = l->capacity == 0 ? 8 : l->capacity * 2;
        bool in_arena = (l->header.ref_count == ZEN_REF_PINNED);
        ZenArena* cur = in_arena ? ZenArena_current() : NULL;
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
    l->items[l->count++] = ZenValue_write_barrier_target(&l->header, value);
    return list;
}

void ZenList_append(ZenList* list, ZenValue item) {
    if (!list) return;
    ZenValue v_list = ZenValue_from_list(list);
    ZenList_append_value(v_list, item);
}

void ZenList_set(ZenList* list, int index, ZenValue item) {
    if (!list) return;
    ZenValue v_list = ZenValue_from_list(list);
    ZenList_set_value_at_index(v_list, ZenValue_make_integer(index), item);
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
    ZenList* out = zen_list_alloc();
    if (!out) return ZenValue_from_list(ZenList_new());
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
    ZenList* out = zen_list_alloc();
    if (!out) return ZenValue_from_list(ZenList_new());
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

    ZenList* out = zen_list_alloc();
    if (!out) return ZenValue_from_list(ZenList_new());
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

    ZenList* out = zen_list_alloc();
    if (!out) return ZenValue_from_list(ZenList_new());
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

    ZenList* out = zen_list_alloc();
    if (!out) return ZenValue_from_list(ZenList_new());
    out->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)remaining);
    out->count = (int)remaining;
    out->capacity = (int)remaining;
    memcpy(out->items, src->items, sizeof(ZenVariant) * (size_t)remaining);
    return ZenValue_from_list(out);
}

ZenValue ZenList_drop_start(ZenValue list, long long n) {
    return ZenList_slice_from(list, ZenValue_make_integer(n));
}

static inline bool zen_list_is_truthy(ZenValue v) {
    if (v.type == ZEN_NOTHING || v.type == ZEN_DEFAULT) return false;
    if (v.type == ZEN_BOOLEAN) return v.as.boolean;
    if (v.type == ZEN_INTEGER) return v.as.integer != 0;
    if (v.type == ZEN_DECIMAL) return v.as.decimal != 0.0;
    if (v.type == ZEN_STRING) return v.as.string && v.as.string[0] != '\0';
    if (v.type == ZEN_LIST) return v.as.list && v.as.list->count > 0;
    if (v.type == ZEN_MAP) return v.as.map && v.as.map->count > 0;
    return true;
}

ZenValue ZenList_reverse(ZenValue list) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_from_list(ZenList_new());
    ZenList* src = list.as.list;
    ZenList* out = zen_list_alloc();
    if (!out) return ZenValue_from_list(ZenList_new());
    out->count = src->count;
    out->capacity = src->count;
    if (src->count > 0) {
        out->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)src->count);
        for (int i = 0; i < src->count; i++) {
            out->items[i] = src->items[src->count - 1 - i];
        }
    } else {
        out->items = NULL;
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_unique(ZenValue list) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_from_list(ZenList_new());
    ZenList* src = list.as.list;
    ZenList* out = ZenList_new();
    for (int i = 0; i < src->count; i++) {
        ZenValue item = src->items[i];
        if (!ZenList_contains_value(ZenValue_from_list(out), item).as.boolean) {
            ZenList_append_value(ZenValue_from_list(out), item);
        }
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_flatten(ZenValue list) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_from_list(ZenList_new());
    ZenList* src = list.as.list;
    ZenList* out = ZenList_new();
    for (int i = 0; i < src->count; i++) {
        ZenValue item = src->items[i];
        if (item.type == ZEN_LIST && item.as.list) {
            for (int j = 0; j < item.as.list->count; j++) {
                ZenList_append_value(ZenValue_from_list(out), item.as.list->items[j]);
            }
        } else {
            ZenList_append_value(ZenValue_from_list(out), item);
        }
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_chunk(ZenValue list, ZenValue size_v) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_from_list(ZenList_new());
    int size = (int)size_v.as.integer;
    if (size <= 0) size = 1;
    ZenList* src = list.as.list;
    ZenList* out = ZenList_new();
    ZenList* curr = NULL;
    for (int i = 0; i < src->count; i++) {
        if (i % size == 0) {
            curr = ZenList_new();
            ZenList_append_value(ZenValue_from_list(out), ZenValue_from_list(curr));
        }
        ZenList_append_value(ZenValue_from_list(curr), src->items[i]);
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_take(ZenValue list, ZenValue n_v) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_from_list(ZenList_new());
    int n = (int)n_v.as.integer;
    if (n <= 0) return ZenValue_from_list(ZenList_new());
    ZenList* src = list.as.list;
    if (n > src->count) n = src->count;
    ZenList* out = zen_list_alloc();
    if (!out) return ZenValue_from_list(ZenList_new());
    out->count = n;
    out->capacity = n;
    out->items = (ZenVariant*)ZenRuntime_allocate(sizeof(ZenVariant) * (size_t)n);
    memcpy(out->items, src->items, sizeof(ZenVariant) * (size_t)n);
    return ZenValue_from_list(out);
}

ZenValue ZenList_drop(ZenValue list, ZenValue n_v) {
    return ZenList_drop_start(list, n_v.as.integer);
}

ZenValue ZenList_map(ZenValue list, ZenValue fn) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_from_list(ZenList_new());
    ZenList* src = list.as.list;
    ZenList* out = ZenList_new();
    for (int i = 0; i < src->count; i++) {
        ZenValue mapped = ZenValue_apply(fn, 1, src->items[i]);
        ZenList_append_value(ZenValue_from_list(out), mapped);
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_filter(ZenValue list, ZenValue fn) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_from_list(ZenList_new());
    ZenList* src = list.as.list;
    ZenList* out = ZenList_new();
    for (int i = 0; i < src->count; i++) {
        ZenValue cond = ZenValue_apply(fn, 1, src->items[i]);
        if (zen_list_is_truthy(cond)) {
            ZenList_append_value(ZenValue_from_list(out), src->items[i]);
        }
    }
    return ZenValue_from_list(out);
}

ZenValue ZenList_reduce(ZenValue list, ZenValue initial, ZenValue fn) {
    if (list.type != ZEN_LIST || !list.as.list) return initial;
    ZenList* src = list.as.list;
    ZenValue acc = initial;
    for (int i = 0; i < src->count; i++) {
        acc = ZenValue_apply(fn, 2, acc, src->items[i]);
    }
    return acc;
}

ZenValue ZenList_each(ZenValue list, ZenValue fn) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_make_nothing();
    ZenList* src = list.as.list;
    for (int i = 0; i < src->count; i++) {
        (void)ZenValue_apply(fn, 1, src->items[i]);
    }
    return ZenValue_make_nothing();
}

ZenValue ZenList_find(ZenValue list, ZenValue fn) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_make_nothing();
    ZenList* src = list.as.list;
    for (int i = 0; i < src->count; i++) {
        ZenValue cond = ZenValue_apply(fn, 1, src->items[i]);
        if (zen_list_is_truthy(cond)) {
            return src->items[i];
        }
    }
    return ZenValue_make_nothing();
}

ZenValue ZenList_any(ZenValue list, ZenValue fn) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_make_boolean(false);
    ZenList* src = list.as.list;
    for (int i = 0; i < src->count; i++) {
        ZenValue cond = ZenValue_apply(fn, 1, src->items[i]);
        if (zen_list_is_truthy(cond)) {
            return ZenValue_make_boolean(true);
        }
    }
    return ZenValue_make_boolean(false);
}

ZenValue ZenList_all(ZenValue list, ZenValue fn) {
    if (list.type != ZEN_LIST || !list.as.list) return ZenValue_make_boolean(true);
    ZenList* src = list.as.list;
    for (int i = 0; i < src->count; i++) {
        ZenValue cond = ZenValue_apply(fn, 1, src->items[i]);
        if (!zen_list_is_truthy(cond)) {
            return ZenValue_make_boolean(false);
        }
    }
    return ZenValue_make_boolean(true);
}

