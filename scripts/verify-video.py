"""Check codec, dimensions and duration, then decode the entire export."""
import json
import re
import subprocess
import sys
from pathlib import Path

video = sys.argv[1]
project = json.loads(Path(sys.argv[2] if len(sys.argv) > 2 else "projects/legal-mate.json").read_text())
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
if project.get("presentation") == "director":
    levels = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-vn", "-af",
                             "silencedetect=noise=-45dB:d=2.2,volumedetect", "-f", "null", "-"],
                            capture_output=True, text=True, check=True).stderr
    peak = re.search(r"max_volume: (-?[\d.]+) dB", levels)
    if not peak or not -12 <= float(peak[1]) <= -1:
        raise SystemExit("Director audio peak outside -12 to -1 dBFS")
    if "silence_start:" in levels:
        raise SystemExit("Director audio contains an unexpected silence of at least 2.2 seconds")
    print(f"Mixed audio peak {peak[1]} dBFS, no silent interval of 2.2 seconds")
print(f"Fully decoded {expected_seconds:g}s H.264/AAC, {picture['width']}×{picture['height']} at {picture['r_frame_rate']} fps")
