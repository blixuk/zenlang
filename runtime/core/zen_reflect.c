#include "zen_reflect.h"
#include "zen_ops.h"
#include "zen_dispatch.h"
#include "zen_closure.h"
#include "../collections/zen_map.h"
#include "../collections/zen_list.h"
#include "../collections/zen_string.h"
#include <stdio.h>
#include <string.h>
#include <stdbool.h>

/* type_name string -> meta map { fields: List, methods: List } */
static ZenValue g_reflect_registry;

/* Simple pointer -> type name tags for native class instances. */
#define ZEN_REFLECT_TAG_CAP 256
static void* g_tag_ptrs[ZEN_REFLECT_TAG_CAP];
static const char* g_tag_names[ZEN_REFLECT_TAG_CAP];
static int g_tag_count = 0;

/* Method invoker table: (type_name, method_name) -> thunk */
#define ZEN_REFLECT_METHOD_CAP 512
typedef struct {
    const char* type_name;
    const char* method_name;
    ZenReflectMethodFn fn;
} ZenReflectMethodEntry;
static ZenReflectMethodEntry g_methods[ZEN_REFLECT_METHOD_CAP];
static int g_method_count = 0;

void ZenReflect_runtime_init(void) {
    if (g_reflect_registry.type == ZEN_MAP) return;
    g_reflect_registry = ZenMap_make_from_arguments(0);
    g_tag_count = 0;
    g_method_count = 0;
    for (int i = 0; i < ZEN_REFLECT_TAG_CAP; i++) {
        g_tag_ptrs[i] = NULL;
        g_tag_names[i] = NULL;
    }
    for (int i = 0; i < ZEN_REFLECT_METHOD_CAP; i++) {
        g_methods[i].type_name = NULL;
        g_methods[i].method_name = NULL;
        g_methods[i].fn = NULL;
    }
}

void ZenReflect_tag_object(void* ptr, const char* type_name) {
    if (!ptr || !type_name) return;
    ZenReflect_runtime_init();
    for (int i = 0; i < g_tag_count; i++) {
        if (g_tag_ptrs[i] == ptr) {
            g_tag_names[i] = type_name;
            return;
        }
    }
    if (g_tag_count >= ZEN_REFLECT_TAG_CAP) return;
    g_tag_ptrs[g_tag_count] = ptr;
    g_tag_names[g_tag_count] = type_name;
    g_tag_count++;
}

static const char* ZenReflect_object_type_cstr(void* ptr) {
    if (!ptr) return NULL;
    for (int i = 0; i < g_tag_count; i++) {
        if (g_tag_ptrs[i] == ptr) return g_tag_names[i];
    }
    return NULL;
}

void ZenReflect_register_method(const char* type_name, const char* method_name,
                                ZenReflectMethodFn fn) {
    if (!type_name || !method_name || !fn) return;
    ZenReflect_runtime_init();
    for (int i = 0; i < g_method_count; i++) {
        if (g_methods[i].type_name && g_methods[i].method_name &&
            strcmp(g_methods[i].type_name, type_name) == 0 &&
            strcmp(g_methods[i].method_name, method_name) == 0) {
            g_methods[i].fn = fn;
            return;
        }
    }
    if (g_method_count >= ZEN_REFLECT_METHOD_CAP) return;
    g_methods[g_method_count].type_name = type_name;
    g_methods[g_method_count].method_name = method_name;
    g_methods[g_method_count].fn = fn;
    g_method_count++;
}

static ZenReflectMethodFn find_method(const char* type_name, const char* method_name) {
    if (!type_name || !method_name) return NULL;
    for (int i = 0; i < g_method_count; i++) {
        if (g_methods[i].type_name && g_methods[i].method_name &&
            strcmp(g_methods[i].type_name, type_name) == 0 &&
            strcmp(g_methods[i].method_name, method_name) == 0) {
            return g_methods[i].fn;
        }
    }
    return NULL;
}

static ZenValue empty_list(void) {
    return ZenList_make_from_arguments(0);
}

void ZenReflect_register_type(ZenValue type_name, ZenValue fields, ZenValue methods) {
    if (g_reflect_registry.type != ZEN_MAP) {
        ZenReflect_runtime_init();
    }
    if (type_name.type != ZEN_STRING) return;
    ZenValue meta = ZenMap_make_from_arguments(0);
    ZenMap_set_value_at_key(meta, ZenValue_make_string("fields"),
                            fields.type == ZEN_LIST ? fields : empty_list());
    ZenMap_set_value_at_key(meta, ZenValue_make_string("methods"),
                            methods.type == ZEN_LIST ? methods : empty_list());
    ZenMap_set_value_at_key(g_reflect_registry, type_name, meta);
}

