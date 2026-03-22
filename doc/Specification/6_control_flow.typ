#import "template.typ": *

= Control Flow

Zenlang features several flexible control flow constructs.

== Conditionals

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === When
        #v(0.5em)

        Syntax:
        ```zl
        when condition { .... }

        when condition { .... } or { .... }

        when condition { .... } or condition { .... } or { .... }
        ```
        #v(0.5em)

        Example:
        ```zl
        when x > 0 {
          write(`positive`)
        } or {
          write(`negative`)
        }
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === When Inline
        #v(0.5em)

        Syntax:
        ```zl
        value when condition or value
        ```
        #v(0.5em)

        Example:
        ```zl
        let messsage -> `positive` when x > 0 or `negative`
        ```
    ]
)

== Defer

Defer runs when the enclosing function returns, even if it panics or returns early.

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Defer
        #v(0.5em)

        Syntax:
        ```zl
        defer expression

        defer { .... }
        ```
        #v(0.5em)

        Example:
        ```zl
        function test {
            defer write(`Defer`)
            write(`Hello`)
        }

        function test {
            let a -> 1
            defer {
                write(`Defer`)
                a -> 100
                write(a) // 100
            }
            write(a) // 1
        }
        ```
    ]
)

== Loops

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Do
        #v(0.5em)

        Syntax:
        ```zl
        do { .... }
        ```
        #v(0.5em)

        Example:
        ```zl
        do {
            write(`Hello`)
        }
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Do When
        #v(0.5em)

        Syntax:
        ```zl
        do when condition { .... }

        do when condition { .... } or { .... }
        ```
        #v(0.5em)

        Example:
        ```zl
        do when x > 0 {
            write(`Hello`)
        }

        do when x > 0 {
            write(`Hello`)
        } or {
            write(`World`)
        }
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Do While
        #v(0.5em)

        Syntax:
        ```zl
        do while condition { .... }

        do while condition { .... } or { .... }

        do { ... } while condition
        ```
        #v(0.5em)

        Example:
        ```zl
        // pre check
        do while condition {
          ....
        }

        // or only with pre check
        do while condition {
          ....
        } or {
          ....
        }

        // post check
        do {
          ....
        } while condition
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Do Until
        #v(0.5em)

        Syntax:
        ```zl
        do until condition { .... }

        do { ... } until condition
        ```
        #v(0.5em)

        Example:
        ```zl
        // pre check
        do until condition {
          ....
        }

        // post check
        do {
          ....
        } until condition
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Do For
        #v(0.5em)

        Syntax:
        ```zl
        do for value in container { .... }

        do for value in container { .... } or { .... }
        ```
        #v(0.5em)

        Example:
        ```zl
        // pre check
        do for value in container {
          ....
        }

        // post check
        do for value in container {
          ....
        } or {
          ....
        }
        ```
    ]
)

=== Break / Continue

As expected in loops.

```zl
break
continue
```
