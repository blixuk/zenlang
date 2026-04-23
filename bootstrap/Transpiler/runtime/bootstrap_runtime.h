#ifndef ZEN_BOOTSTRAP_RUNTIME_H
#define ZEN_BOOTSTRAP_RUNTIME_H

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <setjmp.h>

// Basic types mapping from zen_object.h
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
    ZEN_VARIANT
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

// Generic object base
typedef struct ZenObject {
    ZenValue __none; 
} ZenObject;

struct ZenObject_struct {
    ZenValue kind;
    ZenValue value;
    ZenValue name;
    ZenValue path;
    ZenValue line;
    ZenValue column;
    ZenValue statements;
    ZenValue expression;
    ZenValue arguments;
};

typedef struct ZenVariantObject {
    ZenValue enum_name;
    ZenValue variant_name;
    ZenValue data; // ZenList* of ZenValue
} ZenVariantObject;

// Sentinel for 'nothing'
#define Zen_nothing ((ZenValue){ZEN_NOTHING, {0}})

// Value Constructors
ZenValue zen_int(long long v);
ZenValue zen_float(double v);
ZenValue zen_bool(bool v);
ZenValue zen_str(const char* s);
ZenValue zen_make_string(const char* s);
#define zen_int(v) ((ZenValue){.type = ZEN_INTEGER, .as.integer = (long long)(v)})
#define zen_bool(v) ((ZenValue){.type = ZEN_BOOLEAN, .as.boolean = (bool)(v)})
#define zen_float(v) ((ZenValue){.type = ZEN_DECIMAL, .as.decimal = (double)(v)})
#define zen_double(v) ((ZenValue){.type = ZEN_DECIMAL, .as.decimal = (double)(v)})

ZenValue zen_make_integer(long long v);
ZenValue zen_make_boolean(int v);
ZenValue zen_make_float(double v);
ZenValue zen_make_null(void);
ZenValue zen_val_list(struct ZenList* l);
ZenValue zen_val_map(struct ZenMap* m);
ZenValue zen_val_object(void* o);
ZenValue zen_val_arena(ZenArena* a);
ZenValue zen_error(ZenValue message);
ZenValue ZenValue_new_variant(ZenValue enum_name, ZenValue variant_name, int n_params, ...);
ZenValue ZenValue_is_variant(ZenValue val, ZenValue expected_enum, ZenValue expected_variant);
ZenValue ZenValue_get_variant_name(ZenValue val);
ZenValue ZenValue_get_variant_data(ZenValue val, ZenValue index);

static inline void* zen_get_body_ptr(void* obj) {
    if (!obj) return NULL;
    int kind = *(int*)obj;
    // ASTKind: FUNCTION_STATEMENT=16, FOR_STATEMENT=27, CASE_CLAUSE=34, CHECK_EXPRESSION=31
    if (kind == 16 || kind == 27 || kind == 31 || kind == 34) {
        return ((void**)obj)[3]; // 4th field
    }
    return ((void**)obj)[2]; // 3rd field (While/When/DoWhile)
}

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
    ZenValue: (v), \
    bool: zen_bool(v), \
    int: zen_int(v), \
    long: zen_int((long long)v), \
    long long: zen_int(v), \
    double: zen_float(v), \
    char*: zen_str(v), \
    const char*: zen_str(v), \
    default: zen_val_object((void*)(v)) \
)

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

#define ZEN_ASSIGN(lhs, rhs) (lhs) = (rhs)


// List structure and functions
typedef struct ZenList {
    ZenVariant* items;
    int count;
    int capacity;
} ZenList;

ZenList* ZenList_create();
ZenValue ZenList_from_args(int n, ...);
void ZenList_append(ZenList* list, ZenVariant item);
ZenVariant ZenList_get(ZenList* list, int index);
void ZenList_set(ZenList* list, int index, ZenVariant item);
ZenValue ZenList_count(ZenList* list);

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

ZenMap* ZenMap_create();
ZenValue ZenMap_from_args(int n, ...);
void ZenMap_set(ZenMap* map, ZenVariant key, ZenVariant value);
ZenVariant ZenMap_get(ZenMap* map, ZenVariant key);
ZenValue ZenMap_count(ZenMap* map);

