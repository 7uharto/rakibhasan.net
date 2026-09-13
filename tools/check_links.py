"""Check that every local link and image in the built site exists.

Run:  python tools/check_links.py
"""
import glob
import os
import re

SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

checked = missing = 0
for page in glob.glob(os.path.join(SITE, "**", "index.html"), recursive=True):
    folder = os.path.dirname(page)
    html = open(page, encoding="utf-8").read()
    urls = set(re.findall(r'(?:src|href)="([^"#:]+)"', html))
    for srcset in re.findall(r'srcset="([^"]+)"', html):
        urls.update(part.split()[0] for part in srcset.split(","))
    for url in urls:
        path = os.path.normpath(os.path.join(folder, url))
        if url.endswith("/"):
            path = os.path.join(path, "index.html")
        checked += 1
        if not os.path.exists(path):
            missing += 1
            print("MISSING", os.path.relpath(page, SITE), url)

size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(SITE, "**", "*"), recursive=True) if os.path.isfile(f))
print(f"checked {checked} links, missing {missing}, site size {size / 1e6:.1f} MB")
