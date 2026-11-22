#!/usr/bin/env bash
set -euo pipefail
root="${1:-.cache/signature-models}"
mkdir -p "$root"
get() {
  local name="$1" hash="$2" url="$3"
  if [[ -s "$root/$name" ]] && echo "$hash  $root/$name" | sha256sum --check --status; then
    return
  fi
  curl -fLsS --retry 2 --max-time 180 "$url" -o "$root/$name.part"
  echo "$hash  $root/$name.part" | sha256sum --check --status
  mv "$root/$name.part" "$root/$name"
}
pocket='https://huggingface.co/kyutai/pocket-tts-without-voice-cloning/resolve/d29db7978e464fb90cb3359ee0c69a273b9142cc/languages/english'
get model.safetensors be9c6b4876d3f30740a8225dfcaa2e43dc4aeb753c15272735bee16bbb4abb0a "$pocket/model.safetensors?download=true"
get tokenizer.model d461765ae179566678c93091c5fa6f2984c31bbe990bf1aa62d92c64d91bc3f6 "$pocket/tokenizer.model?download=true"
get alba.safetensors e4a323e8e771f14fd669428d83e7af6d83b4d6d0f0e282c30122f04824f17b1c "$pocket/embeddings/alba.safetensors?download=true"
get anna.safetensors 87e1922e9d1bfb27728ae4f1ea89bc3174e17a9f819ce0a728cfbea19517d9c7 "$pocket/embeddings/anna.safetensors?download=true"
get vosk.zip 30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498 "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
unzip -oq "$root/vosk.zip" -d "$root"
if [[ "${2:-}" == "--casting" ]]; then
  while IFS=$'\t' read -r voice hash; do
    get "$voice.safetensors" "$hash" "$pocket/embeddings/$voice.safetensors?download=true"
  done < <(python -c 'import json; from pathlib import Path; [print(name, item["sha256"], sep="\t") for name, item in json.loads(Path("examples/signature/casting-profiles.json").read_text()).items()]')
fi
