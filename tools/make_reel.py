"""Cut the silent highlight reel used behind the home headline and on the Films page.

Run:  python tools/make_reel.py
Input:  videos-original/<key>.mp4  or the original Vimeo file names (matched by project key)
Output: docs/assets/video/reel-1080.mp4   (desktop)
        docs/assets/video/reel-720.mp4    (phones)
        docs/assets/video/reel-poster.jpg (shown before play and for reduced motion)
The reel is small enough to publish with the site on GitHub (no pCloud dependency).
Edit CLIPS to change which moments appear; times are in seconds into each source film.
"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "videos-original")
OUT = os.path.join(ROOT, "docs", "assets", "video")

CLIP = 3.0   # seconds per clip
FADE = 0.6   # cross-fade between clips
# (film key, start second): calm exterior/facade moments first, a few interiors for rhythm
CLIPS = [
    ("wecon-rainforest", 214),
    ("p2p-healthcare", 25),
    ("wecon-chowdhury-arcade", 50),
    ("wecon-shukrana", 76),
    ("p2p-healthcare", 44),
    ("wecon-chowdhury-arcade", 118),
    ("wecon-shukrana", 100),
    ("wecon-rainforest", 13),
]


def find_source(key):
    for name in os.listdir(SRC):
        stem = os.path.splitext(name)[0].lower()
        project = re.sub(r"[^a-z0-9]+", "-", re.split(r",|___", stem)[0]).strip("-")
        if name.lower().endswith(".mp4") and project == key:
            return os.path.join(SRC, name)
    raise SystemExit(f"no source video for {key} in {SRC}")


def encode(width, crf, out):
    args = ["ffmpeg", "-y", "-v", "error"]
    for key, start in CLIPS:
        args += ["-ss", str(start), "-t", str(CLIP), "-i", find_source(key)]
    # normalise every clip (the films mix 24 and 30 fps), then chain cross-fades
    parts = [f"[{i}:v]fps=30,scale={width}:-2:flags=lanczos,setsar=1,format=yuv420p[v{i}]" for i in range(len(CLIPS))]
    last, offset = "v0", CLIP - FADE
    for i in range(1, len(CLIPS)):
        parts.append(f"[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.2f}[x{i}]")
        last, offset = f"x{i}", offset + CLIP - FADE
    parts.append(f"[{last}]format=yuv420p[out]")  # xfade can output 4:4:4; browsers need 4:2:0
    args += ["-filter_complex", ";".join(parts), "-map", "[out]", "-an",
             "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high",
             "-movflags", "+faststart", out]
    subprocess.run(args, check=True)
    print(f"{os.path.basename(out)}: {os.path.getsize(out) / 1e6:.1f} MB")


def main():
    os.makedirs(OUT, exist_ok=True)
    encode(1920, 27, os.path.join(OUT, "reel-1080.mp4"))
    encode(1280, 28, os.path.join(OUT, "reel-720.mp4"))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1.2", "-i", os.path.join(OUT, "reel-1080.mp4"),
                    "-frames:v", "1", "-vf", "scale=1920:-2", "-q:v", "3", os.path.join(OUT, "reel-poster.jpg")], check=True)
    total = len(CLIPS) * CLIP - (len(CLIPS) - 1) * FADE
    print(f"reel length {total:.1f}s, {len(CLIPS)} clips")


if __name__ == "__main__":
    main()
