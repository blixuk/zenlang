#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if (($# > 0)); then
  echo "tests/lib/run_all.sh currently supports interpreter mode only." >&2
  echo "The generated path still hits existing transpiler gaps in stdlib-heavy programs." >&2
  exit 2
fi

TEST_FILES=(
  tests/lib/test_bytes.zl
  tests/lib/test_cli.zl
  tests/lib/test_collections.zl
  tests/lib/test_core.zl
  tests/lib/test_error.zl
  tests/lib/test_file.zl
  tests/lib/test_geometry.zl
  tests/lib/test_io.zl
  tests/lib/test_json.zl
  tests/lib/test_list.zl
  tests/lib/test_math.zl
  tests/lib/test_memory.zl
  tests/lib/test_path.zl
  tests/lib/test_process.zl
  tests/lib/test_random.zl
  tests/lib/test_range.zl
  tests/lib/test_string.zl
  tests/lib/test_sys.zl
  tests/lib/test_term.zl
  tests/lib/test_test.zl
  tests/lib/test_text.zl
  tests/lib/test_time.zl
  tests/lib/test_ui_extra.zl
  tests/lib/test_ui_table.zl
  tests/lib/test_ui_spinner.zl
  tests/lib/test_text_extra2.zl
  tests/lib/test_collections_math_extra.zl
  tests/lib/test_crypto_jwt_cron.zl
  tests/lib/test_data_extra2.zl
  tests/lib/test_net_extra.zl
  tests/lib/test_test_bench_extra.zl
  tests/lib/test_concurrency.zl
  tests/lib/test_profile.zl
  tests/lib/test_lorem.zl
  tests/lib/test_color.zl
  tests/lib/test_zendata.zl
  tests/lib/test_zencode.zl
  tests/lib/test_zenmark.zl
  tests/lib/test_pdf.zl
  tests/lib/test_http.zl
  tests/lib/test_url.zl
  tests/lib/test_rainbow_brackets.zl
  tests/lib/test_trie.zl
  tests/lib/test_crypto_ciphers.zl
  tests/lib/test_qrcode.zl
  tests/lib/test_deflate_gzip.zl
  tests/lib/test_zip.zl
  tests/lib/test_zar.zl
)

echo "===================================="
echo "      ZEN LIBRARY TEST SUITE        "
echo "===================================="
echo

ZEN="${ZEN:-$ROOT_DIR/bin/zen}"

for test_file in "${TEST_FILES[@]}"; do
  echo ">>> $test_file"
  $ZEN "$test_file"
  echo
done

echo "===================================="
echo "   ALL LIBRARY TESTS PASSED         "
echo "===================================="
