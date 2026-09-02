#import "template.typ": *

= Object-Oriented Programming & Classes

Classes in Zenlang define reference types with encapsulated fields, constructor initialization, and instance methods.

== Class Declarations

Classes are declared using the `class` keyword. Fields are declared with `let`, and constructors are named `init`:

#feature(
    "Class Declaration & Methods",
    "class Identifier {\n    let field_name\n\n    function init(Parameters) {\n        self.field_name -> Parameter\n    }\n\n    function method_name() {\n        ...\n    }\n}",
    "class BankAccount {\n    let owner : String\n    let balance : Decimal\n\n    function init(owner: String, initial_balance: Decimal -> 0.0) {\n        self.owner -> owner\n        self.balance -> initial_balance\n    }\n\n    function deposit(amount: Decimal) {\n        self.balance -> self.balance + amount\n    }\n\n    function get_balance() : Decimal {\n        <- self.balance\n    }\n}"
)

== Instantiation & Usage

Creating an instance invokes the `init` constructor method automatically:

```zl
let account -> BankAccount(`Alice`, 100.0)
account.deposit(50.0)

io.writeln(`Account Balance: ` + Str.to_string(account.get_balance())) // 150.0
```

#note[
  Under dual-path compilation (`-g`), classes are compiled into C structs with associated method dispatch functions. For maximum speed in compiler and low-level code, free functions operating on maps or structures are also idiomatic.
]
