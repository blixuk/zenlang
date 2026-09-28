#ifndef ZEN_CHANNEL_H
#define ZEN_CHANNEL_H

#include "../core/zen_value.h"
#include <pthread.h>
#include <stdbool.h>

typedef struct ZenChannel {
    ZenHeapHeader header;       /* 8 bytes: Intrusive ARC / Sentinel header */
    ZenValue* buffer;           /* Ring buffer array */
    int capacity;
    int count;
    int head;                   /* Write index */
    int tail;                   /* Read index */
    bool is_closed;
    
    // Concurrency Primitives
    pthread_mutex_t lock;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
} ZenChannel;

ZenChannel* ZenChannel_new(int capacity);
ZenValue ZenChannel_make(ZenValue cap_val);
void ZenChannel_destroy(ZenChannel* ch);

bool ZenChannel_send(ZenChannel* ch, ZenValue val);
ZenValue ZenChannel_receive(ZenChannel* ch);
bool ZenChannel_try_send(ZenChannel* ch, ZenValue val);
ZenValue ZenChannel_try_receive(ZenChannel* ch);

void ZenChannel_close(ZenChannel* ch);
bool ZenChannel_is_closed(ZenChannel* ch);

static inline ZenValue ZenValue_from_channel(ZenChannel* ch) {
    ZenValue v;
    v.type = ZEN_CHANNEL;
    v.as.object = (void*)ch;
    return v;
}

static inline ZenChannel* ZenValue_to_channel(ZenValue v) {
    if (v.type != ZEN_CHANNEL) return NULL;
    return (ZenChannel*)v.as.object;
}

#endif /* ZEN_CHANNEL_H */
