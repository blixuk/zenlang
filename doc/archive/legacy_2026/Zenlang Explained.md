# Zenlang: The Complete Language Reference & Specification Manual

## 1. Introduction & Core Philosophy

**Zenlang** is a modern, optionally typed, Unix-native programming language designed for clarity, visual ergonomics, high performance, and rapid systems development. It eliminates historical baggage (such as unstructured string parsing, fragmented concurrency abstractions, and silent `null` pointer dereferences) in favor of visual data flow, explicit control flow, and a unified execution model.

### 1.1 Guiding Principles

1. **Visual Data Flow:** Assignment (`->`) and return (`<-`) operators make the physical direction and movement of data immediately obvious at a glance.
2. **Explicitness Over Magic:** Few hidden coercions. Control flow, mutability, error handling, and type transitions are clearly articulated in syntax.
3. **Terminal-First Ergonomics:** Rich terminal interfaces, ANSI color primitives, structured logging, stream buffering, and raw keyboard polling are native first-class citizens.
4. **Unified Concurrency:** Tasks, channels, fibers, and thread pools are integrated under a coherent concurrency model without color-virality (`async`/`await`).
5. **Three-Layer Execution Architecture:**
   - **`ZenValue` ABI:** Universal tagged-union value layer powering bidirectional interop between interpreted scripts and compiled binaries.
   - **Compiler Native IR:** Flat, cache-locality optimized AST list structures.
   - **Dual Execution Engine:** Fast script execution via Bytecode VM paired with Ahead-of-Time (AOT) C compilation producing standalone native executables.

---

## 2. Lexical Structure & Conventions

### 2.1 Source Encoding
Zenlang source files (`.zl`) must be encoded in **UTF-8**. Whitespace (spaces and tabs) separates tokens but is otherwise not syntactically significant. Indentation does not define blocks; curly braces `{ ... }` delimit scopes.

### 2.2 Comments
Zenlang supports three styles of comments:

```zl
// 1. Single-line comment: Extends to the end of the physical line.

/*
   2. Multi-line block comment:
      Spans across multiple lines.
*/

/!
  3. Documentation comment:
     Extracted by documentation generators (`zen doc` / `docgen.zl`).
     Attached to following declarations (functions, structures, classes).
!/
```

### 2.3 Identifiers & Naming Conventions
- **Variables & Functions:** `snake_case` (e.g. `user_count`, `calculate_checksum`)
- **Types, Structures, Classes & Enums:** `PascalCase` (e.g. `Integer`, `HttpClient`, `Color`)
- **Constants & Sentinels:** `UPPER_CASE` or `PascalCase` (e.g. `MAX_BUFFER_SIZE`, `Nothing`, `Default`, `True`, `False`)
- **Private / Internal Bindings:** Leading underscore (e.g. `_init_cache`, `_NAMED`)

### 2.4 Keywords & Reserved Symbols
- **Binding & Mutability:** `let`, `set`
- **Control Flow:** `when`, `or`, `do`, `while`, `for`, `in`, `until`, `break`, `continue`
- **Functions & Execution:** `function`, `export`, `import`, `use`, `from`, `as`
- **Data & OOP:** `structure`, `class`, `extends`, `enum`, `self`, `parent`, `is`, `is not`
- **Error Handling:** `check`, `raise`
- **Memory & Resource Scoping:** `with`
- **Sentinels & Literals:** `Nothing`, `Default`, `True`, `False`

---

## 3. Variables, Mutability & Storage

Zenlang strictly differentiates between mutable variables and immutable constants.

### 3.1 Mutability: `let` vs `set`
- **`let` (Mutable):** Declares a variable whose value can be reassigned during execution.
- **`set` (Constant):** Declares an immutable binding that cannot be reassigned once initialized.

```zl
let count -> 0            // Mutable variable
count -> count + 1        // Valid reassignment

set MAX_LIMIT -> 1000     // Immutable constant
// MAX_LIMIT -> 2000     // Compile-time error: cannot reassign constant
```

### 3.2 Visual Assignment (`->`)
The visual arrow operator `->` binds the evaluated result of the left-hand expression to the right-hand target identifier:

```zl
// <expression> -> <identifier>
10 + 20 -> total
`Alice` -> user_name
```

### 3.3 Declaration & Typing Modes

