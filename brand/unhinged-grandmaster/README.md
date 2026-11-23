# STOCKFOOL · The Unhinged Grandmaster

Mission 005.3.2 branches from PR #18 so the new asset system sits alongside both the fish identity from PR #17 and the earlier king concepts. The approved Mission 005.2 Lasker–Bauer master remains the source for the experimental edit. Its SHA-256 is checked before and after packaging.

## Artwork and use

| Asset | Use |
| --- | --- |
| Full emblem | Large banners, artwork and thumbnail compositions. The shield, mirrored knights, checker field and collar are all drawn as paths or vector patterns. |
| Standard emblem | Site headers, channel avatars, merchandise and horizontal lockups. Simplified framing and checker work retain the crown, skeptical eye and question mark. |
| Micro icon | 48–96 px icons and small placements. Close crop of the head, with the shield and flanking figures omitted. Use the 256–1024 px exports for high-density icon slots. |
| Horizontal / stacked lockups | Pair custom angular lettering and the secondary tagline with the standard or full emblem. |
| Wordmark / light and dark single-ink variants | Wordmark alone for narrow placements. Single-ink plates for print or controlled backgrounds. |
| Transparent watermark | Reduced-opacity micro emblem for video margins. |
| Palette / avatar | Four approved identity colors and a square channel avatar. |

Ivory `#F6F1E3`, antique gold `#D6B26A`, sage jade `#86A699`, charcoal `#0B120F`. The display lettering is custom vector geometry. The secondary lockup uses Liberation Serif Italic with a Georgia fallback. Use the existing DM Sans caption treatment for documentary copy.

## Comparison and limits

I used the attached concept as the drawing reference and built the vector geometry directly. The full drawing retains the asymmetric eye and question mark, angular gold crown, jade gem, shield, knights and sweeping collar. It simplifies the reference’s carved shading, wrap highlights and ornamental rays into flat facets. The wordmark is custom-drawn in the reference’s angular spirit. Its spacing and outlines differ from the illustration. The 48 px export favors the micro icon. At that size, the crown and question mark carry recognition and the brow reads more clearly than the pupil. The full emblem is best viewed at 256 px or larger.

## Preview and checks

The isolated preview script reuses the frame-referenced overlay approach from PR #17. It fades the horizontal mark into the opening margin, places the micro emblem above the board on the right during the body, and shows the lockup below the board after the final caption. It makes no edits to the storyboard, audio stream or approved master. The experimental video has 1,631 frames at 1080 × 1920 and 30 fps, and its AAC stream is bit-identical to the approved source. Full decode passed. SVG exports were rasterized with Inkscape, and transparency and native pixel dimensions were checked.

Generate vectors with `node scripts/unhinged-grandmaster.mjs <output-folder>`. Run `scripts/preview-unhinged-grandmaster.sh <Mission-005.2-artifact-folder> <output-folder>` for PNGs and the experimental video. Dependencies are Node, Inkscape, ImageMagick, jq and FFmpeg.
