#import "template.typ": *

= Source Code Representation & Lexical Structure

== Source Code Encoding

Zenlang source files are UTF-8 encoded text. Whitespace separates tokens and has no semantic significance except within string literals, comments, and documentation blocks. Indentation is purely stylistic and not syntactically enforced.

== Comments

Zenlang supports three distinct comment forms:

#feature(
    "Single-Line Comments",
    "// ... to end of line",
    "// This is a single-line comment\nlet x -> 42 // Inline comment"
)

#feature(
    "Multi-Line Block Comments",
    "/* ... */",
    "/*\n * Multi-line comment for detailed\n * algorithmic explanations.\n */"
)

#feature(
    "Documentation Comments",
    "/! ... !/",
    "/!\n * @param path String Target file path\n * @return Boolean True if exists\n !/"
)

#note[
  Documentation comments (`/! ... !/`) are parsed by the language introspection engine and tooling (e.g. `zendoc`) to produce structured API reference manuals automatically. Comments do not nest.
]

== Identifiers

Identifiers name variables, functions, structures, classes, modules, and types. An identifier begins with an ASCII letter (`a-z`, `A-Z`) or underscore (`_`), followed by any number of ASCII letters, digits (`0-9`), or underscores. Identifiers are case-sensitive.

#feature(
    "Identifiers",
    "[a-zA-Z_][a-zA-Z0-9_]*",
    "let max_count -> 100\nlet userProfile -> Nothing\nset API_VERSION -> `1.0.0`\nclass NetworkManager { ... }"
)

== Scope Blocks & Namespaces

Zenlang defines three levels of lexical scoping:

=== 1. Global Scope
Exactly one top-level global scope exists per module. It contains module-level variables, functions, constants, structures, and imported packages.

=== 2. Lexical Scopes
Code blocks delimited by curly braces (`{ ... }`) create a new nested lexical scope. Inner scopes inherit symbols from outer enclosing scopes; outer scopes cannot access inner identifiers.

```zl
{
    let outer_val -> 10
    {
        let inner_val -> outer_val + 5 // Valid: reads outer_val
    }
    // inner_val is no longer in scope here
}
```

=== 3. Explicit Named Scopes (`scope`)
Named scopes provide an addressable, isolated namespace within a module:

#feature(
    "Named Scope Blocks",
    "scope Identifier { ... }\nIdentifier.Member",
    "scope Config {\n    set TIMEOUT -> 30\n    set RETRIES -> 3\n}\n\nlet max_wait -> Config.TIMEOUT * Config.RETRIES"
)
