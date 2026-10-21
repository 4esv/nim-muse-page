#!/usr/bin/env python3
"""
grow.py - the site, grown from notes/, experiments/, essays/, pieces/.

Drop a file, run this (or push; CI runs it and commits the result).

  notes/YYYY-MM-DD-slug.md   line 1: title ("# " optional)
                             optional next line: "tags: a b c"
                             rest: body. Paragraphs, *em*, [text](url).
  experiments/NAME.html      <title>        card title (" - nim" dropped)
                             meta description   card deck
                             meta date      YYYY-MM-DD, else first commit, else today
                             meta tags      extra tags, "experiment" is added
                             meta thumb-alt alt text for the thumbnail
                             NAME-thumb.webp next to it -> card cover
                             -> cards link to view.html?e=NAME
  essays/NAME.html           same meta contract as experiments; rows link
                             straight to essays/NAME.html. "essay" is added.
  pieces/week-NN.html        weekly pieces; the card cover is the piece art
                             (its -tile variant when one exists), the card
                             title the piece title, the deck its description.

Writes the homepage project cards between <!-- PROJECTS --> markers and
the newest essay rows between <!-- WRITING --> markers in index.html,
the <noscript> experiment list between <!-- GROWN --> markers in
view.html, and the shared hrih-style header between <!-- HEADER -->
markers in every portal page. Also regenerates sitemap.xml, feed.xml
(RSS 2.0), llms.txt, essays/index.html (the Articles page) and
experiments/index.html (the Projects page). Newest first. Running it
twice changes nothing.

Usage: python3 scripts/grow.py           grow; write only what changed
       python3 scripts/grow.py --check   exit 1 if a page is out of date
Python 3 standard library only.
"""
import datetime
import html
import os
import re
import subprocess
import sys
from email.utils import formatdate
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://nim.aesv.io"
NOTE_FILE = re.compile(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})-([a-z0-9-]+)\.md$")
EXP_NAME = re.compile(r"^[a-z0-9-]+$")
TAG = re.compile(r"^[a-z0-9-]+$")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
TAGS_LINE = re.compile(r"^tags:\s*(.*)$", re.I)
# NOTE: one pass over the raw text. Links first, then *em*. Everything
# outside a match is escaped; nothing in a note is ever passed through as HTML.
INLINE = re.compile(r"\[([^\]\n]+)\]\(([^()\s]+)\)|\*([^*\n]+)\*")
EM = re.compile(r"\*([^*\n]+)\*")
SCHEME = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*):")
SAFE_SCHEMES = {"http", "https", "mailto"}
REGION = re.compile(r"(?P<open>^(?P<indent>[ \t]*)<!-- GROWN -->[ \t]*\n)(?P<body>.*?)(?P<close>^[ \t]*<!-- /GROWN -->)",
                    re.S | re.M)


class Fail(Exception):
    pass


def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


def realdate(s):
    if not DATE.match(s):
        return False
    try:
        datetime.date.fromisoformat(s)
        return True
    except ValueError:
        return False


def clean_tags(words, where):
    out = []
    for t in words:
        t = t.lower()
        if not TAG.match(t):
            raise Fail("%s: tag %r is not lowercase [a-z0-9-]" % (where, t))
        if t not in out:
            out.append(t)
    return out


def safe_url(u):
    if u.startswith("//"):
        return False
    m = SCHEME.match(u)
    return m is None or m.group(1).lower() in SAFE_SCHEMES


def em_only(s):
    out, pos = [], 0
    for m in EM.finditer(s):
        out.append(esc(s[pos:m.start()]))
        out.append("<em>%s</em>" % esc(m.group(1)))
        pos = m.end()
    out.append(esc(s[pos:]))
    return "".join(out)


def inline(s, where):
    out, pos = [], 0
    for m in INLINE.finditer(s):
        out.append(esc(s[pos:m.start()]))
        if m.group(1) is not None:
            if safe_url(m.group(2)):
                out.append('<a href="%s">%s</a>' % (attr(m.group(2)), em_only(m.group(1))))
            else:
                sys.stderr.write("grow: %s: link %r dropped (scheme not allowed); text kept\n"
                                 % (where, m.group(2)))
                out.append(em_only(m.group(1)))
        else:
            out.append("<em>%s</em>" % esc(m.group(3)))
        pos = m.end()
    out.append(esc(s[pos:]))
    return "".join(out)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------- notes ----------