```zl
// 1. Dynamic Variant (Type Inferred & Polymorphic)
let health -> 100

// 2. Explicit Type Annotation
let score : Integer -> 95
set APP_NAME : String -> `ZenEditor`

// 3. Inferred Type Lock (:>)
// Infers the initial type (String) and enforces strict static typing on subsequent assignments
let city :> `London`
// city -> 42 // Type error: expected String
```

### 3.4 Sentinels: `Nothing` vs `Default`

Zenlang prevents null-pointer errors using two standardized, capitalized sentinels:

| Sentinel | Semantic Meaning | Type Equivalent |
|:---|:---|:---|
| **`Nothing`** | Explicit absence of a value (unassigned, missing, optional none). | `ZEN_NOTHING` |
| **`Default`** | The canonical zero-state of a type (`0`, `0.0`, `""`, `False`, `[]`, `{}`). | Type Zero-Value |

```zl
let user_avatar : String -> Nothing  // Explicitly absent
let counter : Integer -> Default     // Evaluates to 0
let flags : List -> Default          // Evaluates to []
let label : String -> Default        // Evaluates to ``

when user_avatar == Nothing {
    // Handle missing avatar
}

when counter == Default {
    // Evaluates to true when counter is 0
}
```

---

## 4. Type System & First-Class Type Casting

Zenlang features a rich type hierarchy supporting both high-level scripting flexibility and low-level native performance.

### 4.1 Primitive Types

| Type Name | Aliases | Description | Example Literals |
|:---|:---|:---|:---|
| `Integer` | `Int`, `Int64`, `Int32`, `Int16`, `Int8` | 64-bit signed integer | `42`, `-15`, `0xFF`, `0b1010` |
| `Decimal` | `Float`, `Float64`, `Float32` | 64-bit double-precision IEEE 754 float | `3.14159`, `-0.5`, `1.0e6` |
| `String` | `Str` | UTF-8 encoded string | `` `Hello World` ``, `` `Line\nBreak` `` |
| `Boolean` | `Bool` | Boolean truth values | `True`, `False` |
| `Rune` | `Char` | 32-bit Unicode code point | `'A'`, `'\n'`, `'\u00A9'` |
| `Bytes` | `Buffer` | Raw binary buffer / byte array | `Bytes([0xDE, 0xAD, 0xBE, 0xEF])` |
| `Void` | — | Unit / absence of return value | `Void` |
| `Variant` | — | Tagged union container capable of holding any `ZenValue` | Dynamic bindings |

### 4.2 Compound & Collection Types

#### Lists
Ordered, growable arrays supporting mixed-type or homogeneous elements:
```zl
let numbers -> [10, 20, 30, 40]
let mixed -> [1, `two`, True, Nothing]

numbers.append(50)
let first -> numbers[0]       // 10
let total -> numbers.length   // 5
let popped -> numbers.pop()   // 50
```

#### Maps
Key-value associative hash tables with string or variant keys:
```zl
let user -> {
    `name` -> `Bob`,
    `age` -> 28,
    `is_admin` -> False
}

user[`role`] -> `Developer`   // Assignment
let name -> user[`name`]      // Lookup
let exists -> user.has(`age`) // True
let keys -> user.keys()       // ['name', 'age', 'is_admin', 'role']
```

#### Sets
Deduplicated collections of unique items:
```zl
import zen.collections.set as Set

let s -> Set.create([1, 2, 2, 3, 4, 4])
Set.has(s, 2)                 // True
let unique_list -> Set.to_list(s) // [1, 2, 3, 4]
```

### 4.3 Type Casting (`<:` and `Type(val)`)

Zenlang provides dual syntax for explicit, safe type conversions:
1. **Visual Cast Operator (`<:`):** `<expression> <: <TargetType>`
2. **Constructor Syntax:** `<TargetType>(<expression>)`

```zl
// Operator syntax:
let port -> `8080` <: Integer
let ratio -> 100 <: Decimal
let active -> 1 <: Boolean
let code -> `Z` <: Integer

// Constructor syntax:
let total -> Integer(`500`)
let text -> String(2026)
let unique -> Set([1, 2, 3, 3])
```

#### Type Cast Matrix

