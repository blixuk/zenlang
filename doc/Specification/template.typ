// Zenlang Documentation Design System
// Themes: "antiquarian" (18th/19th c. engraving), "modernist-dark", "bauhaus", "retro-unix", "brutalist"

#let get-theme(name) = {
  if name == "antiquarian" or name == "engraving" or name == "letterpress" or name == "fortran-style" {
    (
      name: "antiquarian",
      canvas: rgb("#cfe3dc"),       // Classic Duck-Egg Pastel Seafoam Paper (Fortran With Style)
      code-bg: rgb("#c2dbd4"),       // Engraved Inset Block
      subtle-bg: rgb("#b5d3cb"),
      text-main: rgb("#0c2420"),     // Deep Verdigris / Copperplate Black Ink
      text-muted: rgb("#1d423b"),
      text-dim: rgb("#3c655e"),
      border: rgb("#163832"),        // Crisp Copperplate Stroke
      primary: rgb("#0c2420"),      // Dark Engraving Primary
      emerald: rgb("#0d3f35"),
      amber: rgb("#784915"),        // Old Bronze Gold
      rose: rgb("#7a1f1f"),         // Antique Vermilion
      purple: rgb("#4c2260"),
      code-text: rgb("#061d19"),
      font-family: ("Liberation Serif", "DejaVu Serif"),
      syntax-theme: "Style/zenlang.tmTheme",
    )
  } else if name == "bauhaus" or name == "modernist-light" {
    (
      name: "bauhaus",
      canvas: rgb("#ffffff"),
      code-bg: rgb("#f6f8fa"),
      subtle-bg: rgb("#f1f5f9"),
      text-main: rgb("#111827"),
      text-muted: rgb("#4b5563"),
      text-dim: rgb("#9ca3af"),
      border: rgb("#e5e7eb"),
      primary: rgb("#1d4ed8"),      // Bauhaus Cobalt
      emerald: rgb("#059669"),      // Forest Green
      amber: rgb("#d97706"),        // Bauhaus Ochre
      rose: rgb("#dc2626"),         // Bauhaus Vermilion
      purple: rgb("#7c3aed"),
      code-text: rgb("#1e40af"),
      font-family: ("Noto Sans", "Liberation Sans", "DejaVu Sans"),
      syntax-theme: "Style/zenlang.tmTheme",
    )
  } else if name == "retro-unix" or name == "bell-labs" {
    (
      name: "retro-unix",
      canvas: rgb("#fbf8f2"),       // Warm Archival Paper
      code-bg: rgb("#f2ece1"),       // Vintage Code Block
      subtle-bg: rgb("#ebe3d5"),
      text-main: rgb("#1c1917"),     // Charcoal Ink
      text-muted: rgb("#57534e"),
      text-dim: rgb("#a8a29e"),
      border: rgb("#d6cfc2"),
      primary: rgb("#881337"),      // Bell Labs Maroon
      emerald: rgb("#14532d"),
      amber: rgb("#b45309"),
      rose: rgb("#991b1b"),
      purple: rgb("#581c87"),
      code-text: rgb("#713f12"),
      font-family: ("Noto Sans", "Liberation Sans", "DejaVu Sans"),
      syntax-theme: "Style/zenlang.tmTheme",
    )
  } else if name == "brutalist" {
    (
      name: "brutalist",
      canvas: rgb("#f4f4f5"),
      code-bg: rgb("#ffffff"),
      subtle-bg: rgb("#e4e4e7"),
      text-main: rgb("#000000"),
      text-muted: rgb("#3f3f46"),
      text-dim: rgb("#71717a"),
      border: rgb("#000000"),
      primary: rgb("#000000"),
      emerald: rgb("#047857"),
      amber: rgb("#b45309"),
      rose: rgb("#b91c1c"),
      purple: rgb("#6d28d9"),
      code-text: rgb("#000000"),
      font-family: ("Noto Sans", "Liberation Sans", "DejaVu Sans"),
      syntax-theme: "Style/zenlang.tmTheme",
    )
  } else {
    // Default: "modernist-dark" (Sleek, uncluttered dark theme)
    (
      name: "modernist-dark",
      canvas: rgb("#0d1117"),
      code-bg: rgb("#161b22"),
      subtle-bg: rgb("#21262d"),
      text-main: rgb("#e6edf3"),
      text-muted: rgb("#8b949e"),
      text-dim: rgb("#6e7681"),
      border: rgb("#30363d"),
      primary: rgb("#38bdf8"),      // Electric Sky
      emerald: rgb("#34d399"),      // Emerald Green
      amber: rgb("#fbbf24"),        // Amber
      rose: rgb("#f87171"),         // Coral Rose
      purple: rgb("#c084fc"),
      code-text: rgb("#7dd3fc"),
      font-family: ("Noto Sans", "Liberation Sans", "DejaVu Sans"),
      syntax-theme: "Style/zenlang.tmTheme",
    )
  }
}

