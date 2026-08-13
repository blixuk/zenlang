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
To avoid null-pointer exceptions, ZenLang provides **`Nothing`** (no value) and **`Default`** (the type's zero-state). Both are **required language surface** (capitalized like type names). You may assign them and compare with `==` the same way.

```zl
let score : Integer -> Nothing // Explicitly has no value
let lives : Integer -> Default // Evaluates to 0
let flags : List    -> Default // Evaluates to []
let name  : String  -> Default // Evaluates to ``

when score == Nothing { /* absent */ }
when lives == Default { /* zero for Integer */ }
when flags == Default { /* empty list */ }
// Nothing ≠ Default: 0 is Default for Integer, not Nothing
```

**Status:** `Nothing` works today (prefer capital `Nothing` over legacy `nothing`). `Default` is specified here and tracked as **required** endgame work ([selfhost/ENDGAME_PLAN.md](../selfhost/ENDGAME_PLAN.md) Phase L); not fully implemented in the host yet.

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

## 3.4 Ranges (`..` and `..=`)

Range operators build **lists** of integers or single-character strings. Both directions work (ascending and descending).

| Syntax | Meaning | Example result |
|--------|---------|----------------|
| `a..b` | Half-open (start inclusive, end exclusive) | `0..5` → `[0,1,2,3,4]` |
| `a..=b` | Closed (start and end inclusive) | `0..=5` → `[0,1,2,3,4,5]` |
| empty exclusive | `n..n` | `[]` |
| singleton inclusive | `n..=n` | `[n]` |

```zl
// Integers
let xs -> 0..5              // [0, 1, 2, 3, 4]
let ys -> 0..=5             // [0, 1, 2, 3, 4, 5]
let down -> 5..2            // [5, 4, 3]
let down_i -> 5..=2         // [5, 4, 3, 2]

// Characters (single-character strings)
let letters -> `a`..=`z`    // [`a`, `b`, …, `z`]
let few -> `a`..`d`         // [`a`, `b`, `c`]

// Loops
do for i in 1..=4 {
    // i = 1, 2, 3, 4
}

// Indexing / length work like any List
let r -> 10..15
// r.length == 5, r[0] == 10, r[4] == 14
```

**Semantics:**
- Result type is always a **List**.
- Integer operands → `List` of integers; single-character strings → `List` of strings.
- Descending ranges step by −1 when start > end.

**Design notes:**
- Prefer **`..` / `..=`** over `...` — triple-dot is already **rest/spread** in patterns (`[first, ...rest]`).
- Character ranges use single-character strings (ASCII code points in the native backend today).
- Library helpers in `zen.math.range`: `range(start, end)` and `range_inclusive(start, end)` (integers; operators are preferred for new code).

---

## 3.5 Anonymous Functions (Lambdas)

Zenlang anonymous functions use the `function` keyword as a value expression (not a separate `lambda` keyword).

```zl
// Assigned
let double -> function(x) { <- x * 2 }
let add -> function(a, b) { <- a + b }

// Inline as a callback (stdlib style)
let doubled -> list.map(numbers, function(x) { <- x * 2 })
let sum -> list.reduce(numbers, 0, function(acc, x) { <- acc + x })
```

**Semantics today (bootstrap / native):**

| Feature | Status |
|---------|--------|
| `function(params) { body }` as a first-class value | Supported |
| Pass to HOFs (`map` / `filter` / `reduce` / `find`) | Supported (native via `ZenValue_apply`) |
| Capture outer locals | **Supported** — **by-value snapshot** at creation (interpreter + C) |
| Nested `function` naming / recursive lambdas | Limited |

```zl
let n -> 10
let add_n -> function(x) { <- x + n }   // captures n == 10
n -> 99
// add_n(5) == 15  — still uses the snapshotted 10
```

Captures are copied when the lambda is created (not live bindings). Prefer not relying on mutating outer locals from inside a lambda. Up to 8 captures and reasonable apply arity are supported in the native runtime.

Also documented under **Anonymous Functions** in `doc/Zenlang.md` and `doc/Specification/7_functions.typ`. Tests: `tests/language/closure_01.zl`.

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
do for i in 0..10 { ... }           // range → list of 0..9
do for ch in `a`..=`c` { ... }      // `a`, `b`, `c`
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

## 7. Modules, Entry Points & Reflection

Full reference: **[Language_Module_and_Reflect.md](Language_Module_and_Reflect.md)**.

### 7.1 Imports: `use` and packages

`use` is an **alias for `import`** (preferred in new code). Selective form: `from path use name`.

```zl
use zen.io                         // package entry → lib/zen/io/io.zl, binds `io`
use zen.text.string as Str
from zen.io use writeln

// Still valid:
import zen.io as io
from zen.io import writeln
```

Resolver (under `ZEN_PATH`, importer directory first):

1. `{path}.zl`
2. `{path}/{last}.zl` (package entry, e.g. `zen.time` → `time/time.zl`)

Stdlib is **nested packages only** under `lib/zen/<domain>/`. Prefer `use zen.io` over redundant `use zen.io.io`. Map: [Standard_Library_Reference.md](Standard_Library_Reference.md).

### 7.2 Built-in `module`

Every file has a map-like **`module`** binding (no import):

| Field | Meaning |
|-------|---------|
| `name` / `path` / `file` / `dir` | Identity and location |
| `is_entry` | `True` only for the process entry file |
| `entry` | Optional override of the start function (see below) |

```zl
when module.is_entry {
    // script-only init
}
```

### 7.3 Entry points (no decorators)

| Mechanism | Role |
|-----------|------|
| `function main()` | Default process entry (interpret + `-g`) |
| `when module.is_entry { … }` | Entry-only block without naming a function |
| `module.entry -> \`run\`` or `module.entry -> run` | **Bypass `main`**; start at another function |

```zl
function run() { <- 0 }
function main() { <- 1 }
module.entry -> `run`    // host calls run, not main
```

There is **no** `@entry` decorator — entry override is data on `module`, consistent with `is reflectable` (traits/fields, not one-off attributes).

**Status:** `module.entry` is dual-path (interpret + native `-g`). Host `main` runs top-level init, then dispatches to the entry function (or `main` when unset).

### 7.4 Reflection and plugins

```zl
use zen.reflect as reflect
use zen.plugins as P

structure Point is reflectable {
    x: Integer
    y: Integer
}

// Kind + maps
reflect.type_name(1)            // Integer
reflect.fields({`a` -> 1})
m.keys() / m.values() / m.items()

// Dynamic call (plugin tables)
let cmds -> { `hi` -> function(n) { <- n } }
reflect.call(cmds, `hi`, [`zen`])

// Thin plugin helper
let t -> P.create()
t -> P.add(t, `hi`, cmds[`hi`])
P.dispatch(t, `hi`, [`zen`])
```

Opt-in metadata: **`structure` / `class` / `object` … `is reflectable`**. Maps are always field-introspectable without the marker.

*Note: The standard library bridges to the C runtime via builtins for OS primitives (files, process, terminal, time, reflect registry, …).*

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

### 8.2 Processes & Shell Scripting
Zen is meant to **replace bash for many scripts** while still using `/bin/sh` for full shell power (pipes, globs, redirects, `&&` / `||`).

```zl
import zen.sys.process as process

// Bash-like one-liners (via /bin/sh -c)
let out -> process.shell(`ls -la | head -5`)
let n -> process.pipeline(`printf 'a\nb\n' | wc -l`)

// Exit status (bash `$?` / `if cmd`)
when process.ok(`test -f Makefile`) { /* ... */ }
process.require(`make test`)   // fail-fast like set -e

// Full result map: stdout, stderr, code
let r -> process.result(`false`)
// r.code != 0

// Argv form (no shell — safer when no metacharacters)
process.run(`echo`, [`hello`])

// Run under another directory without changing parent cwd (bash: (cd dir && …))
process.shell_in(`/tmp`, `pwd`)

// Per-command environment (bash: FOO=bar cmd) — parent env unchanged
process.shell_env({`FOO` -> `bar`}, `printenv FOO`)
process.shell_in_env(`/tmp`, {`FOO` -> `bar`}, `printenv FOO; pwd`)

// Fluent argv pipeline via real OS pipes (no shell metacharacters needed)
let p -> process.Pipeline(`printf`, [`a\nb\n`])
p.pipe(`wc`, [`-l`])
p.with_env({`LANG` -> `C`})
let n -> p.run()

// Stream lines (like `while read`) without loading full output first
process.each_line(`journalctl -n 20`, function(line) {
    // handle one line
})
```

Structured `Process` objects (`start` / `wait` / `stdout`) remain for longer-lived children. Use `process.shell(\`a | b\`)` when a stage needs globs/redirections; use `Pipeline` when stages are plain argv (safer, real `pipe(2)`).

### 8.3 "Dumb but Honest" Data Formats
Built-in support for simple, human-readable data logic without dependency hell.
```zl
import zen.data.sexp as sexp
import zen.data.logfmt as logfmt
import zen.data.json as json

let row -> logfmt.parse(`time=2026-01-04 level=error msg="bad pass"`)
let obj -> json.parse(`{"ok": true}`)
```

### 8.4 Files & paths
```zl
import zen.io.file as file
import zen.io.path as path

file.write(`out.txt`, `hello`)
let names -> file.list_dir(`.`)
// Recursive walk
file.walk(`lib/zen`, function(p, is_dir) {
    when not is_dir { /* process file p */ }
})
let all -> file.list_files(`lib/zen/sys`)
```

### 8.5 Terminal & Geometry Primitives
First-class support for TUIs and graphical bounds. Raw input + key maps enable nano-like editors (`examples/zedit.zl`).
```zl
import zen.sys.term as term
import zen.geometry as geometry

let rect -> geometry.rectangle(0, 0, 100, 100)

term.raw_enter()
term.alt_screen_enter()
term.move(10, 5)
term.color(`green`, `black`)
term.write(`UI Loaded`)
// Editor-style loop
do {
    let k -> term.read_key()   // map: kind, name, ch, ctrl, code
    when k.kind == `special` and k.name == `ctrl_q` { break }
    when k.kind == `char` { /* insert k.ch */ }
} until false
term.alt_screen_exit()
term.raw_exit()
```