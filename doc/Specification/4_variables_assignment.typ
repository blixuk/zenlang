#import "template.typ": *

= Variables, Constants & Assignment

In Zenlang, data movement is visually explicit. Variables and constants are initialized and updated using the left-to-right flow arrow `->`.

== Mutable Variables (`let`)

Variables are declared with `let`. They can be freely reassigned or mutated throughout their scope.

#feature(
    "Variable Declaration & Binding",
    "let Identifier -> Expression\nlet Identifier : Type -> Expression\nlet Identifier : Type -> Default",
    "let count -> 0\nlet name : String -> `Zen`\nlet buffer : List -> Default"
)

=== Variable Reassignment

Once declared, a variable is reassigned by binding a new value using the arrow `->`:

```zl
let x -> 10
x -> x + 5 // x is now 15
```

== Immutable Constants (`set`)

Constants are declared with `set`. Once bound, attempting to reassign or mutate a constant raises a compile-time or runtime error.

#feature(
    "Constant Declaration",
    "set Identifier -> Expression\nset Identifier : Type -> Expression",
    "set MAX_CONNECTIONS -> 1024\nset PI : Decimal -> 3.1415926535"
)

#warning[
  Constants cannot be rebound. The statement `set PI -> 3.14` followed by `PI -> 3.0` will halt execution with an error.
]

== Sentinel Zero-State Initialization (`Default`)

Variables can be explicitly initialized to their type's natural zero-state using `Default`:

```zl
let counter : Integer -> Default  // Materializes as 0
let flags : Boolean -> Default    // Materializes as False
let items : List -> Default       // Materializes as []
let metadata : Map -> Default     // Materializes as {}
```

== Unassigned Sentinels (`Nothing`)

When a variable represents the absence of a value, it is bound to `Nothing`:

```zl
let active_session -> Nothing
when active_session == Nothing {
    // Session is not established
}
```