// Global active theme palette
#let active-theme = get-theme("modernist-dark")
#let bg-canvas = active-theme.canvas
#let bg-code = active-theme.code-bg
#let bg-subtle = active-theme.subtle-bg
#let text-main = active-theme.text-main
#let text-muted = active-theme.text-muted
#let text-dim = active-theme.text-dim
#let border-hairline = active-theme.border
#let accent-primary = active-theme.primary
#let accent-cyan = active-theme.primary
#let accent-emerald = active-theme.emerald
#let accent-amber = active-theme.amber
#let accent-rose = active-theme.rose
#let accent-purple = active-theme.purple

#let background = bg-canvas
#let foreground = text-main
#let accent = accent-primary
#let accent-dark = bg-subtle
#let white = rgb("#ffffff")
#let gray = text-muted
#let dark-gray = text-dim
#let blue = accent-primary
#let green = accent-emerald
#let orange = accent-amber
#let pink = rgb("#f472b6")
#let purple = accent-purple
#let red = accent-rose
#let yellow = accent-amber

#let project(theme: "modernist-dark", doc-title: "ZENLANG FORMAL SPECIFICATION", doc) = {
  let th = get-theme(theme)

  set page(
    paper: "a4",
    fill: th.canvas,
    margin: (x: 2.2cm, top: 2.6cm, bottom: 2.6cm),
    header: context {
      let page-num = counter(page).get().first()
      if page-num > 2 [
        #grid(
          columns: (1fr, auto),
          align(left)[
            #text(size: 8pt, fill: th.text-dim, weight: "medium", tracking: 0.06em)[
              #if th.name == "antiquarian" [
                ❧ #doc-title ❧
              ] else [
                #doc-title
              ]
            ]
          ],
          align(right)[
            #text(size: 8pt, fill: th.primary, weight: "bold", tracking: 0.06em)[
              v1.0
            ]
          ]
        )
        #v(0.3em)
        #if th.name == "antiquarian" [
          #line(length: 100%, stroke: 0.75pt + th.border)
          #v(-0.2em)
          #line(length: 100%, stroke: 0.25pt + th.border)
        ] else [
          #line(length: 100%, stroke: 0.5pt + th.border)
        ]
      ]
    },
    footer: context {
      let page-num = counter(page).get().first()
      if page-num > 1 [
        #if th.name == "antiquarian" [
          #line(length: 100%, stroke: 0.25pt + th.border)
          #v(-0.2em)
          #line(length: 100%, stroke: 0.75pt + th.border)
        ] else [
          #line(length: 100%, stroke: 0.5pt + th.border)
        ]
        #v(0.6em)
        #grid(
          columns: (1fr, auto, 1fr),
          align(left)[
            #text(size: 7.5pt, fill: th.text-dim)[
              #if th.name == "antiquarian" [
                _Principles of Good Programming_
              ] else [
                The Zen of Programming Language
              ]
            ]
          ],
          align(center)[
            #text(size: 8.5pt, fill: th.text-muted, weight: "medium")[
              #if th.name == "antiquarian" [
                — #page-num —
              ] else [
                #page-num
              ]
            ]
          ],
          align(right)[
            #text(size: 7.5pt, fill: th.text-dim)[Dual Execution Parity]
          ]
        )
      ]
    }
  )

  set text(
    font: th.font-family,
    size: if th.name == "antiquarian" { 10pt } else { 9.5pt },
    fill: th.text-main,
  )

  set par(
    leading: if th.name == "antiquarian" { 0.85em } else { 0.8em },
    justify: true,
  )

  // Headings — Clean, unboxed typography
  show heading.where(level: 1): it => block(
    above: 2.4em,
    below: 1.2em,
    [
      #if th.name == "antiquarian" [
        #align(center)[
          #text(size: 8.5pt, fill: th.text-muted, weight: "bold", tracking: 0.2em)[
            ❖   C H A P T E R   ❖
          ]
          #v(0.4em)
          #text(size: 19pt, weight: "bold", fill: th.text-main)[#it.body]
          #v(0.6em)
          #text(size: 8pt, fill: th.text-dim)[❦   ⁘   ❧]
        ]
      ] else [
        #text(size: 18pt, weight: "bold", fill: th.text-main)[#it.body]
      ]
    ]
  )

  show heading.where(level: 2): it => block(
    above: 1.8em,
    below: 0.8em,
    text(size: if th.name == "antiquarian" { 13pt } else { 12.5pt }, weight: "bold", fill: th.primary, it.body)
  )

  show heading.where(level: 3): it => block(
    above: 1.3em,
    below: 0.5em,
    text(size: 10pt, weight: "bold", fill: th.text-main, it.body)
  )

  // Lists
  set list(marker: text(fill: th.primary)[#if th.name == "antiquarian" [❖] else [•]], spacing: 0.8em)
  set enum(spacing: 0.8em)

  // Tables
  show table: set table(
    stroke: (x, y) => if y == 0 { (bottom: 1pt + th.primary) } else { (bottom: 0.5pt + th.border) },
    fill: (col, row) => none,
    inset: (x: 8pt, y: 7pt),
  )

  show table.cell.where(y: 0): set text(weight: "bold", fill: th.text-main, size: 9pt)

  // Syntax Highlighting Integration
  show raw.where(lang: "zenlang").or(raw.where(lang: "zl")): set raw(
    syntaxes: "Style/zenlang.sublime-syntax",
    theme: th.syntax-theme,
  )

  // Block Code Styling
  show raw.where(block: true): it => block(
    fill: th.code-bg,
    stroke: if th.name == "antiquarian" { 0.75pt + th.border } else { 0.5pt + th.border },
    inset: (x: 14pt, y: 11pt),
    radius: if th.name == "brutalist" or th.name == "antiquarian" { 0pt } else { 4pt },
    width: 100%,
    breakable: false,
    text(font: ("DejaVu Sans Mono", "Liberation Mono"), fill: th.code-text, size: 8.5pt, it)
  )

  // Inline Code
  show raw.where(block: false): it => text(
    font: ("DejaVu Sans Mono", "Liberation Mono"),
    fill: th.code-text,
    size: 0.9em,
    weight: "medium",
    it
  )

  doc
}

// Minimalist Callouts — Pure typographic left-border quotes
#let note(body) = block(
  stroke: (left: 2pt + accent-primary),
  inset: (left: 12pt, y: 3pt),
  above: 1.4em,
  below: 1.4em,
  breakable: false,
  [
    #text(weight: "bold", fill: accent-primary, size: 8pt, tracking: 0.08em)[
      #if active-theme.name == "antiquarian" [❧ PROVERB] else [NOTE]
    ]
    #v(0.2em)
    #body
  ]
)

