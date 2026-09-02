#!/bin/sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
cd "$ROOT"
python3 "$ROOT/bootstrap/Zen.py" "$ROOT/tools/build_book.zl"
echo "Zenlang Book built successfully via Zen Mark: $DIR/Zen_Book.pdf"

