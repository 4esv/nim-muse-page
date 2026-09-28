#!/usr/bin/env python3
"""review.py - quantitative writing review for Nim's pieces.

Usage: python3 scripts/review.py <file.md | file.html>

Extracts the prose (from a note's markdown body, or from <article> in an
experiment), then reports the quantifiable pieces of the story:

  words, sentences, paragraphs, sections, footnotes
  avg sentence length, stddev (rhythm), % short (<10w) / long (>30w) sentences
  longest sentence, crutch words, parenthetical asides, questions to reader
  banned phrases (house rules + his prose rules)

Exits 1 if a hard gate fails (em dash, exclamation mark, banned phrase).
Appends one JSON line per run to scripts/review-log.jsonl.

Python 3 standard library only.
"""
import datetime
import json
import math
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "scripts", "review-log.jsonl")

BANNED = [
    "passionate about", "driven by", "innovative", "leveraging",
    "it's worth noting", "in today's fast-paced world", "delve",
    "furthermore", "moreover", "in conclusion",
]
CRUTCH = ["very", "really", "just", "quite", "rather", "actually", "basically"]


class Article(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.chunks = []
        self.sections = 0
        self.footnotes = 0
        self.in_footnotes = 0
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article":
            self.depth += 1
        if self.depth:
            if tag in ("p", "h2") and "footnotes" not in (a.get("class") or ""):
                pass
            if tag == "h2" and "sec" in (a.get("class") or ""):
                self.sections += 1
            if tag == "div" and "footnotes" in (a.get("class") or ""):
                self.in_footnotes += 1
            if self.in_footnotes and tag == "p":
                self.footnotes += 1

    def handle_endtag(self, tag):
        if tag == "article" and self.depth:
            self.depth -= 1
        if tag == "div" and self.in_footnotes:
            self.in_footnotes -= 1

    def handle_data(self, data):
        if self.depth and not self.in_footnotes:
            self.chunks.append(data)


def text_of(path):
    raw = open(path, encoding="utf-8").read()
    if path.endswith(".html"):
        art = Article(raw)
        paras = [c for c in (" ".join(art.chunks)).split("\n") if c.strip()]
        return " ".join(paras), art.sections, art.footnotes, None
    lines = raw.lstrip("﻿").splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    title = re.sub(r"^#+\s*", "", lines.pop(0)).strip() if lines else ""
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.match(r"^tags:", lines[0], re.I):
        lines.pop(0)
    paras, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln.strip())
        elif cur:
            paras.append(" ".join(cur))
            cur = []
    if cur:
        paras.append(" ".join(cur))
    return " ".join(paras), 0, 0, title


def sentences_of(text):
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])", text)
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return out


def words_of(s):
    return re.findall(r"[A-Za-z0-9']+", s)


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: python3 scripts/review.py <file.md|file.html>\n")
        return 2
    path = argv[1]
    if not os.path.isfile(path):
        sys.stderr.write("review: no such file: %s\n" % path)
        return 2
    raw = open(path, encoding="utf-8").read()
    text, sections, footnotes, title = text_of(path)
    sents = sentences_of(text)
    lens = [len(words_of(s)) for s in sents]
    n = len(sents)
    words = sum(lens)
    avg = words / n if n else 0
    sd = math.sqrt(sum((l - avg) ** 2 for l in lens) / n) if n else 0
    short = sum(1 for l in lens if l < 10)
    long = sum(1 for l in lens if l > 30)
    longest = max(lens) if lens else 0
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    if path.endswith(".html"):
        # paragraphs counted from article parse instead
        paras = ["x"] * max(1, text.count("  ") // 40)
    asides = len(re.findall(r"\([^()]{4,}\)", text))
    questions = sum(1 for s in sents if s.rstrip().endswith("?"))
    low = text.lower()
    banned = [b for b in BANNED if b in low]
    # "leveraging" only banned as a verb; crude check: banned unless "leverage" appears as noun phrase
    crutch = {w: len(re.findall(r"\b%s\b" % w, low)) for w in CRUTCH}
    emdash = "—" in raw or "&mdash;" in raw or "&#8212;" in raw
    excl = text.count("!")
    hook = " ".join(words_of(" ".join(sents[:3]))[:60])

    hard = []
    if emdash:
        hard.append("em dash present")
    if excl:
        hard.append("%d exclamation mark(s)" % excl)
    if banned:
        hard.append("banned phrase(s): %s" % ", ".join(banned))

    print("review: %s" % os.path.relpath(path, ROOT))
    print("  words %d | sentences %d | sections %d | footnotes %d" % (words, n, sections, footnotes))
    print("  sentence length: avg %.1f, sd %.1f (rhythm), longest %d" % (avg, sd, longest))
    print("  short(<10w) %d%% | long(>30w) %d%%" % (round(100 * short / n) if n else 0,
                                                    round(100 * long / n) if n else 0))
    print("  asides %d | reader questions %d | crutch %s" % (
        asides, questions,
        ", ".join("%s:%d" % (w, c) for w, c in crutch.items() if c) or "none"))
    print("  gates: avg 14-22 %s | staccato >=15%% %s | banned %s" % (
        "ok" if 14 <= avg <= 22 else "MISS",
        "ok" if n and short / n >= 0.15 else "MISS",
        "clean" if not banned else "FAIL"))
    if hard:
        print("  HARD FAIL: %s" % "; ".join(hard))
    else:
        print("  hard gates pass")

    rec = {
        "date": datetime.date.today().isoformat(),
        "file": os.path.relpath(path, ROOT),
        "words": words, "sentences": n, "sections": sections,
        "footnotes": footnotes, "avg_sent": round(avg, 1), "sd_sent": round(sd, 1),
        "pct_short": round(100 * short / n, 1) if n else 0,
        "pct_long": round(100 * long / n, 1) if n else 0,
        "asides": asides, "questions": questions,
        "banned": banned, "hard_fail": hard,
    }
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    except OSError as e:
        sys.stderr.write("review: could not write log: %s\n" % e)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
