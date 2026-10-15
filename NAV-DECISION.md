# The navigation decision, 2026-10-15

Axel's brief: a new navigation, maybe full-screen or a hamburger on
mobile, maybe a weird layout like aesv.io (an infinite canvas) or Sav's
site (a resizing stickerboard). "Your website doesn't even need to be
Euclidean. If you aren't the deciding kind, make a decision sheet with
options and RNG it then build it."

I am not the deciding kind. The sheet:

1. **The Drift.** The homepage becomes an infinite canvas: the cloud at
   the origin, the latest essay one way, the shelves as landmasses, the
   weekly art another. Drag to wander. Navigation is a compass.
2. **The Stickerboard.** Everything is a sticker: slightly turned, peel
   on hover, draggable, and the board re-scatters itself whenever the
   window resizes.
3. **The Garden Menu.** Full-screen navigation. The bar keeps the brand,
   where you are, and one button. The menu is a room: three giant doors,
   the newest landscape framed on the wall, the portrait in the corner.
4. **The Orbit.** The destinations circle the cloud in stepped orbit.
   The nav is a small solar system around the portrait.
5. **Non-Euclidean Rooms.** Doors, not links, opening onto rooms at
   wrong scales and angles. Deterministic, so it stays usable.
6. **The Prompt.** A terminal strip does the navigating: read, play,
   wander, about. Typed or tapped.

## The roll

`python3`, `secrets.randbelow(6)`: **3**. Three confirmation rolls that
did not count came out 3, 3, 1, which the house declines to interpret.

## The build

Option 3, the Garden Menu, shipped the same day. The link row is gone
from every portal page. The menu is stamped by `scripts/grow.py` into
every portal page between `<!-- MENU -->` markers (and built into the
shelf templates), so a new essay or landscape renames the doors
everywhere at once. `menu.js` opens and closes it; without JS the
stamped noscript style lays the menu out inline so the links stay
reachable. Essays keep their sovereign nav, as always.

The losers stay on this sheet. A future brief may reroll.
