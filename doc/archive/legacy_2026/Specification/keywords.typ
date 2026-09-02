#import "template.typ": *

= Reserved Keywords & Sentinels

== Reserved Language Keywords

The following identifiers are reserved language keywords and cannot be used as variable or function names:

#table(
  columns: (1fr, 1fr, 1fr, 1fr),
  [`let`], [`set`], [`function`], [`class`],
  [`structure`], [`enumerator`], [`type`], [`scope`],
  [`when`], [`or`], [`and`], [`not`],
  [`xor`], [`do`], [`while`], [`until`],
  [`for`], [`in`], [`break`], [`continue`],
  [`defer`], [`check`], [`raise`], [`assert`],
  [`use`], [`import`], [`from`], [`as`],
  [`export`], [`extend`], [`spawn`], [`await`],
  [`self`], [`parent`], [`module`], [`entry`]
)

== Sentinel Literals & Constants

#table(
  columns: (1.5fr, 3fr),
  [Sentinel], [Description],
  [`Nothing`], [Represents the intentional absence of a value (null/nil state)],
  [`Default`], [Materializes the canonical zero-state for a type (`0`, `""`, `[]`, `{}`)],
  [`True`], [Boolean truth literal (also lowercase `true`)],
  [`False`], [Boolean false literal (also lowercase `false`)]
)