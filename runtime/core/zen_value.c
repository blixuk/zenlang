#include "zen_value.h"
#include "zen_closure.h"
#include "zen_variant.h"
#include "../collections/zen_list.h"
#include "../collections/zen_map.h"
#include "../collections/zen_set.h"
#include "../concurrency/zen_channel.h"
#include "../concurrency/zen_task.h"
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
static pthread_mutex_t zen_intern_lock = PTHREAD_MUTEX_INITIALIZER;

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
        pthread_mutex_lock(&zen_intern_lock);
        char* interned = zen_intern_lookup(s, len, h);
        if (!interned) interned = zen_intern_put(s, len, h);
        pthread_mutex_unlock(&zen_intern_lock);
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

struct ZenList* ZenList_new(void);
struct ZenMap* ZenMap_new(void);
ZenValue ZenSet_new(void);

ZenValue ZenValue_default_for_type(const char* type_name) {
    if (!type_name) return ZEN_DEFAULT_VAL;
    if (strcmp(type_name, "Integer") == 0 ||
        strcmp(type_name, "Integer[64]") == 0 ||
        strcmp(type_name, "Integer[32]") == 0 ||
        strcmp(type_name, "Integer[16]") == 0 ||
        strcmp(type_name, "Integer[8]") == 0 ||
        strcmp(type_name, "Byte") == 0) {
        return ZenValue_make_integer(0);
    }
    if (strcmp(type_name, "Decimal") == 0 ||
        strcmp(type_name, "Decimal[64]") == 0 ||
        strcmp(type_name, "Decimal[32]") == 0) {
        return ZenValue_make_decimal(0.0);
    }
    if (strcmp(type_name, "Boolean") == 0) {
        return ZenValue_make_boolean(false);
    }
    if (strcmp(type_name, "String") == 0 || strncmp(type_name, "String[", 7) == 0 ||
        strcmp(type_name, "Rune") == 0) {
        return ZenValue_make_string("");
    }
    if (strcmp(type_name, "Bytes") == 0) {
        return ZenValue_from_list(ZenList_new());
    }
    if (strcmp(type_name, "List") == 0 || strncmp(type_name, "List<", 5) == 0) {
        return ZenValue_from_list(ZenList_new());
    }
    if (strcmp(type_name, "Vector") == 0 || strncmp(type_name, "Vector[", 7) == 0 || strncmp(type_name, "Vector<", 7) == 0) {
        return ZenValue_from_list(ZenList_new());
    }
    if (strcmp(type_name, "Tuple") == 0 || strncmp(type_name, "Tuple<", 6) == 0) {
        return ZenValue_from_list(ZenList_new());
    }
    if (strcmp(type_name, "Map") == 0 || strncmp(type_name, "Map<", 4) == 0) {
        return ZenValue_from_map(ZenMap_new());
    }
    if (strcmp(type_name, "Set") == 0 || strncmp(type_name, "Set<", 4) == 0) {
        return ZenSet_new();
    }
    if (strcmp(type_name, "Nothing") == 0) {
        return ZEN_NOTHING_VAL;
    }
    return ZEN_DEFAULT_VAL;
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
    ZenHeapHeader_init(&c->header, ZEN_FUNCTION, ZEN_FLAG_CONTAINER);
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
    ZenHeapHeader_init(&c->header, ZEN_FUNCTION, ZEN_FLAG_CONTAINER);
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

void ZenClosure_destroy(ZenClosureData* c) {
    if (!c) return;
    for (int i = 0; i < c->n_caps; i++) {
        ZenValue_release(c->caps[i]);
    }
    if (c->header.ref_count != ZEN_REF_PINNED) {
        free(c);
    }
}

/* Forward declarations of container destructors */
void ZenList_destroy(struct ZenList* list);
void ZenMap_destroy(struct ZenMap* map);
void ZenSet_destroy(struct ZenSet* set);
void ZenVariantObject_destroy(struct ZenVariantObject* v);
void ZenObject_destroy(struct ZenObject* obj);

void ZenValue_destroy_heap_object(ZenHeapHeader* h, ZenValue v) {
    if (!h) return;
    ZenGC_remove_suspect(h);
    h->ref_count = ZEN_REF_DEAD;
    switch (h->type) {
        case ZEN_LIST:
            ZenList_destroy(v.as.list);
            break;
        case ZEN_MAP:
            ZenMap_destroy(v.as.map);
            break;
        case ZEN_SET:
            ZenSet_destroy(v.as.set);
            break;
        case ZEN_VARIANT:
            ZenVariantObject_destroy(v.as.variant);
            break;
        case ZEN_FUNCTION:
            ZenClosure_destroy((ZenClosureData*)v.as.object);
            break;
        case ZEN_OBJECT:
            ZenObject_destroy((struct ZenObject*)v.as.object);
            break;
        case ZEN_CHANNEL:
            ZenChannel_destroy((ZenChannel*)h);
            break;
        case ZEN_TASK:
            ZenTask_destroy((ZenTaskHandle*)h);
            break;
        default:
            break;
    }
}

/* Forward declarations for deep cloning */
struct ZenList* ZenList_deep_clone(struct ZenList* list);
struct ZenMap* ZenMap_deep_clone(struct ZenMap* map);
struct ZenSet* ZenSet_deep_clone(struct ZenSet* set);
struct ZenVariantObject* ZenVariantObject_deep_clone(struct ZenVariantObject* v);
ZenValue ZenValue_from_set(struct ZenSet* set);
ZenValue ZenValue_from_variant(struct ZenVariantObject* v);

typedef struct {
    void* src;
    ZenValue clone;
} ZenClonePair;

#define ZEN_STATIC_CLONE_PAIRS 256
static __thread ZenClonePair zen_static_clone_pairs[ZEN_STATIC_CLONE_PAIRS];
static __thread ZenClonePair* zen_clone_pairs = NULL;
static __thread int zen_clone_count = 0;
static __thread int zen_clone_cap = ZEN_STATIC_CLONE_PAIRS;
static __thread int zen_clone_depth = 0;

void zen_clone_enter(void) {
    zen_clone_depth++;
}

void zen_clone_leave(void) {
    if (--zen_clone_depth == 0) {
        if (zen_clone_pairs != NULL) {
            free(zen_clone_pairs);
            zen_clone_pairs = NULL;
            zen_clone_cap = ZEN_STATIC_CLONE_PAIRS;
        }
        zen_clone_count = 0;
    }
}

ZenValue zen_clone_lookup(void* src) {
    if (!src || zen_clone_count == 0) return (ZenValue){ZEN_NOTHING, {0}};
    ZenClonePair* pairs = zen_clone_pairs ? zen_clone_pairs : zen_static_clone_pairs;
    for (int i = 0; i < zen_clone_count; i++) {
        if (pairs[i].src == src) {
            return pairs[i].clone;
        }
    }
    return (ZenValue){ZEN_NOTHING, {0}};
}

void zen_clone_register(void* src, ZenValue clone) {
    if (!src || zen_clone_depth == 0) return;
    if (zen_clone_count >= zen_clone_cap) {
        int new_cap = zen_clone_cap * 2;
        ZenClonePair* new_p = (ZenClonePair*)malloc(new_cap * sizeof(ZenClonePair));
        if (new_p) {
            ZenClonePair* cur_p = zen_clone_pairs ? zen_clone_pairs : zen_static_clone_pairs;
            memcpy(new_p, cur_p, zen_clone_count * sizeof(ZenClonePair));
            if (zen_clone_pairs != NULL) {
                free(zen_clone_pairs);
            }
            zen_clone_pairs = new_p;
            zen_clone_cap = new_cap;
        } else {
            return;
        }
    }
    ZenClonePair* pairs = zen_clone_pairs ? zen_clone_pairs : zen_static_clone_pairs;
    pairs[zen_clone_count].src = src;
    pairs[zen_clone_count].clone = clone;
    zen_clone_count++;
}

ZenValue ZenValue_clone_to_heap(ZenValue v) {
    if (!ZenValue_is_heap_pointer(v)) return v;

    ZenValue existing = zen_clone_lookup(v.as.object);
    if (existing.type != ZEN_NOTHING) {
        return existing;
    }

    extern void ZenArena_suspend(void);
    extern void ZenArena_resume(void);

    ZenArena_suspend(); 
    zen_clone_enter();
    
    ZenValue promoted = v;
    ZenHeapHeader* h = (ZenHeapHeader*)v.as.object;
    
    switch (h->type) {
        case ZEN_LIST:
            promoted = ZenValue_from_list(ZenList_deep_clone((struct ZenList*)v.as.list));
            break;
        case ZEN_MAP:
            promoted = ZenValue_from_map(ZenMap_deep_clone((struct ZenMap*)v.as.map));
            break;
        case ZEN_SET:
            promoted = ZenValue_from_set(ZenSet_deep_clone((struct ZenSet*)v.as.set));
            break;
        case ZEN_VARIANT:
            promoted = ZenValue_from_variant(ZenVariantObject_deep_clone((struct ZenVariantObject*)v.as.variant));
            break;
        default:
            promoted = v; 
            break;
    }
    
    zen_clone_leave();
    ZenArena_resume();
    return promoted;
}

/* =========================================================================
 * Universal Child Traversal Dispatcher
 * ========================================================================= */
void ZenValue_visit_children(ZenHeapHeader* h, ZenValueVisitor visitor, void* context) {
    if (!h || !(h->flags & ZEN_FLAG_CONTAINER)) return;

    switch (h->type) {
        case ZEN_LIST: {
            ZenList* list = (ZenList*)h;
            for (int i = 0; i < list->count; i++) {
                visitor(list->items[i], context);
            }
            break;
        }
        case ZEN_MAP: {
            ZenMap* map = (ZenMap*)h;
            for (int i = 0; i < map->count; i++) {
                visitor(map->entries[i].key, context);
                visitor(map->entries[i].value, context);
            }
            break;
        }
        case ZEN_SET: {
            ZenSet* set = (ZenSet*)h;
            visitor(set->list, context);
            break;
        }
        case ZEN_VARIANT: {
            ZenVariantObject* var = (ZenVariantObject*)h;
            visitor(var->enum_name, context);
            visitor(var->variant_name, context);
            visitor(var->data, context);
            break;
        }
        case ZEN_FUNCTION: {
            ZenClosureData* closure = (ZenClosureData*)h;
            for (int i = 0; i < closure->n_caps; i++) {
                visitor(closure->caps[i], context);
            }
            break;
        }
        case ZEN_CHANNEL: {
            ZenChannel* ch = (ZenChannel*)h;
            pthread_mutex_lock(&ch->lock);
            for (int i = 0; i < ch->count; i++) {
                int idx = (ch->tail + i) % ch->capacity;
                visitor(ch->buffer[idx], context);
            }
            pthread_mutex_unlock(&ch->lock);
            break;
        }
        case ZEN_TASK: {
            ZenTaskHandle* task = (ZenTaskHandle*)h;
            pthread_mutex_lock(&task->lock);
            visitor(task->callable, context);
            visitor(task->argument, context);
            visitor(task->result, context);
            pthread_mutex_unlock(&task->lock);
            break;
        }
        default:
            break;
    }
}

/* =========================================================================
 * Deep Freezing (Immutable Cross-Thread Promotion)
 * ========================================================================= */
static void freeze_visitor(ZenValue child, void* context) {
    (void)context;
    ZenValue_freeze(child); // Recursively freeze children
}

void ZenValue_freeze(ZenValue v) {
    if (!ZenValue_is_heap_pointer(v)) return;
    if (v.type == ZEN_CHANNEL || v.type == ZEN_TASK) return;
    
    ZenHeapHeader* h = (ZenHeapHeader*)v.as.object;
    if (!h) return;

    // If already frozen or dead, halt the cascade to prevent infinite loops in cyclic graphs
    if (h->ref_count == ZEN_REF_FROZEN || h->ref_count == ZEN_REF_DEAD) {
        return;
    }

    // Lock the header
    h->ref_count = ZEN_REF_FROZEN;
    h->flags |= ZEN_FLAG_FROZEN;

    // Cascade freeze to all children
    ZenValue_visit_children(h, freeze_visitor, NULL);
}