#let tip(body) = block(
  stroke: (left: 2pt + accent-emerald),
  inset: (left: 12pt, y: 3pt),
  above: 1.4em,
  below: 1.4em,
  breakable: false,
  [
    #text(weight: "bold", fill: accent-emerald, size: 8pt, tracking: 0.08em)[
      #if active-theme.name == "antiquarian" [❦ MAXIM] else [TIP]
    ]
    #v(0.2em)
    #body
  ]
)

#let warning(body) = block(
  stroke: (left: 2pt + accent-amber),
  inset: (left: 12pt, y: 3pt),
  above: 1.4em,
  below: 1.4em,
  breakable: false,
  [
    #text(weight: "bold", fill: accent-amber, size: 8pt, tracking: 0.08em)[
      #if active-theme.name == "antiquarian" [❖ CAUTION] else [WARNING]
    ]
    #v(0.2em)
    #body
  ]
)

#let important(body) = block(
  stroke: (left: 2pt + accent-rose),
  inset: (left: 12pt, y: 3pt),
  above: 1.4em,
  below: 1.4em,
  breakable: false,
  [
    #text(weight: "bold", fill: accent-rose, size: 8pt, tracking: 0.08em)[
      #if active-theme.name == "antiquarian" [✠ IMPERATIVE] else [IMPORTANT]
    ]
    #v(0.2em)
    #body
  ]
)

