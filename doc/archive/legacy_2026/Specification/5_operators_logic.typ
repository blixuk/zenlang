#import "template.typ": *

= Operators & Logical Expressions

== Visual Data Flow Operators

Zenlang uses directional arrow operators to express data transfer explicitly:

#table(
  columns: (1fr, 1.5fr, 3fr),
  [Operator], [Name], [Description],
  [`->`], [Bind / Assign], [Moves evaluation result into target variable or map key],
  [`<-`], [Emit / Return], [Emits or returns a value outward to the caller],
  [`:>`], [Type Constrain], [Declares type constraint during binding]
)

== Comparison Operators

Comparison operators evaluate operands and return a `Boolean` (`True` or `False`).

#table(
  columns: (1fr, 2fr, 2.5fr),
  [Operator], [Meaning], [Example],
  [`==`], [Equal to], [`x == 42`, `val == Nothing`],
  [`!=`], [Not equal to], [`x != 0`, `status != Default`],
  [`<`], [Less than], [`a < 10`],
  [`<=`], [Less than or equal], [`count <= max_count`],
  [`>`], [Greater than], [`score > 100`],
  [`>=`], [Greater than or equal], [`level >= 5`]
)

#tip[
  Equality comparison in Zenlang is always `==`. Both `Nothing` and `Default` are fully comparable using `==` and `!=`.
]

== Logical Operators

Logical operations use explicit english keywords rather than punctuation:

```zl
// Logical Boolean Operations
let is_valid -> has_access and not is_expired
let should_retry -> is_timeout or connection_failed
let exclusive -> first_flag xor second_flag
```

== Range Operators

Range operators construct ordered `List` collections of integers or single-character runes:

#feature(
    "Range Operators",
    "start..end     // Half-open range [start, end)\nstart..=end    // Closed range [start, end]",
    "let r1 -> 0..5     // [0, 1, 2, 3, 4]\nlet r2 -> 0..=5    // [0, 1, 2, 3, 4, 5]\nlet letters -> `a`..=`c` // [`a`, `b`, `c`]\n\ndo for i in 1..=4 {\n    // Iterates i = 1, 2, 3, 4\n}"
)

#note[
  `...` is not a range operator in Zenlang; it is used for pattern rest/spread matching (`[head, ...tail]`).
]

== Arithmetic & Bitwise Operators

```zl
// Arithmetic
let sum -> a + b
let diff -> a - b
let product -> a * b
let quotient -> a / b
let remainder -> a % b
let power -> 2 ** 8 // 256

// Bitwise
let bit_and -> flags && 0xFF
let bit_or -> flags || 0x01
let bit_xor -> flags ^^ 0xAA
let bit_shift -> 1 << 4
```
