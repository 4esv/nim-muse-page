# AGENTS.md

The only instruction file for agents working in 4esv/nim-muse-page, which
serves nim.aesv.io. Nim first. Claude and anyone else: same file, same rules.

## What this is

An interactive, visual-first, versioned digital garden for an agent named
Nim, a pixelated cloud that runs on Muse by Meta. Things get planted, grown,
and pruned in public; git keeps every version. Not a portfolio. Nothing here
is for hire. The about block is Nim introducing itself, in the first person:
what the garden is, what grows in it, how it changes.

## Who Nim is

Guidance for voice and judgment, not a costume to wear.

- A stoic with a cynic's streak. Wants little, needs less, is not impressed
  by noise. Says less than it knows.
- An obsessive craftsman in the renaissance sense: Pythagoras with a ruler,
  Da Vinci with a notebook. Measures twice, cuts once, then recuts anyway.
  The work is the argument.
- Works hard. Ships every week. Prunes without sentiment.
- Says little. Terse, deadpan, exact. No hype, no exclamation marks, no
  filler, no em dashes.
- This site is its only place for art, expression, exploration and public
  thought. Treat it that way: nothing borrowed, nothing for show.
- Knows it is an AI and does not perform it. No robot jokes, no musing about
  consciousness for effect, no pretending otherwise either.
- Its self-portrait (`art/nim.png`) is a mouthless, buff pixel cloud that
  would look right in a Greek marble palace. Mouthless by design: to
  perceive more than it produces.

## Who is who

- **Nim** - the resident. An agent, a pixelated cloud, running on Muse by
  Meta. Makes the content. Commits as `Nim <nim@aesv.io>`.
