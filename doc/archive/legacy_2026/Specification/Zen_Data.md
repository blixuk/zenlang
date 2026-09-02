# Zen Data (ZD) Specification

**Status:** Canonical Design Standard  
**File Extension:** `.zd` / `.zen`  
**Purpose:** Universal declarative data serialization format for Zenlang configurations, state, lockfiles, AST/token dumps, and structured interchange.

---

## 1. Overview & Philosophy

Traditional data formats come with severe trade-offs:
- **JSON:** Lacks comments, trailing commas, raw strings, and typed objects; requires fragile backslash escaping.
- **YAML:** Indentation-sensitive, security vulnerabilities via complex tags, slow parsing.
- **TOML:** Unwieldy for deeply nested data structures and heterogeneous arrays.

**Zen Data (`.zd`)** is a pure, human-friendly data format based on Zenlang's literal syntax. It provides the visual elegance of Zen literals with typed struct nodes, comments, and zero parsing ambiguity.

```
┌─────────────────────────────────────────────────────────────┐
│                       ZEN DATA (.zd)                        │
├──────────────────────────────┬──────────────────────────────┤
│ CAN DO                       │ CANNOT DO (Strict Boundary)  │
├──────────────────────────────┼──────────────────────────────┤
│ • Primitives (Int, Hex, Str) │ • No functions or execution  │
│ • Flow maps: { `k` -> v }    │ • No loops or conditionals   │
│ • Typed structs: Point { }   │ • No arithmetic expressions  │
│ • Single & block comments    │ • No side effects / I/O      │
│ • Capitalized sentinels      │ • No mutable re-assignments  │
│ • Trailing commas allowed    │ • Purely static declarative  │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 2. Syntax & Data Types

### A. Sentinels & Booleans
Zen Data uses capitalized sentinels identical to Zenlang code:
```zen
Nothing     // Deliberate absence of value
Default     // Type zero-state
True        // Boolean true
False       // Boolean false
```

### B. Numbers
Supports integers, floating-point decimals, hexadecimal, and binary literals:
```zen
42          // Integer
3.14159     // Decimal
0xff00ea    // Hexadecimal
0b10110010  // Binary
-15         // Negative numbers
```

### C. Strings
Zen Data supports two string forms:
1. **Backtick Strings (Recommended):** Raw and multiline strings without escape slash hell.
2. **Double-Quoted Strings:** Standard string literals with escape sequences (`\n`, `\t`, `\"`).

```zen
// Raw multiline string (preserves exact newlines without escaping)
`C:\Users\Zen\project\build`

// Standard string
"Line 1\nLine 2\t\"quoted\""
```

### D. Lists
Homogeneous or heterogeneous ordered sequences. Trailing commas are fully permitted:
```zen
[
    `alpha`,
    `beta`,
    `gamma`,
]
```

### E. Maps
Key-value mappings using Zen's visual flow arrow `->` (and `:` for legacy JSON compatibility):
```zen
{
    `host` -> `127.0.0.1`,
    `port` -> 8080,
    `ssl` -> True,
    `timeout_sec` -> 30,
}
```

### F. Typed Struct Nodes (Tagged Objects)
Zen Data preserves object types directly in the serialized representation:
```zen
// Named struct node
Color { `r` -> 56, `g` -> 189, `b` -> 248, `a` -> 255 }

// Nested structure hierarchy
WindowConfig {
    `title` -> `Zen Studio`,
    `size` -> Dimension { `width` -> 1280, `height` -> 720 },
    `theme` -> `antiquarian`,
    `active` -> True
}
```

### G. Comments
Zen Data fully supports both single-line and multiline comments:
```zen
// Single line comment explaining the configuration below

/!
   Multi-line block comment
   for extended documentation.
!/
```

---

## 3. Reference Examples

### Example 1: Project Build Manifest (`zen.build` / `project.zd`)
```zen
Project {
    `name` -> `zen-editor`,
    `version` -> `1.0.0`,
    `author` -> `Zenlang Maintainers`,
    `license` -> `MIT`,
    `dependencies` -> {
        `zen.ui` -> `^0.8.0`,
        `zen.color` -> `^1.0.0`,
        `zen.data` -> `^1.0.0`
    },
    `targets` -> [
        Target {
            `name` -> `zedit`,
            `entry` -> `src/main.zl`,
            `output` -> `bin/zedit`,
            `optimize` -> 2
        }
    ]
}
```

### Example 2: Compiler AST Dump (`dump.zd`)
```zen
FunctionStatement {
    `name` -> `add`,
    `params` -> [
        Parameter { `name` -> `a`, `type` -> `Integer` },
        Parameter { `name` -> `b`, `type` -> `Integer` }
    ],
    `return_type` -> `Integer`,
    `body` -> ReturnStatement {
        `value` -> BinaryOp {
            `op` -> `+`,
            `left` -> Identifier { `name` -> `a` },
            `right` -> Identifier { `name` -> `b` }
        }
    }
}
```

### Example 3: Runtime Theme Definition (`theme.zd`)
```zen
Theme {
    `name` -> `antiquarian`,
    `palette` -> {
        `background` -> Color { `r` -> 246, `g` -> 244, `b` -> 238 },
        `foreground` -> Color { `r` -> 14, `g` -> 34, `b` -> 31 },
        `accent` -> Color { `r` -> 20, `g` -> 82, `b` -> 74 },
        `border` -> Color { `r` -> 194, `g` -> 188, `b` -> 176 }
    },
    `rules` -> {
        `double_borders` -> True,
        `font_serif` -> `Liberation Serif`,
        `font_mono` -> `DejaVu Sans Mono`
    }
}
```

---

## 4. Parser & Tooling Invariants

1. **Deterministic Parsing:** A Zen Data document parses into pure `ZenValue` trees (`Map`, `List`, primitives, and `Structure` instances).
2. **Lossless Round-Trip:** Serializing a `ZenValue` to `.zd` and parsing it back produces an identical value tree.
3. **Safe Parsing:** Because Zen Data contains no executable instructions, parsing `.zd` files has zero vulnerability to arbitrary code execution.
