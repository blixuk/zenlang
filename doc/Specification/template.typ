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

#let background = rgb("#2e3440")
#let foreground = rgb("#eceff4")
#let accent = rgb("#5e81ac")
#let accent-dark = rgb("#4c566a")

#let black = rgb("#2e3440")
#let white = rgb("#eceff4")
#let gray = rgb("#d8dee9")
#let dark-gray = rgb("#4c566a")
#let blue = rgb("#5e81ac")
#let green = rgb("#a3be8c")
#let orange = rgb("#d08770")
#let pink = rgb("#b48ead")
#let purple = rgb("#8fbcbb")
#let red = rgb("#bf616a")
#let yellow = rgb("#ebcb8b")

#let project(doc) = {
  set page(
    paper: "a4",
    fill: background,
    margin: (x: 1.5cm, y: 2cm),
  )
  set text(
    font: "Noto Sans",
    size: 10pt,
    fill: foreground
  )

  // Apply global show rules here so they affect the whole doc
  show heading: set text(fill: accent)

  // Your RAW BLOCK styling

  // Code Syntax

  show raw.where(lang: "zenlang").or(raw.where(lang: "zl")): set raw(
    syntaxes: "Style/zenlang.sublime-syntax",
    theme: "Style/zenlang.tmTheme",
  )

  // Optional: specific background styling for zenlang blocks
  show raw.where(lang: "zenlang").or(raw.where(lang: "zl")): it => block(
    fill: rgb("#2e3440"),
    stroke: accent,
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    breakable: false, // Keep concept and example together
    text(fill: rgb("#eceff4"), it),
  )

  doc
}

// Templates

#let feature(title, syntax, example) = {
  block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false, // Keep concept and example together
    [
      === #title
      #v(0.5em)
    
      Syntax:
      #raw(syntax, lang: "zenlang")

      Example:
      #raw(example, lang: "zenlang")
    ]
  )
}

#let small_feature(title, description, syntax) = {
  block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false, // Keep concept and example together
    [
      === #title
      #v(0.5em)
    
      #description

      Syntax:
      #raw(syntax, lang: "zenlang")
    ]
  )
}

#let example_feature(title, example) = {
  block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false, // Keep concept and example together
    [
      === #title
      #v(0.5em)

      Example:
      #raw(example, lang: "zenlang")
    ]
  )
}

#let syntax_feature(title, syntax) = {
  block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false, // Keep concept and example together
    [
      === #title
      #v(0.5em)

      Syntax:
      #raw(syntax, lang: "zenlang")
    ]
  )
}

#let big_feature(title, concept, syntax, example) = {
  v(1em) // Vertical space
  block(
    fill: accent-dark, // background
    stroke: accent, // Blue accent bar on the left
    inset: 10pt,
    radius: 5pt,
    breakable: false, // Keep concept and example together
    [
      #text(fill: white)[ == #title ]
      #v(0.5em)

      #text(fill: gray)[ #concept ]
      #v(0.5em)
      
      #text(fill: white)[ *Syntax:* ]
      #raw(syntax, lang: "zl")

      #text(fill: white)[ *Example:* ]
      #raw(example, lang: "zl") 
    ]
  )
}

// ---------------------------------------------

#let stroke(item) = {
  block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    [
      #item
    ]
  )
}

#let title_code(title, code) = {
  block(
    breakable: false,
    [
      === #title
      #v(0.5em)
      #raw(code, lang: "zl")
    ]
  )
}

#let name_code(name, code) = {
  block(
    breakable: false,
    [
      #name
      #v(0.5em)
      #raw(code, lang: "zl")
    ]
  )
}

#let template_1(template) = {
  block(
    breakable: false,
    width: 100%,
    [
      #template
    ]
  )
}

#let template_2(template_1, template_2) = {
  block(
    breakable: false,
    width: 100%,
    [
      #template_1
      #v(0.5em)
      #template_2
    ]
  )
}

#let template_3(template_1, template_2, template_3) = {
  block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    width: 100%,
    [
      #template_1
      #v(0.5em)
      #template_2
      #v(0.5em)
      #template_3
    ]
  )
}

#let template_4(template_1, template_2, template_3, template_4) = {
  block(
    stroke: accent, 
    inset: 10pt, 
    radius: 5pt,
    breakable: false,
    width: 100%,
    [
      #template_1
      #v(0.5em)
      #template_2
      #v(0.5em)
      #template_3
      #v(0.5em)
      #template_4
    ]
  )
}
