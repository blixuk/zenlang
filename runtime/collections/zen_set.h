#ifndef ZEN_SET_H
#define ZEN_SET_H

#include "core/zen_value.h"

// Set API for Zenlang Bootstrap Runtime
typedef struct ZenSet {
    ZenHeapHeader header;     /* 8 bytes: intrusive ARC / Sentinel header */
    ZenValue list;
} ZenSet;

ZenValue ZenSet_new(void);
void ZenSet_destroy(ZenSet* set);
ZenSet* ZenSet_deep_clone(ZenSet* set);

static inline ZenValue ZenValue_from_set(ZenSet* set) {
    ZenValue v;
    v.type = ZEN_SET;
    v.as.set = set;
    return v;
}
ZenValue ZenSet_from_list(ZenValue list);
ZenValue ZenSet_to_list(ZenValue set);
ZenValue ZenSet_add_value(ZenValue set, ZenValue value);
ZenValue ZenSet_contains_value(ZenValue set, ZenValue value);
ZenValue ZenSet_remove_value(ZenValue set, ZenValue value);
int ZenSet_get_count(ZenValue set);
ZenValue ZenSet_union(ZenValue a, ZenValue b);
ZenValue ZenSet_intersection(ZenValue a, ZenValue b);
ZenValue ZenSet_difference(ZenValue a, ZenValue b);

static inline ZenValue ZenSet_remove(ZenValue set, ZenValue value) { return ZenSet_remove_value(set, value); }
static inline ZenValue ZenSet_add(ZenValue set, ZenValue value) { return ZenSet_add_value(set, value); }

#endif // ZEN_SET_H
