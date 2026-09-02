#import "template.typ": *

= Expressions & Operator Precedence

Expressions in Zenlang produce values and are evaluated from left to right according to operator precedence.

== Operator Precedence Hierarchy

#table(
  columns: (1fr, 2fr, 3fr),
  [Precedence], [Operators], [Description],
  [1 (Highest)], [`.`, `()`, `[]`], [Member access, function call, index lookup],
  [2], [`-` (unary), `not`, `!!`], [Unary negation, logical not, bitwise not],
  [3], [`**`], [Exponentiation],
  [4], [`*`, `/`, `%`, `%%`], [Multiplication, division, modulo, bitwise mod],
  [5], [`+`, `-`], [Addition, subtraction],
  [6], [`<<`, `>>`], [Bitwise bit shifts],
  [7], [`..`, `..=`], [Half-open and closed range construction],
  [8], [`<`, `<=`, `>`, `>=`], [Relational comparison],
  [9], [`==`, `!=`], [Equality and inequality comparison],
  [10], [`&&`, `||`, `^^`], [Bitwise AND, OR, XOR],
  [11], [`and`, `or`, `xor`], [Logical boolean operations],
  [12], [`when ... or`], [Inline conditional ternary],
  [13 (Lowest)], [`->`, `<-`], [Visual binding and return]
)