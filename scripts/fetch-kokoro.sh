#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
directory=.cache/kokoro
mkdir -p "$directory"
download() {
  local filename="$1" digest="$2" asset="$3"
  local target="$directory/$filename"
  if [[ -f "$target" ]] && echo "$digest  $target" | sha256sum --check --status; then
    return
  fi
  local release="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
  if ! curl -fLsS --retry 1 --connect-timeout 8 --max-time 90 "$release/$filename" -o "$target.part"; then
    local auth=()
    if [[ -n "${KOKORO_DOWNLOAD_TOKEN:-}" ]]; then
      auth=(-H "Authorization: Bearer $KOKORO_DOWNLOAD_TOKEN")
    fi
    curl -fLsS --retry 1 --connect-timeout 8 --max-time 90 -H 'Accept: application/octet-stream' "${auth[@]}" \
      "https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/assets/$asset" -o "$target.part"
  fi
  echo "$digest  $target.part" | sha256sum --check
  mv "$target.part" "$target"
}
if [[ "${1:-}" == "--fp32" ]]; then
  download kokoro-v1.0.onnx 7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5 224414194
else
  download kokoro-v1.0.int8.onnx 6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb 224416159
fi
download voices-v1.0.bin bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d 227558528