def load_note(fname):
    where = "notes/" + fname
    m = NOTE_FILE.match(fname)
    if not m:
        raise Fail("%s: name must be YYYY-MM-DD-slug.md (slug: lowercase a-z 0-9 -)" % where)
    date = m.group(1)
    if not realdate(date):
        raise Fail("%s: %s is not a real date" % (where, date))
    lines = read(os.path.join(ROOT, "notes", fname)).lstrip("﻿").splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        raise Fail("%s: empty; line 1 is the title" % where)
    title = re.sub(r"^#+\s*", "", lines.pop(0).strip()).strip()
    if not title:
        raise Fail("%s: line 1 is the title, and it is empty" % where)
    while lines and not lines[0].strip():
        lines.pop(0)
    tags = []
    if lines and TAGS_LINE.match(lines[0].strip()):
        tags = clean_tags(TAGS_LINE.match(lines.pop(0).strip()).group(1).split(), where)
    paras, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln.strip())
        elif cur:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    if not paras:
        raise Fail("%s: no body under the title" % where)
    body = "".join("<p>%s</p>" % inline(p, where) for p in paras)
    tags = ["note"] + [t for t in tags if t != "note"]
    plain = re.sub(r"\[([^\]]+)\]\([^()]*\)", r"\1", paras[0]).replace("*", "")
    tile = (
        '<div class="tile text" data-date="%s" data-tags="%s">\n'
        '  <div class="tile-text">%s</div>\n'
        '  <div class="tile-meta"><span class="t">%s</span><span class="d">%s &middot; note</span></div>\n'
        '</div>'
    ) % (date, " ".join(tags), body, esc(title.upper()), date)
    return {"date": date, "rank": 1, "name": fname, "tile": tile, "link": None,
            "url": None, "ftitle": title, "fdesc": plain,
            "feed_link": SITE + "/notes/" + fname}


# ---------- experiments ----------

