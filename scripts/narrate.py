"""Generate the sample's clearly identified Flite test voice, cue by cue."""
import json
import subprocess
import tempfile
from pathlib import Path

project = json.loads(Path("projects/legal-mate.json").read_text())
rate = 24000
with tempfile.TemporaryDirectory() as temporary:
    folder = Path(temporary)
    text_file = folder / "line.txt"
    pcm = bytearray()
    scene_start = 0
    for scene in project["scenes"]:
        for cue in scene["captions"]:
            line = (cue["text"].replace("’", "'").replace("e5", "E five")
                    .replace("f7", "F seven").replace("e7", "E seven").replace("d5", "D five"))
            text_file.write_text(line)
            command = ["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                       f"flite=textfile={text_file}:voice=slt"]
            voice_format = ["-ar", str(rate), "-ac", "1", "-f", "s16le", "-"]
            spoken = subprocess.check_output(command + voice_format)
            window = (cue["to"] - cue["from"]) / project["fps"]
            speed = max(1, len(spoken) / (2 * rate * (window - 0.25)))
            if speed > 1:
                spoken = subprocess.check_output(command + ["-af", f"atempo={speed}"] + voice_format)
            start = int((scene_start + cue["from"]) * rate / project["fps"]) * 2
            pcm.extend(bytes(start - len(pcm)))
            pcm.extend(spoken)
        scene_start += scene["frames"]
    pcm.extend(bytes(scene_start * rate // project["fps"] * 2 - len(pcm)))
    subprocess.run(["ffmpeg","-y","-v","error","-f","s16le","-ar",str(rate),"-ac","1","-i","-",
                    "-af","loudnorm=I=-16:TP=-2:LRA=8","-b:a","96k","public/legal-narration.mp3"],input=pcm,check=True)
