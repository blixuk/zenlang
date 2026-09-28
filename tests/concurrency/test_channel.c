#include "bootstrap_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <pthread.h>
#include <string.h>

#define NUM_PRODUCERS 4
#define NUM_CONSUMERS 4
#define ITEMS_PER_PRODUCER 1000

typedef struct {
    ZenChannel* ch;
    int producer_id;
} ProducerArgs;

typedef struct {
    ZenChannel* ch;
    int consumer_id;
    int items_received;
} ConsumerArgs;

void* producer_worker(void* arg) {
    ProducerArgs* pargs = (ProducerArgs*)arg;
    for (int i = 0; i < ITEMS_PER_PRODUCER; i++) {
        // Build a nested container graph: List of [Map, Integer, String]
        ZenValue m = ZenValue_from_map(ZenMap_new());
        ZenMap_set_value_at_key(m, ZenValue_make_string("key"), ZenValue_make_integer(i));
        ZenMap_set_value_at_key(m, ZenValue_make_string("producer"), ZenValue_make_integer(pargs->producer_id));
        
        ZenValue l = ZenList_make_from_arguments(3, m, ZenValue_make_integer(i), ZenValue_make_string("payload"));
        
        bool ok = ZenChannel_send(pargs->ch, l);
        assert(ok);
    }
    return NULL;
}

void* consumer_worker(void* arg) {
    ConsumerArgs* cargs = (ConsumerArgs*)arg;
    while (true) {
        ZenValue item = ZenChannel_receive(cargs->ch);
        if (item.type == ZEN_NOTHING) {
            // Channel is closed and drained
            break;
        }
        cargs->items_received++;
        
        // Verify received item is deeply frozen
        assert(ZenValue_is_heap_pointer(item));
        ZenHeapHeader* h = (ZenHeapHeader*)item.as.object;
        assert(h->ref_count == ZEN_REF_FROZEN);
        assert(h->flags & ZEN_FLAG_FROZEN);
        
        // Inspect list elements
        assert(item.type == ZEN_LIST);
        ZenList* list = item.as.list;
        assert(list->count == 3);
        
        ZenValue child_map = list->items[0];
        assert(child_map.type == ZEN_MAP);
        ZenHeapHeader* map_h = (ZenHeapHeader*)child_map.as.object;
        assert(map_h->ref_count == ZEN_REF_FROZEN);
        
        // Retain and Release must be no-ops on frozen objects
        ZenValue_retain(item);
        assert(h->ref_count == ZEN_REF_FROZEN);
        ZenValue_release(item);
        assert(h->ref_count == ZEN_REF_FROZEN);
    }
    return NULL;
}

