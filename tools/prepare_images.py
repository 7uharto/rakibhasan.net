"""Make web-ready images for the site from the InDesign Links folder and the portfolio PDF.

Run:  python tools/prepare_images.py
Output: site/assets/img/<project>/<name>-<width>.webp  +  content/images.json (sizes)
Re-running skips images that already exist.
"""
import json
import os
import pymupdf
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS = r"P:\01. Portfolio\2602 Portfolio\Links"
PDF = r"P:\01. Portfolio\2602 Portfolio\260226 Portfolio.pdf"
OUT = os.path.join(ROOT, "docs", "assets", "img")
MANIFEST = os.path.join(ROOT, "content", "images.json")
WIDTHS = (1200, 2400)
# transparent images to trim to their visible pixels (headshot circle has empty margins)
CROP_TO_CONTENT = {"Headshot.psd"}

# project -> list of (output name, source). Source is a Links filename or "pdf:<page>".
IMAGES = {
    "about": [("headshot", "Headshot.psd")],
    "bridge1400": [
        ("hero", "F2.jpg"),
        ("site", "250729 Site Micro.png"),
        ("massing", "pdf:5"),
        ("plans", "pdf:6"),
        ("section-aa", "pdf:7"),
        ("section-bb", "pdf:8"),
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
    im = Image.open(os.path.join(LINKS, src))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        if src in CROP_TO_CONTENT:
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
