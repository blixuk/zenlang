# Language: `module`, Imports, Reflection, and Plugins

| Attribute | Value |
|:---|:---|
| **Role** | Deep Reference for Module System, Entry Overrides & Reflection |
| **Authority** | Derived Language Reference (Ground Truth in [doc/SPECIFICATION.md](SPECIFICATION.md)) |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## Overview

This guide details the behavior of module context (`module`), dynamic entry point dispatch (`module.entry`), packaging (`use`/`import`/`from`), runtime reflection (`zen.reflect`), and metadata traits (`is reflectable`).

**Core Rule:** Zenlang avoids decorator magic. Traits use `is ...` (e.g. `is reflectable`), and entry point overrides use `module.entry` (data on the module).

---

## 1. Built-in `module`

Every source file has a map-like binding named **`module`**. No import is required.

### 1.1 Fields

| Field | Type | Meaning |
|-------|------|---------|
| `module.name` | String | Short name (entry: file stem; import: last path segment) |
| `module.path` | String | Logical path (entry: stem; import: dotted import path) |
| `module.file` | String | Absolute path to the source file |
| `module.dir` | String | Directory containing that file |
| `module.is_entry` | Boolean | `True` only for the **process entry** file |
| `module.entry` | String or Function | Optional **override** of which function starts the program (see §2) |

Access uses normal map/field syntax:

```zl
use zen.io

function main() {
    io.writeln(module.name)
    io.writeln(module.file)
    when module.is_entry {
        io.writeln(`this is the entry module`)
    }
    <- 0
}
```

### 1.2 Interpreter vs native

| Mode | Behavior |
|------|----------|
| **Interpret** | Each loaded file gets its own `module` map. Imported libraries have `is_entry == False`. |
| **Native (`-g`)** | Host initializes a process-level `module` for the **entry** source via `ZenModule_initialize`. |

### 1.3 Library-safe scripts

```zl
use zen.io

function helper(x) {
    <- x + 1
}

// Only runs when this file is the process entry
when module.is_entry {
    io.writeln(helper(1))
}

function main() {
    <- 0
}
```

When this file is `use`d by another program, `module.is_entry` is false (interpret), so the block does not act as a second main.

---

## 2. Entry points

### 2.1 Default: `function main()`

- Compiled programs and scripts that define **`main`** use it as the host entry.
- Integer return from `main` becomes the process exit code when the host propagates it.
- Dual execution: interpret and `-g` both honor `main` as the default entry name.

### 2.2 Custom entry: `module.entry` (no decorators)

To start at a different function (tests, alternate CLI, bypass `main`):

```zl
use zen.io

function run() {
    io.writeln(`custom entry`)
    <- 0
}

function main() {
    io.writeln(`default entry — skipped when module.entry is set`)
    <- 1
}

// String name of the function:
module.entry -> `run`

// Or a function value (same effect):
// module.entry -> run
```

**Rules (interpret and native `-g`):**

1. Definitions are registered first (`function`, `structure`, `use`/`import`, top-level `let`/`set`, …).
2. Top-level statements **from the entry file** run next (including `module.entry -> …`).
3. The host then calls:
   - the function named/held by `module.entry` if set, else
   - `main` if present, else
   - nothing further (top-level already ran).
4. Imported modules do **not** auto-run an entry function.

**Status:**

| Mode | `module.entry` |
|------|----------------|
| Interpret | **Supported** (`tests/language/module_entry_01.zl`) |
| Native `-g` | **Supported** — host C `main` dispatches after top-level; user `main` is `zen_user_main` |

There is **no** `@entry` decorator. That keeps the language consistent with `is reflectable` rather than a one-off attribute syntax.

### 2.3 Comparison

| Mechanism | Use when |
|-----------|----------|
| `function main()` | Normal tools and dual-path programs |
| `when module.is_entry { … }` | Script-only side effects without a named entry fn |
| `module.entry -> \`run\`` | Alternate entry or tests that must not run `main` |

---

## 3. Imports: `use` and packages

### 3.1 `use` is an alias for `import`

