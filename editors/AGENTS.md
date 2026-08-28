# Purpose

Editor integrations for Zenlang: syntax highlighting, language configuration, snippets, Tree-sitter grammar, and diagnostics.

# Ownership

Owned by the editor support / tooling effort.

# Local Contracts

- Syntax definitions must stay aligned with lexer/spec keywords (`doc/Specification/keywords.typ`, bootstrap lexer).
- **VS Code / Cursor / Antigravity:** `vscode/` — TextMate grammars (`zen.tmLanguage.json`, `zendata.tmLanguage.json`, `zenmark.tmLanguage.json`, `zsp.tmLanguage.json`), snippets, JS extension with native Zenlang LSP client bridge (`bin/zen lsp`) providing real-time diagnostics, completions, hover, definitions, and document symbols (with bootstrap `--check` fallback). Support for `.zl`/`.zs` (Code), `.zd`/`.zen` (Data), `.zm` (Mark), and `.zsp` (Syntax Patterns).
- **Zed:** `zed/` — language extension; requires Tree-sitter grammar in `tree-sitter-zen/`.
- **Tree-sitter:** `tree-sitter-zen/` — `grammar.js` + generated `src/parser.c` + `queries/`.
- **Sublime:** `sublime/zenlang.sublime-syntax`.
- Changes to keywords, operators (`->`, `<-`, `..`, `..=`), or string syntax require updates in **all** active grammars.

# Work Guidance

- Prefer runnable install docs in each subdirectory README.
- After `grammar.js` changes: `cd editors/tree-sitter-zen && npx tree-sitter generate`, then copy `queries/*.scm` → `zed/languages/zen/` (or run `scripts/setup_zed_extension.sh`).
- Commit generated `tree-sitter-zen/src/parser.c` (and related) so Zed can build without regenerating.
- Do not commit `node_modules/`.
- Keep snippets idiomatic (nested imports, `when` without required parens, `<-` returns).

# Verification

```bash
./scripts/setup_vscode_extension.sh
./scripts/setup_zed_extension.sh

# Tree-sitter still parses samples
cd editors/tree-sitter-zen && npx tree-sitter parse ../../examples/getting_started/01_hello.zl

# extension.toml must use a full git SHA (not "local")
grep '^rev' editors/zed/extension.toml
```

Manual:
- VS Code/Antigravity: reload window → open `.zl` → language Zenlang
- Zed: Install Dev Extension → `editors/zed` (check log if grammar fails)

# Child DOX Index

- README.md — install overview for all editors
- vscode/ — package.json, language-configuration.json, snippets.json, syntaxes/, src/extension.js, icons/, README.md
- zed/ — extension.toml, languages/zen/, README.md
- tree-sitter-zen/ — grammar.js, src/, queries/, package.json, README.md
- sublime/ — zenlang.sublime-syntax
- typst/ — doc syntax styles
- `scripts/setup_zed_extension.sh` — generate grammar + patch Zed file:// path
