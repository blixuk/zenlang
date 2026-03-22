# Objects / Model

Should they be called Objects or Models?

## object model

fluid, shape-changing runtime objects. 
flexible objects in the middle, with structs and classes remaining at the edges

This is a deliberate three-tier model.

## Object Model

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

## Shape Typing

support shape constraints, not rigid types.
This is structural typing, not nominal typing.

```

```

## Free Mixing with Structs

Objects can contain structs, and structs can contain objects.

```
player.position -> structure { x: Integer, y: Integer }
player.position.x -> 10
player.position.y -> 20

// or 

structure Position { x: Integer, y: Integer }
player.position -> Position { x -> 10, y -> 20 }
// or 
player.position -> Position { 10, 20 }

```

Create Objects from Structs

```
structure Position { x: Integer, y: Integer }

let position : Object -> object { Position }

position.x -> 10
position.y -> 20
position.z -> 30

write(position.x)
write(position.y)
write(position.z)
```

## Classes Become Templates (Optional)

```
class Enemy {
    health : Integer
    damage : Integer

    function init (health : Integer, damage : Integer) {
        self.health -> health when health not Nothing or 100
        self.damage -> damage when damage not Nothing or 10
    }

    function attack(target : Enemy) {
        target.health -> target.health - self.damage
    }
}

// Class
let enemy : Enemy -> Enemy()

enemy.health -> 100
enemy.damage -> 10

enemy.attack(enemy)

enemy.magic -> 5 // this will not work as the class does not have a magic field
write(enemy.magic) // this will not work as the class does not have a magic field

// Object
let enemy : Object -> object { Enemy() }
// or
let enemy : Object -> object { Enemy(100, 10) }

enemy.health -> 100
enemy.damage -> 10
enemy.magic -> 5

enemy.attack(enemy)

write(enemy.magic)
```

Classes:
- Do not enforce shape at runtime
- Do not prevent mutation
- Are just factory + documentation

## No Inheritance — Only Extension

```
let enemy -> object {
    health -> 50
}

enemy.boss -> true
enemy.phase -> 2

write(enemy.boss)
write(enemy.phase)

// 

function make_boss(base) {
    base.health -> base.health * 5
    base.phase -> 1
    <- base
}

let boss -> make_boss(enemy)

write(boss.health)
write(boss.phase)

```

## Identity & Equality

Entities have identity
== compares identity
Deep equality is explicit

```
when a == b { ... }        // same entity
when equal(a, b) { ... }   // structural compare
```

// Memory & Performance Model (Critical)

Entities are implemented as:
- Hash map + optional inline cache
- Hidden-class optimization possible
- Shape transitions tracked
- JIT-friendly later, but not required

## Signals (Natural Fit)

Signals are just structured fields with runtime support.

```
player.on_hit = signal(damage : Integer)

player.on_hit.connect(
    function (damage : Integer) {
        log(`Took: ` + damage)
    }
)

player.on_hit.emit(10)
```

# Serialization

Entities serialize as:
- JSON-like ?
- ZenData for saving to files (serialize and deserialize)
- Functions stripped (or referenced) ?
- Explicit opt-in for closures ?