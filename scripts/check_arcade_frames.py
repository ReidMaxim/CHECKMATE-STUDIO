"""Detect the repeated header tiles observed in the Impact Polish export."""
import argparse
from pathlib import Path
from statistics import pstdev
import subprocess

WIDTH, HEIGHT = 108, 192


def duplicated_headers(path):
    samples = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-an", "-vf",
                                       "scale=108:192:flags=area,format=gray", "-f", "rawvideo", "-"])
    for n, offset in enumerate(range(0, len(samples), WIDTH*HEIGHT)):
        frame = memoryview(samples)[offset:offset+WIDTH*HEIGHT]
        def patch(start):
            return b"".join(frame[y*WIDTH+6:y*WIDTH+63] for y in range(start,start+14))
        header = patch(21)
        if pstdev(header) < 7:
            continue
        for row in (64,65,66,107,108,109,151,152,153):
            candidate = patch(row)
            if sum(abs(a-b) for a,b in zip(header,candidate,strict=True)) < 3.5*len(header):
                yield n
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expect-defect", action="store_true")
    args = parser.parse_args()
    frames = list(duplicated_headers(args.file))
    print(f"{args.file.name}: {len(frames)} repeated header frames. First indices: {frames[:12]}")
    if bool(frames) != args.expect_defect:
        parser.exit(1,"Frame regression check failed\n")