ZenValue ZenValue_equals(ZenValue a, ZenValue b);
ZenValue ZenValue_not(ZenValue a);
ZenValue ZenValue_neg(ZenValue a);
ZenValue ZenValue_add(ZenValue a, ZenValue b);
ZenValue ZenValue_sub(ZenValue a, ZenValue b);
ZenValue ZenValue_mul(ZenValue a, ZenValue b);
ZenValue ZenValue_div(ZenValue a, ZenValue b);
ZenValue ZenValue_mod(ZenValue a, ZenValue b);
ZenValue ZenValue_pow(ZenValue a, ZenValue b);
ZenValue ZenValue_less_than(ZenValue a, ZenValue b);
ZenValue ZenValue_greater_than(ZenValue a, ZenValue b);
ZenValue ZenValue_less_than_or_equal(ZenValue a, ZenValue b);
ZenValue ZenValue_greater_than_or_equal(ZenValue a, ZenValue b);
ZenValue ZenValue_not_equals(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_and(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_or(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_xor(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_not(ZenValue a);
ZenValue ZenValue_bitwise_mod(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_nor(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_nand(ZenValue a, ZenValue b);
ZenValue ZenValue_bitwise_xnor(ZenValue a, ZenValue b);
ZenValue ZenValue_lshift(ZenValue a, ZenValue b);
ZenValue ZenValue_rshift(ZenValue a, ZenValue b);
ZenValue ZenValue_and(ZenValue a, ZenValue b);
ZenValue ZenValue_or(ZenValue a, ZenValue b);
ZenValue ZenValue_xor(ZenValue a, ZenValue b);
ZenValue ZenValue_nor(ZenValue a, ZenValue b);
ZenValue ZenValue_nand(ZenValue a, ZenValue b);
ZenValue ZenValue_xnor(ZenValue a, ZenValue b);
ZenValue ZenValue_is_type_name(ZenValue val, const char* type_name);


// String functions
const char* ZenString_ptr(ZenValue v);
ZenString ZenString_create(const char* s);
ZenValue ZenString_count(ZenValue s);
#define ZenString_length ZenString_count
ZenValue ZenString_at(ZenValue s, ZenValue index);
ZenValue ZenString_substring(ZenValue s, ZenValue start, ZenValue end);
ZenValue ZenString_split(ZenValue s, ZenValue sep);
ZenValue ZenString_join(ZenList* parts, ZenValue sep);
ZenValue ZenString_concat(ZenValue s1, ZenValue s2);
ZenValue ZenString_replace(ZenValue s, ZenValue old_s, ZenValue new_s);
ZenValue ZenString_to_string(ZenValue v);
ZenValue ZenValue_str(ZenValue v);
ZenValue ZenString_to_upper(ZenValue s);
ZenString ZenString_str(ZenValue x); // This helper should also take ZenValue
ZenValue ZenString_starts_with(ZenValue s, ZenValue prefix);
ZenValue ZenString_ends_with(ZenValue s, ZenValue suffix);
ZenValue ZenString_equals(ZenValue s1, ZenValue s2);
ZenValue ZenString_index_of(ZenValue s, ZenValue sub);
ZenValue ZenString_to_lower(ZenValue s);
ZenValue ZenString_trim(ZenValue s);

// Print helpers
void zl_print_begin(void);
void zl_print_sep(void);
void zl_print_end(void);
void zl_print_int(long long v);
void zl_print_float(double v);
void zl_print_string(const char* v);
void zl_print_bool(bool v);

// Built-in objects
extern ZenValue __builtin_output;
extern ZenValue __builtin_input;
extern ZenValue __builtin_file;
extern ZenValue __builtin_sys;
extern ZenValue __builtin_string;

// IO functions
ZenValue ZenIO_write(ZenValue self, ZenValue v);
ZenValue ZenIO_info(ZenValue self, ZenValue v);
ZenValue ZenIO_warn(ZenValue self, ZenValue v);
ZenValue ZenIO_debug(ZenValue self, ZenValue v);
ZenValue ZenIO_error(ZenValue self, ZenValue v);
ZenValue ZenIO_out_write(ZenValue self, ZenValue s); 
ZenValue ZenIO_write_int(ZenValue self, long long v);
ZenValue ZenIO_file_exists(ZenValue self, ZenValue path);
ZenValue ZenIO_read(ZenValue self, ZenValue prompt);
ZenValue ZenIO_read_file(ZenValue self, ZenValue path);
ZenValue ZenIO_write_file(ZenValue self, ZenValue path, ZenValue content);

// Sys functions
void _ZenSys_init_args(int argc, char** argv);
ZenValue ZenSys_get_args(ZenValue self);
ZenValue ZenSys_exit(ZenValue self, ZenValue code);
ZenValue ZenSys_get_env(ZenValue self, ZenValue name);
ZenValue ZenSys_get_cwd(ZenValue self);
ZenValue ZenSys_platform(ZenValue self);
ZenValue ZenSys_version(ZenValue self);
void zl_init_runtime();
ZenValue __builtin_error(ZenValue msg);
ZenValue __builtin_error_literal(ZenValue msg);

// Exception and Defer handling
typedef struct ZenDeferNode {
    void (*func)(void*);
    void *data;
    struct ZenDeferNode *next;
} ZenDeferNode;

typedef struct {
    jmp_buf buf;
    int defer_depth;
} ZenExceptionContext;

extern ZenValue zen_last_exception;

void zen_exception_push(ZenExceptionContext *ctx);
void zen_exception_pop(void);
void zen_raise(ZenValue val);

void zen_defer_push(void (*func)(void*), void *data);
void zen_defer_run_to(int depth);
int zen_defer_depth(void);

// Arena management
typedef struct ZenArena ZenArena;
ZenArena* zen_arena_create(size_t size);
void* zen_arena_alloc(ZenArena* arena, size_t size);
void zen_arena_reset(ZenArena* arena);
void zen_arena_free(ZenArena* arena);
void zen_arena_push(ZenArena* arena);
void zen_arena_pop(void);
ZenValue ZenValue_get_index(ZenValue obj, ZenValue index);
void ZenValue_set_index(ZenValue obj, ZenValue index, ZenValue value);
void* zen_malloc(size_t size);

/* Memory Module Primitives */
ZenValue Memory_create_arena(ZenValue size);
ZenValue Memory_free_arena(ZenValue arena);
ZenValue Memory_reset_arena(ZenValue arena);
ZenValue Memory_push_arena(ZenValue arena);
ZenValue Memory_pop_arena(void);

#endif /* ZEN_BOOTSTRAP_RUNTIME_H */
