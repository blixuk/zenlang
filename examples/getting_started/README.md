# Getting Started examples

Runnable companion to [doc/Getting_Started.md](../../doc/Getting_Started.md).

Work through them in order. Each file has a `/! ... !/` header with the run command.

## Run all (interpret)

From the **repo root**:

```bash
./scripts/zen install   # once
export ZEN_PATH="${ZEN_PATH:-$PWD:$PWD/selfhost:$PWD/lib}"

for f in examples/getting_started/[0-9]*.zl; do
  echo "=== $f ==="
  ./bin/zen "$f" || python3 bootstrap/Zen.py "$f"
done
```

Optional native check on a few:

```bash
./bin/zen -g examples/getting_started/01_hello.zl
./bin/zen -g examples/getting_started/04_functions.zl
./bin/zen -g examples/getting_started/10_count_lines.zl examples/getting_started/README.md
```

## Map to the tutorial

| File | Tutorial focus |
|------|----------------|
| `01_hello.zl` | Install & run, `main`, backticks, `io` |
| `02_variables.zl` | `let` / `set` / `->` / `nothing` |
| `03_control_flow.zl` | `when` / `or`, `do while`, ranges |
| `04_functions.zl` | `function`, `<-` return, recursion |
| `05_collections.zl` | lists, maps, indexing |
| `06_strings.zl` | `zen.text.string` (`Str.*`) |
| `07_structures.zl` | `structure` types |
| `08_closures.zl` | lambdas, by-value capture |
| `09_cli_args.zl` | `Sys.get_args()`, early exit |
| `10_count_lines.zl` | file I/O CLI tool |
| `11_process.zl` | shell composition |
| `12_patterns.zl` | result maps, rebind, index loops |

## Next

- Unix cookbook demos: `examples/zcat.zl`, `zedit.zl`, `shell_script.zl`
- Full guide: `doc/Getting_Started.md`
