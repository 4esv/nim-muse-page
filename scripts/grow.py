#!/usr/bin/env python3
"""grow.py - tiles from notes/ and experiments/ into the collection.

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

Writes only between <!-- GROWN --> and <!-- /GROWN -->: inside #grid in
index.html (tiles), and inside the <noscript> list in view.html (links).
Also regenerates sitemap.xml and feed.xml (RSS 2.0) at the repo root from
the same collection plus pieces/.
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
            "feed_link": SITE + "/" + href}


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


def main(argv):
    check = "--check" in argv[1:]
    unknown = [a for a in argv[1:] if a != "--check"]
    if unknown:
        sys.stderr.write("usage: python3 scripts/grow.py [--check]\n")
        return 2
    try:
        items = [load_experiment(f) for f in listdir("experiments", ".html")]
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
    n_exp = sum(1 for it in items if it["rank"] == 0)
    n_note = len(items) - n_exp
    what = "tiles: %d, experiments: %d, notes: %d" % (len(items), n_exp, n_note)
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
