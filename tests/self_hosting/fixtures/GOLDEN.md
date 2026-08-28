# E3 golden run-vs-bootstrap set

Frozen list of user programs where **selfhost must match bootstrap**.

Machine list: [GOLDEN.txt](GOLDEN.txt) (`path` + `mode`).
Gate: `./scripts/zen test-golden` (`scripts/run_golden.sh`).

## Paths compared

| Path | Bootstrap | Selfhost |
|------|-----------|----------|
| interpret | `python3 bootstrap/Zen.py FILE` | `bin/zen-selfhost interpret FILE` |
| AOT | `python3 bootstrap/Zen.py -g FILE` | `bin/zen-selfhost run FILE` |

Match: exit code **and** normalized stdout (compiler banners / `DEBUG:` / Driver `ran …` stripped).

## Modes

| Mode | Why |
|------|-----|
| `both` | Language-complete on interpret and AST→C |
| `interpret` | Selfhost interpret green; AOT still a known gap (`Default` materialize; `03_scopes` shadowing/`scope`) |
| `aot` | Bootstrap `-g` green; bootstrap interpret is not (`enum_payload`) |

## Not in this freeze

- MATRIX fixtures bootstrap cannot run (`pattern_bind`, `interp_map` map-key identifiers, `with_region`, `multi_main` import path, `enum_payload` interpret)
- `tests/lib/test_*.zl` — needs selfhost interpret of `zen.test` + stdlib depth
- `tests/language/*` using `zen.test`
- `tests/suite/run_all.zl`, `tests/smoke_test.zl`
- Self-rebuild of `selfhost/zen.zl` — opt-in (`ZEN_SELFHOST_REBUILD=1`)

Grow the list when **both** hosts are green on the claimed mode.
