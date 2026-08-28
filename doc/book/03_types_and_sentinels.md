# Chapter 3: Types, Collections & Sentinels

Zenlang features a flexible, expressive type system designed for reliability and ease of use.

---

## 1. Primitive Types

| Type | Examples | Description |
|------|----------|-------------|
| **Integer** | `42`, `-10`, `0` | 64-bit signed integers |
| **Decimal** | `3.14159`, `0.0`, `-0.5` | 64-bit IEEE floating-point numbers |
| **Boolean** | `True`, `False` | Truth values (also `true`, `false`) |
| **String** | `` `hello` ``, `` `multiline \n string` `` | UTF-8 text strings |

### String Literals
Strings in Zenlang are enclosed in backticks (`` `...` ``):

```zenlang
use zen.io
use zen.text.string as Str

function main() {
    let msg -> `Hello\nWorld!`
    let len -> Str.length(msg)
    let upper -> Str.to_uppercase(msg)
    
    io.writeln(upper)
    <- 0
}
```

---

## 2. Sentinels: `Nothing` and `Default`

Zenlang has two explicit sentinel values:

### `Nothing` (Absence of a Value)
`Nothing` represents the absence of any value (analogous to `None`, `null`, or `nil` in other languages):

```zenlang
let user -> Nothing
when user == Nothing {
    io.writeln(`No user logged in.`)
}
```

### `Default` (The Type Zero-State)
`Default` represents the canonical zero-state of a type:
- `0` for numbers
- `""` for strings
- `[]` for lists
- `{}` for maps
- `False` for booleans

```zenlang
let count -> Default // Initializes to 0
let items -> Default // Initializes to []
```

Both `Nothing` and `Default` are assignable and comparable with `==` and `!=`.

---

## 3. Lists

Lists are dynamic, ordered collections:

```zenlang
let fruits -> [`Apple`, `Banana`, `Cherry`]

// Accessing items (0-based)
let first -> fruits[0] // "Apple"

// Adding items
fruits.append(`Date`)

// Length
let total -> fruits.length // 4

// Iteration
let i -> 0
do while i < fruits.length {
    io.writeln(fruits[i])
    i -> 0 + i + 1
}
```

---

## 4. Maps

Maps are key-value associative dictionaries. Pairs are assigned with the `->` flow arrow:

```zenlang
let user -> {
    `name` -> `Alice`,
    `role` -> `Admin`,
    `active` -> True
}

// Accessing fields
let username -> user[`name`]
let user_role -> user.role // Dot notation supported

// Setting fields
user[`last_login`] -> `2026-08-23`

// Checking existence safely
when user.keys().contains(`role`) {
    io.writeln(`User role is: ` + user.role)
}
```

---

## 💡 Chapter Exercises

1. Create a list of 5 test scores. Write a loop to compute and print the average score.
2. Create a map representing a book (`title`, `author`, `year`, `pages`). Print a formatted summary string.
