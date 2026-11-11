# The Bottom: where the Blender kit goes (cube houses + the Long Stairs)

The Art lane's pieces (`tools/blender/make_story_cubekit.py`, `make_story_longstairs.py`: 24 ids after their second
pass) are placed by the Bottom's generator as instanced props. It is look only: no collision box moved, appeared or
went. Code: `shared/city/kit.js` (`cubeKit`, `stairKit`, `paintOf`, `KIT`, `KIT_SIZE`) and `shared/city/bottom.js`
(`dress`, `stackOf`, the Long Stairs block). Test: `node tests/story/bottomkit.test.mjs`. `KIT.on = false` (kit.js)
builds the district with none of it.

**Sizes.** The models' heights and runs are in each `.glb`'s `jf` meta (not in `index.json`, which is only the list of
ids). The generator runs on the server and in the chunk worker, where no model is ever loaded, so it cannot read them:
they are kept in one small table, `KIT_SIZE` in kit.js, and the test reads every `.glb` and fails if the table and the
files disagree.

## What is placed, by what rule

A wall is one of a cube's four sides (0 = uphill / -z, 1 = +x, 2 = the lane side / +z, 3 = -x). Every model faces -z
and is turned with the same yaw the doors and shutters already use.

| piece | where | how it is positioned |
|---|---|---|
| `cube_window_a/b/c` | every 1.4 x 1.1 window opening on a dressed wall, unless the old `shutter` prop already fills that opening or a side stair climbs across it | on the wall face, bottom middle of the opening (`y + 1.0`). Mix b 50 % / a 25 % / c 25 % from the kit's own random stream. An opening with an AC unit hanging low in it always gets a (the flat barred one). The glowing pane behind stays |
| `cube_corner`, `cube_corner_b` | ground-floor cubes: one post on each dressed wall (the lane front, the side walls), at its left end (`cube_corner`) or its right end (the mirror, `_b`) | a coin toss picks which hand is tried first; the other is tried if that end has an opening within 1.15 m, a side stair, a wall in front of it, or a post already (two walls share each corner). 3.3 m tall at scale 1; on the lowest cubes (2.8) it is shrunk to 0.93 so it does not stand proud of the roof (see the Art list) |
| `cube_eave6`, `cube_eave4`, `cube_eave_b` | the lane side and the uphill side of every real roof (the top cube of a stack) that is dressed, and the lane side of half the ground floors | on the wall face at the slab's underside. A wall is covered with 6 m runs, then a 4 or a 2 for the rest: up to 4.6 m one 4; 4.6 - 5.4 a 4 and a 2; 5.4 - 6.6 one 6; 6.6 - 8.6 a 6 and a 2; 8.6 - 10.6 a 6 and a 4. Pieces overlap when they add up to more than the wall; a single piece may hang 0.3 m past each end or stop 0.3 short. Which end the big piece goes is a coin toss. Only the 6 m piece has a rag, so a front shows one at most; `cube_eave` (2 m with a rag) is no longer placed. Painted with the roof's tint if it has one, else the cube's |
| `container_rib`, `container_rib_half` | container cubes (all five colours now), the two long walls | at floor level, from the wall's end to each opening and on after it (windows cut 0.16 m wider than the hole, doors 0.02): whole 1 m strips, then a half strip when 0.5 m or more is left, the lot centred in its stretch (so under 0.25 m of flat wall shows at each end). 3.3 m tall at scale 1, 0.93 on the lowest cubes like the corner post |
| `container_doors` | the same containers, the two short ends, only where nothing is cut within the doors' width of the middle | wall face at floor level, middle, scale 1 (3.1 m: its top is in the slab, or 0.1 m under it on the tallest cubes) |
| `cube_roofjunk_a/b` | 40 % of top roofs that have nothing else on them (no chair, sofa, sign or tarp) and that nobody crosses (not the roofs level with the terrace above, where the plank bridge lands) | 1.1 m in from two edges. On a back row always the lane-side corners: the uphill edge is beside the lip above, with its washing-line poles, ziplines and grapple rings. Tank 55 %, loft 45 % |
| `stair_step` + `stair_post` | every step of a `sideStair` on the two lowest floors, unless the step is squeezed into the house next door | tread: the step top's downhill edge, middle, yaw pi (the stairs climb -z). Post: same spot, 0.58 m to the open side |
| `longstep_a/b` | every step of the Long Stairs (152), a on even steps, b on odd | the step top's downhill edge, middle of the 8 m |
| `longrail`, `longrail_b` | every block of both stepped rails: `longrail` on the eight flights whose blocks climb 0.53 (128), `longrail_b` on the top flight, whose blocks climb 0.25 (32) | the block's top at its downhill end, middle of its thickness. Handrail colour by flight: yellow, pink, teal |
| `longpole_b` | both neon poles of every flight (18) | the map's pole stands inside the rail block, so the post is the one made to sit on the rail: on the top of the block the pole is in, at the pole's centre, arm turned outward. The neon box is now at the height of its sign frame (3.7 - 4.4 over the rail top, `KIT_SIZE.poleB`). The pole box is collision only (`hide`). `longpole` (the one with its foot on the ground) is not placed |
| `longplaque_a` (doris), `_b` (big len) | one each | doris: flight 2 (the first one you climb from the Lost & Found's lane), 4th step, 2.5 m in from the left rail. big len: flight 4, 7th step, 2.4 m in from the right rail. 43 m and 99 m up from the quest mark at the foot (`bottom:long_stairs`) |

**Paint.** A prop's paint slot takes a variant number. `PAINTS` in props.js has ten colours now: the eight it had, then
the containers' orange (`ff9a4d`) and purple (`9a7aff`). A plain number still wraps over the first eight exactly as
before (washing lines, mannequins and a lost-property pile use numbers of 8 and more, 535 props in the slice: with a
wrap over ten they would all have changed colour), and the two new colours are asked for as -1 and -2. `paintOf(tint)`
in kit.js gives the nearest variant; every container colour has an exact or near one, so all containers get ribs and
doors.

### Which walls get dressed
Two filters, both cheap and both the same on the server and every client:

1. **Hidden walls.** A piece is skipped when the point 0.45 m or 1.0 m out from it is inside another cube (this lot's
   or either neighbour's) or inside the terrace behind (counted up to the top of the lip wall of the lane above). That drops the slots between neighbours (0.8 m), the gap between
   a lot's two rows (0.6 m) and every back wall against the retaining wall. A neighbour's cubes come from a dry run of
   its lot (cached), so nothing is built twice for it.
2. **Walls out of reach.** Only these are dressed: the lane front of the row that stands on the lane, two floors up;
   the backs of the back row from the floor of the lane above to 4 m over it (you look at them over the lip wall);
   the side walls of the two lowest floors (alleys, the gap beside the Long Stairs, a floor that clears the house next
   door). Higher floors and tower fronts behind another row stay bare.

Without filter 2 the kit is about 1,200 instances a chunk; with both it is about 340.

## Determinism (the proof)
- The kit draws from `rng(lotSeed ^ 0x6b17)`, never from the stream that lays the boxes.
- Whole slice, 80 chunks, main `bff3f88` (the first kit) vs this branch: **40,880 collision boxes, hash `c6d85e78` on
  both** (the same hash as before the first kit, main `13572c3`). The Bottom alone: 33,980 boxes, `118b5f2e`. The 52
  chunks outside the Bottom are byte-identical. In the Bottom's 28, all 6,089 props that are not kit pieces are still
  there in the same order, and deco, shapes, lights, triggers, marks, spawns and lanes are identical.
- The only box difference from main is render-side: the 18 neon boxes moved to their lamp posts' frames.
- `tests/story/bottomkit.test.mjs` builds the slice with the kit on and off and checks that nothing but props
  differs; that every piece has a model, a draw distance or detail share, an empty stand-in and a paint props.js can
  draw; that `KIT_SIZE` matches the files; that four chunks hold the same kit as the same ground built in one piece;
  the count per chunk; that roof junk is 2.5 m clear of every mark and zipline end; that every piece sits on a wall,
  step or rail the right way round (probe points); that no corner post or rib stands proud of its roof; and that each
  of the 18 neon boxes is in its lamp post's frame.

## Cost
Kit props per Bottom chunk: **average 341, least 57, most 549** (9,543 over the 28 chunks; the first kit was 302 a
chunk). The district has 217 other props a chunk.

| piece | per chunk | first kit | triangles (full / far copy) |
|---|---|---|---|
| container_rib + _half | 127 + 14 | 64 | 18 / 18, 10 / 10 |
| stair_step, stair_post | 46 + 46 | same | 80 / 12, 120 / 22 |
| cube_eave6, 4, _b | 13.5, 10, 8.6 (32 in all) | 74 | 252 / 59, 170 / 39, 90 / 21 |
| cube_corner, _b | 9.4 + 17 | 25 | 248 / 58 |
| cube_window_b, _a, _c | 14, 11, 7.3 | 16, 13, 2.4 | 138 / 12, 282 / 64, 304 / 24 |
| Long Stairs pieces (332, 75 - 92 in each of its 4 chunks) | 12 | same | 20 - 68 far |
| container_doors, roof junk | 1.9, 4.2 | 1.0, 3.8 | 984 / 224, 736 / 176 and 548 / 130 |

The count went up because orange and purple containers have ribs now (ribs are 18 triangles a strip); the roof lips
went from 74 pieces a chunk to 32.

**Measured like for like** (the city test page, `/storytest.html`, Too HD, 960 x 540, the street view at
(-96, 8.3, 202.5), yaw 0.95): main today **641,933 triangles / 690 draw calls / 9,169 prop instances**; this branch
**644,048 / 711 / 9,713**. That is +0.3 % triangles, +21 draw calls, +544 instances. The draw calls are the new ids (each model is one
instanced draw per material, full and far).

`props.js` has `DETAIL` / `FAR` entries for the new ids (the same numbers as the pieces they sit beside) and
`propcode.js` an empty stand-in for each, so nothing shows while a model loads.

## For the Art lane: what still sits wrong after the second pass
The second pass fixed the floating bit of step lip (it lies on the step below now), the buried lamp-post foot and
stickers, the loose cable, the top flight's handrail, the row of rags, the one-handed corner post and the paint that
glared beside the walls. What is left:

| id | what is off | what I would want |
|---|---|---|
| `cube_corner`, `cube_corner_b`, `container_rib`, `container_rib_half` | 3.3 m does not fit every cube. A piece's top has to land in the 0.3 m roof slab: between h and h + 0.3 over the floor. The cubes are 2.8, 3.0 and 3.2 tall, so the top must be at least 3.2 and at most 3.1: no one height does it. At 3.3 the piece is right on the 3.2 cubes, flush with the slab's top on the 3.0 ones and 0.2 m proud of the roof on the 2.8 ones, so the map still shrinks it to 0.93 there (a third of the cubes; the rib strips are 0.93 m wide on those) | nothing, if a 7 % shrink on the low cubes is fine (it cannot be seen). For exact strips: a second height, 3.05, for the 2.8 cubes |
| `container_doors` | 3.1 fits the 2.8 and 3.0 cubes; on the 3.2 ones a 0.1 m strip of flat wall shows between the doors' top and the slab | fine as it is (it reads as a lintel) |
| `cube_eave6` | it is the only piece with a rag, so every front between 5.4 and 10.6 m wide has exactly one rag, always 0.25 - 0.7 m right of the piece's middle | a bare 6 m piece too (`cube_eave6_b`), so a rag can be one front in three; or move the rag about |
| `cube_eave4`, `cube_eave6` | a 4 m piece on a 3.4 - 4 m wall (and a 6 on a 5.4 - 6 m one) hangs up to 0.3 m past each corner. It reads as an overhang; where two meet at a corner they cross | fine; a mitred end piece would be the tidy answer, not needed |
| every new id | each id is its own set of draw calls (one per material, full and far): the new ids add 21 on the street view (690 -> 711) for the same triangles. `cube_corner_b` repeats `cube_corner`'s 5 + 3 materials, the lips are 2 - 3 + 2 - 3 each | one atlas material per piece plus the paint slot, as asked before: it matters more now there are more ids. `cube_window_c` is down to 304 triangles and 1 far material, but still 7 materials up close |
| `longpole` | no longer placed: every pole on the Long Stairs stands in a rail block, so all 18 are `longpole_b` | keep it for a pole on open ground, or drop it |
| `cube_eave` | no longer placed (the 6 m piece carries the rags) | drop it, or keep it for a short wall elsewhere |
| paint `9a7aff` / `ff9a4d` | (seen on the test page and in the game at night) the ribs on a purple container are a bluer, deeper purple than the flat wall they replace, because the wall is the tint over a pale corrugated texture and the rib is the tint over 0xc8c8c8 with rust specks. It only shows where bare wall is left beside ribs (under 0.25 m at a wall's ends, and the strip round a window) | not a model fault |

Still true from the first list, and not the Art lane's: the old `shutter` prop hung 0.2 m above its window straddles
the roof slab and reads as a second window stacked on a kit frame (world lane: drop the high position).

## Could not place, or left out on purpose
- **Eaves on side walls and on floors above the second**, corner posts above the ground floor, window frames and ribs
  above the second floor: all work, all switched off for the count (`dress()` in bottom.js: the `on` / `corner` /
  `eave` arrays). Now that the pieces have draw distances they could come back; I left the reach rule as it was so
  this change is only the new models.
- **Container doors are rare (54)**: a short end usually has the house door or a window in its middle, and the doors
  only go on a clear one (they are look only: hung over a real doorway or window they would hide a way in).
- **`longpole` and `cube_eave`** are not placed (above).
- **Nothing was placed in the Lost & Found, the market, the gym or the shops**, and nothing outside the Bottom.

## Screenshots
Second pass (`bottomkit2_*.jpg`): the city test page (`/storytest.html`: the game's own streamer, props and materials,
without the HUD; it is lit brighter than the story's night), Too HD, 960 x 540. Before = main `bff3f88` (the first
kit), after = this branch, side by side, same spot and view.

| file | what it shows |
|---|---|
| `bottomkit2_fronts.jpg` | a lane on terrace 2: three rags on the teal front become one long lip with one rag; the peach house's lip is bare and its corner post is the mirrored one; a curtain window on the blue tower |
| `bottomkit2_container.jpg` | the teal first-floor container: darker ribs that sit with the walls, taller doors, a corner post on the house below |
| `bottomkit2_container_walls.jpg` | the purple container gets its ribs (it was left flat for want of a paint) |
| `bottomkit2_sidestair.jpg` | a side stair and the house beside it (the post moved to the other end of that wall) |
| `bottomkit2_longstairs_foot.jpg` | the Long Stairs from the foot: lamp posts standing on the rail with the neon in their frames, the broken bits of lip lying on the steps |
| `bottomkit2_longstairs_half.jpg` | from terrace 4: lamp posts on the rails; the orange container at the left has its ribs |
| `bottomkit2_longstairs_top.jpg` | the top flight: the handrails follow the shallow blocks (they shot up over them before); ribs on the orange container at the left |
| `bottomkit2_roofs.jpg` | terrace 4: bare lips where there were three rags, the caged window (c), a tank on the roof corner (top right), a lip and a corner post on the yellow container, darker yellow ribs |
| `bottomkit2_plaque.jpg` | doris's plaque; the broken bits of lip are on the steps now |
| `bottomkit2_street.jpg` | the street view the triangle and draw-call numbers are from |

First pass (`bottomkit_*.jpg`): in the game, story mode, Too HD, 800 x 450, before = main `13572c3` (no kit),
after = the first kit: `bottomkit_street`, `_container`, `_container_walls`, `_sidestair`, `_longstairs_foot`,
`_longstairs_half`, `_roofjunk`, `_plaque`.

## Not done, not tested
- The second-pass pairs are from the city test page, not the game: one Too HD frame in the game took 5 - 10 s on the
  shared machine. Two spots were then looked at in the game, story mode, Too HD (`bottomkit2_ingame.jpg`: the two
  containers by the Long Stairs, and the teal container from the lane): the teal ribs sit with their wall under the
  night light; the purple ribs read bluer and brighter than the flat wall did (the Art list).
- Only Too HD was run. Potato, Crusty and Mid were not (every new piece has a far copy and a `FAR` / `DETAIL` entry).
- Stills only, no clip; nobody walked up to each piece.
- The reach rule (which walls are dressed) is unchanged from the first kit; the switched-off walls were not tried with
  the new pieces.
- A multiplayer map was not run: outside `shared/city/` the only code touched is `public/js/city/props.js` and
  `propcode.js`, which only the story's city loads.
