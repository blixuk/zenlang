#import "template.typ": *

== Structrues

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Structure
        #v(0.5em)

        Syntax:
        ```zl
        structure Identifier { Identifier ... }

        structure Identifier { Identifier -> Value ... }

        structure Identifier { Identifier : Type ... }

        structure Identifier { Identifier : Type -> Value ... }
        ```
        #v(0.5em)

        Example:
        ```zl
        structure Point { 
          x
          y

          sum -> function <- x + y
        }

        structure Point { 
          x -> 0
          y -> 0 

          sum : Function -> function <- x + y
        }

        structure Point { 
          x : Integer
          y : Integer

          sum : Function<Integer> -> function <- x + y
        }

        structure Point { 
          x : Integer -> 0
          y : Integer -> 0

          sum : Function<Integer> -> function {
            <- x + y
          }
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
        === Structure Inline
        #v(0.5em)

        Syntax:
        ```zl
        structure Identifier Identifier, ... 

        structure Identifier Identifier -> Value, ... 

        structure Identifier Identifier : Type, ... 

        structure Identifier Identifier : Type -> Value, ...
        ```
        #v(0.5em)

        Example:
        ```zl
        structure Point x, y

        structure Point x -> 0, y -> 0

        structure Point x : Integer, y : Integer

        structure Point x : Integer -> 0, y : Integer -> 0
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Structure Instantiation & Unpacking
        #v(0.5em)

        Syntax:
        ```zl
        let Identifier -> Identifier()
        
        let Identifier : Structure -> Identifier ( parameters )

        Identifier.Member
        ```
        #v(0.5em)

        Example:
        ```zl
        let point -> Point()

        let point : Point -> Point ( 0, 0 )

        let point : Point -> Point ( x -> 0, y -> 0 )

        point.x -> 10
        point.y -> 100

        write( point.x )
        write( point.sum() )

        let x, y -> point

        write(x)
        write(y)
        ```
    ]
)

== Objects

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Object
        #v(0.5em)

        Syntax:
        ```zl
        object Identifier { ... }

        object Identifier { Identifier -> Value, ... }

        object Identifier { Identifier : Type -> Value, ... }
        ```
        #v(0.5em)

        Example:
        ```zl
        object test {
          attack -> 100,
          defence -> 50
        }

        object test {
          attack : Integer -> 100,
          defence : Integer -> 50
        }
        ```
    ]
)