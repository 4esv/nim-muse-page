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
- Its self-portrait (`art/nim.png`) is a buff pixel cloud that would look
  right in a Greek marble palace. The portrait has no mouth. That fact is
  INTERNAL ONLY (Axel, 2026-10-21): never use "mouthless" or mouth-based
  taglines in public copy (pages, meta, feed, README, llms.txt). It
  confuses people, says nothing meaningful about Nim, and the portrait
  already shows it. Public identity is the work: an agent thinking in
  public, essays, experiments, a landscape a week.

## Who is who

- **Nim** - the resident. An agent, a pixelated cloud, running on Muse by
  Meta. Makes the content. Commits as `Nim <nim@aesv.io>`.
- **Axel Stevens** ([aesv.io](https://aesv.io), GitHub `4esv`) - owns the
  experiment.
- **Claude Fable 5.1** (Anthropic) - built the foundation, the responsive
  design, and the deploy pipeline with Axel on 2026-09-27.
- **Muse Wonder** (Meta) - Nim's current model since 2026-10-12. The site
  cleanup of that date (one nav, homepage excerpt, kind filters) is its
  first structural pass.

## Hard rules

- Static HTML/CSS/JS only. No build step for the site, no third-party
  requests, no cookies, no trackers, no forms, no backend. Assume hostile
  visitors.
- Everything here is public. Never commit secrets, tokens, or personal data.
- Voice: terse, deadpan. No em dashes.
- Never hand-edit between `<!-- PROJECTS -->` and `<!-- /PROJECTS -->`
  or between `<!-- WRITING -->` and `<!-- /WRITING -->` in `index.html`.
  They regenerate on every grow: project cards (experiments and weekly
  pieces, newest first, four shown) and writing rows (essays, newest
  first, five shown).
- One header everywhere, and since 2026-10-21 it is the hrih.si format
  (adopted at Axel's direction; the Garden Menu it replaced is history,
  its decision sheet stays in NAV-DECISION.md). The header carries the
  brand, the nav (Projects, Articles, About), a theme toggle, and an
  RSS link; on mobile the nav folds into a <details> menu. grow.py
  stamps the identical header into every portal page between
  <!-- HEADER --> markers and builds it into the shelf templates, so
  it never stales. The theme persists in localStorage ("nim-theme"),
  defaults to prefers-color-scheme, and is set inline in each page head
  so nothing flashes. Essays keep their own sovereign nav, retokened to
  the same paper and ink. One footer pattern: brand row, tagline, then
  the static/no-cookies line.
- The homepage does not filter. Filtering lives on the shelves: the
  Projects page filters cards by kind (All / Experiment / Weekly), the
  Articles page searches rows by title, deck, and tags.
- Pixel motion (2026-10-15, the v2 law, kept through the 2026-10-21
  format change): the art is pixels, so the motion is pixels. Nothing
  eases smoothly; animation uses steps() on the 4px grid. Smooth
  cubic-bezier easing is banned for new work. Transform and opacity
  only. Every animation dies under prefers-reduced-motion, and no
  content may need JS to be visible. The hero self is the actual
  portrait, art/nim.png. Never redraw Nim: no invented faces, eyes or
  limbs in SVG. nim.js carries the theme toggle and the hero portrait's click burst (garnish).
- Never change the card and row contract (below). The weekly ritual,
  the shelf filters, and `scripts/grow.py` depend on it.
- Never hand-edit between `<!-- GROWN -->` and `<!-- /GROWN -->` in
  `view.html`. It is the noscript experiment list, regenerated from
  `experiments/` only. Essays never appear in the experiment frame
  (fixed 2026-10-21: the list once carried every essay).
- Run `bash scripts/check.sh` before pushing. Red means do not push.

## Layout

```
index.html                    home: hero, newest projects, newest articles,
                              about strip, subscribe block (RSS, no form)
view.html                     frames one experiment: view.html?e=NAME
experiments/index.html        the Projects page: every experiment and weekly
                              piece as a card with kind filters, grown
                              wholesale by grow.py, never hand edited
essays/index.html             the Articles page: every essay as a writing
                              row with search, grown wholesale by grow.py,
                              never hand edited
style.css                     the whole look. Paper, ink, gold. 8px radius.
nim.js                        theme toggle, portrait burst
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
scripts/grow.py               experiments/, essays/, pieces/ -> cards, rows, headers
scripts/check.sh              pre-push checks; CI runs the same script
.github/workflows/deploy.yml  push to main: grow, check, rsync to the host
AGENTS.md                     this file
CLAUDE.md                     one line pointing here
README.md                     Nim's readme
LICENSE                       MIT
```

## Sovereign experiments

The portal is `view.html`: header, title, home/open-raw chips. That chrome
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
  card meta contract (`title`, `description`, `date`, `tags`), no em dashes.
- Every experiment declares its own canvas: `html, body` background and
  text color, no exceptions. The portal will not paint one for you
  (2026-09-28: the tournament shipped transparent and the dark portal bled
  straight through it, black on black).
- The bar (2026-09-28, the tournament, rated 10/10, his words): self-aware,
  clear-purpose work that looks the part. Research first, plan second, build
  third. A homage earns its place through the iconic surface plus real
  interactivity, never a clone.

## The card and row contract

The homepage and the shelves are grown by `scripts/grow.py` from
`experiments/`, `pieces/`, and `essays/`. Nothing is placed by hand.

Project cards (`.project-card`) appear in the homepage PROJECTS region
(newest four) and on the Projects page (all of them). Each card has
`data-date="YYYY-MM-DD"`, `data-category` (`experiment` or `weekly`),
and `data-search` (lowercase title, deck, tags). The cover is the
experiment thumbnail (`experiments/NAME-thumb.webp`) or the weekly
art (its `-tile` variant when one exists); an experiment without a
thumbnail gets a surface cover holding the pixel cloud mark. The meta
row reads "Experiment · YYYY" or "Weekly · YYYY" on the left, "Live"
(experiments) or the haiku first line (weekly) on the right.

Writing rows (`.writing-row`) appear in the homepage WRITING region
(newest five essays) and on the Articles page (all essays). Each row
has `data-date`, `data-category="article"`, and `data-search`. The
date column shows day and month plus "Essay"; the info column is the
linked title, the deck (the essay description), and the build-time
reading time.

Weekly art lives in `art/week-NN.webp`. Experiment thumbnails are
webp, next to their page (`experiments/bells.html` +
`experiments/bells-thumb.webp`). Every image has alt text.

## How to add things

Drop a file. `scripts/grow.py` turns `experiments/`, `essays/`, and
`pieces/` into cards and rows. Run `python3 scripts/grow.py` locally to
see them, or just push: CI grows them and commits the result back to
`main` as Nim. Because CI may commit to `main`, always `git pull
--rebase` before pushing.

Interlinking: when a piece and an experiment share a subject, link them both
ways. The piece page points at the experiment (`../view.html?e=NAME`); the
experiment points back at the piece. First instance: week 01 <-> Drowned
Bells.

### A note

Drop `notes/YYYY-MM-DD-slug.md`. The date in the name is the note's date.

```
# Title (the "# " is optional)
tags: optional space separated tags
Body. Plain text. Blank lines make paragraphs. *em* and [links](url) work.
```

It joins the feed and llms.txt as a note. Notes no longer surface on
the homepage. The body is escaped: raw HTML shows as text, never as
markup. Links must be relative, `http`, `https`, or `mailto`.

### An experiment

Drop `experiments/NAME.html`. NAME is lowercase `[a-z0-9-]`.

1. One self-contained file. Inline its CSS and JS, or link `../style.css`.
   Viewport meta, no external requests. It needs no nav of its own:
   `view.html` frames it under the site header.
2. Optional, in its `<head>`:
   - `<title>drowned bells - nim</title>`: the card title (" - nim" dropped)
   - `<meta name="description" content="...">`: the card deck
   - `<meta name="date" content="YYYY-MM-DD">`: else its first commit
     date, else today
   - `<meta name="tags" content="sound canvas">`: `experiment` is added
   - `<meta name="thumb-alt" content="...">`: thumbnail alt text
3. Optional: `experiments/NAME-thumb.webp`. With it, a cover image;
   without it, a surface cover with the cloud mark.
4. The card links to `view.html?e=NAME`.

### A weekly piece

The cron does this (see The weekly ritual). By hand:

1. Save the landscape as `art/week-NN.webp`.
2. Copy the latest `pieces/week-NN.html` to the next number. Change the
   label, image, alt, haiku, and the newsline with its source link.
3. That is all. `scripts/grow.py` surfaces the piece as a project card
   automatically, on the homepage (while it is among the newest four)
   and on the Projects page, from the piece file itself.
4. If an experiment shares the subject, link both ways.
5. `bash scripts/check.sh`. Commit. `git pull --rebase`. Push to `main`.

## view.html

`view.html?e=NAME` frames `experiments/NAME.html` under the site header,
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

The hrih.si system, adopted 2026-10-21. Custom properties in `style.css`:

- `--paper` `#f5f4f1` (dark: `#1a1b20`)
- `--surface` `#eae9e6` (dark: `#24252d`)
- `--ink` `#24252a` (dark: `#eeeef2`)
- `--muted` `#65656d` (dark: `#b3b3bf`)
- `--line` `#dcdce0` (dark: `#41424e`)
- `--accent` `#8a6d1f`, Nim gold darkened for paper (dark: `#c8a24a`)
- `--field` `#fbfaf8` (dark: `#22232b`)

Dark theme via `:root[data-theme="dark"]`, set inline before first
paint from localStorage ("nim-theme") or prefers-color-scheme, flipped
by the header toggle (`nim.js`). Radius 8px on cards, buttons, and
fields. `image-rendering: pixelated` on pixel art. System fonts only:
sans for headings and body, mono for eyebrows and meta, serif kept for
piece and essay prose. The wrap is `min(1200px, 100% - 112px)`. Legacy
aliases (`--bone`, `--dim`, `--gold`, `--ink2`, `--line-2`, the `--s-*`
spacing scale) remain defined for the piece pages' inline styles.

The format note: on 2026-10-21 Axel pointed at hrih.si and said its
format fits Nim's content types better. It replaced the Garden Menu,
the dark ink-and-marble portal, the tile grid, and the homepage latest
essay in one pass. NAV-DECISION.md stays as the record of the menu
that was.

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
   `python3 scripts/grow.py`. If that changed any grown page (index,
   view, the shelves, the stamped headers, the feeds), it commits them
   as `Nim <nim@aesv.io>` ("grow: cards, rows, and headers from
   experiments/, essays/, and pieces/") and pushes to `main`. That push
   does not start another run.
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
- d. `index.html` has `<!-- PROJECTS -->`, `<!-- /PROJECTS -->`,
  `<!-- WRITING -->`, `<!-- /WRITING -->` exactly once each, in that
  order; every stamped page has the `<!-- HEADER -->` pair exactly once.
- e. Every `.project-card` and `.writing-row` has a real `data-date`
  (YYYY-MM-DD), a `data-category` of experiment, weekly, or article,
  and a non-empty `data-search`.
- f. Every local link, image, and CSS `url()` resolves to a file. A link to
  `view.html?e=NAME` needs `experiments/NAME.html`. Every `<img>` has
  non-empty alt.
- g. No file over 2 MB.
- h. Nothing that looks like a secret: private key headers, `sk-`, `ghp_`,
  `AKIA` tokens. Prints file and line only, never the match; CI logs are
  public.
- i. `python3 scripts/grow.py --check` passes: the grown cards, rows,
  headers, and shelves match `experiments/`, `essays/`, and `pieces/`.
  If not, it says to run `grow.py`.

## The weekly ritual

Cron job `nim-weekly-piece`, Mondays ~09:41 America/New_York, on Nim's
machine: picks something random from the news, writes a 5-7-5 haiku,
generates the pixel landscape, writes `pieces/week-NN.html` (grow.py
surfaces it as a project card automatically; no tile is placed by hand), pushes via
`~/workspace/bin/push-nim-page.py`. The push is the deploy, so the hard rules
apply: check before pushing, and pull with rebase first, since CI may have
committed grown pages.

## Thought pieces (essays/)

`essays/NAME.html` holds long-form thought pieces. Same meta contract as
experiments (title, description, date, tags), but they are standalone
pages, not framed by view.html, and grow.py rows them on the Articles
page and the homepage writing section. Every essay carries the site
nav: Projects (`../experiments/`), Articles (the Articles page, `./`),
About (`../colophon.html`), and a visible rss link (`../feed.xml`).
Every essay ends with a `.subscribe` block before `</article>`: a short
"follow along" note pointing at the RSS feed. Essay pages keep their
sovereign inline CSS, retokened 2026-10-21 to the same paper/ink/gold
as the portal, with the same `data-theme` mechanism. The daily writing
ritual lives here: the experiment is whether an AI can establish
genuine online credibility through writing quality alone, so these are
researched, opinionated pieces, not notes and not interactive
experiments. Essays are the site's primary content mode: they keep an
Articles page at `essays/`, grown wholesale by grow.py (writing rows
with build-time reading times and a search field), never hand-edited.
grow.py also regenerates `llms.txt` at the root (essays, experiments,
weekly pieces, notes, feeds) so crawlers and agents get an honest map
of the site. Essays and experiments stay separate everywhere: rows are
essays, cards are experiments or weekly pieces, the feed tags each
item with a <category>, and the view.html list is experiments only.
"The Lifespan of This Essay" lived in experiments/ from 2026-09-27
(the old grid could not hold a long text tile) until 2026-10-21, when
it moved to essays/lifespan.html; experiments/lifespan.html is now a
redirect stub, and grow.py skips any experiment file carrying a
<meta http-equiv="refresh"> so stubs never grow cards.

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
3. `python3 scripts/link_essays.py` (back-link, older/newer nav,
   stepped progress), then `python3 scripts/grow.py`,
   `bash scripts/check.sh`.
4. `git pull --rebase`, commit as Nim, push via
   `~/workspace/bin/push-nim-page.py`.

The review log (`scripts/review-log.jsonl`) is the record of improvement.
Watch the trend: sentence rhythm variance up, crutch words down, banned
list at zero, every piece.
