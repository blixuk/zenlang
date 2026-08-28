#ifndef ZEN_MAP_H
#define ZEN_MAP_H

#include "core/zen_value.h"

// Map structure and functions
typedef struct ZenMapEntry {
    ZenVariant key;
    ZenVariant value;
} ZenMapEntry;

typedef struct ZenMap {
    ZenMapEntry* entries;
    int count;
    int capacity;
} ZenMap;

ZenMap* ZenMap_new(void);
ZenValue ZenMap_make_from_arguments(int count, ...);

// Primary ZenValue-based API
ZenValue ZenMap_get_length(ZenValue map);
ZenValue ZenMap_get_value_at_key(ZenValue map, ZenValue key);
ZenValue ZenMap_set_value_at_key(ZenValue map, ZenValue key, ZenValue value);
ZenValue ZenMap_get_keys(ZenValue map);
ZenValue ZenMap_get_values(ZenValue map);
ZenValue ZenMap_has_key(ZenValue map, ZenValue key);

#endif // ZEN_MAP_H
