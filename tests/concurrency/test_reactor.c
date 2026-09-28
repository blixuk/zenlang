#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include "concurrency/zen_task.h"
#include "concurrency/zen_reactor.h"

static double get_time(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static ZenValue blocking_compute(ZenValue arg) {
    // Simulate a blocking C-FFI / foreign library call
    usleep(25000); // 25ms
    int val = (arg.type == ZEN_INTEGER) ? (int)arg.as.integer : 0;
    return ZenValue_make_integer(val * 2);
}

int main(void) {
    printf("[Test] Starting Reactor & Blocking Pool C Tests...\n");
    ZenTaskEngine_init();
    ZenReactor_init();

    // 1. Non-blocking sleep test
    double t0 = get_time();
    ZenReactor_sleep(0.05); // 50ms
    double elapsed = get_time() - t0;
    assert(elapsed >= 0.045 && elapsed < 0.2);
    printf("  [OK] ZenReactor_sleep(0.05) took %.4f seconds\n", elapsed);

    // 2. Non-blocking poll_fd test with pipe
    int fds[2];
    assert(pipe(fds) == 0);
    int flags = fcntl(fds[0], F_GETFL, 0);
    fcntl(fds[0], F_SETFL, flags | O_NONBLOCK);

    // Should timeout when empty
    int res = ZenReactor_poll_fd(fds[0], ZEN_REACTOR_READ, 0.02);
    assert(res == 0); // Timeout
    printf("  [OK] ZenReactor_poll_fd timeout on empty pipe verified\n");

    // Write data into pipe
    char byte = 'Z';
    assert(write(fds[1], &byte, 1) == 1);

    // Should detect readiness immediately
    res = ZenReactor_poll_fd(fds[0], ZEN_REACTOR_READ, 0.2);
    assert(res & ZEN_REACTOR_READ);
    char read_buf = 0;
    assert(read(fds[0], &read_buf, 1) == 1);
    assert(read_buf == 'Z');
    close(fds[0]);
    close(fds[1]);
    printf("  [OK] ZenReactor_poll_fd readiness event verified\n");

    // 3. Dedicated Blocking Pool test
    printf("  [Test] Spawning 10 parallel blocking tasks...\n");
    ZenTaskHandle* tasks[10];
    t0 = get_time();
    for (int i = 0; i < 10; i++) {
        tasks[i] = ZenTask_spawn_blocking(ZenValue_from_function((void*)blocking_compute), ZenValue_make_integer(i + 1));
        assert(tasks[i] != NULL);
    }

    for (int i = 0; i < 10; i++) {
        ZenValue ret = ZenTask_wait(tasks[i]);
        assert(ret.type == ZEN_INTEGER);
        assert(ret.as.integer == (i + 1) * 2);
        ZenValue_release(ZenValue_from_task(tasks[i]));
    }
    elapsed = get_time() - t0;
    printf("  [OK] 10 blocking tasks (25ms each) finished in %.4f seconds (parallel)\n", elapsed);
    assert(elapsed < 0.20); // Must be much faster than sequential (250ms)

    ZenReactor_shutdown();
    ZenTaskEngine_shutdown();
    printf("[SUCCESS] All Reactor & Blocking Pool C tests passed!\n");
    return 0;
}
