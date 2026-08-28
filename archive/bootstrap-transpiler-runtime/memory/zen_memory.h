#ifndef ZEN_MEMORY_H
#define ZEN_MEMORY_H

#include <stddef.h>
#include <setjmp.h>
#include "../core/zen_value.h"

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

extern ZenValue ZenException_last;

void ZenException_push_context(ZenExceptionContext *context);
void ZenException_pop_context(void);
void ZenException_raise(ZenValue value);

void ZenRuntime_defer_push(void (*func)(void*), void *data);
void ZenRuntime_defer_run_to(int depth);
int ZenRuntime_get_defer_depth(void);

// Arena management (Internal)
ZenArena* ZenArena_create(size_t size);
void* ZenArena_allocate(ZenArena* arena, size_t size);
void ZenArena_reset(ZenArena* arena);
void ZenArena_free(ZenArena* arena);
void ZenArena_push(ZenArena* arena);
void ZenArena_pop(void);
void* ZenRuntime_allocate(size_t size);

/* Memory Module API */
ZenValue ZenMemory_create_arena(ZenValue size);
ZenValue ZenMemory_free_arena(ZenValue arena);
ZenValue ZenMemory_reset_arena(ZenValue arena);
ZenValue ZenMemory_push_arena(ZenValue arena);
ZenValue ZenMemory_pop_arena(void);

#endif // ZEN_MEMORY_H
