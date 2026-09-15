"""Render Section BB and the lobby blow-up from Rakib's SVG exports with headless Chrome.

Run:  python tools/render_section_bb.py   then  python tools/prepare_images.py
Input (gitignored originals, both 1920x1080 viewBox, vector only):
  docs/assets/img/bridge1400/Original/Sections/Full of the Blowup Lobby.svg  (section + a copy of the blow-up top-left)
  docs/assets/img/bridge1400/Original/Sections/Blowup Lobby.svg              (the blow-up alone)
Output: Original/Sections/section-bb.png, Original/Sections/lobby-blowup.png

The blow-up copy inside the full export is painted out: the page shows the blow-up as its own figure,
and a coded callout on Section BB's dotted box points to it (callout % are relative to CROP_FULL).
"""
import os
import subprocess
from urllib.parse import quote

from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Sections")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# (source, output, scale, crop box in rendered px or None = trim to drawn area, white-out boxes in rendered px)
JOBS = [
    ("Full of the Blowup Lobby.svg", "section-bb.png", 2, (1000, 280, 3840, 2160), [(150, 320, 1740, 1100)]),
    ("Blowup Lobby.svg", "lobby-blowup.png", 3, None, []),
]
PAD = 40


def render(src, scale, name):
    shot = os.path.join(FOLDER, f"_raw-{name}")
    profile = os.path.join(os.environ.get("TEMP", FOLDER), "rakibhasan-chrome-section-bb")
    url = "file:///" + quote(os.path.join(FOLDER, src).replace("\\", "/"), safe="/:")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                    f"--window-size={1920 * scale},{1080 * scale}", "--default-background-color=ffffffff",
                    "--virtual-time-budget=30000", f"--screenshot={shot}", url],
                   check=True, capture_output=True, timeout=600)
    im = Image.open(shot).convert("RGB")
    os.remove(shot)
    return im


def main():
    for src, out, scale, crop, blanks in JOBS:
        im = render(src, scale, out)
        draw = ImageDraw.Draw(im)
        for box in blanks:
            draw.rectangle(box, fill="white")
        if crop is None:  # trim to the drawn (non-white) area
            b = im.convert("L").point(lambda v: 255 if v < 245 else 0).getbbox()
            crop = (max(b[0] - PAD, 0), max(b[1] - PAD, 0), min(b[2] + PAD, im.width), min(b[3] + PAD, im.height))
        im = im.crop(crop)
        im.save(os.path.join(FOLDER, out))
        print("ok", out, im.size)


if __name__ == "__main__":
    main()
