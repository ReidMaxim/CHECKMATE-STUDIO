#!/usr/bin/env bash
set -euo pipefail
output=${1:-out/questionable-king}
node scripts/questionable-king.mjs "$output"
for source in "$output"/*.svg; do
  name=${source%.svg}
  inkscape "$source" --export-filename="$name.png"
  case "$name" in
    */confused-king|*/king-of-questions|*/questionable-king)
      for size in 48 96 256; do
        small="$name-$size.png"
        inkscape "$source" --export-width="$size" --export-height="$size" --export-filename="$small"
        test "$(identify -format '%wx%h:%[opaque]' "$small" | tr '[:upper:]' '[:lower:]')" = "${size}x${size}:false"
      done
      ;;
  esac
done

marks=(confused-king king-of-questions questionable-king)
small=(-size 1000x548 xc:'#101A16' -font Liberation-Sans -fill '#F7EFDD' -pointsize 26 -annotate +30+45 'STOCKFOOL / NATIVE SIZE')
for i in "${!marks[@]}"; do
  x=$((236+250*i))
  name=${marks[i]//-/ }
  small+=(-pointsize 20 -annotate "+$((x+9))+86" "$name")
done
for size in 48 96 256; do
  case $size in
    48) y=104 ;;
    96) y=170 ;;
    256) y=278 ;;
  esac
  small+=(-pointsize 20 -annotate "+30+$((y+26))" "${size} × ${size} px")
  for i in "${!marks[@]}"; do
    x=$((356+218*i-size/2))
    small+=("$output/${marks[i]}-$size.png" -geometry "+$x+$y" -composite)
  done
done
convert "${small[@]}" "$output/small-size-comparison.png"
for format in avatar banner lockup; do
  files=()
  for mark in "${marks[@]}"; do files+=("$output/$mark-$format.png"); done
  case $format in
    avatar) geometry=340x340+7+7; tile=3x1 ;;
    banner) geometry=940x529+0+6; tile=1x3 ;;
    lockup) geometry=690x155+12+8; tile=1x3 ;;
  esac
  montage "${files[@]}" -tile "$tile" -geometry "$geometry" -background '#101A16' "$output/$format-comparison.png"
done
