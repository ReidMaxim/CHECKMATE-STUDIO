#!/usr/bin/env bash
set -euo pipefail
input=${1:?Pass the extracted Mission 005.2 artifact}
out=${2:-out/royal-treatment}
source=brand/royal-treatment/approved-brand-board.jpeg
master="$input/why-give-up-both-bishops-final-move.mp4"
assets="$out/assets"
mkdir -p "$assets" "$out/review"
verify() {
  printf '%s  %s\n' 4da7b7f2f132cac91a3466e19646e0e56c8603b7b21f7edcf63c182f945acb43 "$source" \
    "$(jq -er .masterSha256 brand/stockfool/identity.json)" "$master" | sha256sum -c -
}
verify
cp "$source" "$out/approved-brand-board.jpeg"
cp brand/royal-treatment/README.md "$out/README.md"
crop() { convert "$source" -crop "$1" +repage -strip "$assets/$2.png"; }
crop 620x482+312+11 channel-emblem
# Exclude only the neighboring wordmark fragments at the bottom corners.
convert "$assets/channel-emblem.png" \
  \( -size 620x482 xc:white -fill black -draw 'polygon 0,455 85,481 0,481 polygon 619,449 540,481 619,481' \) \
  -alpha off -compose CopyOpacity -composite "$assets/channel-emblem-transparent.png"
convert "$assets/channel-emblem-transparent.png" -background '#0B120F' -alpha remove -alpha off "$assets/channel-emblem.png"
crop 596x142+613+801 wordmark-and-tagline
crop 773x208+440+772 closing-lockup
crop 596x119+613+801 opening-wordmark
convert "$source" -crop 215x215+107+777 +repage -resize 512x512 "$assets/avatar.png"
# Keep dark interior pixels. Only the outer corners become transparent.
convert "$assets/avatar.png" \( -size 512x512 xc:black -fill white -draw 'roundrectangle 2,2 509,509 94,94' \) \
  -alpha off -compose CopyOpacity -composite "$assets/avatar-transparent.png"
convert "$assets/closing-lockup.png" -resize 1270x -background '#0B120F' -gravity center \
  -extent 2560x1440 "$assets/youtube-banner.png"
convert "$assets/opening-wordmark.png" -resize 245x "$assets/video-opening.png"
convert "$assets/closing-lockup.png" -resize 515x "$assets/video-closing.png"
convert "$assets/avatar-transparent.png" -resize 88x -channel A -evaluate multiply .64 +channel "$assets/video-watermark.png"
for size in 48 96 256 512; do
  convert "$assets/avatar-transparent.png" -resize "${size}x${size}" "$out/review/avatar-$size.png"
  convert "$out/review/avatar-$size.png" -channel A -evaluate multiply .64 +channel "$out/review/watermark-$size.png"
  for kind in avatar watermark; do
    test "$(identify -format '%wx%h' "$out/review/$kind-$size.png")" = "${size}x${size}"
  done
done
montage "$out"/review/avatar-{48,96,256,512}.png "$out"/review/watermark-{48,96,256,512}.png \
  -font Liberation-Sans -set label '%f' -tile 4x2 -geometry +12+12 -background '#0B120F' -fill '#F6F1E3' "$out/review/size-comparison.png"
cover() {
  local art=$1 bg=$2 line1=$3 line2=$4 filename=$5
  convert -size 1080x1920 gradient:"$bg" \
    \( "$assets/$art.png" -resize 800x \) -gravity center -geometry +0-30 -composite \
    -gravity north -font Liberation-Serif-Bold -fill '#F6F1E3' -pointsize 91 \
    -annotate +0+290 "$line1" -annotate +0+391 "$line2" \
    \( "$assets/wordmark-and-tagline.png" -resize 530x \) -geometry +0+1430 -composite \
    -font Liberation-Sans -fill '#D6B26A' -pointsize 33 -annotate +0+1655 'LASKER / BAUER    •    AMSTERDAM 1889' "$assets/$filename.png"
}
cover channel-emblem '#102C23-#0B120F' 'Why Give Up' 'Both Bishops?' cover-documentary
cover avatar-transparent '#233E32-#0B120F' 'Two Pawns.' 'Two Bishops.' cover-royal
montage "$assets"/cover-{documentary,royal}.png -tile 2x1 -geometry 320x569+8+8 -background '#0B120F' "$out/review/cover-comparison.png"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
ffmpeg -v error -ss 7 -i "$master" -vf 'crop=320:52:88:140' -frames:v 1 -threads 1 "$tmp/clean.png"
opening=$(jq -er '.scenes[0].frames' "$input/storyboard.json")
close=$(jq -er '([.scenes[0:-1][].frames]|add)+.scenes[-1].captions[-1].to' "$input/storyboard.json")
video="$out/royal-treatment-preview.mp4"
ffmpeg -v error -y -filter_complex_threads 2 -threads 2 -i "$master" -i "$tmp/clean.png" \
  -i "$assets/video-opening.png" -i "$assets/video-closing.png" -i "$assets/video-watermark.png" \
  -filter_complex "[0:v][1:v]overlay=88:140:enable='lt(n,$opening)'[clean];[clean][2:v]overlay=92:139:enable='lt(n,$opening)'[open];[open][3:v]overlay=92:1480:enable='gte(n,$close)'[end];[end][4:v]overlay=850:125:enable='between(n,$opening,$((close-1)))'[out]" \
  -map '[out]' -map 0:a:0 -c:v libx264 -threads 4 -preset veryfast -crf 17 -pix_fmt yuv420p -c:a copy -movflags +faststart "$video"
audio() { ffmpeg -v error -i "$1" -map 0:a:0 -c copy -f streamhash -hash sha256 -; }
format() { ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -of csv=p=0 "$1"; }
test "$(audio "$master")" = "$(audio "$video")"
test "$(format "$master")" = "$(format "$video")"
ffmpeg -v error -xerror -threads 2 -i "$video" -f null -
for stamp in 1 20 53.8; do
  ffmpeg -v error -ss "$stamp" -i "$video" -frames:v 1 -vf scale=270:480 -threads 1 "$tmp/$stamp.png"
done
montage "$tmp"/{1,20,53.8}.png -tile 3x1 -geometry +8+8 -background '#0B120F' "$out/review/film-placements.png"
{
  verify
  cmp "$source" "$out/approved-brand-board.jpeg"
  printf 'Video format: %s\nBit-identical AAC: %s\nComplete preview decode passed.\n' "$(format "$video")" "$(audio "$video")"
} | tee "$out/verification.txt"