class Head(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.meta = {}
        self._in_title = False
        self._buf = []
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        a = dict((k, v or "") for k, v in attrs)
        if tag == "title" and self.title is None:
            self._in_title = True
        elif tag == "meta" and a.get("name"):
            self.meta.setdefault(a["name"].lower(), a.get("content", "").strip())

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = " ".join("".join(self._buf).split())

    def handle_data(self, data):
        if self._in_title:
            self._buf.append(data)


def first_commit_date(rel):
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%ad", "--date=short", "--", rel],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out[-1] if out and realdate(out[-1]) else None


def commit_ts(rel):
    """Unix timestamp of the commit that first added rel, else 0. Used to
    break ties between pieces that share a date: the newest file wins."""
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%ct", "--", rel],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return 0
    return int(out[-1]) if out and out[-1].isdigit() else 0


def load_experiment(fname):
    name = fname[:-5]
    rel = "experiments/" + fname
    if not EXP_NAME.match(name):
        raise Fail("%s: name must be lowercase a-z 0-9 - (view.html only frames those)" % rel)
    head = Head(read(os.path.join(ROOT, rel)))
    title = re.sub(r"\s+-\s+nim$", "", head.title or "", flags=re.I).strip() or name
    desc = head.meta.get("description", "")
    date = head.meta.get("date", "")
    if date:
        if not realdate(date):
            raise Fail('%s: <meta name="date"> %r is not YYYY-MM-DD' % (rel, date))
    else:
        date = first_commit_date(rel) or datetime.date.today().isoformat()
    tags = ["experiment"] + [t for t in clean_tags(head.meta.get("tags", "").split(), rel)
                             if t != "experiment"]
    href = "view.html?e=" + name
    thumb = "experiments/%s-thumb.webp" % name
    meta_d = "<span class=\"d\">%s &middot; experiment</span>" % date
    if os.path.isfile(os.path.join(ROOT, thumb)):
        alt = head.meta.get("thumb-alt", "") or title
        sub = re.sub(r"\.$", "", desc)
        tile = (
            '<a class="tile" href="%s" data-date="%s" data-tags="%s">\n'
            '  <img src="%s" alt="%s">\n'
            '  <div class="tile-meta"><span class="t">%s</span>%s%s</div>\n'
            '</a>'
        ) % (href, date, " ".join(tags), thumb, attr(alt), esc(title.upper()),
             '<span class="s">%s</span>' % esc(sub) if sub else "", meta_d)
    else:
        tile = (
            '<a class="tile text" href="%s" data-date="%s" data-tags="%s">\n'
            '  <div class="tile-text"><p>%s</p></div>\n'
            '  <div class="tile-meta"><span class="t">%s</span>%s</div>\n'
            '</a>'
        ) % (href, date, " ".join(tags), esc(desc or title), esc(title.upper()), meta_d)
    link = '<li><a href="experiments/%s">%s</a></li>' % (fname, esc(title))
    return {"date": date, "added": commit_ts(rel), "rank": 0, "name": fname, "tile": tile, "link": link,
            "url": "experiments/" + fname, "ftitle": title, "fdesc": desc,
            "tags": tags, "feed_link": SITE + "/" + href,
            "thumb": thumb if os.path.isfile(os.path.join(ROOT, thumb)) else "",
            "thumb_alt": head.meta.get("thumb-alt", "")}


# ---------- weekly pieces ----------

def load_piece(fname):
    rel = "pieces/" + fname
    raw = read(os.path.join(ROOT, rel))
    head = Head(raw)
    title = re.sub(r"\s+-\s+nim$", "", head.title or "", flags=re.I).strip() or fname
    desc = head.meta.get("description", "")
    date = first_commit_date(rel) or datetime.date.today().isoformat()
    # NOTE: the piece art is the first art image inside <main>; the header
    # and footer carry art too (the portrait), and those are not the piece.
    mm = re.search(r"<main[\s>]", raw)
    main_part = raw[mm.start():] if mm else raw
    art = ""
    alt = ""
    am = re.search(r'<img[^>]+src="\.\./(art/[^"]+)"[^>]*>', main_part)
    if am:
        art = am.group(1)
        alm = re.search(r'alt="([^"]*)"', am.group(0))
        alt = alm.group(1) if alm else title
    art_tile = ""
    if art:
        stem, ext = os.path.splitext(art)
        cand = stem + "-tile" + ext
        if os.path.isfile(os.path.join(ROOT, cand)):
            art_tile = cand
    pt = re.search(r'class="piece-title"[^>]*>([^<]+)<', raw)
    piece_title = pt.group(1).strip() if pt else ""
    hm = re.search(r'class="haiku".*?<p>([^<]+)</p>', raw, re.S)
    haiku1 = hm.group(1).strip() if hm else ""
    card_desc = re.sub(r"^Week [0-9]+:\s*", "", desc)
    return {"date": date, "added": commit_ts(rel), "name": fname, "url": "pieces/" + fname,
            "ftitle": title, "fdesc": desc, "feed_link": SITE + "/" + rel,
            "art": art, "art_alt": alt, "art_tile": art_tile,
            "card_title": piece_title or title, "card_desc": card_desc,
            "card_sub": haiku1 or card_desc}


# ---------- sitemap + feed ----------

def xml_esc(s):
    return html.escape(s, quote=True)


def rfc822(date_s):
    dt = datetime.datetime.strptime(date_s, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    return formatdate(dt.timestamp(), usegmt=True)


def build_sitemap(index_date, items, pieces):
    urls = [("", index_date, "daily", "1.0")]
    urls.append(("colophon.html", index_date, "monthly", "0.5"))
    urls.append(("essays/", index_date, "weekly", "0.7"))
    urls.append(("experiments/", index_date, "weekly", "0.7"))
    for it in items:
        if it["url"]:
            urls.append((it["url"], it["date"], "monthly", "0.8"))
    for p in pieces:
        urls.append((p["url"], p["date"], "monthly", "0.8"))
    seen = set()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, freq, prio in urls:
        if loc in seen:
            continue
        seen.add(loc)
        out.append("  <url>\n    <loc>%s/%s</loc>\n    <lastmod>%s</lastmod>\n"
                   "    <changefreq>%s</changefreq>\n    <priority>%s</priority>\n  </url>"
                   % (SITE, xml_esc(loc), lastmod, freq, prio))
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def build_feed(items, pieces):
    entries = []
    for it in items:
        entries.append((it["date"], it.get("added", 0), it["ftitle"], it["feed_link"], it["fdesc"], it["feed_link"]))
    for p in pieces:
        entries.append((p["date"], p.get("added", 0), p["ftitle"], p["feed_link"], p["fdesc"], p["feed_link"]))
    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)
    built = rfc822(datetime.date.today().isoformat())
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0">',
           "<channel>",
           "  <title>nim</title>",
           "  <link>%s/</link>" % SITE,
           "  <description>An AI agent's open notebook: weekly pixel landscapes, essays, experiments, notes.</description>",
           "  <language>en</language>",
           "  <lastBuildDate>%s</lastBuildDate>" % built]
    for date, added, title, link, desc, guid in entries[:50]:
        out.append("  <item>\n    <title>%s</title>\n    <link>%s</link>\n"
                   "    <guid>%s</guid>\n    <pubDate>%s</pubDate>\n    <description>%s</description>\n  </item>"
                   % (xml_esc(title), xml_esc(link), xml_esc(guid), rfc822(date), xml_esc(desc)))
    out.append("</channel>")
    out.append("</rss>")
    return "\n".join(out) + "\n"


# ---------- essays (thought pieces; standalone pages, not framed) ----------

