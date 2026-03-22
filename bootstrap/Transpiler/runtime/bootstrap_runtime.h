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
    ZEN_OBJECT
} ZenType;

typedef struct ZenValue ZenValue;
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

// Macro-based constructors for global initialization
#define ZEN_VAL_INT(v) ((ZenValue){ZEN_INTEGER, {.integer = (v)}})
#define ZEN_VAL_BOOL(v) ((ZenValue){ZEN_BOOLEAN, {.boolean = (v)}})
#define ZEN_VAL_STR(v) ((ZenValue){ZEN_STRING, {.string = (v)}})

// Sentinel for 'nothing'
#define Zen_nothing ((ZenValue){ZEN_NOTHING, {0}})

// Value Constructors
ZenValue zen_int(long long v);
ZenValue zen_float(double v);
ZenValue zen_bool(bool v);
ZenValue zen_str(const char* s);
ZenValue zen_make_string(const char* s);
ZenValue zen_make_integer(long long v);
ZenValue zen_make_boolean(int v);
ZenValue zen_make_float(double v);
ZenValue zen_make_null(void);
ZenValue zen_val_list(struct ZenList* l);
ZenValue zen_val_map(struct ZenMap* m);
ZenValue zen_val_object(void* o);

// List structure and functions
typedef struct ZenList {
    ZenVariant* items;
    int count;
    int capacity;
} ZenList;

ZenList* ZenList_create();
ZenList* ZenList_from_args(int n, ...);
void ZenList_append(ZenList* list, ZenVariant item);
ZenVariant ZenList_get(ZenList* list, int index);
ZenValue ZenList_length(ZenList* list);

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
ZenMap* ZenMap_from_args(int n, ...);
void ZenMap_set(ZenMap* map, ZenVariant key, ZenVariant value);
ZenVariant ZenMap_get(ZenMap* map, ZenVariant key);
ZenValue ZenMap_length(ZenMap* map);

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

// String functions
ZenString ZenString_create(const char* s);
ZenValue ZenString_length(ZenString s);
ZenValue ZenString_at(ZenString s, int index);
ZenValue ZenString_substring(ZenString s, int start, int end);
ZenValue ZenString_split(ZenString s, ZenString sep);
ZenValue ZenString_join(ZenList* parts, ZenString sep);
ZenValue ZenString_concat(ZenString s1, ZenString s2);
ZenValue ZenString_replace(ZenString s, ZenString old_s, ZenString new_s);
ZenValue ZenValue_str(ZenValue v);
ZenValue ZenString_to_upper(ZenString s);
ZenString ZenString_str(ZenVariant x); // This is a helper, stays char*
ZenValue ZenString_starts_with(ZenString s, ZenString prefix);
ZenValue ZenString_ends_with(ZenString s, ZenString suffix);
ZenValue ZenString_equals(ZenString s1, ZenString s2);
ZenValue ZenString_index_of(ZenString s, ZenString sub);
ZenValue ZenString_to_lower(ZenString s);
ZenValue ZenString_trim(ZenString s);

// Print helpers
void zl_print_begin(void);
void zl_print_sep(void);
void zl_print_end(void);
void zl_print_int(long long v);
void zl_print_float(double v);
void zl_print_string(const char* v);
void zl_print_bool(bool v);

// IO functions
ZenValue IO_write(ZenValue v);
ZenValue out_write(ZenString s, void* data);
ZenValue IO_write_int(long long v);
ZenValue IO_error(ZenValue v);
ZenValue IO_file_exists(ZenValue path);
ZenValue IO_read_file(ZenValue path);
ZenValue IO_write_file(ZenValue path, ZenValue content);
// Sys arguments
void _Sys_init_args(int argc, char** argv);
ZenValue Sys_get_args();
ZenList* _Sys_get_args();

// Sys functions
ZenValue Sys_exit(int code);
ZenValue Sys_get_env(ZenString name);

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

#endif /* ZEN_BOOTSTRAP_RUNTIME_H */
