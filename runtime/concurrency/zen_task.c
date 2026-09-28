#include "zen_task.h"
#include "../memory/zen_memory.h"
#include "../core/zen_dispatch.h"
#include "../core/zen_closure.h"
#include "../collections/zen_list.h"
#include <stdlib.h>
#include <unistd.h>
#include <sched.h>

/* =========================================================================
 * Global Worker Pool State
 * ========================================================================= */
typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t not_empty;
    ZenTaskHandle* head;
    ZenTaskHandle* tail;
    pthread_t* workers;
    int worker_count;
    bool shutdown;
} ZenWorkerPool;

typedef struct {
    pthread_mutex_t lock;
    pthread_cond_t not_empty;
    ZenTaskHandle* head;
    ZenTaskHandle* tail;
    pthread_t* workers;
    int worker_count;
    int idle_count;
    int max_workers;
    bool shutdown;
} ZenBlockingPool;

static ZenWorkerPool pool = {0};
static ZenBlockingPool blocking_pool = {0};
static bool engine_initialized = false;
static __thread ZenTaskHandle* current_worker_task = NULL;

ZenTaskHandle* ZenTask_current(void) {
    return current_worker_task;
}

/* =========================================================================
 * The Frozen Handoff Boundary (Reused from Channels)
 * ========================================================================= */
static ZenValue zen_task_prepare_handoff(ZenValue val) {
    if (!ZenValue_is_heap_pointer(val)) return val;
    if (val.type == ZEN_CHANNEL || val.type == ZEN_TASK) {
        ZenValue_retain(val);
        return val;
    }
    ZenHeapHeader* h = (ZenHeapHeader*)val.as.object;
    if (h && h->ref_count == ZEN_REF_PINNED) {
        extern ZenValue ZenValue_clone_to_heap(ZenValue v);
        val = ZenValue_clone_to_heap(val);
    }
    ZenValue_freeze(val);
    return val;
}

static ZenValue zen_task_legacy_adapter(ZenValue cap_func, ZenValue arg_list) {
    ZenValue (*legacy_fn)(ZenValue*) = (ZenValue (*)(ZenValue*))cap_func.as.object;
    if (arg_list.type == ZEN_LIST && arg_list.as.list) {
        return legacy_fn(arg_list.as.list->items);
    }
    ZenValue dummy = arg_list;
    return legacy_fn(&dummy);
}

static ZenValue ZenDispatch_call(ZenValue callable, ZenValue argument) {
    if (argument.type == ZEN_NOTHING) {
        return ZenValue_apply(callable, 0);
    }
    if (callable.type == ZEN_FUNCTION && callable.as.object && argument.type == ZEN_LIST) {
        ZenClosureData* c = (ZenClosureData*)callable.as.object;
        ZenList* l = argument.as.list;
        if (l && l->count > 1 && c->arity > 1 && c->arity == l->count) {
            switch (l->count) {
                case 2: return ZenValue_apply(callable, 2, l->items[0], l->items[1]);
                case 3: return ZenValue_apply(callable, 3, l->items[0], l->items[1], l->items[2]);
                case 4: return ZenValue_apply(callable, 4, l->items[0], l->items[1], l->items[2], l->items[3]);
                case 5: return ZenValue_apply(callable, 5, l->items[0], l->items[1], l->items[2], l->items[3], l->items[4]);
                case 6: return ZenValue_apply(callable, 6, l->items[0], l->items[1], l->items[2], l->items[3], l->items[4], l->items[5]);
                case 7: return ZenValue_apply(callable, 7, l->items[0], l->items[1], l->items[2], l->items[3], l->items[4], l->items[5], l->items[6]);
                case 8: return ZenValue_apply(callable, 8, l->items[0], l->items[1], l->items[2], l->items[3], l->items[4], l->items[5], l->items[6], l->items[7]);
                default: break;
            }
        }
    }
    return ZenValue_apply(callable, 1, argument);
}

/* =========================================================================
 * Worker Thread Execution Loop
 * ========================================================================= */
