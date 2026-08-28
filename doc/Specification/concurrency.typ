#import "template.typ": *

= Concurrency & Asynchronous Task Model

Zenlang provides a unified concurrency model optimized for responsive terminal user interfaces, background task execution, and asynchronous networked services.

== Core Concurrency Guarantees

1. *Deterministic Visual Data Flow*: Concurrency flows follow the explicit `->` (spawn/bind) and `<-` (await/return) mechanics.
2. *By-Value Isolation*: Variable state captured across tasks or closures is snapshotted by value, preventing race conditions and shared mutable memory corruption.
3. *Cooperative Event Polling*: Non-blocking event polling enables sub-millisecond redraw responsiveness in interactive terminal apps without heavy thread synchronization.
4. *Process Multitasking*: Integration with operating system process pipelines (`zen.sys.process`) enables parallel execution across Unix processes.

== Task Spawning & Await

Tasks represent lightweight asynchronous units of computation:

#feature(
    "Task Spawning & Await",
    "let task -> spawn function() { ... }\nlet output -> await task",
    "// Spawn background task\nlet worker -> spawn function() {\n    let data -> fetch_remote_resource()\n    <- data\n}\n\n// Await completion\nlet result -> await worker"
)

== Cooperative Terminal Polling

For high-performance 60 FPS terminal applications:

```zl
use zen.sys.term as term

// Poll for keyboard events without blocking the render loop
let key -> term.poll_key(16) // 16ms polling window
when key.kind != `none` {
    handle_player_input(key)
}
update_game_physics()
render_frame_buffer()
```

== OS Process Pipelines

High-throughput stream processing across Unix processes:

```zl
use zen.sys.process as process

let p -> process.Pipeline(`cat`, [`access.log`])
p.pipe(`grep`, [`ERROR`])
p.pipe(`wc`, [`-l`])

let total_errors -> p.run()
```
