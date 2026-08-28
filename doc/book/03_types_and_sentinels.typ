= Types, Collections & Sentinels

Zenlang features a flexible, expressive type system designed for reliability and ease of use.

== Primitive Types

#table(
  columns: (1fr, 1.5fr, 3fr),
  [Type], [Examples], [Description],
  [*Integer*], [`42`, `-10`, `0`], [64-bit signed integers],
  [*Decimal*], [`3.14159`, `0.0`, `-0.5`], [64-bit IEEE floating-point numbers],
  [*Boolean*], [`True`, `False`], [Truth values (also lowercase `true`, `false`)],
  [*String*], [``` `hello` ```, ``` `multiline\nstring` ```], [UTF-8 text strings]
)

=== String Literals
Strings in Zenlang are enclosed in backticks (``` `...` ```):

```zl
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

== Sentinels: `Nothing` and `Default`

Zenlang has two explicit sentinel values:

=== `Nothing` (Absence of a Value)
`Nothing` represents the absence of any value:

```zl
let user -> Nothing
when user == Nothing {
    io.writeln(`No user logged in.`)
}
```

=== `Default` (The Type Zero-State)
`Default` represents the canonical zero-state of a type:
- `0` for numbers
- `""` for strings
- `[]` for lists
- `{}` for maps
- `False` for booleans

```zl
let count -> Default // Initializes to 0
let items -> Default // Initializes to []
```

Both `Nothing` and `Default` are assignable and comparable with `==` and `!=`.

== Lists

Lists are dynamic, ordered collections:

```zl
let fruits -> [`Apple`, `Banana`, `Cherry`]

// Accessing items (0-based)
let first -> fruits[0] // `Apple`

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

== Maps

Maps are key-value associative dictionaries. Pairs are assigned with the `->` flow arrow:

```zl
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
