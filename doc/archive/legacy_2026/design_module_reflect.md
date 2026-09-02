# Design: `module`, entry points, and `reflect`

Status: **P0–P3a largely implemented** (no `@entry` decorator — use `module.entry` instead).

**User-facing language documentation:** [Language_Module_and_Reflect.md](Language_Module_and_Reflect.md)  
(Also: Getting Started §4.8b–4.9, Zenlang Explained §7, Standard_Library_Reference for `zen.reflect` / `zen.plugins`.)

Goal: explicit module context, optional script entry, and opt-in reflection — without Python/JS open-object magic, and with dual-path (interpret + `-g`) in mind.

### Implemented now

- Built-in map `module` with `name`, `path`, `file`, `dir`, `is_entry`
- **`module.entry -> \`run\``** (string) or **`module.entry -> run`** (function value) selects process entry; bypasses `main` when set (interpreter)
- **`zen.reflect`**: predicates, map fields, **`call` / `apply`** (map plugin tables + class methods dual-path under `-g`)
- **`zen.plugins`**: `create` / `add` / `has` / `list` / `dispatch` / `merge`
- **`is reflectable`** on structure/class/object
- Tests: `module_01`, `module_entry_01`, `test_reflect`, `test_reflectable`, `test_reflect_call`
- Example: `examples/plugins_demo.zl`

### Not using decorators

No `@entry` / `@reflectable`. Traits use **`is reflectable`**. Entry uses **`module.entry`**.

Related: package short form + `use` alias (done); maps-as-records in selfhost.

---

## 1. Principles

1. **Explicit over magic** — no hidden `__dict__` on every value; reflection is named and opt-in for rich types.
2. **Dual-path first** — anything in the surface must have a story for interpret *and* native (`-g`).
3. **Maps are the dynamic record** — free-form field lists live there; classes/structures add metadata only when asked.
4. **Small core, expandable stdlib** — `module` is tiny host state; `reflect` can grow in `lib/zen/reflect/`.
5. **Prefer free functions** for dual-path reliability (`reflect.fields(x)`), with **method sugar** where it is already natural (`m.keys`).

---

## 2. Built-in `module`

### 2.1 API (proposed)

Injected per compilation unit / runtime module object (not user-assignable globals):

| Member | Type | Meaning |
|--------|------|---------|
| `module.name` | String | Logical name (`zen.io`, `main`, `my_tool`) |
| `module.path` | String | Import path as resolved (dotted or as written) |
| `module.file` | String | Absolute (or project-relative) source file path |
| `module.dir` | String | Directory of `module.file` |
| `module.is_entry` | Boolean | True if this file is the process entry module |
| `module.is_main` | Boolean | Alias of `is_entry` (Python familiarity) — pick **one** name in the end; prefer `is_entry` |

Optional later:

| Member | Meaning |
|--------|---------|
| `module.version` | If we ever stamp packages |
| `module.exports` | List of export names (needs export table) |
| `module.id` | Stable unique id for caching |

### 2.2 Shape in language

**Preferred:** a host binding `module` (like a sealed map / structure), not dunders:

```zl
use zen.io

when module.is_entry {
    io.writeln(`running ` + module.file)
}

function main() {
    io.writeln(module.name)
    <- 0
}
```

**Alternative:** nest under sys — `sys.module.file` — worse for scripts that want a one-liner.

**Not preferred:** `__name__`, `__file__` as special identifiers (works, but not Zen tone).

### 2.3 Implementation sketch

| Path | Behavior |
|------|----------|
| **Interpret** | When loading a module, define `module` in that module’s environment map |
| **Native** | Emit a static `ZenModuleInfo` per file + pointer/global for entry; or inject as `const` map in each TU |

Entry file: the path passed to `Zen.py` / `zen_program` argv0’s source (interpret) or the TU that defines host `main` (native).

---

## 3. Entry points (compiled + scripts)

Today:

- **Compiled / dual-path programs:** `function main()` is the host entry (return code).
- **Scripts:** top-level statements run; `main` may also exist and is called by host when present (bootstrap behavior — keep consistent).

### 3.1 Goals

- Optional, clean way to mark “this is where the program starts” for scripts.
- Do not force `main` on every one-liner.
- Do not break existing `main()`.

### 3.2 Recommended model (layered)

**Layer A — keep `main()` as the universal entry (default)**  
If `main` exists, host calls it after loading (interpret + native). Exit code from return value.  
Top-level statements still run first (module init), then `main` — same as many languages’ “init then main”.

**Layer B — `module.is_entry` guards (no new syntax)**  

```zl
use zen.io

// library-safe helpers always available
function greet(name) {
    io.writeln(`hi ` + name)
}

when module.is_entry {
    greet(`world`)
}
```

This is the cleanest “optional script entry” without new keywords: **init code + entry-only block**.

**Layer C — optional explicit entry annotation (later, if needed)**  

```zl
@entry
function run() {
    <- 0
}
```

or:

```zl
entry function run() { <- 0 }
```

Rules if introduced:

- At most one `@entry` / `entry function` per program (or per entry module).
- If both `@entry` and `main` exist → error (or define priority: `@entry` wins, document it).
- If neither exists → top-level only (script style).

