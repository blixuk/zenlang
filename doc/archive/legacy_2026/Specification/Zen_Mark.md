# Zen Mark (ZM) Specification

**Status:** Canonical Design Standard  
**File Extension:** `.zm`  
**Purpose:** Human-readable technical document, book publishing, and literate programming format for Zenlang, combining Markdown simplicity with Typst/LaTeX layout power.

---

## 1. Overview & Architecture

**Zen Mark (`.zm`)** is built on top of **Zen Data (`.zd`)**. Every Zen Mark document is simultaneously human-readable markup AND a fully programmable Document Object Tree (DOM).

```
┌─────────────────────────────────────────────────────────────┐
│                    ZEN MARK DOCUMENT MODEL                  │
├─────────────────────────────────────────────────────────────┤
│ 1. HEADER     → Entry { ... } (Metadata, Theme & Config)    │
│ 2. DOCUMENT   → Document { layout, padding, content -> [ ] }│
│ 3. BLOCKS     → Heading, Paragraph, Table, CodeBlock, ...   │
│ 4. INLINE     → Span Tuples & 2-Character Doubled Delimiters│
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Document Structure

### A. Frontmatter Header (`Entry`)
The top of any `.zm` file contains optional Zen Data metadata:
```zen
Entry {
    `title` -> `Zenlang Compiler Architecture`,
    `author` -> `Zen Contributors`,
    `date` -> `2026-08-24`,
    `version` -> `1.0.0`,
    `theme` -> `antiquarian`,
    `tags` -> [`compiler`, `bytecode`, `c-aot`],
    `metadata` -> {
        `created` -> `2026-08-24`,
        `updated` -> `2026-08-24`
    }
}
```

### B. Root Document Container (`Document`)
The body of the file contains the root `Document` structure:
```zen
Document {
    // Sequence of Block Elements
    Heading { text -> `Chapter 1: Getting Started`, size -> 1 },
    Paragraph { text -> `Welcome to Zenlang technical documentation.` }
}
```

---

## 3. Block Element Catalog

### 1. `Heading`
```zen
Heading {
    text -> `Chapter Title`,       // Required
    size -> 1,                     // 1 (h1) to 6 (h6)
    align -> `left`,               // `left`, `center`, `right`
    style -> `normal`,             // `normal`, `bold`, `italic`
    padding -> [16, 0, 8, 0]       // [top, right, bottom, left]
}
```

### 2. `Paragraph`
```zen
Paragraph {
    text -> `This is a paragraph with **inline** formatting.`,
    align -> `left`,               // `left`, `center`, `right`, `justify`
    indent -> 0,                   // Indentation level in spaces/tabs
    line_spacing -> 1.2            // Line height multiplier
}
```

### 3. `CodeBlock`
```zen
CodeBlock {
    language -> `zen`,             // Language for syntax highlighting
    theme -> `zen`,                // Color theme
    line_numbers -> True,          // Show line numbers
    evaluate -> False,             // If True, executes code during document build
    code -> ```
        use zen.io
        
        function main() {
            io.writeln(`Hello, ZenMark!`)
            <- 0
        }
    ```
}
```

### 4. `HorizontalRule` / `Divider`
```zen
HorizontalRule {
    type -> `solid`,               // `solid`, `double`, `dotted`, `fleuron`
    thickness -> 1,                // Thickness in pixels/points
    symbol -> `❧`,                 // Optional center fleuron symbol
    padding -> 12                  // Vertical padding
}
```

### 5. `List`
```zen
List {
    type -> `bulleted`,            // `bulleted`, `numbered`, `task`
    prefix -> `1.`,                // Prefix for numbered lists
    marker -> `•`,                 // Marker for bulleted lists
    items -> [
        `Visual directional flow`,
        `Sub-millisecond bytecode VM`,
        `AOT native C compilation`
    ]
}
```

### 6. `Table`
```zen
Table {
    headers -> [`Compiler Stage`, `Mechanism`, `Latency`],
    align -> [`left`, `left`, `right`],
    rows -> [
        [`Lexer`, `Native Token structs`, `1.2ms`],
        [`Parser`, `Recursive descent`, `2.1ms`],
        [`Codegen`, `C transpilation`, `0.4ms`]
    ],
    borders -> `grid`              // `grid`, `clean`, `double`, `none`
}
```

### 7. `Callout` / `Note`
```zen
Callout {
    type -> `tip`,                 // `tip`, `note`, `warning`, `caution`
    title -> `Performance Rule`,
    content -> [
        Paragraph { text -> `Prefer structs over maps for compiler internal IR.` }
    ]
}
```

### 8. `Grid` (Multi-Column Layout)
```zen
Grid {
    columns -> 2,                  // Number of equal or fractional columns
    gap -> 16,                     // Gap between columns
    cells -> [
        Paragraph { text -> `Left column overview text...` },
        Paragraph { text -> `Right column code explanation...` }
    ]
}
```

### 9. `Image` / `Figure`
```zen
Figure {
    source -> `assets/diagram.png`,
    alt -> `Architecture Diagram`,
    caption -> `Figure 1: The Three-Layer Zen Architecture`,
    width -> `80%`,
    align -> `center`
}
```

### 10. `Math`
```zen
Math {
    display -> `block`,            // `block` or `inline`
    equation -> `\text{Luminance} = 0.2126 R + 0.7152 G + 0.0722 B`
}
```

### 11. `Lorem` (Built-in Placeholder Generator)
```zen
Lorem {
    type -> `paragraphs`,          // `words`, `sentences`, `paragraphs`
    count -> 2
}
```

### 12. Layout Spacing
```zen
PageBreak {}
Spacer { height -> 24 }
```

---

## 4. Inline Text & Span System

Zen Mark provides two complementary ways to write formatted text:
1. **Natural Inline Markup:** 2-character doubled delimiters for clean, unambiguous prose.
2. **Structured Span Tuples:** Sequential span arrays for exact programmatic control.

### A. 2-Character Doubled Inline Delimiters

| Delimiter | Span Type | Visual Mnemonic | Render Output |
|---|---|---|---|
| `**text**` | `bold` | Heavy font weight | **Bold text** |
| `^^text^^` | `italic` | Slanted caret | *Italic text* |
| `__text__` | `underline` | Low baseline | <u>Underlined text</u> |
| `~~text~~` | `strike` | Tilde cross-through | ~~Strikethrough~~ |
| `!!text!!` | `keyboard` | Punchy keystroke | `Ctrl` + `Alt` + `Del` |
| `[[text]]` | `monospace` | TeleType brackets | `plain monospace` |
| `{{text}}` | `code` | Expression braces | `let x -> 1` |
| `++text++` | `superscript` | Plus / Up | Baseline shifted up ($x^2$) |
| `--text--` | `subscript` | Minus / Down | Baseline shifted down ($H_2O$) |
| `%%text%%` | `datetime` | Clock / timestamp | `2026-08-24 15:30 UTC` |
| `$$text$$` | `equation` | Formula delimiter | $E = mc^2$ |
| `[text](url)` | `link` | Visual link target | [Link Text](https://zenlang.org) |

---

### B. Structured Span Tuples (Programmatic Form)

Any `Paragraph` or `text` field can be defined sequentially as an array of tagged span tuples:

```zen
Paragraph {
    content -> [
        (raw, `Press `),
        (keyboard, `Ctrl+Shift+P`),
        (raw, ` to open the command palette. In Zen, `),
        (code, `let x -> 1`),
        (raw, ` binds a variable. Formula: `),
        (equation, `x++2++ + y++2++ = z++2++`),
        (newline, 1),
        (link, `https://zenlang.org`, `Official Website`)
    ]
}
```

---

## 5. Renderer Outputs

The Zen Mark compiler renders `.zm` documents to multiple backends without external dependencies:

```
┌─────────────────────────────────────────────────────────────┐
│                    Zen Mark AST (.zm)                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
        [ Terminal ANSI ]   [ Web HTML5 ]   [ Print PDF ]
        `zenmark doc.zm`    `--to html`     `--to pdf`
        • TrueColor escapes • Semantic HTML • Vector fonts
        • Unicode boxes     • Responsive    • Multi-themes
        • ANSI badges       • Dark/Light    • Precision page
