# Zenlang for VS Code / Cursor / Antigravity

Syntax highlighting, snippets, hovers, and bootstrap diagnostics for `.zl` / `.zs` files.

## Install (recommended)

From the **repo root**:

```bash
./scripts/setup_vscode_extension.sh
```

Then **reload the window** in your editor:

- VS Code / Cursor / Antigravity: `Developer: Reload Window`
- Or fully quit and reopen

Open `examples/getting_started/01_hello.zl`. The status bar should show **Zenlang**.

If the file opens as Plain Text:

1. `Ctrl+Shift+P` → **Change Language Mode**
2. Pick **Zenlang**

### Manual symlink

```bash
SRC="$(pwd)/editors/vscode"
NAME=zenlang.zenlang-0.1.0
ln -sfn "$SRC" ~/.vscode/extensions/$NAME
ln -sfn "$SRC" ~/.cursor/extensions/$NAME
ln -sfn "$SRC" ~/.antigravity/extensions/$NAME
ln -sfn "$SRC" ~/.antigravity-ide/extensions/$NAME
```

## Features

| Feature | Notes |
|---------|--------|
| **Syntax** | Keywords, `->` / `<-`, ranges, backtick strings, `/! !/` docs |
| **Snippets** | `main`, `when`, `import`, `fori`, `result`, CLI imports, … |
| **Completions** | Keywords, types, common `zen.*` modules, document words |
| **Hovers** | Operators and core keywords |
| **Diagnostics** | Runs `python3 bootstrap/Zen.py --check <file>` on open/save |
| **Commands** | Typecheck / Run interpret / Run native (`-g`) |

## Settings

| Setting | Default | Meaning |
|---------|---------|---------|
| `zenlang.diagnostics.enabled` | `true` | Enable bootstrap checks |
| `zenlang.diagnostics.onSave` | `true` | Check on save |
| `zenlang.diagnostics.onOpen` | `true` | Check on open |
| `zenlang.bootstrapPath` | `""` | Override path to `Zen.py` |
| `zenlang.pythonPath` | `python3` | Python executable |

Open the **repo root** as the workspace so `bootstrap/Zen.py` is found automatically.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Extension not listed | Run `./scripts/setup_vscode_extension.sh`, reload window |
| `.zl` is Plain Text | Change Language Mode → Zenlang |
| Stale highlighting | Remove old `~/.vscode/extensions/zenlang` if it points at another checkout |
| No diagnostics | Open workspace at repo root; set `zenlang.bootstrapPath` |

## Related

- Zed: `editors/zed/` + `./scripts/setup_zed_extension.sh`
- Tree-sitter: `editors/tree-sitter-zen/`
- Tutorial: `doc/Getting_Started.md`
