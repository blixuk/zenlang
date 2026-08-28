#include "../bootstrap_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>

/*
 * Dynamic function / closure apply.
 * ZEN_FUNCTION values store ZenClosureData* in as.object.
 * Captures are prepended to user arguments when invoking the C function.
 */
static ZenValue zen_invoke_fn(void* fn, int total, ZenValue* args) {
    switch (total) {
        case 0:
            return ((ZenValue (*)(void))fn)();
        case 1:
            return ((ZenValue (*)(ZenValue))fn)(args[0]);
        case 2:
            return ((ZenValue (*)(ZenValue, ZenValue))fn)(args[0], args[1]);
        case 3:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue))fn)(args[0], args[1], args[2]);
        case 4:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3]);
        case 5:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3], args[4]);
        case 6:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3], args[4], args[5]);
        case 7:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3], args[4], args[5], args[6]);
        case 8:
            return ((ZenValue (*)(ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue, ZenValue))fn)(
                args[0], args[1], args[2], args[3], args[4], args[5], args[6], args[7]);
        default:
            fprintf(stderr, "Error: apply arity %d exceeds limit\n", total);
            return ZenValue_make_nothing();
    }
}

ZenValue ZenValue_call(ZenValue value) {
    return ZenValue_apply(value, 0);
}

ZenValue ZenValue_get_field(ZenValue obj, const char* name) {
    if (!name) return ZenValue_make_nothing();
    if (strcmp(name, "length") == 0) return ZenValue_get_length(obj);
    if (obj.type == ZEN_MAP) {
        return ZenMap_get_value_at_key(obj, ZenValue_make_string(name));
    }
    return ZenValue_make_nothing();
}

ZenValue ZenValue_get_kind(ZenValue obj) {
    /* Prefer explicit map field (structure revival, ECS components, …). */
    if (obj.type == ZEN_MAP) {
        ZenValue k = ZenMap_get_value_at_key(obj, ZenValue_make_string("kind"));
        if (k.type != ZEN_NOTHING && !(k.type == ZEN_STRING && ZenString_get_pointer(k) && ZenString_get_pointer(k)[0] == '\0')) {
            if (k.type != ZEN_NOTHING) {
                /* Only use if key present: check via has */
                if (ZenMap_has_key(obj, ZenValue_make_string("kind")).as.boolean) {
                    return k;
                }
            }
        }
        return ZenValue_make_string("Map");
    }
    switch (obj.type) {
        case ZEN_INTEGER: return ZenValue_make_string("Integer");
        case ZEN_DECIMAL: return ZenValue_make_string("Decimal");
        case ZEN_BOOLEAN: return ZenValue_make_string("Boolean");
        case ZEN_STRING: return ZenValue_make_string("String");
        case ZEN_LIST: return ZenValue_make_string("List");
        case ZEN_SET: return ZenValue_make_string("Set");
        case ZEN_FUNCTION: return ZenValue_make_string("Function");
        case ZEN_OBJECT: return ZenValue_make_string("Object");
        case ZEN_ARENA: return ZenValue_make_string("Arena");
        case ZEN_NOTHING: return ZenValue_make_string("Nothing");
        default: return ZenValue_make_string("Variant");
    }
}

ZenValue ZenValue_apply(ZenValue value, int argc, ...) {
    if (value.type != ZEN_FUNCTION || !value.as.object) {
        /* Legacy: bare func pointer in as.func (pre-closure layout) */
        if (value.type == ZEN_FUNCTION && value.as.func) {
            va_list ap;
            va_start(ap, argc);
            ZenValue user[ZEN_MAX_APPLY_ARGS];
            int n = argc < ZEN_MAX_APPLY_ARGS ? argc : ZEN_MAX_APPLY_ARGS;
            for (int i = 0; i < n; i++) user[i] = va_arg(ap, ZenValue);
            va_end(ap);
            return zen_invoke_fn((void*)value.as.func, n, user);
        }
        fprintf(stderr, "Error: apply on non-function type %d\n", value.type);
        return ZenValue_make_nothing();
    }

    ZenClosureData* c = (ZenClosureData*)value.as.object;
    if (!c->fn) {
        fprintf(stderr, "Error: apply on null function\n");
        return ZenValue_make_nothing();
    }

    ZenValue all[ZEN_MAX_APPLY_ARGS];
    int n_caps = c->n_caps;
    if (n_caps < 0) n_caps = 0;
    if (n_caps > ZEN_MAX_CAPTURES) n_caps = ZEN_MAX_CAPTURES;
    for (int i = 0; i < n_caps; i++) {
        all[i] = c->caps[i];
    }

    va_list ap;
    va_start(ap, argc);
    int n_user = argc;
    if (n_user < 0) n_user = 0;
    if (n_caps + n_user > ZEN_MAX_APPLY_ARGS) {
        n_user = ZEN_MAX_APPLY_ARGS - n_caps;
    }
    for (int i = 0; i < n_user; i++) {
        all[n_caps + i] = va_arg(ap, ZenValue);
    }
    va_end(ap);

    return zen_invoke_fn(c->fn, n_caps + n_user, all);
}

ZenValue ZenValue_get_length(ZenValue self) {
    if (self.type == ZEN_LIST) return ZenList_get_length(self);
    if (self.type == ZEN_STRING) return ZenString_get_length(self);
    if (self.type == ZEN_MAP) return ZenMap_get_length(self);
    if (self.type == ZEN_SET) return ZenValue_make_integer(ZenSet_get_count(self));
    return ZenValue_make_integer(0);
}

