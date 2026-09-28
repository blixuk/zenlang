#include "zen_reactor.h"
#include "zen_task.h"
#include "../memory/zen_memory.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <time.h>

#if defined(__linux__)
#include <sys/epoll.h>
#define HAS_EPOLL 1
#elif defined(__APPLE__) || defined(__FreeBSD__) || defined(__OpenBSD__)
#include <sys/event.h>
#define HAS_KQUEUE 1
#else
#include <poll.h>
#define HAS_POLL 1
#endif

/* =========================================================================
 * Reactor State & Data Structures
 * ========================================================================= */

typedef struct ZenReactorTimer {
    double deadline;
    pthread_mutex_t lock;
    pthread_cond_t cond;
    bool done;
    ZenTaskHandle* task;
    struct ZenReactorTimer* next;
} ZenReactorTimer;

typedef struct ZenIOSubscriber {
    int fd;
    int events;
    int ready_events;
    pthread_mutex_t lock;
    pthread_cond_t cond;
    bool done;
    struct ZenIOSubscriber* next;
} ZenIOSubscriber;

static pthread_t reactor_thread;
static pthread_mutex_t reactor_lock = PTHREAD_MUTEX_INITIALIZER;
static bool reactor_initialized = false;
static bool reactor_shutdown = false;

static int wakeup_pipe[2] = {-1, -1};
#if defined(HAS_EPOLL)
static int epoll_fd = -1;
#elif defined(HAS_KQUEUE)
static int kqueue_fd = -1;
#endif

static ZenReactorTimer* timers_head = NULL;
static ZenIOSubscriber* subscribers_head = NULL;

