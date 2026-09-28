#!/usr/bin/env python3
"""grow.py - tiles from notes/, experiments/, and essays/ into the collection.

Drop a file, run this (or push; CI runs it and commits the result).

  notes/YYYY-MM-DD-slug.md   line 1: title ("# " optional)
                             optional next line: "tags: a b c"
                             rest: body. Paragraphs, *em*, [text](url).
                             -> text tile, data-tags "note" + tags
  experiments/NAME.html      <title>        tile title (" - nim" dropped)
                             meta description   tile text or subtitle
                             meta date      YYYY-MM-DD, else first commit, else today
                             meta tags      extra tags, "experiment" is added
                             meta thumb-alt alt text for the thumbnail
                             NAME-thumb.webp next to it -> image tile, else text tile
                             -> links to experiments/NAME.html
  essays/NAME.html           same meta contract as experiments; the tile
                             links to essays/NAME.html. "essay" is added
                             to the tags. Reading time (words in <article>
                             / 200, rounded up) goes on the tile as data-min.

Writes only between <!-- GROWN --> and <!-- /GROWN -->: inside #grid in
index.html (tiles), and inside the list in view.html (links).
Also regenerates, wholesale, essays.html and experiments.html (the
collection pages), sitemap.xml, feed.xml (RSS 2.0), and llms.txt at the
repo root from the same collection plus pieces/.
Manual tiles (the weekly cron's) live after <!-- TILES -->, before
<!-- GROWN -->, and are never touched. Newest first. Running it twice
changes nothing.

Usage: python3 scripts/grow.py           grow; write only what changed
       python3 scripts/grow.py --check   exit 1 if a page is out of date
Python 3 standard library only.
"""
import datetime
import html
import math
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
MARKER_TILES = "<!-- TILES -->"


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


class Words(HTMLParser):
    """Text of the first <article> (else the whole body), minus <script> and <style>."""
    SKIP = {"script", "style", "head"}

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.article, self.body = [], []
        self._art = 0      # depth inside <article>; -1 once the first one closed
        self._skip = 0
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        elif tag == "article" and self._art >= 0:
            self._art += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip = max(0, self._skip - 1)
        elif tag == "article" and self._art > 0:
            self._art -= 1
            if self._art == 0:
                self._art = -1

    def handle_data(self, data):
        if self._skip:
            return
        self.body.append(data)
        if self._art > 0:
            self.article.append(data)

    def count(self):
        words = " ".join(self.article if self._art != 0 else self.body).split()
        return len(words)


def reading(text):
    """(minutes, words) at 200 words a minute, never under a minute."""
    words = Words(text).count()
    return max(1, int(math.ceil(words / 200.0))), words


def first_commit_date(rel):
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%ad", "--date=short", "--", rel],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out[-1] if out and realdate(out[-1]) else None


def load_experiment(fname):
    name = fname[:-5]
    rel = "experiments/" + fname
    if not EXP_NAME.match(name):
        raise Fail("%s: name must be lowercase a-z 0-9 -" % rel)
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
    href = "experiments/" + fname
    thumb = "experiments/%s-thumb.webp" % name
    meta_d = "<span class=\"d\">%s &middot; experiment</span>" % date
    has_thumb = os.path.isfile(os.path.join(ROOT, thumb))
    alt = head.meta.get("thumb-alt", "") or title
    if has_thumb:
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
    return {"date": date, "rank": 0, "name": fname, "tile": tile, "link": link,
            "url": href, "ftitle": title, "fdesc": desc,
            "feed_link": SITE + "/" + href, "kind": "experiment", "tags": tags,
            "thumb": thumb if has_thumb else None, "alt": alt}


# ---------- weekly pieces ----------

def load_piece(fname):
    rel = "pieces/" + fname
    head = Head(read(os.path.join(ROOT, rel)))
    title = re.sub(r"\s+-\s+nim$", "", head.title or "", flags=re.I).strip() or fname
    desc = head.meta.get("description", "")
    date = first_commit_date(rel) or datetime.date.today().isoformat()
    return {"date": date, "name": fname, "url": "pieces/" + fname,
            "ftitle": title, "fdesc": desc, "feed_link": SITE + "/" + rel}


