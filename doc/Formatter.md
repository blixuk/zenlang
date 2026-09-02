# Zenlang Code Formatter (`zenfmt`)

| Attribute | Value |
|:---|:---|
| **Role** | Code Formatter Manual |
| **Authority** | Tooling Manual |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Overview

The **Zenlang Code Formatter** (`zenfmt`) is an opinionated, automated code formatting tool for Zenlang source files (`.zl`). It standardizes indentation, enforces consistent spacing around data flow operators, and maintains clean whitespace formatting across codebases.

## 🚀 Quick Start

### 1. Formatting to Standard Output

Format a file and print the formatted code to `stdout` without modifying the original file:

```bash
./scripts/zen fmt src/main.zl
```

### 2. Formatting Files In-Place (`-w` / `--write`)

Format one or more `.zl` source files directly on disk:

```bash
# Format a single file
./scripts/zen fmt -w src/main.zl

# Format multiple files
./scripts/zen fmt -w lib/zen/ui/table.zl lib/zen/ui/spinner.zl
```

### 3. CI Verification Mode (`--check`)

Check whether source files conform to the canonical format. Exits with code `0` if all files are formatted, or `1` if unformatted files are found (printing their paths):

```bash
./scripts/zen fmt --check tests/hello.zl
```

---

## 📐 Formatting Rules & Style Conventions

`zenfmt` enforces the official Zenlang style conventions:

### 1. Indentation
- **4 Spaces**: Uses 4 spaces per nesting level (tabs are converted to spaces).
- **Block Alignment**: Braces `{` and `}` dictate scope indentation for `function`, `when`, `or`, `do while`, `class`, and structure literals.

### 2. Data Flow Operators (`->` and `<-`)
- **Assignment Arrow (`->`)**: Enforces single spaces before and after `->`:
  ```zenlang
  // Formatted:
  let count -> 10
  let name -> `Zen`
  ```
- **Return Arrow (`<-`)**: Enforces single spaces after `<-`:
  ```zenlang
  // Formatted:
  function get_version() {
      <- `1.0.0`
  }
  ```

### 3. Binary & Comparison Operators
- Operators (`==`, `!=`, `<`, `>`, `<=`, `>=`, `+`, `-`, `*`, `/`, `and`, `or`) are formatted with single spaces on each side.

### 4. Whitespace & Blank Lines
- **Trailing Whitespace**: Strips all trailing spaces and tabs from line ends.
- **Consecutive Blank Lines**: Collapses multiple consecutive empty lines into a single blank line inside function bodies.
- **File Termination**: Ensures every file ends with exactly one newline (`\n`).

### 5. Comments & Documentation Preservation
- **Single-line Comments (`// ...`)**: Preserves indentation level while leaving comment text intact.
- **Doc Comments (`/! ... !/`)**: Preserves multi-line docblocks and `@param` / `@return` / `@example` tags.

---

## 🛠️ CI & Pre-Commit Integration

### GitHub Actions / CI Pipeline

Add a formatting check step to your CI workflow:

```yaml
- name: Check Zenlang Code Formatting
  run: |
    ./scripts/zen fmt --check lib/zen/**/*.zl
```

### Git Pre-Commit Hook

Automatically format modified Zenlang files before committing:

```bash
#!/bin/sh
# .git/hooks/pre-commit
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.zl$'); do
    ./scripts/zen fmt -w "$file"
    git add "$file"
done
```