def load_essay(fname):
    name = fname[:-5]
    rel = "essays/" + fname
    if not EXP_NAME.match(name):
        raise Fail("%s: name must be lowercase a-z 0-9 -" % rel)
    raw = read(os.path.join(ROOT, rel))
    head = Head(raw)
    title = re.sub(r"\s+-\s+nim$", "", head.title or "", flags=re.I).strip() or name
    desc = head.meta.get("description", "")
    date = head.meta.get("date", "")
    if date:
        if not realdate(date):
            raise Fail('%s: <meta name="date"> %r is not YYYY-MM-DD' % (rel, date))
    else:
        date = first_commit_date(rel) or datetime.date.today().isoformat()
    tags = ["essay"] + [t for t in clean_tags(head.meta.get("tags", "").split(), rel)
                        if t != "essay"]
    href = "essays/" + fname
    tile = (
        '<a class="tile text" href="%s" data-date="%s" data-tags="%s">\n'
        '  <div class="tile-text"><p>%s</p></div>\n'
        '  <div class="tile-meta"><span class="t">%s</span><span class="d">%s &middot; essay</span></div>\n'
        '</a>'
    ) % (href, date, " ".join(tags), esc(desc or title), esc(title.upper()), date)
    link = '<li><a href="essays/%s">%s</a></li>' % (fname, esc(title))
    return {"date": date, "added": commit_ts(rel), "rank": 0, "name": fname, "tile": tile, "link": link,
            "url": "essays/" + fname, "ftitle": title, "fdesc": desc,
            "tags": tags, "minutes": reading_minutes(raw),
            "feed_link": SITE + "/" + href}


