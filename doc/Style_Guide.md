# Zenlang Style Guide & Code Standards

| Attribute | Value |
|:---|:---|
| **Role** | Code Formatting & Naming Conventions |
| **Authority** | Definitive Style Reference for Zenlang Code |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Core Aesthetic Principles

Zenlang code should feel **calm, clean, and explicit**. Code is read far more often than it is written.
- Visual arrows (`->`, `<-`, `<~`) should always be surrounded by spaces.
- Sentinels (`Nothing`, `Default`, `True`, `False`) must always be capitalized.
- String literals are strictly delimited by backticks (` `...` `). Double or single quotation marks are not valid syntax.

---

## 2. Naming Conventions

| Category | Convention | Examples |
|:---|:---|:---|
| **Variables** | `snake_case` | `user_id`, `buffer_capacity`, `item_count` |
| **Functions & Tasks** | `snake_case` | `parse_header()`, `calculate_sum()`, `fetch_user()` |
| **Types, Classes & Structs** | `PascalCase` | `Integer`, `HttpClient`, `Vector2`, `Point` |
| **Objects (Blueprints)** | `PascalCase` | `Player`, `HttpRequest` |
| **Objects (Instances)** | `snake_case` | `player`, `request` |
| **Enumerators & Variants** | `PascalCase` | `Direction.North`, `HttpStatus.Ok` |
| **Constants** | `UPPER_CASE` | `MAX_TIMEOUT`, `DEFAULT_PORT`, `BUFFER_SIZE` |
| **Sentinels** | `PascalCase` | `Nothing`, `Default`, `True`, `False` |
| **Private Fields & Methods** | Leading underscore | `_internal_cache`, `_id`, `_reset()` |

---

## 3. Formatting Rules

### 3.1 Indentation & Spacing
- Use **4 spaces** per indentation level (do not use raw tabs).
- Put spaces around all binary operators: `a + b`, `x == 42`, `total -> 10`.
- Put a single space after commas: `[1, 2, 3]`, `{ a, b }`.

### 3.2 Visual Data Flow (`->`, `<-`, `<~`)
- **Assignment (`->`):** Always place spaces before and after:
  ```zl
  let count -> 0
  name -> `Alice`
  ```
- **Return (`<-`):** Always place a space after the return operator:
  ```zl
  function sum(a: Integer, b: Integer) : Integer {
      <- a + b
  }
  ```
- **Yield (`<~`):** Always place a space after the yield operator:
  ```zl
  function stream_items() {
      <~ 1
      <~ 2
  }
  ```

### 3.3 Function Signatures & Arrow Bodies
- Omit empty parameter parentheses on parameterless functions:
  ```zl
  // Preferred:
  function say_hello {
      <- `Hello`
  }
  ```
- Use single-expression arrow bodies for concise helper functions:
  ```zl
  function square(x: Integer) -> x * x
  function greet(name: String) : String -> `Hello, ` + name
  ```

### 3.4 Control Flow & Loops
- Place opening braces on the same line as the statement:
  ```zl
  when is_valid {
      io.info(`Valid`)
  } or {
      io.error(`Invalid`)
  }
  ```
- Place `or` on the closing brace line: `} or when <cond> {` and `} or {`.
- Format `check` cases with uniform alignment:
  ```zl
  check status_code {
      case 200 { io.info(`OK`) },
      case 404 { io.warn(`Not Found`) },
      case 500 { io.error(`Server Error`) }
  } or {
      io.error(`Unknown status`)
  }
  ```

### 3.5 Ranges & Stepped Operators
- Do not put spaces around range operators: `1...5`, `0..-10`, `start..+end`.
- Use stepped `++` and `--` cleanly:
  ```zl
  count++ 5     // Increment by 5
  items++ item  // Append to list
  msg++ `!`     // Append to string
  ```

### 3.6 Error Handling (`?`, `^`, `!`)
- Maintain spacing around error operators:
  ```zl
  let res -> check divide(10, 0) or 0.0
  let res -> ? divide(10, 0) or 0.0
  
  check age >= 0 raise `InvalidAge`
  ? age >= 0 ^ `InvalidAge`

  assert buffer.length > 0
  ! buffer.length > 0
  ```

---

## 4. Automated Formatting with `zenfmt`

Run the native code formatter to automatically format files according to this style guide:

```bash
zen fmt <file.zl>
```

