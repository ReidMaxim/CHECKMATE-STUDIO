"""Controlled callback for the two human-selected narrators."""
import argparse
from array import array
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import wave

from casting_room import EXCERPT, TERMS, export_dry, prepare, score, shortlist
from directors_cut import FPS, RATE, ROOT, write_wave
from signature_voice import FIXTURE, recognize
from storyteller import spoken
from tts_providers import KokoroNarrator, PocketNarrator

FINALISTS = ("george", "marius")
EXPERIMENTS = (("original", .3, 42), ("alternate-seed", .3, 17),
               ("lower-temperature", .2, 42), ("lower-temperature-alt", .2, 17))


def transient_flags(samples, rate):
    """Flag unusually abrupt isolated changes late in a phrase, for listening only."""
    import numpy as np
    samples = np.asarray(samples, dtype=float)
    jumps = np.abs(np.diff(samples))
    if not len(jumps) or not np.max(jumps):
        return []
    end = np.where(np.abs(samples) >= .004)[0]
    if not len(end):
        return []
    active_end = end[-1]
    span = int(rate * .22)
    late = jumps[max(0, active_end - span):min(active_end + span, len(jumps))]
    offset = max(0, active_end - span)
    threshold = max(.045, float(np.quantile(jumps, .995)) * 2.5)
    result = []
    for index in np.flatnonzero(late >= threshold):
        t = int(index) + offset
        if result and t / rate - result[-1]["seconds"] < .025:
            continue
        result.append({"seconds": round(t / rate, 4),
                       "relativeToActiveEnd": round((t - active_end) / rate, 4),
                       "jump": round(float(jumps[t]), 4)})
    return result


def decode(path):
    import numpy as np
    data = subprocess.check_output(["ffmpeg", "-v", "error", "-xerror", "-i", str(path),
                                    "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"])
    return np.frombuffer(data, dtype="<f4")


def waveform(path, stages):
    """Write peak envelopes from the full excerpt with a shared time axis."""
    import numpy as np
    width, height, left = 1100, 270, 140
    span = max(len(samples) for _, samples in stages)
    step = max(1, span // (width - left - 10))
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
           '<rect width="100%" height="100%" fill="#111827"/>']
    for i, (label, samples) in enumerate(stages):
        center = 46 + 78 * i
        svg.append(f'<text x="10" y="{center}" fill="white" font-size="13">{label}</text>')
        for x, start in enumerate(range(0, len(samples), step)):
            chunk = samples[start:start+step]
            low, high = np.min(chunk), np.max(chunk)
            svg.append(f'<path d="M{left+x} {center-low*33:.2f}V{center-high*33:.2f}" stroke="#79e1c1"/>')
    svg.append(f'<text x="{left}" y="258" fill="white" font-size="13">0 to {span/RATE:.2f} seconds</text></svg>')
    path.write_text("\n".join(svg))


def experiment(narrator, rows, output, name, verifier):
    import numpy as np
    excerpt = rows[EXCERPT]
    words = [spoken(row["phrases"][0]["text"]) for row in excerpt]
    clips, raw_hashes, diagnostics = [], [], []
    assembled, boundaries = array("h"), []
    for i, text in enumerate(words):
        if i:
            previous = excerpt[i - 1]
            gap = previous["frames"] - previous["phrases"][0]["to"] + excerpt[i]["phrases"][0]["from"]
            assembled.extend(array("h", [0]) * round(gap * RATE / FPS))
        captured = []
        clip = narrator.synthesize(text, capture=lambda raw, _rate: captured.append(raw.copy()))
        raw = captured[0]
        raw_hashes.append(sha256(raw.tobytes()).hexdigest())
        wav = output / f"{name}-phrase-{i+1}-model-raw.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "1",
                        "-ar", str(RATE), "-i", "-", "-c:a", "pcm_f32le", str(wav)],
                       input=raw.astype("<f4").tobytes(), check=True)
        diagnostics.append({"phrase": i + 1, "text": text, "rawFlags": transient_flags(raw, RATE),
                            "rawSeconds": len(raw)/RATE, "settings": clip.audit()})
        start = len(assembled)
        assembled.extend(clip.pcm)
        boundaries.append((start, len(assembled)))
        clips.append(clip)
    m4a = export_dry(assembled, name, output, output)
    raw = np.asarray(assembled, dtype=float) / 32768
    encoded = decode(m4a)
    normalized = decode(output / f"{name}-normalized.wav")
    waveform(output / f"{name}-waveform.svg",
             [("Assembled PCM", raw), ("Normalized WAV", normalized), ("Decoded AAC", encoded)])
    for item, (start, end) in zip(diagnostics, boundaries, strict=True):
        item.update(excerptStart=start/RATE, excerptEnd=end/RATE,
                    assembledFlags=transient_flags(raw[start:end], RATE),
                    normalizedFlags=transient_flags(normalized[start:end], RATE),
                    encodedFlags=transient_flags(encoded[start:end], RATE))
    review = recognize(verifier, m4a, " ".join(words))
    return {"hashes": raw_hashes, "diagnostics": diagnostics, "wordReview": review,
            "score": score(review), "rawFlagCount": sum(len(item["rawFlags"]) for item in diagnostics)}, clips


