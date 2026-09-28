#include "zen_channel.h"
#include "../memory/zen_memory.h"
#include <stdlib.h>

ZenChannel* ZenChannel_new(int capacity) {
    if (capacity <= 0) capacity = 1;
    
    ZenChannel* ch = (ZenChannel*)ZenRuntime_allocate(sizeof(ZenChannel));
    if (!ch) return NULL;
    
    ZenHeapHeader_init(&ch->header, ZEN_CHANNEL, ZEN_FLAG_CONTAINER);
    ch->capacity = capacity;
    ch->count = 0;
    ch->head = 0;
    ch->tail = 0;
    ch->is_closed = false;
    ch->buffer = (ZenValue*)malloc(capacity * sizeof(ZenValue));
    
    pthread_mutex_init(&ch->lock, NULL);
    pthread_cond_init(&ch->not_empty, NULL);
    pthread_cond_init(&ch->not_full, NULL);
    
    return ch;
}

ZenValue ZenChannel_make(ZenValue cap_val) {
    int cap = 1;
    if (cap_val.type == ZEN_INTEGER) cap = (int)cap_val.as.integer;
    return ZenValue_from_channel(ZenChannel_new(cap));
}

void ZenChannel_destroy(ZenChannel* ch) {
    if (!ch) return;
    
    // Safely release any unconsumed items remaining in the channel buffer
    pthread_mutex_lock(&ch->lock);
    while (ch->count > 0) {
        ZenValue_release(ch->buffer[ch->tail]);
        ch->tail = (ch->tail + 1) % ch->capacity;
        ch->count--;
    }
    pthread_mutex_unlock(&ch->lock);
    
    pthread_cond_destroy(&ch->not_empty);
    pthread_cond_destroy(&ch->not_full);
    pthread_mutex_destroy(&ch->lock);
    
    if (ch->buffer) free(ch->buffer);
    if (ch->header.ref_count != ZEN_REF_PINNED) {
        free(ch);
    }
}

/* =========================================================================
 * The Frozen Handoff Boundary
 * ========================================================================= */
static ZenValue zen_channel_prepare_handoff(ZenValue val) {
    if (!ZenValue_is_heap_pointer(val)) return val;
    
    ZenHeapHeader* h = (ZenHeapHeader*)val.as.object;
    if (h && h->ref_count == ZEN_REF_PINNED) {
        // Escape Hatch: Clone arena values to the standard heap
        extern ZenValue ZenValue_clone_to_heap(ZenValue v);
        val = ZenValue_clone_to_heap(val);
    }
    
    // Deep freeze the graph: 0 ARC churn across threads
    ZenValue_freeze(val);
    return val;
}

/* =========================================================================
 * Blocking Operations (For Worker OS Threads)
 * ========================================================================= */
bool ZenChannel_send(ZenChannel* ch, ZenValue val) {
    if (!ch) return false;
    ZenValue frozen_val = zen_channel_prepare_handoff(val);
    
    pthread_mutex_lock(&ch->lock);
    while (ch->count == ch->capacity && !ch->is_closed) {
        pthread_cond_wait(&ch->not_full, &ch->lock);
    }
    
    if (ch->is_closed) {
        pthread_mutex_unlock(&ch->lock);
        return false; // Cannot send on a closed channel
    }
    
    ch->buffer[ch->head] = frozen_val;
    ch->head = (ch->head + 1) % ch->capacity;
    ch->count++;
    
    pthread_cond_signal(&ch->not_empty);
    pthread_mutex_unlock(&ch->lock);
    return true;
}

ZenValue ZenChannel_receive(ZenChannel* ch) {
    if (!ch) return ZEN_NOTHING_VAL;
    pthread_mutex_lock(&ch->lock);
    while (ch->count == 0 && !ch->is_closed) {
        pthread_cond_wait(&ch->not_empty, &ch->lock);
    }
    
    if (ch->count == 0 && ch->is_closed) {
        pthread_mutex_unlock(&ch->lock);
        return ZEN_NOTHING_VAL; // Channel closed and empty
    }
    
    ZenValue val = ch->buffer[ch->tail];
    ch->tail = (ch->tail + 1) % ch->capacity;
    ch->count--;
    
    pthread_cond_signal(&ch->not_full);
    pthread_mutex_unlock(&ch->lock);
    
    // Return the deeply frozen pointer directly
    return val;
}

/* =========================================================================
 * Non-Blocking & Lifecycle Operations
 * ========================================================================= */
bool ZenChannel_try_send(ZenChannel* ch, ZenValue val) {
    if (!ch) return false;
    ZenValue frozen_val = zen_channel_prepare_handoff(val);
    
    pthread_mutex_lock(&ch->lock);
    if (ch->is_closed || ch->count == ch->capacity) {
        pthread_mutex_unlock(&ch->lock);
        return false;
    }
    
    ch->buffer[ch->head] = frozen_val;
    ch->head = (ch->head + 1) % ch->capacity;
    ch->count++;
    
    pthread_cond_signal(&ch->not_empty);
    pthread_mutex_unlock(&ch->lock);
    return true;
}

ZenValue ZenChannel_try_receive(ZenChannel* ch) {
    if (!ch) return ZEN_NOTHING_VAL;
    pthread_mutex_lock(&ch->lock);
    if (ch->count == 0) {
        pthread_mutex_unlock(&ch->lock);
        return ZEN_NOTHING_VAL;
    }
    
    ZenValue val = ch->buffer[ch->tail];
    ch->tail = (ch->tail + 1) % ch->capacity;
    ch->count--;
    
    pthread_cond_signal(&ch->not_full);
    pthread_mutex_unlock(&ch->lock);
    return val;
}

void ZenChannel_close(ZenChannel* ch) {
    if (!ch) return;
    pthread_mutex_lock(&ch->lock);
    ch->is_closed = true;
    pthread_cond_broadcast(&ch->not_empty); // Wake waiting receivers
    pthread_cond_broadcast(&ch->not_full);  // Wake waiting senders
    pthread_mutex_unlock(&ch->lock);
}

bool ZenChannel_is_closed(ZenChannel* ch) {
    if (!ch) return true;
    pthread_mutex_lock(&ch->lock);
    bool closed = ch->is_closed;
    pthread_mutex_unlock(&ch->lock);
    return closed;
}