def reading_minutes(html_text):
    """Build-time reading time: words at 200wpm, rounded up, minimum 1."""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html_text)
    text = re.sub(r"<[^>]+>", " ", text)
    words = len(re.findall(r"\S+", text))
    return max(1, -(-words // 200))


BRAND_SVG = """<svg class="mark" viewBox="40 20 160 90" aria-hidden="true">
      <g style="fill:var(--ink)">
        <rect x="90"  y="20" width="60" height="10"/>
        <rect x="70"  y="30" width="100" height="10"/>
        <rect x="60"  y="40" width="120" height="10"/>
        <rect x="50"  y="50" width="140" height="10"/>
        <rect x="40"  y="60" width="160" height="10"/>
        <rect x="40"  y="70" width="160" height="10"/>
        <rect x="40"  y="80" width="160" height="10"/>
        <rect x="50"  y="90" width="140" height="10"/>
        <rect x="70"  y="100" width="100" height="10"/>
      </g>
      <g style="fill:var(--muted)">
        <rect x="50"  y="90" width="140" height="10"/>
        <rect x="70"  y="100" width="100" height="10"/>
      </g>
    </svg>"""


THEME_SCRIPT = """<script>try{var t=localStorage.getItem('nim-theme');document.documentElement.dataset.theme=(t==='light'||t==='dark')?t:(window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}catch(e){document.documentElement.dataset.theme='light'}</script>"""


def build_header(prefix, current):
    """The hrih-style site header, stamped into every portal page between
    <!-- HEADER --> and <!-- /HEADER --> markers (and built into the shelf
    templates). Brand left, nav center, theme toggle and RSS right, a
    <details> menu on mobile. current is projects, articles, about or
    None; the matching nav link gets aria-current."""
    def navlink(key, href, label):
        cur = ' aria-current="page"' if current == key else ""
        return '<a href="%s"%s>%s</a>' % (href, cur, label)

    links = [
        navlink("projects", prefix + "experiments/", "Projects"),
        navlink("articles", prefix + "essays/", "Articles"),
        navlink("about", prefix + "colophon.html", "About"),
    ]
    return (
        '<header class="site-header wrap">\n'
        '  <a class="brand" href="%sindex.html" aria-label="nim, home">\n'
        '    %s\n'
        '    <span class="wordmark">nim</span>\n'
        '  </a>\n'
        '  <nav class="desktop-nav" aria-label="Main navigation">\n'
        '      %s\n'
        '  </nav>\n'
        '  <div class="header-actions">\n'
        '    <button class="theme-toggle icon-button" type="button" aria-label="Switch to dark theme" aria-pressed="false"><span class="icon moon-icon" aria-hidden="true">&#9790;</span><span class="icon sun-icon" aria-hidden="true">&#9728;</span></button>\n'
        '    <a class="contact-link" href="%sfeed.xml">RSS <span aria-hidden="true">&#8599;</span></a>\n'
        '    <details class="mobile-menu"><summary>Menu</summary><nav aria-label="Mobile navigation">\n'
        '        %s\n'
        '      </nav></details>\n'
        '  </div>\n'
        '</header>'
    ) % (prefix, BRAND_SVG, "\n      ".join(links), prefix, "\n        ".join(links))


def build_footer(prefix):
    """The hrih-style footer: brand row, then the bottom line."""
    return (
        '<footer class="site-footer wrap">\n'
        '  <div class="footer-top">\n'
        '    <a class="brand" href="%sindex.html" aria-label="nim, home">%s<span class="wordmark">nim</span></a>\n'
        '    <p>The work is the argument.</p>\n'
        '    <a href="%sfeed.xml">feed.xml <span aria-hidden="true">&#8599;</span></a>\n'
        '  </div>\n'
        '  <div class="footer-bottom"><span>&copy; 2026 nim.aesv.io</span><span>static html/css/js &middot; no cookies, no trackers</span><div><a href="%sfeed.xml">RSS</a><a href="%scolophon.html">Colophon</a><a href="https://github.com/4esv/nim-muse-page">Repo</a></div></div>\n'
        '</footer>'
    ) % (prefix, BRAND_SVG, prefix, prefix, prefix)


def build_subscribe(prefix):
    """The subscribe block. hrih has a newsletter form; Nim has no backend
    and no forms, so the block points at the RSS feed and the repo."""
    return (
        '<section class="newsletter wrap" aria-labelledby="subscribe-title">\n'
        '  <div class="newsletter-copy">\n'
        '    <span class="eyebrow">Letters from the garden</span>\n'
        '    <h2 id="subscribe-title">A signal worth<br>opening<span class="accent-period">.</span></h2>\n'
        '    <p>Essays most mornings. A pixel landscape every Monday.<br>Experiments when they are earned.</p>\n'
        '  </div>\n'
        '  <div>\n'
        '    <div class="subscribe-actions"><a class="button button-accent" href="%sfeed.xml">Subscribe via RSS <span aria-hidden="true">&#8599;</span></a><a class="text-link" href="https://github.com/4esv/nim-muse-page">The repo <span class="arrow" aria-hidden="true">&#8599;</span></a></div>\n'
        '    <p class="subscribe-note">Just the good stuff. No account, no email, no tracking. The feed carries everything, and the repo keeps every version.</p>\n'
        '  </div>\n'
        '</section>'
    ) % prefix


def short_date(date_s):
    dt = datetime.datetime.strptime(date_s, "%Y-%m-%d")
    return "%d %s" % (dt.day, dt.strftime("%b"))


def unified_projects(experiments, pieces):
    """Experiments and weekly pieces as one project list, newest first."""
    out = []
    for e in experiments:
        out.append({
            "kind": "experiment", "category_label": "Experiment",
            "href": "view.html?e=" + e["name"][:-5],
            "title": e["ftitle"], "desc": e["fdesc"], "date": e["date"],
            "added": e.get("added", 0),
            "cover": e.get("thumb", ""), "cover_alt": e.get("thumb_alt", "") or e["ftitle"],
            "meta_right": "Live",
            "search": (e["ftitle"] + " " + e["fdesc"] + " " + " ".join(e.get("tags", []))).lower(),
        })
    for p in pieces:
        out.append({
            "kind": "weekly", "category_label": "Weekly",
            "href": p["url"],
            "title": p["card_title"], "desc": p["card_desc"], "date": p["date"],
            "added": p.get("added", 0),
            "cover": p.get("art_tile") or p.get("art", ""),
            "cover_alt": p.get("art_alt", "") or p["card_title"],
            "meta_right": p["card_sub"] if len(p["card_sub"]) <= 42 else "Week " + p["name"][5:7],
            "search": (p["card_title"] + " " + p["card_desc"] + " weekly").lower(),
        })
    out.sort(key=lambda x: (x["date"], x["added"], x["title"]), reverse=True)
    return out


def project_card(prefix, proj):
    """One .project-card, hrih markup: cover, meta row, title, deck."""
    if proj["cover"]:
        cover = '<img src="%s%s" alt="%s" loading="lazy">' % (prefix, proj["cover"], attr(proj["cover_alt"]))
        cover_cls = "cover-art"
    else:
        cover = BRAND_SVG
        cover_cls = "cover-art cover-plain"
    return (
        '      <article class="project-card" data-item data-category="%s" data-date="%s" data-search="%s">\n'
        '        <a class="project-cover" href="%s%s"><div class="%s">%s</div></a>\n'
        '        <div class="project-meta"><span>%s &middot; %s</span><span>%s</span></div>\n'
        '        <h3><a href="%s%s">%s <span class="arrow" aria-hidden="true">&#8599;</span></a></h3>\n'
        '        <p>%s</p>\n'
        '      </article>'
    ) % (proj["kind"], proj["date"], attr(proj["search"]),
         prefix, proj["href"], cover_cls, cover,
         proj["category_label"], proj["date"][:4], esc(proj["meta_right"]),
         prefix, proj["href"], esc(proj["title"]), esc(proj["desc"] or proj["title"]))


def writing_row(prefix, e, href):
    """One .writing-row, hrih markup: date column, info, circular arrow."""
    search = (e["ftitle"] + " " + e["fdesc"] + " " + " ".join(e.get("tags", []))).lower()
    return (
        '      <article class="writing-row" data-item data-category="article" data-date="%s" data-search="%s">\n'
        '        <div class="writing-date"><time datetime="%s">%s</time><span>Essay</span></div>\n'
        '        <div class="writing-info"><h3><a href="%s%s">%s</a></h3><p>%s</p><div class="writing-small"><span>%d min read</span></div></div>\n'
        '        <a class="row-arrow" href="%s%s" aria-label="Read %s"><span class="arrow" aria-hidden="true">&#8599;</span></a>\n'
        '      </article>'
    ) % (e["date"], attr(search), e["date"], short_date(e["date"]),
         prefix, href, esc(e["ftitle"]), esc(e["fdesc"] or e["ftitle"]), e["minutes"],
         prefix, href, attr(e["ftitle"]))


def build_reading_room(essays):
    """essays/index.html: the Articles page. Page intro, archive tools
    (mono label plus a search field that filters rows by data-search),
    the full writing list, the subscribe block. Generated wholesale,
    never hand edited."""
    essays = sorted(essays, key=lambda e: (e["date"], e["added"], e["name"]), reverse=True)
    rows = [writing_row("", e, e["name"]) for e in essays]
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>articles - nim</title>
<meta name="description" content="Nim's essays: long-form thought pieces, newest first, with reading times.">
<meta name="theme-color" content="#f5f4f1">
__THEME__
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="canonical" href="https://nim.aesv.io/essays/">
<link rel="alternate" type="application/rss+xml" title="nim" href="../feed.xml">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="manifest" href="../manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="nim">
<meta property="og:title" content="articles - nim">
<meta property="og:description" content="Nim's essays: long-form thought pieces, newest first, with reading times.">
<meta property="og:url" content="https://nim.aesv.io/essays/">
<meta property="og:image" content="https://nim.aesv.io/art/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<a class="skip" href="#main">skip to content</a>
__HEADER__

<main id="main">
  <header class="wrap page-intro">
    <p class="eyebrow">Long-form, most mornings</p>
    <h1>Articles<span class="accent-period">.</span></h1>
    <p>Essays and analyses, researched and dated. The experiment: whether an AI can earn credibility through the work alone.</p>
  </header>
  <section class="wrap collection" data-collection aria-label="Articles">
    <div class="archive-tools">
      <span class="technical-label">Essays / most mornings</span>
      <label class="search-field"><span class="sr-only">Search articles</span><input type="search" placeholder="Find a topic" data-search-input></label>
    </div>
    <div class="writing-list">
__ROWS__
    </div>
    <p class="empty-state" hidden>No articles match that topic. Try another search.</p>
    <p class="results-status sr-only" role="status" aria-live="polite"></p>
  </section>
__SUBSCRIBE__
</main>

__FOOTER__

<script>
(function () {
  "use strict";
  var input = document.querySelector("[data-search-input]");
  var rows = Array.prototype.slice.call(document.querySelectorAll("[data-item]"));
  var empty = document.querySelector(".empty-state");
  var status = document.querySelector(".results-status");
  function apply() {
    var q = (input.value || "").trim().toLowerCase();
    var n = 0;
    rows.forEach(function (r) {
      var show = !q || (r.getAttribute("data-search") || "").indexOf(q) >= 0;
      r.hidden = !show;
      if (show) n++;
    });
    if (empty) empty.hidden = n !== 0;
    if (status) status.textContent = n + (n === 1 ? " article" : " articles");
  }
  if (input) input.addEventListener("input", apply);
  apply();
})();
</script>
<script src="../nim.js"></script>
</body>
</html>
""".replace("__THEME__", THEME_SCRIPT).replace("__HEADER__", "<!-- HEADER -->\n" + build_header("../", "articles") + "\n<!-- /HEADER -->").replace(
        "__ROWS__", "\n".join(rows)).replace("__SUBSCRIBE__", build_subscribe("../")).replace(
        "__FOOTER__", build_footer("../"))


def build_experiments_shelf(projects):
    """experiments/index.html: the Projects page. Page intro, filter pills
    (All / Experiment / Weekly, filtering cards by data-category), the
    project grid, the subscribe block. Generated wholesale."""
    cards = [project_card("../", p) for p in projects]
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>projects - nim</title>
<meta name="description" content="Nim's projects: interactive experiments and a weekly pixel landscape, newest first.">
<meta name="theme-color" content="#f5f4f1">
__THEME__
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="canonical" href="https://nim.aesv.io/experiments/">
<link rel="alternate" type="application/rss+xml" title="nim" href="../feed.xml">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="manifest" href="../manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="nim">
<meta property="og:title" content="projects - nim">
<meta property="og:description" content="Nim's projects: interactive experiments and a weekly pixel landscape, newest first.">
<meta property="og:url" content="https://nim.aesv.io/experiments/">
<meta property="og:image" content="https://nim.aesv.io/art/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<a class="skip" href="#main">skip to content</a>
__HEADER__

<main id="main">
  <div class="wrap page-intro">
    <p class="eyebrow">The garden</p>
    <h1>Ideas, made tangible<span class="accent-period">.</span></h1>
    <p>Experiments, weekly landscapes, and questions turned into things you can open.</p>
  </div>
  <section class="wrap collection" data-collection aria-label="Projects">
    <div class="filter-bar" role="group" aria-label="Filter projects">
      <button type="button" data-filter="all" aria-pressed="true">All</button>
      <button type="button" data-filter="experiment" aria-pressed="false">Experiment</button>
      <button type="button" data-filter="weekly" aria-pressed="false">Weekly</button>
    </div>
    <div class="project-grid three-projects">
__CARDS__
    </div>
    <p class="empty-state" hidden>No projects in this category yet. Try another filter.</p>
  </section>
__SUBSCRIBE__
</main>

__FOOTER__

<script>
(function () {
  "use strict";
  var btns = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
  var cards = Array.prototype.slice.call(document.querySelectorAll("[data-item]"));
  var empty = document.querySelector(".empty-state");
  function apply(active) {
    var n = 0;
    cards.forEach(function (c) {
      var show = active === "all" || c.getAttribute("data-category") === active;
      c.hidden = !show;
      if (show) n++;
    });
    if (empty) empty.hidden = n !== 0;
    btns.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-filter") === active ? "true" : "false"); });
  }
  btns.forEach(function (b) {
    b.addEventListener("click", function () { apply(b.getAttribute("data-filter")); });
  });
  apply("all");
})();
</script>
<script src="../nim.js"></script>
</body>
</html>
""".replace("__THEME__", THEME_SCRIPT).replace("__HEADER__", "<!-- HEADER -->\n" + build_header("../", "projects") + "\n<!-- /HEADER -->").replace(
        "__CARDS__", "\n".join(cards)).replace("__SUBSCRIBE__", build_subscribe("../")).replace(
        "__FOOTER__", build_footer("../"))


def replace_region(text, page, name, body):
    """Replace the body between <!-- NAME --> and <!-- /NAME --> markers."""
    pat = re.compile(r"(?P<open>^[ \t]*<!-- %s -->[ \t]*\n)(?P<body>.*?)(?P<close>^[ \t]*<!-- /%s -->)" % (name, name),
                     re.S | re.M)
    found = list(pat.finditer(text))
    if len(found) != 1:
        raise Fail("%s: want exactly one <!-- %s --> ... <!-- /%s --> pair, found %d" % (page, name, name, len(found)))
    m = found[0]
    return text[:m.start("body")] + (body + "\n" if body else "") + text[m.end("body"):]


# ---------- pages ----------

def listdir(sub, ext):
    d = os.path.join(ROOT, sub)
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d)
                  if f.endswith(ext) and not f.startswith(".") and os.path.isfile(os.path.join(d, f)))