| Source Type | Target: `Integer` / `Int` | Target: `Decimal` / `Float` | Target: `String` / `Str` | Target: `Boolean` / `Bool` | Target: `Rune` / `Char` | Target: `List` | Target: `Map` |
|:---|:---|:---|:---|:---|:---|:---|
| **`Integer`** | Identity | Float conversion (`n.0`) | String digits (`"42"`) | `n != 0` | Unicode char from code point | `[n]` | `{}` |
| **`Decimal`** | Truncated integer | Identity | Formatted decimal string | `d != 0.0` | Codepoint conversion | `[d]` | `{}` |
| **`String`** | Parsed int (`"42"` → `42`) | Parsed float (`"3.14"` → `3.14`) | Identity | `"True"/"true"/"1"` → `True` | 1st character | `[chars]` | `{}` |
| **`Boolean`** | `True` → `1`, `False` → `0` | `True` → `1.0`, `False` → `0.0` | `"True"` / `"False"` | Identity | `""` | `[b]` | `{}` |
| **`Rune`** | Unicode code point value | Code point as float | 1-char string | Non-zero code point | Identity | `[rune]` | `{}` |
| **`List`** | Element count (`.length`) | `.length` as float | String representation | `len > 0` | 1st element as char | Identity | `{}` |
| **`Map`** | Entry count (`.length`) | `.length` as float | String representation | `len > 0` | `""` | Key list | Identity |
| **`Nothing`** | `0` | `0.0` | `""` | `False` | `""` | `[]` | `{}` |

---

## 5. Operators & Expressions

### 5.1 Arithmetic Operators
- Addition: `a + b` (numbers) or concatenation (strings/lists)
- Subtraction: `a - b`
- Multiplication: `a * b`
- Division: `a / b` (Division by zero throws a catchable exception or error)
- Modulo: `a % b`

### 5.2 Bitwise Operators
- Bitwise AND: `a & b`
- Bitwise OR: `a | b`
- Bitwise XOR: `a ^ b`
- Bitwise NOT: `~a`
- Bitwise Shift Left: `a << b`
- Bitwise Shift Right: `a >> b`

### 5.3 Logical & Comparison Operators
- Logical operators: `and`, `or`, `not` (Short-circuiting evaluation)
- Structural equality: `==`, `!=` (Deep equality for lists, maps, and structures)
- Relational comparisons: `<`, `<=`, `>`, `>=`
- Type testing: `is`, `is not` (e.g. `when val is Integer`)

### 5.4 Extended Operators (`++` and `--`)
Zenlang provides polymorphic `++` and `--` operators:

```zl
// 1. Numbers (Increment / Decrement)
let count -> 5
count++                       // count becomes 6
count--                       // count becomes 5

// 2. Strings (Append / Prepend / Drop)
let msg -> `Hello`
msg++ ` World`                // msg becomes "Hello World"
++msg `>> `                   // msg becomes ">> Hello World"
msg--                         // Drops last character
--msg                         // Drops first character

// 3. Lists (Append / Prepend / Drop)
let items -> [1, 2]
items++ 3                     // items becomes [1, 2, 3]
++items 0                     // items becomes [0, 1, 2, 3]
items--                       // Drops last element ([0, 1, 2])
--items                       // Drops first element ([1, 2])
```

### 5.5 Ranges (`..` and `..=`)
Ranges construct lists of integers or single-character strings:

```zl
// Exclusive range: [start, end)
let r1 -> 0..5                // [0, 1, 2, 3, 4]

// Inclusive range: [start, end]
let r2 -> 0..=5               // [0, 1, 2, 3, 4, 5]

// Descending ranges:
let down -> 5..1              // [5, 4, 3, 2]
let down_inc -> 5..=1         // [5, 4, 3, 2, 1]

// Character ranges:
let alphabet -> `a`..=`z`     // ['a', 'b', ..., 'z']
```

---

## 6. Control Flow & Loops

### 6.1 Conditionals: `when` Statement & Expression

The `when` keyword replaces traditional `if` statements and ternary operators.

#### Statement Form:
```zl
when status == 200 {
    io.info(`Success`)
} or when status == 404 {
    io.warn(`Not Found`)
} or {
    io.error(`Unexpected Status: ` + Str.to_string(status))
}
```

#### Expression Form (Ternary Replacement):
```zl
let status_text -> when is_connected { `Online` } or { `Offline` }
let abs_val -> when x < 0 { -x } or { x }
```

