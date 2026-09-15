"""BRIDGE1400 concept section: split the stepped stair line from the rest of the sketch, and turn the two GIFs into videos.

Run:  python tools/prepare_concept.py
In:   docs/assets/img/bridge1400/Original/Conceptual Sketch/Conceptual Section_1.png, Western Edge - Tourism.gif,
      Eastern Zone - Commercial.gif
Out:  docs/assets/img/bridge1400/concept-rest-{1200,2400}.webp   sketch without the stair (ink on alpha; CSS inverts in dark mode)
      docs/assets/img/bridge1400/concept-stair-{1200,2400}.webp  stair only, used as a CSS mask filled with --accent
      docs/assets/video/bridge1400-{west,east}.mp4 (+ -poster.jpg)
      content/images.json entries, plus the stair end points (% of the image) printed for content/projects.json
"""
import json
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Conceptual Sketch")
IMG = os.path.join(ROOT, "docs", "assets", "img", "bridge1400")
VID = os.path.join(ROOT, "docs", "assets", "video")
MANIFEST = os.path.join(ROOT, "content", "images.json")


def main():
    gray = np.asarray(Image.open(os.path.join(SRC, "Conceptual Section_1.png")).convert("L"))
    alpha = np.where(gray > 245, 0, np.minimum(255, np.round((255 - gray.astype(np.float32)) * 1.15))).astype(np.uint8)
    ink = Image.fromarray(np.where(alpha > 60, 255, 0).astype(np.uint8))
    # the stair is the thick line: opening removes the thin trees and people; flood-fill from its left end keeps only it
    thick = ink.filter(ImageFilter.MinFilter(11)).filter(ImageFilter.MaxFilter(11))
    t = np.asarray(thick)
    ys, xs = np.nonzero(t[:, :60])
    ImageDraw.floodfill(thick, (int(xs[len(xs) // 2]), int(ys[len(ys) // 2])), 128)
    core = np.asarray(thick) == 128
    grown = np.asarray(Image.fromarray(np.where(core, 255, 0).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
    stair = grown & (alpha > 0)
    # keep the tree trunks where they meet the line in the rest layer: only thick pixels count as stair
    a_stair = np.where(stair, alpha, 0).astype(np.uint8)
    a_rest = np.where(stair, 0, alpha).astype(np.uint8)
    y0, y1 = np.nonzero(alpha.any(1))[0][[0, -1]]
    x0, x1 = np.nonzero(alpha.any(0))[0][[0, -1]]
    box = (x0, y0, x1 + 1, y1 + 1)
    w, h = x1 + 1 - x0, y1 + 1 - y0
    manifest = json.load(open(MANIFEST, encoding="utf-8-sig"))
    for name, a in (("concept-rest", a_rest), ("concept-stair", a_stair)):
        im = Image.new("RGBA", (gray.shape[1], gray.shape[0]), (22, 21, 19, 255))
        im.putalpha(Image.fromarray(a))
        im = im.crop(box)
        for width in (1200, 2400):
            out = im if width >= w else im.resize((width, round(h * width / w)), Image.LANCZOS)
            out.save(os.path.join(IMG, f"{name}-{width}.webp"), quality=90, method=6)
        manifest[f"bridge1400/{name}"] = {"w": int(w), "h": int(h)}
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1)
    # stair end points: leftmost and rightmost stair pixels, centre of the line thickness there
    sy, sx = np.nonzero(core)
    for side, xe in (("west", sx.min()), ("east", sx.max())):
        yy = sy[np.abs(sx - xe) < 6]
        print(side, "x %.2f%%  y %.2f%%" % ((xe - x0) / w * 100, (yy.mean() - y0) / h * 100))
    print("image", w, h)

    os.makedirs(VID, exist_ok=True)
    for side, f in (("west", "Western Edge - Tourism.gif"), ("east", "Eastern Zone - Commercial.gif")):
        src, out = os.path.join(SRC, f), os.path.join(VID, f"bridge1400-{side}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-movflags", "+faststart", "-an", out],
                       check=True)
        Image.open(src).convert("RGB").save(os.path.join(VID, f"bridge1400-{side}-poster.jpg"), quality=85)
        print(side, os.path.getsize(out) // 1024, "KB", Image.open(src).size)


if __name__ == "__main__":
    main()
