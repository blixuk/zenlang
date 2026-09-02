# Logic

True            // Boolean True
False           // Boolean False

A and B         // Logical AND
A or B          // Logical OR
not A           // Logical NOT
A or not B      // Logical OR NOT
A and not B     // Logical AND NOT

# Logical Operators

and     // Logical AND
or      // Logical OR
not     // Logical NOT

xor     // Logical XOR
nor     // Logical NOR
nand    // Logical NAND
xnor    // Logical XNOR

Arithmetic Operators

+       // Addition
-       // Subtraction
*       // Multiplication
/       // Division
%       // Modulo Exclusive
%%      // Modulo Inclusive
**      // Power
//      // Quotient

a + b   // Addition
a - b   // Subtraction
a * b   // Multiplication
a / b   // Division
a % b   // Modulo
a ** b  // Power
a // b  // Quotient

# Bitwise Operators

&&      // Bitwise AND
||      // Bitwise OR
!!      // Bitwise NOT
^^      // Bitwise XOR
!|      // Bitwise NOR
!&      // Bitwise NAND
!^      // Bitwise XNOR
<<      // Bitwise LEFT SHIFT
>>      // Bitwise RIGHT SHIFT

# Comparison Operators

==      // Equal
!=      // NOT Equal
<       // Less Than
>       // Greater Than
<=      // Less Than or Equal
>=      // Greater Than or Equal

# Ranges

..     // Range Between
..+    // Range Inclusive
..-    // Range Exclusive
...    // Range Inclusive Exclusive

0..5   // Range 0 to 5 [1, 2, 3, 4]
0..+5  // Range 0 to 5 [1, 2, 3, 4, 5]
0..-5  // Range 0 to 5 [0, 1, 2, 3, 4]
0...5  // Range 0 to 5 [0, 1, 2, 3, 4, 5]

5..0   // Range 5 to 0 [4, 3, 2, 1]
5..+0  // Range 5 to 0 [4, 3, 2, 1, 0]
5..-0  // Range 5 to 0 [5, 4, 3, 2, 1]
5...0  // Range 5 to 0 [5, 4, 3, 2, 1, 0]

# Increment and Decrement

a++  // Increment (postfix)
++a  // Increment (prefix)
a--  // Decrement (postfix)
--a  // Decrement (prefix)

// 1. Numbers (Increment / Decrement)
let count -> 5
count++                       // count becomes 6
count--                       // count becomes 5

count++ 5                     // count becomes 10
count-- 5                     // count becomes 5

// 2. Strings (Append / Prepend / Drop)
let msg -> `Hello`
msg++ ` World`                // msg becomes `Hello World` (append)
++msg `>> `                   // msg becomes `>> Hello World` (prepend)
msg--                         // drops last character
--msg                         // drops first character

// 3. Lists (Append / Prepend / Drop)
let items -> [1, 2]
items++ 3                     // items becomes [1, 2, 3] (append)
++items 0                     // items becomes [0, 1, 2, 3] (prepend)
items--                       // drops last element -> [0, 1, 2]
--items                       // drops first element -> [1, 2]

# Symbol Keywords & Aliases

Keyword: assign, Symbol: -> 
Keyword: infer, Symbol: :>
Keyword: cast, Symbol: <:
Keyword: return, Symbol: <-
Keyword: yield, Symbol: <~
Keyword: type, Symbol: :
Keyword: defer, Symbol: ~ 
Keyword: check, Symbol: ?
Keyword: assert, Symbol: !
Keyword: raise, Symbol: ^