### 6.2 Loops: `do while`, `do for`, `do until`

#### While Loops:
```zl
// Pre-condition test:
let i -> 0
do while i < 5 {
    io.write(Str.to_string(i) + ` `)
    i++
}

// Post-condition test:
let j -> 0
do {
    j++
} while j < 5
```

#### For-In Collection & Range Loops:
```zl
// Iterate over List:
do for item in [`apple`, `banana`, `cherry`] {
    io.info(`Fruit: ` + item)
}

// Iterate over Range:
do for idx in 1..=5 {
    io.info(`Step: ` + Str.to_string(idx))
}
```

#### Loop Controls:
- `break`: Terminates loop execution immediately.
- `continue`: Skips to the next iteration.

---

## 7. Pattern Matching & Destructuring

Zenlang features powerful pattern matching via `when <target> is <pattern>`:

### 7.1 List Matching & Spread Destructuring
```zl
let payload -> [10, 20, 30, 40]

when payload is [1, 2, 3] {
    io.info(`Exact match`)
} or when payload is [first, ...rest] {
    io.info(`First element: ` + Str.to_string(first))
    io.info(`Remaining tail: ` + Str.to_string(rest))
}
```

### 7.2 Map Destructuring
```zl
let person -> { `name` -> `Alice`, `age` -> 30, `role` -> `Admin` }

when person is { name, age } {
    io.info(`Found ` + name + ` aged ` + Str.to_string(age))
}
```

### 7.3 Pattern Guards & Wildcards
```zl
let score -> 85

when score is Integer and score >= 90 {
    io.info(`Grade A`)
} or when score is Integer and score >= 80 {
    io.info(`Grade B`)
}

// Wildcard matching:
let tuple -> [1, 999, 3]
when tuple is [1, _, 3] {
    io.info(`Matched 1 and 3 with ignored middle element`)
}
```

---

## 8. Functions, Return & Closures

### 8.1 Function Declaration
Functions are declared using the `function` keyword. The return value is transmitted using the visual return arrow `<-`:

```zl
function add(a: Integer, b: Integer) : Integer {
    <- a + b
}

// Optional parameter defaults:
function connect(host: String, port: Integer -> 8080) {
    io.info(`Connecting to ` + host + `:` + Str.to_string(port))
    <- True
}
```

### 8.2 First-Class Anonymous Functions (Lambdas)
Functions are first-class citizens and can be stored in variables, passed to higher-order functions, or returned from functions:

```zl
let square -> function(x) { <- x * x }
let result -> square(6) // 36

import zen.collections.list as List

let numbers -> [1, 2, 3, 4, 5]
let doubled -> List.map(numbers, function(x) { <- x * 2 }) // [2, 4, 6, 8, 10]
let evens -> List.filter(numbers, function(x) { <- x % 2 == 0 }) // [2, 4]
let sum -> List.reduce(numbers, 0, function(acc, x) { <- acc + x }) // 15
```

### 8.3 Closures & Snapshot Capture
Anonymous functions capture in-scope variables **by value snapshot** at the time of creation:

```zl
let factor -> 10
let multiplier -> function(x) { <- x * factor }

factor -> 20 // Reassigning outer variable does not mutate the captured snapshot
let res -> multiplier(5) // Evaluates to 50 (5 * 10)
```

---

## 9. Structures, Classes & Object-Oriented Programming

Zenlang supports both lightweight data records (`structure`) and full object-oriented classes (`class`) with single inheritance.

### 9.1 Structures (`structure`)
Lightweight value containers:

```zl
structure Point {
    let x: Integer
    let y: Integer
}

// Construction:
let pt -> Point{ x -> 10, y -> 20 }
let x_coord -> pt.x // 10
pt.y -> 35          // Field mutation
```

### 9.2 Classes & Single Inheritance (`class`, `extends`)
Full OOP support with methods, constructors, `self`, and `parent`:

```zl
class Animal {
    let name: String
    let sound: String

    function init(name: String, sound: String) {
        self.name -> name
        self.sound -> sound
    }

    function speak() : String {
        <- self.name + ` says ` + self.sound
    }
}

class Dog extends Animal {
    let breed: String

    function init(name: String, breed: String) {
        parent.init(name, `Woof`)
        self.breed -> breed
    }

    function speak() : String {
        <- parent.speak() + ` (Breed: ` + self.breed + `)`
    }
}

let d -> Dog(`Rex`, `German Shepherd`)
io.info(d.speak()) // "Rex says Woof (Breed: German Shepherd)"
```

