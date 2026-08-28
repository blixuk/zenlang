#import "template.typ": *

= Module & Package Organization

Zenlang programs are structured into modular packages to encourage composition, encapsulation, and clear dependency boundaries.

== Source Modules

Every `.zl` source file represents an independent compilation unit and module.

=== Built-in `module` Introspection

Every module has access to the implicit built-in `module` object without requiring any imports:

#table(
  columns: (1.5fr, 3fr),
  [Property], [Description],
  [`module.name`], [The identifier name of the current module],
  [`module.path`], [The normalized absolute file path to the module],
  [`module.file`], [The filename with `.zl` extension],
  [`module.dir`], [The directory path containing the file],
  [`module.is_entry`], [Boolean `True` if this file is the process entry point],
  [`module.entry`], [Configurable custom entry point function name]
)

=== Custom Module Entry Points

By default, execution begins at `function main()`. Modules can declare a custom entry point function dynamically:

```zl
function custom_start() {
    io.writeln(`Custom daemon worker initialized.`)
    <- 0
}

module.entry -> `custom_start`
```

== Package Imports (`use`)

Modules import external packages and sibling modules using the `use` statement (the `import` keyword is also supported):

#feature(
    "Package Import Syntax",
    "use package.path\nuse package.path as Alias\nuse `./relative_file.zl` as LocalMod",
    "// Standard nested imports\nuse zen.io\nuse zen.time\nuse zen.text.string as Str\nuse zen.ui.table as table\n\n// Local relative import\nuse `./helpers.zl` as helpers"
)

== Module Resolution & `ZEN_PATH`

The compiler resolves imports across search paths configured in `ZEN_PATH`:
1. *Relative Paths*: Paths beginning with `./` or `../` resolve relative to the calling file.
2. *Standard Library*: Paths starting with `zen.*` resolve to `lib/zen/`.
3. *Compiler Tooling*: Paths starting with `selfhost.*` resolve to `selfhost/`.
4. *Project Root*: Search paths included in the `ZEN_PATH` environment variable.

== Standard Project Hierarchy

```
my_project/
├── .zbuild             // Project build metadata
├── src/                // Application source modules
│   ├── main.zl         // Main application entry
│   └── network/        // Sub-packages
│       └── client.zl
├── lib/                // Vendored local libraries
└── tests/              // Test suites (*_test.zl)
```
