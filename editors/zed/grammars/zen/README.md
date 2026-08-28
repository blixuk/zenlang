# tree-sitter-zen

Tree-sitter grammar for **Zenlang** (`.zl` / `.zs`).

Used by the [Zed extension](../zed/) for syntax highlighting, outline, and indent.

## Build

```bash
cd editors/tree-sitter-zen
npm install
npx tree-sitter generate
npx tree-sitter build   # optional native lib for local testing
npx tree-sitter parse ../../examples/getting_started/01_hello.zl
```

## Layout

| Path | Role |
|------|------|
| `grammar.js` | Grammar source |
| `src/` | Generated parser (after `tree-sitter generate`) |
| `queries/` | Highlight / outline / brackets / indents / textobjects |

## Notes

- Grammar is **MVP-oriented**: real projects highlight well; edge-case full language parity is iterative.
- Prefer regenerating `src/parser.c` after grammar changes and committing the generated files so Zed can build without Node at install time when possible.
