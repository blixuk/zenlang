#ifndef ZEN_REFLECT_H
#define ZEN_REFLECT_H

#include "zen_value.h"

/* Type metadata registry for `is reflectable` structures/classes. */

void ZenReflect_runtime_init(void);

/* Register type metadata: fields and methods are lists of strings. */
void ZenReflect_register_type(ZenValue type_name, ZenValue fields, ZenValue methods);

/* Tag a native class instance pointer with its type name (for method/field lookup). */
void ZenReflect_tag_object(void* ptr, const char* type_name);

/* Lookup helpers (empty list / nothing when unknown). */
ZenValue ZenReflect_fields(ZenValue value);
ZenValue ZenReflect_methods(ZenValue value);
ZenValue ZenReflect_has_field(ZenValue value, ZenValue name);
ZenValue ZenReflect_has_method(ZenValue value, ZenValue name);
ZenValue ZenReflect_field(ZenValue value, ZenValue name);
ZenValue ZenReflect_set_field(ZenValue value, ZenValue name, ZenValue new_value);
ZenValue ZenReflect_type_name(ZenValue value);
ZenValue ZenReflect_is_reflectable(ZenValue value);

/*
 * Dynamic call: map[name](args…) or instance method by name.
 * args must be a List (may be empty).
 *
 * Class methods: register invokers with ZenReflect_register_method
 * (compiler emits thunks for `is reflectable` classes under -g).
 */
typedef ZenValue (*ZenReflectMethodFn)(void* self, ZenValue args);

void ZenReflect_register_method(const char* type_name, const char* method_name,
                                ZenReflectMethodFn fn);

ZenValue ZenReflect_call(ZenValue receiver, ZenValue name, ZenValue args);
ZenValue ZenReflect_apply(ZenValue fn, ZenValue args);

#endif /* ZEN_REFLECT_H */
