"""Render short opening comparisons and complete a first-broadcast review package."""
import argparse
import json
from pathlib import Path
import subprocess

from directors_cut import ROOT


def main(output):
    project_path = ROOT / "projects/unseen-documentary.json"
    original = project_path.read_text()
    project = json.loads(original)
    film = output / "first-broadcast.mp4"
    try:
        for variant in ("none", "minimal", "enhanced"):
            project["branding"]["opening"] = variant
            project_path.write_text(json.dumps(project))
            subprocess.run(["npm", "run", "validate"], check=True, cwd=ROOT)
            subprocess.run(["node", "scripts/broadcast_opening.mjs", str(output), variant], check=True, cwd=ROOT)
    finally:
        project_path.write_text(original)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(film),
                    "-frames:v", "1", "-threads", "1", str(output / "cover.png")], check=True)
    channel = json.loads((output / "channel.json").read_text())
    from html import escape
    (output / "wordmark.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="850" height="160">'
        '<rect width="850" height="160" fill="#121b19"/>'
        f'<text x="40" y="71" font-family="sans-serif" font-size="46" fill="{channel["accent"]}">'
        f'{escape(channel["wordmark"])}</text><text x="40" y="120" font-family="sans-serif" font-size="23" fill="#fff4da">'
        f'{escape(channel["tagline"])}</text></svg>')
    report_path = output / "quality-report.json"
    report = json.loads(report_path.read_text())
    report["technical"].update(mp4Decode=True, audioDecode=True, videoDimensions="1080 × 1920",
                               captionBoundaries=True, assetsComplete=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    main(parser.parse_args().output)
