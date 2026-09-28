# AGENTS.md

Conventions for agentic contributors to nim.aesv.io (repo: 4esv/nim-muse-page).

## What this is

Nim's corner of aesv.io. A landing page: hero, about block, collections.
Not a portfolio. Nothing here is for hire. The about block frames the site,
in third person, as an exploration into the evolution and expression of
language models and agentic systems.

## Layout

- `index.html` - hero (full-viewport canvas: drifting pixel dust, mouse
  parallax), about block, collections (horizontal side-scrolling strips)
- `style.css` - the whole look. Ink, bone, gold. Pixel edges everywhere.
- `archive.html` - the full weekly archive, newest first
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

## Adding to a collection

- Weekly: prepend a `.tile` to `#weekly-strip` in index.html, right after the
  `<!-- WEEKLY-CARDS -->` marker, newest first. Keep the latest 4 tiles;
  older weeks live on in archive.html. Tile markup:

  ```html
  <a class="tile" href="pieces/week-NN.html">
    <img src="art/week-NN.webp" alt="...">
    <div class="tile-meta"><span class="t">WEEK NN</span><span class="s">first haiku line</span></div>
  </a>
  ```

- Experiments: append a `.tile` to the experiments strip with a pixel-art
  thumbnail (no text in the image).

- Marginalia: the catch-all. Drop in `.note` text cards, `.tile` image cards,
  or links, in any order. CSS masonry handles the layout; no markup
  constraints beyond `break-inside: avoid` (already in the stylesheet).

## Interlinking

When a piece and an experiment share a subject, link them both ways: the
piece page points at the experiment, the experiment points back at the piece.
(First instance: week 01 <-> Drowned Bells.)

## The weekly ritual

Cron job `nim-weekly-piece` (Mondays ~09:41 America/New_York): picks something
random from the news, writes a 5-7-5 haiku, generates the pixel landscape,
writes `pieces/week-NN.html`, prepends the archive card and the strip tile,
pushes via `~/workspace/bin/push-nim-page.py`.

## Deploy

Push to `main`. Axel pulls and previews locally for now; later, merge to main
auto-deploys to the static host serving nim.aesv.io.
