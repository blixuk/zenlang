=== Class Declaration

Classes define reference types with methods and fields.

```zl
class Name {
  let name : Type

  function name { .... }
}
```

=== Class Initialization

```zl
class Name {
  let name : Type -> expression

  function init ( parameters ) {
    self.name -> parameter
    statements
  }
}
```

=== Class Inheritance

```zl
class SuperClass {
  let name : Type -> expression

  function init ( parameters ) {
    self.name -> parameter when parameter or default
  }
}

class SubClass : SuperClass {
  function init ( parameters ) {
    parent.init(parameters)
    statements
  }
}
```

=== Class Instantiation

```zl
let name -> Class()
let name : Class -> Class ( parameters )

name.member
name.member -> value

name.member()
name.member ( parameters )
```

= Modules

Zenlang supports importing and exporting code between files.

== Importing

```zl
import math
import utils.helpers
from gui import Button

from zen.io import write
from zen.io import read as r
```

== Exporting

```zl
export function foo { .... }
export class Person { .... }
```
