# Zenlang Documentation Suite

Welcome to the official documentation for **Zenlang**, a modern, Unix-native programming language designed for simplicity, composition, and developer control.

---

## 1. Introduction & Overview

### What is Zenlang?
Zenlang is a high-level, optionally typed language built for the modern Unix environment. It is designed to bridge the gap between rapid shell scripting and robust systems programming, providing a single coherent model for building CLI tools, terminal applications (TUIs), and networked services.

### Core Philosophy
Zenlang is guided by the **Zen Manifesto**:
*   **Simplicity over cleverness**: Code should be obvious and readable.
*   **Composition over frameworks**: Power is built by connecting small, well-defined tools.
*   **Explicitness over magic**: Visual data flow makes state changes and returns unmistakable.
*   **Terminal-first**: The terminal is a primary UI surface, not a legacy afterthought.

### Why Zenlang?
*   **Visual Data Flow**: Uses `->` for assignment and `<-` for return, making data movement visually distinct.
*   **Unified Concurrency**: "Everything is a Task." Zenlang uses fiber-based tasks that suspend naturally, eliminating the complexity of `async`/`await` virality.
*   **Semantic Text**: Text is treated as more than just byte arrays; it supports semantic structures like `Word`, `Sentence`, and `Paragraph`.
*   **Boxed Runtime**: A unified memory model that balances the safety of a managed language with the control of manual arenas.

---

## 2. Getting Started

**Preferred on-ramp:** **[Getting_Started.md](Getting_Started.md)** — install, dual execution (interpret vs `-g`), full language tour, stdlib taste, and design patterns.

**Module / reflect / plugins:** **[Language_Module_and_Reflect.md](Language_Module_and_Reflect.md)** — built-in `module`, `module.entry`, `use`, `zen.reflect`, `is reflectable`, `zen.plugins`.

### Installation (short)

Zenlang is in an active bootstrap phase. On Linux/macOS:

1. Clone this repository and `cd` into it.
2. Ensure `python3` and a C compiler (`gcc` or `clang`) are available.
3. Install the daily CLI:
    ```bash
    ./scripts/zen install
    ./bin/zen tests/hello.zl
    ```

### Hello, World!

```zl
import zen.io.io as io

function main() {
    io.writeln(`Hello, Zenlang!`)
    <- 0
}
```

```bash
./bin/zen hello.zl          # interpret
./bin/zen -g hello.zl       # native via C
```

---

## 3. Language Reference (Core Features)

### Variables & Data Types
Zenlang uses explicit operators to distinguish between mutable and immutable state.

*   **`let`**: Defines a mutable variable.
*   **`set`**: Defines a constant (immutable).

```zenlang
let score : Integer -> 100    // Mutable integer
set PI -> 3.14159             // Inferred decimal constant
let name :> `Alice`           // Type-locked (String) but value can change
```

**Base Types**:
*   `Integer`, `Decimal`, `Boolean` (`True`/`False`)
*   `String` (UTF-32 default), `Rune` (Single glyph)
*   `Variant` (Dynamic type), `Void` (No return)

### Control Flow
Zenlang uses familiar but refined control flow structures.

**`when` (Conditionals)**:
```zenlang
when x > 10 {
    io.write(`Large`)
} or when x > 5 {
    io.write(`Medium`)
} or {
    io.write(`Small`)
}
```

**`do` (Loops)**:
```zenlang
// While loop
do while x < 10 { x++ }

// For-in loop
do for item in [1, 2, 3] {
    io.write(item)
}

// Ranges (lists of ints or single characters)
do for i in 0..10 { }          // 0..9
do for ch in `a`..=`c` { }     // a, b, c
```

### Ranges
```zenlang
0..5           // [0, 1, 2, 3, 4]      exclusive end
0..=5          // [0, 1, 2, 3, 4, 5]   inclusive end
`a`..=`z`      // character list
5..2           // [5, 4, 3]            descending
```
Do not use `...` for ranges (that is rest/spread in patterns).

### Functions
Functions are declared using the `function` keyword and return values using the `<-` operator.

```zenlang
function add(a: Integer, b: Integer) : Integer {
    <- a + b
}

// Anonymous function (lambda); outer locals are captured by value
let multiply -> function(x, y) { <- x * y }
let n -> 2
let scale -> function(x) { <- x * n }
```

### Data Structures
*   **Lists**: Dynamic arrays `[1, 2, 3]`
*   **Maps**: Key-value pairs `{ `key` -> `value` }`
*   **Structures**: Lightweight value types `structure Point { x, y }`
*   **Classes**: Full OOP support with inheritance.

```zenlang
class Person {
    let name : String
    function init(name) { self.name -> name }
    function greet { io.write(`Hi, I'm ` + self.name) }
}
```

### Error Handling
Zenlang uses the **Error Triad** for explicit and predictable failure management.

*   **`raise` / `^`**: Returns an error object.
*   **`check` / `?`**: Unwraps a value or handles an error fallback via an `or` block.
*   **`!` (Assert)**: Halts execution if a condition is met.

```zenlang
function riskyDiv(a, b) {
    when b == 0 { raise `DivideByZero` }
    <- a / b
}

