"""Render the BRIDGE1400 floor-plan SVGs (Revit/Illustrator exports, 1-21 MB) to PNG with headless Chrome.

Run:  python tools/render_plans.py   then  python tools/prepare_images.py
Input:  docs/assets/img/bridge1400/Original/Plans/Plan_<n> copy.svg (gitignored originals, 2000x2000 viewBox)
Output: docs/assets/img/bridge1400/Original/Plans/render/level-<id>.png

All plans share one viewBox, so they are cropped with ONE common box (union of their drawn areas):
the building stays in the same place when a visitor switches levels.
"""
import os
import subprocess
from urllib.parse import quote

from PIL import Image, ImageChops

Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Plans")
OUT = os.path.join(FOLDER, "render")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SIZE = 2600  # screenshot size; the 2000 viewBox scales to fit
PAD = 30
# source file number -> level id (Plan_9 is the typical guest-room floor, Levels 6 to 9; no Level 11 plan)
LEVELS = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 9: "6-9", 10: "10", 12: "12-13"}


def main():
    os.makedirs(OUT, exist_ok=True)
    profile = os.path.join(os.environ.get("TEMP", OUT), "rakibhasan-chrome-plans")
    raw = {}
    for n, level in LEVELS.items():
        src = os.path.join(FOLDER, f"Plan_{n} copy.svg")
        shot = os.path.join(OUT, f"_raw-{level}.png")
        url = "file:///" + quote(src.replace("\\", "/"), safe="/:")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                        f"--window-size={SIZE},{SIZE}", "--default-background-color=ffffffff",
                        "--virtual-time-budget=20000", f"--screenshot={shot}", url],
                       check=True, capture_output=True, timeout=300)
        raw[level] = Image.open(shot).convert("RGB")
        print("rendered", level)
    box = None
    for im in raw.values():  # union of non-white areas
        diff = ImageChops.difference(im, Image.new("RGB", im.size, "white")).convert("L").point(lambda v: 255 if v > 6 else 0)
        b = diff.getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    box = (max(box[0] - PAD, 0), max(box[1] - PAD, 0), min(box[2] + PAD, SIZE), min(box[3] + PAD, SIZE))
    for level, im in raw.items():
        im.crop(box).save(os.path.join(OUT, f"level-{level}.png"))
        os.remove(os.path.join(OUT, f"_raw-{level}.png"))
    print("crop box", box)


if __name__ == "__main__":
    main()
