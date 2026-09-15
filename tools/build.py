"""Build the static site from content/*.json.

Run:  python tools/build.py
Writes site/index.html, site/about/index.html and site/work/<slug>/index.html.
Edit text in content/site.json and content/projects.json, then re-run.
"""
import json
import os
import re
from html import escape as e

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "docs")  # GitHub Pages publishes this folder
C = lambda n: json.load(open(os.path.join(ROOT, "content", n), encoding="utf-8-sig"))

site = C("site.json")
projects = C("projects.json")
sizes = C("images.json")
videos = C("videos.json") if os.path.exists(os.path.join(ROOT, "content", "videos.json")) else {}
FONTS = ("https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;400;500;600"
         "&family=Instrument+Serif:ital@0;1&display=swap")


def img(project, name, alt, base, cls="", sizes_attr="100vw", eager=False):
    s = sizes.get(f"{project}/{name}", {"w": 1600, "h": 1000})
    src = f"{base}assets/img/{project}/{name}"
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img class="{cls}" src="{src}-1200.webp" srcset="{src}-1200.webp 1200w, {src}-2400.webp 2400w" '
            f'sizes="{sizes_attr}" width="{s["w"]}" height="{s["h"]}" alt="{e(alt)}" {load} decoding="async">')


def og_image(project, name, src=None):
    """Share-preview image for LinkedIn and other link cards: 1200x627 JPG (1.91:1)."""
    rel = f"assets/og/{project}.jpg"
    out = os.path.join(SITE, rel)
    src = src or os.path.join(SITE, "assets", "img", project, f"{name}-2400.webp")
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
        f'<a href="{base}{href}">{label}</a>' for href, label in (("#work", "Work"), ("films/", "Films"), ("about/", "About"))
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
    <li><a href="{base}films/">Films</a></li>
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


def reel(base):
    """Silent looping highlight reel. main.js picks 720p or 1080p and skips it for reduced motion."""
    v = f"{base}assets/video/"
    return (f'<div class="reel"><video class="reel-video" muted loop playsinline preload="none" aria-hidden="true" '
            f'poster="{v}reel-poster.jpg" data-src-sm="{v}reel-720.mp4" data-src-lg="{v}reel-1080.mp4"></video>'
            f'<button class="reel-toggle" type="button" aria-label="Pause background video" aria-pressed="false">'
            f'<span class="i-pause"></span></button></div>'
            f'<p class="reel-credit">{credit_html()}</p>')


def credit_html():
    """Reel credit with the company names after "Courtesy of" linked to their websites."""
    text = site["reel_credit"]
    head, sep, tail = text.partition("Courtesy of ")
    tail = e(tail)
    for name, url in site.get("credit_links", {}).items():
        link = f'<a href="{e(url)}" target="_blank" rel="noopener">{e(name)}</a>'
        tail = re.sub(rf"\b{re.escape(e(name))}\b", link, tail, count=1)
    # one inner span so the flex box treats the sentence as a single run of text
    return f"<span>{e(head)}{e(sep)}{tail}</span>"


def film_grid(base):
    """The four full-length films (streamed from pCloud), with facade poster frames."""
    items = []
    for key, title, desc in next(p for p in projects if p.get("videos"))["videos"]:
        v = videos.get(key, {"width": 1920, "height": 1080, "duration": 0})
        mins, secs = divmod(int(v["duration"]), 60)
        items.append(
            f'<figure class="film"><video controls playsinline preload="none" '
            f'poster="{base}assets/video/{key}.jpg" width="{v["width"]}" height="{v["height"]}">'
            f'<source src="{site["video_base"]}{key}.mp4" type="video/mp4"></video>'
            f"<figcaption><strong>{e(title)}</strong>{e(desc)} &middot; {mins}:{secs:02d}</figcaption></figure>")
    return f'<div class="film-grid">{"".join(items)}</div>'


