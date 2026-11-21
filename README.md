# CHECKMATE//STUDIO

Mission 001 builds a screening room and a frame-driven chess film renderer. The sample, **A queen for a king**, runs 41 seconds. It follows one published Légal mate continuation with 4…g6. Edward Winter's Chess Notes 5720 records variant accounts and a rook-odds tradition. For the tactical demonstration, the PGN uses a standard starting position and the published move sequence. The source does not establish a definitive historical game score.

## Review from a phone

Open the dashboard in mobile Safari after an approved Pages deployment. Tap a storyboard shot to seek the preview. Board flip and test narration are preview controls. The export uses the orientation and audio in the storyboard.

In GitHub Actions, open **Test and render sample**, select the feature-branch run, then download **sample-video** from Artifacts. The ZIP contains the MP4 and can be expanded in Files on iPhone. Sample video artifacts are retained for 30 days. Feature-branch pushes start a run. GitHub makes the manual **Run workflow** control available after the workflow exists on the default branch.

For an approved deployment, configure Pages to use GitHub Actions and dispatch **Publish approved dashboard** on `main`. Keep the `github-pages` environment restricted to approved deployments. The dashboard links to Actions for downloadable renders, and its inline preview works from the static site.

## Pipeline

- `projects/*.json` are authored storyboards. `src/storyboard.ts` defines the strict runtime contract and inferred TypeScript types.
- Structural validation runs first. Python compiles PGN, FEN, and named variations into checked snapshots, including move metadata for captures, castling, and promotions. Scene position changes must be contiguous when animated. An intentional discontinuity requires a cut.
- Remotion Player and Remotion's MP4 renderer share `Film`, `Chessboard`, and camera math. All movement is derived from frame number. The render produces 1080 × 1920 at 30 fps, H.264 and AAC.
- Evaluation graphics require attributed input. Mission 001 provides no engine analysis. The sample's audio is a synthetic Flite test voice. `scripts/narrate.py` regenerates it from caption windows with FFmpeg built with libflite.
- Use `audio` for narration, effect, and music cues. Track start/end and caption boundaries use frames. Caption end is exclusive. Scene presets identify the shot's role. Camera instructions provide explicit focus and scale, and the transition selects an immediate cut or 27-frame camera glide. Suspense holds are ordinary scenes with motion disabled.

### Vertical composition

The design reserves 92 px at the left, 158 px at the right, and 217 px above the main content at 1080 × 1920. The caption block starts at y=1460 and is designed for up to three short lines, with the main message above y=1660. The studio wordmark is lower priority. These are conservative design assumptions. Platform controls and caption overlays vary by device, account, app, and post settings.

### Optional developer checks

Node 24, Python 3.12, and FFmpeg/ffprobe.

```sh
npm ci
python -m pip install -r requirements.txt
npm test
npm run build
npm run render
python scripts/verify-video.py out/legal-mate.mp4
```

Set `CHROMIUM_BIN` to use a provisioned Chromium/Chrome build. Without a local candidate Remotion provisions its headless shell. Generated board snapshots, frontend builds, and MP4s stay out of source control. The sample's small narration asset is committed for reproducible previews. Bundled fonts are DM Sans, Playfair Display and Noto Sans Symbols 2 under their respective SIL Open Font Licenses. Chess glyph positions and cues are rendered programmatically.

## Mission 002 proposal

Add a pinned Stockfish UCI runner and a reproducible analysis contract carrying engine version, settings, POV, score type, and legal principal variations. Identify candidate moments through evaluated swings and tactical contrast, then require evidence-backed positions before asking a model to rank story ideas.
