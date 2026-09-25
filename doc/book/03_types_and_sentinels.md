# Chapter 3: Types, The 5 Collections & Sentinels

Zenlang features an expressive, optionally typed type system designed for reliability, high performance, and visual clarity.

---

## 1. Scalar Primitives & Numeric Literals

Zenlang provides fine-grained numeric and text representations:

| Type Name | Sized Forms | Description | Default Zero-State (`Default`) | Example Literal |
|:---|:---|:---|:---|:---|
| **`Integer`** | `Integer[8]`, `Integer[16]`, `Integer[32]`, `Integer[64]` | Signed integer (default 64-bit) | `0` | `42`, `-10`, `0x7B`, `0b1010` |
| **`Decimal`** | `Decimal[32]`, `Decimal[64]` | IEEE 754 floating point (default 64-bit) | `0.0` | `3.14159`, `-0.5`, `1e-5` |
| **`Byte`** | — | 8-bit unsigned raw byte (`0x00..0xFF`) | `0x00` | `0x41`, `65 <: Byte`, `Byte(0x7B)` |
| **`Bytes`** | — | Sequence / buffer of `Byte` values | `Bytes{}` | `Bytes{ 0xDE, 0xAD }` |
| **`String`** | `String[8]`, `String[16]`, `String[32]`, `String[64]` | UTF-8 encoded text buffer | ```` ```` | ```` `Hello, Zen!` ```` |
| **`Boolean`** | — | Boolean truth values | `False` | `True`, `False` |
| **`Rune`** | — | 32-bit Unicode code point scalar | `'\0'` | `'A'`, `'\n'` |
| **`Void`** | — | Unit type representing absence of return | `Void` | `Void` |
| **`Variant`** | — | Dynamic tagged-union container | `Nothing` | (any value) |

### 1.1 Numeric Prefixes & Separators
Zenlang supports hex, octal, binary prefixes, and underscores for readability:

```zl
let hex_val  -> 0x7B             // Hexadecimal (prefix 0x)
let oct_val  -> 0o173            // Octal (prefix 0o)
let bin_val  -> 0b0111_1011      // Binary (prefix 0b)
let big_num  -> 1_000_000        // Underscore separator
let hex_blob -> 0xDE_AD_BE_EF    // Formatted hex
```

### 1.2 Strings & Multi-Line Literals
Strings in Zenlang are strictly enclosed in backticks (`` `...` ``):
- **Single-Line:** `` `Hello, World!` ``
- **Formatted (Interpolated):** `` f`Count is {count}` ``
- **Multi-Line:** Triple backticks preserve formatting and line breaks:
  ````zl
  let banner -> ```
  ==============================
     ZENLANG SYSTEM UTILITY
  ==============================
  ```
  ````

---

## 2. Sentinels: `Nothing` vs `Default`

Zenlang eliminates null-pointer confusion using two capitalized sentinels:

### `Nothing` (Absence of a Value)
Represents explicit absence (unassigned or missing state):

```zl
let user_token : String -> Nothing

when user_token == Nothing {
    io.writeln(`No active session found.`)
}
```

### `Default` (Type Zero-State)
Represents the natural zero-state of a type (`0`, `0.0`, ```` ````, `False`, `[]`, `{}`):

```zl
let count : Integer -> Default // Evaluates to 0
let flags : List    -> Default // Evaluates to []
let conf  : Map     -> Default // Evaluates to {}

when count == Default {
    io.writeln(`Counter is at zero state.`)
}
```

---

## 3. The 5 Core Collection Types

Zenlang provides 5 distinct first-class collection types covering all combinations of ordering, mutability, and sizing:

| Collection | Ordering | Size | Mutability | Elements |
|:---|:---|:---|:---|:---|
| **`List`** | Ordered | Dynamic | Mutable | Homogeneous / Heterogeneous values |
| **`Set`** | Unordered | Dynamic | Mutable | Unique values |
| **`Vector`** | Ordered | Fixed-size | Immutable | Fixed numeric or coordinate data |
| **`Tuple`** | Ordered | Fixed-size | Immutable | Heterogeneous values (optional named fields) |
| **`Map`** | Unordered | Dynamic | Mutable | Key-Value pairs (`key -> value`) |

### 3.1 Collection Literals & Syntax Modes

#### Mode 1: Explicit Type Tags (`Type{ ... }`)
```zl
// 1. Vector (Fixed, Immutable)
let v1 -> Vector{ 10, 20, 30 }

// 2. Set (Dynamic, Unique)
let s1 -> Set{ `apple`, `banana`, `apple` } // Stores { 'apple', 'banana' }

// 3. Tuple (Fixed, Heterogeneous / Named)
let t1 -> Tuple{ `Attack`, 100, True }
let named_t -> Tuple{ name -> `Alice`, score -> 95 }

// 4. List (Dynamic, Ordered)
let l1 -> List{ 1, 2, 3 }

// 5. Map (Key-Value)
let m1 -> Map{ `host` -> `127.0.0.1`, `port` -> 8080 }
```

#### Mode 2: Contextual Type Inference (`let x : Type -> { ... }`)
```zl
let coords : Vector -> { 1.5, 2.5, 3.5 }  // Materializes as Vector
let unique : Set    -> { 10, 20, 30 }      // Materializes as Set
let record : Tuple  -> { `Bob`, 42 }       // Materializes as Tuple
```