static void* worker_thread_loop(void* arg) {
    (void)arg;
    while (1) {
        pthread_mutex_lock(&pool.lock);
        while (!pool.head && !pool.shutdown) {
            pthread_cond_wait(&pool.not_empty, &pool.lock);
        }
        
        if (pool.shutdown && !pool.head) {
            pthread_mutex_unlock(&pool.lock);
            break;
        }
        
        // Dequeue Task
        ZenTaskHandle* task = pool.head;
        pool.head = task->next;
        if (!pool.head) pool.tail = NULL;
        pthread_mutex_unlock(&pool.lock);
        
        // Check Cancellation
        pthread_mutex_lock(&task->lock);
        if (task->state == TASK_CANCELLED) {
            pthread_mutex_unlock(&task->lock);
            ZenValue_release(ZenValue_from_task(task)); // Drop pool's reference
            continue;
        }
        task->state = TASK_RUNNING;
        pthread_mutex_unlock(&task->lock);
        
        // Execute the Task (with its own clean memory scope)
        current_worker_task = task;
        ZenValue result = ZenDispatch_call(task->callable, task->argument);
        current_worker_task = NULL;
        
        // Freeze the result so the awaiting thread can safely read it
        ZenValue frozen_result = zen_task_prepare_handoff(result);
        
        pthread_mutex_lock(&task->lock);
        task->result = frozen_result;
        task->state = (result.type == ZEN_ERROR) ? TASK_FAILED : TASK_COMPLETED;
        pthread_cond_broadcast(&task->cond);
        pthread_mutex_unlock(&task->lock);
        
        ZenValue_release(ZenValue_from_task(task)); // Drop pool's reference
    }
    return NULL;
}

/* =========================================================================
 * Dedicated Blocking C-FFI / I/O Worker Thread Execution Loop
 * ========================================================================= */
static void* blocking_thread_loop(void* arg) {
    (void)arg;
    while (1) {
        pthread_mutex_lock(&blocking_pool.lock);
        blocking_pool.idle_count++;
        while (!blocking_pool.head && !blocking_pool.shutdown) {
            pthread_cond_wait(&blocking_pool.not_empty, &blocking_pool.lock);
        }
        blocking_pool.idle_count--;
        
        if (blocking_pool.shutdown && !blocking_pool.head) {
            pthread_mutex_unlock(&blocking_pool.lock);
            break;
        }
        
        ZenTaskHandle* task = blocking_pool.head;
        blocking_pool.head = task->next;
        if (!blocking_pool.head) blocking_pool.tail = NULL;
        pthread_mutex_unlock(&blocking_pool.lock);
        
        pthread_mutex_lock(&task->lock);
        if (task->state == TASK_CANCELLED) {
            pthread_mutex_unlock(&task->lock);
            ZenValue_release(ZenValue_from_task(task));
            continue;
        }
        task->state = TASK_RUNNING;
        pthread_mutex_unlock(&task->lock);
        
        current_worker_task = task;
        ZenValue result = ZenDispatch_call(task->callable, task->argument);
        current_worker_task = NULL;
        
        ZenValue frozen_result = zen_task_prepare_handoff(result);
        
        pthread_mutex_lock(&task->lock);
        task->result = frozen_result;
        task->state = (result.type == ZEN_ERROR) ? TASK_FAILED : TASK_COMPLETED;
        pthread_cond_broadcast(&task->cond);
        pthread_mutex_unlock(&task->lock);
        
        ZenValue_release(ZenValue_from_task(task));
    }
    return NULL;
}

/* =========================================================================
 * Engine Initialization & Shutdown
 * ========================================================================= */
static int get_cpu_count(void) {
#ifdef _SC_NPROCESSORS_ONLN
    long n = sysconf(_SC_NPROCESSORS_ONLN);
    if (n > 0) return (int)n;
#endif
    return 4;
}

void ZenTaskEngine_init(void) {
    if (engine_initialized) return;
    
    // 1. Cooperative Work-Stealing Compute Pool
    pthread_mutex_init(&pool.lock, NULL);
    pthread_cond_init(&pool.not_empty, NULL);
    pool.head = NULL;
    pool.tail = NULL;
    pool.shutdown = false;
    
    pool.worker_count = get_cpu_count();
    if (pool.worker_count <= 0) pool.worker_count = 4;
    if (pool.worker_count > 32) pool.worker_count = 32;
    
    pool.workers = (pthread_t*)malloc(pool.worker_count * sizeof(pthread_t));
    for (int i = 0; i < pool.worker_count; i++) {
        pthread_create(&pool.workers[i], NULL, worker_thread_loop, NULL);
    }

    // 2. Dedicated Blocking C-FFI / I/O Pool
    pthread_mutex_init(&blocking_pool.lock, NULL);
    pthread_cond_init(&blocking_pool.not_empty, NULL);
    blocking_pool.head = NULL;
    blocking_pool.tail = NULL;
    blocking_pool.shutdown = false;
    blocking_pool.idle_count = 0;
    blocking_pool.max_workers = 64;
    blocking_pool.worker_count = 4;
    blocking_pool.workers = (pthread_t*)malloc(blocking_pool.max_workers * sizeof(pthread_t));
    for (int i = 0; i < blocking_pool.worker_count; i++) {
        pthread_create(&blocking_pool.workers[i], NULL, blocking_thread_loop, NULL);
    }

    engine_initialized = true;
}