def films():
    base = "../"
    body = f"""<section class="reel-hero films-hero">
  {reel(base)}
  <div class="reel-inner">
    <p class="eyebrow">Architectural animation</p>
    <h1>Films</h1>
    <p class="lede">Cinematic walkthroughs I produced for residential, commercial and healthcare high-rises at P2P, Bangladesh.</p>
  </div>
</section>
<section class="films reveal" id="films">
  <h2>Full films</h2>
  <p class="films-note">Press play to watch each project in full, with sound.</p>
  {film_grid(base)}
</section>"""
    poster = os.path.join(SITE, "assets", "video", "reel-poster.jpg")
    write("films/index.html", page(f"Films | {site['name']}",
                                   "Cinematic architectural animations of high-rise projects by Md. Rakib Hasan.",
                                   base, body, "films/", og_image("films", "reel", poster)))


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
    body = f"""<section class="reel-hero intro">
  {reel('')}
  <div class="reel-inner">
    <p class="eyebrow">{e(site['title'])} &middot; {e(site['location'])}</p>
    <h1>Buildings shaped by <em>light</em>, envelope and the details that get them built.</h1>
    <p class="lede">{e(site['tagline'])}</p>
    <p class="cta"><a class="btn" href="#work">View work</a><a class="link" href="films/">Watch films</a></p>
  </div>
</section>
<section class="work" id="work">
  <div class="section-head"><h2>Selected work</h2><span>{len(projects)} projects</span></div>
  <ol class="work-grid">
{''.join(rows)}
  </ol>
</section>"""
    write("index.html", page(f"{site['name']} | {site['title']}", site["tagline"], "", body))


def callout_figure(project, name, cap, base, items):
    """Map with coded callouts: label boxes in a band above the image, dotted elbow leaders, end dots.

    items: [{"label", "note", "x", "y"}], x/y = target as % of the image.
    Phones (CSS) hide the labels and leaders, number the dots and show a numbered list instead.
    """
    # items may be a list, or {"items": [...], "sheet": true} for opaque drawings: the stage gets a white sheet + light ink
    sheet = isinstance(items, dict) and items.get("sheet")
    items = items["items"] if isinstance(items, dict) else items
    s = sizes.get(f"{project}/{name}", {"w": 1600, "h": 1600})
    w, h = s["w"], s["h"]
    items = sorted(items, key=lambda c: c["x"])  # numbered left-to-right in target order
    n = len(items)
    wide = n > 4
    D = 1200 if wide else 560                    # design width of the stage in CSS px (labels scale with it)
    label_w = 15.0 if wide else 30.0             # fixed label width, % of stage
    px = w / D                                   # image pixels per design px
    gap, pitch = 14 * px, 78 * px                # space above the image, row spacing
    # Leaders are single straight lines. Each label sits right above its target; rows are stacked so that
    # no label overlaps another in its row or sits across the leader of a label in a higher row.
    placed = []                                  # (row, left %, right %, target x %)
    for c in items:
        cx = min(max(c["x"], label_w / 2 + 0.5), 100 - label_w / 2 - 0.5)
        l, r, row = cx - label_w / 2 - 0.6, cx + label_w / 2 + 0.6, 0
        def blocked(row, strict):
            return any((pr == row and pl < r and l < prr) or
                       (strict and ((pr > row and l < pt < r) or (pr < row and pl < c["x"] < prr)))
                       for pr, pl, prr, pt in placed)
        # a lower label already covering this target can never be cleared by going up: then only avoid overlaps
        strict = not any(pr >= 0 and pl < c["x"] < prr for pr, pl, prr, pt in placed)
        while blocked(row, strict):
            row += 1
        placed.append((row, l, r, c["x"]))
        c["_row"], c["_lx"] = row, cx
    band = gap + (max(p[0] for p in placed) + 1) * pitch
    H = h + band
    lines, dots, labels, legend = [], [], [], []
    for i, c in enumerate(items):
        label_bottom = band - gap - c["_row"] * pitch
        tx, ty = c["x"] / 100 * w, band + c["y"] / 100 * h
        lines.append(f'<path vector-effect="non-scaling-stroke" '
                     f'd="M{c["_lx"] / 100 * w:.1f},{label_bottom:.1f} L{tx:.1f},{ty:.1f}"/>')
        dots.append(f'<span class="callout-dot" data-n="{i + 1}" style="left:{c["x"]:.2f}%;'
                    f'--ty:{ty / H * 100:.2f}%;--ty-img:{c["y"]:.2f}%"></span>')
        labels.append(f'<span class="callout-label" style="left:{c["_lx"]:.2f}%;top:{label_bottom / H * 100:.2f}%">'
                      f'<strong>{e(c["label"])}</strong><small>{e(c["note"])}</small></span>')
        legend.append(f'<li><strong>{e(c["label"])}</strong> {e(c["note"])}</li>')
    style = (f"--ar:{w}/{H};--ar-img:{w}/{h};--img-top:{band / H * 100:.2f}%;--img-h:{h / H * 100:.2f}%;"
             f"--label-w:{label_w:.1f}%;--design-w:{D}")
    cls = "callout-map" + (" wide" if wide else "") + (" sheet" if sheet else "")
    return (f'<figure class="{cls}"><div class="callout-stage" style="{style}">'
            f'{img(project, name, cap, base, cls="callout-img", sizes_attr="(min-width: 960px) 900px, 100vw")}'
            f'<svg class="callout-lines" viewBox="0 0 {w} {H}" preserveAspectRatio="none" aria-hidden="true">'
            f'{"".join(lines)}</svg>{"".join(dots)}{"".join(labels)}</div>'
            f'<ol class="callout-legend">{"".join(legend)}</ol>'
            f"<figcaption>{e(cap)}</figcaption></figure>")