#### Mode 3: Daily Scripting Shorthands
- **`[1, 2, 3]`** $\rightarrow$ Defaults to **`List`**
- **`{ key -> value }`** $\rightarrow$ Defaults to **`Map`**
- **`(1, 2, 3)`** $\rightarrow$ Defaults to **`Tuple`**

### 3.2 Stepped `++` and `--` Operators
Lists and strings support visual mutations:

```zl
let items -> [1, 2]
items++ 3       // Appends 3 -> [1, 2, 3]
++items 0       // Prepends 0 -> [0, 1, 2, 3]
items--         // Drops last element -> [0, 1, 2]
--items         // Drops first element -> [1, 2]
```

---

## 4. First-Class Type Casting (`<:` and `Type(val)`)

Zenlang supports explicit, safe type conversions through dual syntax:

```zl
let raw_byte : Byte -> 0x41

// Operator syntax (<:):
let int_val -> raw_byte <: Integer   // 65
let str_val -> raw_byte <: String    // `0x41`
let rune_val -> raw_byte <: Rune     // `A`

// Constructor syntax:
let num -> Integer(`500`)            // 500
let txt -> String(2026)              // `2026`
let b   -> Byte(65)                  // 0x41
```

---

## 5. Abstract & Union Types

Zenlang provides four first-class abstract union types for high-level type testing, pattern matching, casting, and polymorphic contracts:

| Abstract Type | Encompassed Concrete Types | Description |
|:---|:---|:---|
| **`Number`** | `Integer` (including `Integer[SIZE]`, `Byte`), `Decimal` (including `Decimal[SIZE]`) | Any numeric value |
| **`Text`** | `String` (including `String[SIZE]`), `Rune` | Textual string and character representations |
| **`Collection`** | `List`, `Vector`, `Vector[N]`, `Set`, `Tuple`, `Map` | Sequential, associative, and aggregate collections |
| **`Container`** | `Structure`, `Object`, `Class`, `Enumerator` | Structured types, records, and OOP instances |

### 5.1 Type Testing & Pattern Matching
Abstract types work seamlessly with `is` checks and `when` pattern branches:

```zl
function inspect_value(val) {
    when val is Number {
        io.writeln(`Received a number: `, val)
    }
    when val is Text {
        io.writeln(`Received text: `, val)
    }
    when val is Collection {
        io.writeln(`Received collection of size: `, val.length)
    }
    when val is Container {
        io.writeln(`Received structured container`)
    }
}
```

### 5.2 Abstract Casting & Annotations
Values can be cast to abstract targets or annotated directly:

```zl
let n1 : Number -> 42
let n2 : Number -> 3.14
let num_val -> `99.5` <: Number    // 99.5

let t : Text -> `zen`
let str_val -> 123 <: Text         // `123`

let c : Collection -> [1, 2, 3]
let list_val -> `abc` <: Collection // [`a`, `b`, `c`]
```

---

## 6. Parameterized Generic Types

Zenlang supports parameterized generic type annotations and casting across collections using canonical angle brackets `<...>`:

| Generic Annotation | Description | Example |
| :--- | :--- | :--- |
| `List<T>` | Homogeneous element list | `let nums : List<Integer> -> [1, 2, 3]` |
| `Map<K, V>` | Key-value mapping | `let scores : Map<String, Integer> -> {`alice` -> 95}` |
| `Set<T>` | Unique element set | `let tags : Set<String> -> Set{`zen`, `code`}` |
| `Vector[N]<T>` | Fixed-capacity sized vector | `let pt : Vector[3]<Decimal> -> Vector{1.0, 2.0, 3.0}` |
| `Tuple<T1, T2, ...>` | Heterogeneous tuple | `let pair : Tuple<Integer, String> -> Tuple{1, `zen`}` |

### 6.1 Generic Type Checking & Unification
The compiler performs compile-time validation, verifying structural compatibility and rejecting mismatched element assignments:

```zl
// Compile error: expected List<Integer>, got List<String>
let bad : List<Integer> -> [`zen`, `lang`]
```

### 6.2 Generic Pattern Matching & Casting
Generic types integrate seamlessly with `is`, `when is`, and `<:` / `Type(val)`:

```zl
function process(c: Collection) {
    when c is List<Integer> {
        // Handle list of integers
    }
    when c is Map<String, Integer> {
        // Handle string-to-integer map
    }
}

let chars -> `hello` <: List<String> // [`h`, `e`, `l`, `l`, `o`]
let unique_ints -> [1, 2, 2, 3] <: Set<Integer>
```

---

## 💡 Chapter Exercises

1. Define a `Byte` holding `0x7F`. Cast it into an `Integer` and a `String`, and print both results.
2. Create a `Set<String>` containing five items with duplicate values. Verify that duplicates are automatically removed.
3. Create a `Tuple<String, Decimal, Boolean>` holding a student's name, grade average, and enrolled status. Access and print each field.
4. Write a function `sum_list(items: List<Integer>) : Integer` that computes the total and demonstrates parameterized return and argument annotations.


