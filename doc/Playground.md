# Zenlang Terminal Playground & Code Lab

| Attribute | Value |
|:---|:---|
| **Role** | Interactive Terminal Playground Guide |
| **Authority** | Tooling Manual |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Overview

The **Zenlang Terminal Playground** is an interactive, split-pane terminal development environment and live code laboratory. It allows developers to write, experiment with, and execute Zenlang code in real-time with zero external IDE dependencies.

## 🚀 Quick Start

### 1. Launching the Playground

Launch the playground directly using the `./scripts/zen` CLI tool:

```bash
# Open an empty playground with starter boilerplate
./scripts/zen playground

# Open an existing Zenlang script
./scripts/zen playground examples/getting_started/01_hello_world.zl
```

Alternatively, invoke via the bootstrap compiler directly:

```bash
python3 bootstrap/Zen.py tools/playground.zl [optional_script.zl]
```

---

## 🖥️ Interface Architecture

The playground features a high-density, terminal-native dual-pane layout with a live documentation drawer and floating autocomplete popup:

```
┌───────────────────────────────────────┬─────────────────────────────────────────┐
│ ZEN PLAYGROUND — [untitled.zl]*       │ Engine: Interpret (Python)              │
├───────────────────────────────────────┼─────────────────────────────────────────┤
│   1 │ import zen.ui.chart as chart    │ Live Telemetry:  ▂▃▅▆▇█                 │
│   2 │                                 │ CPU Load [████████████████████░░░░] 78% │
│   3 │ function main() {               │ RAM Usage [██████████████░░░░░░░░░░] 54%│
│   4 │     let s -> chart.sp█          │                                         │
│     │   ┌─────────────────────────┐   │                                         │
│     │   │ ▶ chart.sparkline       │   │                                         │
│     │   │   chart.bar_chart_h     │   │                                         │
│     │   └─────────────────────────┘   │                                         │
├───────────────────────────────────────┴─────────────────────────────────────────┤
│ 📖 DOC INSPECTOR: chart.sparkline                                               │
│   ▶ chart.sparkline(data: List[Number]) -> String — Generates UTF-8 sparkline   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Ln 4, Col 23 | ^R Run  ^P Templates  ^H Doc  ^O Options  ^E Backend  ^Q Quit    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Editor Pane (Left / Top)
- **Full Text Editing**: Insert, delete, split, and join lines.
- **Line Number Gutter**: Dynamic width line numbers with yellow highlight tracking the active cursor line.
- **Real-Time Syntax Highlighting**:
  - **Keywords** (`function`, `let`, `when`, `or`, `do`, `while`, `class`, `check`, `defer`, `Nothing`, `Default`, `true`, `false`) in **Bright Magenta**.
  - **Flow Operators** (`->`, `<-`) in **Bright Green**.
  - **String Literals** (`"..."` and `` `...` ``) in **Green**.
  - **Numeric Literals** in **Bright Yellow**.
  - **Standard Library Modules** (`io`, `term`, `chart`, `tree`, `fuzzy`, `jwt`, `schema`, `bench`, etc.) in **Bright Cyan**.
  - **Comments** (`// ...`) in **Dim Grey**.

### 2. Output Pane (Right / Bottom)
- **Execution Stream**: Captures complete `stdout` and `stderr` streams.
- **Status Coloring**: Highlights `[INFO]` and `OK` lines in green, and `[ERROR]` and `FAIL` in red.
- **Scroll Buffer**: Supports vertical scrolling for long program outputs.

### 3. Live Documentation Drawer (<kbd>Ctrl</kbd> + <kbd>H</kbd>)
- **Context-Aware Reference**: As the cursor moves across keywords (`when`, `let`, `function`, `->`, `<-`, `check`) or standard library calls (`chart.sparkline`, `jwt.sign`, `fuzzy.filter`, `io.writeln`), the doc drawer automatically displays the signature, parameter description, and code usage.
- **Toggleable**: Press <kbd>Ctrl</kbd> + <kbd>H</kbd> to toggle the drawer on or off.

### 4. IDE Autocomplete Engine (<kbd>Tab</kbd>)
- **Contextual Suggestions**: Type any token prefix (e.g. `ch`, `fu`, `io.`, `jwt.`) and a floating popup appears with matching candidates.
- **Quick Completion**: Navigate suggestions using <kbd>Up</kbd> / <kbd>Down</kbd> and hit <kbd>Tab</kbd> or <kbd>Enter</kbd> to insert.
- **Dismiss**: Press <kbd>Esc</kbd> to dismiss the autocomplete popup.

### 5. Settings & Options Modal (<kbd>Ctrl</kbd> + <kbd>O</kbd>)
- Press <kbd>Ctrl</kbd> + <kbd>O</kbd> to configure live editor behavior on the fly:
  - **Auto-Complete Engine**: `[ON / OFF]`
  - **Live Doc Drawer**: `[ON / OFF]`
  - **Syntax Highlighting**: `[ON / OFF]`
  - **Line Numbers Gutter**: `[ON / OFF]`

---

## ⌨️ Keyboard Shortcuts Reference

