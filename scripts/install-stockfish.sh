#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
target=.cache/stockfish/stockfish
archive=stockfish-ubuntu-x86-64.tar
archive_sha=4dafdd04f71e70755a327b5be258937b281e60ba87bc0a5801399908240d4a73
binary_sha=4e7507c0b1d3a3020e16b212101c0ba8c8cbff5ea87764bd56301c7d53bfa10c
if [[ -x "$target" ]] && echo "$binary_sha  $target" | sha256sum --check --status; then
  exit 0
fi
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
curl -fsSL --retry 2 --connect-timeout 10 --max-time 120 \
  "https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/$archive" -o "$temporary/$archive"
echo "$archive_sha  $temporary/$archive" | sha256sum --check
tar -xf "$temporary/$archive" -C "$temporary" stockfish/stockfish-ubuntu-x86-64
echo "$binary_sha  $temporary/stockfish/stockfish-ubuntu-x86-64" | sha256sum --check
install -Dm755 "$temporary/stockfish/stockfish-ubuntu-x86-64" "$target"
"$target" --version
