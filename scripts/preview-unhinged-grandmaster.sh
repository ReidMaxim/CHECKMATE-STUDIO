#!/usr/bin/env bash
set -euo pipefail
source_dir=${1:?Pass the extracted approved Mission 005.2 artifact}
output=${2:-out/unhinged-grandmaster}
assets="$output/brand"
master="$source_dir/why-give-up-both-bishops-final-move.mp4"
mkdir -p "$output/preview"
expected=$(jq -er .masterSha256 brand/stockfool/identity.json)
verify_master() { printf '%s  %s\n' "$expected" "$master" | sha256sum -c -; }
verify_master
node scripts/unhinged-grandmaster.mjs "$assets"
for file in "$assets"/*.svg; do
  inkscape "$file" --export-filename="${file%.svg}.png" >/dev/null
done
for form in full-emblem standard-emblem micro-icon; do
  for size in 48 96 256 512 1024; do
    image="$assets/$form-$size.png"
    inkscape "$assets/$form.svg" -w "$size" -h "$size" -o "$image" >/dev/null
    test "$(identify -format '%wx%h:%[opaque]' "$image" | tr '[:upper:]' '[:lower:]')" = "${size}x${size}:false"
  done
done
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
inkscape "$assets/horizontal-lockup.svg" -w 310 -o "$scratch/open.png" >/dev/null
inkscape "$assets/horizontal-lockup.svg" -w 540 -o "$scratch/close.png" >/dev/null
inkscape "$assets/watermark.svg" -w 80 -o "$scratch/watermark.png" >/dev/null
opening=$(jq -er '.scenes[0].frames' "$source_dir/storyboard.json")
closing=$(jq -er '([.scenes[0:-1][].frames]|add)+.scenes[-1].captions[-1].to' "$source_dir/storyboard.json")
ffmpeg -v error -threads 2 -ss 7 -i "$master" -vf 'crop=320:52:88:140' -frames:v 1 -threads 1 "$scratch/clean.png"
video="$output/preview/unhinged-grandmaster-experimental.mp4"
ffmpeg -v error -y -filter_complex_threads 2 -threads 2 -i "$master" -i "$scratch/clean.png" \
  -loop 1 -framerate 30 -i "$scratch/open.png" -i "$scratch/close.png" -i "$scratch/watermark.png" \
  -filter_complex "[2:v]format=rgba,fade=t=in:st=0:d=0.47:alpha=1[reveal];[0:v][1:v]overlay=88:140:enable='lt(n,$opening)'[clean];[clean][reveal]overlay=92:120:enable='lt(n,$opening)':shortest=1[open];[open][3:v]overlay=92:1480:enable='gte(n,$closing)'[close];[close][4:v]overlay=850:136:enable='between(n,$opening,$((closing-1)))'[out]" \
  -map '[out]' -map 0:a:0 -c:v libx264 -threads 4 -preset veryfast -crf 17 -pix_fmt yuv420p -c:a copy -movflags +faststart "$video"
audio_hash() { ffmpeg -v error -i "$1" -map 0:a:0 -c copy -f streamhash -hash sha256 -; }
format() { ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -of csv=p=0 "$1"; }
test "$(audio_hash "$master")" = "$(audio_hash "$video")"
test "$(format "$master")" = "$(format "$video")"
ffmpeg -v error -xerror -threads 2 -i "$video" -f null -
for shot in opening watermark closing; do
  case "$shot" in opening) time=1;; watermark) time=20;; closing) time=53.8;; esac
  ffmpeg -v error -y -ss "$time" -i "$video" -frames:v 1 -threads 1 "$output/preview/$shot.png"
done
{
  verify_master
  printf 'Dimensions, frame rate, frame count: %s\n' "$(format "$video")"
  printf 'Bit-identical AAC stream: %s\n' "$(audio_hash "$video")"
  printf 'Full video and audio decode passed.\n'
} | tee "$output/preview/verification.txt"