| Shortcut | Action | Description |
|---|---|---|
| <kbd>Ctrl</kbd> + <kbd>R</kbd> | **Run Code** | Executes the active editor buffer and displays output in the preview pane |
| <kbd>Tab</kbd> | **Autocomplete / Indent** | Inserts autocomplete match if active, or indents 4 spaces |
| <kbd>Ctrl</kbd> + <kbd>H</kbd> | **Toggle Live Docs** | Toggles the contextual documentation inspector drawer |
| <kbd>Ctrl</kbd> + <kbd>O</kbd> | **Options & Settings** | Opens modal to toggle Autocomplete, Doc Drawer, Highlighting, Line Numbers |
| <kbd>Ctrl</kbd> + <kbd>P</kbd> | **Template Gallery** | Opens the interactive overlay modal to browse and load example templates |
| <kbd>Ctrl</kbd> + <kbd>E</kbd> | **Toggle Engine** | Cycles through execution engines (Interpreter, Native AOT `-g`, Self-host) |
| <kbd>Ctrl</kbd> + <kbd>T</kbd> | **Toggle Layout** | Toggles between side-by-side vertical split and stacked horizontal split |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | **Save File** | Saves current buffer to active file (or `playground_saved.zl`) |
| <kbd>Ctrl</kbd> + <kbd>K</kbd> | **Clear Output** | Clears the output preview pane |
| <kbd>Ctrl</kbd> + <kbd>L</kbd> | **Redraw** | Forces a complete terminal redraw |
| <kbd>Ctrl</kbd> + <kbd>Q</kbd> | **Quit** | Cleanly exits the playground and restores terminal state |
| <kbd>Arrows</kbd> / <kbd>Home</kbd> / <kbd>End</kbd> | **Navigate** | Move cursor within the editor |
| <kbd>PgUp</kbd> / <kbd>PgDn</kbd> | **Scroll** | Scroll editor buffer up or down by half a page |
| <kbd>Enter</kbd> | **Split Line / Select** | Accepts highlighted autocomplete / template item, or creates a new line |
| <kbd>Backspace</kbd> / <kbd>Del</kbd> | **Delete** | Deletes characters or merges adjacent lines |

---

## ⚙️ Multi-Backend Execution Engines (<kbd>Ctrl</kbd> + <kbd>E</kbd>)

The playground supports Zenlang's dual-execution model out of the box. Press <kbd>Ctrl</kbd> + <kbd>E</kbd> to cycle between:

1. **`Interpret (Python)`**: Runs via the authoritative Python bootstrap interpreter (`python3 bootstrap/Zen.py`). Best for rapid scripting and immediate feedback.
2. **`Native AOT (-g)`**: Transpiles Zenlang directly into C code, compiles via GCC with the shared C runtime, and executes the native binary. Ideal for testing native performance and C interoperability.
3. **`Selfhost (bin/zen)`**: Routes execution through the self-hosted Zenlang compiler driver (`./bin/zen`).

---

## 📚 Standard Library Template Gallery (<kbd>Ctrl</kbd> + <kbd>P</kbd>)

Press <kbd>Ctrl</kbd> + <kbd>P</kbd> anywhere in the playground to bring up the **Template Gallery** overlay. Use <kbd>Up</kbd> / <kbd>Down</kbd> to select and <kbd>Enter</kbd> to load:

```
┌────────────────────────────────────────────────────────┐
│ ── TEMPLATE GALLERY (Enter: load, Esc: cancel) ──      │
│   ▶ 1. Hello World & Visual Data Flow                  │
│     2. Terminal UI: Charts & Visual Tree               │
│     3. Text Algorithms: Fuzzy Search & Inflect         │
│     4. Advanced Collections & Statistics               │
│     5. Crypto & Security: SHA256 & JWT                 │
│     6. Data Schema Validation                          │
│     7. Micro-Benchmarking Harness                      │
└────────────────────────────────────────────────────────┘
```

### Pre-Bundled Template Examples:

- **1. Hello World & Data Flow**: Explains Zenlang's core `->` (assignment) and `<-` (return) data flow model.
- **2. Terminal UI (`zen.ui.chart`, `zen.ui.tree`)**: Generates UTF-8 sparklines, horizontal bar charts, and ASCII/Unicode directory tree hierarchies.
- **3. Text Algorithms (`zen.text.fuzzy`, `zen.text.inflect`)**: Demonstrates Levenshtein distance matching, scoring, and string case inflections (`camel_case`, `slugify`, `pluralize`).
- **4. Collections & Statistics (`zen.collections.lru`, `zen.math.stats`)**: Demonstrates $O(1)$ LRU cache eviction and summary statistics calculation (`mean`, `median`, `stdev`, `percentile`).
- **5. Crypto & Security (`zen.crypto.hash`, `zen.crypto.jwt`)**: Generates SHA-256 standard digests and signs/verifies HS256 JSON Web Tokens.
- **6. Data Schema Validation (`zen.data.schema`)**: Validates complex nested maps against declarative validation schemas (types, required keys, min/max limits).
- **7. Micro-Benchmarking (`zen.util.bench`)**: Runs micro-benchmarks with high-precision timing, latency calculation, and ops/sec throughput reporting.

---

## 💡 Productivity Tips

1. **Learning Syntax with Live Docs**: Move the cursor over any keyword (`let`, `when`, `check`, `defer`, `->`, `<-`) or function call (`jwt.sign`, `chart.sparkline`) to instantly view the documentation drawer.
2. **Fast Autocompletion**: Type `ch` and press <kbd>Tab</kbd> to immediately complete `chart.sparkline`.
3. **Customizing Display**: Press <kbd>Ctrl</kbd> + <kbd>O</kbd> to adjust features to your preference (e.g. disabling line numbers or autocomplete if working in minimal terminal sizes).
4. **Side-by-Side vs Stacked**: For wide monitors, use **Vertical Split** (<kbd>Ctrl</kbd> + <kbd>T</kbd>) for side-by-side coding and preview. On narrow terminals, switch to **Horizontal Split** to maximize line length.
5. **Testing Native Parity**: Press <kbd>Ctrl</kbd> + <kbd>R</kbd> in `Interpret` mode, then press <kbd>Ctrl</kbd> + <kbd>E</kbd> and <kbd>Ctrl</kbd> + <kbd>R</kbd> to verify identical output under `Native AOT (-g)`!
