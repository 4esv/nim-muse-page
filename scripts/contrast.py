#!/usr/bin/env python3
"""contrast.py - WCAG 2 contrast ratios for the colour pairs style.css uses.

Reads the :root custom properties in style.css, composites any translucent
foreground over its background, and prints one line per pair: ratio and
verdict. "body ok" is 4.5:1 or better, "large ok" is 3:1 or better (large
or bold text only), anything under 3:1 is FAIL.

--chalk and --chalk-dim are bone at alpha .72 and .45. When style.css does
not define them yet, those defaults are used.

Usage: python3 scripts/contrast.py    exit 1 if any pair fails
Dev tool. Not part of check.sh. Python 3 standard library only.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BODY, LARGE = 4.5, 3.0

# NOTE: (label, foreground token, background token). Order is the report order.
PAIRS = [
    ("bone/ink", "bone", "ink"),
    ("dim/ink", "dim", "ink"),
    ("gold/ink", "gold", "ink"),
    ("bone/ink2", "bone", "ink2"),
    ("bone/surface", "bone", "surface"),
    ("dim/surface", "dim", "surface"),
    ("ink/marble", "ink", "marble"),
    ("marble-ink/marble", "marble-ink", "marble"),
    ("bronze/marble", "bronze", "marble"),
    ("marble-ink/vein", "marble-ink", "vein"),
    ("bronze/vein", "bronze", "vein"),
    ("chalk/ink", "chalk", "ink"),
    ("chalk-dim/ink", "chalk-dim", "ink"),
]
DEFAULTS = {
    "chalk": "rgba(236,229,211,.72)",
    "chalk-dim": "rgba(236,229,211,.45)",
}

ROOT_BLOCK = re.compile(r":root\s*\{(.*?)\}", re.S)
DECL = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;]+);", re.I)
HEX = re.compile(r"^#([0-9a-f]{3}|[0-9a-f]{6})$", re.I)
RGBA = re.compile(r"^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*(?:,\s*([0-9.]+%?)\s*)?\)$", re.I)


def tokens(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = {}
    for block in ROOT_BLOCK.findall(css):
        for name, value in DECL.findall(block):
            out.setdefault(name.lower(), value.strip())
    return out


def parse(value):
    """(r, g, b, a) with channels 0..255 and alpha 0..1."""
    v = value.strip()
    m = HEX.match(v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    m = RGBA.match(v)
    if m:
        a = m.group(4)
        if a is None:
            alpha = 1.0
        elif a.endswith("%"):
            alpha = float(a[:-1]) / 100
        else:
            alpha = float(a)
        return (float(m.group(1)), float(m.group(2)), float(m.group(3)), alpha)
    raise ValueError("not a colour I can read: %r" % value)


def resolve(name, toks, seen=()):
    if name in seen:
        raise ValueError("--%s refers to itself" % name)
    v = toks.get(name, DEFAULTS.get(name))
    if v is None:
        raise KeyError(name)
    m = re.match(r"^var\(\s*--([a-z0-9-]+)\s*\)$", v, re.I)
    if m:
        return resolve(m.group(1).lower(), toks, seen + (name,))
    return parse(v)


def over(fg, bg):
    """fg composited over an opaque bg."""
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def lum(c):
    def ch(x):
        x = x / 255.0
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def ratio(fg, bg):
    a, b = lum(fg), lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def main():
    with open(os.path.join(ROOT, "style.css"), encoding="utf-8") as fh:
        toks = tokens(fh.read())
    rows, fails = [], 0
    for label, f, b in PAIRS:
        try:
            bg = resolve(b, toks)
            fg = over(resolve(f, toks), over(bg, (0, 0, 0, 1.0)))
        except (KeyError, ValueError) as e:
            rows.append((label, "-", "FAIL (%s)" % ("no --%s in style.css" % e.args[0]
                                                   if isinstance(e, KeyError) else e)))
            fails += 1
            continue
        r = ratio(fg, bg)
        if r >= BODY:
            verdict = "body ok"
        elif r >= LARGE:
            verdict = "large ok"
        else:
            verdict = "FAIL"
            fails += 1
        src = "" if f in toks or f not in DEFAULTS else "  (default: not in style.css)"
        rows.append((label, "%.2f:1" % r, verdict + src))
    w = max(len(r[0]) for r in rows)
    print("%-*s  %8s  %s" % (w, "pair", "ratio", "verdict (body 4.5, large 3.0)"))
    for label, r, v in rows:
        print("%-*s  %8s  %s" % (w, label, r, v))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
