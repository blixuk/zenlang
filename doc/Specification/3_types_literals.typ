#import "template.typ": *

= Types

Zenlang is optionally typed:
You may declare types, or let them be inferred.

Zenlang defines several Types:

== Primitive Types

#block( // Void
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Void
        #v(0.5em)

        No returned value.
        #v(0.5em)

        Syntax:
        #raw("Void", lang: "zl")

        Example:
        #raw("function test : Void { write(`Hello, World!`) }", lang: "zl")
    ]
)

#block( // Variant
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Variant
        #v(0.5em)

        Stores any Zen Type and able to change value types freely.
        #v(0.5em)

        Syntax:
        #raw("Variant", lang: "zl")

        Example:
        #raw("function test : Variant { <- `Hello, World!` }", lang: "zl")
    ]
)

#block( // Integer
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Integer
        #v(0.5em)

        Defaults to a 32-bit signed integer.
        #v(0.5em)

        Syntax:
        ```zl
        Integer         // 32-bit signed integer defualt
        Integer[Size]   // Size in bits

        Integer[8]      // 8-bit signed integer
        Integer[16]     // 16-bit signed integer
        Integer[32]     // 32-bit signed integer
        Integer[64]     // 64-bit signed integer
        ```

        Example:
        ```zl
        let a : Integer -> 10
        function test : Integer { <- 10 }
        ```
    ]
)

#block( // Decimal
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Decimal
        #v(0.5em)

        Defaults to a 32-bit floating point.
        #v(0.5em)

        Syntax:
        ```zl
        Decimal         // 32-bit floating point defualt
        Decimal[Size]   // Size in bits

        Decimal[32]     // 32-bit floating point
        Decimal[64]     // 64-bit floating point
        ```

        Example:
        ```zl
        let a : Decimal -> 10.0
        function test : Decimal { <- 10.0 }
        ```
    ]
)

#block( // Boolean
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Boolean
        #v(0.5em)

        True or False.
        #v(0.5em)

        Syntax:
        ```zl
        Boolean
        ```

        Example:
        ```zl
        let a : Boolean -> True
        function test : Boolean { <- True }
        ```
    ]
)

#block( // Rune
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Rune
        #v(0.5em)

        UTF-32 defaut
        #v(0.5em)

        Syntax:
        ```zl
        Rune        // UTF-32 defaut
        Rune[Size]  // Encoding Size in bits
        
        Rune[8]     // UTF-8  (8bits  - 1 byte)
        Rune[16]    // UTF-16 (16bits - 2 bytes)
        Rune[32]    // UTF-32 (32bits - 4 bytes)
        ```

        Example:
        ```zl
        let a : Rune -> `A`
        function test : Rune { <- `A` }
        ```
    ]
)

#block( // String
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === String
        #v(0.5em)

        UTF-32 defaut
        #v(0.5em)

        Syntax:
        ```zl
        String       // UTF-32 defaut
        String[Size] // Encoding Size in bits

        String[8]    // UTF-8  (8bits - 1 byte)
        String[16]   // UTF-16 (16bits - 2 bytes)
        String[32]   // UTF-32 (32bits - 4 bytes)
        ```

        Example:
        ```zl
        let a : String -> `Hello, World!`
        function test : String { <- `Hello, World!` }
        ```

        Example:
        ```zl
        x``    // Hex encoded string

        b16``  // Base16 encoded string
        b32``  // Base32 encoded string
        b64``  // Base64 encoded string

        u``    // Unicode encoded string
        u8``   // UTF-8 encoded string
        u16``  // UTF-16 encoded string
        u32``  // UTF-32 encoded string
        ```

        Example:
        ```zl
        f``          // Format string
        f`{a} : {b}` // Format string with arguments

        t``          // Template string
        t`{a} : {b}` // Template string with arguments
        ```
    ]
)

=== Collection Types

#block( // Map
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Map
        #v(0.5em)

        Stores Key Value pairs.
        #v(0.5em)

        Syntax:
        ```zl
        Map
        Map<Type, Type>
        ```

        Example:
        ```zl
        let a : Map<String, Integer> -> { `a` -> 1, `b` -> 2 }
        function test : Map { <- { `a` -> 1, `b` -> 2 } }
        ```
    ]
)

#block( // List
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === List
        #v(0.5em)

        Stores a list of values in a fixed order.
        #v(0.5em)

        Syntax:
        ```zl
        List
        List<Type>
        ```

        Example:
        ```zl
        let a : List -> { 1, 2 }

        let a : List<Integer> -> { 1, 2, 3, 4, 5 }
        let a : List<String> -> { `a`, `b`, `c`, `d`, `e` }
        let a : List<Variant> -> { `a`, 1, True }

        function test : List<Integer> { <- { 1, 2, 3, 4, 5 } }
        ```
    ]
)

#block( // Set
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Set
        #v(0.5em)

        Stores a list of unique values.
        #v(0.5em)

        Syntax:
        ```zl
        Set
        Set<Type>
        ```

        Example:
        ```zl
        let a : Set -> { 1, 2 }

        let a : Set<Integer> -> { 1, 2, 3, 4, 5 }
        let a : Set<String> -> { `a`, `b`, `c`, `d`, `e` }
        let a : Set<Variant> -> { `a`, 1, True }

        function test : Set<Integer> { <- { 1, 2, 3, 4, 5 } }
        ```
    ]
)

