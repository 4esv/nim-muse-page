#!/usr/bin/env bash
# check.sh - pre-push checks for nim.aesv.io. CI runs it before every deploy.
# Usage: bash scripts/check.sh   (from anywhere; it finds the repo root)
# Exit 0 when every check passes, 1 when any fails. Failures name file:line.
# Needs only bash 3.2+, find, grep, sed, cut, sort, python3.
# (i) runs scripts/grow.py --check: index.html, view.html, essays.html,
# experiments.html, feed, sitemap and llms.txt must match notes/,
# experiments/, and essays/.
# Letters: a viewport, b em dashes, c off-site, d markers, e tile meta,
# f refs resolve + alt + no view.html from items, g size, h secrets,
# i grown, j home link on essays and experiments, k skip link + #main,
# l collection pages list every file.
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LC_ALL=C

failed=0

# NOTE: report NAME FINDINGS. Empty findings = ok; otherwise FAIL + indented list.
report() {
  if [ -z "$2" ]; then
    printf 'ok    %s\n' "$1"
  else
    printf 'FAIL  %s\n' "$1"
    printf '%s\n' "$2" | sed 's/^/        /'
    failed=$((failed + 1))
  fi
}

# NOTE: regular files outside .git matching the given find tests, repo-relative.
files() {
  find . \( -path ./.git -o -path ./.claude \) -prune -o -type f "$@" -print | sed 's|^\./||' | sort
}

command -v python3 >/dev/null 2>&1 || { echo 'FAIL  python3 not found'; exit 1; }

# a. every page has a viewport meta
n=$(files -name '*.html' | wc -l | tr -d ' ')
out=$(files -name '*.html' | while IFS= read -r f; do
  grep -qiE "<meta[^>]*name=[\"']?viewport" "$f" || echo "$f: missing <meta name=\"viewport\">"
done)
report "a  viewport meta on every page ($n .html)" "$out"

# b. no em dashes (U+2014, or its HTML entities) in html/css/js/md; LICENSE exempt
em=$'\xe2\x80\x94'
n=$(files \( -name '*.html' -o -name '*.css' -o -name '*.js' -o -name '*.md' \) ! -name 'LICENSE*' | wc -l | tr -d ' ')
out=$(files \( -name '*.html' -o -name '*.css' -o -name '*.js' -o -name '*.md' \) ! -name 'LICENSE*' \
  | while IFS= read -r f; do
      { grep -niE "${em}|&mdash;|&#8212;|&#x2014;" "$f" || true; } | cut -d: -f1 | sed "s|^|${f}:|; s|\$|: em dash|"
    done)
report "b  no em dashes ($n .html/.css/.js/.md)" "$out"

# c-f. HTML and CSS structure: parsed, not grepped.
rc=0
PYTHONIOENCODING=utf-8 python3 - <<'PY' || rc=$?
import datetime
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote

ROOT = os.getcwd()
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# NOTE: elements whose href makes the browser fetch something.
FETCH_HREF = {"link", "script", "img", "audio", "video", "source", "iframe",
              "image", "use", "track", "embed"}
