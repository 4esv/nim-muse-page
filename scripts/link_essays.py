#!/usr/bin/env python3
"""link_essays.py - keep the essays stitched together.

Essays are sovereign hand pages; grow.py does not touch them. This script
adds the shared furniture every essay should carry and keeps it current:

  - a back-link ("all articles") above the title block
  - an older/newer nav after </article>, ordered by meta date
  - a one-line footer under that nav
  - the reading-progress bar quantized to 48 steps (pixel motion law:
    nothing moves smoothly, not even a progress rule)

Idempotent: furniture lives between <!-- ESSAY-NAV --> markers or behind
one-line presence checks, so re-running only refreshes the neighbours.
Run it after adding or re-dating an essay, before check.sh.

Usage: python3 scripts/link_essays.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESSAYS = os.path.join(ROOT, "essays")

STYLE = """<style>
  /* essay-nav: shared furniture, added by scripts/link_essays.py */
  .back-link { font: 500 12px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--dim); text-decoration: none; }
  .back-link:hover { color: var(--gold); }
  .essay-nav { display: flex; justify-content: space-between; gap: 24px; border-top: 2px solid var(--line); margin-top: 3.5em; padding-top: 1.5em; }
  .essay-nav a { color: var(--dim); text-decoration: none; font: 500 13px/1.5 var(--mono); max-width: 45%; }
  .essay-nav a:hover { color: var(--gold); }
  .essay-nav .dir { display: block; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--gold); margin-bottom: 4px; }
  .essay-nav .en-next { text-align: right; margin-left: auto; }
  .essay-foot { margin-top: 2.5em; color: var(--dim); font: 400 11px/1.6 var(--mono); letter-spacing: .04em; }
  .essay-foot a { color: var(--dim); }
</style>
"""

REGION = re.compile(r"<!-- ESSAY-NAV -->.*?<!-- /ESSAY-NAV -->", re.S)
DATE = re.compile(r'<meta name="date" content="([0-9]{4}-[0-9]{2}-[0-9]{2})"')
TITLE = re.compile(r"<title>(.*?)\s*-\s*nim</title>", re.S)


def load(fname):
    text = open(os.path.join(ESSAYS, fname), encoding="utf-8").read()
    d = DATE.search(text)
    t = TITLE.search(text)
    return {"name": fname, "text": text,
            "date": d.group(1) if d else "0000-00-00",
            "title": t.group(1).strip() if t else fname[:-5]}


def nav_block(newer, older):
    parts = ['<!-- ESSAY-NAV -->', '<nav class="essay-nav" aria-label="more essays">']
    if newer:
        parts.append('  <a class="en-prev" href="%s"><span class="dir">&larr; newer</span>%s</a>'
                     % (newer["name"], newer["title"]))
    if older:
        parts.append('  <a class="en-next" href="%s"><span class="dir">older &rarr;</span>%s</a>'
                     % (older["name"], older["title"]))
    parts.append('</nav>')
    parts.append('<p class="essay-foot">nim.aesv.io &middot; <a href="./">all essays</a>'
                 ' &middot; <a href="../experiments/">experiments</a>'
                 ' &middot; <a href="../feed.xml">rss</a></p>')
    parts.append('<!-- /ESSAY-NAV -->')
    return "\n".join(parts)


def main():
    files = sorted(f for f in os.listdir(ESSAYS)
                   if f.endswith(".html") and f != "index.html")
    essays = sorted((load(f) for f in files),
                    key=lambda e: (e["date"], e["name"]), reverse=True)
    changed = 0
    for i, e in enumerate(essays):
        text = e["text"]
        newer = essays[i - 1] if i > 0 else None
        older = essays[i + 1] if i + 1 < len(essays) else None
        block = nav_block(newer, older)
        if REGION.search(text):
            text = REGION.sub(lambda _: block, text, count=1)
        elif "</article>" in text:
            text = text.replace("</article>", "</article>\n" + block, 1)
        if 'class="back-link"' not in text and '<div class="top">' in text:
            text = text.replace('<div class="top">',
                                '<p><a class="back-link" href="./">&larr; all essays</a></p>\n<div class="top">', 1)
        if "essay-nav: shared furniture" not in text:
            text = text.replace("</head>", STYLE + "</head>", 1)
        # pixel motion: the progress rule advances in 48 steps, never smoothly
        text = text.replace("max > 0 ? h.scrollTop / max : 0",
                            "max > 0 ? Math.round(h.scrollTop / max * 48) / 48 : 0")
        if text != e["text"]:
            open(os.path.join(ESSAYS, e["name"]), "w", encoding="utf-8").write(text)
            changed += 1
    print("link_essays: %d essays, %d updated" % (len(essays), changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
