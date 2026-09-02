# Chapter 12: Concurrency & The Unified Task Substrate

Asynchronous programming in modern languages is notoriously fragmented. Developers are forced to navigate promises, futures, green threads, OS threads, and the contagious "Function Color Problem" (`async`/`await`).

Zenlang radically simplifies concurrency by eliminating these bifurcations in favor of a single unified model: **the `task`**.

---

## 1. The Unified Task Philosophy

In Zenlang, concurrency is an execution attribute rather than a type virus:
- There is no `async` keyword.
- There is no `await` keyword.
- All tasks are implicitly suspendable and execute as lightweight M:N runtime fibers (starting at just 4KB of stack space).

```
┌─────────────────────────────────────────────────────────────┐
│                       The Task Model                        │
│                                                             │
│   task fetch_user(id) { ... }  // Implicitly suspendable    │
│   handle -> fetch_user(42).spawn  // Dispatched in bg       │
│   user   -> handle.wait           // Non-blocking suspend   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Declaring & Running Tasks

### 2.1 The `task` Keyword
Declare concurrent work with the `task` keyword:

```zl
use zen.io
use zen.text.string as Str

task fetch_status : String (service_url: String) {
    // Non-blocking I/O suspends fiber automatically:
    io.writeln(`Pinging ` + service_url)
    <- `200 OK`
}
```

### 2.2 Dispatching Work with `.spawn` and `.wait`
- **`.spawn`**: Dispatches the task to the background runtime queue. Returns a `TaskHandle`.
- **`.wait`**: Suspends the calling task until the background task completes, retrieving its returned value without blocking any operating system thread.

```zl
function main() {
    // 1. Dispatch two tasks concurrently:
    let h1 -> fetch_status(`https://api.alpha.com`).spawn
    let h2 -> fetch_status(`https://api.beta.com`).spawn

    // 2. Perform independent local computation:
    io.writeln(`Background requests dispatched...`)

    // 3. Suspend and collect results:
    let res1 -> h1.wait
    let res2 -> h2.wait

    io.writeln(`Alpha: ` + res1)
    io.writeln(`Beta:  ` + res2)
    <- 0
}
```

---

## 3. Structured Concurrency with `with task_group`

Unbounded background tasks cause memory leaks, orphaned resources, and hard-to-debug race conditions. Zenlang guarantees safe concurrency lifetimes through **task groups**:

```zl
function process_batch(items: List) {
    with task_group as group {
        do for item in items {
            // Child tasks are owned by the group:
            process_item_task(item).spawn
        }
        // Block cannot exit until ALL child tasks finish!
    }
    // All fiber resources and memory are cleanly reclaimed here
    io.info(`All batch tasks completed cleanly`)
}
```

### Automatic Error Cancellation
If any task in a `task_group` raises an unhandled error, the group automatically and deterministically cancels all sibling tasks before unwinding.

---

## 4. Message Passing with Channels (`channel`)

Zenlang avoids shared mutable state by using typed, non-blocking channels:

```zl
use zen.io
use zen.text.string as Str

task producer(ch) {
    do for i in 1...5 {
        ch.send(`Item #` + Str.to_string(i))
    }
    ch.close()
}

task consumer(ch) {
    do while not ch.is_closed() {
        let msg -> ch.receive
        when msg != Nothing {
            io.writeln(`Received: ` + msg)
        }
    }
}

function main() {
    let ch -> channel(String)
    producer(ch).spawn
    consumer(ch).spawn
    <- 0
}
```

---

## 5. Dedicated Hardware Threads (`task[parallel]`)

For CPU-intensive numerical processing, video rendering, or cryptography, tasks can request true multi-core OS thread execution:

```zl
task[parallel] compute_sha256 : Bytes (payload: Bytes) {
    // Executes on dedicated OS worker thread pool:
    <- crypto.sha256(payload)
}
```

---

## 6. Lazy Generators (`yield` / `<~`)

Functions and tasks can stream items lazily one at a time using `yield` (`<~`):

```zl
function fibonacci_stream() {
    let a -> 0
    let b -> 1
    do while True {
        <~ a // Yields next value to consumer
        let temp -> a + b
        a -> b
        b -> temp
    }
}

function main() {
    let stream -> fibonacci_stream()
    do for i in 1...10 {
        io.writeln(`Fib: ` + Str.to_string(stream.next()))
    }
    <- 0
}
```

---

## 💡 Chapter Exercises

1. Create a `task download_file(url: String)` that simulates a network request and returns a string message.
2. Use a `task_group` to download 3 files in parallel and print when all three have finished.
3. Build a pipeline with a producer task generating numbers 1 to 20, and a consumer task printing only even numbers.
