# art/build — how the office floor is made

The office view in `index.html` draws two things it does not contain: the floor, as
`art/office.webp` and `art/office-dark.webp`, and a layout object (`const L=`) holding the walk
grid, every seat and every destination on it. Both come out of here. Nothing in this folder
ships to the browser.

## The two states are two plates, not one plate and a filter

`OfficeLightOn.png` and `OfficeLightOff.png` are the same room drawn twice. The switch in the
office bar swaps between them. It is not a brightness filter, and could not be: the neon under
the desks and the glow off a monitor in a dark room are painted, and no filter invents them.

## Running it

In order, from this folder. Needs Python with Pillow.

```
python plates.py         # 1535 -> 1536 wide, then -> ../office.webp and ../office-dark.webp
python measure.py        # finds the chairs, the seats and the screens -> chairs.json
python grid6.py          # walk grid, seats, destinations -> office-layout.json
python apply-layout.py   # writes that into index.html's `const L=` line
```

A few seconds end to end and safe to re-run: the four are deterministic, so an unchanged
pipeline reproduces both plates and `index.html` byte for byte. Worth checking with
`git status` afterwards — if something shows modified when you only meant to change one number,
something upstream moved.

The character sheets in `art/cNN.png` are not built here. Their source is one file per developer
named after them, which is why it is gitignored and the shipped copies are numbered.

## What each step is actually doing

**`plates.py`** — the artwork arrives 1535px wide and the grid wants 1536, which is 192 whole
8px cells. One duplicated column at the right edge is the cheapest way there; resampling a crisp
illustration to gain a single pixel softens every line in it. It also keeps both plates
losslessly as `PLATE.png` and `DARK.png`, because the two steps after this key on exact colours
and webp moves them enough to punch holes in the middle of the room.

**`measure.py`** — finds the furniture. This used to be `plate5.py`, which *built* the empty
floor: strip the drawn-in people, rebuild each desk from its own clean columns, stamp a chair at
every desk. The artwork now arrives with the chairs on it and nobody sitting in them, so all of
that is gone and this measures instead. Chairs are found by their pink, then each rectangle is
pushed out to the outline round the seat and the castors under it — and the sideways test stays
inside the cushion's own rows, or the desk's dark front edge, which runs the full width of the
desk, swallows the chair whole. Feet go 21px below the top of the cushion, which is what leaves
a head, a collar and the shoulders clear of the backrest.

**`grid6.py`** — the walk grid, at 8px cells. A cell is walkable only when *every* pixel in it
is floor; the older ">=55% floor" rule let people walk over desks and counters.

**`apply-layout.py`** — one asserted edit that swaps the `const L=` line. Kept separate so the
grid can be rebuilt and inspected without touching the app.

## Traps

- **The floor is keyed off the lights-OFF plate.** Under daylight the desks and the ground they
  stand on are the same warm tan, near enough identical to the pixel, and no colour rule can
  separate them. With the lights out the floor goes dark and the wood stays lit.
- **8px cells, not 16.** The meeting room's doorway is about 25px wide, so at 16 the threshold
  never yielded a single all-floor cell and the room was sealed off — its carpet came out as two
  regions of its own and nobody could reach a seat. Halving the cell also stops so much open
  floor being lost to cells that merely clip the corner of a desk: 52% of the room is walkable
  at 8 against 34% at 16.
- **Anything measured in cells has to be checked when the cell size changes.** The radius
  `spotsNear` searches and the app's own last-step-onto-a-seat distance were both cell counts,
  and both silently halved. The first collapsed eleven places people stand and talk down to two.
- **`chairs.json` is the handover** from `measure.py` to `grid6.py`, and is tracked so the grid
  can be rebuilt on its own.
- **Don't eyeball a rectangle.** The one time the meeting chairs were typed in by eye they were
  ten pixels left of the real ones, and every backrest was drawn beside its occupant instead of
  round them.
