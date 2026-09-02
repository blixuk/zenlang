# Zen Mark (.zm) Specification & Terminal UI Guide

| Attribute | Value |
|:---|:---|
| **Role** | Document Markup & Terminal UI Format Specification |
| **Authority** | Canonical Reference for the `.zm` Markup Language |
| **Specification Reference** | [doc/SPECIFICATION.md](SPECIFICATION.md) |
| **Documentation Standards** | [doc/DOCUMENTATION_STANDARDS.md](DOCUMENTATION_STANDARDS.md) |

---

## 1. Executive Summary

**Zen Mark (`.zm`)** is Zenlang's native document and terminal layout markup language. It bridges the gap between readable Markdown documentation and high-performance interactive terminal user interfaces (TUIs), providing direct support for ANSI colors, grid boxes, status bars, and formatted typography.

```
┌──────────────────────────────────────┐
│            Zen Mark (.zm)            │
│  - Typography: # Headings, *bold*    │
│  - ANSI Palette: [green: text]       │
│  - TUI Canvas: [box: 80x24]          │
│  - Code blocks: ```zl ... ```        │
└──────────────────┬───────────────────┘
                   │
   zenmark.render_term() / zen doc
                   ▼
┌──────────────────────────────────────┐
│          Terminal / HTML DOM         │
│   (ANSI VT100 escapes or HTML page)  │
└──────────────────────────────────────┘
```

---

## 2. Syntax & Formatting

### 2.1 Headings & Sectioning
```zm
# Document Title (H1)
## Major Section (H2)
### Subsection (H3)
```

### 2.2 Inline Typography & Text Spans
- **Bold:** `*bold text*`
- **Italic:** `_italic text_`
- **Code:** `` `inline_identifier` ``
- **Strikethrough:** `~struck text~`

### 2.3 Color & Style Annotations
Zen Mark allows direct inline ANSI color styling using bracket tags:

```zm
Normal text with [green: success status] and [red: error message].
[bold: [yellow: Warning]]: Resource usage exceeded [cyan: 85%].
```

---

## 3. Terminal UI Blocks & Layouts

Zen Mark supports structured TUI components that render directly to terminal canvases:

```zm
[box: title="System Status", style="rounded", width=60]
CPU Load:  [green: 14%]
RAM Usage: [yellow: 62%]
Network:   [cyan: 1.2 MB/s]
[/box]
```

### 3.1 Code Blocks
```zm
```zl
use zen.io

function main() {
    io.writeln(`Executed via Zen Mark!`)
}
```
```

---

## 4. Standard Library Integration (`zen.ui.zenmark`)

The standard library module `zen.ui.zenmark` parses `.zm` documents and renders them to either ANSI terminal streams or HTML documents:

```zl
use zen.ui.zenmark as zm
use zen.io.file as file
use zen.io

function main() {
    let markup -> file.read_all(`manual.zm`)
    
    // 1. Render to terminal with rich ANSI escapes:
    let term_output -> zm.render_term(markup)
    io.write(term_output)

    // 2. Render to HTML document:
    let html_output -> zm.render_html(markup)
    file.write(`manual.html`, html_output)
    <- 0
}
```
