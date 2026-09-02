
#show raw.where(lang: "zenlang").or(raw.where(lang: "zl")): set raw(
  syntaxes: "zenlang.sublime-syntax",
  theme: "zenlang.tmTheme",
)

// Optional: specific background styling for zenlang blocks
#show raw.where(lang: "zenlang").or(raw.where(lang: "zl")): it => block(
  fill: rgb("#292524"),
  inset: 10pt,
  radius: 4pt,
  width: 100%,
  text(fill: rgb("#ffffff"), it),
)