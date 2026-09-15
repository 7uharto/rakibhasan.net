"""Render the BRIDGE1400 site map from Rakib's Illustrator SVG with a transparent edge fade.

Run:  python tools/render_site_map.py
Input:  docs/assets/img/bridge1400/Original/Site/*.svg   (Illustrator export, not published)
Output: docs/assets/img/bridge1400/Original/Site/site-transparent.png   (2592 px, alpha)
Then:   python tools/prepare_images.py   (makes the web copies)

Why: the SVG fades its edge to solid white (<circle class="st3"> with a white radial gradient),
which shows as a white box on the off-white page and in dark mode. This removes that circle and
applies the same fade as an alpha mask, so the map dissolves into any background.
"""
import glob
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Site")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = os.path.join(FOLDER, "site-transparent.png")
SIZE = 1296   # SVG viewBox
SCALE = 2     # 2592 px output

FADE = """
<radialGradient id="fade" cx="648" cy="648" r="581.9" gradientUnits="userSpaceOnUse">
  <stop offset=".5" stop-color="#fff" stop-opacity="1"/>
  <stop offset=".6" stop-color="#fff" stop-opacity=".7"/>
  <stop offset=".7" stop-color="#fff" stop-opacity=".5"/>
  <stop offset=".8" stop-color="#fff" stop-opacity=".25"/>
  <stop offset=".9" stop-color="#fff" stop-opacity=".08"/>
  <stop offset="1" stop-color="#fff" stop-opacity="0"/>
</radialGradient>
<mask id="fade-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="1296" height="1296">
  <rect width="1296" height="1296" fill="url(#fade)"/>
</mask>
</defs>"""


def main():
    svgs = [p for p in glob.glob(os.path.join(FOLDER, "*.svg")) if not p.endswith("-transparent.svg")]
    if not svgs:
        raise SystemExit(f"no SVG in {FOLDER}")
    src = max(svgs, key=os.path.getmtime)
    svg = open(src, encoding="utf-8").read()
    svg, removed = re.subn(r'<circle class="st3"[^>]*/>', "", svg)  # the white fade overlay
    svg = svg.replace("</defs>", FADE, 1).replace('<g id="Layer_1">', '<g id="Layer_1" mask="url(#fade-mask)">', 1)
    tmp_svg = os.path.join(FOLDER, "_render-transparent.svg")
    tmp_html = os.path.join(FOLDER, "_render.html")
    open(tmp_svg, "w", encoding="utf-8").write(svg)
    open(tmp_html, "w", encoding="utf-8").write(
        f'<!doctype html><html><head><style>html,body{{margin:0;background:transparent}}'
        f'img{{display:block;width:{SIZE}px;height:{SIZE}px}}</style></head>'
        f'<body><img src="_render-transparent.svg"></body></html>')
    profile = os.path.join(os.environ.get("TEMP", FOLDER), "rakibhasan-chrome-render")
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files", "--default-background-color=00000000",
                        f"--force-device-scale-factor={SCALE}", f"--window-size={SIZE},{SIZE}",
                        "--virtual-time-budget=20000", f"--user-data-dir={profile}",
                        f"--screenshot={OUT}", "file:///" + tmp_html.replace("\\", "/")],
                       capture_output=True, timeout=180, check=True)
    finally:
        for p in (tmp_svg, tmp_html):
            if os.path.exists(p):
                os.remove(p)
    print(f"{os.path.basename(src)} -> {os.path.basename(OUT)} (white fade circles removed: {removed})")


if __name__ == "__main__":
    main()
