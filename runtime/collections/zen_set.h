#ifndef ZEN_SET_H
#define ZEN_SET_H

#include "core/zen_value.h"

// Set API for Zenlang Bootstrap Runtime
typedef struct ZenSet {
    ZenValue list;
} ZenSet;

ZenValue ZenSet_new(void);
ZenValue ZenSet_from_list(ZenValue list);
ZenValue ZenSet_to_list(ZenValue set);
ZenValue ZenSet_add_value(ZenValue set, ZenValue value);
ZenValue ZenSet_contains_value(ZenValue set, ZenValue value);
ZenValue ZenSet_remove_value(ZenValue set, ZenValue value);
int ZenSet_get_count(ZenValue set);

#endif // ZEN_SET_H
