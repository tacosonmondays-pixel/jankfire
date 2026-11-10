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
| `container_rib` | container cubes, the two long walls | at floor level, tiled from the wall's end to each opening and on after it (windows cut 0.16 m wider than the hole, doors 0.02). Scale `h / 2.8` so the ribs reach the slab; each strip is centred in its stretch of wall, the leftover (under one rib) shows the wall |
| `container_doors` | container cubes, the two short ends, only where nothing is cut within the doors' width of the middle | wall face at floor level, middle, scale `(h - 0.15) / 2.6` |
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

Without filter 2 the kit is about 1,200 instances a chunk; with both it is about 360.

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
Kit props per Bottom chunk: **average 361, least 61, most 583** (the district had 217 a chunk before, so 579 now).

| piece | per chunk | triangles (full / far copy) |
|---|---|---|
| container_rib | 115 | 18 / 18 |
| cube_eave | 74 | 92 / 22 |
| stair_step, stair_post | 46 + 46 | 80 / 12, 120 / 22 |
| cube_corner | 25 | 248 / 58 |
| cube_window_b, _a, _c | 20, 15, 3 | 138 / 12, 282 / 64, 620 / 142 |
| Long Stairs pieces (332 in all, 75 - 92 in each of its 4 chunks) | 12 | 24 - 74 far |
| container_doors, roof junk | 2.4, 3.8 | 984 / 224, 736 / 176 and 548 / 130 |

A chunk's kit is about 40k triangles at full detail and 9.7k as far copies. Chunk build time in Node goes from about
3.5 ms to about 5.5 ms for a Bottom chunk (the hidden-wall tests).

**It needs two table entries in `public/js/city/props.js` before it is cheap** (not my file to edit). The new ids have
no `FAR` or `DETAIL` entry, so today each one is drawn across the whole props ring and at full detail out to
`propsHi`. Counted from the generator (`node` script, instances inside the ring, three spots):

| preset | kit as props.js draws it today | with the entries below |
|---|---|---|
| Potato | +2,600 to 3,400 instances, +70k to 92k triangles | +130 to 420, +5k to 11k |
| Crusty | +3,600 to 5,000, +124k to 171k | +280 to 600, +14k to 27k |
| Mid | +5,100 to 6,300, +191k to 244k | +600 to 890, +29k to 44k |
| Too HD | +7,400 to 8,200, +330k to 369k | +1,100 to 1,400, +62k to 88k |

(WP1's budgets: Too HD 600k triangles, Potato 150k; the depot was already at 576k.) Draw calls: +26 to 40 on Potato,
+85 to 102 on Too HD, because the pieces carry 68 materials between them (see the Art list).

Suggested entries (the same kind of numbers the doors and shutters have):
```js
Object.assign(DETAIL, { cube_eave: 0.5, cube_window_a: 0.4, cube_window_b: 0.4, cube_window_c: 0.4, cube_corner: 0.4, stair_step: 0.4, stair_post: 0.4, container_doors: 0.6, longstep_a: 0.6, longstep_b: 0.6, longrail: 0.6, longplaque_a: 0.3, longplaque_b: 0.3 });
Object.assign(FAR, { cube_eave: 90, container_rib: 90, cube_window_a: 70, cube_window_b: 70, cube_window_c: 70, cube_corner: 70, stair_step: 70, stair_post: 70, container_doors: 120, cube_roofjunk_a: 120, cube_roofjunk_b: 120, longplaque_a: 40, longplaque_b: 40 });
```
Two more things in that folder, also outside this lane:
- `propcode.js` has no stand-in for the 17 ids, so until each `.glb` arrives every instance is the default magenta
  1 m box. `registerCodeProp(id, [])` for each would draw nothing instead.
- A prop's paint slot only takes one of 8 fixed colours (`PAINTS[v]`), so "the cube's tint" is the nearest of those
  (`paintOf`). See the Art list.
