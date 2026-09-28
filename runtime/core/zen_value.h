#ifndef ZEN_VALUE_H
#define ZEN_VALUE_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

typedef long long ZenInteger;
typedef double ZenDecimal;
typedef bool ZenBoolean;
typedef char* ZenString;

typedef enum {
    ZEN_NOTHING,
    ZEN_DEFAULT,
    ZEN_INTEGER,
    ZEN_DECIMAL,
    ZEN_BOOLEAN,
    ZEN_STRING,
    ZEN_LIST,
    ZEN_MAP,
    ZEN_OBJECT,
    ZEN_ARENA,
    ZEN_ERROR,
    ZEN_FUNCTION,
    ZEN_VARIANT,
    ZEN_SET,
    ZEN_AST_NODE,
    ZEN_TOKEN,
    ZEN_CHANNEL,
    ZEN_TASK
} ZenType;

/* =========================================================================
 * Zenlang Intrusive Heap Header & Reference Counting Sentinels
 * ========================================================================= */

#define ZEN_REF_PINNED  (-1)  /* Allocated in an Arena: Retain/Release are NO-OPs */
#define ZEN_REF_FROZEN  (-2)  /* Deeply immutable: Cross-thread safe, Retain/Release NO-OP */
#define ZEN_REF_DEAD    (0)   /* Marked for destruction */

#define ZEN_FLAG_NONE       0x00
#define ZEN_FLAG_CONTAINER  0x01  /* Can hold child references (List, Map, Variant) */
#define ZEN_FLAG_FROZEN     0x02  /* Immutable bit */
#define ZEN_FLAG_PINNED     0x04  /* Resides in bump arena */

typedef struct ZenHeapHeader {
    int32_t ref_count;   /* 4 bytes */
    uint8_t type;        /* 1 byte  */
    uint8_t flags;       /* 1 byte  */
    uint16_t extra;      /* 2 bytes */
} ZenHeapHeader;         /* Exactly 8 bytes */

typedef struct ZenValue ZenValue;
typedef struct ZenArena ZenArena;
typedef ZenValue ZenVariant;
typedef struct ZenChannel ZenChannel;
typedef struct ZenTaskHandle ZenTaskHandle;
struct ZenAstNode;
struct ZenToken;
struct ZenChannel;
struct ZenTaskHandle;

/* Forward declarations for payload destruction cascade */
void ZenValue_destroy_heap_object(ZenHeapHeader* h, ZenValue v);
void ZenTask_destroy(struct ZenTaskHandle* task);

/* =========================================================================
 * Universal Graph Traversal & Deep Freezing
 * ========================================================================= */
typedef void (*ZenValueVisitor)(ZenValue child, void* context);

void ZenValue_visit_children(ZenHeapHeader* h, ZenValueVisitor visitor, void* context);
void ZenValue_freeze(ZenValue v);

/* =========================================================================
 * Deferred Cycle Collector
 * ========================================================================= */
void ZenGC_add_suspect(ZenHeapHeader* h);
void ZenGC_remove_suspect(ZenHeapHeader* h);
void ZenGC_collect_cycles(void);
int ZenGC_suspect_count(void);

struct ZenValue {
    ZenType type;
    union {
        ZenInteger integer;
        ZenDecimal decimal;
        ZenBoolean boolean;
        ZenString string;
        struct ZenList* list;
        struct ZenMap* map;
        void *object;   // For class instances
        ZenArena* arena;
        struct ZenVariantObject* variant;
        struct ZenSet* set;
        ZenValue (*func)(void); // Simple function pointer
        struct ZenAstNode* ast_node;
        struct ZenToken* token;
        struct ZenChannel* channel;
        struct ZenTaskHandle* task;
    } as;
};

static inline bool ZenValue_is_heap_pointer(ZenValue v) {
    if (v.as.object == NULL) return false;
    return (v.type == ZEN_LIST ||
            v.type == ZEN_MAP ||
            v.type == ZEN_SET ||
            v.type == ZEN_VARIANT ||
            v.type == ZEN_CHANNEL ||
            v.type == ZEN_TASK ||
            (v.type == ZEN_FUNCTION && v.as.object != NULL));
}

static inline ZenHeapHeader* ZenValue_get_header(ZenValue v) {
    if (!ZenValue_is_heap_pointer(v)) return NULL;
    return (ZenHeapHeader*)v.as.object;
}

