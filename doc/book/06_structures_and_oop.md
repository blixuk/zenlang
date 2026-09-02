# Chapter 6: The Three Container Tiers & Object Architecture

Zenlang provides a three-tiered container hierarchy that satisfies every systems and application need: low-level C ABI records (`structure`), fluid dynamic objects (`object`), and nominal OOP classes (`class`).

---

## 1. Low Tier: Value Records (`structure`)

Structures are pure, stack-allocated (or arena-allocated) value records with zero indirection. They directly match the host C ABI layout:

```zl
use zen.io
use zen.text.string as Str

// 1. Minimal untyped field declaration:
structure Vector2 { x, y }

// 2. Typed structure with default values:
structure Vector3 {
    x: Integer -> 0,
    y: Integer -> 0,
    z: Integer -> 0
}

function main() {
    // Instantiation:
    let pt -> Vector2{ x -> 10, y -> 20 }
    let v3 -> Vector3{ z -> 50 } // x and y default to 0

    io.writeln(`pt.x: ` + Str.to_string(pt.x))
    <- 0
}
```

---

## 2. Middle Tier: Fluid Dynamic Objects (`object`)

An `object` is a heap-allocated runtime entity with dynamic fields, bound `self`, and direct 1:1 fidelity with **Zen Data (`.zd`)**:

```zl
use zen.io

// 1. Declaring an Object Blueprint or Instance:
let Player -> object {
    name   : String   -> `Hero`,
    health : Integer  -> 100,
    attack : Integer  -> 15,
    speak  : Function -> function(msg: String) -> self.name + `: ` + msg
}

let player -> Player

// 2. Dynamic Field Additions:
player.weapon -> `Excalibur`
player.level  :> 1           // Type-locked to Integer

// 3. Dynamic Field Removal:
player.remove(`weapon`)

// 4. Bound Method Invocation:
io.writeln(player.speak(`Ready for the quest!`))
```

### 1:1 Zen Data (`.zd`) Roundtrip
Objects serialize directly into human-readable Zen Data and deserialize back into active runtime objects without JSON/YAML schemas:

```zl
use zen.data.zendata as zd

let serialized -> zd.stringify(player)
let restored   -> zd.parse(serialized)
```

---

## 3. High Tier: Nominal Classes & Single Inheritance (`class`)

Classes provide formal nominal object-oriented programming with constructors (`init`), single inheritance (`extends`), `self`, and `parent`:

```zl
use zen.io
use zen.text.string as Str

class Entity {
    let id: Integer
    let name: String

    function init(id: Integer, name: String) {
        self.id -> id
        self.name -> name
    }

    function describe() : String {
        <- `#` + Str.to_string(self.id) + `: ` + self.name
    }
}

class Monster extends Entity {
    let power: Integer

    function init(id: Integer, name: String, power: Integer) {
        parent.init(id, name)
        self.power -> power
    }

    function describe() : String {
        <- parent.describe() + ` [Power: ` + Str.to_string(self.power) + `]`
    }
}

function main() {
    let dragon -> Monster(1, `Red Dragon`, 9000)
    io.writeln(dragon.describe())
    <- 0
}
```

---

## 4. Enumerators & Reflection (`enumerator` / `enum`)

Enumerators define named variant states with first-class introspection properties:

```zl
enumerator Direction {
    North -> 1,
    South -> 2,
    East  -> 3,
    West  -> 4
}

// Built-in Reflection Properties:
Direction.names        // (`North`, `South`, `East`, `West`)
Direction.values       // (1, 2, 3, 4)
Direction.North.name   // `North`
Direction.North.value  // 1

let heading -> Direction.East
when heading is Direction.East {
    io.info(`Heading towards sunrise`)
}
```

---

## 💡 Chapter Exercises

1. Create a `BankAccount` class with `deposit(amount)`, `withdraw(amount)`, and `get_balance()` methods. Ensure withdrawals exceeding the balance are prevented.
2. Create a `Vector2D` struct and write an `add_vectors(v1, v2)` function.
