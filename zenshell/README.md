# zenshell (zsh)

> A modern, next-generation Unix shell written in 100% pure Zenlang.

`zenshell` unifies terminal computing, system scripting, structured data pipelines, and interactive documentation around the **Zen Trinity**:

- **ZenLang (`.zl`)**: The scripting engine and interactive command interpreter. Replaces fragile bash scripts with typed, visual-flow code (`->` and `<-`).
- **ZenData (`.zd`)**: Declarative data serialization standard. Powers shell configuration, session state checkpoints, and structured tabular pipelines.
- **ZenMark (`.zm`)**: Document Object Model for terminal manuals, rich help pages, styled callouts, and ANSI table UI.

---

## Key Features

1. **Structured Object Pipelines**: Pipes (`|`) can pass rich `ZenValue` collections (`List`, `Map`, `Table`) in-process, or stream standard byte streams when communicating with external POSIX binaries.
2. **Directory Stack & Bookmarks**:
   - Stack navigation: `pushd`, `popd`, `dirs`, `jump <index>`, `drop <index>`.
   - Named bookmarks: `dir add proj /path/to/project`, `dir jump proj`.
   - Quick relative jumps: `..`, `...` (`../..`), `.3` (`../../..`), etc.
3. **Dual Execution Engine**:
   - Shell commands & external binaries (`git`, `cargo`, `ls`, `grep`).
   - In-line Zenlang expression evaluation (`let x -> 42`, `[1, 2, 3].map(...)`).
4. **Interactive Line Editing**: Powered by `zen.sys.readline` with 5-color rainbow delimiters, in-line history search, and dynamic tab-completion.
5. **Config & Sessions in ZenData (`.zd`)**:
   - Configuration stored in `~/.config/zenshell/config.zd`.
   - Save and restore named sessions (`session save work`, `session load work`).
6. **Native Terminal Documentation**:
   - `help <cmd>` and `doc <topic>` render formatted ZenMark (`.zm`) manuals directly to your terminal.

---

## Directory Layout

```
zenshell/
├── zen.pkg.zd            # Package manifest (.zd)
├── AGENTS.md             # DOX work contract & guidelines
├── README.md             # Project documentation
├── config/
│   └── default_config.zd # Default fallback configuration
├── docs/
│   └── zenshell.zm       # Interactive terminal user manual in ZenMark
└── src/
    ├── main.zl           # CLI entry point & REPL loop
    ├── core/
    │   ├── command.zl    # Modular base Command contract
    │   ├── context.zl    # State, cwd, bookmarks, variables
    │   ├── config.zl     # ZenData configuration loader/serializer
    │   ├── history.zl    # Persistent history engine (~/.config/zenshell/history)
    │   ├── session.zl    # ZenData session snapshot manager
    │   └── engine.zl     # Dispatcher, pipeline executor & fallback eval
    ├── commands/
    │   ├── directory.zl  # Directory navigation, stack & bookmarks (alias: dir)
    │   ├── list.zl       # Tabular directory listing, detailed & tree (aliases: l, ls, ll, la)
    │   ├── tag.zl        # Semantic place tagging & terminal dividers
    │   ├── open.zl       # Desktop application launcher for files & URLs (alias: o)
    │   ├── eval.zl       # In-line Zenlang evaluator (aliases: =, zen)
    │   ├── run.zl        # Native ZenScript (.zl) runner with CLI arguments
    │   ├── history.zl    # Command history viewer, finder & cleaner
    │   ├── session.zl    # ZenData session manager (save, load, list, remove)
    │   ├── data.zl       # ZenData inspection & query pipeline (zd)
    │   ├── doc.zl        # ZenMark manual viewer & command help
    │   ├── table.zl      # Box table formatter
    │   ├── clear.zl      # Clear terminal window
    │   ├── echo.zl       # Echo arguments
    │   ├── catsay.zl     # ASCII cat speak bubble
    │   ├── sysinfo.zl    # System resource inspection & RAM/CPU dashboard (alias: sys)
    │   ├── calendar.zl   # Terminal monthly and yearly calendar generator (alias: cal)
    │   ├── greet.zl      # Dynamic terminal welcome dashboard with mini calendar
    │   ├── note.zl       # In-terminal notes & scratchpad manager (alias: jot)
    │   ├── alias.zl      # Alias viewer & manager
    │   └── view.zl       # Styled file inspector (head, tail, linecount, wordcount)
    └── ui/
        ├── prompt.zl     # 2-line prompt with dynamic right-aligned status
        ├── theme.zl      # ANSI theme and styling helpers
        └── completer.zl  # Tab completion engine
```

---

## Building and Running

```bash
# Build standalone native AOT binary
cd zenshell && ../bin/zen build

# Run standalone binary
./bin/zsh

# Run headless test suite
./bin/zsh --test

# Launch via project router
./scripts/zen shell
```
