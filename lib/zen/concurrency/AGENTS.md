# Purpose

The Zenlang Concurrency and Task subsystem. Provides first-class channel message passing, cooperative fibers, task lifecycle management, multi-channel `select` multiplexing, synchronization primitives (`WaitGroup`, `Mutex`, `Atomic`, `Barrier`, `Semaphore`, `Once`), and worker task pools across interpreted and native targets.

# Ownership

Standard library maintainers and language concurrency team.

# Local Contracts

- **FIFO Channels (`channel.zl`)**: Supports unbuffered (rendezvous) and buffered queues with safe closure, non-blocking `try_send`/`try_receive`, and multiplexed `select()`.
- **Unified Task Model (`task.zl`)**: Encapsulates asynchronous task lifecycle (`spawn`, `wait`/`await`, `all`, `race`, `cancel`, `timeout`) and bounded `TaskPool` worker queues.
- **Synchronization Primitives (`sync.zl`)**: Provides `WaitGroup` for count coordination, `Mutex` with `with_lock`, `Atomic` with compare-and-swap (`CAS`), `Barrier` for multi-party synchronization, counting `Semaphore`, and `Once` execution guards.
- **Cooperative Fibers (`fiber.zl`)**: Lightweight resumable coroutines with explicit `yield`/`resume` and a cooperative round-robin `Scheduler`.
- **Dual-Path Execution**: Pure Zenlang map-based structures that execute identically under both AST interpreter and native AOT compiled binaries (`-g`).

# Work Guidance

- Prefer `concurrency.*` canonical imports (`zen.concurrency.channel`, `zen.concurrency.task`, `zen.concurrency.sync`, `zen.concurrency.fiber`).
- All exported functions must have `/! ... !/` documentation headers.
- Never block the entire OS process in cooperative tasks; use non-blocking status checks or cooperative sleep spins.

# Verification

- Unit tests: `python3 bootstrap/Zen.py tests/lib/test_concurrency.zl`
- Native compilation: `python3 bootstrap/Zen.py -g tests/lib/test_concurrency.zl`
- Suite runner: `./scripts/zen test-lib` and `./scripts/zen test-lib-native`

# Child DOX Index

- channel.zl: FIFO channel queues, try operations, drain, and multi-channel select multiplexer
- task.zl: Task creation, spawning, await, fan-out all/race, sleep, and TaskPool worker queues
- sync.zl: WaitGroup, Mutex, Atomic integer/boolean, Barrier, Semaphore, and Once guards
- fiber.zl: Resumable Fiber coroutines, yield/resume, and round-robin cooperative Scheduler
- concurrency.zl: Package root entry and canonical public re-exports
