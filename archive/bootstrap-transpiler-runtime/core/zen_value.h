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
    ZEN_SET
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
        struct ZenSet* set;
        ZenValue (*func)(void); // Simple function pointer
    } as;
};

#define ZEN_NOTHING_VAL ((ZenValue){ZEN_NOTHING, {0}})

// Value Constructors
#define ZenValue_make_integer(v) ((ZenValue){.type = ZEN_INTEGER, .as.integer = (long long)(v)})
#define ZenValue_make_boolean(v) ((ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (bool)(v)})
#define ZenValue_make_decimal(v) ((ZenValue){.type = ZEN_DECIMAL, .as.decimal = (double)(v)})

ZenValue ZenValue_make_string(const char* s);
ZenValue ZenValue_make_nothing(void);
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
