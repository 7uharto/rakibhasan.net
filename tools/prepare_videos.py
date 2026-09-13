"""Make poster frames and a size/duration list for the website films.

Run:  python tools/prepare_videos.py
Input:  videos-original/*.mp4          (Vimeo downloads, not published in the repo)
Output: docs/assets/video/<slug>.jpg   (poster frame shown before play, published with the site)
        content/videos.json            (duration, dimensions, size per video)

The videos themselves are NOT re-encoded: Vimeo's 1080p downloads are already ~5 Mbps
H.264 with the index at the start (streams immediately). A CRF 23 re-encode tested on
2026-09-13 saved only 30% at SSIM 0.98. The files are hosted in the pCloud Public Folder
as rakibhasan.net/videos/<slug>.mp4 (see VIDEO_BASE in content/site.json).
"""
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "videos-original")
POSTERS = os.path.join(ROOT, "docs", "assets", "video")
MANIFEST = os.path.join(ROOT, "content", "videos.json")
# poster frame time in seconds, picked from contact sheets (exterior facade shots)
POSTER_AT = {"p2p-healthcare": 27, "wecon-shukrana": 102, "wecon-rainforest": 218, "wecon-chowdhury-arcade": 52}


def slug(name):
    """'wecon_shukrana,_chattogram,_bd___residential...' -> 'wecon-shukrana'"""
    project = re.split(r",|___", os.path.splitext(name)[0])[0]
    return re.sub(r"[^a-z0-9]+", "-", project.lower()).strip("-")


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_entries",
                          "format=duration:stream=codec_type,width,height", path],
                         capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    return float(data["format"]["duration"]), video["width"], video["height"]


def main():
    os.makedirs(POSTERS, exist_ok=True)
    manifest = {}
    for name in sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp4")):
        key = slug(name)
        src = os.path.join(SRC, name)
        duration, w, h = probe(src)
        poster = os.path.join(POSTERS, f"{key}.jpg")
        if not os.path.exists(poster):
            # chosen frame, else 30% in (past the opening fade)
            at = POSTER_AT.get(key, duration * 0.3)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", src,
                            "-frames:v", "1", "-vf", "scale=1600:-2", "-q:v", "3", poster], check=True)
        manifest[key] = {"duration": round(duration), "width": w, "height": h,
                         "mb": round(os.path.getsize(src) / 1e6, 1)}
        print(key, manifest[key], flush=True)
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
