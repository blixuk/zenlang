#include "zen_map.h"
#include "zen_list.h"
#include "core/zen_ops.h"
#include "memory/zen_memory.h"
#include <stdlib.h>
#include <stdarg.h>
#include <stdint.h>
#include <string.h>

static uint32_t zen_map_hash(ZenValue key) {
    if (key.type == ZEN_STRING && key.as.string) {
        uint32_t h = 2166136261u;
        const unsigned char* s = (const unsigned char*)key.as.string;
        while (*s) {
            h ^= (uint32_t)(*s++);
            h *= 16777619u;
        }
        return h ? h : 1u;
    }
    if (key.type == ZEN_INTEGER) {
        uint64_t x = (uint64_t)key.as.integer;
        x ^= x >> 30;
        x *= 0xbf58476d1ce4e5b9ULL;
        x ^= x >> 27;
        return (uint32_t)x;
    }
    if (key.type == ZEN_BOOLEAN) {
        return key.as.boolean ? 0x9e3779b9u : 0x85ebca6bu;
    }
    if (key.type == ZEN_NOTHING) {
        return 0x165667b1u;
    }
    uintptr_t p = (uintptr_t)key.as.object;
    p ^= p >> 16;
    p *= 0x7feb352dU;
    p ^= p >> 15;
    return (uint32_t)p;
}

static int zen_map_keys_equal(ZenValue a, ZenValue b) {
    if (a.type == ZEN_STRING && b.type == ZEN_STRING) {
        if (a.as.string == b.as.string) return 1;
        if (!a.as.string || !b.as.string) return 0;
        return strcmp(a.as.string, b.as.string) == 0;
    }
    return ZenValue_equal(a, b).as.boolean;
}

static void zen_map_rehash(ZenMap* m) {
    int n = 8;
    while (n < m->count * 2 + 2) {
        n *= 2;
    }
    bool in_arena = (m->header.ref_count == ZEN_REF_PINNED);
    ZenArena* cur = in_arena ? ZenArena_current() : NULL;
    int* b;
    if (cur) {
        b = (int*)ZenArena_allocate(cur, sizeof(int) * (size_t)n);
    } else {
        b = (int*)malloc(sizeof(int) * (size_t)n);
    }
    if (!b) return;
    for (int i = 0; i < n; i++) b[i] = -1;
    int mask = n - 1;
    for (int i = 0; i < m->count; i++) {
        uint32_t h = zen_map_hash(m->entries[i].key);
        int j = (int)(h & (uint32_t)mask);
        while (b[j] != -1) {
            j = (j + 1) & mask;
        }
        b[j] = i;
    }
    if (!in_arena && m->buckets) {
        free(m->buckets);
    }
    m->buckets = b;
    m->bucket_n = n;
}

static int zen_map_find_index(ZenMap* m, ZenValue key) {
    if (!m || m->count == 0) return -1;
    if (!m->buckets || m->bucket_n <= 0) {
        for (int i = 0; i < m->count; i++) {
            if (zen_map_keys_equal(m->entries[i].key, key)) return i;
        }
        return -1;
    }
    int mask = m->bucket_n - 1;
    int j = (int)(zen_map_hash(key) & (uint32_t)mask);
    for (int n = 0; n < m->bucket_n; n++) {
        int idx = m->buckets[j];
        if (idx < 0) return -1;
        if (zen_map_keys_equal(m->entries[idx].key, key)) return idx;
        j = (j + 1) & mask;
    }
    return -1;
}

ZenMap* ZenMap_new(void) {
    ZenMap* map = (ZenMap*)ZenRuntime_allocate(sizeof(ZenMap));
    if (!map) return NULL;
    ZenHeapHeader_init(&map->header, ZEN_MAP, ZEN_FLAG_CONTAINER);
    map->entries = NULL;
    map->count = 0;
    map->capacity = 0;
    map->buckets = NULL;
    map->bucket_n = 0;
    return map;
}

void ZenMap_destroy(ZenMap* map) {
    if (!map) return;
    for (int i = 0; i < map->count; i++) {
        ZenValue_release(map->entries[i].key);
        ZenValue_release(map->entries[i].value);
    }
    if (map->header.ref_count != ZEN_REF_PINNED) {
        if (map->entries) {
            free(map->entries);
        }
        if (map->buckets) {
            free(map->buckets);
        }
        free(map);
    }
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
    ZenMap* l = map.as.map;
    if (!l) return ZenValue_make_integer(0);
    return ZenValue_make_integer(l->count);
}

ZenValue ZenMap_get_value_at_key(ZenValue map, ZenValue key) {
    if (map.type != ZEN_MAP) return ZEN_NOTHING_VAL;
    ZenMap* m = map.as.map;
    if (!m) return ZEN_NOTHING_VAL;
    int i = zen_map_find_index(m, key);
    if (i < 0) return ZEN_NOTHING_VAL;
    return m->entries[i].value;
}