static inline void ZenValue_retain(ZenValue v) {
    if (!ZenValue_is_heap_pointer(v)) return;
    ZenHeapHeader* h = (ZenHeapHeader*)v.as.object;
    if (!h) return;
    if (h->type == ZEN_TASK || h->type == ZEN_CHANNEL) {
        __atomic_add_fetch(&h->ref_count, 1, __ATOMIC_RELAXED);
        return;
    }
    if (h->ref_count > 0) {
        h->ref_count++;
    }
}

static inline void ZenValue_release(ZenValue v) {
    if (!ZenValue_is_heap_pointer(v)) return;
    ZenHeapHeader* h = (ZenHeapHeader*)v.as.object;
    if (!h) return;
    if (h->type == ZEN_TASK || h->type == ZEN_CHANNEL) {
        if (__atomic_sub_fetch(&h->ref_count, 1, __ATOMIC_ACQ_REL) == 0) {
            ZenValue_destroy_heap_object(h, v);
        }
        return;
    }
    if (h->ref_count > 0) {
        if (--h->ref_count == 0) {
            ZenValue_destroy_heap_object(h, v);
        } else if (h->flags & ZEN_FLAG_CONTAINER) {
            // Forward alive containers to the Deferred Cycle Collector
            ZenGC_add_suspect(h);
        }
    }
}

ZenValue ZenValue_clone_to_heap(ZenValue v);
void zen_clone_enter(void);
void zen_clone_leave(void);
ZenValue zen_clone_lookup(void* src);
void zen_clone_register(void* src, ZenValue clone);

/* 
 * The Heap Promotion Write Barrier.
 * Intercepts PINNED arena objects escaping into standard heap containers.
 */
static inline ZenValue ZenValue_write_barrier_target(ZenHeapHeader* dest_header, ZenValue v) {
    if (!ZenValue_is_heap_pointer(v)) return v;

    ZenHeapHeader* h = (ZenHeapHeader*)v.as.object;
    if (h && h->ref_count == ZEN_REF_PINNED) {
        // Zero-tax pairing: both destination and value are in the arena
        if (dest_header && dest_header->ref_count == ZEN_REF_PINNED) {
            return v;
        }
        // Arena Escape: Promote via deep-clone to the standard heap
        return ZenValue_clone_to_heap(v);
    }

    // Standard heap object: retain normally
    ZenValue_retain(v);
    return v;
}

static inline ZenValue ZenValue_write_barrier(ZenValue v) {
    return ZenValue_write_barrier_target(NULL, v);
}

static inline void ZenHeapHeader_init(ZenHeapHeader* h, ZenType type, uint8_t flags) {
    extern int ZenArena_stack_depth(void);
    h->type = (uint8_t)type;
    h->extra = 0;
    
    if (ZenArena_stack_depth() > 0) {
        h->ref_count = ZEN_REF_PINNED;
        h->flags = flags | ZEN_FLAG_PINNED;
    } else {
        h->ref_count = 1;
        h->flags = flags;
    }
}

#define ZEN_NOTHING_VAL ((ZenValue){ZEN_NOTHING, {0}})
#define ZEN_DEFAULT_VAL ((ZenValue){ZEN_DEFAULT, {0}})

// Value Constructors
#define ZenValue_make_integer(v) ((ZenValue){.type = ZEN_INTEGER, .as.integer = (long long)(v)})
#define ZenValue_make_boolean(v) ((ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (bool)(v)})
#define ZenValue_from_boolean(v) ZenValue_make_boolean(v)
#define ZenValue_make_decimal(v) ((ZenValue){.type = ZEN_DECIMAL, .as.decimal = (double)(v)})


// C Interop Unboxers
#define ZenValue_to_c_int(v) ((long long)((v).as.integer))
#define ZenValue_to_c_dec(v) ((double)((v).as.decimal))
#define ZenValue_to_c_str(v) ((const char*)((v).as.string))
#define ZenValue_to_c_bool(v) ((bool)((v).as.boolean))
#define ZenValue_to_c_ptr(v) ((void*)((v).as.object))

ZenValue ZenValue_make_string(const char* s);
ZenValue ZenValue_make_nothing(void);
ZenValue ZenValue_make_default(void);
ZenValue ZenValue_default_for_type(const char* type_name);
ZenValue ZenValue_from_list(struct ZenList* l);
ZenValue ZenValue_from_map(struct ZenMap* m);
ZenValue ZenValue_from_object(void* o);
ZenValue ZenValue_from_arena(ZenArena* a);
ZenValue ZenValue_make_error(ZenValue message);
/* Function values: see zen_closure.h (ZenValue_from_function / from_closure). */
ZenValue ZenValue_from_function(ZenValue (*f)(void));
ZenValue ZenValue_from_closure(void* fn, int arity, int n_caps, ...);

