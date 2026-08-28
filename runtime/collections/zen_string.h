#ifndef ZEN_STRING_H
#define ZEN_STRING_H

#include "zen_value.h"
#include "zen_list.h"

const char* ZenString_get_pointer(ZenValue value);
ZenValue ZenString_get_length(ZenValue string);
ZenValue ZenString_get_character_at_index(ZenValue string, ZenValue index);
ZenValue ZenString_get_substring(ZenValue string, ZenValue start, ZenValue end);
ZenValue ZenString_split(ZenValue string, ZenValue separator);
ZenValue ZenString_join(ZenValue list, ZenValue separator);
ZenValue ZenString_concatenate(ZenValue s1, ZenValue s2);
ZenValue ZenString_replace(ZenValue string, ZenValue old_value, ZenValue new_value);
ZenValue ZenString_to_uppercase(ZenValue string);
ZenValue ZenString_to_lowercase(ZenValue string);
ZenValue ZenString_trim(ZenValue string);
ZenValue ZenString_starts_with(ZenValue string, ZenValue prefix);
ZenValue ZenString_ends_with(ZenValue string, ZenValue suffix);
ZenValue ZenString_find_index(ZenValue string, ZenValue substring);
ZenValue ZenString_index_of(ZenValue string, ZenValue substring);
ZenValue ZenString_at(ZenValue string, ZenValue index);
ZenValue ZenString_contains(ZenValue string, ZenValue substring);

// Global unboxing/string conversion
ZenValue ZenValue_to_string(ZenValue value);

#endif // ZEN_STRING_H