**Recommendation:** ship **A + B** first (`main` + `module.is_entry`). Add **C** only if people hate wrapping entry logic in `when module.is_entry`.

### 3.3 What not to do

- Don’t invent a second parallel runtime (“scripts never have main”).
- Don’t auto-run every function named `start` / `run` without marking.
- Don’t require entry for libraries.

---

## 4. `reflect` package

### 4.1 Naming consistency

Your list mixed `fields` / `get_fields` and duplicated `is_function`. Prefer **one verb pattern**:

| Family | Role | Examples |
|--------|------|----------|
| **Predicates** | `is_*` → Boolean | `is_list`, `is_map`, `is_structure` |
| **Presence** | `has_*` → Boolean | `has_field`, `has_method` |
| **Read** | bare plural / singular | `fields(x)`, `field(x, name)`, `methods(x)` |
| **Write** | `set_*` | `set_field` (maps always; reflectable types when allowed) |

Avoid both `fields` and `get_fields` — pick **`fields` / `field`** (shorter, Zen-like).

Rename:

- `is_dict` → **`is_map`** (Zen type is Map, not dict)
- `is_struct` → **`is_structure`** (keyword is `structure`)
- `properties` — define carefully (see below)

### 4.2 Core API (v1 — ship first)

```zl
use zen.reflect as reflect

// Type / kind
reflect.type_name(x)      // "Integer", "Map", "Point", "Function", …
reflect.kind(x)           // stable enum-like string; align with existing .kind where possible

// Predicates (values)
reflect.is_nothing(x)
reflect.is_boolean(x)
reflect.is_integer(x)
reflect.is_decimal(x)
reflect.is_string(x)
reflect.is_list(x)
reflect.is_map(x)
reflect.is_function(x)    // includes closures
reflect.is_structure(x)   // structure instance
reflect.is_class(x)       // class instance (object)
reflect.is_object(x)      // class instance (alias of is_class if we only have one OOP instance kind)
reflect.is_type(x)        // is a type object / constructor, if we reify types later

// Presence
reflect.has_field(x, name)
reflect.has_method(x, name)   // false unless type is reflectable or map-callable convention

// Read (always safe: empty list / nothing if N/A)
reflect.fields(x)             // List of string names
reflect.field(x, name)        // value or nothing
reflect.methods(x)            // List of string names (reflectable only; else [])
reflect.method(x, name)       // function value or nothing

// Write (restricted)
reflect.set_field(x, name, value)   // maps always; reflectable instances if mutable fields
```

### 4.3 Properties vs fields vs methods

Keep the model small:

| Concept | Meaning in Zen |
|---------|----------------|
| **Field** | Data slot (structure field, map key, class instance field) |
| **Method** | Callable associated with a type (class/structure method) |
| **Property** | Optional later: field with get/set functions — **defer** until we have real property syntax |

v1: **do not ship `properties` / `has_property`** unless we define property declarations. Otherwise “property” becomes a synonym soup for field.

### 4.4 `set_method` — careful

```zl
reflect.set_method(x, name, fn)
```

- **Maps:** OK as `x[name] -> fn` if you allow function values in maps (plugin tables).
- **Classes:** only if type is `reflectable` **and** we document “debug/plugin only”; native may no-op or error in release.
- **Default recommendation:** v1 supports `set_field` only; `set_method` in v2 for maps + reflectable types.

### 4.5 Call by name (v2)

```zl
reflect.call(x, name, args_list)
// or
reflect.apply(method, args_list)
```

Useful for plugins; needs dual-path story (interpreter easy; native needs method table).

---

## 5. Opt-in `reflectable`

### 5.1 Preferred syntax

Align with existing `extends` / future traits:

```zl
structure Point is reflectable {
    x: Integer
    y: Integer
}

class Widget is reflectable {
    // ...
}

// Optional later
function plugin_hook(x) is reflectable {
    <- x
}
```

Multiple markers later:

```zl
class Foo is reflectable, serializable {
}
```

### 5.2 Alternatives

| Syntax | Pros | Cons |
|--------|------|------|
| `is reflectable` | Readable, matches “is” keyword | Need grammar for post-name traits |
| `@reflectable` above decl | Easy to parse, familiar | Less “Zen wordy” |
| `structure Point reflectable {` | Compact | Ambiguous vs field names |
| Always-on reflection | No marker | Expensive / noisy on native |

**Recommendation:** `is reflectable` as the long-term form; if grammar is hard short-term, ship `@reflectable` as equivalent.

### 5.3 What the marker means

For a reflectable type **T**, the compiler emits metadata:

```text
T.__meta__ = {
  name, kind,
  fields: [{ name, type_name, offset/key }],
  methods: [{ name, arity, mangled_symbol }],
}
```

Runtime:

- `reflect.fields(instance_of_T)` reads meta  
- Non-reflectable: `fields` for **maps** still works (keys); for opaque class instances returns `[]` or only public documented slots  

### 5.4 Functions as reflectable

Usually low value for v1. Prefer:

