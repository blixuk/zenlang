#include "zen_task.h"
#include <pthread.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdio.h>
#include <sched.h>

// In the bootstrap, we use a simple pthread-based implementation.
// True fibers would manage their own stacks, but this is sufficient for a 0.2.0 bootstrap.

typedef struct ZenTask {
    int kind; // Internal object kind for validation
    pthread_t thread;
    ZenValue (*func)(ZenValue*);
    int arg_count;
    ZenValue* args;
    ZenValue result;
    bool completed;
} ZenTask;

#define ZEN_TASK_KIND 0x5441534B // 'TASK'

static void* task_entry(void* data) {
    ZenTask* task = (ZenTask*)data;
    task->result = task->func(task->args);
    task->completed = true;
    return NULL;
}

ZenValue ZenTask_spawn(void* func, int arg_count, ZenValue* args) {
    ZenTask* task = malloc(sizeof(ZenTask));
    task->kind = ZEN_TASK_KIND;
    task->func = (ZenValue (*)(ZenValue*))func;
    task->arg_count = arg_count;
    
    if (arg_count > 0) {
        task->args = malloc(sizeof(ZenValue) * arg_count);
        for(int i = 0; i < arg_count; i++) {
            task->args[i] = args[i];
        }
    } else {
        task->args = NULL;
    }
    
    task->completed = false;
    task->result = ZEN_NOTHING_VAL;
    
    if (pthread_create(&task->thread, NULL, task_entry, task) != 0) {
        // Fallback for failed thread creation
        fprintf(stderr, "Error: Failed to spawn task thread\n");
        free(task->args);
        free(task);
        return ZEN_NOTHING_VAL;
    }
    
    return ZenValue_from_object(task);
}

ZenValue ZenTask_wait(ZenValue task_handle) {
    if (task_handle.type != ZEN_OBJECT || !task_handle.as.object) {
        return ZEN_NOTHING_VAL;
    }
    
    ZenTask* task = (ZenTask*)task_handle.as.object;
    if (task->kind != ZEN_TASK_KIND) {
        return ZEN_NOTHING_VAL;
    }
    
    pthread_join(task->thread, NULL);
    
    ZenValue res = task->result;
    
    // Cleanup
    free(task->args);
    free(task);
    
    return res;
}

void ZenTask_yield() {
    sched_yield();
}

void ZenTask_scheduler_init() {
    // No-op for pthread implementation
}

void ZenTask_scheduler_run() {
    // No-op for pthread implementation
}