static ZenValue meta_for_type_name(ZenValue type_name) {
    if (g_reflect_registry.type != ZEN_MAP) return ZenValue_make_nothing();
    if (type_name.type != ZEN_STRING) return ZenValue_make_nothing();
    if (!ZenMap_has_key(g_reflect_registry, type_name).as.boolean) {
        return ZenValue_make_nothing();
    }
    return ZenMap_get_value_at_key(g_reflect_registry, type_name);
}

static ZenValue type_name_of_value(ZenValue value) {
    /* Prefer map field `kind` when registered as a reflectable type name. */
    if (value.type == ZEN_MAP) {
        ZenValue k = ZenValue_make_string("kind");
        if (ZenMap_has_key(value, k).as.boolean) {
            ZenValue kind = ZenMap_get_value_at_key(value, k);
            if (kind.type == ZEN_STRING) {
                ZenValue meta = meta_for_type_name(kind);
                if (meta.type != ZEN_NOTHING) {
                    return kind;
                }
            }
        }
    }
    if (value.type == ZEN_OBJECT && value.as.object) {
        const char* tn = ZenReflect_object_type_cstr(value.as.object);
        if (tn) return ZenValue_make_string(tn);
    }
    return ZenValue_get_kind(value);
}

ZenValue ZenReflect_type_name(ZenValue value) {
    return type_name_of_value(value);
}

ZenValue ZenReflect_is_reflectable(ZenValue value) {
    ZenValue tn = type_name_of_value(value);
    ZenValue meta = meta_for_type_name(tn);
    return ZenValue_make_boolean(meta.type != ZEN_NOTHING);
}

static ZenValue meta_list(ZenValue meta, const char* key) {
    if (meta.type != ZEN_MAP) return empty_list();
    ZenValue k = ZenValue_make_string(key);
    if (!ZenMap_has_key(meta, k).as.boolean) return empty_list();
    ZenValue lst = ZenMap_get_value_at_key(meta, k);
    if (lst.type != ZEN_LIST) return empty_list();
    return lst;
}

ZenValue ZenReflect_fields(ZenValue value) {
    ZenValue tn = type_name_of_value(value);
    ZenValue meta = meta_for_type_name(tn);
    if (meta.type != ZEN_NOTHING) {
        return meta_list(meta, "fields");
    }
    /* Non-reflectable maps: all keys (P1 behavior). */
    if (value.type == ZEN_MAP) {
        return ZenMap_get_keys(value);
    }
    return empty_list();
}

ZenValue ZenReflect_methods(ZenValue value) {
    ZenValue tn = type_name_of_value(value);
    ZenValue meta = meta_for_type_name(tn);
    if (meta.type != ZEN_NOTHING) {
        return meta_list(meta, "methods");
    }
    return empty_list();
}

static bool list_contains_string(ZenValue list, ZenValue name) {
    if (list.type != ZEN_LIST || !list.as.list) return false;
    if (name.type != ZEN_STRING) return false;
    for (int i = 0; i < list.as.list->count; i++) {
        ZenValue el = list.as.list->items[i];
        if (el.type == ZEN_STRING && ZenValue_equal(el, name).as.boolean) {
            return true;
        }
    }
    return false;
}

ZenValue ZenReflect_has_field(ZenValue value, ZenValue name) {
    ZenValue fields = ZenReflect_fields(value);
    if (list_contains_string(fields, name)) {
        return ZenValue_make_boolean(true);
    }
    /* Fall back: map key present */
    if (value.type == ZEN_MAP) {
        return ZenMap_has_key(value, name);
    }
    return ZenValue_make_boolean(false);
}

ZenValue ZenReflect_has_method(ZenValue value, ZenValue name) {
    ZenValue methods = ZenReflect_methods(value);
    return ZenValue_make_boolean(list_contains_string(methods, name));
}

ZenValue ZenReflect_field(ZenValue value, ZenValue name) {
    if (value.type == ZEN_MAP) {
        if (ZenMap_has_key(value, name).as.boolean) {
            return ZenMap_get_value_at_key(value, name);
        }
    }
    return ZenValue_make_nothing();
}

ZenValue ZenReflect_set_field(ZenValue value, ZenValue name, ZenValue new_value) {
    if (value.type == ZEN_MAP) {
        return ZenMap_set_value_at_key(value, name, new_value);
    }
    return value;
}

