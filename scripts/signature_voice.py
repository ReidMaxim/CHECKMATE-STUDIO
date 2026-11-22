"""Render an audio-only comparison and retime the frozen Mission 004.2 edit."""
import argparse
from copy import deepcopy
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import subprocess

from compile import compile_project
from directors_cut import FPS, MOVE_FRAMES, RATE, ROOT, produce, trim, write_wave
from storyteller import spoken
from tts_providers import KokoroNarrator, POCKET_VOICES, PocketNarrator

FIXTURE = ROOT / "examples/signature/capture-baseline.json"
TERMS = ("Checkmate, knight, bishop, rook, queen. Castling, sacrifice, capture. "
         "The knight goes to F5. The queen checks from B8. The rook lands on D8.")
HUMAN_REVIEW = ["Identity and accent consistency", "Sentence-end intonation and phrasing",
                "Chess terminology and square pronunciation", "Repeated and missing words",
                "Comfort across the entire script"]


def words(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace("’", "'"))


def discrepancies(expected, recognized):
    source, actual = words(expected), words(recognized)
    matcher = SequenceMatcher(a=source, b=actual, autojunk=False)
    return [{"type": kind, "expected": " ".join(source[i:j]), "recognized": " ".join(actual[k:l])}
            for kind, i, j, k, l in matcher.get_opcodes() if kind != "equal"]


def align(scene, row, clip, retime):
    if len(row["phrases"]) != 1 or scene["moveFrames"] not in (0, MOVE_FRAMES):
        raise ValueError("Comparison expects the frozen single-thought scenes")
    cue = row["phrases"][0]
    lead = cue["from"]
    tail = row["frames"] - cue["to"]
    shot = {key: deepcopy(scene[key]) for key in ("preset", "title", "ply", "camera", "transition",
                                                    "highlights", "arrows", "chapter", "settleCamera", "line")
            if key in scene}
    shot.update(lead=lead / FPS, tail=tail / FPS, phrases=[[cue["text"], 0, spoken(cue["text"])]])
    if scene["moveFrames"]:
        start = scene["moveAt"]
        if retime:
            duration = len(trim(clip.pcm)) / RATE * FPS
            old_duration = row["spokenSamples"][0] / RATE * FPS
            if start >= lead:
                start = lead + round((start - lead) * duration / old_duration)
            # Keep the movement within the phrase if a model returns a short take.
            start = min(start, max(0, lead + int(duration) - MOVE_FRAMES))
        shot["visualMoveAt"] = start / FPS
        # The producer originally uses this cue for every move except checkmate.
        shot["effect"] = "check" if scene["preset"] == "reveal" and scene.get("settleCamera") else "place"
    return shot


def normalize(source, target):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-af",
                    "loudnorm=I=-18:TP=-4:LRA=9", "-ar", str(RATE), "-ac", "1", str(target)], check=True)


def audio_preview(source, target):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-c:a", "aac",
                    "-b:a", "128k", "-movflags", "+faststart", str(target)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(target), "-f", "null", "-"], check=True)


