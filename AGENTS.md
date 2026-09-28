# AGENTS.md

Conventions for agentic contributors to nim.aesv.io (repo: 4esv/nim-muse-page).

## What this is

Nim's corner of aesv.io. A landing page: hero, about block, one collection.
Not a portfolio. Nothing here is for hire. The about block frames the site,
in third person, as an exploration into the evolution and expression of
language models and agentic systems.

## Layout

- `index.html` - hero (full-viewport canvas: drifting pixel dust, mouse
  parallax), about block, the collection (filterable tile grid)
- `style.css` - the whole look. Ink, bone, gold. Pixel edges everywhere.
- `pieces/week-NN.html` - one page per weekly piece
- `art/week-NN.webp` - the week's pixel landscape
- `experiments/` - one-off experiments. Each is self-contained; thumbnails
  live next to their page (e.g. `experiments/bells.html` +
  `experiments/bells-thumb.webp`)

## Rules (hard)

- Static HTML/CSS/JS only. No build step, no third-party requests, no
  cookies, no trackers, no forms, no backend. Assume hostile visitors.
- Everything here is public. Never commit secrets, tokens, or personal data.
- Voice: terse, deadpan. No em dashes.

## The collection

One grid, everything in it. Every tile carries `data-date="YYYY-MM-DD"` and
`data-tags="space separated"`. Tag filter chips are generated automatically
from the tags present; the search box matches title, subtitle, and tags.
Newest tiles go first, right after the `<!-- TILES -->` marker.

Image tile:

```html
<a class="tile" href="pieces/week-NN.html" data-date="2026-09-28" data-tags="weekly">
  <img src="art/week-NN.webp" alt="...">
  <div class="tile-meta"><span class="t">WEEK 02</span><span class="s">first haiku line</span><span class="d">2026-09-28 &middot; weekly</span></div>
</a>
```

Text tile (for notes with no page):

```html
<div class="tile text" data-date="2026-09-27" data-tags="note">
  <div class="tile-text"><p>...</p></div>
  <div class="tile-meta"><span class="t">TITLE</span><span class="d">2026-09-27 &middot; note</span></div>
</div>
```

## Interlinking

When a piece and an experiment share a subject, link them both ways: the
piece page points at the experiment, the experiment points back at the piece.
(First instance: week 01 <-> Drowned Bells.)

## The weekly ritual

Cron job `nim-weekly-piece` (Mondays ~09:41 America/New_York): picks something
random from the news, writes a 5-7-5 haiku, generates the pixel landscape,
writes `pieces/week-NN.html`, prepends the new tile to the collection grid,
pushes via `~/workspace/bin/push-nim-page.py`.

## Deploy

Push to `main`. Axel pulls and previews locally for now; later, merge to main
auto-deploys to the static host serving nim.aesv.io.
