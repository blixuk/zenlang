#ifndef ZEN_DISPATCH_H
#define ZEN_DISPATCH_H

#include "zen_value.h"

ZenValue ZenValue_call(ZenValue value);
// Apply a function value with 0..N ZenValue arguments (varargs after argc).
ZenValue ZenValue_apply(ZenValue value, int argc, ...);

// Dynamic field access for Map records (and similar) e.g. size.width
ZenValue ZenValue_get_field(ZenValue obj, const char* name);

// Runtime type name for `.kind` (Integer, String, Map, …); Map may override via field
ZenValue ZenValue_get_kind(ZenValue obj);
ZenValue ZenValue_type(ZenValue obj);

// Dynamic dispatch helpers
ZenValue ZenValue_get_length(ZenValue self);
ZenValue ZenValue_get_at(ZenValue self, ZenValue index);
ZenValue ZenValue_get(ZenValue self, ZenValue key, ZenValue default_val);
ZenValue ZenValue_set_at(ZenValue self, ZenValue index, ZenValue value);
ZenValue ZenValue_append(ZenValue self, ZenValue value);
ZenValue ZenValue_pop_dispatch(ZenValue self);
ZenValue ZenValue_peek(ZenValue self);
ZenValue ZenValue_remove(ZenValue self, ZenValue value);
ZenValue ZenValue_remove_at(ZenValue self, ZenValue index);
ZenValue ZenValue_contains(ZenValue self, ZenValue value);
ZenValue ZenValue_in(ZenValue value, ZenValue container);
ZenValue ZenValue_get_keys(ZenValue self);
ZenValue ZenValue_get_values(ZenValue self);
ZenValue ZenValue_get_items(ZenValue self);

ZenValue ZenValue_get_substring(ZenValue self, ZenValue start, ZenValue end);
ZenValue ZenValue_starts_with(ZenValue self, ZenValue prefix);
ZenValue ZenValue_ends_with(ZenValue self, ZenValue suffix);
ZenValue ZenValue_join(ZenValue self, ZenValue separator);

ZenValue ZenValue_write(ZenValue self, ZenValue value);
ZenValue ZenValue_writeln(ZenValue self, ZenValue value);
ZenValue ZenValue_read(ZenValue self);
ZenValue ZenValue_close(ZenValue self);

ZenValue ZenValue_info(ZenValue self, ZenValue value);
ZenValue ZenValue_warn(ZenValue self, ZenValue value);
ZenValue ZenValue_error(ZenValue self, ZenValue value);

// String → number (integer if whole, else decimal)
ZenValue ZenValue_to_number(ZenValue self);

// Serialize helpers (native: return data map; full rehydrate needs registry)
ZenValue ZenValue_instantiate(ZenValue class_obj, ZenValue data);
ZenValue ZenValue_create_object(ZenValue type_name, ZenValue data);

// List/string slice
ZenValue ZenValue_slice(ZenValue self, ZenValue start, ZenValue end, ZenValue step);

#endif // ZEN_DISPATCH_H
