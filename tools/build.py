"""Build the static site from content/*.json.

Run:  python tools/build.py
Writes site/index.html, site/about/index.html and site/work/<slug>/index.html.
Edit text in content/site.json and content/projects.json, then re-run.
"""
import json
import os
from html import escape as e

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "docs")  # GitHub Pages publishes this folder
C = lambda n: json.load(open(os.path.join(ROOT, "content", n), encoding="utf-8-sig"))

site = C("site.json")
projects = C("projects.json")
sizes = C("images.json")
FONTS = ("https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;400;500;600"
         "&family=Instrument+Serif:ital@0;1&display=swap")


def img(project, name, alt, base, cls="", sizes_attr="100vw", eager=False):
    s = sizes.get(f"{project}/{name}", {"w": 1600, "h": 1000})
    src = f"{base}assets/img/{project}/{name}"
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img class="{cls}" src="{src}-1200.webp" srcset="{src}-1200.webp 1200w, {src}-2400.webp 2400w" '
            f'sizes="{sizes_attr}" width="{s["w"]}" height="{s["h"]}" alt="{e(alt)}" {load} decoding="async">')


def og_image(project, name):
    """Share-preview image for LinkedIn and other link cards: 1200x627 JPG (1.91:1)."""
    rel = f"assets/og/{project}.jpg"
    out = os.path.join(SITE, rel)
    src = os.path.join(SITE, "assets", "img", project, f"{name}-2400.webp")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        im = Image.open(src).convert("RGB")
        w, h = 1200, 627
        scale = max(w / im.width, h / im.height)
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        left, top = (im.width - w) // 2, (im.height - h) // 2
        im.crop((left, top, left + w, top + h)).save(out, "JPEG", quality=85, optimize=True, progressive=True)
    return f"{site['domain']}/{rel}"


