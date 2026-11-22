"""Build WAV stems and a legal storyboard from measured narration phrases."""
import argparse
from array import array
import json
from math import ceil, exp, pi, sin
from pathlib import Path
import random
import subprocess
import tempfile
from textwrap import wrap
import wave

ROOT = Path(__file__).resolve().parents[1]
RATE = 24000
FPS = 30
SAMPLES = RATE // FPS
MOVE_FRAMES = 19
MAX_CAPTION = 58
EFFECTS = {"open": (115, .22, 2800), "place": (255, .09, 4200),
           "capture": (150, .15, 4500), "check": (410, .23, 3800),
           "reveal": (198, .35, 4200), "evaluation": (240, .22, 3400),
           "close": (122, .22, 2000)}


def frames(seconds):
    return round(seconds * FPS)


def plan(scene, lengths):
    """Place whole phrases on frame boundaries while preserving measured samples."""
    cursor = frames(scene["lead"])
    cues = []
    for (caption, pause, *_), length in zip(scene["phrases"], lengths, strict=True):
        if (len(caption) > MAX_CAPTION and not scene.get("chapter")) or length < SAMPLES:
            raise ValueError(f"Caption exceeds safe budget or audio is too short: {caption}")
        end = cursor + ceil(length / SAMPLES)
        cues.append(dict(from_=cursor, to=end, text=caption))
        cursor = end + frames(pause)
    move_at = 0
    if "anchor" in scene:
        cue = cues[scene["anchor"]]
        move_at = cue["from_"] + 6
        if move_at + MOVE_FRAMES > cue["to"]:
            raise ValueError(f"Move must land during its spoken phrase: {scene['title']}")
    if "visualMoveAt" in scene:
        move_at = frames(scene["visualMoveAt"])
    duration = cursor + frames(scene["tail"])
    if "visualMoveAt" in scene and move_at + MOVE_FRAMES >= duration:
        raise ValueError("Visual move must finish inside its shot")
    return cues, duration, move_at


def caption_pages(cues, chapter):
    if not chapter:
        return [{"from": cue["from_"], "to": cue["to"], "text": cue["text"]} for cue in cues]
    pages = []
    for cue in cues:
        lines = wrap(cue["text"], width=MAX_CAPTION, break_long_words=False, break_on_hyphens=False)
        weights = [len(line.split()) for line in lines]
        span = cue["to"] - cue["from_"]
        start = cue["from_"]
        for index, line in enumerate(lines, 1):
            end = cue["from_"] + round(span * sum(weights[:index]) / sum(weights))
            if end <= start:
                raise ValueError("Caption page has no screen time")
            pages.append({"from":start, "to":end, "text":line})
            start = end
    return pages


def write_wave(path, samples):
    with wave.open(str(path), "wb") as file:
        file.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        file.writeframes(samples.tobytes())


def sound(name):
    frequency, length, level = EFFECTS[name]
    rng = random.Random(name)
    return array("h", (int(level * min(1, i / 50) * exp(-6 * i / (length * RATE)) *
                           (.75 * sin(2*pi*frequency*i/RATE) + .25 * rng.uniform(-1, 1)))
                       for i in range(int(length * RATE))))


def speaker(provider, model_dir, voice, rate):
    if provider == "kokoro":
        from kokoro_onnx import Kokoro
        from onnxruntime import InferenceSession, SessionOptions

        options = SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        session = InferenceSession(str(model_dir / "kokoro-v1.0.int8.onnx"), options,
                                   providers=["CPUExecutionProvider"])
        engine = Kokoro.from_session(session, str(model_dir / "voices-v1.0.bin"))
        if voice not in engine.get_voices():
            raise ValueError(f"Unknown Kokoro voice: {voice}")

        def synthesize(text):
            result, sample_rate = engine.create(text, voice=voice, speed=rate, lang="en-us")
            if sample_rate != RATE:
                raise ValueError(f"Unexpected Kokoro sample rate: {sample_rate}")
            return array("h", (round(32767 * max(-1, min(1, value))) for value in result))

        return synthesize

    def flite(text):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "phrase.txt"
            source.write_text(text.replace("’", "'"))
            return array("h", subprocess.check_output([
                "ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"flite=textfile={source}:voice=slt",
                "-af", f"atempo={rate}", "-ar", str(RATE), "-ac", "1", "-f", "s16le", "-",
            ]))

    return flite


def trim(samples):
    """Keep consonant margins while discarding engine padding."""
    active = [i for i, value in enumerate(samples) if abs(value) > 70]
    if not active:
        raise ValueError("Speech provider returned silent audio")
    return samples[max(0, active[0]-240):active[-1]+320]


