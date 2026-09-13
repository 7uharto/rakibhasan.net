"""Make the public website copy of the resume.

Run:  python tools/make_site_resume.py
Takes the resume's HTML source, swaps in the website email, removes the phone item
(so the contact line reflows with no gap), prints it to PDF with headless Chrome and
writes docs/assets/Md-Rakib-Hasan-Resume.pdf.
When a new resume version exists, point SRC at its email-index HTML and re-run.
"""
import os
import re
import subprocess
import tempfile
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = r"D:\pCloud Offline Sync Folders\04. Projects\Claude\01. Resume Automation\output\email-index-v1.8.html"
OUT = os.path.join(ROOT, "docs", "assets", "Md-Rakib-Hasan-Resume.pdf")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OLD_EMAIL = "rakibhasan.wsu@gmail.com"
NEW_EMAIL = "rakib@rakibhasan.net"


def site_html(html):
    html = html.replace(OLD_EMAIL, NEW_EMAIL)
    # drop the whole phone <span> (icon + number), not just the text
    html, n = re.subn(r'\s*<span><svg[^>]*>(?:(?!</span>).)*?\+1 \(\d{3}\) \d{3}-\d{4}</span>', "", html, flags=re.S)
    if n != 1:
        raise SystemExit(f"expected 1 phone item, found {n}")
    return html


def main():
    html = site_html(open(SRC, encoding="utf-8").read())
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "index.html")
        raw = os.path.join(tmp, "resume.pdf")
        open(page, "w", encoding="utf-8").write(html)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={raw}", "file:///" + page.replace("\\", "/")],
                       check=True, capture_output=True, timeout=120)
        with pymupdf.open(raw) as doc:  # close before the temp folder is deleted
            doc.set_metadata({"title": "Md. Rakib Hasan - Resume", "author": "Md. Rakib Hasan"})
            doc.save(OUT, garbage=4, deflate=True)
    out = pymupdf.open(OUT)
    text = "".join(p.get_text() for p in out)
    print("saved", OUT)
    print("pages:", out.page_count, "| new email:", NEW_EMAIL in text,
          "| old email:", OLD_EMAIL in text, "| phone:", "432-6595" in text)


if __name__ == "__main__":
    main()
