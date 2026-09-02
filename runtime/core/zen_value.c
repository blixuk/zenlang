#include "zen_value.h"
#include "zen_closure.h"
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdarg.h>

/* Identifiers, keywords, qualified symbols (up to 512 bytes), and AST keys
 * are interned into a high-capacity global pool for fast O(1) pointer equality.
 * Unique long strings (emitted C units) remain distinct heap allocations. */
#define ZEN_INTERN_MAX_LEN 512
#define ZEN_INTERN_MAX_LIVE 1048576

typedef struct {
    char* s;
    uint16_t len;
    uint16_t pad;
    uint32_t hash;
} ZenInternSlot;

static ZenInternSlot* zen_intern_slots = NULL;
static int zen_intern_cap = 0;
static int zen_intern_live = 0;

static inline uint32_t zen_intern_hash(const char* s, size_t n) {
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < n; i++) {
        h ^= (uint32_t)(unsigned char)s[i];
        h *= 16777619u;
    }
    return h ? h : 1u;
}

static char* zen_intern_lookup(const char* s, size_t n, uint32_t h) {
    if (!zen_intern_slots || zen_intern_cap <= 0) return NULL;
    int mask = zen_intern_cap - 1;
    int j = (int)(h & (uint32_t)mask);
    for (int ntry = 0; ntry < zen_intern_cap; ntry++) {
        ZenInternSlot* sl = &zen_intern_slots[j];
        if (!sl->s) return NULL;
        if (sl->hash == h && sl->len == (uint16_t)n && memcmp(sl->s, s, n) == 0) {
            return sl->s;
        }
        j = (j + 1) & mask;
    }
    return NULL;
}

static void zen_intern_grow(void) {
    int ncap = zen_intern_cap == 0 ? 4096 : zen_intern_cap * 2;
    ZenInternSlot* nslots = (ZenInternSlot*)calloc((size_t)ncap, sizeof(ZenInternSlot));
    if (!nslots) return;
    int nmask = ncap - 1;
    if (zen_intern_slots) {
        for (int i = 0; i < zen_intern_cap; i++) {
            ZenInternSlot* sl = &zen_intern_slots[i];
            if (!sl->s) continue;
            int j = (int)(sl->hash & (uint32_t)nmask);
            while (nslots[j].s) j = (j + 1) & nmask;
            nslots[j] = *sl;
        }
        free(zen_intern_slots);
    }
    zen_intern_slots = nslots;
    zen_intern_cap = ncap;
}

static char* zen_intern_put(const char* s, size_t n, uint32_t h) {
    if (zen_intern_live >= ZEN_INTERN_MAX_LIVE) return NULL;
    if (!zen_intern_slots || (size_t)zen_intern_live * 10 >= (size_t)zen_intern_cap * 6.5) {
        zen_intern_grow();
        if (!zen_intern_slots) return NULL;
    }
    char* copy = (char*)malloc(n + 1);
    if (!copy) return NULL;
    memcpy(copy, s, n);
    copy[n] = '\0';
    int mask = zen_intern_cap - 1;
    int j = (int)(h & (uint32_t)mask);
    while (zen_intern_slots[j].s) j = (j + 1) & mask;
    zen_intern_slots[j].s = copy;
    zen_intern_slots[j].len = (uint16_t)n;
    zen_intern_slots[j].pad = 0;
    zen_intern_slots[j].hash = h;
    zen_intern_live++;
    return copy;
}

ZenValue ZenValue_make_string(const char* s) {
    ZenValue z;
    z.type = ZEN_STRING;
    if (s == NULL) {
        z.as.string = NULL;
        return z;
    }
    size_t len = strlen(s);
    if (len <= ZEN_INTERN_MAX_LEN) {
        uint32_t h = zen_intern_hash(s, len);
        char* interned = zen_intern_lookup(s, len, h);
        if (!interned) interned = zen_intern_put(s, len, h);
        if (interned) {
            z.as.string = interned;
            return z;
        }
    }
    char* res = (char*)malloc(len + 1);
    if (res) {
        memcpy(res, s, len + 1);
    }
    z.as.string = res;
    return z;
}

ZenValue ZenValue_make_nothing(void) {
    ZenValue z;
    z.type = ZEN_NOTHING;
    return z;
}

ZenValue ZenValue_make_default(void) {
    ZenValue z;
    z.type = ZEN_DEFAULT;
    return z;
}

ZenValue ZenValue_from_list(struct ZenList* l) {
    ZenValue z;
    z.type = ZEN_LIST;
    z.as.list = l;
    return z;
}

ZenValue ZenValue_from_object(void* obj) {
    ZenValue v;
    v.type = ZEN_OBJECT;
    v.as.object = obj;
#ifdef ZEN_RUNTIME_DEBUG
    printf("DEBUG: Created ZEN_OBJECT: %p\n", obj);
#endif
    return v;
}

ZenValue ZenValue_from_map(struct ZenMap* m) {
    ZenValue z;
    z.type = ZEN_MAP;
    z.as.map = m;
    return z;
}

ZenValue ZenValue_from_arena(ZenArena* a) {
    ZenValue z;
    z.type = ZEN_ARENA;
    z.as.arena = a;
    return z;
}

ZenValue ZenValue_make_error(ZenValue message) {
    ZenValue v = {ZEN_ERROR, {0}};
    if (message.type == ZEN_STRING) {
        v.as.string = strdup(message.as.string);
    } else {
        v.as.string = "Unknown Error";
    }
    return v;
}

/* Bare function: zero captures. Payload lives in as.object (ZenClosureData). */
ZenValue ZenValue_from_function(ZenValue (*f)(void)) {
    ZenClosureData* c = (ZenClosureData*)calloc(1, sizeof(ZenClosureData));
    if (!c) {
        ZenValue z;
        z.type = ZEN_NOTHING;
        return z;
    }
    c->fn = (void*)f;
    c->n_caps = 0;
    c->arity = -1;
    ZenValue z;
    z.type = ZEN_FUNCTION;
    z.as.object = c;
    return z;
}

/* Closure with by-value captures. fn is called as (caps..., user_args...). */
ZenValue ZenValue_from_closure(void* fn, int arity, int n_caps, ...) {
    if (n_caps < 0) n_caps = 0;
    if (n_caps > ZEN_MAX_CAPTURES) n_caps = ZEN_MAX_CAPTURES;
    ZenClosureData* c = (ZenClosureData*)calloc(1, sizeof(ZenClosureData));
    if (!c) {
        ZenValue z;
        z.type = ZEN_NOTHING;
        return z;
    }
    c->fn = fn;
    c->n_caps = n_caps;
    c->arity = arity;
    va_list ap;
    va_start(ap, n_caps);
    for (int i = 0; i < n_caps; i++) {
        c->caps[i] = va_arg(ap, ZenValue);
    }
    va_end(ap);
    ZenValue z;
    z.type = ZEN_FUNCTION;
    z.as.object = c;
    return z;
}
