# Zenlang Terminal File Manager (`zenfm`)

| Attribute | Value |
|:---|:---|
| **Role** | Terminal File Manager Manual |
| **Authority** | Tooling Manual |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Overview

The **Zenlang Terminal File Manager** (`zenfm`) is an interactive, high-performance split-pane terminal file manager and code explorer. It provides instant directory traversal, file size calculations, and real-time syntax-highlighted code previews without requiring external tools.

## 🚀 Quick Start

### 1. Launching the File Manager

Launch the file manager using the `./scripts/zen` CLI:

```bash
# Open file manager in current directory
./scripts/zen fm

# Open file manager in a specific directory
./scripts/zen fm lib/zen/ui/
```

Alternatively, invoke via the bootstrap compiler directly:

```bash
python3 bootstrap/Zen.py tools/zenfm.zl [optional_path]
```

Or compile and run as a native AOT binary:

```bash
python3 bootstrap/Zen.py -g tools/zenfm.zl
```

---

## 🖥️ Interface Architecture

`zenfm` utilizes a dual-pane, terminal-buffered layout with live code preview and path telemetry:

```
┌──────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────┐
│ 📁 ZEN FILE MANAGER — ./lib/zen/ui/                      │                                            [11 items]  │
├──────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 📁 .. (Parent Directory)                                 │   1 │ /!                                               │
│ 📁 widgets/                                              │   2 │     Terminal Data Table Formatter.               │
│ ⚡ app.zl                                                │   3 │ !/                                               │
│ ⚡ canvas.zl                                             │   4 │                                                  │
│ ⚡ chart.zl                                              │   5 │ import zen.text.string as Str                    │
│ ▶ ⚡ table.zl                                            │   6 │ import zen.math.math as Math                     │
│ ⚡ spinner.zl                                            │   7 │                                                  │
│ ⚡ tree.zl                                               │   8 │ function format_table(headers, rows, options) {  │
│ 📝 AGENTS.md                                             │   9 │     let b -> get_border_style(style_name)        │
├──────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────┤
│ Ready                                                    ↑/↓:Nav  Enter:Open  Bksp:Parent  P:Playground  Q:Quit   │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Header Bar (Top)
- **Directory Path**: Displays the active directory path.
- **Item Count**: Displays the total number of entries in the current directory.

### 2. Left Pane (Directory Tree & Navigation)
- **Directory Sorting**: Subdirectories appear first, followed by regular files.
- **Visual File Type Badges**:
  - `📁` Subdirectories
  - `⚡` Zenlang Source Files (`.zl`)
  - `📝` Markdown & Text Documentation (`.md`, `.txt`)
  - `🔧` C & Header Source Files (`.c`, `.h`)
  - `⚙ ` Configuration Files (`.json`, `.yaml`, `.toml`)
  - `📜` Scripts (`.sh`, `.py`)
  - `📄` General Files
- **Selection Highlight**: Selected item highlighted with a high-contrast teal badge.

### 3. Right Pane (Live Code Preview)
- **Syntax Highlighting**: Real-time coloring of keywords (`function`, `let`, `when`), stdlib calls, flow arrows (`->`, `<-`), strings, and comments.
- **Line Numbers**: Gutter with 3-digit line numbering.
- **Directory Summaries**: Displays item counts when a directory is highlighted.

### 4. Footer (Status & Shortcuts)
- **Status Context**: Reports current operations, path changes, and actions.
- **Shortcut Legend**: Quick reference for active keybindings.

---

## ⌨️ Keybindings

| Key | Action | Description |
|-----|--------|-------------|
| <kbd>↑</kbd> / <kbd>k</kbd> | Move Selection Up | Highlights previous file or directory |
| <kbd>↓</kbd> / <kbd>j</kbd> | Move Selection Down | Highlights next file or directory |
| <kbd>PageUp</kbd> | Jump Up 10 Items | Fast scrolling for large directories |
| <kbd>PageDown</kbd> | Jump Down 10 Items | Fast scrolling for large directories |
| <kbd>Enter</kbd> | Open Directory | Drills down into the selected subdirectory |
| <kbd>Backspace</kbd> / <kbd>h</kbd> | Parent Directory | Navigates up to `..` |
| <kbd>P</kbd> | Open in Playground | Launches [Zenlang Playground](Playground.md) on the selected `.zl` file |
| <kbd>Q</kbd> / <kbd>Ctrl+C</kbd> | Quit | Restores cursor and exits cleanly |

---

## ⚡ Performance & Dual-Path Execution

`zenfm` is built with Zenlang's line-buffered terminal engine:
- **Zero Flickering**: Renders entire screen rows atomically via `term.write()`.
- **Sub-millisecond Input**: Instant navigation response even in large folders.
- **Full Parity**: Identical execution in both the interpreter and the native C transpiler (`-g`).
