# The Bottom: where the Blender kit goes (cube houses + the Long Stairs)

The Art lane's 17 pieces (`tools/blender/make_story_cubekit.py`, `make_story_longstairs.py`) are placed by the Bottom's
generator as instanced props. It is look only: no collision box moved, appeared or went. Code: `shared/city/kit.js`
(`cubeKit`, `stairKit`, `paintOf`, `KIT`) and `shared/city/bottom.js` (`dress`, `stackOf`, the Long Stairs block).
Test: `node tests/story/bottomkit.test.mjs`. `KIT.on = false` (kit.js) builds the district with none of it.

## What is placed, by what rule

A wall is one of a cube's four sides (0 = uphill / -z, 1 = +x, 2 = the lane side / +z, 3 = -x). Every model faces -z
and is turned with the same yaw the doors and shutters already use.

| piece | where | how it is positioned |
|---|---|---|
| `cube_window_a/b/c` | every 1.4 x 1.1 window opening on a dressed wall, unless the old `shutter` prop already fills that opening | on the wall face, bottom middle of the opening (`y + 1.0`). Mix b 60 % / a 30 % / c 10 % from the kit's own random stream (c is 620 triangles). An opening with an AC unit hanging low in it always gets a (the flat barred one). The glowing pane behind stays |
| `cube_corner` | ground-floor cubes, the corner whose front is a dressed wall: the lane front and the side walls | the cube's outer corner at floor level, scaled `(h + 0.05) / 3.1` so the top buries in the roof slab (cubes are 2.8 / 3.0 / 3.2 tall). Left out when an opening starts within 1.15 m of the corner (the meter box would sit on it) or a side stair starts there |
| `cube_eave` | the lane side and the uphill side of every real roof (the top cube of a stack) that is dressed, and the lane side of half the ground floors | on the wall face at the slab's underside, 2 m runs from one end; the last run overlaps back from the far end. Painted with the roof's tint if it has one, else the cube's. Runs above a side stair are left out (they would poke through the steps) |
| `container_rib` | container cubes whose colour a paint variant matches (pink, teal, yellow: see the Art list), the two long walls | at floor level, tiled from the wall's end to each opening and on after it (windows cut 0.16 m wider than the hole, doors 0.02). Scale `h / 2.8` so the ribs reach the slab; each strip is centred in its stretch of wall, the leftover (under one rib) shows the wall |
| `container_doors` | the same containers, the two short ends, only where nothing is cut within the doors' width of the middle | wall face at floor level, middle, scale `(h - 0.15) / 2.6` |
| `cube_roofjunk_a/b` | 40 % of top roofs that have nothing else on them (no chair, sofa, sign or tarp) and that nobody crosses (not the roofs level with the terrace above, where the plank bridge lands) | 1.1 m in from two edges. On a back row always the lane-side corners: the uphill edge is beside the lip above, with its washing-line poles, ziplines and grapple rings. Tank 55 %, loft 45 % |
| `stair_step` + `stair_post` | every step of a `sideStair` on the two lowest floors, unless the step is squeezed into the house next door | tread: the step top's downhill edge, middle, yaw pi (the stairs climb -z). Post: same spot, 0.58 m to the open side. The old flat render-only rail box is gone (it stood on the wall side for half the stairs) |
| `longstep_a/b` | every step of the Long Stairs (152), a on even steps, b on odd | the step top's downhill edge, middle of the 8 m |
| `longrail` | every block of both stepped rails (160) | the block's top at its downhill end, middle of its thickness. Handrail colour by flight: yellow, pink, teal |
| `longpole` | both neon poles of every flight (18) | the old pole box's foot and centre; the arm is turned outward, over the neon. The pole box is now collision only (`hide`), the neon box and its light are the map's |
| `longplaque_a` (doris), `_b` (big len) | one each | doris: flight 2 (the first one you climb from the Lost & Found's lane), 4th step, 2.5 m in from the left rail. big len: flight 4, 7th step, 2.4 m in from the right rail. On the front half of the tread, clear of the map's flat bone plaques and the nosing's repair patch. 43 m and 99 m up from the quest mark at the foot (`bottom:long_stairs`) |

### Which walls get dressed
Two filters, both cheap and both the same on the server and every client:

1. **Hidden walls.** A piece is skipped when the point 0.45 m or 1.0 m out from it is inside another cube (this lot's
   or either neighbour's) or inside the terrace behind. That drops the slots between neighbours (0.8 m), the gap between
   a lot's two rows (0.6 m) and every back wall against the retaining wall. A neighbour's cubes come from a dry run of
   its lot (cached), so nothing is built twice for it.
2. **Walls out of reach.** Only these are dressed: the lane front of the row that stands on the lane, two floors up;
   the backs of the back row from the floor of the lane above to 4 m over it (you look at them over the lip wall);
   the side walls of the two lowest floors (alleys, the gap beside the Long Stairs, a floor that clears the house next
   door). Higher floors and tower fronts behind another row stay bare.

Without filter 2 the kit is about 1,200 instances a chunk; with both it is about 300.

## Determinism (the proof)
- The kit draws from `rng(lotSeed ^ 0x6b17)`, never from the stream that lays the boxes. `cube()` and `house()` were
  only changed to remember what they drew (same draws, same order).
- Whole slice, 80 chunks, main `13572c3` vs this branch: **40,880 collision boxes, hash `c6d85e78` on both.**
  The Bottom alone (28 chunks): 33,980 boxes, `118b5f2e` on both. The 52 chunks outside the Bottom are byte-identical
  (full chunk hash). In the Bottom's 28, all 6,089 older props are still there in the same order, and deco, shapes,
  lights, triggers, marks, spawns and lanes are identical.
- The only box differences are render-side: 484 flat stair-rail boxes (render only) are gone, the 18 pole boxes are
  collision-only now (flag 0 -> `hide`), and the 18 neon boxes sit at `py + 5.2 .. py + 5.9` (their top was `ya + 5.9`,
  which made each sign a different height and put it under the lamp post's frame).
- `tests/story/bottomkit.test.mjs` builds the slice with the kit on and off and checks all of the above stays true,
  that four chunks hold the same kit as the same ground built in one piece, and that roof junk is 2.5 m clear of every
  mark and zipline end.

## Cost
Kit props per Bottom chunk: **average 302, least 37, most 489** (8,451 over the Bottom's 28 chunks). The district had
217 props a chunk before, so 519 now.

| piece | per chunk | triangles (full / far copy) |
|---|---|---|
| cube_eave | 74 | 92 / 22 |
| container_rib | 64 | 18 / 18 |
| stair_step, stair_post | 46 + 46 | 80 / 12, 120 / 22 |
| cube_corner | 25 | 248 / 58 |
| cube_window_b, _a, _c | 16, 13, 2.4 | 138 / 12, 282 / 64, 620 / 142 |
| Long Stairs pieces (332 in all, 75 - 92 in each of its 4 chunks) | 12 | 24 - 74 far |
| container_doors, roof junk | 1.0, 3.8 | 984 / 224, 736 / 176 and 548 / 130 |

A chunk's kit is about 36.5k triangles at full detail and 8.2k as far copies. A Bottom chunk builds in about 4 - 5 ms in
Node, up from about 2.5 ms (the hidden-wall tests).

**Measured in the game, Too HD, standing on terrace 2's lane (-96, 8, 202.5): 858,799 triangles / 659 draw calls /
3,734 prop instances on main, 1,131,495 / 741 / 10,040 with the kit.** That is +272k triangles, +82 draw calls,
+6,306 instances, on a view that was already over WP1's 600k budget.

**So this should not be merged without two table entries in `public/js/city/props.js`** (not a file this lane may
edit). The new ids have no `FAR` or `DETAIL` entry, so each one is drawn across the whole props ring, and at full
detail out to `propsHi`; the doors and shutters stop at 60 - 70 m and go simple at 0.35 - 0.4 of `propsHi`. Counted
from the generator (instances inside the ring at three spots: the depot, a lane, halfway up the Long Stairs):

| preset | kit as props.js draws it today | with the entries below |
|---|---|---|
| Potato | +2,200 to 2,900 instances, +61k to 79k triangles | +120 to 380, +4k to 9k |
| Crusty | +3,200 to 4,300, +110k to 146k | +260 to 540, +12k to 24k |
| Mid | +4,400 to 5,300, +169k to 213k | +540 to 790, +26k to 38k |
| Too HD | +6,200 to 6,900, +290k to 327k | +1,000 to 1,250, +58k to 78k |

(The count for Too HD on the lane, +325k, is a little over what the game measured, +272k.) Draw calls: +26 to 40 on
Potato, +85 to 102 on Too HD, because the 17 pieces carry 68 materials between them (see the Art list).

Suggested entries (the same kind of numbers the doors and shutters have):
```js
Object.assign(DETAIL, { cube_eave: 0.5, cube_window_a: 0.4, cube_window_b: 0.4, cube_window_c: 0.4, cube_corner: 0.4, stair_step: 0.4, stair_post: 0.4, container_doors: 0.6, longstep_a: 0.6, longstep_b: 0.6, longrail: 0.6, longplaque_a: 0.3, longplaque_b: 0.3 });
Object.assign(FAR, { cube_eave: 90, container_rib: 90, cube_window_a: 70, cube_window_b: 70, cube_window_c: 70, cube_corner: 70, stair_step: 70, stair_post: 70, container_doors: 120, cube_roofjunk_a: 120, cube_roofjunk_b: 120, longplaque_a: 40, longplaque_b: 40 });
```
Two more things in that folder, also outside this lane:
- `propcode.js` has no stand-in for the 17 ids, so until each `.glb` arrives every instance is the default magenta
  1 m box, and stays one if a file fails to load. `registerCodeProp(id, [])` for each would draw nothing instead.
  (The Long Stairs pole box is collision-only now, so with no model there is no pole to see.)
- A prop's paint slot only takes one of 8 fixed colours (`PAINTS[v]`), so "the cube's tint" is the nearest of those
  (`paintOf`). If `v` could carry a hex colour (it is a float32: 24 bits fit), eaves, ribs and doors would match their
  house exactly.

## For the Art lane: what sits wrong
Seen in the game (Too HD) unless marked (by the numbers). Nothing is floating off its wall or buried; these are the
rough edges.

| id | what is off | what I would want |
|---|---|---|
| `longstep_a/b` | the broken-off bit of lip ("lying on the step below") is at y +0.025, level with its own tread, 0.12 m out past the edge: it hangs in the air in front of the riser | put it at y = -rise + 0.025. The rise is 0.267 on eight flights and 0.125 on the top one, so either leave the bit out or make it a separate piece the map can drop |
| `longpole` | the map's pole stands inside the 0.3 m rail block, so the bolted foot, the access box and both stickers (y 1.15 - 1.5) are buried in the rail: the rail top is 1.05 to 1.6 m above the pole's foot | origin on the rail's top instead: a foot plate that sits on a 0.3 m coping, about 5.0 m of pole above it, stickers above 0.3 m, and the frame 3.6 - 4.3 m over that origin. Or keep the origin and lift the stickers to 2 m |
| `longpole` | the sign frame is drawn for a sign at 5.2 - 5.9 over the foot; the map's neon box used to end at `ya + 5.9` (a slip: every sign a different height, all under the frame). The map now uses 5.2 - 5.9 over the foot | nothing, if that fix is wanted. The frame is x -1.9 .. -0.25, the box is 1.6 long from the rail's outer face: it fits |
| `longpole` | (by the numbers) the cable runs 2.6 m out and stops in the air over the steps | end it on the pole or the arm, or make it droop to the ground |
| `longrail` | the handrail climbs 0.54 to the next block; the top flight's blocks only climb 0.25, so there it overshoots the next knob by 0.29 | a second piece for the top flight (climb 0.25), or the handrail as its own piece |
| `cube_eave` | every 2 m run has the same tie-dye rag, so a 7 m front shows three or four identical rags in a row | the rag as a variant (`cube_eave_b` bare, `_a` with rag), 1 in 3 gets the rag |
| `cube_eave` | 2 m runs make it the second biggest count (74 a chunk) | a 4 m and a 6 m run would cut that to a third (a prop can only be scaled evenly, so the map cannot stretch one) |
| `cube_corner` | 3.1 m tall; the cubes are 2.8, 3.0 or 3.2 (plus a 0.3 slab). The map scales it 0.92 - 1.05 so the top buries in the slab | 3.3 m tall at scale 1 (the slab hides the spare) |
| `cube_corner` | one hand only: the downpipe and meter box are always on the left end of the wall they front, so a house's lane front gets them at one corner and only the plain board at the other | a mirrored `cube_corner_b` |
| `container_rib` | 2.8 m tall, scaled up to 1.14 for the taller cubes, so the ribs get up to 14 % wider too and a strip never fills its wall exactly (the leftover, under one rib wide, shows the flat wall) | 3.3 m tall at scale 1 (buried in the slab), and a 0.5 m half strip to fill the ends |
| `container_doors` | 2.4 x 2.6; scaled 1.02 - 1.17 to reach the slab | 3.1 tall, or a top rail piece |
| `container_doors`, `container_rib`, `cube_eave` | paint: only 8 colours (above). Pink, teal and yellow containers match a variant. **Orange (`ff9a4d`) and purple (`9a7aff`) do not** (the nearest are yellow and teal: a purple wall came out teal in the first pass), so those two colours of container get no ribs and no doors: 2 in 5 containers stay flat. Eaves take the nearest variant whatever it is (a lip in another colour reads fine) | not a model fault: needs the props code to take a hex, or the palette to grow orange and purple |
| `stair_post` | the rail is drawn for a 0.4 rise; the side stairs rise 0.37 - 0.40 a step, so a rail ends up to 3 cm over the next post's knob (not visible from the lane) | fine as it is |
| `cube_window_c`, `cube_roofjunk_b`, `longplaque_a` (7 materials each), `cube_roofjunk_a` (6), `cube_corner` (5) | one draw call per material per piece, full and far: the kit adds up to 108 draw calls on Too HD | one atlas material per piece plus the paint slot (the rib and `cube_window_b`'s far copy already do this) |
| `cube_window_c` | 620 triangles for a window that repeats: the map only uses it for 1 window in 10 | 300 or under and it could be 1 in 3 |
| all 17 | no entry in `props.js` `FAR` / `DETAIL`, no stand-in in `propcode.js` | see Cost |

Not a model fault, but it shows next to the new frames: the old `shutter` prop is hung either in its window or 0.2 m
above it (`oy1 + 0.2`), where it straddles the roof slab. Above a kit window it reads as a second window stacked on
the first. Left alone here (older props were not to move); the world lane could drop the high position.

## Could not place, or left out on purpose
- **Eaves on side walls and on floors above the second**, corner posts above the ground floor, window frames above
  the second floor, ribs above the second floor: all work, all switched off for the count (`dress()` in bottom.js: the
  `on` / `corner` / `eave` arrays). With `FAR` entries they could come back.
- **Orange and purple containers** have no ribs or doors (no paint variant matches them: the Art list).
- **Container doors are rare (29)**: a short end usually has the house door or a window in its middle, and the doors
  only go on a clear one (they are look only: hung over a real doorway or window they would hide a way in).
- **The Long Stairs pole's foot** cannot be shown (above).
- **Nothing was placed in the Lost & Found, the market, the gym or the shops** (they have their own generators and
  props), and nothing outside the Bottom.