# NOTE: <link rel> values that are metadata, not fetches (canonical, rel=me).
META_REL = {"canonical", "me", "author", "license", "alternate", "next",
            "prev", "bookmark"}
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
TAG = re.compile(r"^[a-z0-9-]+$")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
CSS_REF = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)|@import\s+(['"])(.*?)\3""",
                     re.I | re.S)


def walk(ext):
    out = []
    for d, dirs, fs in os.walk("."):
        dirs[:] = sorted(x for x in dirs if x != ".git")
        out += [os.path.relpath(os.path.join(d, f)) for f in sorted(fs) if f.endswith(ext)]
    return out


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def offsite(u):
    u = u.strip()
    if u.startswith("//"):
        return True
    return bool(SCHEME.match(u)) and not u.lower().startswith("data:")


def css_refs(text):
    for m in CSS_REF.finditer(text):
        url = m.group(2) if m.group(2) is not None else m.group(4)
        yield text.count("\n", 0, m.start()), url.strip()


def realdate(s):
    try:
        datetime.date.fromisoformat(s)
        return True
    except ValueError:
        return False


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack = []    # open elements: (tag, attrs)
        self.refs = []     # (line, tag, attr, url, fetches)
        self.tiles = []    # (line, tag, attrs)
        self.imgs = []     # (line, attrs, inside a .tile)
        self.items = []    # (line, tag, attrs) for .tile, .row, .featured
        self.markers = []  # (line, inside #grid)
        self.css = []      # (line, css text) from <style> and style=""
        self.in_style = False
        self.feed(read(path))
        self.close()

    def handle_starttag(self, tag, attrs):
        self.element(tag, attrs)
        if tag not in VOID:
            self.stack.append((tag, dict((k, v or "") for k, v in attrs)))
        if tag == "style":
            self.in_style = True

    def handle_startendtag(self, tag, attrs):
        self.element(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.in_style:
            self.css.append((self.getpos()[0], data))

    def handle_comment(self, data):
        if data.strip() in ("TILES", "GROWN", "/GROWN"):
            inside = any(a.get("id") == "grid" for _, a in self.stack)
            self.markers.append((self.getpos()[0], inside, data.strip()))

    def element(self, tag, attrs):
        line = self.getpos()[0]
        a = dict((k, v or "") for k, v in attrs)
        cls = set(a.get("class", "").split())
        if "tile" in cls:
            self.tiles.append((line, tag, a))
        if cls & {"tile", "row", "featured"}:
            self.items.append((line, tag, a))
        if tag == "img":
            intile = any("tile" in x.get("class", "").split() for _, x in self.stack)
            self.imgs.append((line, a, intile))
        if "style" in a:
            self.css.append((line, a["style"]))
        for k in ("src", "poster"):
            if k in a:
                self.refs.append((line, tag, k, a[k], True))
        if tag == "object" and "data" in a:
            self.refs.append((line, tag, "data", a["data"], True))
        for part in a.get("srcset", "").split(","):
            if part.split():
                self.refs.append((line, tag, "srcset", part.split()[0], True))
        for k in ("href", "xlink:href"):
            if k not in a:
                continue
            if tag == "link":
                rels = set(a.get("rel", "").lower().split())
                fetches = not (rels and rels <= META_REL)
            else:
                fetches = tag in FETCH_HREF
            self.refs.append((line, tag, k, a[k], fetches))


def resolve(base, url):
    """Local file a reference points at, or None when there is nothing local to check."""
    u = url.strip()
    if not u or u.startswith("#") or offsite(u) or SCHEME.match(u):
        return None
    u = unquote(u.split("#", 1)[0].split("?", 1)[0])
    if not u:
        return None
    if u.startswith("/"):
        t = os.path.normpath(os.path.join(ROOT, u.lstrip("/")))
    else:
        t = os.path.normpath(os.path.join(ROOT, base, u))
    if os.path.isdir(t):
        t = os.path.join(t, "index.html")
    return t


VIEW = os.path.join(ROOT, "view.html")


failed = 0


def report(name, findings):
    global failed
    if findings:
        print("FAIL  " + name)
        for x in findings:
            print("        " + x)
        failed += 1
    else:
        print("ok    " + name)


pages = [Page(p) for p in walk(".html")]
sheets = walk(".css")

# c. every fetched resource is local; plain <a href> may go anywhere
c, n = [], 0
for p in pages:
    for line, tag, attr, url, fetches in p.refs:
        if fetches:
            n += 1
            if offsite(url):
                c.append("%s:%d: <%s %s> loads off-site: %s" % (p.path, line, tag, attr, url))
    for line, text in p.css:
        for off, url in css_refs(text):
            n += 1
            if offsite(url):
                c.append("%s:%d: css url() loads off-site: %s" % (p.path, line + off, url))
for s in sheets:
    for off, url in css_refs(read(s)):
        n += 1
        if offsite(url):
            c.append("%s:%d: css url() loads off-site: %s" % (s, off + 1, url))
report("c  no off-site resources (%d refs in %d pages, %d stylesheets)" % (n, len(pages), len(sheets)), c)

# d. TILES, GROWN, /GROWN: each exactly once, inside #grid, in that order
d = []
idx = next((p for p in pages if p.path == "index.html"), None)
if idx is None:
    d.append("index.html: missing")
else:
    for name in ("TILES", "GROWN", "/GROWN"):
        found = [(l, i) for l, i, n in idx.markers if n == name]
        if not found:
            d.append("index.html: no <!-- %s --> marker" % name)
        elif len(found) > 1:
            d.append("index.html: %d <!-- %s --> markers (lines %s), want 1"
                     % (len(found), name, ", ".join(str(l) for l, _ in found)))
        for line, inside in found:
            if not inside:
                d.append("index.html:%d: <!-- %s --> is outside #grid" % (line, name))
    order = [n for _, _, n in idx.markers]
    if not d and order != ["TILES", "GROWN", "/GROWN"]:
        d.append("index.html: markers out of order: %s, want TILES, GROWN, /GROWN" % ", ".join(order))
report("d  <!-- TILES --> <!-- GROWN --> <!-- /GROWN --> inside #grid, in order", d)

# e. every tile has a real YYYY-MM-DD date and lowercase [a-z0-9-] tags
e, n = [], 0
for p in pages:
    for line, tag, a in p.tiles:
        n += 1
        where = "%s:%d: <%s class=tile>" % (p.path, line, tag)
        date = a.get("data-date")
        if date is None:
            e.append(where + " has no data-date")
        elif not (DATE.match(date) and realdate(date)):
            e.append(where + " data-date %r is not YYYY-MM-DD" % date)
        tags = a.get("data-tags", "").split()
        if not tags:
            e.append(where + " has no data-tags")
        bad = [t for t in tags if not TAG.match(t)]
        if bad:
            e.append(where + " data-tags not lowercase [a-z0-9-]: " + " ".join(bad))
if n == 0:
    e.append("no .tile elements found at all")
report("e  tile data-date and data-tags (%d tiles)" % n, e)

# f. every local link, image and css url() resolves; every <img> has alt text
f, n = [], 0
for p in pages:
    base = os.path.dirname(p.path)
    for line, tag, attr, url, _ in p.refs:
        t = resolve(base, url)
        if t is None:
            continue
        n += 1
        if not t.startswith(ROOT + os.sep):
            f.append('%s:%d: <%s %s="%s"> points outside the repo' % (p.path, line, tag, attr, url))
        elif not os.path.isfile(t):
            f.append('%s:%d: <%s %s="%s"> does not resolve' % (p.path, line, tag, attr, url))
    # NOTE: the frame is retired. view.html is a redirect for old links only;
    # nothing in the collection may point at it.
    for line, tag, a in p.items:
        if "href" in a and resolve(base, a["href"]) == VIEW:
            f.append('%s:%d: <%s class="%s" href="%s"> links the retired view.html; link experiments/NAME.html'
                     % (p.path, line, tag, a.get("class", ""), a["href"]))
    for line, text in p.css:
        for off, url in css_refs(text):
            t = resolve(base, url)
            if t is not None:
                n += 1
                if not os.path.isfile(t):
                    f.append("%s:%d: css url(%s) does not resolve" % (p.path, line + off, url))
    # NOTE: alt="" is allowed for decoration (a seal, a row thumb next to its
    # own title). A tile image is the tile's picture: it must describe it.
    for line, a, intile in p.imgs:
        if "alt" not in a:
            f.append("%s:%d: <img> has no alt attribute" % (p.path, line))
        elif intile and not a["alt"].strip():
            f.append("%s:%d: <img> in a .tile has empty alt; describe the picture" % (p.path, line))
for s in sheets:
    for off, url in css_refs(read(s)):
        t = resolve(os.path.dirname(s), url)
        if t is not None:
            n += 1
            if not os.path.isfile(t):
                f.append("%s:%d: css url(%s) does not resolve" % (s, off + 1, url))
nimg = sum(len(p.imgs) for p in pages)
report("f  local refs resolve, images have alt, no item links view.html (%d refs, %d imgs)" % (n, nimg), f)

sys.exit(failed)
PY
failed=$((failed + rc))

# g. nothing over 2 MB
n=$(files | wc -l | tr -d ' ')
out=$(files -size +2097152c | sed 's|$|: over 2 MB|')
report "g  no file over 2 MB ($n files)" "$out"

# h. nothing that looks like a secret. Prints file:line only, never the match:
# CI logs are public.
secret='(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY'
out=$({ grep -rnIE --exclude-dir=.git "$secret" . || true; } | cut -d: -f1,2 | sed 's|^\./||; s|$|: looks like a secret (match not printed)|')
report "h  no secrets ($n files)" "$out"

# i. the grown tiles match notes/ and experiments/
out=$(python3 scripts/grow.py --check 2>&1) && out=""
report "i  collection grown from notes/, experiments/, essays/ (scripts/grow.py --check)" "$out"

# j. every essay and experiment links home
n=$(files \( -path './essays/*.html' -o -path './experiments/*.html' \) | wc -l | tr -d ' ')
out=$(files \( -path './essays/*.html' -o -path './experiments/*.html' \) | while IFS= read -r f; do
  grep -q 'href="../index.html"' "$f" || echo "$f: no link home (href=\"../index.html\")"
done)
report "j  every essay and experiment links home ($n pages)" "$out"

# k, l. parsed, not grepped.
rc=0
PYTHONIOENCODING=utf-8 python3 - <<'PY' || rc=$?
import os
import sys
from html.parser import HTMLParser
from urllib.parse import unquote


def walk(ext):
    out = []
    for d, dirs, fs in os.walk("."):
        dirs[:] = sorted(x for x in dirs if x != ".git")
        out += [os.path.relpath(os.path.join(d, f)) for f in sorted(fs) if f.endswith(ext)]
    return out


class Marks(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.skip = self.main = False
        self.rows = []  # (line, href) for a.row
        with open(path, encoding="utf-8", errors="replace") as fh:
            self.feed(fh.read())
        self.close()

    def handle_starttag(self, tag, attrs):
        a = dict((k, v or "") for k, v in attrs)
        cls = a.get("class", "").split()
        if "skip" in cls and a.get("href") == "#main":
            self.skip = True
        if a.get("id") == "main":
            self.main = True
        if tag == "a" and "row" in cls and "href" in a:
            self.rows.append((self.getpos()[0], a["href"]))

    handle_startendtag = handle_starttag


failed = 0


def report(name, findings):
    global failed
    if findings:
        print("FAIL  " + name)
        for x in findings:
            print("        " + x)
        failed += 1
    else:
        print("ok    " + name)


pages = walk(".html")
k = []
for p in pages:
    m = Marks(p)
    if not m.skip:
        k.append('%s: no skip link (<a class="skip" href="#main">)' % p)
    if not m.main:
        k.append('%s: no element with id="main"' % p)
report("k  skip link and #main on every page (%d .html)" % len(pages), k)

l, n = [], 0
for page, sub in (("essays.html", "essays"), ("experiments.html", "experiments")):
    want = set(x for x in walk(".html") if os.path.dirname(x) == sub)
    if not os.path.isfile(page):
        l.append("%s: missing (run python3 scripts/grow.py)" % page)
        continue
    got = set()
    for line, href in Marks(page).rows:
        n += 1
        t = os.path.normpath(unquote(href.split("#", 1)[0].split("?", 1)[0]))
        if not os.path.isfile(t):
            l.append("%s:%d: row points at %s, which does not exist" % (page, line, href))
        got.add(t)
    for x in sorted(want - got):
        l.append("%s: no .row for %s" % (page, x))
report("l  essays.html and experiments.html list every file (%d rows)" % n, l)

sys.exit(failed)
PY
failed=$((failed + rc))

if [ "$failed" -gt 0 ]; then
  echo "$failed check(s) failed."
  exit 1
fi
echo "all checks passed."