def produce(spec, provider, model_dir, voice, rate, *, project=None, stem="director", synthesis=None, model_label=None):
    synthesize = synthesis or speaker(provider, model_dir, voice, rate)
    baseline = project.copy() if project else json.loads((ROOT / "projects/legal-mate.json").read_text())
    if project is None:
        baseline.update(id="legal-directors-cut", title="A Queen for a King · Director’s Cut")
    narration, effects = array("h"), array("h")
    authored = []
    audit = []
    for shot in spec["scenes"]:
        spoken = [trim(synthesize(phrase[2] if len(phrase) > 2 else phrase[0]))
                  for phrase in shot["phrases"]]
        cues, duration, move_at = plan(shot, [len(phrase) for phrase in spoken])
        start = len(narration)
        narration.extend(array("h", [0]) * (duration * SAMPLES))
        effects.extend(array("h", [0]) * (duration * SAMPLES))
        for cue, samples in zip(cues, spoken, strict=True):
            at = start + cue["from_"] * SAMPLES
            narration[at:at+len(samples)] = samples
        animated = "anchor" in shot or "visualMoveAt" in shot
        landing = move_at + MOVE_FRAMES if animated else 0
        if shot.get("effect"):
            at = start + landing * SAMPLES
            pulse = sound(shot["effect"])
            if at + len(pulse) > len(effects):
                raise ValueError(f"Sound exceeds scene: {shot['title']}")
            effects[at:at+len(pulse)] = pulse
        scene = {key: shot[key] for key in ("preset", "title", "ply", "camera")}
        if "chapter" in shot:
            scene["chapter"] = shot["chapter"]
        if "line" in shot:
            scene["line"] = shot["line"]
        if "settleCamera" in shot:
            scene["settleCamera"] = shot["settleCamera"]
        scene.update(frames=duration, moveAt=move_at, moveFrames=MOVE_FRAMES if animated else 0,
                     highlights=shot.get("highlights", []), arrows=shot.get("arrows", []), transition=shot.get("transition","glide"),
                     captions=caption_pages(cues, shot.get("chapter"))
        authored.append(scene)
        audit.append({"title": shot["title"], "start": start // SAMPLES, "frames": duration,
                      "spokenSamples": [len(samples) for samples in spoken], "moveAt": move_at,
                      "anchor": shot.get("anchor"), "cues": scene["captions"]})
        if "chapter" in shot:
            audit[-1].update(chapter=shot["chapter"], phrases=[
                {"text": cue["text"], "from": cue["from_"], "to": cue["to"]} for cue in cues])
    with tempfile.TemporaryDirectory() as folder:
        raw = Path(folder) / "raw.wav"
        write_wave(raw, narration)
        speech_path = ROOT / f"public/{stem}-narration.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
                        "loudnorm=I=-18:TP=-4:LRA=9", "-ar", str(RATE), "-ac", "1",
                        str(speech_path)], check=True)
        with wave.open(str(speech_path), "rb") as stream:
            if abs(stream.getnframes() - len(narration)) > SAMPLES:
                raise ValueError("Normalized audio length drifted by more than one video frame")
    write_wave(ROOT / f"public/{stem}-effects.wav", effects)
    model = model_label or ("Kokoro 82M v1.0 INT8" if provider == "kokoro" else "Flite fallback")
    baseline.update(presentation="director", captionStyle="boxed", scenes=authored,
                    audio=[dict(asset=f"{stem}-narration.wav", start=0, volume=.90, kind="narration",
                                label=f"{model} · {voice if provider == 'kokoro' else 'slt'}"),
                           dict(asset=f"{stem}-effects.wav", start=0, volume=.50, kind="effect",
                                label="Original synthesized effects")])
    (ROOT / f"projects/{baseline['id']}.json").write_text(json.dumps(baseline, indent=2))
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / f"out/{stem}-timing.json").write_text(json.dumps(
        {"provider": provider, "model": model, "voice": voice if provider == "kokoro" else "slt",
         "rate": rate, "fps": FPS, "frames": len(narration) // SAMPLES, "scenes": audit}, indent=2))
    print(f"{model}: {len(narration)/RATE:.2f}s for {len(authored)} scenes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("kokoro", "flite"), default="kokoro")
    parser.add_argument("--model-dir", type=Path, default=ROOT / ".cache/kokoro")
    parser.add_argument("--voice")
    parser.add_argument("--rate", type=float)
    options = parser.parse_args()
    spec = json.loads((ROOT / "projects/directors-script.json.in").read_text())
    rate = spec["rate"] if options.rate is None else options.rate
    if not .75 <= rate <= 1.25:
        parser.error("Speaking rate must be between .75 and 1.25")
    produce(spec, options.provider, options.model_dir, options.voice or spec["voice"], rate)
