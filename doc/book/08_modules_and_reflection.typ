= Modules, Packages & Reflection

As programs grow, structuring code into reusable modules and understanding runtime types through reflection becomes essential.

== Modules & Packages (`use`)

Every `.zl` file is a module. To import and bring external packages into scope, use the canonical `use` keyword:

```zl
// Standard package imports (binds to the final segment: io, time, reflect)
use zen.io
use zen.time
use zen.reflect

// Qualified imports with explicit aliases
use zen.text.string as Str
use zen.math.math as Math
use zen.ui.table as table

// Relative module imports
use `./math_utils.zl` as utils
```

== The Built-in `module` Object

Every Zenlang file has access to the implicit `module` object to query its execution environment:

```zl
use zen.io
use zen.text.string as Str

function main() {
    io.writeln(`Module Name: ` + module.name)
    io.writeln(`Module Path: ` + module.path)
    io.writeln(`Is Entry Point: ` + Str.to_string(module.is_entry))
    <- 0
}
```

=== Custom Module Entry Points

You can define custom start functions and set `module.entry`:

```zl
function run_server() {
    io.writeln(`Server daemon started!`)
    <- 0
}

module.entry -> `run_server`
```

== Runtime Reflection with `zen.reflect`

The `zen.reflect` standard library package provides comprehensive introspection:

```zl
use zen.io
use zen.reflect
use zen.text.string as Str

function inspect_value(val) {
    let t -> reflect.type_name(val)
    io.writeln(`Type: ` + t)

    when reflect.is_list(val) {
        io.writeln(`Contains ` + Str.to_string(val.length) + ` elements`)
    } or when reflect.is_map(val) {
        io.writeln(`Keys: ` + Str.join(val.keys(), `, `))
    }
}

function main() {
    inspect_value(`Hello`)            // Type: String
    inspect_value([1, 2, 3])          // Type: List, Contains 3 elements
    inspect_value({ `a` -> 1, `b` -> 2 }) // Type: Map, Keys: a, b
    <- 0
}
```
