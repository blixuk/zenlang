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

/*
 * Two arena stacks (do not share):
 *
 * 1) Frame stack — bootstrap SMIR function/block regions (ZenArena_push/pop).
 *    RegionExit must not undo user opt-in pushes.
 * 2) User stack — zen.memory push_arena / pop_arena (opt-in bulk reclaim).
 *
 * ZenRuntime_allocate preference: user top → frame top → process malloc.
 * Automatic path (both empty): process malloc; no free required for ordinary values.
 */
#define MAX_ARENAS 128
static ZenArena* ZenFrame_stack[MAX_ARENAS];
static int ZenFrame_sp = 0;
static ZenArena* ZenUser_stack[MAX_ARENAS];
static int ZenUser_sp = 0;

typedef struct ZenArenaChunk {
    struct ZenArenaChunk* next;
    size_t size;
    size_t offset;
} ZenArenaChunk;

struct ZenArena {
    ZenArenaChunk* head;
    ZenArenaChunk* current;
    size_t default_chunk_size;
};

/* --- Frame stack (SMIR) --- */

void ZenArena_push(ZenArena* arena) {
    if (arena && ZenFrame_sp < MAX_ARENAS) {
        ZenFrame_stack[ZenFrame_sp++] = arena;
    }
}

void ZenArena_pop(void) {
    if (ZenFrame_sp > 0) {
        ZenFrame_sp--;
    }
}

static ZenArena* ZenFrame_current(void) {
    if (ZenFrame_sp <= 0) return NULL;
    return ZenFrame_stack[ZenFrame_sp - 1];
}

/* --- User stack (stdlib opt-in) --- */

static void ZenUser_push(ZenArena* arena) {
    if (arena && ZenUser_sp < MAX_ARENAS) {
        ZenUser_stack[ZenUser_sp++] = arena;
    }
}

static void ZenUser_pop(void) {
    if (ZenUser_sp > 0) {
        ZenUser_sp--;
    }
}

static ZenArena* ZenUser_current(void) {
    if (ZenUser_sp <= 0) return NULL;
    return ZenUser_stack[ZenUser_sp - 1];
}

ZenArena* ZenArena_current(void) {
    return ZenUser_current();
}

int ZenArena_stack_depth(void) {
    /* User-visible depth = opt-in pushes only (stable under SMIR frames). */
    return ZenUser_sp;
}

static void ZenUser_remove(ZenArena* arena) {
    int i, j;
    for (i = ZenUser_sp - 1; i >= 0; i--) {
        if (ZenUser_stack[i] == arena) {
            for (j = i; j < ZenUser_sp - 1; j++) {
                ZenUser_stack[j] = ZenUser_stack[j + 1];
            }
            ZenUser_sp--;
        }
    }
}

static void ZenFrame_remove(ZenArena* arena) {
    int i, j;
    for (i = ZenFrame_sp - 1; i >= 0; i--) {
        if (ZenFrame_stack[i] == arena) {
            for (j = i; j < ZenFrame_sp - 1; j++) {
                ZenFrame_stack[j] = ZenFrame_stack[j + 1];
            }
            ZenFrame_sp--;
        }
    }
}

void* ZenRuntime_allocate(size_t size) {
    ZenArena* cur = ZenArena_current();
    if (cur) {
        return ZenArena_allocate(cur, size);
    }
    return malloc(size);
}

ZenArena* ZenArena_create(size_t size) {
    if (size == 0) size = 1024 * 1024;
    ZenArena* arena = (ZenArena*)malloc(sizeof(ZenArena));
    if (!arena) return NULL;

    ZenArenaChunk* chunk = (ZenArenaChunk*)malloc(sizeof(ZenArenaChunk) + size);
    if (!chunk) {
        free(arena);
        return NULL;
    }
    chunk->next = NULL;
    chunk->size = size;
    chunk->offset = 0;

    arena->head = chunk;
    arena->current = chunk;
    arena->default_chunk_size = size;
    return arena;
}

