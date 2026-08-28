# Zen Syntax Pattern (ZSP) Specification

**Status:** Canonical Design Standard  
**Purpose:** Human-readable grammar, syntax design, and RFC specification language for Zenlang.

Traditional formal grammar notations like EBNF are cryptic, symbol-heavy, and difficult to read at a glance. **Zen Syntax Pattern (ZSP)** is a human-first, visual grammar language that models Zen code directly using visual shapes, intuitive slot placeholders, and a 4-stage blueprint format.

---

## 1. Core Notation Rules

| Symbol | Meaning | Example |
|---|---|---|
| `keyword`, `operator` | Written verbatim as in Zenlang | `when`, `function`, `<-`, `->`, `do`, `{ }` |
| `<slot>` | Required placeholder to be filled | `<condition>`, `<expression>`, `<name>` |
| `[ optional ]` | Optional component | `[ or <- <expression> ]`, `[ : <type> ]` |
| `\|` | Alternative choice | `<expression> \| <block>` |
| `...` | Repeatable / chainable construct | `[ or when <condition> <- <expression> ]...` |

---

## 2. Standard Placements Glossary

When authoring ZSP blueprints, use the following standardized placement tags:

| Placement | Description | Examples |
|---|---|---|
| `<keyword>` | Reserved Zenlang keywords | `when`, `function`, `class`, `let`, `set`, `do` |
| `<operator>` | Flow arrows, arithmetic, logic operators | `->`, `<-`, `+`, `==`, `and`, `or`, `not` |
| `<identifier>` | Any valid variable, function, or type name | `x`, `total_count`, `User`, `calculate` |
| `<expression>` | Any valid Zenlang value-producing expression | `1 + 2`, `Str.to_string(x)`, `Point { x -> 1 }` |
| `<condition>` | A Boolean expression evaluating to truthy/falsy | `x > 0`, `is_valid and not is_empty` |
| `<value>` | Any literal, variable, or resolved value | `42`, `"hello"`, `Nothing`, `Default` |
| `<statement>` | A single executable statement | `let x -> 1`, `io.writeln("ok")` |
| `<block>` | Statements enclosed in curly braces | `{ ... }` |
| `<type>` | A type annotation | `Integer`, `String`, `List`, `Map` |
| `<parameter>` | A function/method parameter definition | `name`, `count: Integer` |
| `<pattern>` | A destructuring or matching pattern | `[head, ...tail]`, `{ x, y }`, `Point(x, y)` |

---

## 3. The 4-Stage Zen Blueprint Format

Every syntax feature or proposed RFC is documented in four mandatory stages:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SHAPE      → The visual pattern (Zen-native grammar)     │
│ 2. EXAMPLES   → Real-world idioms & code snippets           │
│ 3. DESUGAR    → AST mapping & equivalence model             │
│ 4. DUAL-PATH  → Rules for Interpreter vs Native (-g)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Reference Blueprints

### Blueprint: Inline Guard & Return (`when ... <-`)

#### 1. Shape
```zen
// Single Guard Exit
when <condition> <- <expression>

// Dual Branch Return
when <condition> <- <expression> or <- <fallback_expression>

// Chained Inline Returns
when <condition> <- <expression> [ or when <condition> <- <expression> ]... or <- <fallback_expression>
```

#### 2. Examples
```zen
// Early exit guard
when not file_exists(path) <- Nothing
when count <= 0 <- Default

// Dual branch return
when is_ready <- get_payload() or <- fetch_remote()

// Chained pure returns
when n == 0 <- 1 or when n == 1 <- 1 or <- fib(n - 1) + fib(n - 2)
```

#### 3. Desugar
```zen
// Input:
when <condition> <- <expression>

// Desugars to:
when <condition> {
    <- <expression>
}
```

#### 4. Dual-Path
- **Interpreter**: Evaluates `<condition>`; if truthy, evaluates `<expression>` and triggers `Return`.
- **Compiler (`-g`)**: Emits `if (ZenValue_is_truthy(cond)) { return expr; }`. Zero overhead.

---

### Blueprint: Expression-Body Functions (`function ... <-`)

#### 1. Shape
```zen
// Untyped Expression Function
function <identifier>( [ <parameter> [ , <parameter> ]... ] ) <- <expression>

// Typed Expression Function
function <identifier>( [ <parameter> [ , <parameter> ]... ] ) : <type> <- <expression>
```

#### 2. Examples
```zen
function square(x) <- x * x
function add(a: Integer, b: Integer) : Integer <- a + b
function full_name(u) <- u.first + ` ` + u.last
```

#### 3. Desugar
```zen
// Input:
function square(x) <- x * x

// Desugars to:
function square(x) {
    <- x * x
}
```

#### 4. Dual-Path
- Function AST receives a single `ReturnStatement` in its block. Identical execution and codegen to standard block functions.

---

### Blueprint: Inline Ternary Expression (`... when ... or ...`)

#### 1. Shape
```zen
<expression_if_true> when <condition> or <expression_if_false>
```

#### 2. Examples
```zen
let label -> `Active` when is_online or `Offline`
let timeout -> 30 when is_slow_net or 5
let config -> load_custom() when exists(`config.zl`) or Default
```

#### 3. Desugar
```zen
// Input:
let x -> a when cond or b

// Desugars to:
let x -> when cond { a } or { b }
```

#### 4. Dual-Path
- Evaluates as a conditional expression yielding the selected value.

---

## 5. Authoring Guide: Writing New ZSP Blueprints

When writing an RFC or language proposal:
1. **Never use BNF/EBNF symbols** (`::=`, `<foo> ::= "bar"`). Use visual code shapes.
2. **Always provide at least 2 real-world examples** demonstrating why the syntax is ergonomic.
3. **Clearly specify the AST desugaring** to prove the construct is unambiguous to parse.
4. **Detail Dual-Path invariants** to ensure parity between interpreter mode and `-g` C transpilation.
