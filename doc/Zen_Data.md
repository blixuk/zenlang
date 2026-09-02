# Zen Data (.zd) Specification & Format Guide

| Attribute | Value |
|:---|:---|
| **Role** | Declarative Data Format Specification |
| **Authority** | Canonical Reference for the `.zd` Data Language |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Executive Summary

**Zen Data (`.zd`)** is Zenlang's native, human-readable data serialization format. It replaces JSON and YAML within the Zen ecosystem by providing direct, 1:1 fidelity with Zenlang's runtime value types—including typed structures, fluid objects, collections, and capitalization-strict sentinels (`Nothing` and `Default`).

```
┌──────────────────────────────────────┐
│            Zen Data (.zd)            │
│  - Strict backtick strings: `hello`  │
│  - Visual pair mapping: `key` -> val │
│  - Typed structures: Vector2{ ... }  │
│  - Sentinels: Nothing, Default       │
└──────────────────┬───────────────────┘
                   │
    zd.parse()     │     zd.stringify()
    (Deserialise)  │     (Serialise)
                   ▼
┌──────────────────────────────────────┐
│         Runtime Value Model          │
│   (Structures, Objects, Maps, Lists) │
└──────────────────────────────────────┘
```

---

## 2. Syntax & Data Primitives

### 2.1 Scalar Values

```zd
// Integers (with base prefixes and digit separators)
decimal_int   -> 42
hex_int       -> 0x7B
binary_int    -> 0b0111_1011
large_int     -> 1_000_000

// Floating-point Decimals
float_val     -> 3.14159
scientific    -> 1.25e-4

// Booleans & Sentinels (Must be capitalized)
is_active     -> True
is_disabled   -> False
absent_data   -> Nothing
zero_state    -> Default

// Strings (Strictly enclosed in backticks)
simple_text   -> `Hello, Zen Data!`
multiline_msg -> ```
Line 1: Clean, human-friendly text
Line 2: Preserves indentation and breaks
```
```

---

## 3. Collections & Compounds

### 3.1 Lists (`[ ... ]`)
Ordered sequences of homogeneous or heterogeneous values:

```zd
fruits -> [
    `apple`,
    `banana`,
    `cherry`
]

matrix -> [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
]
```

### 3.2 Maps (`{ ... }`)
Associative dictionaries using the visual mapping arrow (`->`):

```zd
server_config -> {
    `host` -> `127.0.0.1`,
    `port` -> 8080,
    `ssl`  -> True,
    `workers` -> 4
}
```

### 3.3 Typed Structures (`Type{ ... }`)
Zen Data supports direct deserialization into nominal structures:

```zd
player_spawn -> Point{
    x -> 100,
    y -> 250
}

window_bounds -> Rect{
    x -> 0,
    y -> 0,
    width -> 1920,
    height -> 1080
}
```

---

## 4. Comments in Zen Data
Unlike JSON, Zen Data fully supports comments for configuration and schema annotations:

```zd
// Single-line comment: Service metadata
service_name -> `auth-gateway`

/*
   Multi-line comment:
   Database connection pool parameters
*/
database -> {
    `url` -> `postgres://localhost:5432/app`,
    `max_pool` -> 16
}
```

---

## 5. Zenlang Standard Library API (`zen.data.zendata`)

The standard library module `zen.data.zendata` provides high-throughput serialization and parsing:

```zl
use zen.data.zendata as zd
use zen.io.file as file
use zen.io

function main() {
    // 1. Reading and parsing a .zd file:
    let raw_text -> file.read_all(`config.zd`)
    let config   -> zd.parse(raw_text)

    io.info(`Loaded host: ` + config[`server_config`][`host`])

    // 2. Serializing a runtime object or map:
    let payload -> {
        `timestamp` -> 1725300000,
        `status`    -> `Ready`,
        `retries`   -> 3
    }
    
    let zd_output -> zd.stringify(payload)
    file.write(`output.zd`, zd_output)
    <- 0
}
```

---

## 6. Comparison with Other Formats

| Feature | JSON | YAML | Zen Data (`.zd`) |
|:---|:---|:---|:---|
| **String Delimiters** | Double quotes (`"..."`) | Optional quotes | **Backticks strictly** (`` `...` ``) |
| **Key-Value Mapping** | Colon (`:`) | Colon (`:`) | **Visual arrow** (`->`) |
| **Comments Support** | No | Yes | **Yes** (`//` and `/* */`) |
| **Typed Structs** | No (Untyped) | No (Tag tags `!tag`) | **Yes** (`Type{ ... }`) |
| **Sentinels Support** | `null` only | `null` / `~` | **`Nothing` & `Default`** |
| **Whitespace Semantic**| Free | Significant (Indentation) | **Free (Braced scopes)** |
