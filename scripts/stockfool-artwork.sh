#!/usr/bin/env bash
set -euo pipefail
source=${1:?Pass the approved 1536x1024 STOCKFOOL PNG}
out=${2:-out/stockfool-artwork}
palette='#04140F'
mkdir -p "$out"/{master,assets,review}
printf '%s  %s\n' 9e3b11be279de16ffd1f74d63511c49f66f0b59cce54bb86f6783d4db79e1c8e "$source" | sha256sum -c -
cp "$source" "$out/master/original.png"
convert "$source" -colorspace sRGB -alpha off -strip PNG24:"$out/master/clean-master.png"
# Keep the original painted background wherever the illustration meets it.
# Soft masks only feather the perimeter of deliberate crops.
crop_avatar() {
  local crop=$1 name=$2
  convert "$source" -crop "$crop" +repage -resize 736x736 -background "$palette" -gravity center -extent 800x800 \
    \( -size 800x800 xc:black -fill white -draw 'roundrectangle 16,16 783,783 125,125' -blur 0x12 -gravity center \) \
    -alpha off -compose CopyOpacity -composite +gravity "$out/assets/$name-transparent.png"
  convert "$out/assets/$name-transparent.png" -background "$palette" -alpha remove -alpha off "$out/assets/$name.png"
}
crop_avatar 680x680+425+0 avatar-context
crop_avatar 510x510+505+0 avatar-close
crop_avatar 455x455+535+0 micro-crop
convert "$out/assets/micro-crop-transparent.png" -resize 512x512 "$out/assets/micro-icon.png"
rm "$out/assets/micro-crop.png" "$out/assets/micro-crop-transparent.png"
for variant in avatar-context avatar-close micro-icon; do
  for pixels in 48 96 256; do
    convert "$out/assets/$variant.png" -resize "${pixels}x${pixels}" "$out/review/$variant-$pixels.png"
    test "$(identify -format '%wx%h' "$out/review/$variant-$pixels.png")" = "${pixels}x${pixels}"
  done
done
convert "$source" -crop 1220x245+150+716 +repage -resize 900x -fill "#04140F" -draw "rectangle 128,0 777,13" "$out/assets/original-lettering.png"
convert -size 1510x340 xc:"$palette" \
  \( "$out/assets/avatar-close-transparent.png" -resize 326x326 \) -geometry +48+7 -composite \
  "$out/assets/original-lettering.png" -geometry +433+78 -composite "$out/assets/channel-lockup.png"
convert -size 2560x1440 xc:"$palette" \
  "$out/assets/channel-lockup.png" -geometry +525+550 -composite "$out/assets/youtube-banner.png"
convert -size 1080x1920 gradient:'#102B22-#04140F' \
  \( "$source" -resize 1080x \) -geometry +0+610 -composite \
  -font Liberation-Serif -fill '#F6F1E3' -pointsize 71 -gravity North -annotate +0+375 'Why Give Up Both Bishops?' \
  -fill '#D6B26A' -pointsize 38 -annotate +0+1400 'LASKER / BAUER  ·  AMSTERDAM 1889' "$out/assets/lasker-bauer-cover.png"
marks=(avatar-context avatar-close micro-icon)
small=(-size 1040x440 xc:"$palette" -font Liberation-Sans -fill '#F6F1E3' -pointsize 25 -annotate +26+40 'STOCKFOOL / NATIVE SIZE')
for i in "${!marks[@]}"; do
  center=$((285+286*i))
  small+=(-pointsize 21 -annotate "+$((center-83))+78" "${marks[i]//-/ }")
  for pixels in 48 96 256; do
    case $pixels in 48) y=96;; 96) y=154;; 256) y=251;; esac
    # The large view is provided at full size on the separate crop comparison.
    if [[ "$pixels" == 256 ]]; then continue; fi
    small+=("$out/review/${marks[i]}-$pixels.png" -geometry "+$((center-pixels/2))+$y" -composite)
  done
  small+=(\( "$out/review/${marks[i]}-256.png" -resize 170x170 \) -geometry "+$((center-85))+260" -composite)
done
convert "${small[@]}" "$out/review/48-96-comparison.png"
montage "$out"/review/{avatar-context,avatar-close,micro-icon}-256.png -tile 3x1 -geometry +16+12 -background "$palette" "$out/review/256-crop-comparison.png"
convert "$out/assets/channel-lockup.png" -resize 740x -gravity center -background "$palette" -extent 770x190 "$out/review/lockup-preview.png"
convert "$out/assets/youtube-banner.png" -resize 770x "$out/review/banner-preview.png"
montage "$out"/review/{lockup-preview,banner-preview}.png -tile 1x2 -geometry +0+8 -background "$palette" "$out/review/channel-layouts.png"
cmp "$source" "$out/master/original.png"
