# ZenLang: Official Language Reference

## 1. Introduction & Philosophy

Zenlang is a modern, optionally typed programming language designed for clarity, flexibility, and rapid development. It abandons historical baggage (like monolithic `print` statements, fragmented async/thread models, and unstructured strings) in favor of structured intent, unified execution models, and visual data flow.

**Core Directives:**
* **Visual Data Flow:** Assignment (`->`) and return (`<-`) operators make the movement of data instantly readable.
* **Everything is a Task:** Concurrency is unified. No `async`/`await` virality. Just suspendable tasks.
* **Output is a Stream, Not a Primitive:** `print` is legacy. Output is routed through environment-aware streams (`out`).
* **Semantic Text:** Strings aren't just byte arrays; text has structure (`Glyph`, `Word`, `Sentence`).
* **Dual Execution:** Run dynamically (`.zs` scripts) or compile ahead-of-time (`.zl` binaries) sharing the same runtime bridge.

---

## 2. Variables, Values & Assignment

Zenlang strictly separates mutable from immutable state and handles empty/default states gracefully without the billion-dollar `null` mistake.

### 2.1 Mutability
* `let` defines a **mutable** variable.
* `set` defines a **constant** (immutable).

### 2.2 Assignment & Type Inference
You can explicitly type variables (`:`), infer them (`:>`), or infer the underlying type while keeping it wrapped in a `Variant` (`->`).

```zl
let count : Integer -> 10     // Explicit typing
set PI : Decimal -> 3.14159   // Explicit constant
let name :> `Alice`           // Locked to inferred type (String)
let health -> 100             // Variant inferred as Integer
```

