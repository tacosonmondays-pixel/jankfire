# Backrooms: what still needs modelling

The walk-through (2026-11-12) was played at Too HD on main (d5dca9d7): both spawn lobbies, the big hall at eye height
and from up high, the three long halls, two pillar rooms, both sites, the pool rooms, the stairs and the hole down, and
the freestanding walls in the hall. Pictures: `walkthrough.jpg`. Count from `tools/blender/inventory_maps.mjs`: 1825
boxes still drawn as boxes, and nothing on this map is a Blender model yet (no props, no architecture).

What the pictures show: the whole map is three flat planes. The walls are dark olive slabs with no skirting, no seams and
nothing on them. The ceiling is one painted sheet (the lights are a texture, no grid, no depth). The carpet is a smear of
dark circles. The pillars are bare sticks. Up close the eerie bit (wrong familiarity) is missing because there is nothing
familiar to be wrong: no outlets, no switches, no vents, no damp. The plan is to put the real office back in, so the
emptiness reads.

Ranked by what players see most. Columns:
- **now:** what's there today.
- **plan:** what the model will be.
- **collision:** what happens to the boxes you bump into.
- **size:** triangle budget for the whole map's copy.

Everything below is look-only: the boxes are tagged and hidden once the model loads (`archfield.js`), drawn again if the
file is missing, and `tools/arch/gamehash.mjs` must match before and after. Nothing here needs a full redo: the maze is
procedural but fixed (seed 1777), so the models are built over the real boxes.

| # | What | Now | Plan | Collision | Size |
|---|---|---|---|---|---|
| 1 | **The walls, doorways and pillars** (`wall()` runs, the hall's walls, the hall's freestanding and half walls, every pillar: 1591 wallpaper boxes) | Flat mustard boxes, 1.6 m texture, dark under the fog. Doorways are just gaps. | One Blender model (`backrooms`) over every wallpaper box: real Level 0 wallpaper (0.53 m strips with seams, stripe pairs and a chevron column, a few strips peeling off at the top), a painted skirting board, the drop ceiling's wall angle, worn corner beads on every doorway, casings on the hall's doorways and the doorway to nowhere, a wooden cap on the half walls, corner guards on the pillars. Sparse wall stuff: outlets, switches by doorways, return-air grilles, thermostats, a fire alarm pull, a paper sign that says nothing. Damp: tide marks up from the floor, drips down from the ceiling, mould, leak rings. Vertex AO in every corner. | Unchanged | 100–150k |
| 2 | **The drop ceiling and its lights** (`slab()` + the hall's ceiling, 29 boxes, plus the flicker / dead-panel overlays) | One flat painted sheet; the lights are a texture with a glow map. | A real suspended ceiling: 0.6 x 1.2 m tiles in an exposed T-bar grid, recessed 2x4 troffers with prismatic lenses and the glow, a few tiles missing (black void and ducting behind), sagging or water-stained, the odd one hanging by a corner. The flickering and dead rooms keep working (their troffers take the flicker materials). The hall's 9 m ceiling the same, with taller hangers. | Unchanged | 60–100k |
| 3 | **The carpet and the floor holes** (`groundHoles()`, 59 boxes) | A flat slab with dark circles; the stair holes and the hole down are clean cuts. | Wall-to-wall carpet in its own texture (cut pile, seams, a worn path, damp patches), metal edge strips where it meets the tiles and the Office's carpet tiles, the holes with a torn carpet edge, the slab's broken lip with rebar, and water stains running to them. | Unchanged | 10–20k |
| 4 | **Site A, the Office** (`cube()`, 28 boxes, and the water cooler) | Dark blue boxes for cubicle panels, flat desks, glowing monitor slabs. | An office kit: fabric cubicle panels with aluminium trim and feet, laminate desks with a modesty panel and a drawer pedestal, beige CRT monitors and keyboards, a desk phone, mugs, a chair pushed in (look only, inside the desk's box), the water cooler with its blue jug and cups. | Unchanged | 15–25k |
| 5 | **The pool rooms** (32 boxes, the tiled walls and pillars underneath) | White boxes with a tile texture, one water slab. | Real 15 cm tiles with grout and bullnose edges, a darker band and a gutter at the waterline, tiled pillars with rounded corners, floor drains, a pool ladder or two on the walls, the pool-room arches through the walls. | Unchanged | 20–35k |
| 6 | **Stairs down to the pools** (3 flights: `stairs()` 30 boxes + 9 rail boxes) | Box steps in tile, box rails. | Tiled steps with a nosing tile on every tread, the stair walls tiled, chrome pool handrails (tube bent down at both ends) where the box rails are. | Unchanged | 6–10k |
| 7 | **Site B, the Wet Room** (8 boxes: tiled half walls, two pillars, puddles) | Tiled boxes, flat puddles. | The same tile kit as the pools: capped half walls, pillars, floor drains, a mop bucket and a WET FLOOR sign (look only, in a free corner). | Unchanged | 5–8k |
| 8 | **The visitor** (`backrooms.js` `figure()`, the thing at the end of the hall) | Six black boxes. | A too-tall, too-thin figure in one dark silhouette: a narrow head with no face, sloped shoulders, arms hanging past its knees, long fingers, knees that bend a bit wrong. Still unlit black, only seen far away. Code fallback stays. | None (it's not solid) | 2–4k |
| 9 | **Spawn lobbies** (4 pillars each, in item 1) and a few lobby touches | Bare lobbies. | Covered by items 1–3. Maybe a lone office chair and a dead water fountain per lobby later. | Unchanged | 2–4k |

Not on this list: THE JANITOR (`lorenpcs.js`, shared lore NPC, belongs to the characters lane).

## Order of work
1, 2, 3, then the Office (4), then the pools batch (5, 6, 7), then the visitor (8). One item (or a small batch) per
branch `claude/map-backrooms-<thing>` and draft PR, each from the latest main. Each PR gets:
- the asset QA gate (0 errors) and the arch kit's z-fight check at 0
- `node --test tests/*.test.mjs tests/story/*.test.mjs` passing, the server booting clean
- `tools/arch/gamehash.mjs` identical before and after (look only)
- before/after pictures in Too HD from the same spots, plus one Potato shot
- the frame-rate cost: draw calls and triangles before and after (the maze is big: it is all one map)
- a patch-notes line in the game's voice