let result -> check riskyDiv(10, 0) or {
    io.warn(`Division failed, using default`)
    0
}
```

---

## 4. Advanced Features

### Structured Memory Management
Zenlang provides high-performance memory management without a traditional garbage collector, focusing on **Bounded Arenas**.

*   **`with` statement**: Creates a lexically bounded memory region that is automatically reclaimed when the block exits.
*   **`in` keyword**: Directs an allocation into a specific named arena.
*   **`defer`**: Schedules code to run at the end of the current scope.

```zenlang
import zen.memory

function process {
    with memory.Region() as scene {
        let p in scene -> Person(`Zen`)
        // 'p' is allocated inside 'scene'
    } // 'scene' and all objects inside it are reclaimed here
}
```

### Unified Concurrency (Tasks)
Concurrency is a first-class citizen. Any function or block can be spawned as a **Task**.

```zenlang
task background_work {
    time.sleep(1.second)
    <- `Done`
}

function main {
    let t -> background_work().spawn
    io.write(t.wait)
}
```

---

## 5. Standard Library Overview

| Module | Description | Key Functions |
| :--- | :--- | :--- |
| **`zen.io.io`** | Basic Input/Output & Logging | `write()`, `read()`, `info()`, `warn()`, `error()`, `debug()` |
| **`zen.text.string`**| String Manipulation | `split()`, `join()`, `trim()`, `substring()`, `to_string()` |
| **`zen.collections.list`** | Functional List Utilities | `map()`, `filter()`, `reduce()`, `each()`, `find()`, `contains()` |
| **`zen.collections`**| Map/Set Utilities | `Map.keys()`, `Map.values()`, `Set.from_list()`, `Set.to_list()` |
| **`zen.time`** | Time & Delays | `now()`, `sleep()`, `monotonic()`, `wallclock()`, `500.ms`, `2.seconds` |
| **`zen.sys.process`**| Process Management | `run()`, `get_id()` |
| **`zen.test`** | Unit Testing | `assert_equal()`, `run_unit()`, `run_suite()` |
| **`zen.collections`**| Data Structures | `Map`, `Set`, `Stack`, `Queue` |
| **`zen.error`**| Error Creation | `new()`, `literal()` |
| **`zen.math.math`** | Mathematical Utilities | `abs()`, `sqrt()`, `pow()`, `sin()`, `cos()`, `pi`, `e` |
| **`zen.sys.sys`** | System Environment | `get_args()`, `get_env()`, `get_cwd()`, `platform()`, `version()` |
| **`zen.io.file`** | File System Ops | `read()`, `write()`, `append()`, `exists()`, `remove()`, `walk()`, `list_files()` |
| **`zen.io.path`** | Path Manipulation | `join()`, `basename()`, `dirname()`, `extname()` |
| **`zen.data.json`** | JSON Serialization | `parse()`, `stringify()` |
| **`zen.memory`**| Arena Management | `Region()`, `Arena()`, `push_arena()`, `pop_arena()` |
| **`zen.sys.term`** | Terminal UI | `clear()`, `move()`, `color()`, `reset()`, `alt_screen()`, `get_size()`, `raw_enter()`/`raw_exit()`, `read_key()`/`poll_key()`, `write()`/`flush()`, cursor helpers |
| **`zen.math.random`** | Randomness | `seed()`, `integer()`, `decimal()`, `range()` |
| **`zen.geometry`** | Geometry | `Point`, `Rect`, `Size`, `point()`, `rectangle()`, `size()` |
| **`zen.text.text`** | Semantic Text | `Word`, `Sentence`, `Paragraph`, `capitalize()`, `to_words()`, `wrap()` |

### Logging

Zenlang provides standardized, color-coded logging via the `zen.io.io` module:

- `io.info(msg)`: Blue prefix `[INFO]`
- `io.warn(msg)`: Yellow prefix `[WARN]`
- `io.error(msg)`: Red prefix `[ERROR]` (outputs to `stderr`)
- `io.debug(msg)`: Cyan prefix `[DEBUG]`

---

## 6. Best Practices & Idiomatic Zenlang

1.  **Visual Data Flow**: Use the `->` and `<-` operators consistently to make the data flow obvious to the reader.
2.  **Explicit Memory**: Prefer `with` blocks for large object graphs or temporary data structures to keep the program footprint small.
3.  **Semantic Text**: Don't just use `String`. Use `Word` or `Sentence` when processing natural language to leverage built-in linguistic logic.
4.  **Avoid Global State**: Use the `in` keyword to pass context and dependencies into functions rather than relying on global variables.

---

*Zenlang is calm. Zenlang is deliberate. Zenlang is Unix.*
