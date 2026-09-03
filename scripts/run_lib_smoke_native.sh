#!/usr/bin/env bash
# Native (-g) smoke for a stdlib subset that currently transpiles cleanly.
# Full tests/lib/run_all.sh remains interpreter-only.
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
ZEN="${ZEN:-$ROOT/bin/zen}"

# Subset of tests/lib that compiles and passes under -g.
# Prefer adding modules used by demos / Unix tooling when they go green.
SMOKE=(
  tests/lib/test_core.zl
  tests/lib/test_string.zl
  tests/lib/test_math.zl
  tests/lib/test_list.zl
  tests/lib/test_collections.zl
  tests/lib/test_range.zl
  tests/lib/test_error.zl
  tests/lib/test_test.zl
  tests/lib/test_sys.zl
  tests/lib/test_cli.zl
  tests/lib/test_io.zl
  tests/lib/test_file.zl
  tests/lib/test_path.zl
  tests/lib/test_csv.zl
  tests/lib/test_json.zl
  tests/lib/test_log.zl
  tests/lib/test_time.zl
  tests/lib/test_term.zl
  tests/lib/test_process.zl
  tests/lib/test_http.zl
  tests/lib/test_url.zl
  tests/lib/test_random.zl
  tests/lib/test_geometry.zl
  tests/lib/test_text.zl
  # Graphics / patterns / text extras (already -g green)
  tests/lib/test_bmp.zl
  tests/lib/test_ppm.zl
  tests/lib/test_columns.zl
  tests/lib/test_markdown.zl
  tests/lib/test_fsm.zl
  tests/lib/test_awk.zl
  tests/lib/test_term_keys.zl
  tests/lib/test_regex.zl
  tests/lib/test_memory.zl
  tests/lib/test_xml.zl
  tests/lib/test_data_extra.zl
  tests/lib/test_database.zl
  tests/lib/test_ecs.zl
  tests/lib/test_bytes.zl
  # Data / UI extras (rewritten dual-path)
  tests/lib/test_logfmt.zl
  tests/lib/test_sexp.zl
  tests/lib/test_serialize.zl
  tests/lib/test_canvas.zl
  tests/lib/test_layout.zl
  tests/lib/test_ui_app.zl
  tests/lib/test_ui_widget.zl
  tests/lib/test_zenmark.zl
  tests/lib/test_reflect.zl
  tests/lib/test_reflectable.zl
  tests/lib/test_reflect_call.zl
  tests/lib/test_crypto_extra.zl
  tests/lib/test_net_extra.zl
  tests/lib/test_text_extra.zl
  tests/lib/test_html.zl
  tests/lib/test_ui_extra.zl
  tests/lib/test_text_extra2.zl
  tests/lib/test_collections_math_extra.zl
  tests/lib/test_crypto_jwt_cron.zl
  tests/lib/test_data_extra2.zl
  tests/lib/test_test_bench_extra.zl
  tests/lib/test_concurrency.zl
  tests/lib/test_profile.zl
)

fail=0
for f in "${SMOKE[@]}"; do
  echo "=== native smoke $f ==="
  set +e
  out="$($ZEN -g "$f" 2>&1)"
  code=$?
  set -e
  if [[ "$code" -ne 0 ]]; then
    echo "FAIL exit=$code: $f"
    printf '%s\n' "$out"
    fail=1
    continue
  fi
  if printf '%s\n' "$out" | grep -Eq 'C COMPILE FAILED|Traceback|Type check failed'; then
    echo "FAIL diagnostics: $f"
    printf '%s\n' "$out"
    fail=1
    continue
  fi
  if ! printf '%s\n' "$out" | grep -Eq '\[PASS\]|PASS'; then
    echo "FAIL no PASS markers: $f"
    printf '%s\n' "$out"
    fail=1
    continue
  fi
  if printf '%s\n' "$out" | grep -Eq '\[FAIL\]'; then
    echo "FAIL reported: $f"
    printf '%s\n' "$out"
    fail=1
    continue
  fi
  echo "OK $f"
done

if [[ "$fail" -ne 0 ]]; then
  echo "Native lib smoke FAILED"
  exit 1
fi
echo "Native lib smoke PASSED"
