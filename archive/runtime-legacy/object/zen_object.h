#ifndef ZEN_OBJECT_H
#define ZEN_OBJECT_H

#include <stdbool.h>
#include "../memory/zen_allocator.h"

// Basic types mapping
typedef long long ZenInteger;
typedef double ZenDecimal;
typedef bool ZenBoolean;
typedef char* ZenString;

typedef enum {
    ZEN_NOTHING,
    ZEN_INTEGER,
    ZEN_DECIMAL,
    ZEN_BOOLEAN,
    ZEN_STRING,
    ZEN_LIST,
    ZEN_MAP,
    ZEN_OBJECT,
    ZEN_ARENA,
    ZEN_VARIANT,
    ZEN_FUNCTION,
    ZEN_NATIVE_FUNCTION
} ZenType;

typedef struct ZenValue ZenValue;
typedef struct ZenArena ZenArena;
typedef ZenValue ZenVariant;

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
    } as;
};


// Sentinel for 'nothing'
#define Zen_nothing ((ZenValue){ZEN_NOTHING, {0}})

// ZenList structure
typedef struct ZenList {
    ZenVariant* items;
    int count;
    int capacity;
} ZenList;

// Value Constructors
#define zen_int(v) ((ZenValue){.type = ZEN_INTEGER, .as.integer = (long long)(v)})
#define zen_bool(v) ((ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (bool)(v)})
#define zen_float(v) ((ZenValue){.type = ZEN_DECIMAL, .as.decimal = (double)(v)})
#define zen_double(v) ((ZenValue){.type = ZEN_DECIMAL, .as.decimal = (double)(v)})

ZenValue zen_str(const char* s);
ZenValue zen_val_list(struct ZenList* l);
ZenValue zen_val_map(struct ZenMap* m);
ZenValue zen_val_object(void* o);
ZenValue zen_val_arena(ZenArena* a);

static inline ZenValue __zen_box_val(ZenValue v) { return v; }
static inline ZenValue __zen_box_bool(bool v) { return zen_bool(v); }
static inline ZenValue __zen_box_int(long long v) { return zen_int(v); }
static inline ZenValue __zen_box_double(double v) { return zen_float(v); }
static inline ZenValue __zen_box_str(const char* v) { return zen_str(v); }
static inline ZenValue __zen_box_obj(void* v) { return zen_val_object(v); }

static inline bool __zen_unbox_bool(ZenValue v) { return v.as.boolean; }
static inline int __zen_unbox_int(ZenValue v) { return (int)v.as.integer; }
static inline long long __zen_unbox_long(ZenValue v) { return v.as.integer; }
static inline double __zen_unbox_decimal(ZenValue v) { return v.as.decimal; }
static inline char* __zen_unbox_string(ZenValue v) { return v.as.string; }
static inline void* __zen_unbox_object(ZenValue v) { return v.as.object; }
static inline ZenValue __zen_unbox_val(ZenValue v) { return v; }

// Macro-based ABI helpers
#define ZEN_BOX(v) _Generic((v), \
    ZenValue: __zen_box_val, \
    bool: __zen_box_bool, \
    int: __zen_box_int, \
    long: __zen_box_int, \
    long long: __zen_box_int, \
    double: __zen_box_double, \
    char*: __zen_box_str, \
    const char*: __zen_box_str, \
    default: __zen_box_obj \
)((v))

#define ZEN_UNBOX(v, t) _Generic((t), \
    bool: __zen_unbox_bool, \
    int: __zen_unbox_int, \
    long long: __zen_unbox_long, \
    double: __zen_unbox_decimal, \
    char*: __zen_unbox_string, \
    ZenValue: __zen_unbox_val, \
    default: __zen_unbox_object \
)(_Generic((v), ZenValue: (v), default: (ZenValue){0}))

#define ZEN_ASSIGN(lhs, rhs) (lhs) = (rhs)

// Bitwise Operations
ZenValue ZenValue_and(ZenValue a, ZenValue b);
ZenValue ZenValue_or(ZenValue a, ZenValue b);
ZenValue ZenValue_xor(ZenValue a, ZenValue b);
ZenValue ZenValue_not(ZenValue a);
ZenValue ZenValue_lshift(ZenValue a, ZenValue b);
ZenValue ZenValue_rshift(ZenValue a, ZenValue b);
ZenValue ZenValue_mod(ZenValue a, ZenValue b);


// List functions
ZenList* ZenList_create();
void ZenList_append(ZenList* list, ZenVariant item);
ZenVariant ZenList_get(ZenList* list, int index);
ZenValue ZenList_count(ZenList* list);
ZenList* ZenList_from_args(int count, ...);

// String functions
ZenString ZenString_ptr(ZenValue v);
ZenString ZenString_create(const char* s);
ZenValue ZenString_count(ZenValue s);
#define ZenString_length ZenString_count
ZenValue ZenString_at(ZenValue s, ZenValue index);
ZenValue ZenString_substring(ZenValue s, ZenValue start, ZenValue end);
ZenValue ZenString_split(ZenValue s, ZenValue sep);
ZenValue ZenString_join(ZenList* parts, ZenValue sep);
ZenValue ZenString_concat(ZenValue s1, ZenValue s2);
ZenValue ZenString_replace(ZenValue s, ZenValue old_s, ZenValue new_s);
ZenValue ZenString_str(ZenValue x); 
ZenValue ZenString_starts_with(ZenValue s, ZenValue prefix);
ZenValue ZenString_ends_with(ZenValue s, ZenValue suffix);
ZenValue ZenString_equals(ZenValue s1, ZenValue s2);
ZenValue ZenString_index_of(ZenValue s, ZenValue sub);
ZenValue ZenString_to_upper(ZenValue s);
ZenValue ZenString_to_lower(ZenValue s);

#endif
