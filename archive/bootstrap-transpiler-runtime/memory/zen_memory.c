#include "../bootstrap_runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

/* Exception and Defer handling */

ZenValue ZenException_last;
#define MAX_EXCEPTIONS 100
static ZenExceptionContext *ZenException_stack[MAX_EXCEPTIONS];
static int ZenException_stack_pointer = 0;
static ZenDeferNode *ZenRuntime_defer_stack = NULL;
static int ZenRuntime_current_defer_depth = 0;

void ZenException_push_context(ZenExceptionContext *context) {
    if (ZenException_stack_pointer < MAX_EXCEPTIONS) {
        ZenException_stack[ZenException_stack_pointer++] = context;
    }
}

void ZenException_pop_context(void) {
    if (ZenException_stack_pointer > 0) {
        ZenException_stack_pointer--;
    }
}

void ZenException_raise(ZenValue value) {
    ZenException_last = value;
    if (ZenException_stack_pointer > 0) {
        ZenExceptionContext* context = ZenException_stack[ZenException_stack_pointer - 1];
        ZenRuntime_defer_run_to(context->defer_depth);
        longjmp(context->buf, 1);
    } else {
        ZenValue s_v = ZenValue_to_string(value);
        fprintf(stderr, "Unhandled exception: %s\n", s_v.as.string);
        exit(1);
    }
}

void ZenRuntime_defer_push(void (*func)(void*), void *data) {
    ZenDeferNode *node = malloc(sizeof(ZenDeferNode));
    node->func = func; 
    node->data = data; 
    node->next = ZenRuntime_defer_stack;
    ZenRuntime_defer_stack = node; 
    ZenRuntime_current_defer_depth++;
}

void ZenRuntime_defer_run_to(int target_depth) {
    while (ZenRuntime_current_defer_depth > target_depth && ZenRuntime_defer_stack != NULL) {
        ZenDeferNode *node = ZenRuntime_defer_stack;
        ZenRuntime_defer_stack = node->next; 
        ZenRuntime_current_defer_depth--;
        node->func(node->data); 
        free(node);
    }
}

int ZenRuntime_get_defer_depth(void) { 
    return ZenRuntime_current_defer_depth; 
}

/* Arena stack */
#define MAX_ARENAS 128
static ZenArena* ZenArena_stack[MAX_ARENAS];
static int ZenArena_stack_pointer = 0;

void ZenArena_push(ZenArena* arena) {
    if (ZenArena_stack_pointer < MAX_ARENAS) {
        ZenArena_stack[ZenArena_stack_pointer++] = arena;
    }
}

void ZenArena_pop(void) {
    if (ZenArena_stack_pointer > 0) {
        ZenArena_stack_pointer--;
    }
}

void* ZenRuntime_allocate(size_t size) {
    // TEMPORARY FIX: Disable arena stack allocation for objects
    // because returning an object from a local block causes use-after-free 
    // when the block's arena is freed.
    return malloc(size);
}

/* Arena management */

struct ZenArena {
    void* buffer;
    size_t size;
    size_t offset;
};

ZenArena* ZenArena_create(size_t size) {
    if (size == 0) size = 1024 * 1024; // Default 1MB
    ZenArena* arena = (ZenArena*)malloc(sizeof(ZenArena));
    arena->buffer = malloc(size);
    arena->size = size;
    arena->offset = 0;
    return arena;
}

void* ZenArena_allocate(ZenArena* arena, size_t size) {
    if (!arena) return malloc(size);
    // Align to 8 bytes for safety
    size = (size + 7) & ~7;
    if (arena->offset + size > arena->size) {
        // Fallback to malloc if arena is full for the bootstrap compiler
        return malloc(size);
    }
    void* ptr = (char*)arena->buffer + arena->offset;
    arena->offset += size;
    return ptr;
}

void ZenArena_reset(ZenArena* arena) {
    if (arena) arena->offset = 0;
}

void ZenArena_free(ZenArena* arena) {
    if (arena) {
        if (arena->buffer) {
            memset(arena->buffer, 0xCC, arena->size);
            free(arena->buffer);
        }
        free(arena);
    }
}

/* Memory Module Functions */

ZenValue ZenMemory_create_arena(ZenValue size_value) {
    size_t s = 0;
    if (size_value.type == ZEN_INTEGER) s = (size_t)size_value.as.integer;
    return ZenValue_from_arena(ZenArena_create(s));
}

ZenValue ZenMemory_free_arena(ZenValue arena_value) {
    if (arena_value.type == ZEN_ARENA) {
        ZenArena_free(arena_value.as.arena);
    }
    return ZenValue_make_nothing();
}

ZenValue ZenMemory_reset_arena(ZenValue arena_value) {
    if (arena_value.type == ZEN_ARENA) {
        ZenArena_reset(arena_value.as.arena);
    }
    return ZenValue_make_nothing();
}

ZenValue ZenMemory_push_arena(ZenValue arena_value) {
    if (arena_value.type == ZEN_ARENA) {
        ZenArena_push(arena_value.as.arena);
    }
    return ZenValue_make_nothing();
}

ZenValue ZenMemory_pop_arena(void) {
    ZenArena_pop();
    return ZenValue_make_nothing();
}