### 2.3 Special Values (`Nothing` and `Default`)
To avoid null-pointer exceptions, ZenLang provides `Nothing` (no value) and `Default` (the type's zero-state).

```zl
let score : Integer -> Nothing // Explicitly has no value
let lives : Integer -> Default // Evaluates to 0
let flags : Vector -> Default  // Evaluates to []
```

---

## 3. The Type System & Literals

Zenlang’s type system is granular, allowing optimization where needed, while remaining scriptable.

### 3.1 Base Types
* **Primitives:** `Void`, `Variant`, `Boolean` (`True`/`False`)
* **Numbers:** `Integer[8|16|32|64]`, `Decimal[32|64]`, `Number` (Abstract)
* **Text:** `String[8|16|32]` (UTF-32 default)

### 3.2 Collection Types & Literals
Collections have explicit literal syntaxes for clarity. They can be fully written out or abbreviated.

```zl
// Vectors (Static Array, fixed type)
let v :> [Vector]{1, 2, 3}
let v :> [V]{1, 2, 3}

// Lists (Dynamic Array)
let l :> [List]{1, `a`, True}

// Sets (Unique values)
let s :> [Set]{1, 2, 3}

// Tuples (Fixed size, ordered, can be named)
let t :> [Tuple]{1, 2, 3}
let t :> [T]{ x -> 10, y -> 20 }

// Maps (Key-Value)
let m :> [Map]{ `name` -> `Alice`, `age` -> 30 }
let m :> [M]{ `name` -> `Alice`, `age` -> 30 }
```

### 3.3 Semantic Textual Types
ZenLang treats text as semantic structures, allowing rich text-manipulation APIs built natively over the `String` type.

* **Glyph (`[G]`)**: A single Unicode character.
* **Word (`[W]`)**: A sequence of Glyphs.
* **Sentence (`[S]`)**: Words separated by spaces.
* **Paragraph (`[P]`)**: Sentences.
* **Chapter (`[C]`)**: Paragraphs.
* **Book (`[B]`)**: Chapters.

```zl
let w : Word -> [W]`Hello`
w[0] -> [G]`J` // Changes Word to "Jello"

let p : Paragraph -> [P]`
This is a test.
It is very cool.
`
```

---

## 4. Unified Concurrency: The Task

ZenLang fixes the fragmented `async`/`await`/`thread` model by reducing it to a single concept: **The Task**. A task runs until it needs to wait; the runtime handles the rest. Internally, all tasks are fibers multiplexed onto threads.

### 4.1 Declaring & Running Tasks
Tasks are implicitly suspendable. You do not use `async` or `await`.

```zl
task fetch_user : String (id: Integer) {
    let data -> net.get(f`/user/{id}`)
    <- data
}

function main {
    // Suspend current task and wait for result (Does NOT block OS thread)
    let user -> fetch_user(42).wait

    // Fire-and-forget (Returns a handle/future)
    let handle -> fetch_user(10).spawn
}
```

### 4.2 Threading & Advanced Control (Optional)
Threads are resources, not logic units. You only specify them when necessary.

```zl
// Pin to a CPU thread
task[cpu] crunch_numbers { ... }

// Run in a parallel pool
pool[parallel] {
    crunch_numbers().spawn
}
```

### 4.3 Structured Concurrency & Channels
Tasks cannot outlive their parent. Channels provide safe cross-task communication.

```zl
channel Message

task producer(ch) { ch.send(`Ping`) }
task consumer(ch) { write(ch.receive) }
```

---

## 5. Control Flow & Error Handling

### 5.1 Conditionals (`when`) and Loops (`do`)
```zl
// Conditional
when status == 200 { out.write(`OK`) } or { out.write(`Error`) }

// Loops
do while x < 10 { x++ }
do for item in [L]{1, 2, 3} { ... }
```

### 5.2 Error Triad (`^`, `?`, `!`)
Errors are task failures managed through explicit symbols.

* **`^` (Raise):** Immediately return an Error variant.
* **`?` (Check):** Unwraps a value or handles the error.
* **`!` (Assert):** Halts if a condition is false.

```zl
function divide(a: Decimal, b: Decimal) : [Decimal, Error] {
    when b == 0 { ^ `DivisionByZero` }
    <- a / b
}

// Fallback to 0 if error occurs
let result -> ? divide(10, 0) or 0
```

---

## 6. The Output System (Goodbye `print`)

`print` is a legacy primitive. ZenLang uses a structured, environment-aware `out` stream. Output is a capability routed by the runtime (Terminal, Log, File, or UI).

```zl
// Standard writing
out.write(`Player {name} has {hp} HP`, { name -> `Alice`, hp -> 100 })

// Semantic Channels
out.info(`Server started`)
out.error(`Connection failed`)
out.debug(state)

// Buffered Output (Ideal for TUIs/Games)
let buffer -> out.buffer()
buffer.write(`Loading...`)
buffer.flush()
```

---

## 7. Modules & Dependency Management

ZenLang uses a hierarchical resolution system capable of Tree Shaking (Dead Code Elimination). 

* **`include`**: Dumb copy-paste (useful for raw text/macros).
* **`import`**: Semantic dependency graph resolution.

```zl
import zen.io
from zen.io import out as logger
from text.columns import *

logger.write(`Ready.`)
```

*Note: The standard library uses a bridging mechanism (`native` or `extern`) to connect interpreted/compiled standard code to the C/Rust runtime.*

---

## 8. Standard Library Highlights

ZenLang's standard library is built for modern scripting and systems programming.

### 8.1 Time as a Primitive
Durations are first-class primitives, avoiding "magic number" millisecond bugs.
```zl
let delay : Duration -> 500.ms
let timeout -> 2.hours

time.sleep(250.ms)
```

### 8.2 Processes & Piping
Unix philosophy built into the language.
```zl
process.spawn("ps aux")
    .pipe("grep zen")
    .run()
```

### 8.3 "Dumb but Honest" Data Formats
Built-in support for simple, human-readable data logic without dependency hell.
```zl
from formats import sexpressions as sexp
from formats import logformat as logfmt

let config -> sexp.parse(`config.sexp`)
let row -> logfmt.parse(`time=2026-01-04 level=error msg="bad pass"`)
```

### 8.4 Terminal & Geometry Primitives
First-class support for TUIs and graphical bounds.
```zl
let rect -> geometry.rectangle(0, 0, 100, 100)

term.alt_screen {
    term.move(10, 5)
    term.color(fg -> green)
    out.write(`UI Loaded`)
}
```