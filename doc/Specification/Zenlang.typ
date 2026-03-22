// Styling

// Nord Colour Palette
// Polar Night
// #2e3440
// #3b4252
// #434c5e
// #4c566a
// Snow Storm
// #d8dee9
// #e5e9f0
// #eceff4
// Frost
// #8fbcbb
// #88c0d0
// #81a1c1
// #5e81ac
// Aurora
// #bf616a
// #d08770
// #ebcb8b
// #a3be8c
// #b48ead

// #let background = rgb("#2e3440")
// #let foreground = rgb("#eceff4")
// #let accent = rgb("#5e81ac")
// #let accent-dark = rgb("#4c566a")

// #let black = rgb("#2e3440")
// #let white = rgb("#eceff4")
// #let gray = rgb("#d8dee9")
// #let dark-gray = rgb("#4c566a")
// #let blue = rgb("#5e81ac")
// #let green = rgb("#a3be8c")
// #let orange = rgb("#d08770")
// #let pink = rgb("#b48ead")
// #let purple = rgb("#8fbcbb")
// #let red = rgb("#bf616a")
// #let yellow = rgb("#ebcb8b")

// // Page Styling

// #set page(
//   paper: "a4",
//   fill: background,
//   margin: (x: 1.5cm, y: 2cm),
// )

// #set text(
//   font: "Noto Sans",
//   size: 11pt,
//   fill: foreground
// )

// // Code Syntax

// #show raw.where(lang: "zenlang").or(raw.where(lang: "zl")): set raw(
//   syntaxes: "Style/zenlang.sublime-syntax",
//   theme: "Style/zenlang.tmTheme",
// )

// // Optional: specific background styling for zenlang blocks
// #show raw.where(lang: "zenlang").or(raw.where(lang: "zl")): it => block(
//   fill: rgb("#2e3440"),
//   stroke: accent,
//   inset: 10pt,
//   radius: 4pt,
//   width: 100%,
//   breakable: false, // Keep concept and example together
//   text(fill: rgb("#eceff4"), it),
// )


#import "template.typ": *

#show: project

// Document

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
