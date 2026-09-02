# The Unified Task Concurrency Substrate

| Attribute | Value |
|:---|:---|
| **Role** | Concurrency Architecture & Task Programming Guide |
| **Authority** | Canonical Reference for Zenlang Concurrency & Tasks |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Executive Summary

Zenlang resolves the historical complexity of asynchronous programming by rejecting the "Function Color Problem" (`async`/`await` infection) and eliminating the confusing fragmentation between promises, futures, coroutines, fibers, and threads.

Instead, Zenlang provides a single, unified execution abstraction: **the `task`**.

> **"A task is a unit of execution that runs until it needs to wait. The runtime handles the rest."**

```
┌───────────────────────────────────────────────────────────────┐
│                     USER INTENT LAYER                         │
│   task fetch_user(id) { ... }                                 │
│   handle -> fetch_user(42).spawn                              │
│   user   -> handle.wait                                       │
└───────────────────────────────┬───────────────────────────────┘
                                │
               Runtime Progressive Scheduling
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                 M:N RUNTIME FIBER SUBSTRATE                   │
│   - Lightweight stackful fibers (starts at 4KB)               │
│   - Non-blocking I/O event reactor & timer wheel              │
│   - Multiplexed automatically across hardware worker threads  │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Core Mechanics

### 2.1 Declaring a Task (`task`)
A `task` is declared with the `task` keyword. It is **implicitly suspendable** without requiring `async` annotations:

```zl
task fetch_remote_profile : Profile (user_id: Integer) {
    let raw_json -> net.get(`https://api.example.com/users/` + Str.to_string(user_id))
    <- json.parse(raw_json) <: Profile
}
```

### 2.2 Intent Methods: `.spawn` and `.wait`

| Method | Role | Description |
|:---|:---|:---|
| **`.spawn`** | Dispatch | Begins execution concurrently in the background; returns a `TaskHandle`. |
| **`.wait`**  | Suspend & Retrieve | Suspends the calling task until the target completes; yields the return value. |

```zl
function load_dashboard() {
    // 1. Dispatch background work concurrently:
    let profile_h   -> fetch_remote_profile(101).spawn
    let inventory_h -> fetch_inventory(101).spawn

    // 2. Perform independent local computation:
    prepare_canvas()

    // 3. Suspend and retrieve results (never blocks OS thread):
    let profile   -> profile_h.wait
    let inventory -> inventory_h.wait

    render(profile, inventory)
}
```

---

## 3. Structured Concurrency (`with task_group`)

Uncontrolled background tasks cause resource leaks and orphaned processes. Zenlang enforces **task scoping** through `with task_group`:

```zl
task handle_http_request : Response (req: Request) {
    with task_group as group {
        let auth_h -> authenticate(req.token).spawn
        let data_h -> load_data(req.query).spawn

        // Both tasks must complete before exiting this block:
        let auth -> auth_h.wait
        when not auth.is_valid {
            ^ `UnauthorizedError`
        }

        <- Response{ status -> 200, body -> data_h.wait }
    } 
    // If any error is raised or the block exits, all remaining child tasks
    // within `group` are automatically and deterministically cancelled!
}
```

### Invariants of Structured Concurrency:
1. **Lifetime Containment:** A spawned task cannot outlive its parent task group unless explicitly detached.
2. **Deterministic Cancellation:** When a task group encounters an unhandled error, all sibling tasks are cancelled immediately.
3. **No Zombie Fibers:** The runtime guarantees zero orphaned fiber leaks.

---

## 4. Channels & Message Passing (`channel`)

Tasks share data through typed, non-blocking channels rather than shared mutable memory:

```zl
use zen.io
use zen.text.string as Str

task data_producer(out_ch) {
    do for i in 1...10 {
        out_ch.send(`Message ` + Str.to_string(i))
    }
    out_ch.close()
}

task data_consumer(in_ch) {
    do while not in_ch.is_closed() {
        let msg -> in_ch.receive // Suspends fiber until data is available
        when msg != Nothing {
            io.writeln(`Received: ` + msg)
        }
    }
}

function main() {
    let ch -> channel(String)
    data_producer(ch).spawn
    data_consumer(ch).spawn
    <- 0
}
```

---

## 5. Progressive Hardware Disclosure (`task[parallel]`)

For compute-heavy algorithms (scientific simulations, video rendering, cryptography), tasks can explicitly request dedicated OS worker threads:

```zl
// Dedicated hardware thread pool dispatch:
task[parallel] compute_monte_carlo : Decimal (iterations: Integer) {
    let hits -> 0
    do for i in 1...iterations {
        when random_hit() { hits++ }
    }
    <- (hits <: Decimal) / (iterations <: Decimal) * 4.0
}
```

---

## 6. Cooperative Cancellation

Every task handle exposes a cooperative cancellation mechanism:

```zl
let monitor -> start_sensor_polling().spawn

// Cancel when no longer required:
monitor.cancel()

when monitor.is_cancelled() {
    io.warn(`Sensor polling aborted.`)
}
```

---

## 7. Comparison: Traditional Async vs. Zenlang Task Model

| Aspect | Traditional Async/Await (JS, Python, Rust) | Zenlang Unified Task Model |
|:---|:---|:---|
| **Function Color** | Contagious (`async` infects all callers) | **Colorless** (`task` is unified) |
| **Blocking vs Non-blocking** | Error-prone (`sleep` vs `async_sleep`) | **Impossible to block the OS thread** |
| **Orphaned Tasks** | Frequent background leaks | **Guaranteed by `with task_group`** |
| **Threads Exposure** | Leaky abstraction | **Progressive disclosure (`task[parallel]`)** |
| **Execution Primitives** | Divided into Promise, Future, Thread | **One primitive: `task`** |
