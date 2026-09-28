#include "bootstrap_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <pthread.h>
#include <string.h>

#define CONCURRENT_TASK_COUNT 1000

// Helper function 1: Square
ZenValue task_square(ZenValue arg) {
    assert(arg.type == ZEN_INTEGER);
    long long x = arg.as.integer;
    return ZenValue_make_integer(x * x);
}

// Helper function 2: Process complex nested graph
ZenValue task_process_graph(ZenValue arg) {
    // Verify argument is deeply frozen
    assert(ZenValue_is_heap_pointer(arg));
    ZenHeapHeader* h = (ZenHeapHeader*)arg.as.object;
    assert(h->ref_count == ZEN_REF_FROZEN);
    assert(h->flags & ZEN_FLAG_FROZEN);
    
    assert(arg.type == ZEN_LIST);
    ZenList* l = arg.as.list;
    assert(l->count == 3);
    
    ZenValue map_val = l->items[0];
    assert(map_val.type == ZEN_MAP);
    ZenHeapHeader* mh = (ZenHeapHeader*)map_val.as.object;
    assert(mh->ref_count == ZEN_REF_FROZEN);
    
    ZenValue name_val = ZenMap_get_value_at_key(map_val, ZenValue_make_string("name"));
    assert(name_val.type == ZEN_STRING);
    assert(strcmp(name_val.as.string, "zen_task") == 0);
    
    // Return a new map
    ZenValue res_map = ZenValue_from_map(ZenMap_new());
    ZenMap_set_value_at_key(res_map, ZenValue_make_string("status"), ZenValue_make_string("processed"));
    ZenMap_set_value_at_key(res_map, ZenValue_make_string("code"), ZenValue_make_integer(200));
    return res_map;
}

// Helper function 3: Sum arena list
ZenValue task_sum_list(ZenValue arg) {
    assert(arg.type == ZEN_LIST);
    ZenList* l = arg.as.list;
    long long sum = 0;
    for (int i = 0; i < l->count; i++) {
        sum += l->items[i].as.integer;
    }
    return ZenValue_make_integer(sum);
}

// Helper function 4: Closure target (caps: a, b; arg: c)
ZenValue task_closure_fn(ZenValue cap_a, ZenValue cap_b, ZenValue user_c) {
    assert(cap_a.type == ZEN_INTEGER);
    assert(cap_b.type == ZEN_INTEGER);
    assert(user_c.type == ZEN_INTEGER);
    return ZenValue_make_integer(cap_a.as.integer + cap_b.as.integer + user_c.as.integer);
}

// Helper function 5: Fan-out task
ZenValue task_compute(ZenValue arg) {
    assert(arg.type == ZEN_INTEGER);
    long long idx = arg.as.integer;
    return ZenValue_make_integer(idx * 2 + 1);
}

