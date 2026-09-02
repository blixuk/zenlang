# Chapter 3: Types, The 5 Collections & Sentinels

Zenlang features an expressive, optionally typed type system designed for reliability, high performance, and visual clarity.

---

## 1. Scalar Primitives & Numeric Literals

Zenlang provides fine-grained numeric and text representations:

| Type Name | Aliases | Description | Default Zero-State (`Default`) | Example Literal |
|:---|:---|:---|:---|:---|
| **`Integer`** | `Int`, `Int64`, `Int32` | 64-bit signed integer | `0` | `42`, `-10`, `0x7B`, `0b1010` |
| **`Decimal`** | `Float`, `Float64` | 64-bit IEEE 754 float | `0.0` | `3.14159`, `-0.5`, `1e-5` |
| **`Byte`** | — | 8-bit unsigned raw byte (`0x00..0xFF`) | `0x00` | `0x41`, `65 <: Byte`, `Byte(0x7B)` |
| **`Bytes`** | `Buffer` | Sequence / buffer of `Byte` values | `Bytes{}` | `Bytes{ 0xDE, 0xAD }`, `B{ 0x01 }` |
| **`String`** | `Str` | UTF-8 encoded text buffer | ```` ```` | ```` `Hello, Zen!` ```` |
| **`Boolean`** | `Bool` | Boolean truth values | `False` | `True`, `False` |
| **`Rune`** | `Char` | 32-bit Unicode code point scalar | `'\0'` | `'A'`, `'\n'` |
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

#### Mode 1: Explicit Type Tags (`Type{ ... }` or 1-Letter Aliases)
```zl
// 1. Vector (Fixed, Immutable)
let v1 -> Vector{ 10, 20, 30 }
let v2 -> V{ 10, 20, 30 }

// 2. Set (Dynamic, Unique)
let s1 -> Set{ `apple`, `banana`, `apple` } // Stores { 'apple', 'banana' }
let s2 -> S{ 1, 2, 3 }

// 3. Tuple (Fixed, Heterogeneous / Named)
let t1 -> Tuple{ `Attack`, 100, True }
let t2 -> T{ `Attack`, 100, True }
let named_t -> Tuple{ name -> `Alice`, score -> 95 }

// 4. List (Dynamic, Ordered)
let l1 -> List{ 1, 2, 3 }
let l2 -> L{ 1, 2, 3 }

// 5. Map (Key-Value)
let m1 -> Map{ `host` -> `127.0.0.1`, `port` -> 8080 }
let m2 -> M{ `a` -> 1, `b` -> 2 }
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

## 💡 Chapter Exercises

1. Define a `Byte` holding `0x7F`. Cast it into an `Integer` and a `String`, and print both results.
2. Create a `Set` containing five items with duplicate values. Verify that duplicates are automatically removed.
3. Create a `Tuple` holding a student's name, grade average (Decimal), and enrolled status (Boolean). Access and print each field.