ZenValue ZenValue_get_at(ZenValue self, ZenValue index) {
    if (self.type == ZEN_LIST) return ZenList_get_value_at_index(self, index);
    if (self.type == ZEN_STRING) return ZenString_get_character_at_index(self, index);
    if (self.type == ZEN_MAP) return ZenMap_get_value_at_key(self, index);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_set_at(ZenValue self, ZenValue index, ZenValue value) {
    if (self.type == ZEN_LIST) return ZenList_set_value_at_index(self, index, value);
    if (self.type == ZEN_MAP) return ZenMap_set_value_at_key(self, index, value);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_append(ZenValue self, ZenValue value) {
    if (self.type == ZEN_LIST) return ZenList_append_value(self, value);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_pop_dispatch(ZenValue self) {
    if (self.type == ZEN_LIST) return ZenList_pop(self);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_peek(ZenValue self) {
    if (self.type == ZEN_LIST) return ZenList_peek(self);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_remove(ZenValue self, ZenValue value) {
    if (self.type == ZEN_LIST) return ZenList_remove(self, value);
    if (self.type == ZEN_SET) return ZenSet_remove_value(self, value);
    if (self.type == ZEN_MAP) return ZenMap_remove_key(self, value);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_remove_at(ZenValue self, ZenValue index) {
    if (self.type == ZEN_LIST) return ZenList_remove_at_index(self, index);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_contains(ZenValue self, ZenValue value) {
    if (self.type == ZEN_LIST) return ZenList_contains_value(self, value);
    if (self.type == ZEN_MAP) return ZenMap_has_key(self, value);
    if (self.type == ZEN_SET) return ZenSet_contains_value(self, value);
    if (self.type == ZEN_STRING) return ZenValue_make_boolean(ZenString_find_index(self, value).as.integer != -1);
    return ZenValue_make_boolean(false);

}

ZenValue ZenValue_get_keys(ZenValue self) {
    if (self.type == ZEN_MAP) return ZenMap_get_keys(self);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_get_values(ZenValue self) {
    if (self.type == ZEN_MAP) return ZenMap_get_values(self);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_get_items(ZenValue self) {
    if (self.type == ZEN_MAP) return ZenMap_get_items(self);
    return ZenList_make_from_arguments(0);
}

ZenValue ZenValue_get_substring(ZenValue self, ZenValue start, ZenValue end) {
    if (self.type == ZEN_STRING) return ZenString_get_substring(self, start, end);
    if (self.type == ZEN_LIST) return ZenValue_slice(self, start, end);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_slice(ZenValue self, ZenValue start, ZenValue end) {
    if (self.type == ZEN_STRING) return ZenString_get_substring(self, start, end);
    if (self.type != ZEN_LIST || !self.as.list) return ZenList_make_from_arguments(0);
    long long s = (start.type == ZEN_INTEGER) ? start.as.integer : 0;
    long long e = (end.type == ZEN_INTEGER) ? end.as.integer : self.as.list->count;
    if (s < 0) s = 0;
    if (e > self.as.list->count) e = self.as.list->count;
    if (s > e) s = e;
    ZenValue out = ZenList_make_from_arguments(0);
    for (long long i = s; i < e; i++) {
        ZenList_append_value(out, self.as.list->items[i]);
    }
    return out;
}

ZenValue ZenValue_instantiate(ZenValue class_obj, ZenValue data) {
    (void)class_obj;
    /* Native cannot reify class templates; return member map for callers. */
    return data;
}

ZenValue ZenValue_create_object(ZenValue type_name, ZenValue data) {
    (void)type_name;
    return data;
}

ZenValue ZenValue_starts_with(ZenValue self, ZenValue prefix) {
    if (self.type == ZEN_STRING) return ZenString_starts_with(self, prefix);
    return ZenValue_make_boolean(false);
}

ZenValue ZenValue_ends_with(ZenValue self, ZenValue suffix) {
    if (self.type == ZEN_STRING) return ZenString_ends_with(self, suffix);
    return ZenValue_make_boolean(false);
}

ZenValue ZenValue_join(ZenValue self, ZenValue separator) {
    if (self.type == ZEN_LIST) return ZenString_join(self, separator);
    return ZenValue_make_nothing();
}

ZenValue ZenValue_write(ZenValue self, ZenValue value) { return ZenIO_write_value(value); }
ZenValue ZenValue_writeln(ZenValue self, ZenValue value) { return ZenIO_write_line(value); }
ZenValue ZenValue_write_raw(ZenValue self, ZenValue value) { return ZenIO_write_raw(value); }
ZenValue ZenValue_read(ZenValue self) { return ZenIO_read_value(ZenValue_make_nothing()); }
ZenValue ZenValue_read_line(ZenValue self) { return ZenIO_read_line(); }
ZenValue ZenValue_read_exact(ZenValue self, ZenValue count) { return ZenIO_read_exact(count); }

ZenValue ZenValue_info(ZenValue self, ZenValue value) { return ZenIO_write_info(value); }
ZenValue ZenValue_warn(ZenValue self, ZenValue value) { return ZenIO_write_warning(value); }
ZenValue ZenValue_error(ZenValue self, ZenValue value) { return ZenIO_write_error(value); }

/* Parse decimal/integer from a string ZenValue (json, user .to_number()). */
ZenValue ZenValue_to_number(ZenValue self) {
    if (self.type != ZEN_STRING || !self.as.string) {
        return ZenValue_make_nothing();
    }
    const char* s = self.as.string;
    char* end = NULL;
    /* Prefer integer when no decimal point / exponent */
    int has_dot = 0;
    for (const char* p = s; *p; p++) {
        if (*p == '.' || *p == 'e' || *p == 'E') { has_dot = 1; break; }
    }
    if (!has_dot) {
        long long v = strtoll(s, &end, 10);
        if (end != s) return ZenValue_make_integer(v);
    }
    double d = strtod(s, &end);
    if (end == s) return ZenValue_make_nothing();
    return ZenValue_make_decimal(d);
}
