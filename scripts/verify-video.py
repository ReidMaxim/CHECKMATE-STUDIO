"""Check codec, dimensions and duration, then decode the entire export."""
import json
import subprocess
import sys
from pathlib import Path

video = sys.argv[1]
project = json.loads(Path("projects/legal-mate.json").read_text())
info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video]))
picture = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
audio = next(stream for stream in info["streams"] if stream["codec_type"] == "audio")
expected_seconds = sum(scene["frames"] for scene in project["scenes"]) / project["fps"]
if (picture["codec_name"], picture["pix_fmt"], picture["width"], picture["height"], picture["r_frame_rate"]) != (
    "h264", "yuv420p", project["width"], project["height"], f'{project["fps"]}/1'
):
    raise SystemExit("Unexpected video encoding")
if audio["codec_name"] != "aac" or abs(float(info["format"]["duration"]) - expected_seconds) > 0.1:
    raise SystemExit("Unexpected audio encoding or duration")
subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", video, "-f", "null", "-"], check=True)
print(f"Fully decoded {expected_seconds:g}s H.264/AAC, {picture['width']}×{picture['height']} at {picture['r_frame_rate']} fps")
