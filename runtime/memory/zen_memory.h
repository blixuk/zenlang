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
ZenArena* ZenArena_current(void);
int ZenArena_stack_depth(void);
void ZenArena_suspend(void);
void ZenArena_resume(void);

/* Process heap when no arena pushed; current arena when pushed (opt-in). */
void* ZenRuntime_allocate(size_t size);

/* Memory Module API */
ZenValue ZenMemory_create_arena(ZenValue size);
ZenValue ZenMemory_free_arena(ZenValue arena);
ZenValue ZenMemory_reset_arena(ZenValue arena);
ZenValue ZenMemory_push_arena(ZenValue arena);
ZenValue ZenMemory_pop_arena(void);
ZenValue ZenMemory_arena_depth(void);
ZenValue ZenMemory_using_arena(void);
ZenValue ZenMemory_arena_allocated(ZenValue arena_value);
ZenValue ZenMemory_arena_capacity(ZenValue arena_value);
ZenValue ZenMemory_arena_chunks(ZenValue arena_value);
ZenValue ZenMemory_arena_stats(ZenValue arena_value);

#endif // ZEN_MEMORY_H