void ZenTaskEngine_shutdown(void) {
    if (!engine_initialized) return;
    
    // 1. Shutdown Compute Pool
    pthread_mutex_lock(&pool.lock);
    pool.shutdown = true;
    pthread_cond_broadcast(&pool.not_empty);
    pthread_mutex_unlock(&pool.lock);
    
    for (int i = 0; i < pool.worker_count; i++) {
        pthread_join(pool.workers[i], NULL);
    }
    free(pool.workers);
    pthread_mutex_destroy(&pool.lock);
    pthread_cond_destroy(&pool.not_empty);

    // 2. Shutdown Blocking Pool
    pthread_mutex_lock(&blocking_pool.lock);
    blocking_pool.shutdown = true;
    pthread_cond_broadcast(&blocking_pool.not_empty);
    pthread_mutex_unlock(&blocking_pool.lock);

    for (int i = 0; i < blocking_pool.worker_count; i++) {
        pthread_join(blocking_pool.workers[i], NULL);
    }
    free(blocking_pool.workers);
    pthread_mutex_destroy(&blocking_pool.lock);
    pthread_cond_destroy(&blocking_pool.not_empty);

    engine_initialized = false;
}

/* =========================================================================
 * Task Public API
 * ========================================================================= */
ZenTaskHandle* (ZenTask_spawn)(ZenValue callable, ZenValue argument) {
    if (!engine_initialized) {
        ZenTaskEngine_init();
    }
    
    extern void ZenArena_suspend(void);
    extern void ZenArena_resume(void);
    ZenArena_suspend();
    ZenTaskHandle* task = (ZenTaskHandle*)malloc(sizeof(ZenTaskHandle));
    ZenArena_resume();
    if (!task) return NULL;
    
    ZenHeapHeader_init(&task->header, ZEN_TASK, ZEN_FLAG_NONE);
    task->callable = zen_task_prepare_handoff(callable);
    task->argument = zen_task_prepare_handoff(argument);
    task->result = (ZenValue){ .type = ZEN_NOTHING, .as.integer = 0 };
    task->state = TASK_PENDING;
    task->next = NULL;
    
    pthread_mutex_init(&task->lock, NULL);
    pthread_cond_init(&task->cond, NULL);
    
    // Retain once for the caller (returned pointer) and once for the thread pool queue
    task->header.ref_count = 2; 
    
    pthread_mutex_lock(&pool.lock);
    if (!pool.head) {
        pool.head = task;
        pool.tail = task;
    } else {
        pool.tail->next = task;
        pool.tail = task;
    }
    pthread_cond_signal(&pool.not_empty);
    pthread_mutex_unlock(&pool.lock);
    
    return task;
}

ZenValue (ZenTask_wait)(ZenTaskHandle* task) {
    if (!task) return (ZenValue){ .type = ZEN_NOTHING, .as.integer = 0 };
    pthread_mutex_lock(&task->lock);
    while (task->state == TASK_PENDING || task->state == TASK_RUNNING ||
           task->state == TASK_WAITING_IO || task->state == TASK_WAITING_TIMER) {
        pthread_cond_wait(&task->cond, &task->lock);
    }
    ZenValue res = task->result;
    pthread_mutex_unlock(&task->lock);
    return res; // Already frozen, safe to return directly
}

ZenValue ZenTask_wait_value(ZenValue task_val) {
    if (task_val.type == ZEN_TASK && task_val.as.object) {
        return (ZenTask_wait)((ZenTaskHandle*)task_val.as.object);
    }
    return (ZenValue){ .type = ZEN_NOTHING, .as.integer = 0 };
}

ZenValue ZenTask_spawn_val(ZenValue callable, ZenValue argument) {
    ZenTaskHandle* h = (ZenTask_spawn)(callable, argument);
    return ZenValue_from_task(h);
}