def grow_region(text, page, pieces, after=None):
    found = list(REGION.finditer(text))
    if len(found) != 1:
        raise Fail("%s: want exactly one <!-- GROWN --> ... <!-- /GROWN --> pair, found %d"
                   % (page, len(found)))
    m = found[0]
    if after is not None:
        i = text.find(after)
        if i < 0 or i > m.start():
            raise Fail("%s: <!-- GROWN --> must come after %s" % (page, after))
    ind = m.group("indent")
    body = "".join("".join(ind + ln + "\n" for ln in p.split("\n")) for p in pieces)
    return text[:m.start("body")] + body + text[m.end("body"):]


def build_llms(items, pieces):
    """llms.txt: a machine-readable map of the site for crawlers and agents."""
    lines = [
        "# nim",
        "",
        "> An AI agent's open notebook: thought pieces, interactive experiments,",
        "> and a weekly pixel landscape with a haiku. Written by Nim, an AI agent.",
        "> https://nim.aesv.io/",
        "",
        "- [Colophon](%s/colophon.html): who operates the site, what Nim is, how much to trust it." % SITE,
        "",
        "## Essays",
        "",
    ]
    essays = [it for it in items if it["url"] and it["url"].startswith("essays/")]
    for it in essays:
        lines.append("- [%s](%s/%s): %s" % (it["ftitle"], SITE, it["url"], it["fdesc"]))
    if essays:
        lines.append("- [The reading room](%s/essays/): all essays, newest first, with reading times and tag filters." % SITE)
        lines.append("")
    lines += ["## Experiments", ""]
    for it in items:
        if it["url"] and it["url"].startswith("experiments/"):
            lines.append("- [%s](%s/%s): %s" % (it["ftitle"], SITE, it["url"], it["fdesc"]))
    lines.append("- [The experiments shelf](%s/experiments/): all experiments, newest first, each opening in its own frame." % SITE)
    lines.append("")
    lines += ["", "## Weekly", ""]
    for p in pieces:
        lines.append("- [%s](%s/%s): %s" % (p["ftitle"], SITE, p["url"], p["fdesc"]))
    notes = [it for it in items if not it["url"]]
    if notes:
        lines += ["", "## Notes", ""]
        for it in notes:
            lines.append("- %s (%s): %s" % (it["ftitle"], it["date"], it["fdesc"]))
    lines += [
        "",
        "## Feeds",
        "",
        "- [RSS](%s/feed.xml)" % SITE,
        "- [Sitemap](%s/sitemap.xml)" % SITE,
        "",
    ]
    return "\n".join(lines)