### 9.3 Enumerations (`enum`)
Tagged unions with optional payloads:

```zl
enum Shape {
    Circle(radius: Decimal),
    Rectangle(width: Decimal, height: Decimal),
    Point
}

let s -> Shape.Circle(5.0)

when s is Shape.Circle(r) {
    let area -> 3.14159 * r * r
    io.info(`Circle Area: ` + Str.to_string(area))
} or when s is Shape.Rectangle(w, h) {
    let area -> w * h
    io.info(`Rectangle Area: ` + Str.to_string(area))
}
```

---

## 10. Error Handling & Exception Model

Zenlang eliminates unhandled runtime crashes through structured `check` expressions, explicit error objects, and C `setjmp`/`longjmp` exception boundaries.

### 10.1 `check` Expressions & Fallbacks
The `check` expression wraps an operation that may fail or raise an error, providing a seamless fallback block:

```zl
function divide(a: Integer, b: Integer) {
    when b == 0 {
        <- __builtin.error(`Division by zero`)
    }
    <- a / b
}

function main() {
    // If divide(10, 0) fails, execution branches into the fallback block:
    let result -> check divide(10, 0) or {
        io.warn(`Caught division error; applying default`)
        0
    }
    io.info(`Result: ` + Str.to_string(result)) // Result: 0
}
```

### 10.2 Explicit `raise` Statement
```zl
function parse_config(path: String) {
    when not file.exists(path) {
        raise `Config file not found: ` + path
    }
    <- file.read_to_string(path)
}
```

---

## 11. Modules, Imports & Packaging

### 11.1 Importing Modules
Modules are referenced by dot-separated paths mapped to the directory structure under `ZEN_PATH`:

```zl
// 1. Module namespace import:
import zen.io.io as io
import zen.text.string as Str

// 2. Selective symbol import:
from zen.math.math import abs, min, max

// 3. Package root alias (use keyword):
use zen.io
use zen.sys.process as process
```

### 11.2 Exporting Declarations
```zl
export function calculate_hash(data: String) : String {
    // ...
}

export structure Config {
    let host: String
    let port: Integer
}
```

### 11.3 Built-in `module` Context
Every file has access to an intrinsic `module` object:
- `module.name`: The identifier name of the current module.
- `module.path`: Full filesystem path to the current source file.
- `module.is_entry`: `True` if this file is the execution entry point.
- `module.entry`: Can be set to redirect the execution entry function (e.g. `module.entry -> "custom_main"`).

---

## 12. Memory Model & Resource Scoping (`with`)

Zenlang provides automatic memory management by default while supporting high-performance memory arenas for zero-overhead bulk allocations.

### 12.1 Scoped Arenas (`with`)
The `with` statement binds a scoped resource, guaranteeing deterministic cleanup and arena reclamation upon block exit:

```zl
import zen.memory as Memory

with Memory.Arena.create(1024 * 1024) as arena {
    // All temporary allocations inside this block are pooled within the arena
    let temp_buffer -> Memory.alloc_in(arena, 512)
    // ... perform high-throughput allocations ...
}
// Arena memory is reclaimed in O(1) time here
```

---

## 13. Concurrency & Asynchronous Tasks

Zenlang provides a unified concurrency toolkit under `zen.sys.concurrency`.

### 13.1 Tasks & Spawning
```zl
import zen.sys.concurrency as sync

function worker(id: Integer) : String {
    <- `Task ` + Str.to_string(id) + ` complete`
}

let t1 -> sync.task_spawn(function() { <- worker(1) })
let t2 -> sync.task_spawn(function() { <- worker(2) })

let r1 -> sync.task_await(t1)
let r2 -> sync.task_await(t2)
```

### 13.2 Channels
```zl
let chan -> sync.channel_create(10) // Buffered channel

sync.channel_send(chan, `Hello from background`)
let msg -> sync.channel_recv(chan)
sync.channel_close(chan)
```

### 13.3 Synchronization Primitives
- **`WaitGroup`:** `wg_create()`, `wg_add()`, `wg_done()`, `wg_wait()`.
- **`Mutex`:** `mutex_create()`, `mutex_lock()`, `mutex_unlock()`.
- **`Atomic`:** `atomic_create()`, `atomic_get()`, `atomic_set()`, `atomic_add()`.