#block( // Tuple
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Tuple
        #v(0.5em)

        Stores a list of Types in a fixed order. Tuple can be named.
        #v(0.5em)

        Syntax:
        ```zl
        Tuple
        Tuple<Type, ... >
        ```

        Example:
        ```zl
        let a : Tuple -> { 1, 2 }

        // Tuple with 2 elements of different types
        let a : Tuple<String, Integer> -> { `Attack`, 100 }

        // Tuple with 2 elements of the same type, but named
        function test : Tuple<Integer> { <- { `Attack` -> 100, `Defense` -> 100 } }
        ```
    ]
)

#block( // Vector
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Vector
        #v(0.5em)

        Stores a fixed length list of values in a fixed order
        #v(0.5em)

        Syntax:
        ```zl
        Vector
        Vector[Size]        // Size in elements
        Vector[Size]<Type>
        ```

        Example:
        ```zl
        let a : Vector[4] -> { 1, 2, 3, 4 }
        let a : Vector[4]<Integer> -> { 1, 2, 3, 4 }
        let a : Vector[4]<String> -> { `a`, `b`, `c`, `d` }
        let a : Vector[4]<Variant> -> { `a`, 1, True }

        function test : Vector[4]<Integer> { <- { 1, 2, 3, 4 } }
        ```
    ]
)

== Container Types

```zl
Class       // Stores a list of [Function, Assignment] Types
Object      // Stores a list of [Function, Assignment] Types
Structure   // Stores a list of Structure Member Types
Enumerator  // Stores a list of Enumerator Member Types
```

== Action Types

```zl
Function    // Stores a list of Function Parameter Types
Task        // Stores a list of [Function, Assignment] Types
```

== Abstract Types

#block( // Number
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Number
        #v(0.5em)

        Accepts Integer and Decimal values
        #v(0.5em)

        Syntax:
        ```zl
        Number
        ```

        Example:
        ```zl
        let a : Number -> 1
        let a : Number -> 1.0

        function add(a : Number, b : Number) : Number { <- a + b }
        ```
    ]
)

#block( // Text
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Text
        #v(0.5em)

        Accepts String and Rune values
        #v(0.5em)

        Syntax:
        ```zl
        Text
        ```

        Example:
        ```zl
        let a : Text -> `Hello, World!`

        function print(input : Text) : Void { write(input) }
        ```
    ]
)

```zl
Number      // Number Type (Integer, Decimal)
Text        // Text Type (String, Rune)
Container   // Container Type (Class, Object, Structure, Enumerator)
Collection  // Collection Type (Map, List, Set, Tuple, Vector)
```

=== User-Defined Types

Zenlang supports custom types via:
- classes
- structures
- enumerators

Classes support inheritance. Structures are simple value types. Enumerators define closed sets of named variants.

==== Structures

```zl
from zen.io import write

structure a1 { x, y }
structure a2 { x -> 1, y -> 10 }
structure a3 { x :> 0, y :> 0 }
structure a4 { x : Integer, y : Integer }
structure a5 { x : Integer -> 0, y : Integer -> 0 }

structure Vector2 { x, y }

structure XYZ {
	x -> 0.0
	y -> 0.0
	z -> 0.0
	sum -> function <- x + y + z
}

write(XYZ.x) // 0.0
write(XYZ.sum()) // 0.0

XYZ.x -> 1.0
XYZ.z -> 1.0
XYZ.z -> 1.0

write(XYZ.sum()) // 3.0

structure Vector3 {
    x : Integer -> 0
    y : Integer -> 0
    z : Integer -> 0

    sum : Integer -> function <- x + y + z

    add : Integer -> function ( a ) <- x + a

    zero : Integer -> function {
        x -> 0
        y -> 0
        z -> 0
    }
}

```

==== Enumerators

```zl
from zen.io import write

enumerator name { .... }

enumerator Direction { North, South, East, West }

write(Direction) // ( (`North`, 0), (`South`, 1), (`East`, 2), (`West`, 3) )

enumerator Direction {
    North -> 1,
    South -> 2,
    East -> 3,
    West -> 4
}

write(Direction) // ( (`North`, 1), (`South`, 2), (`East`, 3), (`West`, 4) )
write(Direction.names) // ( `North`, `South`, `East`, `West` )
write(Direction.values) // ( 1, 2, 3, 4 )
write(Direction.South) // (`South`, 2)
write(Direction.South.name) // `South`
write(Direction.South.value) // 2

enumerator Week {
    SUNDAY -> -1,
    MONDAY -> 1,
    TUESDAY -> 10,
    WEDNESDAY -> 100
}
write(Week) // ( (`SUNDAY`, -1), (`MONDAY`, 1), (`TUESDAY`, 10), (`WEDNESDAY`, 100) )

enumerator Week {
    SUNDAY -> 10,
    MONDAY -> auto,
    TUESDAY -> auto,
    WEDNESDAY -> auto
}

write(Week) // ( (`SUNDAY`, 10), (`MONDAY`, 11), (`TUESDAY`, 12), (`WEDNESDAY`, 13) )
```

