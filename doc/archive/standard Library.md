
# ZenLang Standard / Core Library Ideas


## PPM simple graphic's library

Structured Text as a First-Class Concept (Not “Just Strings”)
Line-Oriented Streams (lines)
Most languages treat text as blobs. Unix treats it as lines.

```
let line -> in.read.line(0, `log.txt`)
let lines -> in.read.lines(`log.txt`)

do for line in lines {
    when line.contains(`ERROR`) {
        out.write(line)
    }
}

stream lines(`log.txt`) {
    when line.matches(`^WARN`) {
        emit warning(line)
    }
}
```

This enables:
- Streaming processing
- Zero buffering by default
- Pipe-friendly semantics

## Columns / Fields (AWK without AWK)
A simple delimiter-based record parser:

```
import text.columns

let rows -> columns(`data.csv`, `,`)

do for row in rows {
    let price -> row[3].to_float()
}
```

No CSV spec hell. No RFCs. Just:
- delimiter
- escape rules optional
- predictable behavior

This replaces:
- 80% of CSV libraries
- Most AWK scripts
- Many ad-hoc parsers

## “Dumb but Honest” Data Formats

S-Expressions as a Built-In Data Type
S-expressions are criminally underused outside Lisp.

```
(
  server
    (port 8080)
    (root "/var/www")
)
```

Why this matters:
- Trivially parsed
- Trivially serialized
- Round-trippable
- Human editable


```
from formats import sexpressions as sexp

let config -> sexp.parse(`config.sexp`)
```

This avoids:
- JSON edge cases
- YAML ambiguity
- TOML complexity

## Other Formats to Include

- JSON
- CSV
- Markdown
- HTML
- XML
- SVG

## Tagged Lines (Log-Native Data)

A format designed for logs, not config files:

```
time=2026-01-04 level=error user=42 msg=`bad password`
```

```
from formats import logformat as logfmt

let entry -> logfmt.parse(line)
```

This aligns with:
- systemd logs
- Heroku logs
- Modern observability stacks

## Explicit Time as a Value (Not a Mess)

Duration as a Primitive

Not a number. Not a float. A real type.

```
let timeout: Duration -> 500.ms
let timeout: Duration -> 500.miliseconds
let delay -> 2.s
let delay -> 2.seconds
let delay -> 2.m
let delay -> 2.minutes
let delay -> 2.h
let delay -> 2.hours
let delay -> 2.d
let delay -> 2.days
```

```
sleep(250.ms)
retry(3.times, 100.ms)
```

This avoids:
- Unit confusion
- Magic constants
- Time math bugs

## Time

```
let start -> time.monotonic()
let start -> time.wallclock()

time.now()

time.sleep(...)


```

## Explicit Processes, Pipes, and Files

Processes as Values

```
let p -> process.spawn("ls", ["-la"])
let output -> p.stdout.read()

```

```
process("ps aux")
    .pipe("grep zen")
    .pipe("sort -k3")
    .run()

```

No shell required. No string parsing.

Built-in "Piping" Primitive: Instead of just having a pipe operator |, include a stream module that treats every data source (files, sockets, arrays) as a uniform iterator.

## First-Class Environment Access
A 'sh' or 'env' module that makes interacting with shell environment variables and system paths feel like interacting with a native dictionary, but with strict type-safety.

## Zero-Config Serialization
A zen format (simpler than JSON) built into the core that allows for "instant-save" of any data structure to a flat file, facilitating the Unix "everything is a text stream" concept.

Maybe something like Godot's resource system?

Should be able to save any data structure to a file and load it back.
Should be able to handle large files for data persistence and databases.

## File Descriptors as First-Class

Not hidden streams. Explicit handles.

```
let fd -> file.open(`data.bin`, `rb`)
let bytes -> fd.read(512)
```

## Binary Data Without Apology

Byte Arrays and Views

```
let buf -> bytes(1024)
buf[0] -> 0xFF
buf[0:10]
buf.slice(0, 10)
let header -> buf[0..15]
```

This supports:
- Protocols
- Image formats
- Binary parsing
- Embedded systems

## Struct Packing / Unpacking

No reflection. No magic. Declarative layout.

```
let header -> binary.read(fd, {
    magic: u32,
    version: u16,
    flags: u16
})
```

## Minimal Geometry

Rectangles, Points, Sizes

```
let rect -> geometry.rectangle(0, 0, 100, 100)
let point -> geometry.point(10, 20)
let size -> geometry.size(100, 100)

structure Point { x: Integer, y: Integer }
structure Rect  { x, y, w, h }

```

Used everywhere:
- UI
- Graphics
- Collision
- Layout

Small, universal, and boring—in a good way.

## Terminal-Native UI Primitives

Cursor, Color, and Screen Control

```
term.clear()
term.move(10, 5)
term.color(fg->green, bg->black)
out.write(`Hello`)
term.reset()
```

Alternate Screen Buffer. Clean entry/exit. No terminal corruption.

```
term.alt_screen {
    run_app()
}
```

## Observability as a Core Concept

Structured Logging (Not print)

```
log.info(`User logged in`, { user_id: 42 })

log.info(`user_login`, {
    user: id,
    ip: addr
})

```

Outputs logfmt or JSON depending on environment.

## Tracing Without a Framework

```
trace(`db.query`) {
    run_query()
}

```

```
trace.span(`my_operation`) {
    do_something()
}
```

This produces:
- Duration
- Nesting
- Correlation IDs

## Deterministic Randomness

```
let rng -> random.seed(42)
let num -> rng.next()

let int -> random.integer(1, 10)
let dec -> random.decimal(0.0, 1.0)

let int -> random.range(1, 10)
let dec -> random.range(0.0, 1.0)
```

Critical for:
- Games
- Simulations
- Testing

## ZenDoc (Zen Documentation Format)

This could be a great addition to Zenlang, it would allow for easy documentation of code in comments and allow for writing documentation in a structured way.

```

```

## ZenMark (Zen Markup Language)

This could be a great addition to Zenlang, it would allow for easy writing in a structured way.

```

```



## Stack

## Queue

## Database

## ECS (Entity Component System)

## State Machine

## MVC (Model-View-Controller)

