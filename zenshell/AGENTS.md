# DOX: zenshell

## Purpose
`zenshell` (`zsh`) is a modern, next-generation Unix shell written in 100% pure Zenlang. It operates as an independent top-level project separate from the Zenlang compiler toolchain.

`zenshell` unifies terminal computing around the Zen Trinity:
1. **ZenLang (`.zl`)**: The scripting engine and command language, replacing brittle bash/sh scripts with typed, memory-safe, visual-flow code.
2. **ZenData (`.zd`)**: The data serialization and configuration standard, powering shell configuration (`config.zd`), session checkpoints, and structured tabular pipelines.
3. **ZenMark (`.zm`)**: The document and manual format, rendering interactive man pages, styled command help, callouts, and ANSI table UI directly in the terminal.

It incorporates advanced productivity features inspired by the `zenshell-nodep` prototype:
- Intelligent directory stack (`push`, `pop`, `jump`, `drop`) and named bookmarks.
- Hybrid execution: seamless routing between built-in commands, POSIX binaries, and live Zenlang expressions.
- First-class structured object pipelines with Unicode box-drawing tables.
- Interactive line editing with history, rainbow brackets, and dynamic Tab autocompletion via `zen.sys.readline`.

## Ownership
`zenshell` is owned as an independent ecosystem product within the Zenlang project tree. It depends solely on the shared Zenlang runtime (`runtime/`) and standard library (`lib/zen/`), remaining decoupled from compiler internals (`selfhost/` and `bootstrap/`).

## Local Contracts
- **Independence**: `zenshell` must build and run as a standalone CLI application. It must not depend on compiler private internals.
- **Trinity Parity**:
  - Configuration must be declarative ZenData (`.zd`), using `zen.data.zendata`.
  - Documentation and command help must be written in ZenMark (`.zm`), rendered with `zen.text.zenmark.render_term`.
  - Shell scripts are native Zenlang (`.zl`) files executed via `zen run` or `process.shell`.
- **String Syntax**: Strict enforcement of backtick strings (`` `...` ``); double quotes are forbidden.
- **Zero External Dependencies**: All interactive line reading, terminal formatting, and process management rely exclusively on `lib/zen/` (`zen.sys.readline`, `zen.sys.process`, `zen.ui.table`, `zen.sys.termposix`).
- **Configuration & State Paths**:
  - User config resides at `~/.config/zenshell/config.zd`, falling back to `zenshell/config/default_config.zd`.
  - Persistent command history is stored at `~/.config/zenshell/history`.
  - Saved ZenData sessions are stored at `~/.config/zenshell/sessions/<name>.zd`.
  - Saved directory tags are stored at `~/.config/zenshell/tags.zd`.
  - Persistent notes/scratchpad are stored at `~/.config/zenshell/notes.zd`.
- **Registered Core Commands**: `directory` (alias `dir`), `list` (aliases `l`, `ls`, `ll`, `la`), `tag`, `open` (alias `o`), `eval` (aliases `=`, `zen`), `run`, `sysinfo` (alias `sys`), `calendar` (alias `cal`), `greet`, `note` (alias `jot`), `history`, `session`, `zd`, `doc`, `table`, `view`, `clear`, `echo`, `catsay`, `alias`. Base class resides in `src/core/command.zl`.

## Work Guidance
- Implement modular commands in `zenshell/src/commands/` extending the base `Command` contract.
- Each command must provide an embedded `.zm` help document accessible via `<cmd> help` or `doc <cmd>`.
- Use `zen.sys.process` for external binaries and piping; avoid raw bash subshells where Zen APIs suffice.
- Output from commands should prefer structured collections (`List`, `Map`, `Table`) so downstream pipelines can filter/project data before terminal rendering.

## Verification
- Syntax & Type Verification: `ZEN_PATH=".:zenshell:lib" ./bin/zen check zenshell/src/main.zl`
- Smoke Run: `ZEN_PATH=".:zenshell:lib" ./bin/zen run zenshell/src/main.zl --test`
- Native AOT Build: `./bin/zen build zenshell/zen.pkg.zd`

## Child DOX Index
*(No child DOX trees currently required; subtrees are governed by this document).*
