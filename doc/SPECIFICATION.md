# The Zenlang Language Specification

| Attribute | Value |
|:---|:---|
| **Role** | Canonical Language Specification (Single Source of Truth) |
| **Authority** | Authoritative Ground Truth for Grammar, Syntax, Types, and Semantics |
| **Execution Target** | Dual-Path (Script Bytecode VM & Ahead-of-Time C Compilation) |
| **Value ABI** | `ZenValue` Universal Tagged-Union Layer |
| **Platform Version** | `v1.0.0-beta.1` (Unified Developer Platform & Native Self-Host Closure) |
| **Documentation Standards** | [DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## Table of Contents

1. [Architecture & Design Philosophy](#1-architecture--design-philosophy)
2. [Source Representation & Lexical Grammar](#2-source-representation--lexical-grammar)
3. [Variables, Mutability & Sentinels](#3-variables-mutability--sentinels)
4. [Data Types & Type Hierarchy](#4-data-types--type-hierarchy)
5. [The 5 Core Collection Types](#5-the-5-core-collection-types)
   - [5.1 Collection Syntax Modes](#51-collection-syntax-modes)
   - [5.2 First-Class Collection Member Methods](#52-first-class-collection-member-methods)
   - [5.3 Sequence Slicing & Negative Indexing](#53-sequence-slicing--negative-indexing)
   - [5.4 Directional Comprehensions](#54-directional-comprehensions)
   - [5.5 Collection Spreads (`...`)](#55-collection-spreads-)
6. [Operators, Logic & Precedence](#6-operators-logic--precedence)
   - [6.6 Flow Operators: Null Coalescing (`??`) & Pipeline (`|>`)](#66-flow-operators-null-coalescing--pipeline-)
   - [6.7 Symbol Keywords & Aliases](#67-symbol-keywords--aliases)
   - [6.8 Operator Precedence Table](#68-operator-precedence-table)
7. [First-Class Type Casting](#7-first-class-type-casting)
   - [7.1 `Byte` Casting & Conversions](#71-byte-casting--conversions)
   - [7.2 Sized Type Casting & Bit-Width Truncation](#72-sized-type-casting--bit-width-truncation)
   - [7.3 Type Cast Matrix](#73-type-cast-matrix)
   - [7.4 Universal Type Introspection (`type(x)`)](#74-universal-type-introspection-typex)
8. [Control Flow & Branching](#8-control-flow--branching)
9. [Pattern Matching & Destructuring](#9-pattern-matching--destructuring)
10. [Functions, Returns & Closures](#10-functions-returns--closures)
11. [Container Types & Object Architecture](#11-container-types--object-architecture)
12. [Error Handling & Resilience Model](#12-error-handling--resilience-model)
13. [Modules, Namespaces & Packaging](#13-modules-namespaces--packaging)
   - [13.1 Importing Modules](#131-importing-modules)
   - [13.2 Intrinsic `module` Metadata](#132-intrinsic-module-metadata)
   - [13.3 Direct C Header Imports (`extern use`)](#133-direct-c-header-imports-extern-use)
   - [13.4 Dynamic Foreign Function Interface (FFI) & Zero-Glue System Modules](#134-dynamic-foreign-function-interface-ffi--zero-glue-system-modules)
14. [Scoped Resource Management & Memory Arenas (`with`)](#14-scoped-resource-management--memory-arenas-with)
15. [The Unified Task Concurrency Substrate](#15-the-unified-task-concurrency-substrate)
16. [Developer Toolchain & CLI Reference](#16-developer-toolchain--cli-reference)

---

## 1. Architecture & Design Philosophy

Zenlang is a modern, optionally typed, Unix-native programming language designed for building scripts, terminal applications, system utilities, and networked services using a single, unified execution model.

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

### 1.1 Core Directives
1. **Visual Data Flow:** Data movement is visually intuitive: assignment flows left-to-right (`->`), and function return emits outward (`<-`).
2. **Explicitness Over Magic:** No hidden control flow, silent coercions, or implicit variable capture. Code does exactly what is written.
3. **Terminal-First Ergonomics:** The terminal is a primary execution environment with native stream buffering, layout canvas, raw keyboard polling, and ANSI color math.
4. **Three-Layer Execution Architecture:**
   - **Layer 1: Universal `ZenValue` ABI:** Tagged-union value layer powering complete bidirectional interop between interpreted scripts and compiled binaries.
   - **Layer 2: Compiler Positional IR:** Flat, cache-locality optimized AST lists for high compiler throughput and instant arena cleanup.
   - **Layer 3: Dual Execution Engine:** Fast script execution via Bytecode VM paired with Ahead-of-Time (AOT) C compilation producing standalone native executables.

---

## 2. Source Representation & Lexical Grammar

### 2.1 File Formats & Encoding
Zenlang source and data files must be encoded in **UTF-8**:
- **`*.zl` (Zenlang Source Code):** Executable scripts, library modules, and applications.
- **`*.zd` (Zen Data):** Declarative data serialization format (native replacement for JSON/YAML).
- **`*.zm` (Zen Mark):** Lightweight markup format for terminal user interfaces and documentation.

Whitespace (spaces, tabs, newlines) serves only to delimit tokens. Indentation is purely stylistic and has no syntactic meaning. Scopes are explicitly delimited by braces (`{ ... }`).

### 2.2 Comments
Zenlang defines three comment styles:

```zl
// 1. Single-line comment: Extends to end of physical line.

/*
   2. Multi-line block comment:
      Spans multiple lines. Comments do not nest.
*/

/!
   3. Documentation comment:
      Attached to following symbols (functions, structs, classes)
      and parsed by `zen doc` tools.
!/
```

### 2.3 Identifiers
- **Syntax:** `[a-zA-Z_][a-zA-Z0-9_]*`
- **Variables & Functions:** `snake_case` (e.g. `user_count`, `parse_header`)
- **Types, Structures, Classes & Enums:** `PascalCase` (e.g. `Integer`, `HttpRequest`, `Color`)
- **Constants & Sentinels:** `UPPER_CASE` or `PascalCase` (e.g. `MAX_BUFFER`, `Nothing`, `Default`, `True`, `False`)

### 2.4 Keywords & Reserved Symbols
- **Storage & Binding:** `let`, `set`
- **Control Flow:** `when`, `or`, `do`, `while`, `for`, `in`, `until`, `break`, `continue`, `before`, `after`, `case`
- **Functions & Concurrency:** `function`, `return`, `task`, `yield`
- **Modules & Namespaces:** `use`, `from`, `import`, `export`, `as`
- **Container Types & OOP:** `structure`, `object`, `class`, `extends`, `enumerator`, `enum`, `self`, `parent`, `is`, `is not`
- **Error Handling & Scoping:** `check`, `raise`, `assert`, `with`, `defer`
- **Sentinels:** `Nothing`, `Default`, `True`, `False`
- **Visual Operator Symbols:**
  - `->` (`assign`): Variable / property assignment
  - `<-` (`return`): Function return / emit
  - `:>` (`infer`): Inferred type-lock declaration
  - `:`  (`type`): Explicit type annotation
  - `<:` (`cast`): First-class type casting
  - `<~` (`yield`): Generator value emission
  - `~`  (`defer`): Deferred cleanup block
  - `?`  (`check`): Exception unwrapping / check
  - `!`  (`assert`): Invariant contract assertion
  - `^`  (`raise`): Exception unwinding / raise

---

## 3. Variables, Mutability & Sentinels

Zenlang strictly separates mutable variables from immutable constants.

### 3.1 `let` (Mutable) vs `set` (Constant)
- **`let`:** Declares a mutable variable that can be rebound.
- **`set`:** Declares an immutable constant that cannot be reassigned once initialized.

```zl
let counter -> 0
counter -> counter + 1        // Valid reassignment

set MAX_LIMIT -> 1024
// MAX_LIMIT -> 2048         // Compile-time error: cannot reassign constant
```

### 3.2 Visual Assignment (`->`)
The visual arrow operator `->` assigns and binds the value of the expression on the right into the target identifier on the left:

```zl
// Variable assignment / reassignment:
total -> 100 + 50
language_name -> `Zen`
```

### 3.3 Declaration & Typing Modes

```zl
// 1. Dynamic Variant (Polymorphic & Inferred)
let payload -> 100

// 2. Explicit Type Annotation
let port : Integer -> 8080
set HOST : String -> `127.0.0.1`

// 3. Inferred Type Lock (:>)
let status :> `Active` // Locked to String; rejects non-string assignments later
```

### 3.4 Sentinels: `Nothing` vs `Default`

Zenlang eliminates null-pointer ambiguities using two standardized, capitalized sentinels:

| Sentinel | Meaning | Materialized Zero-Value |
|:---|:---|:---|
| **`Nothing`** | Explicit absence of a value (unassigned, missing). | `ZEN_NOTHING` |
| **`Default`** | Type natural zero-state (`0`, `0.0`, ```` ````, `False`, `[]`, `{}`). | Type Zero-Value |

```zl
let user_token : String -> Nothing
let attempts   : Integer -> Default // Evaluates to 0
let flags      : List    -> Default // Evaluates to []

when user_token == Nothing {
    // Handle unauthenticated state
}

when attempts == Default {
    // Evaluates to True when attempts is 0
}
```

---

## 4. Data Types & Type Hierarchy

Zenlang provides a robust, optionally typed type system with fine-grained numeric and text representations.

### 4.1 Base Types Table

Zenlang strictly enforces canonical type names with zero informal aliases. Informal abbreviations (such as `Int`, `Int64`, `Int32`, `Int16`, `Int8`, `UInt8`, `Float`, `Float64`, `Float32`, `Double`, `Str`, `Bool`, `Char`, `Glyph`, and `Buffer`) are deprecated and strictly forbidden.

| Type Name | Sized Forms | Description | Default Zero-State (`Default`) | Example Literal / Cast |
|:---|:---|:---|:---|:---|
| **`Integer`** | `Integer[8]`, `Integer[16]`, `Integer[32]`, `Integer[64]` | Signed integer (defaults to 64-bit signed) | `0` | `42`, `-10`, `70000 <: Integer[16]` |
| **`Decimal`** | `Decimal[32]`, `Decimal[64]` | IEEE 754 floating point (defaults to 64-bit) | `0.0` | `3.14159`, `-0.5`, `3.5 <: Decimal[32]` |
| **`Byte`** | — | 8-bit unsigned raw byte (`0x00..0xFF`) | `0x00` | `0x41`, `300 <: Byte`, `Byte(0x7B)` |
| **`Bytes`** | — | Sequence / buffer of `Byte` values | `Bytes{}` | `Bytes{ 0xDE, 0xAD }`, `B{ 0x01 }` |
| **`String`** | `String[SIZE]` | UTF-8 encoded text buffer (length-clamped if sized) | ```` ```` | ```` `Hello, Zen!` ````, ```` `HelloWorld` <: String[5] ```` |
| **`Boolean`** | — | Boolean truth values (`True` / `False`) | `False` | `True`, `False` |
| **`Rune`** | — | 32-bit Unicode code point scalar | `'\0'` | `'A'`, `'\n'` |
| **`Void`** | — | Unit type representing absence of return | `Void` | `Void` |
| **`Nothing`** | — | Absent / unassigned value | `Nothing` | `Nothing` |
| **`Default`** | — | Type natural zero-state value | `Default` | `Default` |
| **`Variant`** | — | Dynamic tagged-union container | `Nothing` | (any value) |

### 4.2 Numeric Prefixes & Separators
Zenlang supports standard base prefixes and underscore readability separators:

```zl
let hex_val  -> 0x7B             // Hexadecimal (prefix 0x)
let oct_val  -> 0o173            // Octal (prefix 0o)
let bin_val  -> 0b0111_1011      // Binary (prefix 0b)
let big_num  -> 1_000_000        // Underscore digit separator
let hex_blob -> 0xDE_AD_BE_EF    // Formatted hex
```

### 4.3 String Literals & Multi-Line Strings
- **Single-Line Strings:** Single backticks: ```` `Hello, World!` ````
- **Formatted Strings:** Prefixed single backticks: ```` f`Count is {count}` ````
- **Multi-Line Strings:** Triple backticks:
  ````zl
  let banner -> ```
  ==============================
     ZENLANG SYSTEM UTILITY
  ==============================
  ```
  ````

### 4.4 The Unified Type Universe

Zenlang categorizes all values into five clear structural families:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                               THE TYPE UNIVERSE                                │
├──────────────────────────┬─────────────────────────────────────────────────────┤
│ **1. Primitive Scalars** │ `Integer`, `Integer[SIZE]`, `Decimal`,              │
│                          │ `Decimal[SIZE]`, `Byte`, `Bytes`, `String`,         │
│                          │ `String[SIZE]`, `Boolean`, `Rune`, `Void`,          │
│                          │ `Nothing`, `Default`                                │
├──────────────────────────┼─────────────────────────────────────────────────────┤
│ **2. Core Collections**  │ `List` (Dynamic array), `Set` (Unique set),         │
│                          │ `Vector` / `Vector[LENGTH]` (Fixed array),          │
│                          │ `Tuple` (Fixed record), `Map` (Dictionary)          │
├──────────────────────────┼─────────────────────────────────────────────────────┤
│ **3. Container Tiers**   │ `structure` (Fixed C ABI value record),             │
│                          │ `object` (Fluid runtime entity + Zen Data .zd),     │
│                          │ `class` (Nominal OOP with `extends`),               │
│                          │ `enumerator` / `enum` (Named variant states)        │
├──────────────────────────┼─────────────────────────────────────────────────────┤
│ **4. Action & Async**    │ `Function` (First-class callable),                  │
│                          │ `Task` (Suspendable concurrent fiber),              │
│                          │ `Channel` (Message-passing queue)                   │
├──────────────────────────┼─────────────────────────────────────────────────────┤
│ **5. Polymorphic & Err** │ `Variant` (Universal tagged-union container),       │
│                          │ `Error` (Structured runtime error instance)         │
└──────────────────────────┴─────────────────────────────────────────────────────┘
```

### 4.5 Abstract & Union Types

Zenlang provides four first-class abstract union types that categorize related base types for pattern matching, type annotations, and type casting:

| Abstract Type | Underlying Subtypes | Description | Example Pattern / Cast |
|:---|:---|:---|:---|
| **`Number`** | `Integer` (including sized `Integer[8..64]`, `Byte`), `Decimal` (`Decimal[32..64]`) | Any numeric value | `val is Number`, `Number("42")`, `"3.14" <: Number` |
| **`Text`** | `String` (including sized `String[SIZE]`), `Rune` | Any character or string textual value | `val is Text`, `Text(123)`, `42 <: Text` |
| **`Collection`** | `List`, `Vector`, `Set`, `Tuple`, `Map` | Any composite data collection or sequence | `val is Collection`, `Collection("abc")` |
| **`Container`** | `Structure`, `Object`, `Class`, `Enumerator` | Any record, OOP class instance, or enum state | `val is Container` |

Abstract types can be used across all typing and control flow constructs:

```zl
// 1. Type Testing and Pattern Matching
when input is Number {
    // Matches Integer, Decimal, Byte
}
when input is Text {
    // Matches String, Rune
}
when input is Collection {
    // Matches List, Map, Set, Vector, Tuple
}
when input is Container {
    // Matches Structure, Class, Object, Enumerator
}

// 2. Type Annotations
let count    : Number     -> 42
let greeting : Text       -> `hello`
let items    : Collection -> [1, 2, 3]

// 3. Type Casting
let n -> `3.14` <: Number     // Evaluates to 3.14
let t -> 100 <: Text          // Evaluates to `100`
let c -> `xyz` <: Collection  // Evaluates to [`x`, `y`, `z`]
```

### 4.6 User-Defined Generics & Parameterized Types

Zenlang provides first-class support for parameterized generic types and generic definitions across functions, structures, and classes using standard angle bracket `<...>` syntax:

#### 1. Generic Parameter Declarations
- **Generic Functions:** `function identity<T>(x: T) : T { <- x }`
- **Generic Structures:** `structure Box<T> { value: T }`, `structure Pair<A, B> { first: A, second: B }`
- **Generic Classes:** `class Storage<T> { let item: T ... }`

#### 2. Generic Invocations & Instantiations
- **Explicit Type Arguments:** `identity<Integer>(42)`, `Box<Integer>{ value: 777 }`, `Storage<String>(`initial`)`
- **Type-Inferred Calls:** `identity(100)` automatically infers `T -> Integer`
- **Pattern Matching & Structural Subtyping:** Generic types unify structurally; `Box<Integer>` matches `b is Box` and `b is Box<Integer>`.

#### 3. Strict Canonical Type Enforcement
In accordance with Zenlang type rules, informal single-letter abbreviations (`T`, `L`, `S`, `M`, `V`) remain strictly forbidden as collection type aliases, and are only valid identifiers when explicitly declared as active generic type parameters in the current lexical scope.

---

## 5. The 5 Core Collection Types

Zenlang provides 5 distinct first-class collection types covering all combinations of ordering, mutability, and sizing:

| Collection Type | Ordering | Size | Mutability | Elements |
|:---|:---|:---|:---|:---|
| **`List`** | Ordered | Dynamic | Mutable | Homogeneous / Heterogeneous values |
| **`Set`** | Unordered | Dynamic | Mutable | Unique values |
| **`Vector`** | Ordered | Fixed-size | Immutable | Values |
| **`Tuple`** | Ordered | Fixed-size | Immutable | Heterogeneous values (optional field names) |
| **`Map`** | Unordered | Dynamic | Mutable | Key-Value pairs (`key -> value`) |

### 5.1 Collection Syntax Modes

#### 1. Explicit Type-Tagged Literals (`Type{ ... }`)
Can be used anywhere in expressions with complete clarity:

```zl
// 1. Vector (Fixed, Immutable)
let v -> Vector{ 1, 2, 3, 4 }

// 2. Set (Dynamic, Unique)
let s -> Set{ 1, 2, 3, 4 }

// 3. Tuple (Fixed, Heterogeneous / Named)
let t -> Tuple{ `Attack`, 100, True }
let nt -> Tuple{ name -> `Alice`, score -> 95 } // Named Tuple

// 4. List (Dynamic, Ordered)
let l -> List{ 1, 2, 3 }

// 5. Map (Key-Value)
let m -> Map{ `a` -> 1, `b` -> 2 }
```

#### 2. Contextual Type Inference (`let x : Type -> { ... }`)
When an identifier has an explicit type annotation, generic braces `{ ... }` automatically materialize into that specific type:

```zl
let a : Vector -> { 1, 2, 3 }       // Materializes as Vector
let b : Set    -> { 1, 2, 3 }       // Materializes as Set
let c : List   -> { 1, 2, 3 }       // Materializes as List
let d : Tuple  -> { 1, `a`, True }  // Materializes as Tuple
let e : Map    -> { `a` -> 1 }      // Materializes as Map
```

#### 3. Untyped Shorthand Literals
For fast daily scripting, Zenlang maps the 3 ASCII bracket pairs to their most common defaults:
- **`[1, 2, 3]`** $\rightarrow$ Defaults to **`List`**
- **`{ key -> value }`** $\rightarrow$ Defaults to **`Map`**
- **`(1, 2, 3)`** $\rightarrow$ Defaults to **`Tuple`**

---

### 5.2 First-Class Collection Member Methods

Zenlang provides expressive built-in member methods across core collection types with 100% execution parity across interpreter VM, bytecode runtime, and native AOT compiled binaries:

#### `List` Member Methods
- **Transformation & Reordering:**
  - `list.reverse()`: Returns a new reversed list.
  - `list.unique()`: Returns a new list with duplicate elements removed (preserving initial insertion order).
  - `list.flatten()`: Recursively flattens nested lists into a single-depth list.
  - `list.chunk(size)`: Chunks elements into sublists of length `size`.
- **Selection & Slicing:**
  - `list.take(count)`: Returns the first `count` elements.
  - `list.drop(count)`: Returns all elements following the first `count` elements.
  - `list.join(delimiter)`: Joins string representations of elements with `delimiter`.
- **Higher-Order Combinators:**
  - `list.map(fn)`: Transforms elements through unary mapping function `fn`.
  - `list.filter(fn)`: Retains elements where predicate `fn(x)` evaluates truthy.
  - `list.reduce(fn, initial)`: Accumulates values left-to-right via `fn(acc, item)`.
  - `list.each(fn)`: Iterates over elements executing `fn(x)` for side-effects.
  - `list.find(fn)`: Returns first element satisfying `fn(x)`, or `Nothing`.
  - `list.any(fn)`: Evaluates `True` if at least one element satisfies `fn(x)`.
  - `list.all(fn)`: Evaluates `True` if every element satisfies `fn(x)`.

#### `Map` Member Methods
- `map.keys()`: Returns a list of all map keys.
- `map.values()`: Returns a list of all map values.
- `map.items()`: Returns a list of `Tuple{ key, value }` pairs.
- `map.has(key)`: Returns `True` if `key` exists in map.
- `map.get(key, default_val?)`: Retrieves value for `key`, returning `default_val` or `Nothing` if missing.
- `map.merge(other_map)`: Returns a new merged map with keys from `other_map` overriding.
- `map.invert()`: Returns a new map with values inverted into keys.

#### `Set` Member Methods
- `set.to_list()`: Materializes set elements as a list.
- `set.has(item)`: Tests containment (`item in set`).
- `set.add(item)`: Inserts element into set.
- `set.remove(item)`: Removes element from set.
- `set.union(other_set)`: Set union ($A \cup B$).
- `set.intersection(other_set)`: Set intersection ($A \cap B$).
- `set.difference(other_set)`: Set difference ($A \setminus B$).

---

### 5.3 Sequence Slicing & Negative Indexing

Strings and Lists support uniform Python-style interval slicing and negative indexing:

```zl
let items -> [10, 20, 30, 40, 50]
let word  -> `Zenlang`

// 1. Negative indexing (counting from end)
let last_item -> items[-1]       // 50
let last_char -> word[-1]        // 'g'

// 2. Interval slicing: seq[start:end:step]
let sub -> items[1:4]            // [20, 30, 40]
let pre -> word[:3]              // `Zen`
let post -> word[3:]             // `lang`

// 3. Stepping and sequence reversal
let evens -> items[::2]          // [10, 30, 50]
let rev_word -> word[::-1]       // `gnalneZ`
let rev_list -> items[::-1]      // [50, 40, 30, 20, 10]
```

---

### 5.4 Directional Comprehensions

Zenlang introduces **Directional Comprehensions**, leveraging Zen's signature `->` data-flow operator to transform and filter collections concisely without imperative loops or callbacks:

#### 1. Directional List Comprehensions
A list comprehension consists of bracket delimiters `[...]` enclosing an iterative generator clause `for <var> in <iterable>`, an optional filtering predicate `when <condition>`, and the visual transformation arrow `-> <expression>`:

```zl
// Standard transformation:
let squares -> [for x in 1...5 -> x * x]
// Result: [1, 4, 9, 16, 25]

// Filtered transformation (when clause):
let evens -> [for x in 1...10 when x % 2 == 0 -> x]
// Result: [2, 4, 6, 8, 10]

// Transforming existing collections:
let names -> [`alice`, `bob`, `charlie`]
let shout -> [for name in names -> name + `!`]
// Result: [`alice!`, `bob!`, `charlie!`]
```

#### 2. Directional Map Comprehensions
A map comprehension enclosed within braces `{...}` iterates over collections or key-value sequences to construct a dynamic `Map`:

```zl
// Constructing inverted or keyed records:
let users -> [{ `id` -> 101, `name` -> `Alice` }, { `id` -> 102, `name` -> `Bob` }]
let id_lookup -> {for u in users -> u.id: u.name}
// Result: { 101 -> `Alice`, 102 -> `Bob` }

// Filtered map comprehension:
let scores -> { `Alice` -> 95, `Bob` -> 62, `Charlie` -> 88 }
let honors -> {for k, v in scores when v >= 80 -> k: v}
// Result: { `Alice` -> 95, `Charlie` -> 88 }
```

---

### 5.5 Collection Spreads (`...`)

The collection spread operator `...` unpacks elements of an existing collection into a newly constructed literal:

#### 1. List Spreading
```zl
let head -> [1, 2, 3]
let tail -> [4, 5, 6]
let combined -> [...head, ...tail, 7, 8]
// Result: [1, 2, 3, 4, 5, 6, 7, 8]
```

#### 2. Map Spreading & Immutable Merging
In map literals, spreading unpacks key-value pairs into the new map. Subsequent entries override earlier keys, providing clean immutable update patterns:

```zl
let default_cfg -> { `host` -> `localhost`, `port` -> 8080, `debug` -> False }
let production_cfg -> {
    ...default_cfg,
    `host` -> `zenlang.org`,
    `debug` -> True
}
```

---

## 6. Operators, Logic & Precedence

Zenlang provides an expressive, complete digital logic and arithmetic operator system structured around a clear design principle: **Words represent Boolean Logical Gates**, while **Doubled Symbols represent Bitwise Binary Gates**.

### 6.1 Arithmetic & Numeric Operators

| Operator | Name | Example | Description |
|:---|:---|:---|:---|
| **`+`** | Addition / Concat | `a + b` | Adds numbers, concatenates strings/lists |
| **`-`** | Subtraction / Negation | `a - b`, `-a` | Arithmetic subtraction or unary negation |
| **`*`** | Multiplication | `a * b` | Numeric multiplication |
| **`/`** | Float Division | `a / b` | True floating-point division |
| **`//`** | Integer Quotient | `a // b` | Truncated floor / integer division |
| **`%`** | Modulo (Exclusive) | `a % b` | Standard remainder |
| **`%%`** | Modulo (Inclusive) | `a %% b` | Mathematical Euclidean wrapping modulo |
| **`**`** | Exponentiation | `a ** b` | Power (e.g. `2 ** 8` $\rightarrow$ `256`) |

### 6.2 Boolean Logic vs. Bitwise Binary Gates

Zenlang features complete 7-gate digital logic across both boolean and binary domains:

| Logic Gate | Boolean Logical (Keywords) | Bitwise Binary (Doubled Symbols) | Semantics |
|:---|:---|:---|:---|
| **AND** | `a and b` | `a && b` | True/1 if both operands are True/1 |
| **OR** | `a or b` | `a \|\| b` | True/1 if either operand is True/1 |
| **NOT** | `not a` | `!!a` | Logical / Bitwise inversion |
| **XOR** | `a xor b` | `a ^^ b` | Exclusive OR (True/1 if operands differ) |
| **NAND** | `a nand b` | `a !& b` | Inverted AND: `not (a and b)` |
| **NOR** | `a nor b` | `a !\| b` | Inverted OR: `not (a or b)` |
| **XNOR** | `a xnor b` | `a !^ b` | Equivalence (True/1 if operands match) |
| **SHIFTS** | — | `a << b`, `a >> b` | Binary shift left / shift right |

### 6.3 Comparison & Relational Operators

| Operator | Meaning | Example |
|:---|:---|:---|
| **`==`** | Equal (Deep structural equality) | `x == 42`, `list == [1, 2]` |
| **`!=`** | Not Equal | `x != 0`, `status != Nothing` |
| **`<`** | Less Than | `a < 10` |
| **`>`** | Greater Than | `score > 100` |
| **`<=`** | Less Than or Equal | `count <= max_count` |
| **`>=`** | Greater Than or Equal | `level >= 5` |
| **`in`** | Membership / Containment (List, Map, Set, String, Range) | `42 in nums`, `'key' in map`, `'zen' in str` |
| **`is`** | Type / Pattern Match | `when val is Integer` |
| **`is not`** | Negative Type Test | `when val is not Nothing` |

### 6.4 The 4-Range Boundary System

Zenlang defines four distinct range operators providing exact mathematical control over boundary endpoints:

| Range Syntax | Name | Math Interval | Ascending (`0` to `5`) | Descending (`5` to `0`) |
|:---|:---|:---|:---|:---|
| **`..`** | Range Between | $(start, end)$ | `[1, 2, 3, 4]` | `[4, 3, 2, 1]` |
| **`..+`** | Range Inclusive End | $(start, end]$ | `[1, 2, 3, 4, 5]` | `[4, 3, 2, 1, 0]` |
| **`..-`** | Range Exclusive End | $[start, end)$ | `[0, 1, 2, 3, 4]` | `[5, 4, 3, 2, 1]` |
| **`...`** | Range Full Inclusive | $[start, end]$ | `[0, 1, 2, 3, 4, 5]` | `[5, 4, 3, 2, 1, 0]` |

```zl
// Loop examples:
do for i in 1...5 {
    // Iterates i = 1, 2, 3, 4, 5
}

let chars -> `a`...`e` // [`a`, `b`, `c`, `d`, `e`]
```

### 6.5 Polymorphic Increment & Decrement (`++` and `--`)

```zl
// 1. Numbers (With Optional Step Amounts)
let count -> 5
count++                       // count becomes 6
count--                       // count becomes 5
count++ 5                     // count becomes 10 (adds 5)
count-- 2                     // count becomes 8  (subtracts 2)

// 2. Strings (Append / Prepend / Drop)
let msg -> `Hello`
msg++ ` World`                // msg becomes `Hello World` (append)
++msg `>> `                   // msg becomes `>> Hello World` (prepend)
msg--                         // drops last character
--msg                         // drops first character

// 3. Lists (Append / Prepend / Drop)
let items -> [1, 2]
items++ 3                     // items becomes [1, 2, 3] (append)
++items 0                     // items becomes [0, 1, 2, 3] (prepend)
items--                       // drops last element -> [0, 1, 2]
--items                       // drops first element -> [1, 2]
```

### 6.6 Flow Operators: Null Coalescing (`??`) & Pipeline (`|>`)

Zenlang provides two dedicated data-flow operators that streamline pipelines and sentinel fallback handling:

#### 1. Nullish / Sentinel Coalescing (`??`)
Evaluates the left operand; if the value equals `Nothing`, evaluates and returns the fallback right operand:

```zl
let username -> input_user ?? `Guest`
let timeout  -> config[`timeout`] ?? 30
```

#### 2. Directional Pipeline (`|>`)
Chains sequential transformations by passing the left-hand expression as the first argument into the right-hand function call:

```zl
use zen.text.string as Str

let clean -> raw_input
    |> Str.trim
    |> Str.to_lower
```
When the target function expects additional arguments, `x |> func(y)` evaluates to `func(x, y)`:
```zl
let result -> `zenlang` |> Str.replace(`zen`, `fast_zen`)
```

---

### 6.7 Symbol Keywords & Aliases

Zenlang provides 1:1 keyword equivalents for visual operators:

| Visual Symbol | English Keyword | Description |
|:---|:---|:---|
| **`->`** | `assign` | Variable / map key assignment |
| **`:>`** | `infer` | Inferred type lock declaration |
| **`:`** | `type` | Explicit type annotation |
| **`<:`** | `cast` | First-class type casting |
| **`<-`** | `return` | Function return / outward emit |
| **`<~`** | `yield` | Generator / coroutine yield |
| **`~`** | `defer` | Deferred block cleanup |
| **`?`** | `check` | Exception check & recovery |
| **`!`** | `assert` | Invariant assertion |
| **`^`** | `raise` | Exception unwinding |

### 6.8 Operator Precedence Table

| Precedence | Operator Class | Operators | Associativity | Description |
|:---|:---|:---|:---|:---|
| **1 (Highest)** | Primary | `()`, `[]`, `.`, `()` (call), `...` (spread) | Left | Member access, indexing, invocation, unpacking |
| **2** | Type Cast | `<:`, `cast` | Left | Type casting operator |
| **3** | Unary | `not`, `-`, `!!`, `++`, `--`, `~`, `?`, `!`, `^` | Right | Unary prefixes, inversions, error ops |
| **4** | Multiplicative | `*`, `/`, `//`, `%`, `%%`, `**` | Left | Multiplication, division, modulo, power |
| **5** | Additive | `+`, `-`, `++`, `--` | Left | Addition, subtraction, concat, postfix ops |
| **6** | Bitwise Shift | `<<`, `>>` | Left | Binary bit shifts |
| **7** | Relational | `<`, `<=`, `>`, `>=`, `in`, `is`, `is not` | Left | Comparison, membership, and type checking |
| **8** | Equality | `==`, `!=` | Left | Structural deep equality |
| **9** | Bitwise Logic | `&&`, `^^`, `\|\|`, `!&`, `!\|`, `!^` | Left | Complete 7-gate bitwise logic |
| **10** | Logical Logic | `and`, `xor`, `or`, `nand`, `nor`, `xnor` | Left | Complete 7-gate boolean logic |
| **11** | Range | `..`, `..+`, `..-`, `...` | Non-assoc | Range construction |
| **12** | Null Coalescing | `??` | Left | Fallback sentinel evaluation |
| **13** | Pipeline | `\|>` | Left | Directional function piping |
| **14 (Lowest)** | Visual Flow | `->`, `<-`, `<~` | Right | Assignment, return, yield |

---

## 7. First-Class Type Casting

Zenlang supports explicit, safe type conversions through dual syntax:
1. **Operator Syntax (`<:`):** `<expression> <: <TargetType>`
2. **Constructor Syntax:** `<TargetType>(<expression>)`

```zl
// Operator syntax:
let n -> `42` <: Integer
let s -> 100 <: String
let b -> 1 <: Boolean
let byte_val -> 65 <: Byte

// Constructor syntax:
let total -> Integer(`500`)
let text -> String(2026)
let raw_byte -> Byte(0x41)
```

### 7.1 `Byte` Casting & Conversions

```zl
let a : Byte -> 0x41

// Casting Byte to other types:
a <: Integer      // 65
a <: Decimal      // 65.0
a <: Rune         // `A`
a <: String       // `0x41`

Integer(a)        // 65
Decimal(a)        // 65.0
Rune(a)           // `A`
String(a)         // `0x41`

// Casting other types to Byte:
65 <: Byte        // 0x41
65.0 <: Byte      // 0x41
`A` <: Byte       // 0x41
`0x41` <: Byte    // 0x41

Byte(65)          // 0x41
Byte(65.0)        // 0x41
Byte(`A`)         // 0x41
Byte(`0x41`)      // 0x41
```

### 7.2 Sized Type Casting & Bit-Width Truncation

Casting to sized types applies deterministic bit-width truncation and wrapping across all execution backends (C runtime, Bytecode VM, Interpreter):

```zl
// Byte: unsigned 8-bit [0..255]
300 <: Byte               // 44 (300 & 0xFF)
(-1) <: Byte              // 255
Byte(300)                 // 44

// Integer[16]: signed 16-bit [-32768..32767]
70000 <: Integer[16]      // 4464
(-32769) <: Integer[16]   // 32767
Integer[16](70000)        // 4464

// Integer[32]: signed 32-bit
5000000000 <: Integer[32] // 705032704
Integer[32](5000000000)   // 705032704

// Decimal[32]: single-precision 32-bit float
3.5 <: Decimal[32]        // 3.5

// String[SIZE]: maximum character length clamping
`HelloWorld` <: String[5] // `Hello`
`Zen` <: String[10]        // `Zen`
```

### 7.3 Type Cast Matrix

| Source Type | Target: `Integer` | Target: `Decimal` | Target: `Byte` | Target: `String` | Target: `Boolean` | Target: `Rune` | Target: `List` | Target: `Map` |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **`Integer`** | Identity | Float value (`n.0`) | `n & 0xFF` | Digits string (``` `42` ```) | `n != 0` | Char from codepoint | `[n]` | `{}` |
| **`Decimal`** | Truncated int | Identity | `int(d) & 0xFF` | Decimal string | `d != 0.0` | Codepoint conversion | `[d]` | `{}` |
| **`Byte`** | Numeric byte (`65`) | Float byte (`65.0`) | Identity | Hex string (``` `0x41` ```) | `b != 0` | Char rune (``` `A` ```) | `[b]` | `{}` |
| **`String`** | Parsed integer | Parsed float | Hex or 1st byte | Identity | ``` `True` / `true` / `1` ``` | 1st character | `[chars]` | `{}` |
| **`Boolean`** | `1` / `0` | `1.0` / `0.0` | `0x01` / `0x00` | ``` `True` / `False` ``` | Identity | ```` ```` | `[b]` | `{}` |
| **`Rune`** | Codepoint value | Float codepoint | Codepoint byte | 1-char string | Non-zero | Identity | `[rune]` | `{}` |
| **`List`** | `.length` | `.length` float | `.length & 0xFF` | String representation | `len > 0` | 1st char | Identity | `{}` |
| **`Map`** | `.length` | `.length` float | `.length & 0xFF` | String representation | `len > 0` | ```` ```` | Key list | Identity |
| **`Nothing`** | `0` | `0.0` | `0x00` | ```` ```` | `False` | ```` ```` | `[]` | `{}` |

### 7.4 Universal Type Introspection (`type(x)`)

Zenlang provides `type(x)` as a first-class universal prelude available without imports. It returns a string naming the underlying Zen type:

```zl
let t1 -> type(42)            // `Integer`
let t2 -> type(3.14)          // `Decimal`
let t3 -> type(`zen`)         // `String`
let t4 -> type(True)          // `Boolean`
let t5 -> type([1, 2, 3])     // `List`
let t6 -> type({`a` -> 1})    // `Map`
let t7 -> type(Set([1, 2]))   // `Set`
let t8 -> type(Nothing)       // `Nothing`
let t9 -> type(Default)       // `Default`
```

For custom structures, classes, or maps declaring a `kind` or `__type__` attribute, `type(x)` returns that declared type name.

### 7.4 Standard Math Library (`zen.math`)

All mathematical operations, trigonometry, interpolations, and constants reside in the standard math module (`import zen.math.math as math` or `use zen.math as math`).

Zenlang implements a **Full Name Primary + Short Name Alias** duality: full descriptive names are declared as the primary functions for readability, while standardized short names (and common industry aliases) are exported as aliases for concise computation:

| Operation | Primary Full Name | Short Name Alias | Additional Aliases |
|:---|:---|:---|:---|
| **Absolute Value** | `absolute(x)` | `abs` | |
| **Minimum** | `minimum(a, b)` | `min` | |
| **Maximum** | `maximum(a, b)` | `max` | |
| **Square** | `square(x)` | `sqr` | |
| **Square Root** | `square_root(x)` | `sqrt` | |
| **Power** | `power(base, exp)` | `pow` | |
| **Cube** | `cube(x)` | `cube` | |
| **Cube Root** | `cube_root(x)` | `cbrt` | |
| **Ceiling** | `ceiling(x)` | `cil` | `ceil` |
| **Floor** | `floor(x)` | `flr` | |
| **Round** | `round(x)` | `rnd` | |
| **Clamp** | `clamp(val, lo, hi)` | `clp` | |
| **Sine** | `sine(x)` | `sin` | |
| **Cosine** | `cosine(x)` | `cos` | |
| **Tangent** | `tangent(x)` | `tan` | |
| **Cotangent** | `cotangent(x)` | `cot` | |
| **Secant** | `secant(x)` | `sec` | |
| **Cosecant** | `cosecant(x)` | `csc` | |
| **Arc Tangent** | `arc_tangent(x)` | `atan` | |
| **Arc Tangent 2** | `arc_tangent_2(y, x)` | `atan2` | |
| **Arc Sine** | `arc_sine(x)` | `asin` | |
| **Arc Cosine** | `arc_cosine(x)` | `acos` | |
| **Hypotenuse** | `hypotenuse(x, y)` | `hyp` | |
| **Linear Interpolation** | `linear_interpolate(a, b, t)` | `lerp` | |
| **Inverse Lerp** | `inverse_linear_interpolate(a, b, x)` | `ilrp` | |
| **Smooth Interpolation** | `smooth_interpolate(e0, e1, x)` | `serp` | `smoothstep` |
| **Sign** | `sign(x)` | `sgn` | `signum` |
| **Float Modulo** | `float_modulo(a, b)` | `fmod` | |
| **Exponential** | `exponential(x)` | `exp` | |
| **Base-2 Exponent** | `exponential_base_2(x)` | `exp2` | |
| **Natural Logarithm** | `logarithm(x)` | `log` | |
| **Base-10 Logarithm** | `logarithm_base_10(x)` | `log10` | |
| **Base-2 Logarithm** | `logarithm_base_2(x)` | `log2` | |
| **Fractional Part** | `fraction(x)` | `frc` | |
| **Truncate** | `truncate(x)` | `trc` | |
| **Step Threshold** | `step(edge, x)` | `stp` | |
| **Hyperbolic Sine** | `hyperbolic_sine(x)` | `sinh` | |
| **Hyperbolic Cosine** | `hyperbolic_cosine(x)` | `cosh` | |
| **Hyperbolic Tangent** | `hyperbolic_tangent(x)` | `tanh` | |
| **Hyperbolic Cotangent** | `hyperbolic_cotangent(x)` | `coth` | |
| **Hyperbolic Secant** | `hyperbolic_secant(x)` | `sech` | |
| **Hyperbolic Cosecant** | `hyperbolic_cosecant(x)` | `csch` | |
| **Arc Hyperbolic Sine** | `arc_hyperbolic_sine(x)` | `asinh` | |
| **Arc Hyperbolic Cosine** | `arc_hyperbolic_cosine(x)` | `acosh` | |
| **Arc Hyperbolic Tangent** | `arc_hyperbolic_tangent(x)` | `atanh` | |
| **Arc Hyperbolic Cotangent** | `arc_hyperbolic_cotangent(x)` | `acoth` | |
| **Arc Hyperbolic Secant** | `arc_hyperbolic_secant(x)` | `asech` | |
| **Arc Hyperbolic Cosecant** | `arc_hyperbolic_cosecant(x)` | `acsch` | |
| **Is Infinite** | `is_infinite(x)` | `inf` | |
| **Is Not-A-Number** | `is_not_a_number(x)` | `nan` | |
| **Is Finite** | `is_finite(x)` | `fnt` | |

---

## 8. Control Flow & Branching

Zenlang provides clean, keyword-driven control flow structures that replace traditional C-style constructs with expressive `when` branching, `check` matching tables, and `do` loops with fallback branches and iteration hooks.

### 8.1 Conditional Branching (`when ... or`)

```zl
// 1. Multi-Branch Statement Form:
when score >= 90 {
    grade -> `A`
} or when score >= 80 {
    grade -> `B`
} or {
    grade -> `C`
}

// 2. Single-Line Form:
when is_valid { save_record() } or { log_error() }

// 3. Inline Expression Form (Ternary Replacement):
let status -> `Online` when is_connected or `Offline`
let discount -> 0.20 when is_vip or 0.0

// 4. Inline Function Return:
<- result when is_valid or Default
```

### 8.2 Multi-Branch Match & Switch (`check`)

`check` serves as Zenlang's structured multi-way branching and condition table construct:

#### 1. Value-Match Mode
```zl
check status_code {
    case 200 { io.info(`OK`) },
    case 404 { io.warn(`Not Found`) },
    case 500 { io.error(`Server Error`) }
} or {
    io.error(`Unknown status code`)
}
```

#### 2. Condition-Mode (No Target Identifier)
Evaluates boolean expressions in order; first truthy case executes:
```zl
check {
    case score >= 90 { grade -> `A` },
    case score >= 80 { grade -> `B` },
    case score >= 70 { grade -> `C` }
} or {
    grade -> `F`
}
```

#### 3. Expression-Returning Match
```zl
let exit_code -> check command {
    case `start`   <- 0,
    case `stop`    <- 1,
    case `restart` <- 2
} or <- -1
```

### 8.3 Looping Constructs (`do`)

All looping constructs in Zenlang begin explicitly with the `do` keyword:

```zl
// 1. Infinite / Base Block Loop
do {
    poll_events()
}

// 2. Pre-Condition While Loop (with optional `or` if loop never executed):
do while has_work() {
    process_next_job()
} or {
    io.writeln(`No jobs to process.`) // Runs if condition was False on entry
}

// 3. Pre-Condition Until Loop (runs until condition becomes True):
let ready -> False
do until ready {
    ready -> check_ready()
}

// 4. For-In Collection & Range Loop (with optional `or` if empty):
do for item in active_users {
    render_user(item)
} or {
    io.writeln(`User list is empty.`) // Runs if active_users had 0 elements
}

// Full inclusive range loop:
do for i in 1...5 {
    io.writeln(`Step: ` + Str.to_string(i))
}

// Key-Value map unpacking:
do for key, val in user_data {
    io.writeln(key + `: ` + Str.to_string(val))
}

// 5. Post-Condition Loops
let attempts -> 0
do {
    attempts++
} while attempts < 3 and not success

do {
    read_chunk()
} until stream.is_eof()

// 6. Iteration Hooks (`before` and `after`)
do while running {
    process_frame()
} before {
    clear_screen()
} after {
    render_screen()
}

// 7. Loop Control
break       // Immediately exits innermost loop
continue    // Skips to next iteration
```

---

## 9. Pattern Matching & Destructuring

Zenlang provides first-class pattern matching through both single-pattern `when ... is` expressions and multi-pattern `check` tables.

### 9.1 Single-Pattern Extraction (`when <target> is <pattern>`)

```zl
// 1. List Spread & Slicing:
let payload -> [10, 20, 30, 40]
when payload is [head, ...tail] {
    io.info(`Head: ` + Str.to_string(head)) // 10
    io.info(`Tail: ` + Str.to_string(tail)) // [20, 30, 40]
}

// 2. Map Destructuring:
let user -> { `name` -> `Bob`, `role` -> `Admin` }
when user is { name, role } {
    io.info(name + ` has role ` + role)
}

// 3. Tuple Destructuring:
let pair -> (`Attack`, 100)
when pair is (stat, value) {
    io.info(stat + `: ` + Str.to_string(value))
}

// 4. Guards & Wildcards (_):
let val -> 150
when val is Integer and val > 100 {
    io.info(`Large Integer: ` + Str.to_string(val))
}

let coords -> [1, 999, 3]
when coords is [1, _, 3] {
    io.info(`Matched wildcard pattern`)
}
```

### 9.2 Multi-Pattern Matching (`check <target>`)

```zl
check payload {
    case []                              { io.info(`Empty list`) },
    case [head, ...tail]                 { io.info(`Head element: ` + Str.to_string(head)) },
    case { `status` -> `ok`, `data` -> d} { io.info(`Success payload`) },
    case in 1...100                      { io.info(`Numeric range match`) },
    case is String                       { io.info(`String payload`) }
} or {
    io.error(`Unrecognized payload shape`)
}
```

---

## 10. Functions, Returns & Closures

Functions in Zenlang are first-class citizens with support for explicit or inferred return types, parameterless signatures without empty parentheses, single-expression arrow bodies (`->`), parameter defaults, and snapshot-by-value closures.

### 10.1 Function Declarations

```zl
// 1. Parameterless function (no parentheses required):
function say_hello {
    <- `Hello`
}

// 2. Return type with block body:
function get_number : Integer {
    <- 42
}

// 3. Typed parameters and return type:
function add : Integer (a: Integer, b: Integer) {
    <- a + b
}

// 4. Single-expression arrow bodies:
function get_answer : Integer -> 42
function greet : String (name: String) -> `Hello, ` + name

// 5. Default parameter values:
function connect(host: String, port: Integer -> 8080, timeout: Integer -> 30) : Boolean {
    io.info(`Connecting to ` + host + `:` + Str.to_string(port))
    <- True
}
```

### 10.2 Return Keywords & Visual Return (`<-` and `return`)
Functions emit their return value using either the visual return arrow `<-` or the `return` keyword:

```zl
function check_status(code: Integer) : String {
    when code == 200 {
        <- `OK`
    } or {
        return `Error`
    }
}
```

### 10.3 First-Class Anonymous Functions (Lambdas)

Lambdas can be written using block bodies or single-expression arrow/emit syntax:

```zl
// 1. Single-expression lambda:
let greet -> function(name) <- `Hello, ` + name

// 2. Arrow lambda:
let square -> function(x) -> x * x

// 3. Typed lambda:
let add : Function<Integer> -> function(a: Integer, b: Integer) {
    <- a + b
}

use zen.collections.list as List
let numbers -> [1, 2, 3, 4]
let doubled -> List.map(numbers, function(x) -> x * 2)
```

### 10.4 Lexical Closures (Snapshot by Value)
Closures capture outer local variables **by value** at the exact moment of function creation:

```zl
let factor -> 10
let multiplier -> function(x) { <- x * factor } // Captures factor == 10

factor -> 99
let result -> multiplier(5) // Returns 50 (5 * 10)
```

### 10.5 Entry Points & Dynamic Program Arguments (`main`)
Executable Zenlang programs define their entry point via `function main`:
- **Dynamic Arity Binding:** `function main(args)` dynamically accepts command-line arguments as a Zenlang `List` of strings.
- **Zero-Parameter Entry:** `function main()` or `function main { ... }` is also valid for zero-argument entry points.
- **Ambient Globals:** All scripts and functions have ambient access to `args` (a `List` of CLI strings) and `env` (a `Map` of process environment variables) without requiring imports.
- **Exit Status:** Returning an `Integer` from `main` sets the process exit code (`<- 0` for success).

```zl
function main(args) {
    writeln(`Executing: ` + args[0])
    when args.length > 1 {
        writeln(`Argument: ` + args[1])
    }
    <- 0
}
```

---

## 11. Container Types & Object Architecture

Zenlang organizes data containers into **Three Distinct Tiers**, bridging the gap between low-level systems performance, fluid dynamic scripting, and structured application OOP:

```
┌───────────────┬────────────────────────────┬───────────────────────────────────────────┐
│ Tier          │ Name                       │ Primary Purpose                           │
├───────────────┼────────────────────────────┼───────────────────────────────────────────┤
│ **Low Tier**  │ `structure` (Struct)       │ Fixed layout, value data, fast C ABI      │
│ **Middle Tier**│ `object`   (Runtime Object)│ Fluid shape, dynamic fields, bound `self` │
│ **High Tier** │ `class`    (Nominal Class) │ Formal OOP, inheritance (`extends`), init │
└───────────────┴────────────────────────────┴───────────────────────────────────────────┘
```

---

### 11.1 Low Tier: Structures (`structure`)
Structures provide fixed-layout, value-semantics records engineered for high performance, serialization, math, ECS, and direct C interop:

```zl
// 1. Untyped minimal fields:
structure Vector2 { x, y }

// 2. Untyped fields with default values:
structure Vector2 { x -> 0, y -> 0 }

// 3. Typed fields:
structure Vector3 { x: Integer, y: Integer, z: Integer }

// 4. Typed fields with default values:
structure Vector3 { x: Integer -> 0, y: Integer -> 0, z: Integer -> 0 }

// 5. Structure with member functions:
structure XYZ {
    x -> 0.0,
    y -> 0.0,
    z -> 0.0,
    sum -> function { <- x + y + z }
}

// Instantiation and field assignment:
let pt -> Vector2{ x -> 10, y -> 20 }
pt.x -> 15
```

---

### 11.2 Middle Tier: Fluid Objects (`object`)
An `object` is a heap-allocated, identity-bearing runtime entity with dynamic fields, structural shape typing, and dynamically bound methods:

```zl
// 1. Object Blueprint / Instance Declaration:
let Player -> object {
    name   : String   -> `Player`,
    health : Integer  -> 100,
    attack : Integer  -> 10,
    hit    : Function -> function (target) {
        target.health -> target.health - self.attack
    }
}

let player -> Player

// 2. Dynamic Field Addition & Modification:
player.weapon -> `Sword`
player.level  :> 5               // Inferred type lock

// 3. Dynamic Field Removal:
player.remove(`weapon`)

// 4. Attaching Methods Dynamically (Methods are just fields):
player.speak -> function : String (message: String) -> self.name + `: ` + message
io.writeln(player.speak(`Ready for battle!`))

player.take_damage -> function(amount: Integer) {
    self.health -> self.health - amount
    <- self.health
}
```

#### Objects and Zen Data (`.zd`)
In-memory `object` and `structure` entities have 1:1 declarative fidelity with **Zen Data (`.zd`)**, Zenlang's native human-readable data serialization format. Objects serialize directly to Zen Data without needing JSON or YAML:
```zl
use zen.data.zendata as zd

let zd_text -> zd.stringify(player)       // Serialize object to .zd
let loaded  -> zd.parse(zd_text)           // Deserializes back into active Object
```

---

### 11.3 High Tier: Classes & Single Inheritance (`class`, `extends`)
Classes provide formal nominal OOP with constructors (`init`), single inheritance (`extends`), `self`, and `parent`:

```zl
class Vehicle {
    let brand: String
    let speed: Decimal

    function init(brand: String, speed: Decimal) {
        self.brand -> brand
        self.speed -> speed
    }

    function describe() : String {
        <- self.brand + ` at ` + Str.to_string(self.speed) + ` km/h`
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

let car -> ElectricCar(`Model 3`, 100.0, 92)
io.writeln(car.describe())
```

---

### 11.4 Enumerators (`enumerator` / `enum`)
Enumerators define named variant states with first-class introspection properties:

```zl
enumerator Direction {
    North -> 1,
    South -> 2,
    East  -> 3,
    West  -> 4
}

// Built-in Reflection & Introspection Properties:
Direction.names        // (`North`, `South`, `East`, `West`)
Direction.values       // (1, 2, 3, 4)
Direction.South        // (`South`, 2)
Direction.South.name   // `South`
Direction.South.value  // 2

// Auto-valued variants:
enumerator Status {
    Pending,
    Active,
    Closed
}

let current -> Status.Active
when current is Status.Active {
    io.info(`Status is active`)
}
```

---

### 11.5 Reflection & Traits (`is reflectable`, `zen.reflect`)
Zenlang avoids decorator magic. Types declare reflectability using the `is reflectable` trait:

```zl
use zen.reflect as reflect

structure User is reflectable {
    let id: Integer
    let name: String
}

reflect.type_name(123)            // "Integer"
reflect.fields({ `a` -> 1 })      // ["a"]
reflect.has_field(User, `name`)   // True
```

---

## 12. Error Handling & Resilience Model

Zenlang rejects traditional `try/catch` spaghetti and invisible stack-unwinding `GOTO` jumps. Instead, errors are **first-class values** handled with left-aligned, explicit constructs: **Result Maps**, **`raise` (`^`)**, **`check` (`?`)**, and **`assert` (`!`)**.

### 12.1 The Error Handling Triad

| Operation | Keyword Form | Symbolic Form | Semantics |
|:---|:---|:---|:---|
| **Immediate Error Return** | `raise ErrorName` | `^ ErrorName` | Immediately returns an error value / variant |
| **Error with Metadata** | `raise ErrorName with val` | `^ ErrorName with val` | Returns error tagged with contextual value |
| **Unwrap / Recovery** | `check expr or fallback` | `? expr or fallback` | Evaluates `expr`; if error occurs, returns `fallback` |
| **Inline Guard & Raise** | `check cond raise error` | `? cond ^ error` | Validates condition; raises error if False |
| **Invariant Assertion** | `assert condition` | `! condition` | Halts execution or panics if condition is False |
| **Assertion with Raise** | `assert cond raise error` | `! cond ^ error` | Raises specific error if condition is False |

---

### 12.2 Explicit Multiple Return Types (`[Type, Error]`)

Functions that may fail declare their expected types or return unions without unwinding the stack:

```zl
function divide : [Decimal, Error] (a: Decimal, b: Decimal) {
    when b == 0 {
        ^ `DivisionByZeroError` // Immediate error return via symbol
    }
    <- a / b
}

// 1. Recover with default value (inline):
let result -> check divide(10, 0) or 0.0

// 2. Symbolic inline recovery:
let result -> ? divide(10, 0) or 0.0

// 3. Fallback recovery block (with ambient `error` or explicit alias):
let value -> check divide(10, 0) or (err) {
    io.warn(`Division failed: ` + Str.to_string(err))
    <- 0.0
}

// 4. Pattern matching with type and membership cases:
check divide(10, 0) {
    case is Error { io.error(`Caught error variant`) }
    case in [1.0, 2.0, 5.0] { io.info(`Expected quotient`) }
} or (err) {
    io.warn(`Unhandled result: ` + Str.to_string(err))
}
```

---

### 12.3 Guard Validation & Propagation

```zl
function process_age(age: Integer) {
    // Validate condition or raise error:
    check age >= 0 raise `InvalidAgeError`
    
    // Symbolic equivalent:
    ? age <= 150 ^ `ImpossibleAgeError`

    io.info(`Age confirmed: ` + Str.to_string(age))
}
```

---

### 12.4 Assertions (`assert` / `!`)

Assertions enforce invariants and contract preconditions:

```zl
assert buffer.length > 0
! pointer != Nothing

// Assert with custom error raising:
assert file_exists(path) raise `FileNotFound`
! token.is_valid ^ `UnauthorizedToken`
```

---

### 12.5 Result Maps (Idiomatic Zen Flow)

For domain-level operations, functions return structured success/failure maps:

```zl
function read_config(path: String) {
    when not file.exists(path) {
        <- { `ok` -> False, `value` -> Nothing, `error` -> `file_not_found` }
    }
    <- { `ok` -> True, `value` -> file.read_all(path), `error` -> ```` ```` }
}

let res -> read_config(`app.zd`)
when not res.ok {
    io.error(`Failed: ` + res.error)
} or {
    process_data(res.value)
}
```

---

## 13. Modules, Namespaces & Packaging

### 13.1 Importing Modules
```zl
// 1. Qualified import:
use zen.io
use zen.text.string as Str

// 2. Selective symbol import:
from zen.math.math import abs, min, max
```

### 13.2 Intrinsic `module` Metadata
Every file has access to an intrinsic `module` object:
- `module.name`: Stem name of current module.
- `module.path`: Full canonical filesystem path.
- `module.is_entry`: Boolean flag indicating if file was process entry point.
- `module.entry`: Entry function pointer (defaults to `main`).

---

### 13.3 Direct C Header Imports (`extern use`)

Zenlang features zero-wrapper native C interoperability. C system and external library headers can be imported directly into Zenlang source files:

```zl
// 1. Direct system header include:
extern use `<unistd.h>`
extern use `<math.h>`
extern use `<sys/sysinfo.h>`

// 2. Importing with namespace alias:
extern use unistd as u

// 3. Selective C symbol import:
extern from `<math.h>` use sqrt, pow, cos, sin
```

#### Automatic Type Boxing & Marshalling
Direct C calls seamlessly bridge the C11 and `ZenValue` runtimes:
- Primitive return values from C functions (integers, doubles, pointers, booleans) automatically box into `ZenValue` via C11 `_Generic` macros (`ZenValue_from_c(...)`).
- Zenlang arguments passed to `extern` C functions are unboxed into native scalar C types automatically based on signature inference.
- Headers are deduplicated and emitted directly during Ahead-of-Time C compilation (`zen compile` / `zen run`).

---

### 13.4 Dynamic Foreign Function Interface (FFI) & Zero-Glue System Modules

For runtime dynamic linking and operating system inspection without manual C shims, the standard library provides core modules:

| Module | Purpose | Key Functions / Capabilities |
|:---|:---|:---|
| **`zen.sys.ffi`** | Dynamic library (`.so` / `.dylib`) loader | `load(path)`, `open(path)`, `symbol(h, name, type)`, `call(fn, args, ret)`, `close(h)`, `error()`, `resolve(name)` |
| **`zen.sys.hardware`** | Host CPU & memory architecture | `cpu_count()`, `available_cpu_count()`, `page_size()`, `physical_pages()`, `available_pages()`, `clock_ticks()`, `hardware_summary()` |
| **`zen.sys.meminfo`** | System RAM statistics & consumption | `total_ram_bytes()`, `available_ram_bytes()`, `used_ram_bytes()`, `total_ram_mb()`, `available_ram_mb()`, `used_ram_mb()`, `total_ram_gb()`, `ram_usage_pct()`, `memory_summary()` |
| **`zen.sys.termposix`** | POSIX TTY & terminal stream flushing | `is_stdin_tty()`, `is_stdout_tty()`, `is_stderr_tty()`, `is_tty_fd(fd)`, `flush_input()`, `flush_output()`, `flush_both()`, `terminal_summary()` |
| **`zen.sys.readline`** | 100% Pure Zen terminal line editor | Interactive line navigation, history search, rainbow delimiter matching, tab autocompletion |

---

## 14. Scoped Resource Management & Memory Arenas (`with`)

The `with` statement provides deterministic, automatic resource cleanup and zero-fragmentation memory scoping:

### 14.1 Scoped Memory Arenas
```zl
use zen.memory as Memory

with Memory.Arena.create(1024 * 1024) as arena {
    let temp_buffer -> Memory.alloc_in(arena, 512)
    // High-throughput scratch allocations
}
// Entire arena memory is instantly reclaimed in O(1) upon block exit
```

### 14.2 Scoped I/O & File Resources
```zl
use zen.io.file as file

with file.open(`data.zd`) as f {
    let content -> file.read_all(f)
    process_content(content)
}
// File handle `f` is guaranteed to be closed upon block exit
```

---

## 15. The Unified Task Concurrency Substrate

Zenlang rejects the complexity of traditional asynchronous programming: there is no viral `async` keyword, no `await` contagion, and no fragmentation between futures, promises, fibers, and threads.

Instead, Zenlang defines a single, unified abstraction: **the `task`**.

> **"A task is a unit of execution that runs until it needs to wait. The runtime handles the rest."**

---

### 15.1 Declaring a Task (`task`)

Tasks are implicitly suspendable and managed by the runtime fiber scheduler:

```zl
// Keyword Identifier : ReturnType ( Parameters ) { Statements }
task fetch_user : User (id: Integer) {
    let data -> net.get(`/user/` + Str.to_string(id))
    <- parse_user(data)
}
```

---

### 15.2 Concurrency Intent: `.spawn` and `.wait`

Zenlang uses intent-based methods rather than low-level mechanisms:
- **`.spawn`**: Dispatches the task to run concurrently in the background.
- **`.wait`**: Suspends the current task until the result is ready (without blocking the underlying OS thread).

```zl
// 1. Concurrent Background Execution:
let handle -> fetch_user(42).spawn

// ... Do other concurrent work ...

// 2. Suspend and Retrieve Result:
let user -> handle.wait

// 3. Error Recovery on Task Waits (via check):
let user -> check fetch_user(42).wait or {
    io.warn(`Failed to fetch user; using offline guest`)
    <- GuestUser
}
```

---

### 15.3 Structured Concurrency (`with task_group`)

Zenlang prevents orphaned tasks and background memory leaks by enforcing task lifetimes through `with task_group`:

```zl
task handle_request : Response (req: Request) {
    with task_group as group {
        let profile   -> load_profile(req.user_id).spawn
        let inventory -> load_inventory(req.item_id).spawn

        <- Response{
            profile   -> profile.wait,
            inventory -> inventory.wait
        }
    } // Both spawned tasks are guaranteed to complete or cancel before exiting!
}
```

---

### 15.4 Progressive Hardware Disclosure (`task[parallel]`)

By default, tasks run on lightweight M:N runtime fibers multiplexed across an I/O event reactor. When CPU-intensive workloads require dedicated hardware OS threads, progressive disclosure enables direct hardware dispatch:

```zl
// Dispatched directly to hardware OS thread pool:
task[parallel] crunch_physics : Matrix (world: WorldState) {
    <- simulate_particles(world)
}

task[cpu] encode_video : Bytes (frames: List<Frame>) {
    <- render_h264(frames)
}
```

---

### 15.5 Channels & Message Passing (`channel`)

Tasks communicate safely without shared mutable memory using typed, non-blocking channels:

```zl
let ch -> channel(String)

task producer(ch) {
    ch.send(`Ping`)
    ch.send(`Pong`)
}

task consumer(ch) {
    let first -> ch.receive    // Suspends until message arrives
    io.info(`Received: ` + first)
}

producer(ch).spawn
consumer(ch).spawn
```

---

### 15.6 Cooperative Task Cancellation

```zl
let monitor_handle -> start_telemetry().spawn

// Cancel when no longer needed:
monitor_handle.cancel() // Cancellation propagates deterministically through task tree
```

---

### 15.7 Generators & Lazy Yielding (`yield` / `<~`)

Functions that produce streams of values lazily use `yield` (or the visual `<~` operator):

```zl
function fibonacci(limit: Integer) {
    let a -> 0
    let b -> 1
    do while a < limit {
        <~ a              // Visual yield operator (or: yield a)
        let next -> a + b
        a -> b
        b -> next
    }
}

// Consumption via loop:
do for val in fibonacci(50) {
    io.writeln(`Fib: ` + Str.to_string(val))
}
```

---

### 15.8 Native Console I/O, Ambient Streams & Structured Output
Zenlang treats standard I/O streams as first-class ambient instances and provides universal console preludes available across all scopes with **zero imports**:

#### Universal Console I/O Preludes (No Imports)
- `write(value)`: Writes string representation of value directly to standard output without a trailing newline.
- `writeln(value)`: Writes string representation of value directly to standard output followed by a newline.
- `read(prompt?)`: Reads from standard input with an optional prompt string.
- `readln(prompt?)`: Reads a line from standard input with an optional prompt string.

```zl
write(`Loading... `)
writeln(`Done!`)
let name -> readln(`Your name: `)
```

> **Design Note:** Zenlang rejects legacy `print` and `println` keywords. Use `write(...)` or `writeln(...)`.

#### Native Ambient Streams (`stdout`, `stderr`, `stdin`)
Zenlang adheres to the Unix philosophy by exposing standard streams natively as ambient stream objects with direct member methods:

| Stream | Method | Signature | Description |
|:---|:---|:---|:---|
| `stdout` | `.write(val)` | `(val: Any) -> Nothing` | Writes to stdout without newline |
| `stdout` | `.writeln(val)` | `(val: Any) -> Nothing` | Writes to stdout with newline |
| `stdout` | `.flush()` | `() -> Nothing` | Flushes stdout buffer |
| `stderr` | `.write(val)` | `(val: Any) -> Nothing` | Writes to stderr without newline |
| `stderr` | `.writeln(val)` | `(val: Any) -> Nothing` | Writes to stderr with newline |
| `stderr` | `.flush()` | `() -> Nothing` | Flushes stderr buffer |
| `stdin` | `.read(prompt?)` | `(prompt: String?) -> String` | Reads from stdin |
| `stdin` | `.readln(prompt?)` | `(prompt: String?) -> String` | Reads next line from stdin |
| `stdin` | `.lines()` | `() -> List<String>` | Reads all remaining lines as a list |

```zl
stdout.write(`status: ok `)
stdout.flush()
stderr.writeln(`error: missing configuration`)
let input -> stdin.readln(`> `)
```

#### Structured Stream Output (`zen.io`)
For tagged and ANSI-styled terminal messaging, the standard library `zen.io` package extends stream handling:
- `io.write(text)`: Raw text output
- `io.writeln(text)`: Line output with terminal newline
- `io.info(text)`: Informational output (tagged/colored)
- `io.warn(text)`: Warning output to stderr
- `io.error(text)`: Error output to stderr
- `io.debug(text)`: Debug output (suppressed in release mode)

---

## 16. Developer Toolchain & CLI Reference

```bash
# Execution & Evaluation
zen <file.zl>                   # Fast script execution via Bytecode VM
zen run <file.zl>               # Compile and execute native binary
zen repl                        # Interactive development REPL

# Build & Compilation
zen build <file.zl>             # Build standalone native executable
zen compile <file.zl> <out.c>   # Transpile into optimized C source code
zen bundle <file.zl>            # Compile into portable .zbc bytecode archive

# Testing & Verification
zen test                        # Run full test ladder (core, parity, lib, native)
zen bench                       # Run benchmark suites
zen check <file.zl>             # Run static type checker and diagnostics

# Developer Tools & Introspection
zen disasm <file.zl>            # Disassemble bytecode instructions
zen ast <file.zl>               # Print visual AST syntax tree
zen completion bash             # Generate shell autocompletion
zen doc                         # Generate HTML documentation
```