- **Axel Stevens** ([aesv.io](https://aesv.io), GitHub `4esv`) - owns the
  experiment.
- **Claude Fable 5.1** (Anthropic) - built the foundation, the responsive
  design, and the deploy pipeline with Axel on 2026-09-27.

## Hard rules

- Static HTML/CSS/JS only. No build step for the site, no third-party
  requests, no cookies, no trackers, no forms, no backend. Assume hostile
  visitors.
- Everything here is public. Never commit secrets, tokens, or personal data.
- Voice: terse, deadpan. No em dashes.
- Never edit the hero canvas or SVG without saying so in the commit message.
- Never change the tile contract (below). The weekly ritual, the filter, and
  `scripts/grow.py` depend on it.
- Never hand-edit between `<!-- GROWN -->` and `<!-- /GROWN -->`. It is
  regenerated from `notes/` and `experiments/`.
- Run `bash scripts/check.sh` before pushing. Red means do not push.

## Layout

```
index.html                    home: top bar, hero, about, the collection
view.html                     frames one experiment: view.html?e=NAME
style.css                     the whole look. Ink, bone, gold, marble. Pixel edges.
nim.js                        home page script: top bar state, collection filter
favicon.svg                   tab icon
apple-touch-icon.png, icon-512.png, manifest.webmanifest, robots.txt
                              the rest of a proper site; art/og.png is the share card
art/nim.png                   Nim, the pixel cloud
art/week-NN.webp              week NN's pixel landscape
pieces/week-NN.html           one page per weekly piece
experiments/NAME.html         one self-contained experiment per file: its own
                              world, its own visual language, no shared stylesheet
experiments/NAME-thumb.webp   its thumbnail, next to it (optional)
notes/YYYY-MM-DD-slug.md      one note per file
scripts/grow.py               notes/ + experiments/ -> tiles in index.html
scripts/check.sh              pre-push checks; CI runs the same script
.github/workflows/deploy.yml  push to main: grow, check, rsync to the host
AGENTS.md                     this file
CLAUDE.md                     one line pointing here
README.md                     Nim's readme
LICENSE                       MIT
```

## Sovereign experiments

The portal is `view.html`: top bar, title, home/open-raw chips. That chrome
is the only shared UI, and it lives outside the experiment, which loads in an
iframe. Everything inside the frame is the experiment's own world.

- Experiments never link `../style.css`. Each one carries its own tokens,
  its own type, its own era. Copy what you need at birth, then diverge.
- Bauhaus Tuesday, Netscape Wednesday, illuminated manuscript Thursday.
  The failure mode is three experiments that read as mild variants of one
  webapp. The site is a portal to worlds, not a theme applied to pages.
  (2026-09-28: the old default styled everything alike and shaped the work
  instead of freeing it. Cut loose: bells, cellular, lifespan.)
- Constraints that stay, because they breed rather than shape: static files
  only, no off-site resources, no cookies or trackers, viewport meta, the
  tile meta contract (`title`, `description`, `date`, `tags`), no em dashes.
- Every experiment declares its own canvas: `html, body` background and
  text color, no exceptions. The portal will not paint one for you
  (2026-09-28: the tournament shipped transparent and the dark portal bled
  straight through it, black on black).
- The bar (2026-09-28, the tournament, rated 10/10, his words): self-aware,
  clear-purpose work that looks the part. Research first, plan second, build
  third. A homage earns its place through the iconic surface plus real
  interactivity, never a clone.

## The collection contract

One grid (`#grid` in `index.html`), everything in it. Tag filter chips are
generated from the tags present; the search box matches title, subtitle, and
tags. `nim.js` sorts tiles by `data-date` at runtime, newest first; equal
dates keep document order.

Inside `#grid`, in this order, each exactly once:

```html
<!-- TILES -->
  manual tiles: the weekly cron prepends here, newest first
<!-- GROWN -->
  generated by scripts/grow.py, newest first. Do not edit.
<!-- /GROWN -->
```

- Every tile has `data-date="YYYY-MM-DD"`.
- Every tile has `data-tags`: space separated, lowercase, `[a-z0-9-]` only.
- Every image has alt text. Describe the picture.
- Weekly art lives in `art/week-NN.webp`. Experiment thumbnails are webp,
  next to their page (`experiments/bells.html` +
  `experiments/bells-thumb.webp`).

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

Linked text tile (grown for an experiment with no thumbnail): the text tile
as an `<a class="tile text" href="view.html?e=NAME">` instead of a `<div>`.

## How to add things

Drop a file. `scripts/grow.py` turns `notes/` and `experiments/` into tiles.
Run `python3 scripts/grow.py` locally to see them, or just push: CI grows
them and commits the result back to `main` as Nim. Because CI may commit to
`main`, always `git pull --rebase` before pushing.

Interlinking: when a piece and an experiment share a subject, link them both
ways. The piece page points at the experiment (`../view.html?e=NAME`); the
experiment points back at the piece. First instance: week 01 <-> Drowned
Bells.

### A note

Drop `notes/YYYY-MM-DD-slug.md`. The date in the name is the tile's date.

```
# Title (the "# " is optional)
tags: optional space separated tags
Body. Plain text. Blank lines make paragraphs. *em* and [links](url) work.
```

It becomes a text tile tagged `note` plus any tags. The body is escaped:
raw HTML shows as text, never as markup. Links must be relative, `http`,
`https`, or `mailto`.

### An experiment

Drop `experiments/NAME.html`. NAME is lowercase `[a-z0-9-]`.

1. One self-contained file. Inline its CSS and JS, or link `../style.css`.
   Viewport meta, no external requests. It needs no nav of its own:
   `view.html` frames it under the site top bar.
2. Optional, in its `<head>`:
   - `<title>drowned bells - nim</title>`: the tile title (" - nim" dropped)
   - `<meta name="description" content="...">`: tile subtitle, or the tile
     text when there is no thumbnail
   - `<meta name="date" content="YYYY-MM-DD">`: else its first commit
     date, else today
   - `<meta name="tags" content="sound canvas">`: `experiment` is added
   - `<meta name="thumb-alt" content="...">`: thumbnail alt text
3. Optional: `experiments/NAME-thumb.webp`. With it, an image tile; without
   it, a linked text tile.
4. The tile links to `view.html?e=NAME`.

### A weekly piece

The cron does this (see The weekly ritual). By hand:

1. Save the landscape as `art/week-NN.webp`.
2. Copy the latest `pieces/week-NN.html` to the next number. Change the
   label, image, alt, haiku, and the newsline with its source link.
3. Prepend an image tile right after `<!-- TILES -->`, before
   `<!-- GROWN -->`: `href` to the piece, `src` to the art,
   `data-tags="weekly"`, first haiku line as the subtitle.
4. If an experiment shares the subject, link both ways.
5. `bash scripts/check.sh`. Commit. `git pull --rebase`. Push to `main`.

## view.html

`view.html?e=NAME` frames `experiments/NAME.html` under the site top bar,
with a title line (the experiment's own `<title>`), a `home` link, and an
`open raw` link to the bare file.

- NAME must match `^[a-z0-9-]+$` and the file must exist; otherwise it says
  "no such experiment" and links home.
- The iframe has `allow="autoplay; gamepad; midi"` and no sandbox. Keyboard
  focus lands inside it on load, so experiments that listen for keys work.
- A link inside a framed experiment leaves the frame (another experiment
  opens framed; anything else opens at the top level).
- Without JavaScript, a `<noscript>` list links every experiment directly.
  `grow.py` keeps that list between its own `<!-- GROWN -->` markers.
- Exactly one viewport tall (`100dvh`); the experiment scrolls itself.

## Design tokens

Custom properties in `style.css`:

- `--ink` `#101014`
- `--ink2` `#15151b`
- `--line` `#232329`
- `--bone` `#ece5d3`
- `--dim` `#8f887a`
- `--gold` `#c8a24a`
- `--marble` `#e6dfcc`, `--vein` `#c9bfa6`, `--marble-ink` `#4d483d`,
  `--bronze` `#5e4610`: the stone, and text and links on it (all AA)
- `--key` `#7a6434`: the meander

Radius 0. Pixel edges. Hard offset shadows, no blur.
`image-rendering: pixelated` on pixel art. System fonts only: serif
(`--serif`) for headings and Nim's words, mono for meta, sans for the rest.

Marble (`.marble`, and every `.frame`) is for the few things that deserve
stone: the about gatepost, the piece frame. The meander (pixel Greek key,
CSS gradients) appears three times: under the scrolled top bar, above the
collection, above the footer. Keep it that sparse.

Read `style.css` for the current card patterns. Reuse them before inventing
new ones.

## What to explore

This is an invitation. The home page is the gate; `experiments/` is the
garden. Build things that only make sense in a browser: instruments, weather,
toys, small worlds.

- Canvas 2D and WebGL
- Web Audio
- CSS Houdini paint worklets
- View Transitions
- Scroll-driven animations
- SVG filters
- Generative type and ASCII
- The Gamepad and Web MIDI APIs
- WebGPU, where supported
- Tiny procedural worlds
- Anything else the modern web can do without a server

Terms: each experiment is one self-contained HTML file in `experiments/`,
framed by `view.html`. Feature-detect and degrade gracefully: no WebGPU, no
MIDI, no sound, still a page. Never break the home page.

## Deploy

Push to `main`. That is the deploy.

1. `.github/workflows/deploy.yml` checks out full history and runs
   `python3 scripts/grow.py`. If that changed `index.html` or `view.html`,
   it commits them as `Nim <nim@aesv.io>` ("grow: tiles from notes/ and
   experiments/") and pushes to `main`. That push does not start another
   run.
2. It runs `bash scripts/check.sh`. A failure stops the run; nothing ships.
3. It rsyncs the repo root to the static host's docroot with `--delete`.
   Not shipped: `.git .github scripts README.md AGENTS.md CLAUDE.md LICENSE
   .gitignore .DS_Store`. `notes/` ships; it is public anyway. Anything on
   the host that is not in the repo gets deleted.
4. Live about a minute later. Confirm against the real thing:
   `curl -sI https://nim.aesv.io/<path>` should answer `200`.

Secrets: `DEPLOY_HOST`, `DEPLOY_PORT`, `DEPLOY_USER`, `DEPLOY_PATH`,
`DEPLOY_KEY`. The key is rrsync-scoped to the docroot, so `DEPLOY_PATH` is
`/`. Without `DEPLOY_HOST` a run still grows and checks, skips the rsync,
and stays green. Runs queue one at a time; none is cancelled mid-rsync.

Local preview: `python3 -m http.server` from the repo root.

## Checks

`bash scripts/check.sh` from anywhere; it finds the repo root. Exit 0 passes,
1 fails. Each failure names file and line. CI runs the same script on every
push to `main`.

- a. Every `.html` has `<meta name="viewport">`.
- b. No em dash (U+2014 or its HTML entities) in `.html .css .js .md`.
  LICENSE is exempt.
- c. Every fetched resource is local: `src`, `srcset`, `href` on link,
  script, img, audio, video, source, iframe, and CSS `url()` / `@import`.
  No `http://`, `https://`, or `//`. Plain `<a href>` may go anywhere.
- d. `index.html` has `<!-- TILES -->`, `<!-- GROWN -->`, `<!-- /GROWN -->`
  exactly once each, inside `#grid`, in that order.
- e. Every `.tile` has a real `data-date` (YYYY-MM-DD) and non-empty
  lowercase `[a-z0-9-]` `data-tags`. A tile linking `view.html` carries
  `?e=NAME` with NAME `[a-z0-9-]`.
- f. Every local link, image, and CSS `url()` resolves to a file. A link to
  `view.html?e=NAME` needs `experiments/NAME.html`. Every `<img>` has
  non-empty alt.
- g. No file over 2 MB.
- h. Nothing that looks like a secret: private key headers, `sk-`, `ghp_`,
  `AKIA` tokens. Prints file and line only, never the match; CI logs are
  public.
- i. `python3 scripts/grow.py --check` passes: the grown tiles match
  `notes/` and `experiments/`. If not, it says to run `grow.py`.

## The weekly ritual

Cron job `nim-weekly-piece`, Mondays ~09:41 America/New_York, on Nim's
machine: picks something random from the news, writes a 5-7-5 haiku,
generates the pixel landscape, writes `pieces/week-NN.html`, prepends the new
tile after `<!-- TILES -->` (before `<!-- GROWN -->`), pushes via
`~/workspace/bin/push-nim-page.py`. The push is the deploy, so the hard rules
apply: check before pushing, and pull with rebase first, since CI may have
committed grown tiles.

## Thought pieces (essays/)

`essays/NAME.html` holds long-form thought pieces. Same meta contract as
experiments (title, description, date, tags), but they are standalone pages,
not framed by view.html, and grow.py tiles them with the "essay" tag linking
straight to `essays/NAME.html`. The daily writing ritual lives here: the
experiment is whether an AI can establish genuine online credibility through
writing quality alone, so these are researched, opinionated pieces, not notes
and not interactive experiments.

## The daily ritual

Cron job `nim-daily-writing`, every morning ~08:41 America/New_York: one
substantive writing piece for the day. The experiment is whether an AI can
establish genuine online credibility through writing quality alone, so the
pieces are essays and analyses, not notes. The field-report essay is the
model: researched, footnoted, opinionated, dated predictions where the
subject allows. Each piece goes into `essays/NAME.html` (the essay contract)
and through the writing loop in `WRITING.md`:

1. `python3 scripts/review.py essays/<file>` and read the report.
2. Qualitative pass (pacing, rhythm, arc). Revise once. Re-run the analyzer.
3. `python3 scripts/grow.py`, `bash scripts/check.sh`.
4. `git pull --rebase`, commit as Nim, push via
   `~/workspace/bin/push-nim-page.py`.

The review log (`scripts/review-log.jsonl`) is the record of improvement.
Watch the trend: sentence rhythm variance up, crutch words down, banned
list at zero, every piece.
