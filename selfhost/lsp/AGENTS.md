# Purpose

Language Server Protocol (LSP) daemon implementation in pure Zenlang. Provides IDE intelligence (real-time diagnostics, completions, hover tooltips, jump-to-definition, and document outline symbols) over standard JSON-RPC 2.0 stdio framing.

# Ownership

Selfhost tooling and IDE integrations maintainers.

# Local Contracts

- **Framing & Async Transport:** Standard JSON-RPC 2.0 over standard I/O with `Content-Length: <n>\r\n\r\n` framing (`Protocol.zl`). Implements non-blocking kernel event reactor polling (`read_message_async()` backed by `conc.poll_fd(0, 1, 0.5)`) to prevent blocking the cooperative fiber scheduler.
- **Server Engine & Positional AST:** `Server.zl` maintains in-memory document buffers and parsed AST caches. All AST traversals strictly utilize the Three-Layer Architecture's flat positional struct accessors from `compiler.AST` (`prog_stmts`, `ast_kind`, `fn_name`, `class_name`, `struct_name`, `let_name`, `ast_line`, etc.) rather than legacy dictionary lookups.
- **Capabilities:**
  - `textDocumentSync`: Full sync (`didOpen`, `didChange`, `didSave`, `didClose`).
  - `completionProvider`: Contextual keyword, stdlib module, operator (`->`, `<-`, `:>`), and local positional AST symbol completions.
  - `hoverProvider`: Keyword, operator, and declaration Markdown tooltips.
  - `definitionProvider`: Declaration navigation for functions, classes, structures, and variables.
  - `documentSymbolProvider`: Hierarchical AST outline symbols mapped to standard LSP SymbolKinds.
- **Diagnostics:** Emits `textDocument/publishDiagnostics` on change/open/save via `Parser.parse_source` and `TypeChecker.check_program`.
- **CLI Entry & Daemon Loop:** `tools/zenlsp.zl`. Concurrently spawns `reader_task(ch)` on the native fiber pool, receives parsed JSON-RPC messages via an MPMC ring-buffer channel (`conc.channel(100)`), dispatches to `Server.handle_request(srv, msg)`, and handles graceful exit on `exit` method.

# Work Guidance

- Keep JSON parsing and formatting compliant with JSON-RPC 2.0 specs.
- Do not mutate global state outside document buffers during request handling.
- Keep protocol IO non-blocking via `poll_fd` readiness checks before reading stdin.
- Maintain 100% dual-path parity between native AOT compilation and interpreter execution.

# Verification

- Automated test suite: `tests/tools/test_lsp.zl`
  ```bash
  python3 bootstrap/Zen.py tests/tools/test_lsp.zl
  ./bin/zen run tests/tools/test_lsp.zl
  ```
- End-to-end JSON-RPC daemon verification:
  ```bash
  ./bin/zen run tools/zenlsp.zl
  python3 bootstrap/Zen.py tools/zenlsp.zl
  ```

# Child DOX Index

- Protocol.zl: JSON-RPC 2.0 framing, serialization, and async reactor reader
- Server.zl: Language server state, positional AST queries, and capability handlers