def sketch_grid(project, items, base):
    """Transparent hand sketches (ink only) in a grid."""
    tiles = "".join(f'<figure class="sketch zoom">{img(project, n, cap, base, sizes_attr="(min-width: 900px) 33vw, 50vw")}'
                    f"<figcaption>{e(cap)}</figcaption></figure>" for n, cap in items)
    return f'<div class="sketch-grid">{tiles}</div>'


def zones_figure(project, z, base):
    """Concept section sketch between live-text zone cards (two above, two below)."""
    def card(c):
        tag = f'<p class="zone-tag">{e(c["tag"])}</p>' if c.get("tag") else ""
        return f'<div class="zone">{tag}<h3>{e(c["title"])}</h3><p>{e(c["text"])}</p></div>'
    n, cap = z["image"]
    west, east = z["ends"]
    return (f'<figure class="zones"><div class="zone-row">{"".join(map(card, z["cards"][:2]))}</div>'
            f'<div class="sketch zone-art">{img(project, n, cap, base, sizes_attr="(min-width: 1400px) 1400px, 100vw")}</div>'
            f'<div class="zone-axis"><span>&larr; {e(west)}</span><strong>{e(z["middle"])}</strong><span>{e(east)} &rarr;</span></div>'
            f'<div class="zone-row">{"".join(map(card, z["cards"][2:]))}</div>'
            f"<figcaption>{e(cap)}</figcaption></figure>")


def steps_list(project, items):
    """Massing steps: cleaned inline SVGs (content/svg/<project>/) with live step titles and text."""
    lis = []
    for i, (fname, title, text) in enumerate(items, 1):
        svg = open(os.path.join(ROOT, "content", "svg", project, fname), encoding="utf-8").read()
        lis.append(f'<li class="step"><div class="step-art">{svg}</div>'
                   f'<p class="step-n">Step {i}</p><h3>{e(title)}</h3><p>{e(text)}</p></li>')
    return f'<ol class="steps">{"".join(lis)}</ol>'


