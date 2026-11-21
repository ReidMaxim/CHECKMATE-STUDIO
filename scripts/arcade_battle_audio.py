"""Produce the battle cut's voice and original effects with the existing Kokoro pipeline."""
from array import array
from math import exp, pi, sin
from pathlib import Path
import subprocess
import tempfile

from directors_cut import RATE, ROOT, speaker, trim, write_wave

SECONDS = 14.5
LINES = [(1.66, "Black takes the queen!"), (6.22, "Check. Only one reply."),
         (8.36, "The knight is ready."), (10.32, "Checkmate!"), (12.03, "White wins.")]
CUES = [(89/30, [330, 196, 98]), (188/30, [392, 587]),
        (311/30, [392, 523, 659, 784])]


def main():
    say = speaker("kokoro", ROOT/".cache/kokoro", "am_puck", 1.06)
    mix = array("h", [0]) * round(RATE*SECONDS)
    for start, text in LINES:
        at = round(start*RATE)
        voice = trim(say(text))
        mix[at:at+len(voice)] = array("h", (round(.73*sample) for sample in voice))
    for start, notes in CUES:
        for index, freq in enumerate(notes):
            at = round((start+index*.082)*RATE)
            for i in range(round(.15*RATE)):
                t=i/RATE
                amplitude=2500*min(1,i/75)*exp(-23*t)
                mix[at+i] += round(amplitude*(sin(2*pi*freq*t)+.24*sin(6*pi*freq*t)))
    with tempfile.TemporaryDirectory() as directory:
        wav=Path(directory)/"battle.wav"
        write_wave(wav,mix)
        subprocess.run(["ffmpeg","-v","error","-y","-i",str(wav),"-af",
                        "loudnorm=I=-16:TP=-2.5:LRA=8","-codec:a","libmp3lame",
                        "-b:a","96k",str(ROOT/"public/arcade-battle.mp3")],check=True)


if __name__ == "__main__":
    main()