int main(void) {
    printf("[TEST] Starting ZenTask C-level Concurrency Test Driver...\n");
    
    // Initialize Runtime & Task Engine
    ZenRuntime_initialize();
    
    // -------------------------------------------------------------------------
    // Test 1: Basic Task Spawn & Wait
    // -------------------------------------------------------------------------
    printf("[TEST 1] Basic Task Spawn & Wait (Square function)...\n");
    ZenValue fn1 = ZenValue_from_function((ZenValue (*)(void))task_square);
    ZenTaskHandle* t1 = ZenTask_spawn(fn1, ZenValue_make_integer(12));
    assert(t1 != NULL);
    
    ZenValue r1 = ZenTask_wait(t1);
    assert(r1.type == ZEN_INTEGER);
    assert(r1.as.integer == 144);
    assert(ZenTask_get_state(t1) == TASK_COMPLETED);
    
    // Release caller's handle
    ZenValue_release(ZenValue_from_task(t1));
    printf("[TEST 1] PASS\n");
    
    // -------------------------------------------------------------------------
    // Test 2: Complex Graph Handoff & Freezing Boundary
    // -------------------------------------------------------------------------
    printf("[TEST 2] Complex Graph Handoff & Freezing Boundary...\n");
    ZenValue m2 = ZenValue_from_map(ZenMap_new());
    ZenMap_set_value_at_key(m2, ZenValue_make_string("name"), ZenValue_make_string("zen_task"));
    ZenMap_set_value_at_key(m2, ZenValue_make_string("version"), ZenValue_make_integer(1));
    
    ZenValue l2 = ZenList_make_from_arguments(3, m2, ZenValue_make_integer(42), ZenValue_make_string("payload"));
    
    ZenValue fn2 = ZenValue_from_function((ZenValue (*)(void))task_process_graph);
    ZenTaskHandle* t2 = ZenTask_spawn(fn2, l2);
    assert(t2 != NULL);
    
    ZenValue r2 = ZenTask_wait(t2);
    assert(r2.type == ZEN_MAP);
    
    // Verify result is frozen
    ZenHeapHeader* r2_h = (ZenHeapHeader*)r2.as.object;
    assert(r2_h->ref_count == ZEN_REF_FROZEN);
    assert(r2_h->flags & ZEN_FLAG_FROZEN);
    
    ZenValue status_val = ZenMap_get_value_at_key(r2, ZenValue_make_string("status"));
    assert(status_val.type == ZEN_STRING);
    assert(strcmp(status_val.as.string, "processed") == 0);
    
    ZenValue code_val = ZenMap_get_value_at_key(r2, ZenValue_make_string("code"));
    assert(code_val.type == ZEN_INTEGER && code_val.as.integer == 200);
    
    ZenValue_release(ZenValue_from_task(t2));
    printf("[TEST 2] PASS\n");
    
    // -------------------------------------------------------------------------
    // Test 3: Arena Escape Hatch & Frozen Promotion
    // -------------------------------------------------------------------------
    printf("[TEST 3] Arena Escape Hatch & Frozen Promotion...\n");
    ZenValue arena_val = ZenMemory_create_arena(ZenValue_make_integer(1024 * 1024));
    ZenMemory_push_arena(arena_val);
    
    // Allocate list in bump arena
    ZenValue arena_list = ZenList_make_from_arguments(3,
        ZenValue_make_integer(10),
        ZenValue_make_integer(20),
        ZenValue_make_integer(30)
    );
    ZenHeapHeader* al_h = (ZenHeapHeader*)arena_list.as.object;
    assert(al_h->ref_count == ZEN_REF_PINNED);
    
    ZenValue fn3 = ZenValue_from_function((ZenValue (*)(void))task_sum_list);
    // Spawning task clones arena data to standard heap and freezes it
    ZenTaskHandle* t3 = ZenTask_spawn(fn3, arena_list);
    assert(t3 != NULL);
    
    // Pop and destroy the arena immediately
    ZenMemory_pop_arena();
    ZenMemory_free_arena(arena_val);
    
    // Await task - worker processed the promoted, frozen clone safely
    ZenValue r3 = ZenTask_wait(t3);
    assert(r3.type == ZEN_INTEGER);
    assert(r3.as.integer == 60);
    
    ZenValue_release(ZenValue_from_task(t3));
    printf("[TEST 3] PASS\n");
    
    // -------------------------------------------------------------------------
    // Test 4: Closure Support with Captured Variables
    // -------------------------------------------------------------------------
    printf("[TEST 4] Closure Execution with Captured Variables...\n");
    ZenValue closure = ZenValue_from_closure(
        (void*)task_closure_fn,
        1, /* 1 user argument */
        2, /* 2 captures */
        ZenValue_make_integer(100),
        ZenValue_make_integer(200)
    );
    
    ZenTaskHandle* t4 = ZenTask_spawn(closure, ZenValue_make_integer(50));
    assert(t4 != NULL);
    
    ZenValue r4 = ZenTask_wait(t4);
    assert(r4.type == ZEN_INTEGER);
    assert(r4.as.integer == 350);
    
    ZenValue_release(ZenValue_from_task(t4));
    printf("[TEST 4] PASS\n");
    
    // -------------------------------------------------------------------------
    // Test 5: Concurrency Fan-out / Fan-in (Stress: 1000 tasks)
    // -------------------------------------------------------------------------
    printf("[TEST 5] Heavy Concurrency Fan-out / Fan-in (%d tasks)...\n", CONCURRENT_TASK_COUNT);
    ZenValue fn5 = ZenValue_from_function((ZenValue (*)(void))task_compute);
    ZenTaskHandle* handles[CONCURRENT_TASK_COUNT];
    
    // Spawn all 1,000 tasks
    for (int i = 0; i < CONCURRENT_TASK_COUNT; i++) {
        handles[i] = ZenTask_spawn(fn5, ZenValue_make_integer(i));
        assert(handles[i] != NULL);
    }
    
    // Await all 1,000 tasks and verify results
    for (int i = 0; i < CONCURRENT_TASK_COUNT; i++) {
        ZenValue res = ZenTask_wait(handles[i]);
        assert(res.type == ZEN_INTEGER);
        assert(res.as.integer == i * 2 + 1);
        assert(ZenTask_get_state(handles[i]) == TASK_COMPLETED);
        
        // Clean up handle
        ZenValue_release(ZenValue_from_task(handles[i]));
    }
    printf("[TEST 5] PASS (all %d tasks executed correctly)\n", CONCURRENT_TASK_COUNT);
    
    // -------------------------------------------------------------------------
    // Test 6: Task Cancellation API
    // -------------------------------------------------------------------------
    printf("[TEST 6] Task Cancellation API...\n");
    ZenValue fn6 = ZenValue_from_function((ZenValue (*)(void))task_square);
    ZenTaskHandle* t6 = ZenTask_spawn(fn6, ZenValue_make_integer(99));
    assert(t6 != NULL);
    
    // Check cancellation query
    bool is_canc = ZenTask_is_cancelled(t6);
    (void)is_canc;
    if (ZenTask_get_state(t6) == TASK_PENDING) {
        ZenTask_cancel(t6);
        assert(ZenTask_is_cancelled(t6));
    }
    ZenTask_wait(t6); // Must not hang
    ZenValue_release(ZenValue_from_task(t6));
    printf("[TEST 6] PASS\n");
    
    // -------------------------------------------------------------------------
    // Test 7: Universal ABI & Type Introspection
    // -------------------------------------------------------------------------
    printf("[TEST 7] Universal ABI & Type Introspection...\n");
    ZenValue fn7 = ZenValue_from_function((ZenValue (*)(void))task_square);
    ZenTaskHandle* t7 = ZenTask_spawn(fn7, ZenValue_make_integer(5));
    ZenValue task_val = ZenValue_from_task(t7);
    
    assert(task_val.type == ZEN_TASK);
    assert(ZenValue_is_heap_pointer(task_val));
    
    ZenValue kind = ZenValue_get_kind(task_val);
    assert(kind.type == ZEN_STRING);
    assert(strcmp(kind.as.string, "Task") == 0);
    
    assert(ZenValue_is_type_name(task_val, "Task").as.boolean);
    
    ZenValue wait_res = ZenTask_wait(task_val);
    assert(wait_res.type == ZEN_INTEGER && wait_res.as.integer == 25);
    
    // Release task_val
    ZenValue_release(task_val);
    printf("[TEST 7] PASS\n");
    
    // Shutdown Engine
    ZenRuntime_terminate();
    
    printf("\n>>> ALL ZENTASK CONCURRENCY TESTS PASSED SUCCESSFULLY! <<<\n");
    return 0;
}
