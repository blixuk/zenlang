#!/bin/sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"
cd "$DIR"
typst compile --root "$ROOT" ./Zen_Book.typ Zen_Book.pdf
echo "Zenlang Book built successfully: $DIR/Zen_Book.pdf"