static double get_monotonic_time(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static void reactor_wakeup(void) {
    if (wakeup_pipe[1] >= 0) {
        char b = 1;
        ssize_t ret = write(wakeup_pipe[1], &b, 1);
        (void)ret;
    }
}

static void reactor_drain_wakeup(void) {
    if (wakeup_pipe[0] >= 0) {
        char buf[64];
        while (read(wakeup_pipe[0], buf, sizeof(buf)) > 0) {}
    }
}

static void reactor_add_fd(int fd, int events) {
#if defined(HAS_EPOLL)
    if (epoll_fd >= 0) {
        struct epoll_event ev;
        memset(&ev, 0, sizeof(ev));
        ev.events = EPOLLONESHOT;
        if (events & ZEN_REACTOR_READ) ev.events |= EPOLLIN;
        if (events & ZEN_REACTOR_WRITE) ev.events |= EPOLLOUT;
        ev.data.fd = fd;
        epoll_ctl(epoll_fd, EPOLL_CTL_ADD, fd, &ev);
    }
#elif defined(HAS_KQUEUE)
    if (kqueue_fd >= 0) {
        struct kevent kev[2];
        int n = 0;
        if (events & ZEN_REACTOR_READ) {
            EV_SET(&kev[n++], fd, EVFILT_READ, EV_ADD | EV_ONESHOT, 0, 0, NULL);
        }
        if (events & ZEN_REACTOR_WRITE) {
            EV_SET(&kev[n++], fd, EVFILT_WRITE, EV_ADD | EV_ONESHOT, 0, 0, NULL);
        }
        kevent(kqueue_fd, kev, n, NULL, 0, NULL);
    }
#endif
}

static void reactor_del_fd(int fd) {
#if defined(HAS_EPOLL)
    if (epoll_fd >= 0) {
        epoll_ctl(epoll_fd, EPOLL_CTL_DEL, fd, NULL);
    }
#elif defined(HAS_KQUEUE)
    if (kqueue_fd >= 0) {
        struct kevent kev[2];
        EV_SET(&kev[0], fd, EVFILT_READ, EV_DELETE, 0, 0, NULL);
        EV_SET(&kev[1], fd, EVFILT_WRITE, EV_DELETE, 0, 0, NULL);
        kevent(kqueue_fd, kev, 2, NULL, 0, NULL);
    }
#endif
}

/* =========================================================================
 * Background Reactor Loop (Event Polling & Timer Expiration)
 * ========================================================================= */

static void* reactor_thread_loop(void* arg) {
    (void)arg;
#if defined(HAS_EPOLL)
    struct epoll_event events[64];
#elif defined(HAS_KQUEUE)
    struct kevent events[64];
#endif

    while (1) {
        pthread_mutex_lock(&reactor_lock);
        if (reactor_shutdown) {
            pthread_mutex_unlock(&reactor_lock);
            break;
        }

        // 1. Calculate timeout until earliest timer
        double now = get_monotonic_time();
        int timeout_ms = -1; // Wait forever if no timers
        if (timers_head) {
            double diff = timers_head->deadline - now;
            if (diff <= 0.0) {
                timeout_ms = 0;
            } else {
                timeout_ms = (int)(diff * 1000.0) + 1;
            }
        }
        pthread_mutex_unlock(&reactor_lock);

        // 2. Poll kernel events
        int n = 0;
#if defined(HAS_EPOLL)
        n = epoll_wait(epoll_fd, events, 64, timeout_ms);
#elif defined(HAS_KQUEUE)
        struct timespec ts;
        struct timespec* tsp = NULL;
        if (timeout_ms >= 0) {
            ts.tv_sec = timeout_ms / 1000;
            ts.tv_nsec = (timeout_ms % 1000) * 1000000L;
            tsp = &ts;
        }
        n = kevent(kqueue_fd, NULL, 0, events, 64, tsp);
#else
        usleep(timeout_ms > 0 ? timeout_ms * 1000 : 1000);
        n = 0;
#endif

        pthread_mutex_lock(&reactor_lock);
        if (reactor_shutdown) {
            pthread_mutex_unlock(&reactor_lock);
            break;
        }

        // 3. Process expired timers
        now = get_monotonic_time();
        while (timers_head && timers_head->deadline <= now) {
            ZenReactorTimer* expired = timers_head;
            timers_head = expired->next;
            expired->next = NULL;

            pthread_mutex_lock(&expired->lock);
            expired->done = true;
            pthread_cond_broadcast(&expired->cond);
            pthread_mutex_unlock(&expired->lock);
        }

        // 4. Process I/O events
        if (n > 0) {
            for (int i = 0; i < n; i++) {
#if defined(HAS_EPOLL)
                int fd = events[i].data.fd;
                uint32_t ev = events[i].events;
                if (fd == wakeup_pipe[0]) {
                    reactor_drain_wakeup();
                    continue;
                }
                int ready = 0;
                if (ev & (EPOLLIN | EPOLLPRI)) ready |= ZEN_REACTOR_READ;
                if (ev & EPOLLOUT) ready |= ZEN_REACTOR_WRITE;
                if (ev & EPOLLERR) ready |= ZEN_REACTOR_ERROR;
                if (ev & EPOLLHUP) ready |= ZEN_REACTOR_HANGUP;
#elif defined(HAS_KQUEUE)
                int fd = (int)events[i].ident;
                if (fd == wakeup_pipe[0]) {
                    reactor_drain_wakeup();
                    continue;
                }
                int ready = 0;
                if (events[i].filter == EVFILT_READ) ready |= ZEN_REACTOR_READ;
                if (events[i].filter == EVFILT_WRITE) ready |= ZEN_REACTOR_WRITE;
                if (events[i].flags & EV_ERROR) ready |= ZEN_REACTOR_ERROR;
                if (events[i].flags & EV_EOF) ready |= ZEN_REACTOR_HANGUP;
#else
                int fd = -1; int ready = 0;
#endif
                // Notify subscriber
                ZenIOSubscriber* sub = subscribers_head;
                while (sub) {
                    if (sub->fd == fd) {
                        pthread_mutex_lock(&sub->lock);
                        sub->ready_events |= ready;
                        sub->done = true;
                        pthread_cond_broadcast(&sub->cond);
                        pthread_mutex_unlock(&sub->lock);
                        break;
                    }
                    sub = sub->next;
                }
            }
        }
        pthread_mutex_unlock(&reactor_lock);
    }
    return NULL;
}

/* =========================================================================
 * Lifecycle Management
 * ========================================================================= */

void ZenReactor_init(void) {
    if (reactor_initialized) return;

    if (pipe(wakeup_pipe) == 0) {
        int flags = fcntl(wakeup_pipe[0], F_GETFL, 0);
        fcntl(wakeup_pipe[0], F_SETFL, flags | O_NONBLOCK);
        flags = fcntl(wakeup_pipe[1], F_GETFL, 0);
        fcntl(wakeup_pipe[1], F_SETFL, flags | O_NONBLOCK);
    }

#if defined(HAS_EPOLL)
    epoll_fd = epoll_create1(EPOLL_CLOEXEC);
    if (epoll_fd >= 0 && wakeup_pipe[0] >= 0) {
        struct epoll_event ev;
        memset(&ev, 0, sizeof(ev));
        ev.events = EPOLLIN;
        ev.data.fd = wakeup_pipe[0];
        epoll_ctl(epoll_fd, EPOLL_CTL_ADD, wakeup_pipe[0], &ev);
    }
#elif defined(HAS_KQUEUE)
    kqueue_fd = kqueue();
    if (kqueue_fd >= 0 && wakeup_pipe[0] >= 0) {
        struct kevent kev;
        EV_SET(&kev, wakeup_pipe[0], EVFILT_READ, EV_ADD, 0, 0, NULL);
        kevent(kqueue_fd, &kev, 1, NULL, 0, NULL);
    }
#endif

    reactor_shutdown = false;
    pthread_create(&reactor_thread, NULL, reactor_thread_loop, NULL);
    reactor_initialized = true;
}

void ZenReactor_shutdown(void) {
    if (!reactor_initialized) return;

    pthread_mutex_lock(&reactor_lock);
    reactor_shutdown = true;
    reactor_wakeup();
    pthread_mutex_unlock(&reactor_lock);

    pthread_join(reactor_thread, NULL);

    if (wakeup_pipe[0] >= 0) { close(wakeup_pipe[0]); wakeup_pipe[0] = -1; }
    if (wakeup_pipe[1] >= 0) { close(wakeup_pipe[1]); wakeup_pipe[1] = -1; }
#if defined(HAS_EPOLL)
    if (epoll_fd >= 0) { close(epoll_fd); epoll_fd = -1; }
#elif defined(HAS_KQUEUE)
    if (kqueue_fd >= 0) { close(kqueue_fd); kqueue_fd = -1; }
#endif

    reactor_initialized = false;
}

bool ZenReactor_is_running(void) {
    return reactor_initialized && !reactor_shutdown;
}

/* =========================================================================
 * Non-blocking Sleep & I/O Polling
 * ========================================================================= */

void ZenReactor_sleep(double seconds) {
    if (seconds <= 0.0) return;
    if (!reactor_initialized) ZenReactor_init();

    ZenTaskHandle* cur_task = ZenTask_current();
    if (cur_task) {
        pthread_mutex_lock(&cur_task->lock);
        cur_task->state = TASK_WAITING_TIMER;
        pthread_mutex_unlock(&cur_task->lock);
    }

    ZenReactorTimer timer;
    timer.deadline = get_monotonic_time() + seconds;
    pthread_mutex_init(&timer.lock, NULL);
    pthread_cond_init(&timer.cond, NULL);
    timer.done = false;
    timer.task = cur_task;
    timer.next = NULL;

    pthread_mutex_lock(&reactor_lock);
    // Insert sorted by deadline
    if (!timers_head || timer.deadline < timers_head->deadline) {
        timer.next = timers_head;
        timers_head = &timer;
    } else {
        ZenReactorTimer* cur = timers_head;
        while (cur->next && cur->next->deadline <= timer.deadline) {
            cur = cur->next;
        }
        timer.next = cur->next;
        cur->next = &timer;
    }
    reactor_wakeup();
    pthread_mutex_unlock(&reactor_lock);

    pthread_mutex_lock(&timer.lock);
    while (!timer.done && !reactor_shutdown) {
        pthread_cond_wait(&timer.cond, &timer.lock);
    }
    pthread_mutex_unlock(&timer.lock);

    if (cur_task) {
        pthread_mutex_lock(&cur_task->lock);
        cur_task->state = TASK_RUNNING;
        pthread_mutex_unlock(&cur_task->lock);
    }

    pthread_mutex_destroy(&timer.lock);
    pthread_cond_destroy(&timer.cond);
}

ZenValue ZenReactor_sleep_val(ZenValue seconds_val) {
    double secs = 0.0;
    if (seconds_val.type == ZEN_INTEGER) {
        secs = (double)seconds_val.as.integer;
    } else if (seconds_val.type == ZEN_DECIMAL) {
        secs = seconds_val.as.decimal;
    }
    ZenReactor_sleep(secs);
    return (ZenValue){ .type = ZEN_NOTHING, .as.integer = 0 };
}

int ZenReactor_poll_fd(int fd, int events, double timeout_sec) {
    if (fd < 0) return -1;
    if (!reactor_initialized) ZenReactor_init();

    ZenTaskHandle* cur_task = ZenTask_current();
    if (cur_task) {
        pthread_mutex_lock(&cur_task->lock);
        cur_task->state = TASK_WAITING_IO;
        pthread_mutex_unlock(&cur_task->lock);
    }

    ZenIOSubscriber sub;
    sub.fd = fd;
    sub.events = events;
    sub.ready_events = 0;
    sub.done = false;
    pthread_mutex_init(&sub.lock, NULL);
    pthread_cond_init(&sub.cond, NULL);

    pthread_mutex_lock(&reactor_lock);
    sub.next = subscribers_head;
    subscribers_head = &sub;
    reactor_add_fd(fd, events);
    reactor_wakeup();
    pthread_mutex_unlock(&reactor_lock);

    pthread_mutex_lock(&sub.lock);
    if (timeout_sec < 0.0) {
        while (!sub.done && !reactor_shutdown) {
            pthread_cond_wait(&sub.cond, &sub.lock);
        }
    } else {
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        long sec = (long)timeout_sec;
        long nsec = (long)((timeout_sec - (double)sec) * 1e9);
        ts.tv_sec += sec;
        ts.tv_nsec += nsec;
        if (ts.tv_nsec >= 1000000000L) {
            ts.tv_sec++;
            ts.tv_nsec -= 1000000000L;
        }
        while (!sub.done && !reactor_shutdown) {
            int r = pthread_cond_timedwait(&sub.cond, &sub.lock, &ts);
            if (r == ETIMEDOUT) break;
        }
    }
    int result = sub.ready_events;
    pthread_mutex_unlock(&sub.lock);

    if (cur_task) {
        pthread_mutex_lock(&cur_task->lock);
        cur_task->state = TASK_RUNNING;
        pthread_mutex_unlock(&cur_task->lock);
    }

    pthread_mutex_lock(&reactor_lock);
    reactor_del_fd(fd);
    if (subscribers_head == &sub) {
        subscribers_head = sub.next;
    } else {
        ZenIOSubscriber* cur = subscribers_head;
        while (cur && cur->next != &sub) cur = cur->next;
        if (cur) cur->next = sub.next;
    }
    pthread_mutex_unlock(&reactor_lock);

    pthread_mutex_destroy(&sub.lock);
    pthread_cond_destroy(&sub.cond);

    return result;
}
