#import "template.typ": *

= Structures, Maps & Collections

Zenlang provides lightweight composite data structures, key-value maps, and dynamic lists.

== Structures (`structure`)

Structures define typed record schemas with named fields:

#feature(
    "Structure Declaration",
    "structure Identifier {\n    field : Type\n    field : Type -> DefaultValue\n}",
    "structure Point {\n    x : Integer -> 0\n    y : Integer -> 0\n}\n\nlet origin -> Point()\nlet target -> Point(10, 25)\nlet dist_x -> target.x - origin.x"
)

=== Inline Structure Declaration

For compact records:

```zl
structure Vector2D x: Decimal, y: Decimal
let velocity -> Vector2D(1.5, -3.2)
```

== Associative Maps (`Map`)

Maps represent key-value dictionaries. Keys and values are bound using the `->` flow arrow:

#feature(
    "Map Literal Definition",
    "{ `key` -> value, `key2` -> value2 }",
    "let config -> {\n    `host` -> `127.0.0.1`,\n    `port` -> 8080,\n    `debug` -> True\n}\n\n// Key lookup\nlet current_port -> config[`port`]\n\n// Field assignment\nconfig[`timeout`] -> 30"
)

#tip[
  Map keys are canonical UTF-8 strings enclosed in backticks. Both bracket indexing (`m["key"]`) and dot-syntax (`m.key`) are supported for valid identifiers.
]

== Dynamic Lists (`List`)

Lists are ordered, growable sequences of values:

```zl
let tasks -> [`Compile`, `Link`, `Test`]

// Indexing (0-based)
let first_step -> tasks[0]

// Length
let count -> tasks.length

// Appending
tasks.append(`Package`)

// Iteration
do for task in tasks {
    io.writeln(`Executing: ` + task)
}
```