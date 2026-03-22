#import "template.typ": *

== Source Code Representation

Zenlang source files are UTF-8 encoded text. Whitespace generally has no semantic meaning except to separate tokens. Newlines may influence indentation in the future but currently do not affect parsing.

Whitespace is ignored except inside:
- Strings
- Multiline strings
- Comments

Indentation is not syntactically significant.

#pagebreak()

== Comments

Comments do not nest.

// #block(
//     stroke: accent, 
//     inset: 10pt, 
//     radius: 5pt,
//     breakable: false,
//     [
//         === Single Line Comment
//         #v(0.5em)

//         Syntax:
//         ```zl
//         // ... 
//         ```
//         #v(0.5em)

//         Example:
//         ```zl
//         // this is a single line comment
//         ```
//     ]
// )

#feature(
    "Single Line Comment",
    "// ...",
    "// this is a single line comment"
)

#feature(
    "Multi-line Comment",
    "/* ... */",
    "/*\n This\n is\n a\n multi-line\n comment\n */"
)

#feature(
    "Documentation Comment",
    "/! ... !/",
    "/!\n This\n is\n a\n multi-line\n documentation\n comment\n !/"
)
 
== Identifiers

Identifiers are names used to identify variables, functions, classes, types, and other symbols.

An identifier consists of:
- a leading letter or underscore
- followed by letters, digits, or underscores

Identifiers are case-sensitive.

#feature(
    "Identifiers",
    "[a-zA-Z_][a-zA-Z0-9_]*",
    "UPPERCASE\nlowercase\ncamelCase\nSnake_Case\nPascalCase\n"
)

== Scope Blocks

Zen supports:
- Global scope
- Lexical scope (single and nested)
- Named scope (explicit, addressable)

Scope Blocks use:

#syntax_feature(
    "Single Scope",
    "{ ... }",
)

#syntax_feature(
    "Nested Scope",
    "{ ...\n    { ... }\n }",
)

#syntax_feature(
    "Named Scope",
    "scope Identifier { ... }\n\nIdentifier.Identifier",
)

#example_feature(
    "Scopes",
    "/* Scope Level 0 : Global Scope */\n\n{ /* Scope Level 1 */ }\n\n{ /* Scope Level 1 */\n    { /* Scope Level 2 */ }\n}\n\nscope NamedScope { /* Scope Level 1 : NamedScope */ }",
)

Single, Nested and Named Scope Blocks:
```zl
/* Scope Level 0 : Global Scope */

{ /* Scope Level 1 */ }

{ /* Scope Level 1 */
    { /* Scope Level 2 */ }
}

scope NamedScope { /* Scope Level 1 : Named Scope */ }
```

=== Global Scope

Exactly one global scope per program/module.

Contains:
- Builtins
- Global constants and variables
- Global functions, structures, enumerators
- Global named scopes

Rules:
- Always visible
- Cannot reference child scopes
- Exists for the lifetime of the program

Example:
```zl
set VERSION : String -> `0.1.0`

function main {
    write(VERSION)
}
```

=== Lexical Scopes (single and nested)

These are implicit scopes, created by syntax. Scopes can nest arbitrarily.

Single scopes:
- One parent
- One lifetime
- No name
- No external visibility

Example:
```zl
{
    let x -> 10
}
```

Nested scopes:
- Inner scopes can read parent symbols
- Parents cannot read child symbols
- Shadowing allowed

Example:
```zl
{
    let x -> 10
    {
        let y -> x + 5
    }
}
```

=== Named Scopes (explicit scopes)

Think of it as a labeled block.

Named scope:
- A scope with an identifier
- Lexically nested
- Addressable by name
- Not a namespace (important distinction)

Example:
```zl
scope Config {
    set MAX_HP : Integer -> 100
}

write(Config.MAX_HP)
```

Use cases:

```zl
scope GameConfig {
    set MAX_PLAYERS : Integer -> 64
    set TICK_RATE : Integer -> 60
}
```

```zl
scope PlayerState {
    let health -> 100
    let stamina -> 50
}
```

```zl
scope Platform {

    scope Windows {
        set PATH_SEPERATOR : String -> `\`
    }

    scope Linux {
        set PATH_SEP : String -> `/`
    }

}

write(Platform.Linux.PATH_SEP)
```
