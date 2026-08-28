# Zenlang Style Guide

This document defines the canonical coding standards and style conventions for the Zenlang ecosystem. All standard library code, self-hosted compiler sources, and user applications must adhere to these guidelines, enforced automatically by [zenfmt](Formatter.md).

---

## 1. Naming Conventions

| Entity | Casing | Examples |
|---|---|---|
| **Variables & Local Bindings** | `snake_case` | `user_id`, `max_buffer_size`, `count`, `item_list` |
| **Functions & Methods** | `snake_case` | `format_table()`, `read_lines()`, `next_frame()`, `parse_tokens()` |
| **Classes, Structures, Enums** | `PascalCase` | `Table`, `Spinner`, `FileManager`, `Point`, `TokenType` |
| **Type Annotations** | `PascalCase` | `Integer`, `Decimal`, `Boolean`, `String`, `List`, `Map` |
| **Sentinels & Literals** | `PascalCase` | `Nothing`, `Default`, `True`, `False` |
| **Global Constants** | `UPPER_SNAKE` | `MAX_BUFFER_LEN`, `DEFAULT_TIMEOUT_MS`, `G_SRC` |
| **Modules & Packages** | `snake_case` | `zen.ui.table`, `zen.text.string`, `zen.math.stats` |

---

## 2. Visual Data Flow (`->` and `<-`)

Zenlang emphasizes explicit directional data flow:

### Assignment & Binding (`->`)
Use `->` for all variable declarations and re-assignments. Keep a single space before and after `->`:

```zen
// Preferred:
let total_items -> 100
let name -> `Zenlang`
let [head, tail] -> parse_head_tail(tokens)

// Avoid:
let total_items->100
let name  ->  `Zenlang`
```

### Return Statements (`<-`)
Use `<-` for returning values from functions. Place a space after `<-`:

```zen
// Preferred:
function compute_area(w: Integer, h: Integer) : Integer {
    <- w * h
}

// Concise expression functions:
function square(x) <- x * x

// Single-line early guard exits:
function validate(x) {
    when x < 0 <- { `ok` -> False, `error` -> `Negative value` }
    <- { `ok` -> True, `value` -> x }
}
```

---

## 3. Control Flow & Branching

### `when` Statements
Use `when` for conditionals. Chain alternatives with `or when` and fallback with `or`:

```zen
when score >= 90 {
    grade -> `A`
} or when score >= 80 {
    grade -> `B`
} or {
    grade -> `F`
}
```

### Pattern Matching & Destructuring (`when ... is`)
Use `when ... is` for zero-overhead structural destructuring of variants, lists, maps, and tagged structs:

```zen
when result is Ok(value) {
    io.writeln(`Computation succeeded: ` + Str.to_string(value))
} or when result is Err(msg) {
    io.writeln(`Error encountered: ` + msg)
}

when point is Point { x, y } {
    io.writeln(`Coordinates: (` + Str.to_string(x) + `, ` + Str.to_string(y) + `)`)
}
```

### Iteration Loops
Use `do for item in collection` for collections and `do while` for condition-driven loops:

```zen
// Preferred collection iteration:
let items -> [`alpha`, `beta`, `gamma`]
do for item in items {
    io.writeln(item)
}

// Condition loop:
let i -> 0
do while i < 10 {
    i -> i + 1
}
```

---

## 4. Error Handling & Boundaries

### Structured `check / or` Blocks
Wrap risky IO and parsing operations in `check / or` blocks rather than allowing unexpected crashes:

```zen
function load_user_config(path) {
    check {
        let content -> file.read(path)
        let cfg -> json.parse(content)
        <- { `ok` -> True, `config` -> cfg }
    } or {
        <- { `ok` -> False, `error` -> `Failed to read config from ` + path }
    }
}
```

---

## 5. Memory Management & Scoped Arenas

Use `with memory.create_arena(...) as arena` for high-throughput batch processing or compiler phases:

```zen
import zen.memory as memory

function process_large_payload(records) {
    // 16MB arena allocated upon entry, freed in O(1) upon exit
    with memory.create_arena(16 * 1024 * 1024) as arena {
        do for record in records {
            let processed -> transform_record(record)
            save_record(processed)
        }
    }
}
```

---

## 6. Documentation Comments (`/! ... !/`)

Use docblocks (`/! ... !/`) for all public functions, classes, structures, and modules:

```zen
/!
  Formats tabular data with customizable borders and column alignment.
  @param headers List of column header strings.
  @param rows List of row data lists.
  @param options Optional map with "style", "align", and "padding".
  @return Formatted multi-line string.
  @example
      let t -> format_table(["A", "B"], [[1, 2]], {})
!/
function format_table(headers, rows, options) {
    // ...
}
```
