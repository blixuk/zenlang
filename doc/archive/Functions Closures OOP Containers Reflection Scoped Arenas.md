
# Functions & Closures

Functions:
```
// function <identifier> { <statements> }

function say_hello { <- `Hello` }

// function <identifier> : <ReturnType> { <statements> }

function get_number : Integer { <- 42 }

// function <identifier> : <ReturnType> ( parameters ) { <statements> }

function add : Integer ( a : Integer, b : Integer ) { <- a + b }

// function <identifier> -> <statement>

function get_number -> 42

// unction <identifier> : <ReturnType> -> <statement>

function get_number : Integer -> 42

// function <identifier> : <ReturnType> ( parameters ) -> <statement>

function greet : String ( name : String ) -> `Hello, ` + name

```

Inline Functions:
```
// let <identifier> -> function <- <statement>

let greet -> function <- `Hello, ` + name

// let <identifier> : Function<ReturnType> -> function <- <statement>

let add : Function<Integer> -> function <- 42

// let <identifier> : Function<ReturnType> -> function { <- <statement> }

let add : Function<Integer> -> function { <- 42 }
```

Parameters may be typed or untyped:

```
function <identifier> ( <parameter>, <parameter> ) { .... }
function <identifier> ( <parameter> : <type>, <parameter> : <type> ) { .... }
```

```
// 1. Function Declaration with Return (<-) and Type Annotations:
function calculate_tax(subtotal: Decimal, rate: Decimal) : Decimal {
    <- subtotal * rate
}

// 2. Default Parameter Values:
function connect(host: String, port: Integer -> 8080, timeout: Integer -> 30) : Boolean {
    io.info(`Connecting to ` + host + `:` + Str.to_string(port))
    <- True
}

// 3. First-Class Anonymous Functions (Lambdas):
let square -> function(x) { <- x * x }
let result -> square(6) // 36

// 4. Lexical Closures (Snapshot by Value):
// Closures capture surrounding local variables by value at the moment of creation
let factor -> 10
let multiplier -> function(x) { <- x * factor } // captures factor = 10

factor -> 99
let out -> multiplier(5) // Returns 50 (5 * 10)

```

Function may omit return type if inferred.
A `return` statement may be used, or the `<-` return operator.`
Function returns with either the `return` keyword or the `<-` return operator.
Function can have parameters and default parameter values.
First-Class Anonymous Functions (Lambdas)
Lexical Closures (Snapshot by Value)

# Container Types: Structures, Classes, Objects & Enumerators

Classes (class) — Full OOP with Methods & Inheritance
Single inheritance, constructor method (init), self, and parent

Classes:
```
class <identifier> {
    let <identifier> -> <expression>

    function <identifier> {
        <statements>
    }

}

class <identifier> extends <identifier> {

    function <identifier> {
        <statements>
    }

}
```

```
class Vehicle {
    let brand: String
    let speed: Decimal

    function init(brand: String, speed: Decimal) {
        self.brand -> brand
        self.speed -> speed
    }

    function describe() : String {
        <- self.brand + ` at ` + Str.to_string(self.speed) + ` km/h`
    }
}

class ElectricCar extends Vehicle {
    let battery: Integer

    function init(brand: String, speed: Decimal, battery: Integer) {
        parent.init(brand, speed)
        self.battery -> battery
    }

    function describe() : String {
        <- parent.describe() + ` [Battery: ` + Str.to_string(self.battery) + `%]`
    }
}

let car -> ElectricCar(`Model 3`, 100.0, 92)
io.writeln(car.describe())

```

# Structures

Structures (structure) — Lightweight Data Containers
Data-first, value-oriented records

```
structure vector2 { x, y }

structure vector2 { x -> 0, y -> 0 }

structure vector3 { x: Integer, y: Integer, z: Integer }

structure vector3 { x: Integer -> 0, y: Integer -> 0, z: Integer -> 0 }

structure XYZ { 
	x -> 0.0,
	y -> 0.0,
	z -> 0.0,
	sum -> function { <- x + y + z }
}
```

```
structure Point {
    let x: Integer
    let y: Integer
}

