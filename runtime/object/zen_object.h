#ifndef ZEN_OBJECT_H
#define ZEN_OBJECT_H

#include <stdbool.h>
#include "../memory/zen_allocator.h"

// Basic types mapping
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
    ZEN_MAP
} ZenType;

typedef struct ZenValue {
    ZenType type;
    union {
        ZenInteger integer;
        ZenDecimal decimal;
        ZenBoolean boolean;
        ZenString string;
        struct ZenList* list;
        // struct ZenMap* map;
    } as;
} ZenValue;

typedef ZenValue ZenVariant;


// Sentinel for 'nothing'
#define Zen_nothing ((ZenValue){ZEN_NOTHING, {0}})

// ZenList structure
// ZenList structure
typedef struct ZenList {
    ZenVariant* items;
    int count;
    int capacity;
} ZenList;

// Value Constructors
ZenValue zen_int(long long v);
ZenValue zen_float(double v);
ZenValue zen_bool(bool v);
ZenValue zen_str(const char* s);
ZenValue zen_val_list(ZenList* l);


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
int ZenList_length(ZenList* list);
ZenList* ZenList_from_args(int count, ...);

// String functions
ZenString ZenString_create(const char* s);
int ZenString_length(ZenString s);
ZenString ZenString_at(ZenString s, int index);
ZenString ZenString_substring(ZenString s, int start, int end);
ZenList* ZenString_split(ZenString s, ZenString sep);
ZenString ZenString_join(ZenList* parts, ZenString sep);
ZenString ZenString_concat(ZenString s1, ZenString s2);
ZenString ZenString_replace(ZenString s, ZenString old_s, ZenString new_s);
ZenString ZenString_to_upper(ZenString s);
ZenString ZenString_str(ZenVariant x); // This needs to handle ZenValue struct now
int ZenString_starts_with(ZenString s, ZenString prefix);
int ZenString_ends_with(ZenString s, ZenString suffix);
int ZenString_equals(ZenString s1, ZenString s2);
int ZenString_index_of(ZenString s, ZenString sub);

#endif
