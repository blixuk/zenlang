#ifndef ZEN_BOOTSTRAP_RUNTIME_H
#define ZEN_BOOTSTRAP_RUNTIME_H

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <setjmp.h>
#include "object/zen_object.h"
#include "sys/zen_sys.h"
#include "io/zen_io.h"


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

#define ZEN_TRUE ((ZenValue){.type = ZEN_BOOLEAN, .as.boolean = true})
#define ZEN_FALSE ((ZenValue){.type = ZEN_BOOLEAN, .as.boolean = false})
#define True ZEN_TRUE
#define False ZEN_FALSE
#define None Zen_nothing

// Value Constructors - already in zen_object.h or here
ZenValue zen_make_string(const char* s);
ZenValue zen_make_integer(long long v);
ZenValue zen_make_boolean(int v);
ZenValue zen_make_float(double v);
ZenValue zen_make_null(void);
ZenValue zen_val_map(struct ZenMap* m);
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
ZenValue ZenString_count(ZenValue s);
ZenValue ZenString_at(ZenValue s, ZenValue index);
ZenValue ZenString_substring(ZenValue s, ZenValue start, ZenValue end);
ZenValue ZenString_split(ZenValue s, ZenValue sep);
ZenValue ZenString_join(ZenList* parts, ZenValue sep);
ZenValue ZenString_concat(ZenValue s1, ZenValue s2);
ZenValue ZenString_replace(ZenValue s, ZenValue old_s, ZenValue new_s);
ZenValue ZenString_to_string(ZenValue v);
ZenValue ZenValue_str(ZenValue v);
ZenValue ZenString_to_upper(ZenValue s);
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

void zen_exception_push(void* ctx);
void zen_exception_pop(void);
void zen_raise(ZenValue val);

void zen_defer_push(void (*func)(void*), void *data);
void zen_defer_run_to(int depth);
int zen_defer_depth(void);

// Arena management
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

void zl_init_runtime(void);

#endif /* ZEN_BOOTSTRAP_RUNTIME_H */