def page(title, desc, base, body, path="", image=None):
    image = image or og_image(projects[0]["slug"], projects[0]["hero"])
    nav = "".join(
        f'<a href="{base}{href}">{label}</a>' for href, label in (("#work", "Work"), ("about/", "About"))
    ).replace(f'href="{base}#work"', f'href="{base}index.html#work"')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{site['domain']}/{path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{site['domain']}/{path}">
<meta property="og:site_name" content="{e(site['name'])}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="627">
<meta property="og:image:alt" content="{e(title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="{e(site['name'])}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%23161513'/%3E%3Ctext x='16' y='22' font-family='Arial' font-size='14' font-weight='700' fill='%23f4f2ee' text-anchor='middle'%3ERH%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{base}assets/css/style.css">
</head>
<body>
<header class="bar">
  <a class="mark" href="{base}index.html">{e(site['name'])}</a>
  <nav>{nav}<a href="mailto:{site['email']}">Contact</a>
  <button class="theme" type="button" aria-label="Toggle dark mode"><span></span></button></nav>
</header>
<main>
{body}
</main>
<footer class="foot" id="contact">
  <p class="foot-big">Let's talk.<br><a href="mailto:{site['email']}">{e(site['email'])}</a></p>
  <ul>
    <li><a href="{site['linkedin']}" target="_blank" rel="noopener">LinkedIn</a></li>
    <li><a href="{site['vimeo']}" target="_blank" rel="noopener">Animations on Vimeo</a></li>
    <li><a href="{base}{site['resume']}" target="_blank" rel="noopener">Resume (PDF)</a></li>
  </ul>
  <p class="small">&copy; 2026 {e(site['name'])}. {e(site['title'])}, {e(site['location'])}.</p>
</footer>
<div class="lightbox" hidden><button type="button" aria-label="Close">&times;</button><img alt=""></div>
<script src="{base}assets/js/main.js"></script>
</body>
</html>
"""


def write(rel, html):
    path = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("wrote", rel)


def home():
    rows = []
    for i, p in enumerate(projects, 1):
        rows.append(f"""<li class="work-item reveal">
  <a href="work/{p['slug']}/">
    <figure>{img(p['slug'], p['hero'], p['title'], '', sizes_attr='(min-width: 900px) 50vw, 100vw', eager=i == 1)}</figure>
    <div class="work-meta">
      <span class="num">{i:02d}</span>
      <h3>{e(p['title'])}</h3>
      <p>{e(p['type'])} &middot; {e(p['location'])} &middot; {e(p['year'])}</p>
    </div>
  </a>
</li>""")
    body = f"""<section class="intro">
  <p class="eyebrow">{e(site['title'])} &middot; {e(site['location'])}</p>
  <h1>Buildings shaped by <em>light</em>, envelope and the details that get them built.</h1>
  <p class="lede">{e(site['tagline'])}</p>
  <p class="cta"><a class="btn" href="#work">View work</a><a class="link" href="about/">About me</a></p>
</section>
<section class="work" id="work">
  <div class="section-head"><h2>Selected work</h2><span>{len(projects)} projects</span></div>
  <ol class="work-grid">
{''.join(rows)}
  </ol>
</section>"""
    write("index.html", page(f"{site['name']} | {site['title']}", site["tagline"], "", body))


def project(i, p):
    base = "../../"
    slug = p["slug"]
    meta = [("Type", p["type"]), ("Location", p["location"]), ("Year", p["year"]), ("Context", p["context"]),
            ("Role", p["role"]), ("Team", p["team"]), ("Tools", p["tools"])]
    meta_html = "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in meta if v)
    facts = "".join(f'<div class="fact"><span>{e(k)}</span><strong>{e(v)}</strong></div>' for k, v in p.get("facts", []))
    parts = []
    for s in p.get("sections", []):
        figs = "".join(
            f'<figure class="zoom">{img(slug, n, cap, base, sizes_attr="(min-width: 1400px) 1400px, 100vw")}'
            f"<figcaption>{e(cap)}</figcaption></figure>" for n, cap in s["images"])
        text = f"<p>{e(s['text'])}</p>" if s["text"] else ""
        parts.append(f'<section class="chapter reveal"><div class="chapter-text"><h2>{e(s["heading"])}</h2>{text}</div>'
                     f'<div class="chapter-figs">{figs}</div></section>')
    if p.get("gallery"):
        def tile(n, t, d, url=""):
            name = f'<a href="{e(url)}" target="_blank" rel="noopener">{e(t)} &#8599;</a>' if url else e(t)
            cap = f"<figcaption><strong>{name}</strong>{e(d)}</figcaption>" if t else ""
            return f'<figure class="zoom">{img(slug, n, t or p["title"], base, sizes_attr="(min-width: 900px) 25vw, 50vw")}{cap}</figure>'
        tiles = "".join(tile(*g) for g in p["gallery"])
        parts.append(f'<section class="gallery reveal"><h2>Selected renders</h2><div class="masonry">{tiles}</div></section>')
    if p.get("table"):
        trs = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in p["table"])
        parts.append(f'<section class="table-wrap reveal"><h2>Project list</h2><div class="scroll"><table>'
                     f"<thead><tr><th>Project</th><th>Type</th><th>Size</th></tr></thead>"
                     f"<tbody>{trs}</tbody></table></div></section>")
    nxt = projects[i % len(projects)]
    body = f"""<article class="project">
  <header class="project-hero">
    {img(slug, p['hero'], p['title'], base, cls='hero-img', eager=True)}
    <div class="hero-title"><p class="eyebrow">{i:02d} / {len(projects):02d}</p><h1>{e(p['title'])}</h1><p>{e(p['subtitle'])}</p></div>
  </header>
  <section class="project-intro">
    <dl class="meta">{meta_html}</dl>
    <div class="intro-text">{''.join(f'<p>{e(t)}</p>' for t in p['intro'])}<div class="facts">{facts}</div></div>
  </section>
  {''.join(parts)}
  <a class="next" href="{base}work/{nxt['slug']}/"><span>Next project</span><strong>{e(nxt['title'])}</strong></a>
</article>"""
    desc = f"{p['title']}: {p['subtitle']}. {p['type']}, {p['location']}."
    write(f"work/{slug}/index.html", page(f"{p['title']} | {site['name']}", desc, base, body, f"work/{slug}/",
                                          og_image(slug, p["hero"])))


def about():
    base = "../"
    rows = lambda items: "".join(
        "<li>" + "".join(f"<span>{e(c)}</span>" for c in r) + "</li>" for r in items)  # keep empty cells so columns line up
    body = f"""<section class="about">
  <div class="about-photo reveal">{img('about', 'headshot', site['name'], base, sizes_attr='(min-width: 900px) 30vw, 60vw', eager=True)}</div>
  <div class="about-text">
    <p class="eyebrow">About</p>
    <h1>{e(site['name'])}</h1>
    {''.join(f'<p>{e(t)}</p>' for t in site['bio'])}
    <p class="cta"><a class="btn" href="{base}{site['resume']}" target="_blank" rel="noopener">Download resume</a>
    <a class="link" href="mailto:{site['email']}">Email me</a></p>
  </div>
</section>
<section class="cv">
  <div class="cv-block reveal"><h2>Experience</h2><ul>{rows(site['experience'])}</ul></div>
  <div class="cv-block reveal"><h2>Education</h2><ul>{rows(site['education'])}</ul></div>
  <div class="cv-block reveal"><h2>Awards</h2><ul>{rows(site['awards'])}</ul></div>
  <div class="cv-block reveal"><h2>Certifications</h2><ul>{rows(site['certifications'])}</ul></div>
  <div class="cv-block cv-tools reveal"><h2>Tools</h2><ul>{rows(site['skills'])}</ul></div>
</section>"""
    write("about/index.html", page(f"About | {site['name']}", " ".join(site["bio"][:1]), base, body, "about/"))


if __name__ == "__main__":
    home()
    for i, p in enumerate(projects, 1):
        project(i, p)
    about()
    open(os.path.join(SITE, "CNAME"), "w").write("rakibhasan.net\n")
