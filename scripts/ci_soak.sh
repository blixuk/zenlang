#!/usr/bin/env bash
# Local soak path (E3.5): handoff-soak = selfhost-smoke + hybrid checks + golden.
# Keep this off the fast ci_smoke ladder. No remote CI. Self-rebuild of zen.zl stays opt-in.
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
export ZEN_PATH="${ZEN_PATH:-$ROOT:$ROOT/selfhost:$ROOT/lib}"
export ZEN_SELFHOST_REBUILD="${ZEN_SELFHOST_REBUILD:-0}"

echo "=== zen ci_soak: handoff-soak ==="
echo "ZEN_SELFHOST_REBUILD=$ZEN_SELFHOST_REBUILD"
bash "$ROOT/scripts/handoff_soak.sh"
echo "=== zen ci_soak: PASSED ==="
