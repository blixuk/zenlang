#import "template.typ": *

=== Function Declarations

Functions are introduced with the function keyword.

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Functions
        #v(0.5em)

        Syntax:
        ```zl
        function Identifier { ... }

        function Identifier : ReturnType { ... }

        function Identifier ( Parameters ) { ... }

        function Identifier ( Parameters ) : ReturnType { ... }
        ```
        #v(0.5em)

        Example:
        ```zl
        function hello_world {
          write(`Hello World`)
        }

        function get_greeting : String {
          <- `Hello World`
        }

        function print : String ( message : String ) {
          write(message)
        }

        function add : Integer ( a : Integer, b : Integer ) {
          <- a + b
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
        === Functions Inline
        #v(0.5em)

        Syntax:
        ```zl
        function Identifier Expression

        function Identifier <- Expression

        function Identifier : ReturnType <- Expression

        function Identifier ( Parameters ) Expression

        function Identifier ( Parameters ) <- Expression

        function Identifier ( Parameters ) : ReturnType <- Expression
        ```
        #v(0.5em)

        Example:
        ```zl
        function hello_world write(`Hello World`)

        function hello_world <- `Hello World`

        function get_greeting : String <- `Hello World`

        function print : String ( message : String ) write(message)

        function add ( a, b ) <- a + b

        function sub : Integer ( a : Integer, b : Integer ) <- a - b
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Anonymous Functions
        #v(0.5em)

        Syntax:
        ```zl
        let Identifier -> function { ... }

        let Identifier : ReturnType -> function { ... }

        let Identifier ( Parameters ) -> function { ... }
        ```
        #v(0.5em)

        Example:
        ```zl
        let hello_world -> function {
          write(`Hello World`)
        }

        let get_greeting : Function<String> -> function {
          <- `Hello World`
        }

        let print : Function<String> -> function ( message : String ) {
          write(message)
        }

        let add : Function<Integer> -> function ( a : Integer, b : Integer ) {
          <- a + b
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
        === Anonymous Functions Inline
        #v(0.5em)

        Syntax:
        ```zl
        let Identifier -> function ...

        let Identifier -> function <- ... 

        let Identifier : ReturnType -> function <- ... 

        let Identifier ( Parameters ) -> function ... 

        let Identifier ( Parameters ) -> function <- ... 
        ```
        #v(0.5em)

        Example:
        ```zl
        let hello_world -> function write(`Hello World`)

        let get_greeting : Function<String> -> function <- `Hello World`

        let print : Function<String> -> function ( message : String ) write(message)

        let add : Function<Integer> -> function ( a : Integer, b : Integer ) <- a + b
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Function Parameters
        #v(0.5em)

        Syntax:
        ```zl
        ( Identifier, ... )

        ( Identifier : Type, ... )

        ( Identifier -> Value, ... )

        ( Identifier : Type -> Value, ... )
        ```
        #v(0.5em)

        Example:
        ```zl
        ( a, b )

        ( a : Integer, b : Integer )

        ( a -> 1, b -> 2 )

        ( a : Integer -> 1, b : Integer -> 2 )
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Function Variadic Parameters
        #v(0.5em)

        Syntax:
        ```zl
        ( Identifier* )

        ( Identifier** )
        ```
        #v(0.5em)

        Example:
        ```zl
        // Variadic Arguments
        function test ( args* ) {
          write(args[0])

          for arg in args {
            write(arg)
          }
        }

        test( 1, 2, 3 )

        // Variadic Keyword Arguments
        function test ( kwargs** ) { 
          write(kwargs.a)

          for key, value in kwargs {
            write(key)
            write(value)
          }
        }

        test( a -> 1, b -> 2, c -> 3 )

        test( a : Integer -> 1, b : Integer -> 2, c : Integer -> 3 )
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Function Structrue Unpacking
        #v(0.5em)

        Syntax:
        ```zl
        ```
        #v(0.5em)

        Example:
        ```zl
        function add( x, y ) {
          write(x + y)
        }

        structure vec2 { x -> 1, y -> 2 }

        add( vec2 )
        ```
    ]
)

#block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
        === Function Returns
        #v(0.5em)

        Syntax:
        ```zl
        function Identifier : ReturnType, ... { ... }

        function Identifier : ReturnType<Type, ... > { ... }
        ```
        #v(0.5em)

        Example:
        ```zl
        // Single Return
        function add( x, y ) : Integer {
          <- x + y
        }

        let result : Integer = add( 1, 2 )

        // Multiple Returns
        function test( x, y ) : Integer, Integer {
          <- x, y
        }

        let result = test( 1, 2 ) // result is a Tuple = ( 1, 2 )

        let a, b : Integer = test( 1, 2 )

        // Multiple Return Unpacking
        function test( x, y, z ) : Tuple<Integer, Integer> {
          <- ( x * z, y * z)
        }
        
        let result -> test( 1, 2, 3 )

        let a, b : Integer -> test( 1, 2, 3 )
        ```
    ]
)
