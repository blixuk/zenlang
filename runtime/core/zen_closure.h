#ifndef ZEN_CLOSURE_H
#define ZEN_CLOSURE_H

#include "zen_value.h"

/* Max captured outer locals per lambda (by-value snapshot). */
#define ZEN_MAX_CAPTURES 8
/* Max total C arguments when applying (captures + user args). */
#define ZEN_MAX_APPLY_ARGS 12

/*
 * Closure / function value payload.
 * Stored in ZenValue.as.object when type == ZEN_FUNCTION.
 * Bare functions have n_caps == 0; true closures snapshot outer locals.
 *
 * Generated lambda C signatures always receive captures first, then user args:
 *   ZenValue lambda(ZenValue cap0, ..., ZenValue capN, ZenValue arg0, ...)
 */
typedef struct ZenClosureData {
    ZenHeapHeader header;     /* 8 bytes: intrusive ARC / Sentinel header */
    void* fn;       /* C function pointer (variable arity of ZenValue args) */
    int n_caps;     /* number of captured values */
    int arity;      /* number of user parameters expected (-1 = unknown) */
    ZenValue caps[ZEN_MAX_CAPTURES];
} ZenClosureData;

/* Wrap a bare C function (no captures). arity may be -1. */
ZenValue ZenValue_from_function(ZenValue (*f)(void));

/* Build a closure: fn receives (caps..., user_args...). */
ZenValue ZenValue_from_closure(void* fn, int arity, int n_caps, ...);

void ZenClosure_destroy(ZenClosureData* c);

/* Accessors used by apply. */
static inline int ZenClosure_is(ZenValue v) {
    return v.type == ZEN_FUNCTION && v.as.object != NULL;
}

static inline ZenClosureData* ZenClosure_data(ZenValue v) {
    return (ZenClosureData*)v.as.object;
}

#endif /* ZEN_CLOSURE_H */
