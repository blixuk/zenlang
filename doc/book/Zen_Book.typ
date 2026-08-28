// The Zen of Programming: A Practical Guide to Zenlang
// Master Typst Document — Clean Modernist & Antiquarian Architecture

#import "../Specification/template.typ": *

#let active-theme-name = sys.inputs.at("theme", default: "antiquarian")
#let th = get-theme(active-theme-name)

#show: project.with(theme: active-theme-name, doc-title: "THE ZEN OF PROGRAMMING")

// ==========================================
// BOOK COVER PAGE
// ==========================================

#if th.name == "antiquarian" [
  #align(center + horizon)[
    #block(
      width: 100%,
      height: 96%,
      [
        #place(top + left, image("engraving_frame.jpg", width: 100%, height: 100%, fit: "stretch"))
        #place(center + top, dy: 10.8cm)[
          #block(width: 44%)[
            #align(center)[
              #text(size: 16pt, weight: "bold", fill: th.primary, font: "Liberation Serif")[
                ZENLANG WITH STYLE
              ]
              #v(0.4em)
              #text(size: 8.5pt, weight: "bold", fill: th.primary, font: "Liberation Serif", tracking: 0.16em)[
                PROGRAMMING PROVERBS
              ]
              #v(0.6em)
              #text(size: 7pt, fill: th.text-dim)[❧   ⁘   ❦]
              #v(0.6em)
              #text(size: 8.5pt, weight: "bold", fill: th.primary, font: "Liberation Serif", tracking: 0.08em)[
                THE ZENLANG AUTHORS
              ]
              #v(1.0em)
              #text(size: 7.5pt, style: "italic", fill: th.primary, font: "Liberation Serif")[
                Principles of Good Programming with Numerous Examples to Improve Style and Proficiency
              ]
            ]
          ]
        ]
        #place(center + bottom, dy: -1.8cm)[
          #text(size: 7.5pt, weight: "bold", fill: th.primary, tracking: 0.12em)[
            [ HAYDEN / ZEN PRESS • FIRST EDITION ]
          ]
        ]
      ]
    )
  ]
] else [
  #v(3cm)

  #text(size: 8.5pt, weight: "bold", fill: th.primary, tracking: 0.2em)[
    THE OFFICIAL LANGUAGE GUIDE
  ]

  #v(1.2em)

  #text(size: 34pt, weight: "bold", fill: th.text-main)[
    The Zen of\
    Programming
  ]

  #v(0.8em)

  #text(size: 12.5pt, weight: "regular", fill: th.text-muted)[
    A Practical Guide to Mastering Zenlang
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
        *Authors:* Zenlang Development Team\
        *Edition:* First Edition (Language 1.0)\
        *Companion:* Standard Library Reference
      ]
    ],
    align(right)[
      #text(size: 8pt, fill: th.text-dim)[
        August 2026\
        `zenlang.org`
      ]
    ]
  )
]

#pagebreak()

// ==========================================
// FOREWORD & OVERVIEW
// ==========================================
= Foreword: The Zen of Code

Most programming languages force you into a compromise:
- *High-level scripting languages* (Python, Ruby, JavaScript) offer rapid prototyping and ergonomic data manipulation, but struggle with terminal latency, distribution overhead, and single-binary packaging.
- *Systems languages* (C, C++, Rust, Zig) deliver blisteringly fast, sub-millisecond execution and tiny native binaries, but require extensive boilerplate for daily scripts and UI layout.

*Zenlang bridges this divide.*

It combines visual data flow (`->` and `<-`), first-class terminal canvas rendering, dual execution parity (interpret instantly during development or compile directly to native C with `-g`), and explicit memory management.

#pagebreak()

// ==========================================
// TABLE OF CONTENTS
// ==========================================
#outline(title: [Table of Contents], depth: 2, indent: auto)

#pagebreak()

// ==========================================
// PART I: FUNDAMENTALS
// ==========================================
#align(center + horizon)[
  #text(size: 10pt, weight: "bold", fill: th.primary, tracking: 0.15em)[PART I]
  #v(0.6em)
  #text(size: 24pt, weight: "bold", fill: th.text-main)[Language Fundamentals]
  #v(0.8em)
  #line(length: 30%, stroke: 1pt + th.primary)
  #v(0.8em)
  #text(size: 10pt, fill: th.text-muted)[Installation, visual data flow, types, sentinels, and expressive control flow.]
]

#pagebreak()

#include "01_getting_started.typ"

#include "02_visual_data_flow.typ"

#include "03_types_and_sentinels.typ"

#include "04_control_flow.typ"

// ==========================================
// PART II: ABSTRACTIONS & ARCHITECTURE
// ==========================================
#align(center + horizon)[
  #text(size: 10pt, weight: "bold", fill: th.primary, tracking: 0.15em)[PART II]
  #v(0.6em)
  #text(size: 24pt, weight: "bold", fill: th.text-main)[Abstractions & Architecture]
  #v(0.8em)
  #line(length: 30%, stroke: 1pt + th.primary)
  #v(0.8em)
  #text(size: 10pt, fill: th.text-muted)[Functions, snapshot closures, structures, classes, error handling, and modules.]
]

#pagebreak()

#include "05_functions_and_closures.typ"

#include "06_structures_and_oop.typ"

#include "07_error_handling.typ"

#include "08_modules_and_reflection.typ"

// ==========================================
// PART III: TERMINAL SYSTEMS & PROJECTS
// ==========================================
#align(center + horizon)[
  #text(size: 10pt, weight: "bold", fill: th.primary, tracking: 0.15em)[PART III]
  #v(0.6em)
  #text(size: 24pt, weight: "bold", fill: th.text-main)[Terminal Systems & Projects]
  #v(0.8em)
  #line(length: 30%, stroke: 1pt + th.primary)
  #v(0.8em)
  #text(size: 10pt, fill: th.text-muted)[High-speed ANSI canvas, dual execution under C, and full practical applications.]
]

#pagebreak()

#include "09_terminal_mastery.typ"

#include "10_dual_execution_and_c.typ"

#include "11_practical_projects.typ"