ZenTaskHandle* ZenTask_spawn_blocking(ZenValue callable, ZenValue argument) {
    if (!engine_initialized) {
        ZenTaskEngine_init();
    }
    
    extern void ZenArena_suspend(void);
    extern void ZenArena_resume(void);
    ZenArena_suspend();
    ZenTaskHandle* task = (ZenTaskHandle*)malloc(sizeof(ZenTaskHandle));
    ZenArena_resume();
    if (!task) return NULL;
    
    ZenHeapHeader_init(&task->header, ZEN_TASK, ZEN_FLAG_NONE);
    task->callable = zen_task_prepare_handoff(callable);
    task->argument = zen_task_prepare_handoff(argument);
    task->result = (ZenValue){ .type = ZEN_NOTHING, .as.integer = 0 };
    task->state = TASK_PENDING;
    task->next = NULL;
    
    pthread_mutex_init(&task->lock, NULL);
    pthread_cond_init(&task->cond, NULL);
    
    task->header.ref_count = 2; // caller + queue
    
    pthread_mutex_lock(&blocking_pool.lock);
    if (!blocking_pool.head) {
        blocking_pool.head = task;
        blocking_pool.tail = task;
    } else {
        blocking_pool.tail->next = task;
        blocking_pool.tail = task;
    }
    
    // Scale blocking pool workers dynamically if no workers are idle
    if (blocking_pool.idle_count == 0 && blocking_pool.worker_count < blocking_pool.max_workers) {
        int idx = blocking_pool.worker_count;
        blocking_pool.worker_count++;
        pthread_create(&blocking_pool.workers[idx], NULL, blocking_thread_loop, NULL);
    }
    
    pthread_cond_signal(&blocking_pool.not_empty);
    pthread_mutex_unlock(&blocking_pool.lock);
    
    return task;
}

ZenValue ZenTask_spawn_blocking_val(ZenValue callable, ZenValue argument) {
    ZenTaskHandle* h = ZenTask_spawn_blocking(callable, argument);
    return ZenValue_from_task(h);
}

void ZenTask_enqueue_ready(ZenTaskHandle* task) {
    if (!task) return;
    pthread_mutex_lock(&task->lock);
    task->state = TASK_PENDING;
    pthread_mutex_unlock(&task->lock);
    
    pthread_mutex_lock(&pool.lock);
    task->next = NULL;
    if (!pool.head) {
        pool.head = task;
        pool.tail = task;
    } else {
        pool.tail->next = task;
        pool.tail = task;
    }
    pthread_cond_signal(&pool.not_empty);
    pthread_mutex_unlock(&pool.lock);
}

ZenValue ZenTask_spawn_legacy(void* func, int arg_count, ZenValue* args) {
    ZenValue arg = ZenList_make_from_arguments(0);
    for (int i = 0; i < arg_count; i++) {
        ZenList_append_value(arg, args[i]);
    }
    ZenValue cap = { .type = ZEN_OBJECT, .as.object = func };
    ZenValue fn = ZenValue_from_closure((void*)zen_task_legacy_adapter, 1, 1, cap);
    ZenTaskHandle* h = (ZenTask_spawn)(fn, arg);
    return ZenValue_from_task(h);
}

void ZenTask_cancel(ZenTaskHandle* task) {
    if (!task) return;
    pthread_mutex_lock(&task->lock);
    if (task->state == TASK_PENDING) {
        task->state = TASK_CANCELLED;
        pthread_cond_broadcast(&task->cond);
    }
    pthread_mutex_unlock(&task->lock);
}

bool ZenTask_is_cancelled(ZenTaskHandle* task) {
    if (!task) return false;
    pthread_mutex_lock(&task->lock);
    bool cancelled = (task->state == TASK_CANCELLED);
    pthread_mutex_unlock(&task->lock);
    return cancelled;
}

ZenTaskState ZenTask_get_state(ZenTaskHandle* task) {
    if (!task) return TASK_FAILED;
    pthread_mutex_lock(&task->lock);
    ZenTaskState s = task->state;
    pthread_mutex_unlock(&task->lock);
    return s;
}

void ZenTask_destroy(ZenTaskHandle* task) {
    if (!task) return;
    
    ZenValue_release(task->callable);
    ZenValue_release(task->argument);
    ZenValue_release(task->result);
    
    pthread_cond_destroy(&task->cond);
    pthread_mutex_destroy(&task->lock);
    
    if (task->header.ref_count != ZEN_REF_PINNED) {
        free(task);
    }
}

void ZenTask_yield(void) {
    sched_yield();
}

void ZenTask_scheduler_init(void) {
    ZenTaskEngine_init();
}

void ZenTask_scheduler_run(void) {
    // Background pool is continuously active
}
