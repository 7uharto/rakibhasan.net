"""Make the public website copy of the resume: same PDF with the phone number removed.

Run:  python tools/make_site_resume.py
Reads the latest email resume and writes site/assets/Md-Rakib-Hasan-Resume.pdf.
When a new resume version exists, update SRC below and re-run.
"""
import os
import re
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = r"D:\pCloud Offline Sync Folders\04. Projects\Claude\01. Resume Automation\PDFs\Resume - Md. Rakib Hasan - email v2.0.pdf"
OUT = os.path.join(ROOT, "docs", "assets", "Md-Rakib-Hasan-Resume.pdf")
PHONE = re.compile(r"^(\+1|\(\d{3}\)|\d{3}-\d{4})$")


def main():
    doc = pymupdf.open(SRC)
    for page in doc:
        words = [w for w in page.get_text("words") if PHONE.match(w[4])]
        if not words:
            continue
        rect = pymupdf.Rect(words[0][:4])
        for w in words[1:]:
            rect |= pymupdf.Rect(w[:4])
        # widen left to catch the phone icon that sits before the number
        area = pymupdf.Rect(rect.x0 - 14, rect.y0 - 1, rect.x1 + 1, rect.y1 + 1)
        page.add_redact_annot(area, fill=False)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
        for link in page.get_links():
            if link.get("uri", "").startswith("tel:"):
                page.delete_link(link)
    doc.set_metadata({"title": "Md. Rakib Hasan - Resume", "author": "Md. Rakib Hasan"})
    doc.save(OUT, garbage=4, deflate=True)
    text = "".join(p.get_text() for p in pymupdf.open(OUT))
    print("saved", OUT, "| phone still present:", "432-6595" in text)


if __name__ == "__main__":
    main()
