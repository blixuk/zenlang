#!/usr/bin/env bash
# Run the language core set under the Python bootstrap interpreter.
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
  tests/suite/run_all.zl
  tests/language/error_handling_test_01.zl
  tests/language/pattern_matching_01.zl
  tests/language/pattern_matching_02.zl
  tests/language/ownership_01.zl
  tests/language/range_syntax_01.zl
  tests/language/closure_01.zl
  tests/language/test_extended_operators.zl
  tests/language/test_in_operator.zl
  tests/language/test_type_introspection.zl
  tests/language/default_sentinel_01.zl
  tests/language/collection_methods_01.zl
  tests/language/flow_operators_01.zl
  tests/language/fstring_test_01.zl
  tests/language/sequence_slicing_01.zl
)

fail=0
for f in "${CORE[@]}"; do
  echo "=== interpret $f ==="
  if ! $ZEN "$f"; then
    echo "FAIL: $f"
    fail=1
  fi
done

if [[ "$fail" -ne 0 ]]; then
  echo "Core interpret tests FAILED"
  exit 1
fi
echo "Core interpret tests PASSED"