void* ZenArena_allocate(ZenArena* arena, size_t size) {
    if (!arena) return malloc(size);
    size = (size + 7) & ~7;
    ZenArenaChunk* cur = arena->current;
    if (!cur || cur->offset + size > cur->size) {
        size_t chunk_size = arena->default_chunk_size;
        if (size > chunk_size) chunk_size = size;
        ZenArenaChunk* next = (ZenArenaChunk*)malloc(sizeof(ZenArenaChunk) + chunk_size);
        if (!next) return malloc(size);
        next->next = NULL;
        next->size = chunk_size;
        next->offset = 0;
        if (cur) cur->next = next;
        if (!arena->head) arena->head = next;
        arena->current = next;
        cur = next;
    }
    char* buf = (char*)(cur + 1);
    void* ptr = (void*)(buf + cur->offset);
    cur->offset += size;
    return ptr;
}

void ZenArena_reset(ZenArena* arena) {
    if (!arena) return;
    for (ZenArenaChunk* ch = arena->head; ch; ch = ch->next) {
        ch->offset = 0;
    }
    arena->current = arena->head;
}

void ZenArena_free(ZenArena* arena) {
    if (!arena) return;
    ZenUser_remove(arena);
    ZenFrame_remove(arena);
    ZenArenaChunk* ch = arena->head;
    while (ch) {
        ZenArenaChunk* next = ch->next;
        free(ch);
        ch = next;
    }
    free(arena);
}

/* Memory Module Functions (user stack) */

ZenValue ZenMemory_create_arena(ZenValue size_value) {
    size_t s = 0;
    if (size_value.type == ZEN_INTEGER) s = (size_t)size_value.as.integer;
    ZenArena* a = ZenArena_create(s);
    if (!a) return ZenValue_make_nothing();
    return ZenValue_from_arena(a);
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
    if (arena_value.type == ZEN_ARENA && arena_value.as.arena) {
        ZenUser_push(arena_value.as.arena);
    }
    return ZenValue_make_nothing();
}

ZenValue ZenMemory_pop_arena(void) {
    ZenUser_pop();
    return ZenValue_make_nothing();
}

ZenValue ZenMemory_arena_depth(void) {
    return ZenValue_make_integer((long long)ZenUser_sp);
}

ZenValue ZenMemory_using_arena(void) {
    return ZenValue_make_boolean(ZenUser_sp > 0);
}

static ZenArena* resolve_target_arena(ZenValue arena_value) {
    if (arena_value.type == ZEN_ARENA && arena_value.as.arena) {
        return arena_value.as.arena;
    }
    return ZenArena_current();
}

ZenValue ZenMemory_arena_allocated(ZenValue arena_value) {
    ZenArena* a = resolve_target_arena(arena_value);
    if (!a) return ZenValue_make_integer(0LL);
    size_t total = 0;
    for (ZenArenaChunk* ch = a->head; ch; ch = ch->next) {
        total += ch->offset;
    }
    return ZenValue_make_integer((long long)total);
}

ZenValue ZenMemory_arena_capacity(ZenValue arena_value) {
    ZenArena* a = resolve_target_arena(arena_value);
    if (!a) return ZenValue_make_integer(0LL);
    size_t total = 0;
    for (ZenArenaChunk* ch = a->head; ch; ch = ch->next) {
        total += ch->size;
    }
    return ZenValue_make_integer((long long)total);
}

ZenValue ZenMemory_arena_chunks(ZenValue arena_value) {
    ZenArena* a = resolve_target_arena(arena_value);
    if (!a) return ZenValue_make_integer(0LL);
    int count = 0;
    for (ZenArenaChunk* ch = a->head; ch; ch = ch->next) {
        count++;
    }
    return ZenValue_make_integer((long long)count);
}

ZenValue ZenMemory_arena_stats(ZenValue arena_value) {
    ZenArena* a = resolve_target_arena(arena_value);
    size_t allocated = 0;
    size_t capacity = 0;
    int chunks = 0;
    if (a) {
        for (ZenArenaChunk* ch = a->head; ch; ch = ch->next) {
            allocated += ch->offset;
            capacity += ch->size;
            chunks++;
        }
    }
    ZenValue map = ZenMap_make_from_arguments(0);
    ZenMap_set_value_at_key(map, ZenValue_make_string("allocated"), ZenValue_make_integer((long long)allocated));
    ZenMap_set_value_at_key(map, ZenValue_make_string("capacity"), ZenValue_make_integer((long long)capacity));
    ZenMap_set_value_at_key(map, ZenValue_make_string("chunks"), ZenValue_make_integer((long long)chunks));
    return map;
}
