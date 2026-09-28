#ifndef ZEN_REACTOR_H
#define ZEN_REACTOR_H

#include "../core/zen_value.h"
#include "zen_task.h"
#include <stdbool.h>

typedef enum {
    ZEN_REACTOR_READ   = 1 << 0,
    ZEN_REACTOR_WRITE  = 1 << 1,
    ZEN_REACTOR_ERROR  = 1 << 2,
    ZEN_REACTOR_HANGUP = 1 << 3
} ZenReactorEvents;

/* Reactor Lifecycle */
void ZenReactor_init(void);
void ZenReactor_shutdown(void);
bool ZenReactor_is_running(void);

/* File Descriptor Non-Blocking Polling */
int ZenReactor_poll_fd(int fd, int events, double timeout_sec);

/* Non-blocking Sleep (yields fiber without blocking OS worker threads) */
void ZenReactor_sleep(double seconds);
ZenValue ZenReactor_sleep_val(ZenValue seconds_val);

#endif /* ZEN_REACTOR_H */