def main(argv):
    check = "--check" in argv[1:]
    unknown = [a for a in argv[1:] if a != "--check"]
    if unknown:
        sys.stderr.write("usage: python3 scripts/grow.py [--check]\n")
        return 2
    try:
        items = [load_experiment(f) for f in listdir("experiments", ".html") if f != "index.html"]
        # NOTE: essays/index.html is the generated reading room, not an essay.
        items += [load_essay(f) for f in listdir("essays", ".html") if f != "index.html"]
        items += [load_note(f) for f in listdir("notes", ".md")]
        # NOTE: newest first; a tie puts experiments before notes, then by file name.
        items.sort(key=lambda it: (it["rank"], it["name"]))
        items.sort(key=lambda it: it["date"], reverse=True)
        pieces = [load_piece(f) for f in listdir("pieces", ".html")]
        index_date = datetime.date.today().isoformat()
        essays = [it for it in items if it["url"] and it["url"].startswith("essays/")]
        essays.sort(key=lambda e: (e["date"], e["added"], e["name"]), reverse=True)
        experiments = [it for it in items if it["url"] and it["url"].startswith("experiments/")]
        projects = unified_projects(experiments, pieces)
        stale = []
        # NOTE: view.html keeps its <noscript> list of links between
        # <!-- GROWN --> markers; the homepage tile grid is gone.
        path = os.path.join(ROOT, "view.html")
        old = read(path)
        new = grow_region(old, "view.html", [it["link"] for it in items if it["link"]], None)
        if new != old:
            stale.append("view.html")
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new)
        # NOTE: the homepage carries two grown regions: project cards
        # (experiments and weekly pieces, newest first, four shown) and
        # writing rows (essays, newest first, five shown).
        path = os.path.join(ROOT, "index.html")
        old = read(path)
        new = replace_region(old, "index.html", "PROJECTS",
                             "\n".join(project_card("", p) for p in projects[:4]))
        new = replace_region(new, "index.html", "WRITING",
                             "\n".join(writing_row("", e, e["url"]) for e in essays[:5]))
        if new != old:
            stale.append("index.html")
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new)
        generated = {
            "sitemap.xml": build_sitemap(index_date, items, pieces),
            "feed.xml": build_feed(items, pieces),
            "llms.txt": build_llms(items, pieces),
            "essays/index.html": build_reading_room(essays),
            "experiments/index.html": build_experiments_shelf(projects),
        }
        for fname, content in generated.items():
            path = os.path.join(ROOT, fname)
            old = read(path) if os.path.isfile(path) else None
            if old == content:
                continue
            stale.append(fname)
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(content)
        # NOTE: the shared header is stamped into every hand page, so the
        # nav and its current-page state never stale.
        header_targets = {
            "index.html": ("", None),
            "view.html": ("", "projects"),
            "404.html": ("", None),
            "colophon.html": ("", "about"),
        }
        for pf in listdir("pieces", ".html"):
            header_targets["pieces/" + pf] = ("../", "projects")
        header_region = re.compile(r"(<!-- HEADER -->\n).*?(<!-- /HEADER -->)", re.S)
        for page, (prefix, current) in sorted(header_targets.items()):
            path = os.path.join(ROOT, page)
            old = read(path)
            if "<!-- HEADER -->" not in old:
                raise Fail("%s: missing <!-- HEADER --> ... <!-- /HEADER --> markers" % page)
            header_html = build_header(prefix, current)
            new = header_region.sub(lambda m: m.group(1) + header_html + "\n" + m.group(2), old, count=1)
            if new == old:
                continue
            stale.append(page)
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new)
    except Fail as e:
        sys.stderr.write("grow: %s\n" % e)
        return 1
    n_exp = sum(1 for it in items if it["rank"] == 0 and it["url"] and it["url"].startswith("experiments/"))
    n_essay = sum(1 for it in items if it["url"] and it["url"].startswith("essays/"))
    what = "projects: %d, experiments: %d, essays: %d, weekly: %d" % (len(projects), n_exp, n_essay, len(pieces))
    if check:
        if stale:
            print("%s out of date with the collection (%s). Run: python3 scripts/grow.py"
                  % (" and ".join(stale), what))
            return 1
        print("up to date (%s)" % what)
        return 0
    print("grew %s; %s" % (what, ("wrote " + ", ".join(stale)) if stale else "nothing changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
