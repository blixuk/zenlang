# Purpose

Language Server Protocol (LSP) daemon implementation in pure Zenlang. Provides IDE intelligence (real-time diagnostics, completions, hover tooltips, jump-to-definition, and document outline symbols) over standard JSON-RPC 2.0 stdio framing.

# Ownership

Selfhost tooling and IDE integrations maintainers.

# Local Contracts

- **Framing:** Standard JSON-RPC 2.0 over standard I/O with `Content-Length: <n>\r\n\r\n` framing (`Protocol.zl`).
- **Server Engine:** `Server.zl` maintains an in-memory document cache (`DOCS`) mapping URI to document text.
- **Capabilities:**
  - `textDocumentSync`: Full sync (`didOpen`, `didChange`, `didSave`, `didClose`).
  - `completionProvider`: Contextual keyword, stdlib module, operator (`->`, `<-`, `:>`), and local AST symbol completions.
  - `hoverProvider`: Keyword, operator, and declaration Markdown tooltips.
  - `definitionProvider`: Declaration navigation for functions, classes, and structures.
  - `documentSymbolProvider`: Hierarchical AST outline symbols.
- **Diagnostics:** Emits `textDocument/publishDiagnostics` on change/open/save via `Parser.parse_source` and `TypeChecker.check_program`.
- **CLI Entry:** `tools/zenlsp.zl`. Hybrid `./bin/zen lsp` runs that file via bootstrap. Not linked into `zen-selfhost`.

# Work Guidance

- Keep JSON parsing and formatting compliant with JSON-RPC 2.0 specs.
- Do not mutate global state outside `DOCS` during request handling.
- Keep protocol IO non-blocking where possible and flush stdout after writing message payloads.

# Verification

- Automated test suite: `tests/tools/test_lsp.zl`
  ```bash
  ./bin/zen tests/tools/test_lsp.zl
  ./bin/zen -g tests/tools/test_lsp.zl
  ```
- Subcommand:
  ```bash
  ./bin/zen lsp
  ```

# Child DOX Index

- Protocol.zl: JSON-RPC 2.0 framing and serialization
- Server.zl: Language server state and capability handlers