```

---

## 6. Complete Sample Document (`getting_started.zm`)

```zen
Entry {
    `title` -> `Zenlang Quickstart Guide`,
    `author` -> `Zenlang Team`,
    `date` -> `2026-08-24`,
    `theme` -> `antiquarian`
}

Document {
    Heading { text -> `Getting Started with Zenlang`, size -> 1, align -> `center` },
    
    HorizontalRule { type -> `fleuron`, symbol -> `❦`, padding -> 8 },
    
    Paragraph {
        text -> `Zenlang is a modern, Unix-native programming language designed around **visual directional data flow**. Code reads cleanly with visual arrows: \`->\` for assignment and \`<-\` for return.`
    },
    
    Callout {
        type -> `tip`,
        title -> `Keyboard Shortcut`,
        content -> [
            Paragraph {
                text -> `Press !!Ctrl+B!! in your editor to build, or run {{zen -g main.zl}} to produce an optimized C binary.`
            }
        ]
    },
    
    Heading { text -> `Code Example`, size -> 2 },
    
    CodeBlock {
        language -> `zen`,
        line_numbers -> True,
        code -> ```
            use zen.io
            use zen.color
            
            function main() {
                let status -> color.paint(`[STATUS: READY]`, color.named(`green`), Nothing)
                io.writeln(status)
                <- 0
            }
        ```
    },
    
    Table {
        headers -> [`Feature`, `Zenlang`, `Traditional C`],
        rows -> [
            [`Assignment`, `let x -> 10`, `int x = 10;`],
            [`Return`, `<- result`, `return result;`],
            [`Branching`, `when cond { ... }`, `if (cond) { ... }`]
        ]
    }
}
```

---

## 7. Standardized Document Archetypes & Themes

Zen Mark provides standardized **Document Archetypes** (layout templates) and **Design Themes** (color and typographic palettes) so all technical documents have a consistent, stunning visual identity.

### A. Document Archetypes

| Archetype | Badge / Purpose | Key Visual Features |
|---|---|---|
| `specification` | `CANONICAL SPECIFICATION` | Hierarchical numbered sections, formal blueprint boxes, wide technical layout. |
| `tutorial` | `TUTORIAL & LEARNER LADDER` | Step cards, goal checklists, prominent keycap badges, live code output. |
| `release_notes` | `RELEASE CHANGELOG` | Release banner, categorized pill badges (`[Added]`, `[Changed]`, `[Fixed]`, `[Breaking]`). |
| `manual` | `API & STDLIB MANUAL` | 2-column signature cards, parameter/return tables, copyable snippets. |
| `cheatsheet` | `QUICK REFERENCE` | 2/3 column high-density grid layout, operator and shortcut lookup tables. |
| `book` | `ZEN MONOGRAPH` | Book margins, chapter fleuron ornaments (`❧`, `❦`), running headers/footers. |

### B. Design Themes

| Theme | Background | Primary Ink | Accent / Glow | Typography |
|---|---|---|---|---|
| `antiquarian` | Warm Cream `#f6f4ee` | Deep Pine `#0e221f` | Copper Gold `#c27803` | Georgia / Serif body, Courier mono |
| `modernist_dark` | Slate Charcoal `#0f172a` | Clean White `#f8fafc` | Sky Cyan `#38bdf8` | Modern system sans, Fira Code mono |
| `clean_light` | Pure White `#ffffff` | Slate Ink `#1e293b` | Indigo `#4f46e5` | Clean sans-serif, DejaVu mono |
| `retro_terminal` | Pitch Black `#0a0a0a` | Amber CRT `#ffb000` | Emerald `#00ff66` | 100% Monospace TeleType vibe |
