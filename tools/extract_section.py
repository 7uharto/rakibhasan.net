"""Render Rakib's Section AA SVG export to PNG with headless Chrome and crop it to the building.

Run:  python tools/extract_section.py   then  python tools/prepare_images.py
Input:  docs/assets/img/bridge1400/Original/Sections/260914 Transverse Section AA' v1.2.svg
Output: docs/assets/img/bridge1400/Original/Sections/section-aa.png

The SVG = one embedded render (no structure lines) + vector overlays (blue section-cut members, ground fade)
+ callout text and hairline leaders. Chrome renders the raster and the overlays; the Futura text and 0.2px
leaders do not show, and the callouts are rebuilt as HTML (content/projects.json, positions = leader end
points as % of this crop). Do not use the embedded PNG alone: it lacks the blue cut members.
"""
import os
import subprocess
from urllib.parse import quote

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Sections")
SRC = os.path.join(FOLDER, "260914 Transverse Section AA' v1.2.svg")
OUT = os.path.join(FOLDER, "section-aa.png")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCALE = 3                      # viewBox 1584 x 891 -> 4752 x 2673 px
CROP_SVG = (250, 40, 1350, 800)  # building + ground fade, in SVG units (callout % are relative to this box)


def main():
    shot = os.path.join(FOLDER, "_raw-section-aa.png")
    profile = os.path.join(os.environ.get("TEMP", FOLDER), "rakibhasan-chrome-section")
    url = "file:///" + quote(SRC.replace("\\", "/"), safe="/:")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                    f"--window-size={1584 * SCALE},{891 * SCALE}", "--default-background-color=00000000",
                    "--virtual-time-budget=20000", f"--screenshot={shot}", url],
                   check=True, capture_output=True, timeout=300)
    im = Image.open(shot).convert("RGBA")
    box = tuple(v * SCALE for v in CROP_SVG)
    im.crop(box).save(OUT)
    os.remove(shot)
    print("ok", os.path.relpath(OUT, ROOT), im.crop(box).size, "from", im.size)


if __name__ == "__main__":
    main()
