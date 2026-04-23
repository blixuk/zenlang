# Zenlang Language Specification (Draft v0.1)

Zenlang is a modern, minimal, optionally-typed programming language designed for clarity, flexibility, and rapid development. The language blends concepts from Python, JavaScript, and statically typed languages while maintaining its own identity. Zenlang supports both interpreted and compiled execution models and is built around simple syntax, powerful type inference, and a flexible object system.

## Introduction
Zenlang is a high-level programming language designed to be:

- Beginner-friendly with readable syntax inspired by Python & JavaScript
- Optionally statically typed (types can be declared or inferred)
- Object-oriented, with classes and mutable objects
- Capable of both interpreted and compiled execution
- Async/await capable to support concurrent operations
- Suitable for CLI, GUI, and web applications
- Supports ZenScript (.zs) for quick, dynamic execution
- Supports ZenLang (.zl) for compiled, optimized binaries

The language focuses on simplicity, extensibility, and ease of prototyping while remaining powerful for full-scale applications.

## Lexical Structure

### Source Code Representation

Zenlang source files are UTF-8 encoded text. Whitespace generally has no semantic meaning except to separate tokens. Newlines may influence indentation in the future but currently do not affect parsing.

Whitespace is ignored except inside:
- Strings
- Multiline strings
- Comments

Indentation is not syntactically significant (unlike Python).
Blocks use: 
```
{ } 
```

### Comments

Single-line:
```
// this is a comment
```

Multi-line:
```
/*
This is a multi-line comment
*/
```

Multi-line comments cannot nest.

### Identifiers

Identifiers name variables, functions, classes, types, and other symbols.

An identifier consists of:
- a leading letter or underscore
- followed by letters, digits, or underscores

Identifiers must match:

```
[a-zA-Z_][a-zA-Z0-9_]*
```

Examples:
```
x
helloWorld
_myVar
HTTPServer
```

Identifiers are case-sensitive.

### Keywords
Reserved keywords (cannot be used as identifiers):

```
let
set
type

class
function
structure
enumerator
check

do
when
while
until
for
break
continue
in

and
or
not

True 
False

try
catch
raise

async 
await

import
export
extend
from
```

## Literals

Zenlang includes the following literal types:

### Integer literals
Sequence of digits:
```
0
42
123456789
```

### Floating-point literals
Contain a decimal point:
```
3.14159
0.5
.25
10.
```

### Boolean literals
```
True
False
```

### Nothing literal
```
Nothing
```

### Character and String literals
Characters and strings are both enclosed in backticks. A single-code-point backtick literal is a character; longer text is a string.
```
`c`
`hello world`
```

### List literals
```
[]
[1, 2, 3, 4]
```

### Tuple literals
```
(1, 2, 3)
```

### Dictionary literals
```
{ "a" -> 1, "b" -> 2 }
```

## Types
Zenlang is optionally typed:
You may declare types, or let them be inferred.

### Built-in Types
Zenlang defines several primitive types:
```
Void      - No returned value
Variant   - Tagged union; stores any Zen value
Integer   - 64-bit signed integer
Float     - 64-bit floating point
Boolean   - True / False
Character - Unicode scalar value
String    - UTF-8 string
```

### User-Defined Types
Zenlang supports custom types via:
- classes
- structures
- enumerators

Classes support inheritance. Structures are simple value types. Enumerators define closed sets of named variants.

Classes:
```
class Animal {
    name : String
    function speak {
        write("...")
    }
}

class Dog extends Animal {
    function speak {
        write("Woof!")
    }
}
```

Structures:
```
structure vector2 { x, y }

structure XYZ { 
	x -> 0.0,
	y -> 0.0,
	z -> 0.0,
	sum -> function { <- x + y + z }
}
```

### Type Annotations
A variable or parameter may specify its type:

```
let x : Integer -> 10   // x : Integer
let y -> 10             // y : Variant
```

If no type is specified, Zenlang attempts to infer the type from context.

The special operator :> means “infer type from value” and may be used where explicit annotation syntax appears.

```
let x :> 10             // y : inferred Integer
```

### Type Inference
Zenlang infers types in:
- variable declarations
- function returns
- arithmetic expressions
- list, tuple, and dictionary literals

## Variable Declarations

### let Variable (mutable)
```
let name -> expression
let name : Type -> expression

let x -> 10
let y : Float -> 3.14
let z :> `Hello World`
```

### set Constant (immutable)
```
set name : Type -> expression

set PI : Float -> 3.14159
```
Trying to reassign a set raises an error.

### Assignment typing
```
let x -> 1            // Type will be resolved to Variant and inferred as Integer
let y : Integer -> 2  // Type will be resolved as Integer
let z :> 3            // Type will be resolved to Integer and inferred as Integer
```

## Functions Declarations

Functions are introduced with the function keyword.

### Functions:
```
function name { statements }
function name : ReturnType { statements }
function name : ReturnType ( parameters ) { statements }

function name -> statement
function name : ReturnType -> statement
function name : ReturnType ( parameters ) -> statement
```

### Inline Functions:
```
let name -> function <- statement
let name : Function<ReturnType> -> function <- statement
```

A function may omit return type if inferred.
A `return` statement may be used, or the `<-` return operator.

### Parameters:

Parameters may be typed or untyped:

```
function name ( name, name ) { .... }
function name ( name : String, name : Integer ) { .... }
```

### Async Functions

```
async function name ( .... ) { .... }

await name( .... )
```

## Class Declarations

Classes define reference types with methods and fields.

```
```

## 5. Expressions
Zenlang expressions evaluate to values.

### 5.1 Literals
```
10        - Integer
3.14      - Float
`hello`   - String
`c`       - Character
True      - Boolean
False     - Boolean
Nothing   - No value
```

