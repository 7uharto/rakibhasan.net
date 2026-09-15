"""Clean Illustrator SVG exports so they can be inlined in the page.

Run:  python tools/prepare_svgs.py
Input:  docs/assets/img/bridge1400/Original/Massing/Massing Diagram-0N.svg (gitignored originals)
Output: content/svg/bridge1400/massing-N.svg (read and inlined by build.py)

- black strokes/fills follow the page text colour (currentColor), so they work in light and dark mode
- Illustrator's .st0/.st1 class names are made unique per file (all 8 share one page)
- ids, comments and unstyled glyph outlines (never drawn) are removed
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Massing")
OUT = os.path.join(ROOT, "content", "svg", "bridge1400")


def clean(s, prefix):
    s = re.sub(r"<\?xml.*?\?>|<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r'\s(?:id|version|xmlns:xlink)="[^"]*"', "", s)
    s = re.sub(r"\bst(\d+)\b", lambda m: f"{prefix}s{m.group(1)}", s)
    s = re.sub(r"#000\b", "currentColor", s)
    s = re.sub(r"<line (?![^>]*class=)[^>]*/>", "", s)  # no stroke set = invisible outlined text
    s = re.sub(r"<g>\s*</g>", "", s)
    s = re.sub(r"\n\s*\n+", "\n", s).strip()
    return s.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)


def main():
    os.makedirs(OUT, exist_ok=True)
    for i in range(1, 9):
        src = os.path.join(SRC, f"Massing Diagram-0{i}.svg")
        out = os.path.join(OUT, f"massing-{i}.svg")
        s = clean(open(src, encoding="utf-8").read(), f"m{i}")
        open(out, "w", encoding="utf-8").write(s + "\n")
        print("ok", os.path.relpath(out, ROOT), len(s), "bytes")


if __name__ == "__main__":
    main()
