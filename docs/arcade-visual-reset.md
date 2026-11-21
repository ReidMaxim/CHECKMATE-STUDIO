# Mission 002.A.2 · visual reset and rendering repair

## Defect and reproduction

The archived Impact Polish export is preserved as [the original Actions artifact](https://github.com/ReidMaxim/CHECKMATE-STUDIO/actions/runs/44875861611/artifacts/14696450531). The MP4 decodes without FFmpeg bitstream errors. The decoded picture nonetheless repeats whole rectangular regions, including the page title and background. The full-frame scan flags 170 of 780 frames, including capture frames 233 and 250. Frame 233 occurs before the queen inset mounts, so that inset cannot account for the defect on its own. The same frame 250 drawn directly through Chromium's Remotion still path is clean. The inset and board use bounded, separate SVG roots. Neither contains a repeated title node.

This points to the video capture/transfer route. The archived export alone cannot establish the exact internal Chromium/Remotion fault or separate rasterization from the pixel handoff to the encoder. To isolate the path in CI, the capture-window probe holds the composition, browser, GL setting, dimensions and encoder options constant, changing only shared-memory capture. The archive remains the reliable positive control if the intermittent problem fails to recur in the shorter window.

Disabling shared-memory capture alone still left a frame flagged in one cloud Battle Cut. The arcade CI also pins Chromium Headless Shell 141 (already clean in a local Battle Cut). The existing Remotion/FFmpeg encoder and documentary render settings are retained. CI scans the full decoded Impact repair and Battle Cut for repeated header tiles and saves capture samples. The detector targets the observed repeat pattern, not every possible kind of visual corruption.

## Battle Cut

The 14.5-second composition switches between one full arena SVG and one full-board SVG. Neither scene overlays the other. The bishop and queen exchange, and the knight-versus-king finisher, are labeled dramatizations of `Bxd1` and `Nd5#`. The board bridges them with `Bxf7+` and the forced `Ke7`. The final position holds for 81 frames. Hand-authored piece silhouettes and arena geometry define the original art. The pinned soundtrack uses the existing Kokoro CPU pipeline (am_puck, 1.06×), with original synthesized effects at the capture, check and mate.

## Verified board states

Each row's FEN is the state after that move and before the next row's move. The battle view starts from the first row. Source is the published Légal continuation and Mission 002's replay-validated evidence.

| Ply | Move | FEN |
|---:|---|---|
| 9 | `Nxe5` | `rn1qkbnr/ppp2p1p/3p2p1/4N3/2B1P1b1/2N5/PPPP1PPP/R1BQK2R b KQkq - 0 5` |
| 10 | `Bxd1` | `rn1qkbnr/ppp2p1p/3p2p1/4N3/2B1P3/2N5/PPPP1PPP/R1BbK2R w KQkq - 0 6` |
| 11 | `Bxf7+` | `rn1qkbnr/ppp2B1p/3p2p1/4N3/4P3/2N5/PPPP1PPP/R1BbK2R b KQkq - 0 6` |
| 12 | `Ke7` | `rn1q1bnr/ppp1kB1p/3p2p1/4N3/4P3/2N5/PPPP1PPP/R1BbK2R w KQ - 1 7` |
| 13 | `Nd5#` | `rn1q1bnr/ppp1kB1p/3p2p1/3NN3/4P3/8/PPPP1PPP/R1BbK2R b KQ - 2 7` |