---

## 14. Standard Library Catalog

The standard library lives under `lib/zen/` with comprehensive coverage across all systems and application domains:

| Module Domain | Package Path | Primary Capabilities |
|:---|:---|:---|
| **I/O & Files** | `zen.io.io`, `zen.io.file`, `zen.io.path`, `zen.io.csv` | File read/write, streaming buffers, directory walking, path manipulation, CSV parsing. |
| **System & Process** | `zen.sys.sys`, `zen.sys.process`, `zen.sys.term`, `zen.sys.time` | Subprocess execution, piped pipelines, raw TUI keyboard polling, high-resolution clocks, timers. |
| **Text & Strings** | `zen.text.string`, `zen.text.regex`, `zen.text.markdown`, `zen.text.zenmark`, `zen.text.fuzzy` | String manipulation, regex pattern matching, Markdown/ZenMark AST & HTML rendering, fuzzy search. |
| **Math & Stats** | `zen.math.math`, `zen.math.random`, `zen.math.stats`, `zen.math.geometry` | Trigonometry, power/log, random distributions, mean/stddev, 2D/3D vectors, rectangles. |
| **Collections** | `zen.collections.list`, `.set`, `.stack`, `.queue`, `.priority_queue`, `.lru`, `.ring_buffer` | Stacks, queues, min/max heap PriorityQueue, LRU cache with eviction, bounded ring buffer. |
| **Data Formats** | `zen.data.json`, `.zendata`, `.schema`, `.tar`, `.xml`, `.yaml`, `.toml`, `.ini`, `.dotenv`, `.logfmt` | JSON parser/encoder, ZenData AST format, schema validation, tar archives, XML/YAML/TOML. |
| **Networking** | `zen.net.http`, `zen.net.server`, `zen.net.ip`, `zen.net.socket` | HTTP client/server, TCP sockets, CIDR/IPv4/IPv6 validation and routing. |
| **Cryptography** | `zen.crypto.sha256`, `zen.crypto.hmac`, `zen.crypto.jwt` | SHA-256 digests, HMAC authentication, JWT encoding/decoding/validation. |
| **Color & Graphics** | `zen.color.color`, `zen.graphics.bmp`, `zen.graphics.ppm` | 24-bit TrueColor, RGB/RGBA, HSL, Hex, ANSI escapes, BMP/PPM image generators. |
| **Terminal UI (TUI)** | `zen.ui.canvas`, `zen.ui.layout`, `zen.ui.table`, `zen.ui.spinner`, `zen.ui.prompt`, `zen.ui.tree` | Virtual screen buffer canvas, flexbox layout engine, ANSI tables, spinners, tree inspectors. |
| **Tooling & PM** | `zen.tooling.project`, `.builder`, `.tester`, `.bench`, `.docgen`, `.pkg`, `.dash`, `.repl` | Project scaffolding, compilation, test discovery, benchmarking, HTML docgen, package manager. |
| **Test Suite** | `zen.test.test` | Unit testing harness, assertion helpers (`assert_equal`, `assert_true`), test suite runners. |

---

## 15. Developer Toolchain & CLI Guide

The unified `zen` driver provides all necessary development commands:

```bash
# Running & Evaluating
zen <file.zl>                   # Execute script via Bytecode VM
zen run <file.zl>               # Compile and run natively
zen repl                        # Launch interactive stateful REPL

# Building & Compiling
zen build <file.zl>             # Compile to native binary in build/
zen compile <file.zl> <out.c>   # Transpile to optimized C source
zen bundle <file.zl>            # Package into portable .zbc bytecode

# Quality, Testing & Benchmarking
zen test                        # Run full test ladder (core, parity, lib, native)
zen bench                       # Execute benchmark suites in benches/
zen check <file.zl>             # Run static type checker and diagnostics
zen lint                        # Analyze code style and syntax guidelines

# Introspection & Developer Tools
zen disasm <file.zl>            # Disassemble bytecode instructions
zen ast <file.zl>               # Display visual AST syntax tree
zen completion bash             # Generate Bash tab-completion script
zen doc                         # Generate HTML documentation in docs/
zen pkg <install|add|list>      # Manage project dependencies
```