int main(void) {
    printf("[TEST] Starting ZenChannel C-level Test Driver...\n");
    
    // -------------------------------------------------------------------------
    // Test 1: Basic Ring Buffer FIFO and Non-blocking Operations
    // -------------------------------------------------------------------------
    printf("[TEST 1] Ring Buffer FIFO & Non-blocking ops...\n");
    ZenChannel* ch = ZenChannel_new(3);
    assert(ch != NULL);
    assert(ch->capacity == 3);
    assert(ch->count == 0);
    assert(!ZenChannel_is_closed(ch));
    
    // Try receive from empty channel
    ZenValue empty = ZenChannel_try_receive(ch);
    assert(empty.type == ZEN_NOTHING);
    
    // Send 3 values
    assert(ZenChannel_try_send(ch, ZenValue_make_integer(10)));
    assert(ZenChannel_try_send(ch, ZenValue_make_integer(20)));
    assert(ZenChannel_try_send(ch, ZenValue_make_integer(30)));
    
    // Buffer is full (capacity 3)
    assert(!ZenChannel_try_send(ch, ZenValue_make_integer(40)));
    
    // Receive 3 values in FIFO order
    ZenValue r1 = ZenChannel_try_receive(ch);
    assert(r1.type == ZEN_INTEGER && r1.as.integer == 10);
    ZenValue r2 = ZenChannel_try_receive(ch);
    assert(r2.type == ZEN_INTEGER && r2.as.integer == 20);
    ZenValue r3 = ZenChannel_try_receive(ch);
    assert(r3.type == ZEN_INTEGER && r3.as.integer == 30);
    
    assert(ch->count == 0);
    ZenChannel_destroy(ch);
    printf("[TEST 1] PASS\n");
    
    // -------------------------------------------------------------------------
    // Test 2: Arena Escape Hatch & Frozen Promotion
    // -------------------------------------------------------------------------
    printf("[TEST 2] Arena Escape Hatch & Frozen Promotion...\n");
    ZenChannel* arena_ch = ZenChannel_new(2);
    
    ZenValue a_val = ZenMemory_create_arena(ZenValue_make_integer(1024 * 1024));
    ZenMemory_push_arena(a_val);
    
    // Allocate list in arena
    ZenValue arena_list = ZenList_make_from_arguments(2, ZenValue_make_integer(111), ZenValue_make_integer(222));
    ZenHeapHeader* al_h = (ZenHeapHeader*)arena_list.as.object;
    assert(al_h->ref_count == ZEN_REF_PINNED);
    
    // Send arena list into channel: prepare_for_handoff should clone and freeze!
    bool send_ok = ZenChannel_send(arena_ch, arena_list);
    assert(send_ok);
    
    // Pop arena and free it
    ZenMemory_pop_arena();
    ZenMemory_free_arena(a_val);
    
    // Receive from channel - pointer must remain fully valid and frozen on heap!
    ZenValue rec_list = ZenChannel_receive(arena_ch);
    assert(rec_list.type == ZEN_LIST);
    ZenHeapHeader* rec_h = (ZenHeapHeader*)rec_list.as.object;
    assert(rec_h->ref_count == ZEN_REF_FROZEN);
    assert(rec_h->flags & ZEN_FLAG_FROZEN);
    assert(rec_list.as.list->count == 2);
    assert(rec_list.as.list->items[0].as.integer == 111);
    assert(rec_list.as.list->items[1].as.integer == 222);
    
    ZenChannel_destroy(arena_ch);
    printf("[TEST 2] PASS\n");
    
    // -------------------------------------------------------------------------
    // Test 3: Multi-threaded Producer / Consumer Workload
    // -------------------------------------------------------------------------
    printf("[TEST 3] Multi-threaded MPMC (%d producers, %d consumers, %d items/prod)...\n",
           NUM_PRODUCERS, NUM_CONSUMERS, ITEMS_PER_PRODUCER);
    
    ZenChannel* mpmc_ch = ZenChannel_new(64);
    pthread_t producers[NUM_PRODUCERS];
    pthread_t consumers[NUM_CONSUMERS];
    ProducerArgs pargs[NUM_PRODUCERS];
    ConsumerArgs cargs[NUM_CONSUMERS];
    
    // Start consumers
    for (int i = 0; i < NUM_CONSUMERS; i++) {
        cargs[i].ch = mpmc_ch;
        cargs[i].consumer_id = i;
        cargs[i].items_received = 0;
        pthread_create(&consumers[i], NULL, consumer_worker, &cargs[i]);
    }
    
    // Start producers
    for (int i = 0; i < NUM_PRODUCERS; i++) {
        pargs[i].ch = mpmc_ch;
        pargs[i].producer_id = i;
        pthread_create(&producers[i], NULL, producer_worker, &pargs[i]);
    }
    
    // Wait for all producers to finish
    for (int i = 0; i < NUM_PRODUCERS; i++) {
        pthread_join(producers[i], NULL);
    }
    printf("[TEST 3] All producers finished sending.\n");
    
    // Close channel to signal consumers once buffer empties
    ZenChannel_close(mpmc_ch);
    assert(ZenChannel_is_closed(mpmc_ch));
    
    // Wait for all consumers to finish
    int total_received = 0;
    for (int i = 0; i < NUM_CONSUMERS; i++) {
        pthread_join(consumers[i], NULL);
        total_received += cargs[i].items_received;
        printf("  Consumer %d processed %d items\n", i, cargs[i].items_received);
    }
    
    printf("[TEST 3] Total items received: %d (expected %d)\n",
           total_received, NUM_PRODUCERS * ITEMS_PER_PRODUCER);
    assert(total_received == NUM_PRODUCERS * ITEMS_PER_PRODUCER);
    
    ZenChannel_destroy(mpmc_ch);
    printf("[TEST 3] PASS\n");
    
    // -------------------------------------------------------------------------
    // Test 4: Channel Value and Intrusive Heap Lifecycle
    // -------------------------------------------------------------------------
    printf("[TEST 4] Channel Value boxing & destruction dispatcher...\n");
    ZenChannel* ch4 = ZenChannel_new(4);
    ZenValue ch_val = ZenValue_from_channel(ch4);
    assert(ch_val.type == ZEN_CHANNEL);
    assert(ZenValue_is_heap_pointer(ch_val));
    assert(ZenValue_get_header(ch_val)->ref_count == 1);
    
    // Retain and Release via standard ZenValue ARC
    ZenValue_retain(ch_val);
    assert(ZenValue_get_header(ch_val)->ref_count == 2);
    ZenValue_release(ch_val);
    assert(ZenValue_get_header(ch_val)->ref_count == 1);
    
    // Final release triggers ZenValue_destroy_heap_object -> ZenChannel_destroy
    ZenValue_release(ch_val);
    printf("[TEST 4] PASS\n");
    
    printf("\n>>> ALL ZEN_CHANNEL CONCURRENCY TESTS PASSED SUCCESSFULLY! <<<\n");
    return 0;
}