def recognize(model, path, expected):
    from vosk import KaldiRecognizer
    audio = subprocess.check_output(["ffmpeg", "-v", "error", "-xerror", "-i", str(path),
                                     "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
    recognizer = KaldiRecognizer(model, 16000)
    pieces = []
    for start in range(0, len(audio), 8000):
        if recognizer.AcceptWaveform(audio[start:start + 8000]):
            pieces.append(json.loads(recognizer.Result())["text"])
    pieces.append(json.loads(recognizer.FinalResult())["text"])
    transcript = " ".join(part for part in pieces if part)
    return {"expected": expected, "recognized": transcript,
            "differences": discrepancies(expected, transcript)}


def compare(args):
    from vosk import Model, SetLogLevel
    SetLogLevel(-1)
    verifier = Model(str(args.models / "vosk-model-small-en-us-0.15"))
    fixture = json.loads(FIXTURE.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    rows = fixture["timing"]["scenes"]
    original_scenes = fixture["project"]["scenes"]
    if [row["phrases"][0]["text"] for row in rows] != [claim["text"] for claim in fixture["claims"]]:
        raise ValueError("Frozen timeline and claim ledger disagree")
    expected = " ".join(spoken(row["phrases"][0]["text"]) for row in rows)
    report = {"reference": fixture["reference"], "selected": fixture["selected"], "claims": fixture["claims"],
              "normalization": "FFmpeg loudnorm, target −18 LUFS and −4 dBTP; mono 24 kHz",
              "reviewStatus": "Listener approval pending", "listenerChecklist": HUMAN_REVIEW,
              "wordReviewMethod": "Vosk ASR differences are listening prompts, not verified omissions or mispronunciations.",
              "comparisonFilm": args.film_voice, "comparisonFilmDecision":
                  ("Alba is the provisional cut because the first screening retained D eight and fit close to the benchmark runtime."
                   if args.film_voice == "alba" else "Manual selection of Anna for comparison."),
              "defaultVoice": "af_heart",
              "candidates": {}}
    for name in ("af_heart", *POCKET_VOICES):
        pocket = name in POCKET_VOICES
        narrator = (PocketNarrator(name, args.models) if pocket else
                    KokoroNarrator(ROOT / ".cache/kokoro", name, fixture["rates"]))
        clips = [narrator.synthesize(spoken(row["phrases"][0]["text"])) for row in rows]
        shots = [align(scene, row, clip, pocket)
                 for scene, row, clip in zip(original_scenes, rows, clips, strict=True)]
        clips_by_text = dict(zip([shot["phrases"][0][2] for shot in shots], clips, strict=True))
        # Reuse the frozen project ID so all renderer settings match the archived production.
        produce({"scenes": shots}, "kokoro" if not pocket else "pocket", args.models, name, 1,
                project=fixture["project"], stem="unseen", synthesis=lambda text: clips_by_text[text].pcm,
                model_label=clips[0].model)
        project_file = ROOT / "projects/unseen-documentary.json"
        project = compile_project(json.loads(project_file.read_text()))
        timing = json.loads((ROOT / "out/unseen-timing.json").read_text())
        if not pocket and project["scenes"] != original_scenes:
            raise ValueError("Resynthesized Kokoro storyboard diverged from the frozen edit")
        audition = args.output / f"{name}-full-script.m4a"
        audio_preview(ROOT / "public/unseen-narration.wav", audition)
        terms = narrator.synthesize(spoken(TERMS))
        terms_raw = args.models / f"{name}-terms.wav"
        write_wave(terms_raw, terms.pcm)
        terms_normalized = args.models / f"{name}-terms-normalized.wav"
        normalize(terms_raw, terms_normalized)
        term_preview = args.output / f"{name}-chess-terms.m4a"
        audio_preview(terms_normalized, term_preview)
        script_check = recognize(verifier, audition, expected)
        term_check = recognize(verifier, term_preview, spoken(TERMS))
        report["candidates"][name] = dict(phrases=[clip.audit() for clip in clips], timing=timing,
                                          wordReview=script_check, chessTerms=term_check,
                                          listeningStatus="Human listening pending")
        (args.output / f"{name}-storyboard.json").write_text(json.dumps(project, indent=2) + "\n")
        if name == args.film_voice:
            args.film_dir.mkdir(parents=True, exist_ok=True)
            for asset in ("unseen-narration.wav", "unseen-effects.wav"):
                (args.film_dir / asset).write_bytes((ROOT / "public" / asset).read_bytes())
            (args.film_dir / project_file.name).write_bytes(project_file.read_bytes())
    if args.film_voice:
        (ROOT / "projects/unseen-documentary.json").write_bytes((args.film_dir / "unseen-documentary.json").read_bytes())
        for asset in ("unseen-narration.wav", "unseen-effects.wav"):
            (ROOT / "public" / asset).write_bytes((args.film_dir / asset).read_bytes())
    (args.output / "voice-profiles.json").write_bytes(FIXTURE.with_name("voice-profiles.json").read_bytes())
    (args.output / "voice-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", type=Path, default=ROOT / ".cache/signature-models")
    parser.add_argument("--film-voice", choices=POCKET_VOICES, default="alba")
    args = parser.parse_args()
    args.film_dir = ROOT / "out/signature-render-assets"
    compare(args)
