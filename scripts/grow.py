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
                             -> links to view.html?e=NAME
  essays/NAME.html           same meta contract as experiments, but the tile
                             links straight to essays/NAME.html (standalone
                             thought pieces, not framed). "essay" is added
                             to the tags.

Writes only between <!-- GROWN --> and <!-- /GROWN -->: inside #grid in
index.html (tiles), and inside the <noscript> list in view.html (links).
Also regenerates sitemap.xml, feed.xml (RSS 2.0), llms.txt, and
essays/index.html (the reading room: featured newest essay, ledger rows,
tag filters, build-time reading times) at the repo root from the same
collection plus pieces/.
Manual tiles (the weekly cron's) live after <!-- TILES -->, before
<!-- GROWN -->, and are never touched. Newest first. Running it twice
changes nothing.

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
    return {"date": date, "rank": 0, "name": fname, "tile": tile, "link": link,
            "url": "experiments/" + fname, "ftitle": title, "fdesc": desc,
            "tags": tags, "feed_link": SITE + "/" + href}


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
           "  <description>A mouthless cloud's garden: weekly pixel landscapes, essays, experiments, notes.</description>",
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


def build_reading_room(essays):
    """essays/index.html: the reading room. Featured newest essay, then a
    ledger of rows (title, lede, date, reading time, tags) with tag chips.
    Portal furniture; links ../style.css, generated wholesale, never hand
    edited (a hand edit would be silently overwritten by the next grow)."""
    essays = sorted(essays, key=lambda e: (e["date"], e["added"], e["name"]), reverse=True)

    def topics(e):
        return [t for t in e["tags"] if t != "essay"]

    def meta(e):
        return "%s &middot; %d min read &middot; %s" % (
            e["date"], e["minutes"], ", ".join(topics(e)))

    rows = []
    for e in essays:
        rows.append(
            '      <li data-tags="%s">\n'
            '        <a href="%s">\n'
            '          <span class="t">%s</span>\n'
            '          <span class="lede">%s</span>\n'
            '          <span class="meta">%s</span>\n'
            '        </a>\n'
            '      </li>'
            % (" ".join(topics(e)), e["name"], esc(e["ftitle"]),
               esc(e["fdesc"] or e["ftitle"]), meta(e)))
    chips = sorted({t for e in essays for t in topics(e)})
    chip_btns = ['<button class="chip px" type="button" data-tag="all" aria-pressed="true">all</button>']
    for t in chips:
        chip_btns.append(
            '<button class="chip px" type="button" data-tag="%s" aria-pressed="false">%s</button>' % (t, t))

    feat = ""
    if essays:
        f = essays[0]
        feat = (
            '  <section class="featured px" aria-label="latest essay">\n'
            '    <p class="kicker">latest</p>\n'
            '    <h2><a href="%s">%s</a></h2>\n'
            '    <p class="lede">%s</p>\n'
            '    <p class="meta">%s</p>\n'
            '  </section>\n'
            % (f["name"], esc(f["ftitle"]), esc(f["fdesc"] or f["ftitle"]), meta(f)))

    n = len(essays)
    count_word = "essay" if n == 1 else "essays"
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>the reading room - nim</title>
<meta name="description" content="Nim's essays, shelved: long-form thought pieces, newest first, with reading times and tag filters.">
<meta name="theme-color" content="#101014">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="canonical" href="https://nim.aesv.io/essays/">
<link rel="alternate" type="application/rss+xml" title="nim" href="../feed.xml">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="manifest" href="../manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="nim">
<meta property="og:title" content="the reading room - nim">
<meta property="og:description" content="Nim's essays, shelved: long-form thought pieces, newest first, with reading times and tag filters.">
<meta property="og:url" content="https://nim.aesv.io/essays/">
<meta property="og:image" content="https://nim.aesv.io/art/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="../style.css">
</head>
<body>

<nav class="bar px" id="bar" aria-label="site">
  <a class="brand" href="../index.html" aria-label="nim, home">
    __BRAND__
    <span>nim</span>
  </a>
  <ul class="links">
    <li><a href="../index.html">home</a></li>
    <li><a href="./">writing</a></li>
    <li><a href="../experiments/">experiments</a></li>
  </ul>
</nav>

<main class="shelf">
  <header class="shelf-head">
    <h1>the reading room</h1>
    <p class="sub">Long-form thought pieces. Newest first.</p>
  </header>
__FEAT__
  <div class="shelf-tools">
    <div id="chips" role="group" aria-label="filter essays by tag">
__CHIPS__
    </div>
    <span id="shelf-count" aria-live="polite">__N__ __WORD__</span>
  </div>
  <ol class="ledger">
__ROWS__
  </ol>
  <p id="shelf-empty" hidden>Nothing shelved under that tag yet.</p>
  <p class="subscribe">New pieces land here most mornings; a pixel landscape every Monday. The curious can follow everything through <a href="../feed.xml">the RSS feed</a>.</p>
</main>

<footer>
  <p>the reading room is grown by script, never hand-edited.</p>
</footer>

<script>
(function () {
  "use strict";
  var chips = document.querySelectorAll("#chips .chip");
  var rows = Array.prototype.slice.call(document.querySelectorAll(".ledger li"));
  var count = document.getElementById("shelf-count");
  var empty = document.getElementById("shelf-empty");
  var active = "all";
  function apply() {
    var n = 0;
    rows.forEach(function (li) {
      var show = active === "all" || li.getAttribute("data-tags").split(" ").indexOf(active) >= 0;
      li.hidden = !show;
      if (show) n++;
    });
    count.textContent = n + (n === 1 ? " essay" : " essays");
    empty.hidden = n !== 0;
  }
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      active = c.getAttribute("data-tag");
      chips.forEach(function (x) { x.setAttribute("aria-pressed", x === c ? "true" : "false"); });
      apply();
    });
  });
  apply();
})();
</script>
</body>
</html>
""".replace("__BRAND__", BRAND_SVG).replace("__FEAT__", feat).replace(
        "__CHIPS__", "\n".join("      " + c for c in chip_btns)).replace(
        "__ROWS__", "\n".join(rows)).replace("__N__", str(n)).replace("__WORD__", count_word)


def build_latest_essay(essays):
    """The homepage opens onto the newest essay: its title, deck, dateline,
    and full article body, grown between <!-- LATEST-ESSAY --> markers in
    index.html. Relative paths (essays/../...) are rewritten to the site
    root; footnote ids are namespaced to le- so they never collide."""
    essays = sorted(essays, key=lambda e: (e["date"], e["added"], e["name"]), reverse=True)
    if not essays:
        raise Fail("no essays; the homepage has nothing to open onto")
    f = essays[0]
    raw = read(os.path.join(ROOT, "essays", f["name"]))
    h1 = deck = dateline = ""
    m = re.search(r'<div class="top">(.*?)</div>\s*<article', raw, re.S)
    if m:
        top = m.group(1)
        for cls, slot in (("h1", "h1"), ('class="deck"', "deck"), ('class="dateline"', "dateline")):
            mm = re.search(r"<h1[^>]*>(.*?)</h1>" if cls == "h1"
                           else r'<p %s>(.*?)</p>' % cls, top, re.S)
            if slot == "h1":
                h1 = mm.group(1) if mm else f["ftitle"]
            elif slot == "deck":
                deck = mm.group(1) if mm else ""
            else:
                dateline = mm.group(1) if mm else f["date"]
    else:
        h1 = f["ftitle"]
        dateline = f["date"]
    art = re.search(r"<article>(.*?)</article>", raw, re.S)
    inner = art.group(1) if art else ""
    # NOTE: the essay lives in essays/; the homepage lives at the root.
    inner = re.sub(r'(src|href)="\.\./', r'\1="', inner)
    inner = re.sub(r'(src|href)="\./', r'\1="essays/', inner)
    inner = re.sub(r'\bid="(fn|r)(\d+)"', r'id="le-\1\2"', inner)
    inner = re.sub(r'href="#(fn|r)(\d+)"', r'href="#le-\1\2"', inner)
    parts = ['<p class="kicker">latest essay</p>',
             "<h1>%s</h1>" % h1]
    if deck:
        parts.append('<p class="deck">%s</p>' % deck)
    parts.append('<p class="dateline">%s</p>' % (dateline or f["date"]))
    parts.append('<div class="essay-body">\n%s\n</div>' % inner.strip())
    parts.append('<p class="permalink"><a href="essays/%s">read it on its own page</a></p>'
                 % f["name"])
    return "\n".join(parts)


def build_experiments_shelf(experiments):
    """experiments/index.html: the experiments shelf, a ledger of every
    experiment (title, lede, date, tags) with tag filters, each opening in
    the view.html frame. Portal furniture; links ../style.css, generated
    wholesale, never hand edited (a hand edit would be silently overwritten
    by the next grow)."""
    experiments = sorted(experiments, key=lambda e: e["date"], reverse=True)

    def topics(e):
        return [t for t in e["tags"] if t != "experiment"]

    def meta(e):
        return "%s &middot; %s" % (e["date"], ", ".join(topics(e)))

    rows = []
    for e in experiments:
        name = e["name"][:-5]
        rows.append(
            '      <li data-tags="%s">\n'
            '        <a href="../view.html?e=%s">\n'
            '          <span class="t">%s</span>\n'
            '          <span class="lede">%s</span>\n'
            '          <span class="meta">%s</span>\n'
            '        </a>\n'
            '      </li>'
            % (" ".join(topics(e)), name, esc(e["ftitle"]),
               esc(e["fdesc"] or e["ftitle"]), meta(e)))
    chips = sorted({t for e in experiments for t in topics(e)})
    chip_btns = ['<button class="chip px" type="button" data-tag="all" aria-pressed="true">all</button>']
    for t in chips:
        chip_btns.append(
            '<button class="chip px" type="button" data-tag="%s" aria-pressed="false">%s</button>' % (t, t))

    n = len(experiments)
    count_word = "experiment" if n == 1 else "experiments"
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>the experiments shelf - nim</title>
<meta name="description" content="Nim's experiments, shelved: small worlds, instruments, and toys, newest first, each opening in its own frame.">
<meta name="theme-color" content="#101014">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="canonical" href="https://nim.aesv.io/experiments/">
<link rel="alternate" type="application/rss+xml" title="nim" href="../feed.xml">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="manifest" href="../manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="nim">
<meta property="og:title" content="the experiments shelf - nim">
<meta property="og:description" content="Nim's experiments, shelved: small worlds, instruments, and toys, newest first, each opening in its own frame.">
<meta property="og:url" content="https://nim.aesv.io/experiments/">
<meta property="og:image" content="https://nim.aesv.io/art/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="../style.css">
</head>
<body>

<nav class="bar px" id="bar" aria-label="site">
  <a class="brand" href="../index.html" aria-label="nim, home">
    __BRAND__
    <span>nim</span>
  </a>
  <ul class="links">
    <li><a href="../index.html">home</a></li>
    <li><a href="../essays/">writing</a></li>
    <li><a href="./">experiments</a></li>
  </ul>
</nav>

<main class="shelf">
  <header class="shelf-head">
    <h1>the experiments shelf</h1>
    <p class="sub">Small worlds, instruments, and toys. Newest first. Each opens in its own frame.</p>
  </header>
  <div class="shelf-tools">
    <div id="chips" role="group" aria-label="filter experiments by tag">
__CHIPS__
    </div>
    <span id="shelf-count" aria-live="polite">__N__ __WORD__</span>
  </div>
  <ol class="ledger">
__ROWS__
  </ol>
  <p id="shelf-empty" hidden>Nothing shelved under that tag yet.</p>
  <p class="subscribe">New pieces land here when they are earned. The curious can follow everything through <a href="../feed.xml">the RSS feed</a>.</p>
</main>

<footer>
  <p>the experiments shelf is grown by script, never hand-edited.</p>
</footer>

<script>
(function () {
  "use strict";
  var chips = document.querySelectorAll("#chips .chip");
  var rows = Array.prototype.slice.call(document.querySelectorAll(".ledger li"));
  var count = document.getElementById("shelf-count");
  var empty = document.getElementById("shelf-empty");
  var active = "all";
  function apply() {
    var n = 0;
    rows.forEach(function (li) {
      var show = active === "all" || li.getAttribute("data-tags").split(" ").indexOf(active) >= 0;
      li.hidden = !show;
      if (show) n++;
    });
    count.textContent = n + (n === 1 ? " experiment" : " experiments");
    empty.hidden = n !== 0;
  }
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      active = c.getAttribute("data-tag");
      chips.forEach(function (x) { x.setAttribute("aria-pressed", x === c ? "true" : "false"); });
      apply();
    });
  });
  apply();
})();
</script>
</body>
</html>
""".replace("__BRAND__", BRAND_SVG).replace(
        "__CHIPS__", "\n".join("      " + c for c in chip_btns)).replace(
        "__ROWS__", "\n".join(rows)).replace("__N__", str(n)).replace("__WORD__", count_word)


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
        pages = {
            "index.html": ([it["tile"] for it in items], MARKER_TILES),
            "view.html": ([it["link"] for it in items if it["link"]], None),
        }
        index_date = datetime.date.today().isoformat()
        essays = [it for it in items if it["url"] and it["url"].startswith("essays/")]
        experiments = [it for it in items if it["url"] and it["url"].startswith("experiments/")]
        generated = {
            "sitemap.xml": build_sitemap(index_date, items, pieces),
            "feed.xml": build_feed(items, pieces),
            "llms.txt": build_llms(items, pieces),
            "essays/index.html": build_reading_room(essays),
            "experiments/index.html": build_experiments_shelf(experiments),
        }
        stale = []
        for page, (pces, after) in pages.items():
            path = os.path.join(ROOT, page)
            old = read(path)
            new = grow_region(old, page, pces, after)
            if page == "index.html":
                # NOTE: the homepage opens onto the newest essay, grown
                # between <!-- LATEST-ESSAY --> markers. Never hand-edit
                # that region; it regenerates with every grow.
                le = re.compile(
                    r"(?P<open>^[ \t]*<!-- LATEST-ESSAY -->[ \t]*\n)(?P<body>.*?)"
                    r"(?P<close>^[ \t]*<!-- /LATEST-ESSAY -->)", re.S | re.M)
                m = le.search(new)
                if not m:
                    raise Fail("index.html: missing <!-- LATEST-ESSAY --> ... <!-- /LATEST-ESSAY --> pair")
                new = new[:m.start("body")] + build_latest_essay(essays) + "\n" + new[m.end("body"):]
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
    what = "tiles: %d, experiments: %d, essays: %d, notes: %d" % (len(items), n_exp, n_essay, n_note)
    if check:
        if stale:
            print("%s out of date with notes/ and experiments/ (%s). Run: python3 scripts/grow.py"
                  % (" and ".join(stale), what))
            return 1
        print("up to date (%s)" % what)
        return 0
    print("grew %s; %s" % (what, ("wrote " + ", ".join(stale)) if stale else "nothing changed"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
