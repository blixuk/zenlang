#ifndef ZEN_TASK_H
#define ZEN_TASK_H

#include "../core/zen_value.h"
#include <pthread.h>
#include <stdbool.h>

typedef enum {
    TASK_PENDING,
    TASK_RUNNING,
    TASK_COMPLETED,
    TASK_FAILED,
    TASK_CANCELLED
} ZenTaskState;

typedef struct ZenTaskHandle {
    ZenHeapHeader header;       /* 8 bytes: Intrusive ARC / Sentinel header */
    ZenValue callable;          /* The closure or function to execute */
    ZenValue argument;          /* The frozen arguments passed to the task */
    ZenValue result;            /* The frozen return value (or Error object) */
    
    ZenTaskState state;
    pthread_mutex_t lock;
    pthread_cond_t cond;
    
    struct ZenTaskHandle* next; /* Intrusive linked-list pointer for the worker queue */
} ZenTaskHandle;

/* Engine Initialization & Teardown */
void ZenTaskEngine_init(void);
void ZenTaskEngine_shutdown(void);

/* Task API */
ZenTaskHandle* (ZenTask_spawn)(ZenValue callable, ZenValue argument);
ZenValue ZenTask_spawn_val(ZenValue callable, ZenValue argument);
ZenValue ZenTask_spawn_legacy(void* func, int arg_count, ZenValue* args);

ZenValue (ZenTask_wait)(ZenTaskHandle* task);
ZenValue ZenTask_wait_value(ZenValue task_val);

void ZenTask_cancel(ZenTaskHandle* task);
bool ZenTask_is_cancelled(ZenTaskHandle* task);
ZenTaskState ZenTask_get_state(ZenTaskHandle* task);
void ZenTask_destroy(ZenTaskHandle* task);

/* Legacy Scheduler API */
void ZenTask_yield(void);
void ZenTask_scheduler_init(void);
void ZenTask_scheduler_run(void);

static inline ZenValue ZenValue_from_task(ZenTaskHandle* task) {
    ZenValue v;
    v.type = ZEN_TASK;
    v.as.object = (void*)task;
    return v;
}

static inline ZenTaskHandle* ZenValue_to_task(ZenValue v) {
    if (v.type != ZEN_TASK) return NULL;
    return (ZenTaskHandle*)v.as.object;
}

#define _GET_SPAWN_MACRO(_1, _2, _3, NAME, ...) NAME
#define ZenTask_spawn(...) _GET_SPAWN_MACRO(__VA_ARGS__, ZenTask_spawn_legacy, ZenTask_spawn)(__VA_ARGS__)

#define ZenTask_wait(x) _Generic((x), \
    ZenValue: ZenTask_wait_value, \
    default: (ZenTask_wait) \
)(x)

#endif /* ZEN_TASK_H */
