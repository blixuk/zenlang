
**unified concurrency substrate** with *progressive disclosure*: one mental model at the surface, deeper control only when explicitly requested.

**language-level design**
---

## 1. Reframing the Problem

The mistake most languages make is treating:

* async
* coroutines
* fibers
* threads
* futures

as *separate concepts*

In reality, they are **different views of the same thing**:

> *A unit of execution that may suspend, resume, and eventually produce a value.*

So the correct abstraction is not “async” or “fiber” or “thread”.

### The correct abstraction is:

## **A Task**

---

## 2. The Core Abstraction: `task`

In ZenLang, everything concurrent is a **task**.

A `task`:

* Executes code
* May suspend
* May resume on a different thread
* May produce a value
* May fail
* Is scheduled by the runtime

### This single abstraction:

* **Feels like async** to users
* **Runs on fibers** in the runtime
* **Maps to threads** when needed
* **Returns futures** implicitly

---

## 3. Mental Model (User-Facing)

### Basic Rule

> “A task runs until it needs to wait, then the runtime handles the rest.”

The user does **not** think in threads, fibers, or event loops.

They think:

* “Run this”
* “Wait for this”
* “Get the result”

---

## 4. Syntax Proposal (ZenLang-style)

### 4.1 Declaring a Task

```

// Keyword Identifier : ReturnType ( Parameters ) { Statements }

task fetch_user : User (id: Integer) {
    data -> net.get("/user/" + id)
    <- parse_user(data)
}
```

No `async`.
No `await`.

A `task` is **implicitly suspendable**.

---

### 4.2 Waiting for a Task

```
let user -> fetch_user(42).wait
```

`wait`:

* Suspends the *current task*
* Does **not block the OS thread**
* Runtime resumes when ready

This maps directly to:

* `await`
* `yield`
* `future.get()`

But without exposing those concepts.

---

### 4.3 Fire-and-Forget

```zen
task log_event(event)
```

or explicitly:

```
log_event(event).spawn
```

---

## 5. Futures Without Saying “Future”

Every `task` **is** a future.

You do not expose a `Future<T>` type unless advanced users want it.

### Advanced Use (Optional)

```
let handle -> fetch_user(42).spawn
...
let user -> handle.wait
```

---

## 6. Structured Concurrency (Built-In)

ZenLang should enforce **task lifetimes**.

```
task handle_request {
    with task_group {
        a -> load_profile().spwan
        b -> load_inventory().spawn
        <- merge(a.wait, b.wait)
    }
}

write(handle_request().result)
```

Rules:

* Tasks cannot outlive their parent unless explicitly detached
* Failures propagate deterministically
* No orphaned work

---

## 7. How Threads Fit (Advanced Layer)

Threads are **execution resources**, not logic units.

Expose them *only when required*:

```
task[cpu] heavy_compute {
    <- crunch_numbers()
}
```

```
// Parallel (Hardware Thread)
task[parallel] heavy_compute {
    <- crunch_numbers()
}
```

Or:

```
pool[cpu] {
    heavy_compute().spawn
}
```

```
pool[parallel] {
    heavy_compute().spawn
}
```

The runtime decides:

* Which OS thread
* When to migrate
* How to schedule

---

## 8. Fibers (Completely Hidden)

Internally:

* Every task is a **fiber**
* Fibers are multiplexed onto threads
* Fibers suspend on:

  * I/O
  * Timers
  * Task waits
  * Channels

The user never sees:

* Stack switching
* Yield points
* Context switching

---

## 9. Channels & Messaging (Optional but Powerful)

For advanced concurrency:

```
channel Message

task producer(ch) {
    ch.send(`hello`)
}

task consumer(ch) {
    let msg -> ch.receive
}
```

Channels:

* Suspend tasks, not threads
* Integrate with the scheduler
* Work across threads

---

## 10. Error Handling (Critical)

Errors are **task failures**, not exceptions in a vacuum.

```
task risky {
    raise `network error`
}

task main {
    try {
        result -> risky().wait 
    } catch {
        <- default_value
    }
}
```

Failures:

* Propagate through task trees
* Can be caught at boundaries
* Cancel sibling tasks if desired

---

## 11. Cancellation (First-Class)

```zen
handle = long_task().spawn
...
handle.cancel
```

Cancellation:

* Cooperative
* Deterministic
* Propagates downward

---

## 12. The Runtime Model (Hidden but Clean)

Internally ZenLang has:

* **Task Scheduler**
* **Fiber Pool**
* **Event Loop**
* **Thread Pools**
* **I/O Reactor**
* **Timer Wheel**

But users interact with:

* `task`
* `spawn`
* `wait`
* `channel`

---

## 13. Why This Is Better Than `async/await`

| Problem                  | Traditional Async | Zen Task Model |
| ------------------------ | ----------------- | -------------- |
| Viral async              | Yes               | No             |
| Blocking vs non-blocking | Confusing         | Impossible     |
| Threads                  | Exposed           | Optional       |
| Futures                  | Explicit          | Implicit       |
| Cancellation             | Manual            | Built-in       |
| Game loops               | Awkward           | Natural        |

---

## 14. Naming Philosophy (Very Important)

Avoid:

* `async`
* `await`
* `promise`
* `future`

These are implementation details.

Use:

* `task`
* `spawn`
* `wait`
* `group`
* `channel`

These describe **intent**, not mechanism.

---

## 15. One-Sentence ZenLang Concurrency Philosophy

> **ZenLang has one unit of concurrency: the task.
> Tasks suspend, resume, and return values.
> The runtime decides how.**

---