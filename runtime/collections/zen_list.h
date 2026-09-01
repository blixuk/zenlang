#ifndef ZEN_LIST_H
#define ZEN_LIST_H

#include "core/zen_value.h"

// List structure and functions
typedef struct ZenList {
    ZenVariant* items;
    int count;
    int capacity;
} ZenList;

ZenList* ZenList_new(void);
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

static inline ZenValue ZenList_remove_at(ZenValue list, ZenValue index) { return ZenList_remove_at_index(list, index); }

#endif // ZEN_LIST_H
