#ifndef ZEN_MAP_H
#define ZEN_MAP_H

#include "core/zen_value.h"

// Map structure and functions
typedef struct ZenMapEntry {
    ZenVariant key;
    ZenVariant value;
} ZenMapEntry;

typedef struct ZenMap {
    ZenHeapHeader header;     /* 8 bytes: intrusive ARC / Sentinel header */
    ZenMapEntry* entries;
    int count;
    int capacity;
    /* Open-addressed index into entries (insertion order preserved). */
    int* buckets;
    int bucket_n;
} ZenMap;

ZenMap* ZenMap_new(void);
void ZenMap_destroy(ZenMap* map);
ZenMap* ZenMap_deep_clone(ZenMap* map);
ZenValue ZenMap_set(ZenMap* map, ZenValue key, ZenValue value);
ZenValue ZenMap_make_from_arguments(int count, ...);

// Primary ZenValue-based API
ZenValue ZenMap_get_length(ZenValue map);
ZenValue ZenMap_get_value_at_key(ZenValue map, ZenValue key);
ZenValue ZenMap_set_value_at_key(ZenValue map, ZenValue key, ZenValue value);
ZenValue ZenMap_get_keys(ZenValue map);
ZenValue ZenMap_get_values(ZenValue map);
/* List of maps { key, value } for each entry. */
ZenValue ZenMap_get_items(ZenValue map);
ZenValue ZenMap_has_key(ZenValue map, ZenValue key);
ZenValue ZenMap_remove_key(ZenValue map, ZenValue key);
ZenValue ZenMap_merge(ZenValue a, ZenValue b);
ZenValue ZenMap_invert(ZenValue map);
ZenValue ZenMap_get(ZenValue map, ZenValue key, ZenValue default_val);

#endif // ZEN_MAP_H
