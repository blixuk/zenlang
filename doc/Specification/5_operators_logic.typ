== Logic

```zl
True
False

True and False
True or False
not True 
```

== Logical Operators

```zl
and     // Logical AND
or      // Logical OR
not     // Logical NOT
xor     // Logical XOR
nor     // Logical NOR
nand    // Logical NAND
xnor    // Logical XNOR
```

== Bitwise Operators

```zl
&&      // Bitwise AND
||      // Bitwise OR
!!      // Bitwise NOT
^^      // Bitwise XOR
!|      // Bitwise NOR
!&      // Bitwise NAND
!^      // Bitwise XNOR
%%      // Bitwise MOD
<<      // Bitwise LEFT SHIFT
>>      // Bitwise RIGHT SHIFT
```

== Comparison Operators

```zl
=       // Equal
!=      // NOT Equal
&=      // AND Equal
|=      // OR Equal
^=      // XOR Equal
%=      // MOD Equal
<       // Less Than
>       // Greater Than
<=      // Less Than or Equal
>=      // Greater Than or Equal
<<=     // LEFT SHIFT Equal
>>=     // RIGHT SHIFT Equal
```

== Arithmetic Operators

```zl
+       // Addition
-       // Subtraction
*       // Multiplication
/       // Division
%       // Remainder (Modulo)
**      // Exponentiation (Power)
++      // Increment
--      // Decrement
//      // Quotient
()      // Parentheses
```

== Range Operators

Range operators build *lists* of integers or single-character strings.
They sit between comparison and arithmetic in the expression grammar.

```zl
a..b     // Half-open range: start inclusive, end exclusive
a..=b    // Closed range: start and end inclusive
```

Examples:

```zl
0..5           // [0, 1, 2, 3, 4]
0..=5          // [0, 1, 2, 3, 4, 5]
5..2           // [5, 4, 3]           (descending)
5..=2          // [5, 4, 3, 2]
`a`..`d`       // [`a`, `b`, `c`]
`a`..=`c`      // [`a`, `b`, `c`]

do for i in 1..=4 {
    // i = 1, 2, 3, 4
}
```

Notes:

- Result type is a `List`.
- Operands are integers, or single-character strings (character code points).
- `...` is *not* a range operator; it is rest/spread in patterns (`[head, ...tail]`).
- Library helpers: `zen.math.range.range(start, end)` and `range_inclusive(start, end)`
  (integer ranges; operators are preferred in new code).

== Order of Operations

```zl
1 + (2 * 2)
(2 + 2) * (8 / 2) + 10
(4 * 4 / (4 + 4))
```