let pt -> Point{ x -> 10, y -> 20 }
pt.x -> 15
```

# Enumerators

Enumerators (enum / Enumerator) — Named Variant States

```
enumerator Direction { 
    North -> 1, 
    South -> 2, 
    East -> 3, 
    West -> 4 
}

write(Direction)
// ( (`North`, 1), (`South`, 2), (`East`, 3), (`West`, 4) )
write(Direction.names)
// ( `North`, `South`, `East`, `West` )
write(Direction.values)
// ( 1, 2, 3, 4 )
write(Direction.South)
// (`South`, 2)
write(Direction.South.name)
// `South`
write(Direction.South.value)
// 2

```

```
enumerator Direction {
    North,
    South,
    East,
    West
}

enumerator HttpStatus {
    Ok -> 200,
    NotFound -> 404,
    ServerError -> 500
}

let status -> HttpStatus.Ok

when status is HttpStatus.Ok {
    io.info(`Success`)
}
```

# Reflection & Traits (is reflectable, zen.reflect)

Zenlang avoids decorator magic. Structures and classes declare reflectability using the is reflectable trait:

```
use zen.reflect as reflect

structure User is reflectable {
    let id: Integer
    let name: String
}

reflect.type_name(123)            // "Integer"
reflect.fields({ `a` -> 1 })      // ["a"]
reflect.has_field(User, `name`)   // True

```

# Scoped Memory Arenas (with)

For high-throughput systems programming, Zenlang provides zero-fragmentation bump arenas:

```
use zen.memory as Memory

with Memory.Arena.create(1024 * 1024) as arena {
    let scratch_buf -> Memory.alloc_in(arena, 4096)
    // All temporary allocations in this block are drawn from the arena pool
}
// Entire arena is reclaimed in O(1) time upon block exit

```

We could extend the use of 'with' for more things, like I/O operations in the future.

# Objects / Data

object model:
fluid, shape-changing runtime objects. 
flexible objects in the middle, with structs and classes remaining at the edges

The Three Tiers:

Tier	Name	Purpose
Low	    struct	Fixed, fast, value data
Middle	object	Flexible runtime objects
High	class	Optional abstraction / tooling

The Low Layer: Struct (Unchanged, Still Rigid)

Structs remain:
- Fixed layout
- Typed
- Value semantics
- No shape mutation

They exist for:
- Performance
- Serialization
- ECS
- Math
- Networking

The Middle Layer: Objects

Core Semantics

An Object is:
- A heap-allocated, identity-bearing map
- Keys are strings or symbols
- Values are any type
- Fields can be added or removed at runtime
- Functions can be attached dynamically
- No inheritance
- Shape is not fixed

Think: JavaScript object without prototypes, plus optional typing.

```
let Player -> object {
    name : String,
    health : Integer,
    attack : Integer,
    hit : Function
}

let Player -> object {
    name : String -> `Player`,
    health : Integer -> 100,
    attack : Integer -> 10,
    hit : Function -> function (target : Player) { target.health -> target.health - attack }
}

let player -> Player
player.hit(player)

player.weapon -> `Knife`
player.level :> 5

player.remove(`weapon`)
player.add(`weapon`, `Sword`)

```

Methods Are Just Fields

```
player.speak -> function : String (message : String) { <- self.name + `: ` + message }
// or 
player.speak -> function (message) <- self.name + `: ` + message
player.speak(`Hello`)

player.take_damage -> function : Integer (amount : Integer) {
    self.health -> self.health - amount
    <- self.health
}
write(`Player health: ` + player.take_damage(10))

player.get_health -> function <- self.health
```

Rules:
- self is dynamically bound
- No method tables?
- No vtables?
- No dispatch hierarchy?

Shape Typing

support shape constraints, not rigid types.
This is structural typing, not nominal typing.

Classes Become Templates (Optional)?

Do we have 'objects' or do with have 'data' that are Zen Data or do objects resolve to zen data instead of json or maps or do we have both 'objects' and 'data'?
