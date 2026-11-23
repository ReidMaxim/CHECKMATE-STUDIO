#!/usr/bin/env bash
set -euo pipefail
source_dir=${1:?Pass the Mission 005.2 artifact directory}
out=${2:-out/stockfool-artwork}
master="$source_dir/why-give-up-both-bishops-final-move.mp4"
expected=$(jq -er .masterSha256 brand/stockfool/identity.json)
verify_master() { printf '%s  %s\n' "$expected" "$master" | sha256sum -c -; }
verify_master
mkdir -p "$out/video"
temp=$(mktemp -d)
trap 'rm -rf "$temp"' EXIT
assets="$out/assets"
convert "$assets/original-lettering.png" -resize 230x "$temp/open-a.png"
convert "$assets/channel-lockup.png" -resize 350x "$temp/open-b.png"
convert "$assets/channel-lockup.png" -resize 520x "$temp/close.png"
convert "$assets/micro-icon.png" -resize 84x -channel A -evaluate multiply .58 +channel "$temp/micro.png"
ffmpeg -v error -threads 2 -ss 7 -i "$master" -vf 'crop=320:52:88:140' -frames:v 1 -threads 1 "$temp/blank.png"
opening=$(jq -er '.scenes[0].frames' "$source_dir/storyboard.json")
closing=$(jq -er '([.scenes[0:-1][].frames]|add)+.scenes[-1].captions[-1].to' "$source_dir/storyboard.json")
base="[0:v][1:v]overlay=88:140:enable='lt(n,$opening)'[clean]"
render() {
  local name=$1 graph=$2
  shift 2
  ffmpeg -v error -y -filter_complex_threads 2 -threads 2 -i "$master" -i "$temp/blank.png" "$@" \
    -filter_complex "$base;$graph" -map '[out]' -map 0:a:0 -c:v libx264 -threads 4 -preset veryfast -crf 17 \
    -pix_fmt yuv420p -c:a copy -movflags +faststart "$out/video/$name.mp4"
}
# A is an opening comparison only. B is a separate full documentary preview.
render a-lettering-opening '[clean][2:v]overlay=92:134[out]' -i "$temp/open-a.png" -t 6
render b-artwork-documentary "[clean][2:v]overlay=92:115:enable='lt(n,$opening)'[opening];[opening][3:v]overlay=92:1480:enable='gte(n,$closing)'[closing];[closing][4:v]overlay=850:133:enable='between(n,$opening,$((closing-1)))'[out]" \
  -i "$temp/open-b.png" -i "$temp/close.png" -i "$temp/micro.png"
audio() { ffmpeg -v error -i "$1" -map 0:a:0 -c copy -f streamhash -hash sha256 -; }
format() { ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -of csv=p=0 "$1"; }
video="$out/video/b-artwork-documentary.mp4"
test "$(audio "$master")" = "$(audio "$video")"
test "$(format "$master")" = "$(format "$video")"
for movie in "$out"/video/*.mp4; do
  ffmpeg -v error -xerror -threads 2 -i "$movie" -f null -
done
for shot in opening-a opening-b corner closing; do
  name=b-artwork-documentary
  case "$shot" in
    opening-a) t=1; name=a-lettering-opening;;
    opening-b) t=1;;
    corner) t=20;;
    closing) t=53.8;;
  esac
  ffmpeg -v error -y -ss "$t" -i "$out/video/$name.mp4" -frames:v 1 -vf scale=270:480 -threads 1 "$temp/$shot.png"
done
montage "$temp"/{opening-a,opening-b,corner,closing}.png -tile 2x2 -geometry +8+8 -background '#04140F' "$out/review/documentary-comparison.png"
{
  verify_master
  printf 'Preview format: %s\n' "$(format "$video")"
  printf 'Bit-identical AAC: %s\n' "$(audio "$video")"
  printf 'Both preview files passed full decode.\n'
} | tee "$out/video/verification.txt"
