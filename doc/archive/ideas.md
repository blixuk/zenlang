```c


```


Primitive Types:

Boolean (1bit)

Integer - 32bit
Integer[8] (8bit)
Integer[16] (16bit)
Integer[32] (32bit)
Integer[64] (64bit)
Integer[128] (128bit) - Possible addition

Decimal - 32bit
Decimal[32] (32bit)
Decimal[64] (64bit)
Decimal[128] (128bit) - Possible addition

Number (Integer, Decimal, Hexadecimal, Binary, Octal)?
Integer: 1
Decimal: 0.5
Hexadecimal: 0x7B
Binary: 0b01111011
Octal: 0o173

support writing numbers with _ as separator.
1_000_000 is the same as 1000000

(UTF-8, UTF16, UTF-32)

Rune - UTF-?
Rune[8] (UTF-8)
Rune[16] (UTF-16)
Rune[32] (UTF-32)

String - UTF-?
String[8] (UTF-8)
String[16] (UTF-16)
String[32] (UTF-32)

Extended Types:

Character -> Word -> Sentence -> Paragraph -> Chapter -> Book

Structure

Enumerator

Dictionary

List

Tuple

Vector?

------------------------

Boolean

Integer
Integer[8]
Integer[16]
Integer[32]
Integer[64]

Decimal
Decimal[32]
Decimal[64]

Rune
Rune[8]
Rune[16]
Rune[32]

String
String[8]
String[16]
String[32]

Structure

Function

Enumerator

Dictionary
Dictionary<String, Integer>
Dictionary<String[8], Integer[8]>

Tuple
Tuple<Integer, String>
Tuple<Integer[8], String[8]>

List
List<Integer>
List<Integer[64]>
List<String>
List<String[8]>


-----------------------------------

Full C ABI Compatibility
zen fits right into your C application with full C ABI compatibility out of the box: no need for special "C compatible" types or functions, no limitations on what zen features you can use from C.

Macros
Compile Time and Semantic Macros
Unlock the full power of compile-time code with macros that read like functions

Meta Programming?

Inline Assembly
Write asm as regular inline code without using strings or cryptic constraints.


Detailed stacktraces
Error Messages
incode error and debug printing

Zendoc comment todo, fixme, note..ect

Zen Regex alternative
Pattern matching

Loops with entry and exit function calling?
Run function/block at start of loop before the body and at the end of the loop after body.

Signals like in Godot gdscript

Coroutines / futures / threads combined

Multiple stacks or stack matrix

lable: lable keyword used to define a lable. Use: 'lable start'
moveto: goto label, but within scope. Use: 'moveto start'
jumpto: goto label, but globally. Use: 'jumpto start'


keyword: defer - to defer something to be called at the end of the current scope
keyword: yield - to yield something to be called at the end of the current scope
keyword: assert - to assert something

----------------------


