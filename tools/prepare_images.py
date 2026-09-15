"""Make web-ready images for the site from the InDesign Links folder and the portfolio PDF.

Run:  python tools/prepare_images.py
Output: site/assets/img/<project>/<name>-<width>.webp  +  content/images.json (sizes)
Re-running skips images that already exist.
"""
import json
import os
import numpy as np
import pymupdf
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS = r"P:\01. Portfolio\2602 Portfolio\Links"
PDF = r"P:\01. Portfolio\2602 Portfolio\260226 Portfolio.pdf"
OUT = os.path.join(ROOT, "docs", "assets", "img")
MANIFEST = os.path.join(ROOT, "content", "images.json")
WIDTHS = (1200, 2400)
# transparent images to trim to their visible pixels (headshot circle has empty margins)
CROP_TO_CONTENT = {"Headshot.psd", "site-transparent.png"}
# hair-edge halo cleanup only: it recolours semi-transparent pixels, which would darken soft fades (site map)
DECONTAMINATE = {"Headshot.psd"}
# hand sketches on white paper: brightness becomes transparency, so only the ink is kept (works on dark pages too)
SKETCHES = os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Conceptual Sketch")
# floor plans rendered from SVG by tools/render_plans.py (white background, common crop)
PLANS = os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Plans", "render")
INK_TO_ALPHA = {"Conceptual Section_1.png", "sec_1.png", "sec_2.png", "plan_1.png", "plan_2.png", "plan_3.png",
                "elevation_1.png"}