==== Classes

```zl
from zen.io import write

class Person {
    let name : String -> `Unknown`
    let age : Integer -> 0

    function init(name : String, age : Integer) : Void {
        self.name -> name
        self.age -> age
        write(`Initialized ` + self.name)
    }

    function greet() : Void {
        write(`Hello, my name is ` + self.name + ` and I am ` + self.age + ` years old.`)
    }
}

let person : Person -> Person(`Alice`, 30)
write(person.greet())
```

```zl
from zen.io import write

class Animal {
    let name -> `Animal`

    function sound() {
        write(`Generic sound`)
    }
}

class Dog extends Animal {
    function sound() {
        write(`Woof!`)
    }
}

write(`-- Animal --`)
let animal -> Animal()
write(animal.name)
animal.sound()

write(`-- Dog --`)
let dog -> Dog()
write(dog.name)
dog.sound()
```

```zl
from zen.io import write

class Animal {
    function sound() {
        write(`Generic Animal Sound`)
    }
}

class Dog extends Animal {
    function sound() {
        write(`Dog says:`)
        parent.sound()
    }
}

let dog -> Dog()
dog.sound()
```

=== Abstract Types

==== Number
```zl
let x : Number -> 10
let y : Number -> 1.0
let z : Number -> 0x7B
```

==== Text
```zl
let x : Text -> `A`
let y : Text -> `This is a sentance`
let z : Text -> `Word`
```

==== Container
```zl
let x : Container -> function ( x ) <- x
let y : Container -> structure x , y
let z : Container -> enumerator A, B, C

let x : Container -> function ( x : Integer ): Integer {
    <- x
}
let y : Container -> structure {
    x -> 0.0
    y -> 1.0
}
let z : Container -> enumerator {
    A,
    B,
}
```

==== Collection
```zl
let x : Collection -> [1, 2, 3]
let y : Collection -> (`Hello`, 123)
```

=== Type Annotations
A variable or parameter may specify its type:

```zl
let x : Integer -> 10   // x : Integer
let y -> 10             // y : Variant
```

If no type is specified, Zenlang attempts to infer the type from context.

The special operator :> means “infer type from value” and may be used where explicit annotation syntax appears.

```zl
let x :> 10             // y : inferred Integer
```

=== Type Inference

Zenlang infers types in:
- variable declarations
- function returns
- arithmetic expressions
- list, tuple, and dictionary literals

== Literals

Zenlang includes the following literal types:

=== Integer literals

Sequence of digits:

```zl
0
42
123456789
1_000_000
```

=== Floating-point literals

Contain a decimal point:

```zl
3.14159
0.5
.25
10.
```

=== Number literals

Number Type can hold (Integer, Decimal, Hexadecimal, Binary, Octal)

```zl
1           // Integer
0.5         // Decimal
0x7B        // Hexadecimal
0o173       // Octal
0b01111011  // Binary
1e-5        // Scientific

// Underscored Separators
1_000_000
0xDE_AD_BE_EF
0b1101_0001
```

=== Boolean literals
```zl
True
False
```

=== Nothing and Default literals

`Nothing` represents the absence of a value (unassigned or null state).
`Default` represents the type's natural zero-state or empty value.

```zl
Nothing
Default
```

When assigned to a typed variable or evaluated in a typed context, `Default` materializes according to its type:

- `Integer`: `0`
- `Decimal`: `0.0`
- `Boolean`: `False`
- `String` / `Rune`: #raw("``", lang: "zl") (empty string)
- `List`: `[]` (empty list)
- `Map` / `Dictionary`: `{}` (empty map)
- `Structure` / `Class`: Default field zero-values / empty instance
- `Nothing` / `Void`: `Nothing`

```zl
let x : Integer -> Default
when x == Default {
    // True: x equals the zero value of its type (0)
}
when x == 0 {
    // True
}
when x == Nothing {
    // False: 0 is not Nothing
}
```

=== Rune and String literals

Runes and strings are both enclosed in backticks. A single-code-point backtick literal is a Rune and multiple-code-point backtick literal is a string.

```zl
``                      // Empty string
`c`                     // Rune
`hello world`           // String
```

=== List literals

```zl
[]                      // Empty list
[1, 2, 3, 4]            // List of numbers
[1, `a`, True]          // List of mixed types
```

=== Tuple literals

```zl
()                      // Empty tuple
(1, 2, 3)               // Tuple of numbers
(1, `a`, True)          // Tuple of mixed types
(`a` -> 1, `b` -> 2)    // Named tuple
```

=== Dictionary literals

```zl
{ }                     // Empty dictionary
{ `a` -> 1, `b` -> 2 }  // Dictionary of Key: String and Value: Number
```

== Generic literals

```zl
l{1, 2, 3}              // List
v{1, 2, 3}              // Vector
t{1, 2, 3}              // Tuple
d{`a` -> 1, `b` -> 2}   // Dictionary
```