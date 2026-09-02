# Zenlang: Canonical Language Reference Manual

**Version:** 1.0 (Native Self-Hosted)  
**Target Execution:** Dual-Path (Script Bytecode VM & Ahead-of-Time C Compilation)  
**Core Value ABI:** `ZenValue` Tagged-Union Layer

---

## Table of Contents

1. [Introduction & Architectural Design](#1-introduction--architectural-design)
2. [Lexical Conventions & Source Representation](#2-lexical-conventions--source-representation)
3. [Variables, Storage & Mutability](#3-variables-storage--mutability)
4. [Type System, Sentinels & Type Casting](#4-type-system-sentinels--type-casting)
5. [Operators & Expression Semantics](#5-operators--expression-semantics)
6. [Control Flow & Conditional Expressions](#6-control-flow--conditional-expressions)
7. [Pattern Matching & Destructuring](#7-pattern-matching--destructuring)
8. [Functions, Returns & Closures](#8-functions-returns--closures)
9. [Structures, Classes & Object-Oriented Programming](#9-structures-classes--object-oriented-programming)
10. [Error Handling & Native Exception Model](#10-error-handling--native-exception-model)
11. [Modules, Namespaces & Packaging](#11-modules-namespaces--packaging)
12. [Memory Model & Resource Scoping (`with`)](#12-memory-model--resource-scoping-with)
13. [Concurrency, Tasks & Channels](#13-concurrency-tasks--channels)
14. [Standard Library Catalog](#14-standard-library-catalog)
15. [Compiler CLI & Toolchain Manual](#15-compiler-cli--toolchain-manual)

---

## 1. Introduction & Architectural Design

Zenlang is a statically and optionally typed systems scripting language engineered for visual clarity, expressiveness, zero-overhead Unix interop, and dual-mode execution.

```
┌─────────────────────────────────────────────────────────────┐
│                       Zenlang Source                        │
│                     (*.zl, *.zd, *.zm)                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
   ┌──────────────────────────┐  ┌──────────────────────────┐
   │    Bytecode Script VM    │  │     AOT C Transpiler     │
   │  (Instant execution,     │  │   (Optimized binaries,   │
   │   REPL, dynamic scripts) │  │    zero-dep deployment)  │
   └────────────┬─────────────┘  └────────────┬─────────────┘
                │                             │
                └──────────────┬──────────────┘
                               ▼
            ┌────────────────────────────────────┐
            │          Universal Runtime         │
            │           `ZenValue` ABI           │
            └────────────────────────────────────┘
```

### 1.1 The Three-Layer Execution Model
1. **Universal `ZenValue` ABI:** Every Zen value in memory is a tagged union holding integers, IEEE 754 floats, UTF-8 strings, lists, maps, structures, or function pointers. This guarantees 100% ABI compatibility between interpreted scripts and compiled native C binaries.
2. **Positional Native IR:** The compiler token stream and AST representation are flattened into memory-efficient positional arrays for high cache locality and fast $O(1)$ arena teardowns.
3. **Dual Execution:**
   - **Script VM (`zen <file.zl>`):** Compiles AST directly into dense bytecode instructions executed by a fast stack-based virtual machine.
   - **AOT Native (`zen build <file.zl>`):** Transpiles AST into high-performance, standard ISO C99 code linked against the runtime.

---

## 2. Lexical Conventions & Source Representation

### 2.1 UTF-8 Source Code
All source files are UTF-8 text. Whitespace (spaces, tabs, newlines) serves only to separate tokens. Indentation is not syntactically significant.

### 2.2 Comment Syntax
```zl
// Line comment: Extends to the end of the line.

/*
   Block comment:
   Can span across multiple lines.
*/

/!
   Documentation comment:
   Preserved by doc generators and attached to following symbols.
!/
```

### 2.3 Literals & Escapes
- **Integers:** Decimal (`42`), Hexadecimal (`0xFF`), Binary (`0b1010`).
- **Decimals:** Double precision floating point (`3.14159`, `-0.001`, `1e9`).
- **Strings:** Enclosed in backticks (`` `Hello\nWorld` ``) supporting standard escape sequences (`\n`, `\t`, `\r`, `\\`, `\``, `\0`, `\xHH`, `\uHHHH`).
- **Booleans:** `True` and `False`.
- **Sentinels:** `Nothing` (absent value), `Default` (type zero-state).

---

## 3. Variables, Storage & Mutability

### 3.1 `let` vs `set`
- `let` defines a **mutable** variable that can be reassigned.
- `set` defines an **immutable** constant that cannot be mutated.

```zl
let counter -> 0
counter -> counter + 1        // OK

set BUFFER_LIMIT -> 4096
// BUFFER_LIMIT -> 8192      // Error: Constant cannot be modified
```

### 3.2 Visual Assignment (`->`)
Data flows from left to right into the target binding:

```zl
// Value -> Binding
`Production` -> environment_mode
1024 * 768   -> total_pixels
```

### 3.3 Type Modes

```zl
// 1. Dynamic Variant
let payload -> { `id` -> 101 }

// 2. Explicit Type Annotation
let max_connections : Integer -> 100
set SERVER_NAME     : String  -> `Gateway`

// 3. Inferred Type Lock (:>)
let active_status :> True // Locked as Boolean; cannot accept non-booleans later
```

---

## 4. Type System, Sentinels & Type Casting

### 4.1 Base Types Table

| Type | Description | Zero-Value (`Default`) |
|:---|:---|:---|
| `Integer` (`Int`, `Int64`, `Int32`) | 64-bit signed two's-complement integer | `0` |
| `Decimal` (`Float`, `Float64`) | 64-bit IEEE 754 double precision float | `0.0` |
| `String` (`Str`) | UTF-8 encoded text buffer | `""` (empty string) |
| `Boolean` (`Bool`) | Boolean logical state (`True` / `False`) | `False` |
| `Rune` (`Char`) | 32-bit Unicode scalar value | `'\0'` |
| `Bytes` (`Buffer`) | Byte array buffer | `Bytes([])` |
| `List` | Homogeneous or heterogeneous dynamic array | `[]` |
| `Map` | String-keyed or Variant-keyed hash table | `{}` |
| `Set` | Unique element set | `Set([])` |
| `Void` | Absence of value or return | `Void` |
| `Variant` | Universal container holding any `ZenValue` | `Nothing` |

### 4.2 Sentinels
- **`Nothing`:** Represents the complete absence of a value.
- **`Default`:** Represents the type's natural zero-state (`0`, `0.0`, `""`, `False`, `[]`, `{}`).

```zl
let optional_value : String -> Nothing
let empty_counter  : Integer -> Default // 0

when optional_value == Nothing { /* handle missing */ }
when empty_counter == Default  { /* handle zero */ }
```

### 4.3 Type Casting (`<:` and `Type(val)`)
Converts values safely across types:

```zl
// 1. Operator form (<:)
let n -> `1234` <: Integer
let s -> 45.67 <: String
let b -> 1 <: Boolean // True

// 2. Constructor form Type(val)
let total -> Integer(`900`)
let text -> String(2026)
```

---

## 5. Operators & Expression Semantics

### 5.1 Operator Precedence & Summary

| Operator Class | Operators | Associativity | Description |
|:---|:---|:---|:---|
| **Primary** | `()`, `[]`, `.`, `->` (call) | Left | Indexing, member access, call |
| **Casting** | `<:` | Left | Type cast operator |
| **Unary** | `not`, `-`, `~`, `++`, `--` | Right | Logical NOT, negation, bitwise NOT, prefix ops |
| **Multiplicative** | `*`, `/`, `%` | Left | Multiplication, division, modulo |
| **Additive** | `+`, `-`, `++`, `--` | Left | Addition, subtraction, string/list concat |
| **Shift** | `<<`, `>>` | Left | Bitwise shifts |
| **Relational** | `<`, `<=`, `>`, `>=`, `is`, `is not` | Left | Comparison and type checking |
| **Equality** | `==`, `!=` | Left | Structural deep equality |
| **Bitwise** | `&`, `^`, `|` | Left | Bitwise AND, XOR, OR |
| **Logical** | `and`, `or` | Left | Short-circuiting logical operations |
| **Range** | `..`, `..=` | Non-assoc | Half-open and closed range construction |
| **Data Flow** | `->` (bind), `<-` (return) | Right | Visual assignment and function return |

### 5.2 Extended Operators (`++` and `--`)
```zl
// Numbers
let x -> 10
x++        // 11
x--        // 10

// Strings
let s -> `Zen`
s++ `lang` // "Zenlang"
s--        // "Zenlan"

// Lists
let l -> [1, 2]
l++ 3      // [1, 2, 3]
l--        // [1, 2]
```

### 5.3 Ranges
```zl
let exclusive -> 0..5      // [0, 1, 2, 3, 4]
let inclusive -> 0..=5     // [0, 1, 2, 3, 4, 5]
let reversed  -> 5..1      // [5, 4, 3, 2]
let chars     -> `a`..=`e` // ['a', 'b', 'c', 'd', 'e']
```

---

## 6. Control Flow & Conditional Expressions

### 6.1 `when` Statement & Expression
```zl
// Statement:
when code == 200 {
    io.info(`Success`)
} or when code == 404 {
    io.warn(`Not Found`)
} or {
    io.error(`Error`)
}

// Expression (Ternary Replacement):
let label -> when is_active { `Running` } or { `Stopped` }
```

### 6.2 Iteration (`do while`, `do for`)
```zl
// Pre-condition while loop:
let i -> 0
do while i < 5 {
    io.write(Str.to_string(i) + ` `)
    i++
}

// Post-condition while loop:
let j -> 0
do {
    j++
} while j < 5

// For-in collection loop:
do for item in [`apple`, `banana`, `cherry`] {
    io.info(item)
}

// For-in range loop:
do for n in 1..=10 {
    io.info(`Number ` + Str.to_string(n))
}
```

---

## 7. Pattern Matching & Destructuring

```zl
// 1. List Matching & Rest Spread
let packet -> [10, 20, 30, 40]
when packet is [1, 2, 3] {
    // Exact match
} or when packet is [head, ...tail] {
    io.info(`Head: ` + Str.to_string(head)) // 10
    io.info(`Tail: ` + Str.to_string(tail)) // [20, 30, 40]
}

// 2. Map Matching
let record -> { `name` -> `Bob`, `role` -> `Admin` }
when record is { name, role } {
    io.info(name + ` is ` + role)
}

// 3. Guards & Wildcards
let val -> 42
when val is Integer and val > 40 {
    io.info(`Large Integer`)
}

let tuple -> [1, 999, 3]
when tuple is [1, _, 3] {
    io.info(`Matched middle wildcard`)
}
```

---

## 8. Functions, Returns & Closures

### 8.1 Declaration & Return
```zl
function calculate_area(width: Decimal, height: Decimal) : Decimal {
    <- width * height
}

// Default parameter values:
function send_request(url: String, timeout_ms: Integer -> 5000) {
    // ...
    <- True
}
```

### 8.2 First-Class Anonymous Functions (Lambdas)
```zl
let multiply -> function(a, b) { <- a * b }
let result -> multiply(4, 5) // 20

import zen.collections.list as List
let doubled -> List.map([1, 2, 3], function(x) { <- x * 2 }) // [2, 4, 6]
```

### 8.3 Lexical Closures (Snapshot by Value)
```zl
let base -> 100
let add_base -> function(x) { <- x + base } // Captures base == 100

base -> 500
add_base(10) // Returns 110 (uses snapshotted value 100)
```

---

## 9. Structures, Classes & Object-Oriented Programming

### 9.1 Structures (`structure`)
```zl
structure Vector2 {
    let x: Decimal
    let y: Decimal
}

let v -> Vector2{ x -> 3.0, y -> 4.0 }
v.x -> 5.0
```

### 9.2 Classes & Inheritance (`class`, `extends`)
```zl
class Vehicle {
    let brand: String
    let speed: Decimal

    function init(brand: String, speed: Decimal) {
        self.brand -> brand
        self.speed -> speed
    }

    function describe() : String {
        <- self.brand + ` running at ` + Str.to_string(self.speed) + ` km/h`
    }
}

class ElectricCar extends Vehicle {
    let battery_pct: Integer

    function init(brand: String, speed: Decimal, battery: Integer) {
        parent.init(brand, speed)
        self.battery_pct -> battery
    }

    function describe() : String {
        <- parent.describe() + ` [Battery: ` + Str.to_string(self.battery_pct) + `%]`
    }
}

let tesla -> ElectricCar(`Tesla Model 3`, 120.0, 88)
io.info(tesla.describe())
```

### 9.3 Enums (`enum`)
```zl
enum Status {
    Pending,
    Active(started_at: Integer),
    Failed(reason: String)
}

let current -> Status.Active(1725200000)

when current is Status.Active(t) {
    io.info(`Started at timestamp: ` + Str.to_string(t))
}
```

---

## 10. Error Handling & Native Exception Model

### 10.1 `check` Expressions
Safely wraps error-prone expressions with an automatic fallback:

```zl
function safe_divide(a: Integer, b: Integer) {
    when b == 0 {
        <- __builtin.error(`Division by zero`)
    }
    <- a / b
}

let result -> check safe_divide(10, 0) or {
    io.warn(`Division failed, using zero fallback`)
    0
}
```

### 10.2 `raise` Statement
Throws an error that propagates through the call stack to the nearest `check` boundary:

```zl
function load_file(p: String) {
    when not file.exists(p) {
        raise `File does not exist: ` + p
    }
    <- file.read_to_string(p)
}
```

---

## 11. Modules, Namespaces & Packaging

### 11.1 Module Imports
```zl
// 1. Qualified module import
import zen.io.io as io
import zen.text.string as Str

// 2. Selective import
from zen.math.math import abs, min, max

// 3. Package root alias (use keyword)
use zen.io
use zen.sys.process as process
```

### 11.2 Intrinsic `module` Metadata
- `module.name`: Module stem name.
- `module.path`: Canonical file system path.
- `module.is_entry`: Boolean flag indicating if file was the CLI entry.
- `module.entry`: Entry function pointer (defaults to `main`).

---

## 12. Memory Model & Resource Scoping (`with`)

Zenlang combines automatic memory management with scoped memory arenas:

```zl
import zen.memory as Memory

with Memory.Arena.create(1024 * 1024) as arena {
    let buffer -> Memory.alloc_in(arena, 4096)
    // High-throughput scratch allocations
}
// All memory allocated in the arena is instantly reclaimed here
```

---

## 13. Concurrency, Tasks & Channels

```zl
import zen.sys.concurrency as sync

// 1. Spawning Tasks
let task_handle -> sync.task_spawn(function() {
    <- `Worker finished`
})
let result -> sync.task_await(task_handle)

// 2. Channels
let ch -> sync.channel_create(5)
sync.channel_send(ch, `Message`)
let received -> sync.channel_recv(ch)
sync.channel_close(ch)

// 3. Synchronization (Mutex, WaitGroup, Atomic)
let mu -> sync.mutex_create()
sync.mutex_lock(mu)
// Critical section
sync.mutex_unlock(mu)
```

---

## 14. Standard Library Catalog

| Category | Modules | Key Functions & Types |
|:---|:---|:---|
| **I/O** | `zen.io.io`, `zen.io.file`, `zen.io.path`, `zen.io.csv` | `read_file`, `write_file`, `walk`, `join`, `base_name`, `parse_csv` |
| **System** | `zen.sys.sys`, `zen.sys.process`, `zen.sys.term`, `zen.sys.time` | `shell`, `pipeline`, `read_key`, `color`, `now_ms`, `sleep` |
| **Text** | `zen.text.string`, `zen.text.regex`, `zen.text.markdown`, `zen.text.fuzzy` | `split`, `join`, `trim`, `replace`, `match`, `render_html`, `fuzzy_match` |
| **Math** | `zen.math.math`, `zen.math.random`, `zen.math.stats`, `zen.math.geometry` | `sin`, `cos`, `pow`, `rand_int`, `mean`, `stddev`, `Point`, `Rectangle` |
| **Collections** | `zen.collections.list`, `.set`, `.stack`, `.queue`, `.priority_queue`, `.lru`, `.ring_buffer` | `PriorityQueue`, `LRU`, `RingBuffer`, `Set`, `Stack`, `Queue` |
| **Data Formats** | `zen.data.json`, `.zendata`, `.schema`, `.tar`, `.xml`, `.yaml`, `.toml`, `.ini`, `.logfmt` | `json.parse`, `json.stringify`, `tar.extract`, `xml.parse`, `yaml.parse` |
| **Networking** | `zen.net.http`, `zen.net.server`, `zen.net.ip`, `zen.net.socket` | `http.get`, `http.post`, `Server.create`, `ip.is_ipv4`, `socket.connect` |
| **Crypto** | `zen.crypto.sha256`, `zen.crypto.hmac`, `zen.crypto.jwt` | `sha256.digest`, `hmac.sign`, `jwt.encode`, `jwt.decode` |
| **Color & UI** | `zen.color.color`, `zen.ui.canvas`, `zen.ui.layout`, `zen.ui.table`, `zen.ui.spinner` | `rgb`, `hsl`, `hex`, `Table.render`, `Spinner.tick`, `Canvas.draw_text` |
| **Tooling** | `zen.tooling.project`, `.builder`, `.tester`, `.bench`, `.docgen`, `.pkg`, `.dash`, `.repl` | Project management, compilation, test discovery, benchmarking, interactive REPL |
| **Testing** | `zen.test.test` | `assert_equal`, `assert_true`, `assert_false`, `run_suite` |

---

## 15. Compiler CLI & Toolchain Manual

The unified `zen` compiler and driver provides complete development utilities:

```bash
# Execution
zen script.zl                   # Fast script execution via Bytecode VM
zen run app.zl                  # Compile and execute native binary
zen repl                        # Interactive development REPL

# Build & Compilation
zen build app.zl                # Build standalone native executable in build/
zen compile app.zl out.c        # Transpile into optimized C99 source code
zen bundle app.zl               # Compile into portable .zbc bytecode archive

# Testing & Verification
zen test                        # Run full 4-tier test ladder
zen bench                       # Run benchmark suites in benches/
zen check app.zl                # Run static type checker and diagnostics
zen lint                        # Style and best-practice linter

# Developer Tools & Introspection
zen disasm app.zl               # Disassemble bytecode instructions
zen ast app.zl                  # Print syntax tree structure
zen completion bash             # Generate shell autocompletion
zen doc                         # Generate HTML documentation
```
