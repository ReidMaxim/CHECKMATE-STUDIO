# Mission 004 · The Unseen Game

Start on the Live Director branch. The Deep Blue authored treatment, prepared voice fixture, and existing benchmark workflow have their original entry points. The unseen workflow consumes a PGN directly, runs Stockfish 17.1, verifies up to four candidates independently at higher depth, and re-ranks supported candidates by screening qualities, deeper mover-relative expected-result loss and recorded checkmate. White is the stored score perspective. Expected result and engine lines are finite-depth estimates.

## Demonstrations

The Opera Game and Capablanca–Tartakower were selected from published scores before screening. The former is a short attacking game with a recorded mate. The latter has a long rook-and-pawn phase. Their sources are supplied in the PGN headers. No position, pivot, or moves are specified to the director for either game.

## Cloud review

In GitHub Actions, open **Produce unseen-game documentary**. A blank PGN input processes both examples. Use a repository PGN path or paste a single PGN. Choose the branch containing the workflow. The primary example and submitted games render MP4s. The second example exports evidence, treatments, script, storyboard and timing. Each successful job uploads one review artifact. On iPhone, sign into GitHub in Safari, open the run, download and unzip the artifact in Files, and open the MP4.

Set repository Actions secret `OPENROUTER_API_KEY` and variable `STORY_MODEL` to a compatible free model for hosted production. Auto mode uses hosted planning if configured and records the actual mode. Live mode fails on missing configuration. There are at most two HTTP attempts per production, with a 25-second request timeout, 2,600 response tokens, and a zero-price routing cap. An invalid model plan fails validation. Offline mode uses deterministic editorial assembly and fresh audio and provides no evidence of hosted scripting.

## How the screenplay is grounded

The hosted director selects and orders verified sentence-level evidence including alternatives. It writes opening questions and takeaway prompts within a restricted factuality grammar. The resulting script is an evidence-constrained screenplay, with limited prose range. PGN headers are preserved as supplied metadata. Fictional motives and unsupported historical claims cannot enter the dialogue. Recorded facts replay on the main board. Alternative facts replay only on a distinctly labeled branch. The editorial rubric weighs clarity (25), accessibility (20), visual opportunities (20), structure (20) and variety of treatment (15), with the option of selecting a candidate or treatment manually.

Kokoro uses the Mission 003.1 phrase-level rate profiles, signal checks and bounded retries. The actual audio establishes durations. Runtime outside 35–60 seconds fails production. Artifacts contain the selected treatment, claim ledger, exact measured timing and configuration. A null MP4 validation field means that artifact has not undergone video decoding.

Review the hook, through-line, teaching value, accuracy, narration, pacing, camera and engagement beside the Mission 003.1 benchmark. The technical report and timing audit support review. They cannot decide whether the film holds attention.
