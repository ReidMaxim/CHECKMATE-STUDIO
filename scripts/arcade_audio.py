"""Synthesize the experimental ARCADE//CHESS cut and verify its evidence."""
import argparse
from array import array
import json
from math import exp, pi, sin
from pathlib import Path
import subprocess
import tempfile

from chess_intelligence import validate
from directors_cut import RATE, ROOT, speaker, trim, write_wave

SECONDS = 26
FPS = 30
VOICE = "am_puck"
SPEED = 1.06
EXPECTED = ["Nxe5", "Bxd1", "Bxf7+", "Ke7", "Nd5#"]
EFFECTS = {"move": [270], "capture": [280, 125], "check": [440, 660], "mate": [523, 659, 784, 1047]}
BED = [130.81, 130.81, 155.56, 130.81, 98, 116.54, 98, 87.31]


def sample_at(seconds):
    return round(seconds * FPS) * (RATE // FPS)


def validate_arcade(evidence, cues):
    validate(evidence)
    assert [move["actual"]["san"] for move in evidence["moveAssessments"][8:13]] == EXPECTED
    assert [cue["ply"] for cue in cues] == [8, 9, 10, 11, 12, 13, 13]
    assert evidence["positions"][13]["evaluation"]["mate"] == 0
    for cue, following in zip(cues, cues[1:] + [{"time": SECONDS}]):
        if not 0 <= cue["time"] < following["time"] <= SECONDS:
            raise ValueError("Arcade cues must be ascending and inside the film")
        if "hit" in cue and not .4 <= cue["hit"] < following["time"] - cue["time"] - .5:
            raise ValueError("Move animation or effect exceeds its cue window")


def produce(provider):
    cues = json.loads((ROOT / "src/arcade-cues.json").read_text())
    evidence = json.loads((ROOT / "examples/analysis/legal-mate.json").read_text())
    validate_arcade(evidence, cues)
    say = speaker(provider, ROOT / ".cache/kokoro", VOICE, SPEED)
    narration = array("h", [0]) * (RATE * SECONDS)
    effects = array("h", [0]) * (RATE * SECONDS)
    audible = bytearray(RATE * SECONDS)
    for cue, following in zip(cues, cues[1:] + [{"time": SECONDS}]):
        spoken = trim(say(cue["speak"]))
        offset = sample_at(cue["time"] + .10)
        end = offset + len(spoken)
        if end > sample_at(following["time"]):
            raise ValueError(f"Speech exceeds scene: {cue['title']}")
        narration[offset:end] = spoken
        audible[offset:end] = b"\x01" * len(spoken)
        if "effect" not in cue:
            continue
        at = sample_at(cue["time"]) + sample_at(cue["hit"])
        frequencies = EFFECTS[cue["effect"]]
        for step, frequency in enumerate(frequencies):
            for i in range(int(.08 * RATE)):
                t = i/RATE
                level = 2000 * min(1,i/64) * exp(-42*t)
                value = sin(2*pi*frequency*t) + .22*sin(6*pi*frequency*t)
                effects[at + round(step*.075*RATE) + i] += round(level * value)
    for i in range(len(effects)):
        t = i/RATE
        beat = int(t * 4)
        age = t - beat / 4
        duck = .48 if audible[i] else 1.
        effects[i] += round(570*duck*min(1,age*100)*exp(-15*age)*sin(2*pi*BED[beat % len(BED)]*t))
    with tempfile.TemporaryDirectory() as tmp:
        speech_file, effect_file = Path(tmp)/"voice.wav", Path(tmp)/"fx.wav"
        write_wave(speech_file, narration)
        write_wave(effect_file, effects)
        subprocess.run(["ffmpeg","-v","error","-y","-i",str(speech_file),"-i",str(effect_file),
                        "-filter_complex","amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-2:LRA=8",
                        "-ar",str(RATE),"-ac","1",str(ROOT/"public/arcade-mix.wav")],check=True)
    output = ROOT / "out"
    output.mkdir(exist_ok=True)
    (output/"arcade-audit.json").write_text(json.dumps({
        "provider":provider,"voice":VOICE if provider=="kokoro" else "slt","speed":SPEED,
        "fps":FPS,"seconds":SECONDS,"positionBefore":evidence["positions"][8]["fen"],
        "game":evidence["game"]["sha256"],"source":evidence["source"],"moves":EXPECTED,
        "engine":evidence["engine"],"cues":cues},indent=2))
    (output/"arcade-format.json").write_text(json.dumps({
        "width":1080,"height":1920,"fps":FPS,"scenes":[{"frames":FPS*SECONDS}]}))
    print(f"Verified legal line and authored mix: {SECONDS}s, {provider}")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider",choices=["kokoro","flite"],default="kokoro")
    produce(parser.parse_args().provider)
