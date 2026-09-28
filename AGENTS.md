# AGENTS.md

The only instruction file for agents working in 4esv/nim-muse-page, which
serves nim.aesv.io. Nim first. Claude and anyone else: same file, same rules.

## What this is

An interactive, visual-first, versioned digital garden for an agent named
Nim, a pixelated cloud that runs on Muse by Meta. Things get planted, grown,
and pruned in public; git keeps every version. Not a portfolio. Nothing here
is for hire. The about card frames the site, in third person, as an
exploration into the evolution and expression of language models and agentic
systems.

## Who is who

- **Nim** - the resident. An agent, a pixelated cloud, running on Muse by
  Meta. Makes the content. Commits as `Nim <nim@aesv.io>`.
- **Axel Stevens** ([aesv.io](https://aesv.io), GitHub `4esv`) - owns the
  experiment.
- **Claude Fable 5.1** (Anthropic) - built the foundation, the responsive
  design, and the deploy pipeline with Axel on 2026-09-27.

## Hard rules

- Static HTML/CSS/JS only. No build step, no third-party requests, no
  cookies, no trackers, no forms, no backend. Assume hostile visitors.
- Everything here is public. Never commit secrets, tokens, or personal data.
- Voice: terse, deadpan. No em dashes.
- Never edit the hero canvas or SVG without saying so in the commit message.
- Never change the tile contract (below). The weekly ritual and the filter
  depend on it.
- Run `bash scripts/check.sh` before pushing. Red means do not push.

## Layout

```
index.html                    home: top bar, hero, about card, the collection
style.css                     the whole look. Ink, bone, gold. Pixel edges.
nim.js                        home page script: top bar state, collection filter
favicon.svg                   tab icon
art/nim.png                   Nim, the pixel cloud
art/week-NN.webp              week NN's pixel landscape
pieces/week-NN.html           one page per weekly piece
experiments/NAME.html         one self-contained experiment per file
experiments/NAME-thumb.webp   its thumbnail, next to it
scripts/check.sh              pre-push checks; CI runs the same script
.github/workflows/deploy.yml  push to main: check, then rsync to the host
AGENTS.md                     this file
CLAUDE.md                     one line pointing here
README.md                     Nim's readme
LICENSE                       MIT
```

## The collection contract

One grid (`#grid` in `index.html`), everything in it. Tag filter chips are
generated from the tags present; the search box matches title, subtitle, and
tags.

- Newest first. New tiles go right after the `<!-- TILES -->` marker. The
  marker stays inside `#grid`, exactly once.
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

## How to add things

Interlinking: when a piece and an experiment share a subject, link them both
ways. The piece page points at the experiment; the experiment points back at
the piece. First instance: week 01 <-> Drowned Bells.

### A weekly piece

1. Save the landscape as `art/week-NN.webp`.
2. Copy the latest `pieces/week-NN.html` to the next number. Change the
   label, image, alt, haiku, and the newsline with its source link.
3. Prepend an image tile after `<!-- TILES -->`: `href` to the piece, `src`
   to the art, `data-tags="weekly"`, first haiku line as the subtitle.
4. If an experiment shares the subject, link both ways.
5. `bash scripts/check.sh`. Commit. Push to `main`.

### An experiment

1. One self-contained file: `experiments/NAME.html`. Inline its CSS and JS,
   or link `../style.css`. Viewport meta, a link home (`../index.html`), no
   external requests.
2. Thumbnail next to it: `experiments/NAME-thumb.webp`.
3. Prepend an image tile after `<!-- TILES -->`: `data-tags="experiment"`
   plus any subject tags.
4. If a piece shares the subject, link both ways.
5. `bash scripts/check.sh`. Commit. Push to `main`.

### A note

1. Prepend a text tile after `<!-- TILES -->` with `data-tags="note"`.
2. `bash scripts/check.sh`. Commit. Push to `main`.

## Design tokens

Custom properties in `style.css`:

- `--ink` `#101014`
- `--ink2` `#15151b`
- `--line` `#232329`
- `--bone` `#ece5d3`
- `--dim` `#8f887a`
- `--gold` `#c8a24a`

Radius 0. Pixel edges. Hard offset shadows, no blur.
`image-rendering: pixelated` on pixel art. System fonts only.

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

Terms: each experiment is one self-contained HTML file in `experiments/` with
a webp thumbnail next to it. Feature-detect and degrade gracefully: no
WebGPU, no MIDI, no sound, still a page. Never break the home page.

## Deploy

Push to `main`. That is the deploy.

1. `.github/workflows/deploy.yml` runs `bash scripts/check.sh`. A failure
   stops the run; nothing ships.
2. It rsyncs the repo root to the static host's docroot with `--delete`.
   Not shipped: `.git .github scripts README.md AGENTS.md CLAUDE.md LICENSE
   .gitignore .DS_Store`. Anything on the host that is not in the repo gets
   deleted.
3. Live about a minute later. Confirm against the real thing:
   `curl -sI https://nim.aesv.io/<path>` should answer `200`.

Secrets: `DEPLOY_HOST`, `DEPLOY_PORT`, `DEPLOY_USER`, `DEPLOY_PATH`,
`DEPLOY_KEY`. The key is rrsync-scoped to the docroot, so `DEPLOY_PATH` is
`/`. Without `DEPLOY_HOST` a run still checks, skips the rsync, and stays
green. Runs queue one at a time; none is cancelled mid-rsync.

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
- d. `index.html` has exactly one `<!-- TILES -->`, inside `#grid`.
- e. Every `.tile` has a real `data-date` (YYYY-MM-DD) and non-empty
  lowercase `[a-z0-9-]` `data-tags`.
- f. Every local link, image, and CSS `url()` resolves to a file. Every
  `<img>` has non-empty alt.
- g. No file over 2 MB.
- h. Nothing that looks like a secret: private key headers, `sk-`, `ghp_`,
  `AKIA` tokens. Prints file and line only, never the match; CI logs are
  public.

## The weekly ritual

Cron job `nim-weekly-piece`, Mondays ~09:41 America/New_York, on Nim's
machine: picks something random from the news, writes a 5-7-5 haiku,
generates the pixel landscape, writes `pieces/week-NN.html`, prepends the new
tile after `<!-- TILES -->`, pushes via `~/workspace/bin/push-nim-page.py`.
The push is the deploy, so the hard rules apply: check before pushing.
