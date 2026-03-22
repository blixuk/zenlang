#import "template.typ": *

== Variables & Assignment

=== Variable (mutable)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Let Assignment Expression
        #v(0.5em)

        Syntax:
        ```zl
        let Identifier -> Expression
        let Identifier : Type -> Expression
        let Identifier :> Expression
        ```
        #v(0.5em)

        Example:
        ```zl
        let a -> 10
        let b : Integer -> 100
        let c :> `Hello World`
        ```
    ]
)

=== Constant (immutable)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Set Assignment Expression
        #v(0.5em)

        Trying to reassign a constant raises an error.
        #v(0.5em)

        Syntax:
        ```zl
        set Identifier : Type -> Expression
        set Identifier :> Expression
        ```
        #v(0.5em)

        Example:
        ```zl
        set PI : Decimal -> 3.14159
        set FPS :> 60
        ```
    ]
)

=== Assignment typing

```zl
let x -> 1            // Type will be resolved to Variant and inferred as Integer
let y : Integer -> 2  // Type will be resolved as Integer
let z :> 3            // Type will be resolved to Integer and inferred as Integer
```
