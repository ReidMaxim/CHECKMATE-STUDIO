"""Audition upstream voice states and prepare two frozen-story comparison films."""
import argparse
from array import array
import json
from pathlib import Path
import shutil
import subprocess

from compile import compile_project
from directors_cut import FPS, RATE, ROOT, frames, produce, write_wave
from signature_voice import FIXTURE, align, audio_preview, recognize
from storyteller import spoken
from tts_providers import CASTING_PROFILES, KokoroNarrator, PocketNarrator

TERMS = "The knight, rook, and bishop. Checkmate. A sacrifice. The rook lands on D8."
EXCERPT = slice(1, 4)
REFERENCES = ("af_heart", "alba")


def score(review):
    """Machine screening only. Ignore known homophones and spelling variants."""
    aliases = {"night": "knight", "peace": "piece", "bee": "b", "be": "b"}
    def canonical(text):
        return [aliases.get(word, word) for word in text.split()]
    return sum(max(len(item["expected"].split()), len(item["recognized"].split()))
               for item in review["differences"]
               if canonical(item["expected"]) != canonical(item["recognized"]))


def shortlist(candidates, override=None):
    """Advance the two strongest technical candidates for listener review."""
    if override is not None:
        if len(set(override)) != 2 or len(override) != 2 or any(name not in CASTING_PROFILES for name in override):
            raise ValueError("Human shortlist requires two distinct catalog voices")
        return list(override)
    def rank(name):
        row = candidates[name]
        return row["score"], abs(row["seconds"] - 18), name
    names = [name for name in CASTING_PROFILES if "score" in candidates.get(name, {})]
    if len(names) < 2:
        raise ValueError("Fewer than two usable casting candidates")
    return sorted(names, key=rank)[:2]


def normalize_audition(source, target):
    settings = "loudnorm=I=-18:TP=-4:LRA=9"
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(source), "-af",
                            settings + ":print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    levels = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    effect = settings + ":linear=true" + "".join(
        f":measured_{target}={levels['input_' + key]}"
        for target, key in (("I", "i"), ("LRA", "lra"), ("TP", "tp"), ("thresh", "thresh")))
    effect += f":offset={levels['target_offset']}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-af", effect,
                    "-ar", str(RATE), "-ac", "1", str(target)], check=True)


def export_dry(pcm, stem, scratch, output):
    raw, normalized = (scratch / f"{stem}-{kind}.wav" for kind in ("raw", "normalized"))
    write_wave(raw, pcm)
    normalize_audition(raw, normalized)
    target = output / f"{stem}.m4a"
    audio_preview(normalized, target)
    return target


def prepare(fixture, name, narrator, measured, output, verifier):
    original = fixture["project"]["scenes"]
    rows = fixture["timing"]["scenes"]
    clips = [measured[i] if i in measured else narrator.synthesize(spoken(row["phrases"][0]["text"]))
             for i, row in enumerate(rows)]
    shots = [align(scene, row, clip, True)
             for scene, row, clip in zip(original, rows, clips, strict=True)]
    by_text = dict(zip([shot["phrases"][0][2] for shot in shots], clips, strict=True))
    produce({"scenes": shots}, "pocket", output, name, 1, project=fixture["project"], stem="unseen",
            synthesis=lambda text: by_text[text].pcm, model_label=clips[0].model)
    storyboard_path = ROOT / "projects/unseen-documentary.json"
    storyboard = compile_project(json.loads(storyboard_path.read_text()))
    for scene, frozen in zip(storyboard["scenes"], original, strict=True):
        if [cue["text"] for cue in scene["captions"]] != [cue["text"] for cue in frozen["captions"]]:
            raise ValueError("Frozen caption wording changed during casting")
    directory = output / "render-inputs" / name
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(storyboard_path, directory / storyboard_path.name)
    for asset in ("unseen-narration.wav", "unseen-effects.wav"):
        shutil.copyfile(ROOT / "public" / asset, directory / asset)
    expected = " ".join(spoken(row["phrases"][0]["text"]) for row in rows)
    return dict(timing=json.loads((ROOT / "out/unseen-timing.json").read_text()),
                phrases=[clip.audit() for clip in clips],
                wordReview=recognize(verifier, directory / "unseen-narration.wav", expected))


def run(models, output):
    from vosk import Model, SetLogLevel
    SetLogLevel(-1)
    verifier = Model(str(models / "vosk-model-small-en-us-0.15"))
    fixture = json.loads(FIXTURE.read_text())
    rows = fixture["timing"]["scenes"]
    excerpt = rows[EXCERPT]
    words = [spoken(row["phrases"][0]["text"]) for row in excerpt]
    output.mkdir(parents=True, exist_ok=True)
    scratch = output.parent / "casting-scratch"
    scratch.mkdir(exist_ok=True)
    report = {"reference": fixture["reference"], "excerpt": " ".join(words), "terms": spoken(TERMS),
              "normalization": "−18 LUFS target, −4 dBTP limit; native Pocket tempo",
              "screening": "Transcript discrepancy count with homophones ignored and runtime as tie-breaker. "
                           "The two lowest counts advance. Listener approval pending.",
              "humanReview": ["Naturalness", "Expressiveness", "Consistency", "Distinctive character", "Pronunciation"],
              "candidates": {}}
    takes = {}
    for name in (*REFERENCES, *CASTING_PROFILES):
        narrator = (KokoroNarrator(ROOT / ".cache/kokoro", name, fixture["rates"])
                    if name == "af_heart" else PocketNarrator(name, models))
        try:
            clips = [narrator.synthesize(text) for text in words]
            pcm = array("h")
            for i, clip in enumerate(clips):
                if i:
                    prior = excerpt[i - 1]
                    gap_frames = prior["frames"] - prior["phrases"][0]["to"] + excerpt[i]["phrases"][0]["from"]
                    pcm.extend(array("h", [0]) * round(gap_frames * RATE / FPS))
                pcm.extend(clip.pcm)
            audition = export_dry(pcm, f"{name}-audition", scratch, output)
            term = narrator.synthesize(spoken(TERMS))
            terms = export_dry(term.pcm, f"{name}-chess-terms", scratch, output)
        except (ValueError, RuntimeError) as error:
            if name in REFERENCES:
                raise
            report["candidates"][name] = {"failed": str(error)}
            continue
        speech_check = recognize(verifier, audition, " ".join(words))
        term_check = recognize(verifier, terms, spoken(TERMS))
        report["candidates"][name] = dict(seconds=len(pcm) / RATE, narration=[clip.audit() for clip in clips],
                                          wordReview=speech_check, pronunciation=term_check,
                                          score=score(speech_check) + score(term_check))
        takes[name] = dict(zip(range(*EXCERPT.indices(len(rows))), clips, strict=True))
    selected = shortlist(report["candidates"])
    report["shortlist"] = selected
    report["profileSources"] = CASTING_PROFILES
    for name in selected:
        narrator = PocketNarrator(name, models)
        report["candidates"][name]["fullFilm"] = prepare(fixture, name, narrator, takes[name], output, verifier)
    (output / "casting-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (output / "shortlist.json").write_text(json.dumps(selected) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, default=ROOT / ".cache/signature-models")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.models, args.output)