def plan_viewer(project, plans, base):
    """Floor plans, one level at a time. No JavaScript: radio inputs + labels switch the panels (CSS nth-of-type).

    plans: [[image name, level label, [program items]]]. Phones get the same tabs as wrapping chips.
    """
    group = f"plans-{project}"
    inputs = "".join(f'<input class="plan-radio" type="radio" name="{group}" id="{group}-{i}"{" checked" if i == 0 else ""}>'
                     for i in range(len(plans)))
    tabs = "".join(f'<label for="{group}-{i}">{e(label.replace("Levels ", "").replace("Level ", "").replace(" to ", "–").replace(" and ", "–"))}</label>'
                   for i, (_, label, _) in enumerate(plans))
    panels = "".join(
        f'<figure class="plan-panel"><div class="plan-sheet zoom">'
        f'{img(project, n, f"{label} floor plan", base, sizes_attr="(min-width: 1100px) 1000px, 100vw")}</div>'
        f'<figcaption><strong>{e(label)}</strong><ul>{"".join(f"<li>{e(x)}</li>" for x in items)}</ul></figcaption></figure>'
        for n, label, items in plans)
    return (f'<div class="plan-viewer">{inputs}<div class="plan-tabs"><span>Level</span>{tabs}</div>'
            f'<div class="plan-panels">{panels}</div></div>')


def project(i, p):
    base = "../../"
    slug = p["slug"]
    meta = [("Type", p["type"]), ("Location", p["location"]), ("Year", p["year"]), ("Context", p["context"]),
            ("Role", p["role"]), ("Team", p["team"]), ("Tools", p["tools"])]
    meta_html = "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in meta if v)
    facts = "".join(f'<div class="fact"><span>{e(k)}</span><strong>{e(v)}</strong></div>' for k, v in p.get("facts", []))
    parts = []
    for s in p.get("sections", []):
        callouts = s.get("callouts", {})
        figs = "".join(
            callout_figure(slug, n, cap, base, callouts[n]) if n in callouts else
            f'<figure class="zoom">{img(slug, n, cap, base, sizes_attr="(min-width: 1400px) 1400px, 100vw")}'
            f"<figcaption>{e(cap)}</figcaption></figure>" for n, cap in s.get("images", []))
        if s.get("pair"):  # drawings side by side (one column on phones); an int pairs from that image on
            k = s["pair"] if type(s["pair"]) is int else 0
            head = "".join(figs_list[:k]) if (figs_list := re.findall(r"<figure.*?</figure>", figs, re.S)) else ""
            figs = f'{head}<div class="fig-pair">{"".join(figs_list[k:])}</div>'
        if s.get("sketches"):
            figs +=sketch_grid(slug, s["sketches"], base)
        if s.get("zones"):
            figs += zones_figure(slug, s["zones"], base)
        if s.get("steps"):
            figs += steps_list(slug, s["steps"])
        if s.get("plans"):
            figs += plan_viewer(slug, s["plans"], base)
        text = f"<p>{e(s['text'])}</p>" if s["text"] else ""
        if s.get("stats"):
            text += '<div class="facts">' + "".join(
                f'<div class="fact"><span>{e(k)}</span><strong>{e(v)}</strong></div>' for v, k in s["stats"]) + "</div>"
        if s.get("note"):
            text += f'<p class="small">{e(s["note"])}</p>'
        if s.get("calc"):  # worked calculations behind the stats, collapsed by default
            text += ('<details class="calc"><summary>How these were calculated</summary><ul>'
                     + "".join(f"<li>{e(c)}</li>" for c in s["calc"]) + "</ul></details>")
        side = " side" if s.get("side") else ""  # text beside a small figure instead of above it
        parts.append(f'<section class="chapter reveal{side}"><div class="chapter-text"><h2>{e(s["heading"])}</h2>{text}</div>'
                     f'<div class="chapter-figs">{figs}</div></section>')
    if p.get("videos"):
        # full players live on the Films page; here, a link card to it
        parts.append(f'<section class="films-teaser reveal" id="films"><a href="{base}films/">'
                     f'<img src="{base}assets/video/reel-poster.jpg" alt="Still from the P2P animation reel" loading="lazy" width="1920" height="1080">'
                     f'<span class="films-teaser-text"><span class="eyebrow">{len(p["videos"])} films</span>'
                     f'<strong>Watch the animations I produced at P2P &rarr;</strong></span></a></section>')
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
    films()
    about()
    open(os.path.join(SITE, "CNAME"), "w").write("rakibhasan.net\n")
