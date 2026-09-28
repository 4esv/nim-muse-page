# WRITING.md

Nim's writing loop. Every piece gets reviewed before it ships, and the
numbers get logged so the writing measurably improves over time.

## The loop

1. Draft the piece.
2. Run `python3 scripts/review.py <file>` and read the report.
3. Qualitative pass: pacing, rhythm, arc (below).
4. Revise once. Re-run the analyzer. Log the numbers (the script appends
   to `scripts/review-log.jsonl` automatically).
5. `bash scripts/check.sh`. Commit. Push.

## Pacing

- The lede states the terms within the first 60 words. No throat-clearing.
- No paragraph over ~150 words in an essay, ~90 in a note. A long paragraph
  is a held breath; use it once per piece, on purpose.
- Alternate density: a heavy paragraph earns a light one after it.
- Sections should escalate, not accumulate. If two sections make the same
  point, cut one.

## Rhythm

- Vary sentence length on purpose. Target: average 14 to 22 words, with at
  least 15% of sentences under 10 words (the staccato) and none over 40
  unless it is doing real work.
- Parenthetical asides are seasoning, not structure. More than one per
  paragraph is a tic.
- Questions to the reader: at most two per piece. They are a spotlight;
  leave it on and it stops meaning anything.

## Arc

- Premise early (the lede), tension in the middle sections, release in the
  coda. The coda lands; it does not summarize.
- Every section earns its keep by changing what the reader knows or feels.
  If a section could be deleted without loss, delete it.
- Footnotes are for sourcing and for jokes that would break the sentence.
  Never for the actual argument.

## Voice gates (from the house rules and his prose rules)

- No em dashes. No exclamation marks. No hype.
- Never: "passionate about", "driven by", "innovative", "leveraging" as a
  verb, "it's worth noting", "in today's fast-paced world", "delve".
- Terse, deadpan, exact. Abstract over detail. The work is the argument.

## The log

`scripts/review-log.jsonl` holds one line per reviewed draft: date, file,
word count, sentence stats, and the gates. Watch the trend, not any single
piece. The goal is a visible upward slope in engagement metrics and a flat
zero on the banned list.
