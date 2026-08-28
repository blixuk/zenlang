= Structures, Classes & OOP

Zenlang supports both lightweight data structures and full object-oriented classes with methods and state encapsulation.

== Structures (`struct`)

Structures are pure, named data records:

```zl
struct Point {
    x: Integer,
    y: Integer
}

function main() {
    let p -> Point(10, 20)
    io.writeln(`Point coordinates: ` + Str.to_string(p.x) + `, ` + Str.to_string(p.y))
    <- 0
}
```

== Classes & Object-Oriented Programming (`class`)

Classes encapsulate both state and behavior. Methods receive an implicit `self` reference:

```zl
use zen.io
use zen.text.string as Str

class Counter {
    let count -> 0

    function increment() {
        self.count -> self.count + 1
        <- self.count
    }

    function decrement() {
        self.count -> self.count - 1
        <- self.count
    }

    function reset() {
        self.count -> 0
    }

    function get_value() {
        <- self.count
    }
}

function main() {
    let c -> Counter()
    c.increment()
    c.increment()
    io.writeln(`Count is: ` + Str.to_string(c.get_value())) // 2
    <- 0
}
```

=== Constructors with Initialization

```zl
class Rectangle {
    let width -> 0
    let height -> 0

    function area() {
        <- self.width * self.height
    }

    function perimeter() {
        <- 2 * (self.width + self.height)
    }
}

function create_rect(w, h) {
    let r -> Rectangle()
    r.width -> w
    r.height -> h
    <- r
}
```

== Algebraic Data Types (ADTs)

ADTs allow modeling domain entities as closed sets of variants:

```zl
enum Shape {
    Circle(radius: Decimal),
    Rect(width: Decimal, height: Decimal)
}

function describe_shape(shape) {
    check shape {
        case Shape.Circle(r) {
            io.writeln(`Circle with radius: ` + Str.to_string(r))
        },
        case Shape.Rect(w, h) {
            io.writeln(`Rectangle: ` + Str.to_string(w) + `x` + Str.to_string(h))
        }
    }
}
```
