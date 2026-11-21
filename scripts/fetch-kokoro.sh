#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
directory=.cache/kokoro
mkdir -p "$directory"
download() {
  local filename="$1" digest="$2" asset="$3"
  local target="$directory/$filename"
  if echo "$digest  $target" | sha256sum --check --status; then
    return
  fi
  curl -fLsS --retry 2 --connect-timeout 8 --max-time 120 -H 'Accept: application/octet-stream' \
    "https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/assets/$asset" -o "$target.part"
  echo "$digest  $target.part" | sha256sum --check
  mv "$target.part" "$target"
}
download kokoro-v1.0.int8.onnx 6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb 224416159
download voices-v1.0.bin bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d 227558528
