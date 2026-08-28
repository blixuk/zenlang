#ifndef ZEN_TASK_H
#define ZEN_TASK_H

#include "../core/zen_value.h"

typedef struct ZenTask ZenTask;

// Function pointer for task.
// In the bootstrap, we simplify this to a generic function call.
typedef ZenValue (*ZenTaskFunc)(void);

ZenValue ZenTask_spawn(void* func, int arg_count, ZenValue* args);
ZenValue ZenTask_wait(ZenValue task_handle);
void ZenTask_yield();

// Scheduler functions
void ZenTask_scheduler_init();
void ZenTask_scheduler_run();

#endif