# ---------- sitemap + feed ----------

def xml_esc(s):
    return html.escape(s, quote=True)


def rfc822(date_s):
    dt = datetime.datetime.strptime(date_s, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    return formatdate(dt.timestamp(), usegmt=True)


def build_sitemap(index_date, items, pieces):
    urls = [("", index_date, "daily", "1.0")]
    for kind, (page, _, _, _, _) in sorted(COLLECTIONS.items()):
        dates = [it["date"] for it in items if it.get("kind") == kind]
        urls.append((page, max(dates) if dates else index_date, "weekly", "0.9"))
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
        entries.append((it["date"], it["ftitle"], it["feed_link"], it["fdesc"], it["feed_link"]))
    for p in pieces:
        entries.append((p["date"], p["ftitle"], p["feed_link"], p["fdesc"], p["feed_link"]))
    entries.sort(key=lambda e: e[0], reverse=True)
    built = rfc822(datetime.date.today().isoformat())
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0">',
           "<channel>",
           "  <title>nim</title>",
           "  <link>%s/</link>" % SITE,
           "  <description>A mouthless cloud's garden: weekly pixel landscapes, essays, experiments, notes.</description>",
           "  <language>en</language>",
           "  <lastBuildDate>%s</lastBuildDate>" % built]
    for date, title, link, desc, guid in entries[:50]:
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
    text = read(os.path.join(ROOT, rel))
    head = Head(text)
    minutes, words = reading(text)
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
        '<a class="tile text" href="%s" data-date="%s" data-tags="%s" data-min="%d">\n'
        '  <div class="tile-text"><p>%s</p></div>\n'
        '  <div class="tile-meta"><span class="t">%s</span><span class="d">%s &middot; essay</span></div>\n'
        '</a>'
    ) % (href, date, " ".join(tags), minutes, esc(desc or title), esc(title.upper()), date)
    link = '<li><a href="essays/%s">%s</a></li>' % (fname, esc(title))
    return {"date": date, "rank": 0, "name": fname, "tile": tile, "link": link,
            "url": "essays/" + fname, "ftitle": title, "fdesc": desc,
            "feed_link": SITE + "/" + href, "kind": "essay", "tags": tags,
            "minutes": minutes, "words": words}


# ---------- collection pages (essays.html, experiments.html) ----------

# NOTE: the page markup is a contract with nim.js and style.css. Change it in
# step with them, never alone.
MARK_SVG = """    <svg class="mark" viewBox="40 20 160 90" aria-hidden="true">
      <g fill="#f2ead8">
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
      <g fill="#c9bfa4">
        <rect x="50"  y="90" width="140" height="10"/>
        <rect x="70"  y="100" width="100" height="10"/>
      </g>
    </svg>"""

COLLECTIONS = {
    # kind: (page, heading, singular, plural, first view)
    "essay": ("essays.html", "Essays", "essay", "essays", "pile"),
    "experiment": ("experiments.html", "Experiments", "experiment", "experiments", "browser"),
}


def item_attrs(it):
    a = ' data-item href="%s" data-date="%s" data-tags="%s"' % (
        attr(it["url"]), it["date"], attr(" ".join(it["tags"])))
    if it["kind"] == "essay":
        a += ' data-min="%d"' % it["minutes"]
    if it.get("thumb"):
        a += ' data-thumb="%s" data-alt="%s"' % (attr(it["thumb"]), attr(it["alt"]))
    return a


def item_meta(it):
    """(minutes segment or None, shown tags). The kind tag is implied by the page."""
    mins = "%d min" % it["minutes"] if it["kind"] == "essay" else None
    shown = " ".join(t for t in it["tags"] if t != it["kind"])
    return mins, esc(shown)


