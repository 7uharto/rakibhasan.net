"""Turn Rakib's hand-edited highlight reel into the website versions.

Run:  python tools/encode_reel.py
Input:  newest videos-original/Highlight Video/reel-master*.mp4   (Premiere export, not published)
Output: docs/assets/video/reel-1080.mp4   (desktop)
        docs/assets/video/reel-720.mp4    (phones)
        docs/assets/video/reel-poster.jpg (still before play / reduced motion)

Any black tail at the end of the export is detected and trimmed so the loop never
flashes black. Output is silent, tagged Rec. 709, and has its index at the start.
(tools/make_reel.py is the older automatic cutter, kept as a fallback.)
"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REEL_DIR = os.path.join(ROOT, "videos-original", "Highlight Video")


def latest_master():
    """Newest reel-master*.mp4 (e.g. 'reel-master v1.2.mp4'), so new versions need no code change."""
    masters = [os.path.join(REEL_DIR, f) for f in os.listdir(REEL_DIR)
               if f.lower().startswith("reel-master") and f.lower().endswith(".mp4")]
    if not masters:
        raise SystemExit(f"no reel-master*.mp4 in {REEL_DIR}")
    return max(masters, key=os.path.getmtime)


MASTER = latest_master()
OUT = os.path.join(ROOT, "docs", "assets", "video")
POSTER_AT = 1.0  # seconds into the reel for the still image
TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout)


def content_end(path):
    """End of real footage: start of a black tail that runs to the end, else full length."""
    total = duration(path)
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-vf", "blackdetect=d=0.1:pix_th=0.10",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    for start, end in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log):
        if total - float(end) < 0.15:  # black segment reaches the end of the file
            return float(start)
    return total


def encode(src, end, width, crf, maxrate_mbps, out):
    # setparams writes the Rec. 709 labels into the stream itself (the master has none)
    vf = (f"scale={width}:-2:flags=lanczos,format=yuv420p,"
          "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-t", f"{end:.3f}", "-vf", vf, "-an",
                    "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high",
                    "-maxrate", f"{maxrate_mbps}M", "-bufsize", f"{maxrate_mbps * 2}M",
                    *TAGS, "-movflags", "+faststart", out], check=True)
    print(f"{os.path.basename(out)}: {os.path.getsize(out) / 1e6:.1f} MB")


def main():
    os.makedirs(OUT, exist_ok=True)
    total, end = duration(MASTER), content_end(MASTER)
    print(f"master {total:.2f}s, footage ends {end:.2f}s, trimming {total - end:.2f}s")
    # targets: ~7 MB desktop, ~3 MB phone for a ~27 s silent loop
    encode(MASTER, end, 1920, 27, 2.5, os.path.join(OUT, "reel-1080.mp4"))
    encode(MASTER, end, 1280, 28, 1.2, os.path.join(OUT, "reel-720.mp4"))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(POSTER_AT), "-i", MASTER, "-frames:v", "1",
                    "-vf", "scale=1920:-2", "-q:v", "3", os.path.join(OUT, "reel-poster.jpg")], check=True)
    print(f"reel length {end:.2f}s")


if __name__ == "__main__":
    main()