// Feature Presentation — Clean unboxed layout
#let feature(title, syntax, example) = {
  block(
    above: 1.4em,
    below: 1.4em,
    breakable: false,
    [
      #text(weight: "bold", fill: text-main, size: 10pt)[#title]
      #v(0.4em)
      #grid(
        columns: (1fr, 1.2fr),
        gutter: 12pt,
        [
          #text(size: 7.5pt, fill: text-dim, weight: "bold", tracking: 0.08em)[SYNTAX]
          #raw(syntax, lang: "zl")
        ],
        [
          #text(size: 7.5pt, fill: text-dim, weight: "bold", tracking: 0.08em)[EXAMPLE]
          #raw(example, lang: "zl")
        ]
      )
    ]
  )
}

#let small_feature(title, description, syntax) = {
  block(
    above: 1.2em,
    below: 1.2em,
    breakable: false,
    [
      #text(weight: "bold", fill: text-main, size: 10pt)[#title]
      #v(0.2em)
      #text(fill: text-muted, size: 9pt)[#description]
      #v(0.4em)
      #raw(syntax, lang: "zl")
    ]
  )
}

#let example_feature(title, example) = {
  block(
    above: 1.2em,
    below: 1.2em,
    breakable: false,
    [
      #text(weight: "bold", fill: text-main, size: 10pt)[#title]
      #v(0.4em)
      #raw(example, lang: "zl")
    ]
  )
}

#let syntax_feature(title, syntax) = {
  block(
    above: 1.2em,
    below: 1.2em,
    breakable: false,
    [
      #text(weight: "bold", fill: text-main, size: 10pt)[#title]
      #v(0.4em)
      #raw(syntax, lang: "zl")
    ]
  )
}

#let big_feature(title, concept, syntax, example) = {
  block(
    above: 1.5em,
    below: 1.5em,
    breakable: false,
    [
      #text(weight: "bold", fill: accent-primary, size: 11pt)[#title]
      #v(0.3em)
      #text(fill: text-muted, size: 9pt)[#concept]
      #v(0.5em)
      #grid(
        columns: (1fr, 1.2fr),
        gutter: 12pt,
        [
          #text(size: 7.5pt, fill: text-dim, weight: "bold", tracking: 0.08em)[SYNTAX]
          #raw(syntax, lang: "zl")
        ],
        [
          #text(size: 7.5pt, fill: text-dim, weight: "bold", tracking: 0.08em)[EXAMPLE]
          #raw(example, lang: "zl")
        ]
      )
    ]
  )
}

#let stroke(item) = {
  block(
    above: 1em,
    below: 1em,
    breakable: false,
    [#item]
  )
}

#let title_code(title, code) = {
  block(
    above: 1.2em,
    below: 1.2em,
    breakable: false,
    [
      #text(weight: "bold", fill: text-main, size: 9.5pt)[#title]
      #v(0.3em)
      #raw(code, lang: "zl")
    ]
  )
}

#let name_code(name, code) = {
  block(
    above: 1em,
    below: 1em,
    breakable: false,
    [
      #text(size: 8.5pt, fill: text-dim, weight: "bold")[#name]
      #v(0.3em)
      #raw(code, lang: "zl")
    ]
  )
}
