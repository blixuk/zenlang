#!/usr/bin/env bash
# Compare interpreter vs native (-g) on the language core set.
# Compares exit codes and normalized stdout (strips compile banners / DEBUG lines).
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
ZEN="${ZEN:-$ROOT/bin/zen}"

CORE=(
  tests/01_primitives.zl
  tests/02_variables.zl
  tests/03_scopes.zl
  tests/04_functions.zl
  tests/05_control_flow.zl
  tests/06_structs.zl
  tests/hello.zl
  tests/smoke_test.zl
  tests/language/pattern_matching_01.zl
  tests/language/pattern_matching_02.zl
  tests/language/error_handling_test_01.zl
  tests/language/range_syntax_01.zl
  tests/language/closure_01.zl
  tests/language/test_extended_operators.zl
  tests/language/test_in_operator.zl
  tests/language/test_intrinsics.zl
)

normalize() {
  # Drop compiler banners, ANSI colors, and leftover DEBUG noise; keep program output.
  # Banner may share a line with program text if the program omitted a trailing newline,
  # so strip the banner as a substring rather than deleting whole matching lines.
  sed -E \
    -e 's/\x1B\[[0-9;]*[A-Za-z]//g' \
    -e 's/Compiled successfully\. Running program://g' \
    -e 's/Running program://g' \
    -e 's/ran output\/build\/.*\(exit [0-9]+\)//g' \
    -e 's/\[INFO\] //g' \
    -e 's/\[ERROR\] //g' \
    -e 's/\[WARN\] //g' \
    -e '/^DEBUG:/d' \
    -e '/^DEBUG /d' \
    -e '/^!!! C COMPILE FAILED/d' \
    | tr -d '\r' \
    | sed -E 's/[[:space:]]+$//' \
    | awk 'NF'
  # Keep only non-empty lines so minor newline/flush differences do not fail parity.
}

fail=0
for f in "${CORE[@]}"; do
  echo "=== parity $f ==="
  i_out="$(mktemp)"
  n_out="$(mktemp)"
  i_err=0
  n_err=0

  set +e
  $ZEN "$f" >"$i_out" 2>&1
  i_err=$?
  $ZEN -g "$f" >"$n_out" 2>&1
  n_err=$?
  set -e

  if [[ "$i_err" -ne 0 ]]; then
    echo "FAIL interpret exit=$i_err: $f"
    cat "$i_out"
    fail=1
    rm -f "$i_out" "$n_out"
    continue
  fi
  if [[ "$n_err" -ne 0 ]]; then
    echo "FAIL native exit=$n_err: $f"
    cat "$n_out"
    fail=1
    rm -f "$i_out" "$n_out"
    continue
  fi

  i_norm="$(normalize <"$i_out")"
  n_norm="$(normalize <"$n_out")"

  if [[ "$i_norm" != "$n_norm" ]]; then
    echo "FAIL output mismatch: $f"
    echo "--- interpret ---"
    printf '%s\n' "$i_norm"
    echo "--- native ---"
    printf '%s\n' "$n_norm"
    fail=1
  else
    echo "OK $f"
  fi
  rm -f "$i_out" "$n_out"
done

if [[ "$fail" -ne 0 ]]; then
  echo "Core parity FAILED"
  exit 1
fi
echo "Core parity PASSED"