```zl
use zen.io                    // preferred
import zen.io                 // still valid

use zen.text.string as Str    // rename
from zen.io use writeln       // selective (alias of from … import)
from zen.io import writeln    // still valid
```

Default binding without `as` is the **last path segment** (`use zen.io` → name `io`).

### 3.2 Package short form

Resolver tries, under `ZEN_PATH` (and the importer’s directory first):

1. `{path}.zl`
2. `{path}/{last}.zl` (package entry)

So:

| Write | Resolves to (typical) |
|-------|------------------------|
| `use zen.io` | `lib/zen/io/io.zl` |
| `use zen.io.file` | `lib/zen/io/file.zl` |
| `use zen.time` | `lib/zen/time/time.zl` |

Prefer **`use zen.io`** over redundant `use zen.io.io`.

### 3.3 Search path

`ZEN_PATH` is a list of roots (see `scripts/zen`). Example:

```text
$REPO : $REPO/selfhost : $REPO/lib
```

---

## 4. Reflection (`zen.reflect`)

```zl
use zen.reflect as reflect
```

### 4.1 Type name and kind

```zl
reflect.type_name(1)       // `Integer`
reflect.kind(`hi`)         // `String` (alias of type_name)
reflect.type_name({})      // `Map`
reflect.type_name(function(x) { <- x })  // `Function`
```

Values also support **`.kind`** for the same tag family (maps may store a field named `kind` that overrides for structure instances).

### 4.2 Predicates

| Function | True when |
|----------|-----------|
| `is_nothing` | Nothing |
| `is_boolean` | Boolean |
| `is_integer` | Integer |
| `is_decimal` | Decimal |
| `is_string` | String |
| `is_list` | List |
| `is_map` | Map (plain map tag) |
| `is_set` | Set |
| `is_function` | Function / closure |
| `is_structure` | Reflectable structure instance or map with non-`Map` `kind` |
| `is_object` | Object-like / limited class tagging |
| `is_reflectable` | Type was declared `is reflectable` and registered |

### 4.3 Fields (maps always; structures when reflectable)

```zl
let m -> { `a` -> 1, `b` -> 2 }

reflect.fields(m)              // key list
reflect.has_field(m, `a`)
reflect.field(m, `a`)          // 1
m -> reflect.set_field(m, `c`, 3)   // rebind under -g
```

Also:

```zl
m.keys()
m.values()
m.items()    // list of { `key`, `value` }
```

Stdlib: `zen.collections.collections` → `Map.keys` / `Map.values` / `Map.items`.

### 4.4 Methods (reflectable types)

```zl
reflect.methods(x)           // list of method name strings
reflect.has_method(x, `bump`)
// method(x, name) — name probe; prefer call for invoke
```

Without `is reflectable`, method lists are empty for ordinary values.

### 4.5 Dynamic call: `reflect.call` / `reflect.apply`

```zl
// Plugin table: map of name → function
let cmds -> {
    `add` -> function(a, b) { <- a + b },
    `id`  -> function(x) { <- x }
}

reflect.call(cmds, `add`, [2, 3])    // 5
reflect.apply(cmds[`id`], [9])       // 9
```

| Receiver | Interpret | Native `-g` |
|----------|-----------|-------------|
| Map of functions | Yes | Yes |
| Reflectable class instance | Yes | Not yet (use maps for dual-path plugins) |

**Args must be a list** (use `[]` for none). Each list element is one parameter.

```zl
reflect.call(table, `help`, [])
reflect.call(table, `hello`, [`Ada`])
```

---

## 5. `is reflectable`

Opt-in **metadata**, not hidden shadow state on every value.

```zl
structure Point is reflectable {
    x: Integer
    y: Integer
}

class Counter is reflectable {
    let n: Integer

    function init() {
        self.n -> 0
    }

    function bump() {
        self.n -> self.n + 1
    }

    function value() {
        <- self.n
    }
}

function main() {
    let p -> Point { x -> 1, y -> 2 }
    ! reflect.is_reflectable(p)
    ! reflect.has_field(p, `x`)
    ! reflect.type_name(p) == `Point`

    let c -> Counter()
    c.bump()
    ! reflect.has_method(c, `bump`)
    <- 0
}
```