### 5.2 Binary Operators
```
+ - * / % ^       - arithmetic
== != < > <= >=   - comparison
and or            - logical (short-circuiting)
```

### 5.3 Unary Operators
```
-expression        - negate
not expression     - logical not
```

### 5.4 Function Calls
```
write("hi")
```

### 5.5 Member Access
```
object.name
object.method()
```

### 5.6 Indexing
```
list_item[0]
dictionary_item[`key`]
```

## 6. Statements

### 6.1 Variable Assignment
`->` symbol for assignments
```
let x -> 10
x -> x + 1
```

### 6.2 Return Statement
can use `return` keyword or `<-` symbol for returns
```
function multiply(a, b) : Integer {
  <- a * b
}

function add(a, b) : Integer {
  return a + b
}
```

### 6.3 Control Statements
```
when <condition> { 
  .... 
}

when <condition> { 
  .... 
} or { 
  .... 
}

when <condition> {
  ....
} or <condition> {
  ....
} or {
  ....
}
```

Inline version:
```
let messsage -> `positive` when x > 0 or `negative`
```

### 6.4 Do Loop
```
do {
  write(`Done`)
}
```

### 6.5 Do when Loop
```
do when <condition> {
  write(`Done`)
}

do when <condition> {
  write(`Working`)
} or {
  write('Done')
}
```

### 6.6 Do While Loop
```
// pre check
let a -> 0
do while a < 3 {
  write(a)
  a -> a + 1
}

// post check
let z -> 0
do {
  write(z)
  z -> z + 1
} while z == 1

// or only with pre check
let b -> 0
do while b < 3 {
  write(b)
  b -> b + 1
} or {
  write(`Else`)
}
```

### 6.7 Do Until Loop
```
// pre check
let c -> 0
do until c == 3 {
  write(c)
  c -> c + 1
}

// post check
let x -> 0
do {
  write(x)
  x -> x + 1
} until x == 1
```

### 6.8 Do For Loop
```
do for i in [1, 2, 3, 4] {
  write(i)
}

do for i in [] {
  write(i)
} or {
  write(`empty`)
}
```

6.9 Break / Continue
As expected in loops.

## 7. Functions

### 7.1 Declaration
```
function add(a : Integer, b : Integer) : Integer {
  <- a + b
}
```

Return type is optional if inferred defualts to Variant:
```
function test {
  <- 10 * 2
}
```

### 7.2 Anonymous Functions
```
let x -> function(x) { <- x * 2 }
let x -> function(x) : Integer { <- x * 2 }
let x : Function -> function(x) : Integer { <- x * 2 }
let x : Function<Integer> -> function : Integer { <- 1 }
```

### 7.3 Async Functions (proposed)
```
async function loadData {
  let x -> await http.get("...")
}
```

## 8. Classes

### Syntax:
```
class Name {
  field1 : Type
  field2 : Type
    
  function method1 { ... }
}
```

### Constructor:
```
class Person {
  name : String
  age : Integer

  function init(n, a) {
    name -> n
    age -> a
  }
}
```

### Instantiation:
```
let p -> Person("bob", 30)
```

### Inheritance:
```
class Dog extends Animal { ... }
```

## 9. Error Handling

### 9.1 Try / Catch
```
try {
  dangerous()
} catch error {
  write(error)
}
```

### 9.2 Raise
```
raise "Error message"
```

## 10. Async / Await (proposed)
Zenlang supports asynchronous operations:
```
async function fetchData {
  let res -> await http.get("https://...")
  <- res
}
```

Await may only be used inside async functions.

## 11. Modules & Imports

### Standard Libiaries:
```
import math
import core
```

### File-level modules:
```
// import file
import token

// import folder.file
import lexer.token

// from file import class
from token import Token

// from folder.file import class
from lexer.token import Token
```

### Exports (proposed): 
```
export function foo { ... }
export set PI -> 3.14
```
or exported (public) by defualt and use '_Ienditfier' for private (not exported)
```
// private (not exported)
function _foo { ... }

// public (exported)
function bar { ... }
```

## 12. Standard Library Overview

Includes built-ins for:

### I/O:
```
output
input
```

### System:
```
exit
```

### Collections:
- Lists
- Dictionaries
- Sorting
- Iterators / Iterables
- Containers
- Sets

### Proposed:
- HTTP (Async)
- GUI (Widgets, windows, events)
- Concurrency (Async tasks, event loop)

## 13. Runtime Model
Zenlang’s runtime includes:
- A garbage-collected or ref-counted heap (TBD)
- A variant value representation supporting dynamic typing
- Native stack frame for function calls
- Async event loop for await
- Standard library modules
- Optional JIT execution for .zs scripts
- Compilation pipeline for .zl files

## 14. Compilation Pipeline
 - 1. Lexer → tokens
 - 2. Parser → AST
 - 3. Type Checker → annotated AST
 - 4. Interpreter / Optimizer (optional)
 - 5. LLVM Backend → LLVM IR
 - 6. Object File / JIT
 - 7. Executable or REPL execution

## 15. Target File Types

ZenScript - `.zs`
- Interpreted
- Optional typing
- Fast iteration

ZenLang - `.zl`
- Optionally Statically typed
- Compiled to native code
- Optimizable

## 16. Future Extensions (Optional)
- Comment Documentation (ZenMark)
- System Calls (Linux syscalls)
- Pattern matching (match)
- Traits / interfaces
- Enumerators with methods
- Generics
- Macro system
- Reflection
- Metaclasses
- Namespace system
- Asembly in code (ASM)
- C interfaces ABI (application binary interface)
- Godot interfacing to allow use of Godot GUI?
