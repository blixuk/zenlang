
Zenlang is optionally typed:
You may declare types, or let them be inferred.

// Base Values

Default     // Default Value
Nothing     // No Value

// Base Types

Void        // No Returned Value
Variant     // Tagged union, Variant Type Stores any Value

Integer     // 32-bit signed integer default
Integer[8]  // 8-bit
Integer[16] // 16-bit
Integer[32] // 32-bit
Integer[64] // 64-bit

Decimal     // 32-bit floating point default
Decimal[32] // 32-bit
Decimal[64] // 64-bit

String      // UTF-32 default
String[8]   // UTF-8 (8bits - 1 byte)
String[16]  // UTF-16 (16bits - 2 bytes)
String[32]  // UTF-32 (32bits - 4 bytes)

Boolean     // True / False 

// Collection Types

List        // Ordered, Dynamic, Mutable, Values
Set         // Unordered, Dynamic, Mutable, Unique values
Vector      // Ordered, Fixed size, Immutable, Values
Tuple       // Ordered, Fixed size, Immutable, Values with different types
Map         // Unordered, Dynamic, Mutable, Key-value pairs

// Container Types

Class       //
Object      //
Structure   //
Enumerator  //

// Action Types

Function    //
Task        //

// Abstract Types

Number      // (Integer, Decimal)
Text        // (Rune, String)
Container   // (Class, Object, Structure, Enumerator)
Collection  // (Map, List, Set, Tuple, Vector)

// User-Defined Types

Zenlang supports custom types via:
- Class
- Object
- Structure
- Enumerator

// Type Annotations

List<Type, ...>
Set<Type>`
Vector[length]<Type>
Tuple<Type, ...>
Map<Type, Type>

Structure<Type, ...>
Enumerator<Type>

-------------------------

// Base Values

Nothing // is a special type that can be assigned to any identifier and sets no value.
Default // is a special type that can be assigned to any identifier and sets default value.

-------------------------

// Base Types

Void    //
Varient // 

let a : Integer -> 10       // Value: 10
let a : Integer -> Nothing  // Value: Nothing
let a : Integer -> Default  // Value: 0

let a : Decimal -> 10.0     // Value: 10.0
let a : Decimal -> Nothing  // Value: Nothing
let a : Decimal -> Default  // Value: 0.0

let a : String -> `Hello`   // Value: `Hello`
let a : String -> Nothing   // Value: Nothing
let a : String -> Default   // Value: ``

let a : Boolean -> True     // Value: True
let a : Boolean -> Nothing  // Value: Nothing
let a : Boolean -> Default  // Value: False

// Collection Types

let a : List -> [1, 2, 3]   // Value: [1, 2, 3]
let a : List -> Nothing     // Value: Nothing
let a : List -> Default     // Value: []

let a : Set -> [1, 2, 3]    // Value: [1, 2, 3]
let a : Set -> Nothing      // Value: Nothing
let a : Set -> Default      // Value: []

let a : Vector -> [1, 2, 3] // Value: [1, 2, 3]
let a : Vector -> Nothing   // Value: Nothing
let a : Vector -> Default   // Value: []

let a : Tuple -> (1, 2, 3)                  // Value: (1, 2, 3)
let a : Tuple -> (a -> 1, b -> 2, c -> 3)   // Named Tuple
let a : Tuple -> Nothing                    // Value: Nothing
let a : Tuple -> Default                    // Value: ()

let a : Dictionary -> {`a` -> 1, `b` -> 2}  // Value: {`a` -> 1, `b` -> 2}
let a : Dictionary -> Nothing               // Value: Nothing
let a : Dictionary -> Default               // Value: {}

-------------------------

Default Type: [Type]{ ... } or [T]{ ... }
This will only work for when a type is also assigned.

let a : Vector -> {1, 2, 3}
let a :> Vector{1, 2, 3}
let a :> V{1, 2, 3}
let a -> Vector{1, 2, 3}
let a -> V{1, 2, 3}

let a : List -> {1, 2, 3}
let a :> List{1, 2, 3}
let a :> L{1, 2, 3}
let a -> List{1, 2, 3}
let a -> L{1, 2, 3}

let a : Set -> {1, 2, 3}
let a :> Set{1, 2, 3}
let a :> S{1, 2, 3}
let a -> Set{1, 2, 3}
let a -> S{1, 2, 3}v

let a : Tuple -> {1, 2, 3}
let a : Tuple -> {a -> 1, b -> 2, c -> 3}
let a :> Tuple{1, 2, 3}
let a :> Tuple{a -> 1, b -> 2, c -> 3}
let a :> T{1, 2, 3}
let a -> Tuple{1, 2, 3}
let a -> T{1, 2, 3}

let a : Map -> {`a` -> 1, `b` -> 2}
let a :> Map{`a` -> 1, `b` -> 2}
let a :> M{`a` -> 1, `b` -> 2}
let a -> Map{`a` -> 1, `b` -> 2}
let a -> M{`a` -> 1, `b` -> 2}


-------------------------

// Literals

Zenlang includes the following literal types:

// Integer literals

Sequence of digits:

0
42
123456789
1_000_000

// Floating-point literals

Contain a decimal point:

3.14159
0.5
.25
10.

// Number literals

Number Type can hold (Integer, Decimal, Hexadecimal, Binary, Octal)

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

// Boolean literals
True
False

// Nothing literal

Nothing

// String literals

String literals are both enclosed in backticks. A single-code-point backtick literal is a String and multiple-code-point backtick literal is a string.

``                      // Empty string
`c`                     // String of length 1
`hello world`           // String

// Vector literals

Vector{}                  // Empty vector
Vector{1, 2, 3, 4}        // Vector of numbers
Vector{1, 2, 3, 4}        // Vector are fixed size and can only have one type no mixed types

// List literals

List{}                      // Empty list
List{1, 2, 3, 4}            // List of numbers
List{1, `a`, True}          // List of mixed types

// Set literals

Set{}                      // Empty set
Set{1, 2, 3, 4}            // Set can only have one type no mixed types
Set{5, 6, 7, 8}            // Set can't have 2 of them same only unique values

// Tuple literals

Tuple{}                      // Empty tuple
Tuple{1, 2, 3}               // Tuple of numbers
Tuple{1, `a`, True}          // Tuple of mixed types
Tuple{a -> 1, b -> 2}        // Named tuple

// Map literals

Map{}                     // Empty map
Map{ `a` -> 1, `b` -> 2 }  // Map of Key: String and Value: Number

// Generic literals

Vector{1, 2, 3, 4}        // Vector of numbers
List{1, 2, 3, 4}          // List of numbers
Set{1, 2, 3, 4}           // Set of numbers
Tuple{1, 2, 3, 4}         // Tuple of numbers
Tuple{a -> 1, b -> 2}     // Tuple (Named)
Map{`a` -> 1, `b` -> 2}   // Map of Key: String and Value: Number

V{1, 2, 3}              // Vector
L{1, 2, 3}              // List
S{1, 2, 3}              // Set
T{1, 2, 3}              // Tuple
T{a -> 1, b -> 2}       // Tuple (Named)
M{`a` -> 1, `b` -> 2}   // Map

