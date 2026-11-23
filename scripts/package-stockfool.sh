#!/usr/bin/env bash
set -euo pipefail
source_dir=${1:?Pass the extracted Mission 005.2 artifact folder}
output=${2:-out/stockfool}
master="$source_dir/why-give-up-both-bishops-final-move.mp4"
identity=brand/stockfool/identity.json
assets="$output/brand"
mkdir -p "$output/video" "$output/evidence"
expected=$(jq -er .masterSha256 "$identity")
printf '%s  %s\n' "$expected" "$master" | sha256sum -c -
node scripts/stockfool-assets.mjs "$assets"
for svg in "$assets"/*.svg; do
  inkscape "$svg" --export-filename="${svg%.svg}.png" >/dev/null
done
cp "$master" "$output/video/approved-master.mp4"
cp "$source_dir"/{storyboard,timing,claim-ledger,outcome-review,tts-manifest}.json "$output/evidence/"
cp docs/stockfool.md "$output/STOCKFOOL-release-guide.md"
cp "$identity" "$output/identity.json"
opening_frames=$(jq -er '.scenes[0].frames' "$source_dir/storyboard.json")
closing_frame=$(jq -er '([.scenes[0:-1][].frames]|add)+(.scenes[-1].captions[-1].to)' "$source_dir/storyboard.json")
clip_seconds=$(awk -v frames="$opening_frames" 'BEGIN {print frames / 30}')
read -r open_x open_y < <(jq -r '[.opening.x,.opening.y]|@tsv' "$identity")
read -r close_x close_y < <(jq -r '[.closing.x,.closing.y]|@tsv' "$identity")
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
# The board and camera do not affect the static top margin. Sample it after
# the archived opening wordmark disappears and replace only that rectangle.
ffmpeg -nostdin -v error -threads 2 -ss 7 -i "$master" -vf 'crop=320:52:88:140' -frames:v 1 -threads 1 "$scratch/clean-margin.png"
clean="[0:v][1:v]overlay=88:140:enable='lt(n,$opening_frames)'"
encode() {
  local output_name=$1 graph=$2
  shift 2
  ffmpeg -nostdin -v error -filter_complex_threads 2 -threads 2 -i "$master" -i "$scratch/clean-margin.png" "$@" \
    -filter_complex "$graph[out]" -map '[out]' -map 0:a:0 -t "$clip_seconds" \
    -c:v libx264 -threads 4 -preset veryfast -crf 17 -pix_fmt yuv420p -c:a copy -movflags +faststart \
    "$output/video/$output_name.mp4"
}
encode opening-a-control "$clean"
encode opening-b-wordmark "$clean[clean];[clean][2:v]overlay=$open_x:$open_y:enable='lt(n,$opening_frames)'" \
  -i "$assets/opening-minimal.png"
encode opening-c-mascot "$clean[clean];[clean][2:v]overlay=$open_x:$open_y:enable='lt(n,$opening_frames)'" \
  -i "$assets/opening-mascot.png"
ffmpeg -nostdin -v error -filter_complex_threads 2 -threads 2 -i "$master" -i "$scratch/clean-margin.png" \
  -i "$assets/opening-minimal.png" -i "$assets/closing-lockup.png" \
  -filter_complex "$clean[clean];[clean][2:v]overlay=$open_x:$open_y:enable='lt(n,$opening_frames)'[open];[open][3:v]overlay=$close_x:$close_y:enable='gte(n,$closing_frame)'[out]" \
  -map '[out]' -map 0:a:0 -c:v libx264 -threads 4 -preset veryfast -crf 17 -pix_fmt yuv420p -c:a copy -movflags +faststart \
  "$output/video/stockfool-release-cut.mp4"
ffmpeg -nostdin -v error -ss 50 -i "$output/video/stockfool-release-cut.mp4" -c copy -movflags +faststart "$output/video/closing-treatment.mp4"
ffmpeg -nostdin -v error -sseof -0.4 -i "$output/video/stockfool-release-cut.mp4" -frames:v 1 -threads 1 "$output/branded-closing-frame.png"
audio_hash() { ffmpeg -nostdin -v error -i "$1" -map 0:a:0 -c copy -f streamhash -hash sha256 -; }
release="$output/video/stockfool-release-cut.mp4"
test "$(audio_hash "$master")" = "$(audio_hash "$release")"
frames() { ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of csv=p=0 "$1"; }
test "$(frames "$master")" = "$(frames "$release")"
for movie in "$output"/video/*.mp4; do
  ffmpeg -nostdin -v error -xerror -threads 2 -i "$movie" -f null -
done
{
  printf 'Approved master SHA-256: %s\n' "$expected"
  printf 'Bit-identical encoded audio stream: %s\n' "$(audio_hash "$release")"
  printf 'Master and release video frames: %s\n' "$(frames "$release")"
  printf 'Opening overlay frames: 0–%s\n' "$((opening_frames-1))"
  printf 'Closing overlay starts at frame: %s, after the final caption\n' "$closing_frame"
  printf 'All video outputs passed complete decode.\n'
} | tee "$output/evidence/package-verification.txt"
