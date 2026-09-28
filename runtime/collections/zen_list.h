#ifndef ZEN_LIST_H
#define ZEN_LIST_H

#include "core/zen_value.h"

// List structure and functions
typedef struct ZenList {
    ZenHeapHeader header;     /* 8 bytes: intrusive ARC / Sentinel header */
    ZenVariant* items;        /* 8 bytes: naturally aligned pointer       */
    int count;                /* 4 bytes                                  */
    int capacity;             /* 4 bytes                                  */
} ZenList;                    /* 24 bytes total                           */

ZenList* ZenList_new(void);
void ZenList_destroy(ZenList* list);
ZenList* ZenList_deep_clone(ZenList* list);
void ZenList_append(ZenList* list, ZenValue item);
void ZenList_set(ZenList* list, int index, ZenValue item);
ZenValue ZenList_make_from_arguments(int count, ...);

// Primary ZenValue-based API
ZenValue ZenList_get_length(ZenValue list);
ZenValue ZenList_get_value_at_index(ZenValue list, ZenValue index);
ZenValue ZenList_set_value_at_index(ZenValue list, ZenValue index, ZenValue value);
ZenValue ZenList_append_value(ZenValue list, ZenValue value);
ZenValue ZenValue_from_list(ZenList* list);
ZenValue ZenList_remove(ZenValue list, ZenValue item);
ZenValue ZenList_remove_at_index(ZenValue list, ZenValue index);
ZenValue ZenList_pop(ZenValue list);
ZenValue ZenList_peek(ZenValue list);
ZenValue ZenList_contains_value(ZenValue list, ZenValue value);
// Slice from start_index inclusive to end of list (for rest patterns).
ZenValue ZenList_slice_from(ZenValue list, ZenValue start_index);
ZenValue ZenList_clone(ZenValue list);
ZenValue ZenList_concat(ZenValue a, ZenValue b);
ZenValue ZenList_prepend(ZenValue list, ZenValue item);
ZenValue ZenList_drop_end(ZenValue list, long long n);
ZenValue ZenList_drop_start(ZenValue list, long long n);

ZenValue ZenList_reverse(ZenValue list);
ZenValue ZenList_unique(ZenValue list);
ZenValue ZenList_flatten(ZenValue list);
ZenValue ZenList_chunk(ZenValue list, ZenValue size);
ZenValue ZenList_take(ZenValue list, ZenValue n);
ZenValue ZenList_drop(ZenValue list, ZenValue n);
ZenValue ZenList_map(ZenValue list, ZenValue fn);
ZenValue ZenList_filter(ZenValue list, ZenValue fn);
ZenValue ZenList_reduce(ZenValue list, ZenValue initial, ZenValue fn);
ZenValue ZenList_each(ZenValue list, ZenValue fn);
ZenValue ZenList_find(ZenValue list, ZenValue fn);
ZenValue ZenList_any(ZenValue list, ZenValue fn);
ZenValue ZenList_all(ZenValue list, ZenValue fn);

static inline ZenValue ZenList_remove_at(ZenValue list, ZenValue index) { return ZenList_remove_at_index(list, index); }

#endif // ZEN_LIST_H