- reflect **on function values**: `is_function`, maybe `arity` later  
- not “function declaration is reflectable”

---

## 6. Intuitive collection / structure sugar

These are **data protocols**, not full reflection. Prefer implementing as **stdlib methods / free functions** that dual-path already understand.

### 6.1 Maps

```zl
let m -> { `x` -> 1, `y` -> 2 }

m.keys        // or m.keys()   — List of keys
m.values      // List of values
m.items       // List of { `key`, `value` } or [k, v] pairs — pick one
```

**Recommendation:** methods with **empty call form** optional later; start with **functions or methods that are calls** for dual-path clarity:

```zl
Map.keys(m)
Map.values(m)
Map.items(m)
// plus method form if receiver dispatch is solid:
m.keys()
```

Property form `m.keys` without `()` is nicer but collides with “key named keys” and needs field-vs-method rules. Prefer **`keys()`** first.

### 6.2 Lists

```zl
let xs -> [1, 2, 3]
xs.length     // already exists conceptually
// items() is redundant with the list itself — skip or alias to copy
xs.enumerate()  // later: [[0,1],[1,2],...]
```

**Skip `list.items`** unless it means something distinct (e.g. copy). A list *is* its items.

### 6.3 Structures

```zl
structure Point { x: Integer, y: Integer }
let p -> Point { x -> 1, y -> 2 }

// Only if reflectable OR always for structures (cheaper than classes):
p.fields()     // [`x`, `y`]
// or
reflect.fields(p)
```

**Recommendation:** structures can always expose field names (layout known); classes require `reflectable` for methods. Or both require `reflectable` for consistency.

### 6.4 Unified protocol (optional trait)

```zl
// Conceptual — not required v1
// Iterable keys: Map
// Iterable fields: Structure/Class reflectable
```

---

## 7. Unified mental model

```text
                    ┌─────────────┐
                    │   module    │  context of *this file*
                    └─────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   module.is_entry    module.file      (exports later)
         │
         │  entry policy: main() and/or when module.is_entry { }
         ▼
┌──────────────────────────────────────────┐
│                 values                    │
│  Map: always dynamic (keys/values/items) │
│  List: length, index                     │
│  Structure/Class: data; methods if any   │
└──────────────────────────────────────────┘
         │
         │  reflect.*
         ▼
┌──────────────────────────────────────────┐
│ predicates + fields/methods + set_field  │
│ rich method tables only if reflectable   │
└──────────────────────────────────────────┘
```

---

## 8. Example: library-safe script

```zl
use zen.io
use zen.reflect as reflect

structure Counter is reflectable {
    n: Integer
}

function bump(c) {
    c.n -> c.n + 1
    <- c
}

function main() {
    let c -> Counter { n -> 0 }
    c -> bump(c)
    io.writeln(reflect.type_name(c))
    io.writeln(reflect.fields(c).length)  // or join names
    <- 0
}

// Script-style alternative without main:
// when module.is_entry {
//     // same body
// }
```

---

## 9. Phased delivery

| Phase | Deliver | Dual-path |
|-------|---------|-----------|
| **P0** | `module.file`, `module.name`, `module.is_entry` | Interpret + native const module info |
| **P0** | Document `main()` + `when module.is_entry` entry policy | Host already calls `main` |
| **P1** | `zen.reflect` predicates + `type_name` / `kind` | Map to runtime type tags |
| **P1** | `fields` / `field` / `set_field` for **maps** | Existing map ops |
| **P1** | `Map.keys` / `values` / `items` (and method form if easy) | Stdlib + runtime |
| **P2** | `is reflectable` (or `@reflectable`) on structure/class | Emit metadata in C |
| **P2** | `fields`/`methods` for reflectable instances | Metadata tables |
| **P3** | `call` by name, `set_method` on maps/plugins | Interpreter first; native subset |
| **P3** | `@entry` / `entry function` if still wanted | Host entry selection |

---

## 10. Open choices (decide when implementing)

1. **`module.is_entry` vs `module.is_main`** — recommend **`is_entry` only**.  
2. **Structures always field-reflectable?** — recommend **yes for fields**, methods still need marker if any.  
3. **`keys` vs `keys()`** — recommend **`keys()`** first.  
4. **Trait grammar `is reflectable` vs `@reflectable`** — either; ship attribute first if faster.  
5. **Top-level then `main` order** — document clearly; don’t run `main` twice.

---

## 11. Summary

| Idea | Verdict |
|------|---------|
| `module.name` / `path` / `file` / `is_entry` | **Yes** — core |
| Optional script entry | **`when module.is_entry` + existing `main()`**; `@entry` later if needed |
| `reflect.*` free functions | **Yes** — consistent `is_` / `has_` / `fields` / `set_field` |
| Drop dual `get_fields` / `properties` in v1 | **Yes** — keep surface small |
| `is reflectable` | **Yes** — metadata, not shadows |
| `m.keys()` / structure `fields()` | **Yes** — protocol sugar; maps first |
| Full JS/Python dynamism | **No** — maps + opt-in meta only |

This keeps Zen explicit and Unix-tool friendly while giving libraries, debuggers, and plugins a real introspection ladder.