Also valid on `object`. Multiple traits may be listed later (`is reflectable, …`).

**What the marker does:**

- Registers field names (and class method names) in a runtime registry.
- Native structures remain map-backed with a `kind` field; reflectable classes are tagged for type-name lookup.
- Does **not** enable open monkey-patching of arbitrary types.

---

## 6. Plugins (`zen.plugins`)

Thin helpers around **map-of-functions** tables + `reflect.call`.

```zl
use zen.plugins as P
use zen.io

function hello(name) {
    io.writeln(`hi ` + name)
    <- 0
}

function main() {
    let cmds -> P.create()
    cmds -> P.add(cmds, `hello`, hello)

    ! P.has(cmds, `hello`)
    <- P.dispatch(cmds, `hello`, [`zen`])
}
```

| API | Role |
|-----|------|
| `create()` | Empty table `{}` |
| `add(table, name, fn)` | Register handler; **returns** table (rebind under `-g`) |
| `register_cmd` | Alias of `add` (avoids C keyword issues with `register`) |
| `has(table, name)` | Command present? |
| `list(table)` | Command names |
| `dispatch(table, name, args)` | `reflect.call` wrapper; `args` is a list |
| `merge(base, overlay)` | Overlay wins on key clash |

Full CLI-style demo: **`examples/plugins_demo.zl`**.

### Plugin conventions

1. Prefer **maps of functions** over classes for dual-path tools.
2. Register explicitly (`P.add`); do not rely on global magic discovery.
3. Under native, keep handlers as plain functions in maps so `reflect.call` works.
4. For process-level plugins later: prelink modules or run external processes — not free `dlopen` of arbitrary `.zl` in native binaries.

---

## 7. Quick reference

```zl
// Module context
module.name / .path / .file / .dir / .is_entry
module.entry -> `run`          // or -> run

// Imports
use zen.io
use zen.text.string as Str
from zen.io use writeln

// Reflect
use zen.reflect as reflect
reflect.type_name(x)
reflect.is_map(x) / is_integer(x) / …
reflect.fields(x) / field / set_field / has_field
reflect.methods(x) / has_method
reflect.call(recv, name, args_list)
reflect.apply(fn, args_list)

// Reflectable types
structure S is reflectable { … }
class C is reflectable { … }

// Plugins
use zen.plugins as P
P.create() / add / has / list / dispatch / merge
```

---

## 8. Tests and examples

| Path | Covers |
|------|--------|
| `tests/language/module_01.zl` | `module.*` fields, `is_entry` |
| `tests/language/module_entry_01.zl` | `module.entry` bypasses `main` |
| `tests/lib/test_reflect.zl` | predicates, map fields, keys/items |
| `tests/lib/test_reflectable.zl` | `is reflectable` structures/classes |
| `tests/lib/test_reflect_call.zl` | `call` / `apply` / plugins |
| `examples/plugins_demo.zl` | CLI plugin table |

```bash
export ZEN_PATH=$PWD:$PWD/lib
python3 bootstrap/Zen.py tests/language/module_01.zl
python3 bootstrap/Zen.py -g tests/lib/test_reflect_call.zl
python3 bootstrap/Zen.py examples/plugins_demo.zl hello
```

---

## 9. Status summary

| Feature | Interpret | Native `-g` |
|---------|-----------|-------------|
| `module.name/file/…/is_entry` | Yes | Yes (entry file) |
| `module.entry` custom start | Yes | Yes (string name or function value) |
| `use` / package short form | Yes | Yes |
| `reflect` predicates + map fields | Yes | Yes |
| `is reflectable` fields/methods meta | Yes | Yes |
| `reflect.call` map plugins | Yes | Yes |
| `reflect.call` class methods | Yes | Yes (`is reflectable` + method tables) |
| `zen.plugins` | Yes | Yes |
