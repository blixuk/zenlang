#include "zen_value.h"
#include "zen_closure.h"
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

ZenValue ZenValue_make_string(const char* s) {
    ZenValue z;
    z.type = ZEN_STRING;
    if (s == NULL) {
        z.as.string = NULL;
    } else {
        size_t len = strlen(s);
        char* res = malloc(len + 1);
        strcpy(res, s);
        z.as.string = res;
    }
    return z;
}

ZenValue ZenValue_make_nothing(void) {
    ZenValue z;
    z.type = ZEN_NOTHING;
    return z;
}

ZenValue ZenValue_from_list(struct ZenList* l) {
    ZenValue z;
    z.type = ZEN_LIST;
    z.as.list = l;
    return z;
}

ZenValue ZenValue_from_object(void* obj) {
    ZenValue v;
    v.type = ZEN_OBJECT;
    v.as.object = obj;
#ifdef ZEN_RUNTIME_DEBUG
    printf("DEBUG: Created ZEN_OBJECT: %p\n", obj);
#endif
    return v;
}

ZenValue ZenValue_from_map(struct ZenMap* m) {
    ZenValue z;
    z.type = ZEN_MAP;
    z.as.map = m;
    return z;
}

ZenValue ZenValue_from_arena(ZenArena* a) {
    ZenValue z;
    z.type = ZEN_ARENA;
    z.as.arena = a;
    return z;
}

ZenValue ZenValue_make_error(ZenValue message) {
    ZenValue v = {ZEN_ERROR, {0}};
    if (message.type == ZEN_STRING) {
        v.as.string = strdup(message.as.string);
    } else {
        v.as.string = "Unknown Error";
    }
    return v;
}

/* Bare function: zero captures. Payload lives in as.object (ZenClosureData). */
ZenValue ZenValue_from_function(ZenValue (*f)(void)) {
    ZenClosureData* c = (ZenClosureData*)calloc(1, sizeof(ZenClosureData));
    if (!c) {
        ZenValue z;
        z.type = ZEN_NOTHING;
        return z;
    }
    c->fn = (void*)f;
    c->n_caps = 0;
    c->arity = -1;
    ZenValue z;
    z.type = ZEN_FUNCTION;
    z.as.object = c;
    return z;
}

/* Closure with by-value captures. fn is called as (caps..., user_args...). */
ZenValue ZenValue_from_closure(void* fn, int arity, int n_caps, ...) {
    if (n_caps < 0) n_caps = 0;
    if (n_caps > ZEN_MAX_CAPTURES) n_caps = ZEN_MAX_CAPTURES;
    ZenClosureData* c = (ZenClosureData*)calloc(1, sizeof(ZenClosureData));
    if (!c) {
        ZenValue z;
        z.type = ZEN_NOTHING;
        return z;
    }
    c->fn = fn;
    c->n_caps = n_caps;
    c->arity = arity;
    va_list ap;
    va_start(ap, n_caps);
    for (int i = 0; i < n_caps; i++) {
        c->caps[i] = va_arg(ap, ZenValue);
    }
    va_end(ap);
    ZenValue z;
    z.type = ZEN_FUNCTION;
    z.as.object = c;
    return z;
}