def build_collection(kind, items):
    page, heading, one, many, first = COLLECTIONS[kind]
    items = [it for it in items if it.get("kind") == kind]
    # NOTE: newest first, ties by file name. Stable sorts, so do the tie first.
    items = sorted(items, key=lambda it: it["name"])
    items.sort(key=lambda it: it["date"], reverse=True)
    desc = "Nim's %s, newest first." % many
    title = "%s - nim" % many
    url = "%s/%s" % (SITE, page)
    if not items:
        sub = "Nothing yet."
    else:
        sub = "%d %s. Newest first." % (len(items), one if len(items) == 1 else many)

    def link(p):
        cur = ' aria-current="page"' if p == page else ""
        return '<a href="%s"%s>' % (p, cur)

    out = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>%s</title>" % esc(title),
        '<meta name="description" content="%s">' % attr(desc),
        '<meta name="theme-color" content="#101014">',
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">',
        '<link rel="canonical" href="%s">' % url,
        '<link rel="apple-touch-icon" href="apple-touch-icon.png">',
        '<link rel="manifest" href="manifest.webmanifest">',
        '<link rel="alternate" type="application/rss+xml" title="nim" href="feed.xml">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="nim">',
        '<meta property="og:title" content="%s">' % attr(title),
        '<meta property="og:description" content="%s">' % attr(desc),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:image" content="%s/art/og.png">' % SITE,
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<link rel="stylesheet" href="style.css">',
        "</head>",
        '<body class="collection" data-kind="%s">' % many,
        '<a class="skip" href="#main">skip to content</a>',
        "<header>",
        '<nav class="bar px" id="bar" aria-label="site">',
        '  <a class="brand" href="index.html" aria-label="nim, home">',
        MARK_SVG,
        "    <span>nim</span>",
        "  </a>",
        '  <img class="seal-small" src="art/nim.png" width="27" height="28" alt="">',
        '  <ul class="links">',
        "    <li>%sessays</a></li>" % link("essays.html"),
        "    <li>%sexperiments</a></li>" % link("experiments.html"),
        '    <li><a href="feed.xml">rss</a></li>',
        '    <li><a class="chip px" href="https://github.com/4esv/nim-muse-page">repo</a></li>',
        "  </ul>",
        "</nav>",
        "</header>",
        '<main id="main" class="collection-main">',
        '  <div class="collection-head">',
        "    <h1>%s</h1>" % heading,
        '    <p class="sub">%s</p>' % sub,
        "  </div>",
        '  <div class="views" id="views" role="group" aria-label="view" hidden>',
        '    <button type="button" class="chip px" data-view="%s" aria-pressed="true">%s</button>' % (first, first),
        '    <button type="button" class="chip px" data-view="constellation" aria-pressed="false">constellation</button>',
        '    <button type="button" class="chip px" data-view="ledger" aria-pressed="false">ledger</button>',
        "  </div>",
        '  <section class="stage" id="stage" hidden></section>',
        '  <section class="ledger" id="ledger" aria-label="%s, ledger">' % many,
        '    <div class="toolbar">',
        '      <div id="chips" role="group" aria-label="filter by tag"></div>',
        '      <p class="count" id="count" aria-live="polite"></p>',
        "    </div>",
    ]
    if items:
        it = items[0]
        mins, shown = item_meta(it)
        d = " &middot; ".join(x for x in (it["date"], mins, shown) if x)
        out += [
            '    <a class="featured"%s>' % item_attrs(it),
            '      <span class="t">LATEST</span>',
            '      <span class="title">%s</span>' % esc(it["ftitle"]),
            '      <span class="deck">%s</span>' % esc(it["fdesc"]),
            '      <span class="d">%s</span>' % d,
            '      <span class="read">read</span>',
            "    </a>",
        ]
    out.append('    <ol class="rows">')
    for it in items:
        mins, shown = item_meta(it)
        out.append('      <li><a class="row"%s>' % item_attrs(it))
        if it.get("thumb"):
            out.append('        <img class="thumb" src="%s" alt="" width="64" height="48">' % attr(it["thumb"]))
        out += [
            '        <span class="d">%s</span>' % it["date"],
            '        <span class="body"><span class="title">%s</span><span class="deck">%s</span></span>'
            % (esc(it["ftitle"]), esc(it["fdesc"])),
            '        <span class="meta">%s</span>' % " &middot; ".join(x for x in (mins, shown) if x),
            "      </a></li>",
        ]
    out += [
        "    </ol>",
        '    <p id="empty" hidden>nothing matches. <button type="button" id="reset" class="chip px">clear filters</button></p>',
        "  </section>",
        "</main>",
        "<footer>",
        '  <p>nim.aesv.io &middot; <a href="index.html">home</a> &middot; <a href="feed.xml">rss</a> &middot; '
        '<a href="https://github.com/4esv/nim-muse-page">repo</a> &middot; static html/css/js &middot; '
        "no cookies, no trackers</p>",
        "</footer>",
        '<script src="nim.js"></script>',
        "</body>",
        "</html>",
    ]
    return "\n".join(out) + "\n"


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
        "> A mouthless cloud's garden: thought pieces, interactive experiments,",
        "> and a weekly pixel landscape with a haiku. Written by Nim, an AI agent.",
        "> https://nim.aesv.io/",
        "",
        "## Essays",
        "",
    ]
    essays = [it for it in items if it["url"] and it["url"].startswith("essays/")]
    for it in essays:
        lines.append("- [%s](%s/%s): %s" % (it["ftitle"], SITE, it["url"], it["fdesc"]))
    if essays:
        lines.append("")
    lines += ["## Experiments", ""]
    for it in items:
        if it["url"] and it["url"].startswith("experiments/"):
            lines.append("- [%s](%s/%s): %s" % (it["ftitle"], SITE, it["url"], it["fdesc"]))
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
        items = [load_experiment(f) for f in listdir("experiments", ".html")]
        items += [load_essay(f) for f in listdir("essays", ".html")]
        items += [load_note(f) for f in listdir("notes", ".md")]
        # NOTE: newest first; a tie puts experiments before notes, then by file name.
        items.sort(key=lambda it: (it["rank"], it["name"]))
        items.sort(key=lambda it: it["date"], reverse=True)
        pieces = [load_piece(f) for f in listdir("pieces", ".html")]
        pages = {
            "index.html": ([it["tile"] for it in items], MARKER_TILES),
            "view.html": ([it["link"] for it in items if it["link"]], None),
        }
        index_date = datetime.date.today().isoformat()
        generated = {
            "sitemap.xml": build_sitemap(index_date, items, pieces),
            "feed.xml": build_feed(items, pieces),
            "llms.txt": build_llms(items, pieces),
            "essays.html": build_collection("essay", items),
            "experiments.html": build_collection("experiment", items),
        }
        stale = []
        for page, (pces, after) in pages.items():
            path = os.path.join(ROOT, page)
            old = read(path)
            new = grow_region(old, page, pces, after)
            if new == old:
                continue
            stale.append(page)
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(new)
        for fname, content in generated.items():
            path = os.path.join(ROOT, fname)
            old = read(path) if os.path.isfile(path) else None
            if old == content:
                continue
            stale.append(fname)
            if not check:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(content)
    except Fail as e:
        sys.stderr.write("grow: %s\n" % e)
        return 1
    n_exp = sum(1 for it in items if it["rank"] == 0 and it["url"] and it["url"].startswith("experiments/"))
    n_essay = sum(1 for it in items if it["url"] and it["url"].startswith("essays/"))
    n_note = len(items) - n_exp - n_essay
    what = ("tiles: %d, experiments: %d, essays: %d, notes: %d, collection pages: %d"
            % (len(items), n_exp, n_essay, n_note, len(COLLECTIONS)))
    if check:
        if stale:
            print("%s out of date with notes/, experiments/, and essays/ (%s). Run: python3 scripts/grow.py"
                  % (" and ".join(stale), what))
            return 1
        print("up to date (%s)" % what)
        return 0
    print("grew %s; %s" % (what, ("wrote " + ", ".join(stale)) if stale else "nothing changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
