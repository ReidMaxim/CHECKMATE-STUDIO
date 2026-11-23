# STOCKFOOL · Artwork integration

The artwork source is [Stockfool: Questionable Moves.png](https://chatgpt.com/library?file_id=libfile_fb750c21d0e481919ea191283378dbe2&account_id=personal), 1536 × 1024. This branch builds on PR #19; PRs #17 through #19 retain their previous assets. The export package contains a bit-for-bit original and a clean sRGB PNG with metadata stripped. Its approved SHA-256 is checked by the export script. The artwork itself remains in the release bundle and source file rather than in Git.

## Assets for review

- **Avatar context** keeps more of the shoulders and chess pattern. **Avatar close** foregrounds the crown, face and question mark. Both have feathered crop variants on transparent canvases.
- **Micro icon** uses a tighter crop without lettering, at a reduced size. No facial details were redrawn. Review samples at 48, 96 and 256 px use the same native resolutions.
- **Channel lockup and banner** pair the close crop with the artwork’s original STOCKFOOL lettering and tagline. The banner keeps the lockup in the central band.
- **Vertical cover** uses the full artwork and a separate episode title.
- **Documentary A** previews the lettering-only opening. **Documentary B** previews the art lockup over the existing opening, a small corner mark, and closing branding after the final caption. Both are review exports.
- The interior dark tones belong to the illustration. The transparent variants feather only the perimeter of the crop to protect those tones. The master is raster. A faithful editable vector was not produced.

Run `scripts/stockfool-artwork.sh <approved-PNG>` with ImageMagick, then `scripts/preview-stockfool-artwork.sh <Mission-005.2-artifact-directory>` with FFmpeg and jq. The full preview checks the approved video SHA-256 before and after, copies its AAC stream without encoding, and compares dimensions, frame rate and frame count. The working branch is for review only.