# project -> list of (output name, source). Source is a Links filename or "pdf:<page>".
IMAGES = {
    "about": [("headshot", "Headshot.psd")],
    "bridge1400": [
        ("hero", "F2.jpg"),
        ("site", os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Site", "site-transparent.png")),
        ("sketch-section-1", os.path.join(SKETCHES, "sec_1.png")),
        ("sketch-section-2", os.path.join(SKETCHES, "sec_2.png")),
        ("sketch-plan-1", os.path.join(SKETCHES, "plan_1.png")),
        ("sketch-plan-2", os.path.join(SKETCHES, "plan_2.png")),
        ("sketch-plan-3", os.path.join(SKETCHES, "plan_3.png")),
        ("sketch-elevation", os.path.join(SKETCHES, "elevation_1.png")),
        ("concept-section", os.path.join(SKETCHES, "Conceptual Section_1.png")),
        *[(f"plan-level-{lv}", os.path.join(PLANS, f"level-{lv}.png")) for lv in ("1", "2", "3", "4", "5", "6-9", "10", "12-13")],
        ("structure-nw", os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Structural Axon", "Structural Axon NW.pdf")),
        ("structure-se", os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Structural Axon", "Structural Axon SE.pdf")),
        ("section-aa", os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Sections", "section-aa v1.0.png")),
        ("section-bb", os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Sections", "section-bb.png")),
        ("lobby-blowup", os.path.join(ROOT, "docs", "assets", "img", "bridge1400", "Original", "Sections", "lobby-blowup.png")),
    ],
    "professional-work": [
        ("wecon-northdale", "240120_WECON Northdale_Night_A.jpg"),
        ("shafique-residence-2", "240303_Shafique TWO_A_142226.jpg"),
        ("wecon-south-lawn", "WECON-Southlawn-A D5_Image-2_20231126_120903.jpg"),
        ("wecon-southdale", "WECON Southdale xD5_Image-7_20231018_154118.jpg"),
        ("rayan-house", "Rayan House 0 D5_Image 7_20231207_154703.jpg"),
        ("islami-bank-apt", "Nazrul Islam Islami Bank Mozaffar Nagar_B_D5_Image_20231217_162121.jpg"),
        ("wecon-haqs-bay", "WECON Haq's Bay 20240215 FINAL.png"),
        ("wecon-mehedibag", "WECON Mehedibag_FRONT_D5_Image_20240130_131109.jpg"),
        ("konar-bari", "Konarbari (4).jpg"),
        ("harun-vandar-mosque", "D5_Image_20220721_170203_3.jpg"),
        ("almas-shimul-office", "210927 Almas Shimul Home Office 3.png"),
        ("shafi-motors-office", "210622 Common Space 2.png"),
        ("tower-c-night", "C_Night 2.8x4.5.png"),
        ("tower-c8", "C8.2.jpg"),
        ("tower-a10", "A 10 D5_Image_20230304_111351 copy.jpg"),
        ("commercial-d5c", "D5_C_20231224_141741.jpg"),
        ("residence-000", "000.JPG"),
        ("residence-20220622", "D5_Image_20220622_154724.jpg"),
        ("residence-20230805", "~D5_Image_20230805_192348.png"),
        ("building-a", "a.jpg"),
    ],
    "solaris": [
        ("hero", "Cover.psd"),
        ("exterior-day", "Exterior Day.psd"),
        ("retail-corridor", "6.png"),
        ("context", "pdf:15"),
        ("site", "pdf:16"),
        ("axon", "pdf:17"),
        ("wall-sections", "pdf:18"),
    ],
    "forestreat": [
        ("hero", "+ F_Courtyard.jpg"),
        ("entry", "Longrender.psd"),
        ("concept", "pdf:10"),
        ("form", "pdf:11"),
        ("plans", "pdf:12"),
        ("section", "pdf:13"),
    ],
    "bussin-blocks": [
        ("hero", "Cover_1.psd"),
        ("silo-boulevard", "F 1 Ex Silo Boulevard_inpainting01 copy.jpg"),
        ("idaho-road-entry", "F 11 Entry(1)_inpainting03.png"),
        ("waiting-hall", "F 4 Bus INT_inpainting01.png"),
        ("boarding-zone", "X3 Bus(2) copy.jpg"),
        ("concept", "pdf:21"),
        ("masterplan", "pdf:22"),
        ("cote", "pdf:23"),
    ],
}


def decontaminate(im, radius=12):
    """Remove the white halo on cut-out edges (e.g. hair).

    Semi-transparent edge pixels still carry the old white background color.
    Replace their color with the average of nearby fully opaque pixels.
    """
    rgba = np.asarray(im, dtype=np.float32)
    alpha = rgba[..., 3]
    solid = (alpha >= 250).astype(np.float32)

    def blur(channel):  # channel values 0-255; PIL blurs only 8-bit images
        img = Image.fromarray(np.clip(channel, 0, 255).astype(np.uint8), "L")
        return np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)

    weight = blur(solid * 255) / 255 + 1e-4
    out = rgba.copy()
    edge = (alpha > 0) & (alpha < 250)
    for c in range(3):
        spread = blur(rgba[..., c] * solid) / weight
        out[..., c][edge] = spread[edge]
    # thin, faint fringe pixels add haze; fade them out
    out[..., 3] = np.where(alpha < 40, 0, alpha)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def load(src, doc):
    if src.startswith("pdf:"):
        page = doc[int(src[4:]) - 1]
        # hide the portfolio's "Page  N" labels so drawings don't read as PDF pages
        words = page.get_text("words")
        for i, w in enumerate(words):
            if w[4] == "Page" and i + 1 < len(words) and words[i + 1][4].isdigit():
                r = pymupdf.Rect(w[:4]) | pymupdf.Rect(words[i + 1][:4])
                page.add_redact_annot(r + (-1, -1, 1, 1), fill=False)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
        zoom = 3200 / page.rect.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if src.lower().endswith(".pdf"):  # single-drawing PDF export (Revit): render, trim the white margins
        page = pymupdf.open(src)[0]
        zoom = 2400 / page.rect.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        ink = im.convert("L").point(lambda v: 255 if v < 245 else 0).getbbox()
        return im.crop((max(ink[0] - 40, 0), max(ink[1] - 40, 0), min(ink[2] + 40, im.width), min(ink[3] + 40, im.height)))
    if os.path.basename(src) in INK_TO_ALPHA:
        gray = Image.open(src).convert("L")  # white paper -> 0 alpha, black ink -> full alpha
        alpha = Image.eval(gray, lambda v: 0 if v > 245 else min(255, round((255 - v) * 1.15)))
        im = Image.new("RGBA", gray.size, (22, 21, 19, 255))  # --ink colour; dark mode inverts it in CSS
        im.putalpha(alpha)
        return im.crop(alpha.getbbox())
    im = Image.open(src if os.path.isabs(src) else os.path.join(LINKS, src))  # absolute = file outside Links
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        if os.path.basename(src) in CROP_TO_CONTENT:
            if os.path.basename(src) in DECONTAMINATE:
                im = decontaminate(im)
            return im.crop(im.split()[-1].getbbox())  # keep transparency, no white fill
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def main():
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    manifest = json.load(open(MANIFEST, encoding="utf-8-sig")) if os.path.exists(MANIFEST) else {}
    doc = pymupdf.open(PDF)
    for project, items in IMAGES.items():
        os.makedirs(os.path.join(OUT, project), exist_ok=True)
        for name, src in items:
            key = f"{project}/{name}"
            paths = [os.path.join(OUT, project, f"{name}-{w}.webp") for w in WIDTHS]
            if key in manifest and all(os.path.exists(p) for p in paths):
                continue
            im = load(src, doc)
            for w, path in zip(WIDTHS, paths):
                copy = im.copy()
                if copy.width > w:
                    copy = copy.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
                copy.save(path, "WEBP", quality=80, method=6)
            manifest[key] = {"w": im.width, "h": im.height}
            print("ok", key)
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
