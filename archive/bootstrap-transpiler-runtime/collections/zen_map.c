#include "zen_map.h"
#include "zen_list.h"
#include "core/zen_ops.h"
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>

ZenMap* ZenMap_new(void) {
    ZenMap* map = malloc(sizeof(ZenMap));
    map->entries = NULL;
    map->count = 0;
    map->capacity = 0;
    return map;
}

ZenValue ZenMap_make_from_arguments(int count, ...) {
    ZenMap* map = ZenMap_new();
    va_list args;
    va_start(args, count);
    for (int i = 0; i < count; i++) {
        ZenVariant key = va_arg(args, ZenVariant);
        ZenVariant value = va_arg(args, ZenVariant);
        ZenMap_set_value_at_key(ZenValue_from_map(map), key, value);
    }
    va_end(args);
    return ZenValue_from_map(map);
}

ZenValue ZenMap_get_length(ZenValue map) {
    if (map.type != ZEN_MAP) return ZenValue_make_integer(0);
    ZenMap* m = map.as.map;
    if (!m) return ZenValue_make_integer(0);
    return ZenValue_make_integer(m->count);
}

ZenValue ZenMap_get_value_at_key(ZenValue map, ZenValue key) {
    if (map.type != ZEN_MAP) return ZEN_NOTHING_VAL;
    ZenMap* m = map.as.map;
    if (!m) return ZEN_NOTHING_VAL;

    for (int i = 0; i < m->count; i++) {
        if (ZenValue_equal(m->entries[i].key, key).as.boolean) {
            return m->entries[i].value;
        }
    }

    return ZEN_NOTHING_VAL;
}

ZenValue ZenMap_set_value_at_key(ZenValue map, ZenValue key, ZenValue value) {
    if (map.type != ZEN_MAP) return map;
    ZenMap* m = map.as.map;
    if (!m) return map;

    // Check for existing key
    for (int i = 0; i < m->count; i++) {
        if (ZenValue_equal(m->entries[i].key, key).as.boolean) {
            m->entries[i].value = value;
            return map;
        }
    }

    // Add new key
    if (m->count >= m->capacity) {
        m->capacity = m->capacity == 0 ? 8 : m->capacity * 2;
        m->entries = realloc(m->entries, sizeof(ZenMapEntry) * m->capacity);
    }

    m->entries[m->count].key = key;
    m->entries[m->count].value = value;
    m->count++;

    return map;
}

ZenValue ZenMap_get_keys(ZenValue map) { 
    if (map.type != ZEN_MAP) return ZenValue_make_nothing();
    ZenList* keys = ZenList_new();
    ZenMap* m = map.as.map;
    for (int i = 0; i < m->count; i++) {
        ZenList_append_value(ZenValue_from_list(keys), m->entries[i].key);
    }
    return ZenValue_from_list(keys);
}

ZenValue ZenMap_get_values(ZenValue map) { 
    if (map.type != ZEN_MAP) return ZenValue_make_nothing();
    ZenList* values = ZenList_new();
    ZenMap* m = map.as.map;
    for (int i = 0; i < m->count; i++) {
        ZenList_append_value(ZenValue_from_list(values), m->entries[i].value);
    }
    return ZenValue_from_list(values);
}

ZenValue ZenMap_has_key(ZenValue map, ZenValue key) { 
    if (map.type != ZEN_MAP) return ZenValue_make_boolean(false);
    ZenMap* m = map.as.map;
    for (int i = 0; i < m->count; i++) {
        if (ZenValue_equal(m->entries[i].key, key).as.boolean) return ZenValue_make_boolean(true);
    }
    return ZenValue_make_boolean(false);
}