// Common operations
ZenValue ZenValue_get_length(ZenValue v);
ZenValue ZenValue_get_index(ZenValue v, ZenValue index);

// Predicates return ZenValue booleans so generated temps stay uniformly typed.
static inline ZenValue ZenValue_is_nothing(ZenValue v) {
    return ZenValue_make_boolean(v.type == ZEN_NOTHING);
}
ZenValue ZenValue_is_error(ZenValue v);

// Unboxing helpers
#define ZenValue_to_integer(v) ((v).as.integer)
#define ZenValue_to_decimal(v) ((v).as.decimal)
#define ZenValue_to_boolean(v) ((v).as.boolean)
#define ZenValue_as_string(v) ((v).as.string)
#define ZenValue_to_list(v) ((v).as.list)
#define ZenValue_to_map(v) ((v).as.map)
#define ZenValue_to_object(v) ((v).as.object)

static inline ZenValue __zen_box_val(ZenValue v) { return v; }
static inline ZenValue __zen_box_bool(bool v) { return ZenValue_make_boolean(v); }
static inline ZenValue __zen_box_int(int v) { return ZenValue_make_integer(v); }
static inline ZenValue __zen_box_long(long long v) { return ZenValue_make_integer(v); }
static inline ZenValue __zen_box_double(double v) { return ZenValue_make_decimal(v); }
static inline ZenValue __zen_box_str(const char* v) { return ZenValue_make_string(v); }
static inline ZenValue __zen_box_obj(void* v) { return ZenValue_from_object(v); }
static inline ZenValue __zen_box_uint(unsigned long long v) { return ZenValue_make_integer((long long)v); }
static inline ZenValue __zen_box_float(float v) { return ZenValue_make_decimal((double)v); }

// C11 Automatic Type Boxing for C Interop (extern use)
#define ZenValue_from_c(expr) _Generic((expr), \
    ZenValue:             __zen_box_val, \
    bool:                 __zen_box_bool, \
    char:                 __zen_box_int, \
    signed char:          __zen_box_int, \
    unsigned char:        __zen_box_uint, \
    short:                __zen_box_int, \
    unsigned short:       __zen_box_uint, \
    int:                  __zen_box_int, \
    unsigned int:         __zen_box_uint, \
    long:                 __zen_box_long, \
    unsigned long:        __zen_box_uint, \
    long long:            __zen_box_long, \
    unsigned long long:   __zen_box_uint, \
    float:                __zen_box_float, \
    double:               __zen_box_double, \
    char*:                __zen_box_str, \
    const char*:          __zen_box_str, \
    void*:                __zen_box_obj, \
    default:              __zen_box_obj \
)(expr)

static inline bool __zen_unbox_bool(ZenValue v) { return v.as.boolean; }
static inline int __zen_unbox_int(ZenValue v) { return (int)v.as.integer; }
static inline long long __zen_unbox_long(ZenValue v) { return v.as.integer; }
static inline double __zen_unbox_decimal(ZenValue v) { return v.as.decimal; }
static inline char* __zen_unbox_string(ZenValue v) { return v.as.string; }
static inline void* __zen_unbox_object(ZenValue v) { return v.as.object; }
static inline ZenValue __zen_unbox_val(ZenValue v) { return v; }

#define ZEN_ASSIGN(lhs, rhs) (lhs) = (rhs)

#define ZEN_BOX(v) _Generic((v), \
    ZenValue: __zen_box_val, \
    bool: __zen_box_bool, \
    int: __zen_box_int, \
    long: __zen_box_long, \
    long long: __zen_box_long, \
    double: __zen_box_double, \
    char*: __zen_box_str, \
    const char*: __zen_box_str, \
    default: __zen_box_obj \
)(v)


#define ZEN_UNBOX(v, t) _Generic((v), \
    ZenValue: _Generic((t), \
        ZenValue: __zen_unbox_val, \
        bool: __zen_unbox_bool, \
        long long: __zen_unbox_long, \
        int: __zen_unbox_int, \
        double: __zen_unbox_decimal, \
        char*: __zen_unbox_string, \
        default: __zen_unbox_object \
    )(_Generic((v), ZenValue: (v), default: (ZenValue){0})), \
    default: (v) \
)

#endif // ZEN_VALUE_H