ZenValue ZenMap_set_value_at_key(ZenValue map, ZenValue key, ZenValue value) {
    if (map.type != ZEN_MAP) return map;
    ZenMap* m = map.as.map;
    if (!m) return map;
    int found = zen_map_find_index(m, key);
    if (found >= 0) {
        ZenValue old_val = m->entries[found].value;
        m->entries[found].value = ZenValue_write_barrier_target(&m->header, value);
        ZenValue_release(old_val);
        return map;
    }
    if (m->count >= m->capacity) {
        int new_capacity = m->capacity == 0 ? 8 : m->capacity * 2;
        bool in_arena = (m->header.ref_count == ZEN_REF_PINNED);
        ZenArena* cur = in_arena ? ZenArena_current() : NULL;
        if (cur) {
            ZenMapEntry* new_entries = (ZenMapEntry*)ZenArena_allocate(cur, sizeof(ZenMapEntry) * (size_t)new_capacity);
            if (m->count > 0 && m->entries) {
                memcpy(new_entries, m->entries, sizeof(ZenMapEntry) * (size_t)m->count);
            }
            m->entries = new_entries;
            m->capacity = new_capacity;
        } else {
            m->entries = (ZenMapEntry*)realloc(m->entries, sizeof(ZenMapEntry) * (size_t)new_capacity);
            m->capacity = new_capacity;
        }
    }
    int idx = m->count;
    m->entries[idx].key = ZenValue_write_barrier_target(&m->header, key);
    m->entries[idx].value = ZenValue_write_barrier_target(&m->header, value);
    m->count++;
    if (!m->buckets || m->count * 2 > m->bucket_n) {
        zen_map_rehash(m);
    } else {
        int mask = m->bucket_n - 1;
        int j = (int)(zen_map_hash(key) & (uint32_t)mask);
        while (m->buckets[j] != -1) {
            j = (j + 1) & mask;
        }
        m->buckets[j] = idx;
    }
    return map;
}

ZenMap* ZenMap_deep_clone(ZenMap* map) {
    if (!map) return NULL;
    ZenMap* new_map = ZenMap_new();
    if (!new_map) return NULL;
    zen_clone_register((void*)map, ZenValue_from_map(new_map));
    for (int i = 0; i < map->count; i++) {
        ZenMap_set_value_at_key(ZenValue_from_map(new_map), map->entries[i].key, map->entries[i].value);
    }
    return new_map;
}

ZenValue ZenMap_set(ZenMap* map, ZenValue key, ZenValue value) {
    if (!map) return ZEN_NOTHING_VAL;
    return ZenMap_set_value_at_key(ZenValue_from_map(map), key, value);
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

ZenValue ZenMap_get_items(ZenValue map) {
    if (map.type != ZEN_MAP) return ZenList_make_from_arguments(0);
    ZenValue out = ZenList_make_from_arguments(0);
    ZenMap* m = map.as.map;
    if (!m) return out;
    for (int i = 0; i < m->count; i++) {
        ZenValue pair = ZenMap_make_from_arguments(0);
        ZenMap_set_value_at_key(pair, ZenValue_make_string("key"), m->entries[i].key);
        ZenMap_set_value_at_key(pair, ZenValue_make_string("value"), m->entries[i].value);
        ZenList_append_value(out, pair);
    }
    return out;
}

ZenValue ZenMap_has_key(ZenValue map, ZenValue key) {
    if (map.type != ZEN_MAP) return ZenValue_make_boolean(false);
    ZenMap* m = map.as.map;
    if (!m) return ZenValue_make_boolean(false);
    return ZenValue_make_boolean(zen_map_find_index(m, key) >= 0);
}

ZenValue ZenMap_remove_key(ZenValue map, ZenValue key) {
    if (map.type != ZEN_MAP || !map.as.map) return map;
    ZenMap* m = map.as.map;
    int i = zen_map_find_index(m, key);
    if (i < 0) return map;
    ZenValue old_k = m->entries[i].key;
    ZenValue old_v = m->entries[i].value;
    for (int j = i; j < m->count - 1; j++) {
        m->entries[j] = m->entries[j + 1];
    }
    m->count--;
    ZenValue_release(old_k);
    ZenValue_release(old_v);
    if (m->count == 0) {
        ZenArena* cur = ZenArena_current();
        if (!cur && m->buckets) {
            free(m->buckets);
        }
        m->buckets = NULL;
        m->bucket_n = 0;
    } else {
        zen_map_rehash(m);
    }
    return map;
}

ZenValue ZenMap_merge(ZenValue a, ZenValue b) {
    ZenMap* out = ZenMap_new();
    if (a.type == ZEN_MAP && a.as.map) {
        for (int i = 0; i < a.as.map->count; i++) {
            ZenMap_set_value_at_key(ZenValue_from_map(out), a.as.map->entries[i].key, a.as.map->entries[i].value);
        }
    }
    if (b.type == ZEN_MAP && b.as.map) {
        for (int i = 0; i < b.as.map->count; i++) {
            ZenMap_set_value_at_key(ZenValue_from_map(out), b.as.map->entries[i].key, b.as.map->entries[i].value);
        }
    }
    return ZenValue_from_map(out);
}

ZenValue ZenMap_invert(ZenValue map) {
    ZenMap* out = ZenMap_new();
    if (map.type == ZEN_MAP && map.as.map) {
        for (int i = 0; i < map.as.map->count; i++) {
            ZenMap_set_value_at_key(ZenValue_from_map(out), map.as.map->entries[i].value, map.as.map->entries[i].key);
        }
    }
    return ZenValue_from_map(out);
}

ZenValue ZenMap_get(ZenValue map, ZenValue key, ZenValue default_val) {
    if (map.type != ZEN_MAP || !map.as.map) return default_val;
    if (ZenMap_has_key(map, key).as.boolean) {
        return ZenMap_get_value_at_key(map, key);
    }
    return default_val;
}