def run(models, output):
    from vosk import Model, SetLogLevel

    SetLogLevel(-1)
    output.mkdir(parents=True, exist_ok=True)
    fixture = json.loads(FIXTURE.read_text())
    rows = fixture["timing"]["scenes"]
    verifier = Model(str(models / "vosk-model-small-en-us-0.15"))
    finalists = shortlist({}, FINALISTS)
    report = {"selection": {"voices": finalists, "method": "Human listening feedback", "frontRunner": "george"},
              "reference": fixture["reference"], "profiles": {
                  "george": {"license": "CC BY 4.0", "source": "CSTR VCTK p315, published by Kyutai"},
                  "marius": {"license": "CC0", "source": "Unmute Voice Donation Project Selfie, published by Kyutai"}},
              "modelLicense": "CC BY 4.0", "fallback": "af_heart", "approval": "Human listening pending",
              "experiments": {}, "films": {}, "regressions": {}}
    successful = {}
    for name, temperature, seed in (*EXPERIMENTS, ("original-repeat", .3, 42)):
        try:
            narrator = PocketNarrator("marius", models, temperature=temperature, seeds=(seed,))
            result, clips = experiment(narrator, rows, output, f"marius-{name}", verifier)
            report["experiments"][name] = result
            successful[name] = clips
        except (ValueError, RuntimeError) as exc:
            report["experiments"][name] = {"failed": str(exc)}
    experiments = report["experiments"]
    report["seedReplayMatches"] = ("original" in successful and "original-repeat" in successful
        and experiments["original"]["hashes"] == experiments["original-repeat"]["hashes"])
    options = [name for name in successful if name not in ("original", "original-repeat")]
    best = min(options, key=lambda name: (experiments[name]["score"], experiments[name]["rawFlagCount"]), default=None)
    report["mariusComparison"] = best
    report["diagnosisLimits"] = ("Transient measures are advisory and cannot identify a breath, mouth click or repeated phoneme. "
                               "Use raw phrase WAVs and the normalized and AAC excerpt before calling the issue repaired.")
    approved_for_render = ["george"]
    settings = {name: (temperature, seed) for name, temperature, seed in EXPERIMENTS}
    for name in finalists:
        if name == "marius" and not best:
            continue
        temperature, seed = settings[best] if name == "marius" else (.3, 42)
        narrator = PocketNarrator(name, models, temperature=temperature, seeds=(seed,))
        measured = dict(zip(range(1, 4), successful[best], strict=True)) if name == "marius" else {}
        try:
            film = prepare(fixture, name, narrator, measured, output, verifier)
            term = narrator.synthesize(spoken(TERMS))
            sample = export_dry(term.pcm, f"{name}-chess-terms", output, output)
            film["pronunciation"] = recognize(verifier, sample, spoken(TERMS))
            film["transcriptFlags"] = score(film["wordReview"])
            report["films"][name] = film
            # Keep ASR advisory. Skip comparison only on conspicuous transcript divergence.
            if name == "marius" and film["transcriptFlags"] <= 22:
                approved_for_render.append(name)
        except (ValueError, RuntimeError) as exc:
            if name == "george":
                raise
            report["films"][name] = {"failed": str(exc)}
    for name in ("af_heart", "alba", "anna"):
        narrator = (KokoroNarrator(ROOT / ".cache/kokoro", name, fixture["rates"]) if name == "af_heart"
                    else PocketNarrator(name, models))
        report["regressions"][name] = narrator.synthesize("A knight and a rook. Checkmate.").audit()
    (output / "callback-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "shortlist.json").write_text(json.dumps(approved_for_render) + "\n")
    for name, result in experiments.items():
        summary = ({k: result[k] for k in ("score", "rawFlagCount")} |
                   {"phraseFlags": [{p: row[p] for p in ("rawFlags", "assembledFlags", "normalizedFlags", "encodedFlags")}
                                    for row in result["diagnostics"]]}) if "diagnostics" in result else result
        print("EXPERIMENT", name, json.dumps(summary))
    print("CALLBACK", json.dumps({"seedReplayMatches": report["seedReplayMatches"], "best": best,
                                  "films": {key: value.get("transcriptFlags") for key, value in report["films"].items()},
                                  "render": approved_for_render}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.models, args.output)
