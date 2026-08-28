// Zenlang Language Specification
// Formal Language Definition & Reference Manual

#import "template.typ": *

#let active-theme-name = sys.inputs.at("theme", default: "antiquarian")
#let th = get-theme(active-theme-name)

#show: project.with(theme: active-theme-name, doc-title: "ZENLANG FORMAL SPECIFICATION")

// ==========================================
// COVER PAGE
// ==========================================

#if th.name == "antiquarian" [
  #align(center + horizon)[
    #block(
      width: 100%,
      height: 96%,
      [
        #place(top + left, image("Style/engraving_frame.jpg", width: 100%, height: 100%, fit: "stretch"))
        #place(center + top, dy: 10.8cm)[
          #block(width: 44%)[
            #align(center)[
              #text(size: 16pt, weight: "bold", fill: th.primary, font: "Liberation Serif")[
                ZENLANG WITH STYLE
              ]
              #v(0.4em)
              #text(size: 8.5pt, weight: "bold", fill: th.primary, font: "Liberation Serif", tracking: 0.16em)[
                F O R M A L   S P E C I F I C A T I O N
              ]
              #v(0.6em)
              #text(size: 7pt, fill: th.text-dim)[❧   ⁘   ❦]
              #v(0.6em)
              #text(size: 8.5pt, weight: "bold", fill: th.primary, font: "Liberation Serif", tracking: 0.08em)[
                ZENLANG ARCHITECTURE GROUP
              ]
              #v(1.0em)
              #text(size: 7.5pt, style: "italic", fill: th.primary, font: "Liberation Serif")[
                Principles of Formal Language Definition, Visual Data Flow, and Dual Execution Architecture
              ]
            ]
          ]
        ]
        #place(center + bottom, dy: -1.8cm)[
          #text(size: 7.5pt, weight: "bold", fill: th.primary, tracking: 0.12em)[
            [ ARCHIVAL SPECIFICATION • AUGUST 2026 ]
          ]
        ]
      ]
    )
  ]
] else [
  #v(3cm)

  #text(size: 8.5pt, weight: "bold", fill: th.primary, tracking: 0.2em)[
    FORMAL SPECIFICATION
  ]

  #v(1.2em)

  #text(size: 34pt, weight: "bold", fill: th.text-main)[
    The Zenlang\
    Specification
  ]

  #v(0.8em)

  #text(size: 12.5pt, weight: "regular", fill: th.text-muted)[
    Language Definition, Visual Data Flow & Dual Execution Architecture
  ]

  #v(2.5em)
  #line(length: 100%, stroke: 1.5pt + th.primary)
  #v(1.5em)

  #text(size: 9.5pt, fill: th.text-muted)[
    Visual Data Flow ($->$ / $<-$)  •  Zero-Latency Terminal UI  •  Dual Execution Parity
  ]

  #v(1fr)

  #line(length: 100%, stroke: 0.5pt + th.border)
  #v(1.2em)

  #grid(
    columns: (1fr, 1fr),
    align(left)[
      #text(size: 8pt, fill: th.text-dim)[
        *Document Edition:* 1.0 Specification Draft\
        *Language Authority:* Reference Bootstrap / Selfhost\
        *Execution Target:* Native C & Bytecode Engine
      ]
    ],
    align(right)[
      #text(size: 8pt, fill: th.text-dim)[
        *Zenlang Architecture Group*\
        August 2026\
        github.com/zenlang/zen
      ]
    ]
  )
]

#pagebreak()

// ==========================================
// TABLE OF CONTENTS
// ==========================================
#outline(title: [Table of Contents], depth: 2, indent: auto)

#pagebreak()

// ==========================================
// SPECIFICATION CHAPTERS
// ==========================================

#include "1_introduction.typ"

#include "2_syntax.typ"

#include "3_types_literals.typ"

#include "4_variables_assignment.typ"

#include "5_operators_logic.typ"

#include "6_control_flow.typ"

#include "7_functions.typ"

#include "8_data_structures.typ"

#include "9_object_oriented_programming.typ"

#include "10_error_handling.typ"

#include "11_organization.typ"

#include "concurrency.typ"

#include "expressions.typ"

#include "keywords.typ"

#include "runtime.typ"
