# art/build — how the office floor is made

The office view in `index.html` draws two things it does not contain: `art/office.webp`, the
empty floor, and a layout object (`const L=`) holding the walk grid, every seat and every
destination on it. Both come out of here. Nothing in this folder ships to the browser.

## The source artwork is not in this repo

This repository is public, and the artwork is 1.9 MB besides. Two things have to be on the
machine before any of this runs, under the user's `Downloads`:

| what | where |
|---|---|
| the floor plan, with people and name plates still on it | `Downloads/DevOfficeFinal.png` |
| the prop sheet the manager's monitor comes from | `Downloads/OFficeSpriteswithCharacters/sprites/props/pc-back.png` |

Needs Python with Pillow. Everything else it reads, it made itself.

## Running it

In order, from this folder:

```
python chair.py          # cuts one meeting-room chair out of the artwork -> chair.png
python plate5.py         # builds the empty floor -> ../office.webp, PLATE.png, chairs.json
python grid6.py          # walk grid, seats, destinations -> office-layout.json
python apply-layout.py   # writes that into index.html's `const L=` line
```

It takes a few seconds end to end and is safe to re-run: the four together are deterministic,
so an unchanged pipeline reproduces `../office.webp` and `index.html` byte for byte. That is
worth checking with `git status` after a run — if either shows modified when you only meant to
change one number, something upstream moved.

## What each step is actually doing

**`chair.py`** — the desks in the artwork have no chairs. Rather than draw one, it keys one of
the meeting room's own chairs out of its background so the desks match the room they are in.
Keep the *bottom* row's chair, not the top: the occupant faces away from us, so the backrest
has to be the near side. The alpha key alone leaves the table's dark edge attached, so the
body's column span is measured on a clear row and everything outside it is cleared above.

**`plate5.py`** — removes the seated figures, the manager and the baked-on `DEV NN` labels, and
stamps a chair at every desk. There was never a hand-drawn empty plate: a desk is horizontally
uniform, so the per-row median of its own clean columns restores the wood, the plank lines and
the dark bottom border in one pass. The manager is a special case — he sits *behind* his desk,
so the generic patch box erases the desk itself.

**`grid6.py`** — the walk grid, at 16 px cells. A cell is walkable only when *every* pixel in it
is floor; the older ">=55% floor" rule let people walk over desks and counters. Chairs are
blocked by **area overlap >= 0.35** against the cell — colour detection blocks nothing (a chair
covering part of a cell still leaves it mostly floor) and centre-in-rect blocks too little,
because a 38 px chair straddles a 32 px grid. It also asserts that every seat and destination
has a walkable approach, and reports the ones whose nearest floor cell is suspiciously far.

**`apply-layout.py`** — one asserted edit that swaps the `const L=` line. Kept separate so the
grid can be rebuilt and inspected without touching the app.

## Traps

- **Don't feed `office.webp` to `grid6.py`.** It keys walkable cells off exact floor colours and
  webp's compression moves them enough to punch holes in the middle of the room. That is what
  `PLATE.png` is for, and why it is lossless.
- **`chairs.json` is the handover** from `plate5.py` to `grid6.py` — chair rectangles, seat
  positions and monitor rectangles. It is tracked so `grid6.py` can be re-run on its own.
- **The near side of the meeting table has to be measured, not eyeballed.** The first pass had
  those five chairs about ten pixels left of where they are, which put every redrawn backrest
  beside its occupant instead of round them.