static ZenValue apply_fn_with_list(ZenValue fn, ZenValue args) {
    if (args.type != ZEN_LIST || !args.as.list) {
        return ZenValue_apply(fn, 0);
    }
    int n = args.as.list->count;
    if (n < 0) n = 0;
    if (n > ZEN_MAX_APPLY_ARGS) n = ZEN_MAX_APPLY_ARGS;
    /* Unroll small arities for ZenValue_apply varargs */
    ZenValue* items = args.as.list->items;
    switch (n) {
        case 0: return ZenValue_apply(fn, 0);
        case 1: return ZenValue_apply(fn, 1, items[0]);
        case 2: return ZenValue_apply(fn, 2, items[0], items[1]);
        case 3: return ZenValue_apply(fn, 3, items[0], items[1], items[2]);
        case 4: return ZenValue_apply(fn, 4, items[0], items[1], items[2], items[3]);
        case 5: return ZenValue_apply(fn, 5, items[0], items[1], items[2], items[3], items[4]);
        case 6: return ZenValue_apply(fn, 6, items[0], items[1], items[2], items[3], items[4], items[5]);
        default: {
            /* 7..12 */
            return ZenValue_apply(fn, n,
                n > 0 ? items[0] : ZenValue_make_nothing(),
                n > 1 ? items[1] : ZenValue_make_nothing(),
                n > 2 ? items[2] : ZenValue_make_nothing(),
                n > 3 ? items[3] : ZenValue_make_nothing(),
                n > 4 ? items[4] : ZenValue_make_nothing(),
                n > 5 ? items[5] : ZenValue_make_nothing(),
                n > 6 ? items[6] : ZenValue_make_nothing(),
                n > 7 ? items[7] : ZenValue_make_nothing(),
                n > 8 ? items[8] : ZenValue_make_nothing(),
                n > 9 ? items[9] : ZenValue_make_nothing(),
                n > 10 ? items[10] : ZenValue_make_nothing(),
                n > 11 ? items[11] : ZenValue_make_nothing());
        }
    }
}

ZenValue ZenReflect_apply(ZenValue fn, ZenValue args) {
    return apply_fn_with_list(fn, args);
}

ZenValue ZenReflect_call(ZenValue receiver, ZenValue name, ZenValue args) {
    /* Map plugin table or tagged class instance */
    if (receiver.type == ZEN_MAP && name.type == ZEN_STRING) {
        if (ZenMap_has_key(receiver, name).as.boolean) {
            ZenValue fn = ZenMap_get_value_at_key(receiver, name);
            if (fn.type == ZEN_FUNCTION) {
                return apply_fn_with_list(fn, args);
            }
            fprintf(stderr, "reflect.call: map entry is not a function\n");
            return ZenValue_make_nothing();
        }
        ZenValue tn = type_name_of_value(receiver);
        const char* tn_str = ZenString_get_pointer(tn);
        const char* mn = ZenString_get_pointer(name);
        if (tn_str && mn) {
            ZenReflectMethodFn mfn = find_method(tn_str, mn);
            if (mfn) {
                ZenValue arg_list = args;
                if (arg_list.type != ZEN_LIST) {
                    arg_list = empty_list();
                }
                return mfn((void*)receiver.as.map, arg_list);
            }
        }
        fprintf(stderr, "reflect.call: map has no key '%s'\n",
                ZenString_get_pointer(name) ? ZenString_get_pointer(name) : "?");
        return ZenValue_make_nothing();
    }

    /* Tagged class instances: method tables registered for `is reflectable` types */
    if (receiver.type == ZEN_OBJECT && receiver.as.object && name.type == ZEN_STRING) {
        const char* tn = ZenReflect_object_type_cstr(receiver.as.object);
        const char* mn = ZenString_get_pointer(name);
        if (!tn) {
            fprintf(stderr, "reflect.call: object has no reflect type tag\n");
            return ZenValue_make_nothing();
        }
        if (!mn) {
            fprintf(stderr, "reflect.call: invalid method name\n");
            return ZenValue_make_nothing();
        }
        ZenReflectMethodFn mfn = find_method(tn, mn);
        if (!mfn) {
            fprintf(stderr, "reflect.call: no method '%s' on type '%s'\n", mn, tn);
            return ZenValue_make_nothing();
        }
        ZenValue arg_list = args;
        if (arg_list.type != ZEN_LIST) {
            arg_list = empty_list();
        }
        return mfn(receiver.as.object, arg_list);
    }

    fprintf(stderr, "reflect.call: unsupported receiver type %d\n", receiver.type);
    return ZenValue_make_nothing();
}
