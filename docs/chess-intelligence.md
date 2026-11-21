# Mission 002 · Chess intelligence

The analyzer accepts one standard-chess PGN, including a custom starting FEN, with at most 600 plies. It preserves its original text and supplied source. It analyzes every nonterminal position, compares the played move with the best line from the same root, and records the independent search after the move. When the played move is absent from MultiPV, Stockfish searches that move alone at the same limit. The root-only search is labeled because a restricted single-line search can reach different conclusions from MultiPV.

Stockfish **17.1**, Linux x86-64, installed from the official release with archive and binary SHA-256 verification. Default depth 12, MultiPV 3, 1 thread, 32 MiB hash and eight retained continuation plies. Engine name, binary hash and embedded network identifiers accompany the output. Each UCI operation has a 12-second response allowance and the game has a 180-second default budget. A final in-flight query may extend past the game budget by the per-command timeout. A failed or timed-out command exits with an error. Re-run at a higher depth for closer editorial review. Time-limited runs are useful for screening but can vary by CPU load.

```sh
python -m pip install -r requirements.txt
bash scripts/install-stockfish.sh
python scripts/chess_intelligence.py analyze examples/chess/deep-blue.pgn --depth 12 --multipv 3 --cache .cache/analysis --output out/deep-blue.json
python scripts/chess_intelligence.py validate out/deep-blue.json
python scripts/chess_intelligence.py storyboard out/deep-blue.json ply-16
STOCKFISH_INTEGRATION=1 npm test
```

Use a path to another PGN to analyze an unseen game. `--time` accepts seconds per search, as an alternative to `--depth`. The cache keys include the binary/network identity, UCI settings, search limits, MultiPV, exact starting FEN and full move history, and any root restriction. Terminal results use chess rules. The adapter emits PGN and verified `variations` compatible with the storyboard compiler, plus the relevant ply and squares.

## Evidence and ranking

The [v1 JSON Schema](analysis.schema.json) describes the exchange contract. Semantic validation legally replays every PV and checks FEN, SAN, original moves, expected-score perspective, position references and candidate order. `engine` and `engine-root` mark hypothetical analysis. Only `game` lines are claimed to have occurred in the PGN. Source and headers come from the input. A published score can have disputed provenance.

All raw scores and native Stockfish WDL are stored from White's viewpoint. Expected score is win probability plus half draw probability in Stockfish's model. Black's expected score is its complement. Mate remains typed separately from centipawns. Move loss compares best and played outcomes from the mover's perspective on the same root. The independently evaluated resulting board is stored separately. These numbers describe the engine's model, not outcomes for humans.

A lone legal move is forced and excluded from editorial ranking. A move matching the first PV is best at this limit. Otherwise near-best is loss up to 0.02, good under 0.06, inaccuracy from 0.06, and mistake from 0.13. Blunder requires loss at least 0.26 and either a destination under 0.40 or a crossing below 0.67 from at least 0.67. A lost engine-reported winning mate can flag an inaccuracy even if outcome loss is under 0.04. Material loss of at least two conventional points across the played-move engine line, expected result at least 0.60, and loss at most 0.06 can flag a sacrifice candidate. It cannot establish intent or soundness. An ending with at most seven pieces and at least 0.10 loss can flag an endgame turn. A reported mate is based on finite-depth engine evidence. If the PV is truncated, the stored prefix is legally replayable, but it is not a proof tree for all defenses.

Rank weights are impact 30, tactics 18, clarity 14, surprise 10, teaching value 10, short line 8, story hook 5, search depth 5. Dimensions and weights are exposed in JSON. `--weights` accepts a JSON object with those keys (see `WEIGHTS` in the CLI), and `--minimum` adjusts the default score floor of 47. Candidates are sorted by score and then earliest ply, retaining at most three and skipping those within two plies of a higher-ranked selection. Positional themes and defensive resources without a strong measurable consequence can be missed.

## Examples and cloud review

- The published Légal mate continuation includes the queen capture and terminal mate. The attribution discusses variants of the historical score.
- Deep Blue–Kasparov game six is a full historical PGN with an independently detected Black-side mistake. The fixture links to the published move score.
- The studio-authored king-and-pawn ending contrasts a winning line and a king move that gives away the advantage.
- The studio-authored quiet ending demonstrates a checking move with no qualifying story. It is intentionally kept as a negative control.

The screening room includes a static analysis section with these four precomputed records. It can replay the recorded game and candidate variations and download evidence with no engine or tokens in the browser. The **Analyze chess examples** workflow includes both branch-push verification and manual dispatch. GitHub exposes manual dispatch once the workflow is on the default branch. The workflow publishes fresh evidence, warm-cache measurements and the dashboard build. Existing film delivery and the verified Director’s Cut remain available through their original pipeline.
