# Islands and Islands S&D: what still needs modelling

The walk-through (2026-11-11) was played at Too HD from every spawn, the S&D sites and overhead, plus `tools/blender/inventory_maps.mjs`. The pictures are in `walkthrough.jpg`:
- rows 1–4: Islands (overview, tiki village, huts, pier, bridges, fort, lighthouse point)
- rows 5–8: Islands S&D (overview, spawns, sites, boardwalks) plus Skull Rock and the wreck

Already Blender models, so not on this list: the lighthouse (with its iron stair), the shipwreck, Skull Rock (with its cave and spine), the rocks (`rocks_islands`, `rocks_islands_sd`), the palms (the `palm` prop), the crates and barrels, and Mount Kaboom's dressing (`kaboom` on Islands, `kaboom_sd` on S&D, each on its heightfield).

The list is ranked by what players see most. Islands quick play is the busier map, and S&D's middle is its busiest spot. Columns:
- **now:** what's there today.
- **plan:** what the model will be.
- **collision:** what happens to the boxes you bump into.
- **size:** the triangle budget.

Every model covers its own boxes, like the wreck and the lighthouse: the boxes are tagged and hidden once the model loads, and drawn again if the file is missing. Collision stays boxes.

| # | What | Maps | Now | Plan | Collision | Size |
|---|---|---|---|---|---|---|
| 1 | ~~**Mount Kaboom, S&D's terraced volcano**~~ **done** (`KABOOM_SD` + `kaboom_sd` dressing) | islands_sd (the middle, between the spawns) | Was three black stepped slabs, six box stair flights and a box rim. | **Owner (2026-11-11): redo it properly: a real sloped cone, fight ledges cut into the slopes, lava pools that read as lava.** Done as the Islands mountain made small: a real walkable cone on the shaped ground (same footprint, same 9 m summit, same lava throat), boulders up the flanks for cover going up, rock ledges, warm cracks, cooled flows and a lava channel down the north gully, a broken ankle-high rim so the summit stays open. | Spawn-to-site routes unchanged (all four within 1%), no new sightlines into either site or spawn, climbing it is as fast as walking flat ground, bots climb every side (`tests/kaboom_sd.test.mjs`). | ~5k |
| 2 | **Fort Splinter** (`fort()`) *(built: `fort.glb` / `fort_sd.glb`, see `fort_before_after.jpg`)* | both (Islands TDM attackers' spawn; S&D pirates' spawn) | Grey box walls, merlons, bastions, box stairs, an armoury of walls, a box well. | A weathered sea fort. Coursed stone with mortar, moss and salt stains; real crenellations; bastions with cut corners and cannon ports; a timber gate with iron straps (a big west gate on S&D); stone wall-walk stairs. In the courtyard: a lean-to armoury with a plank roof, a stone well with a winch and bucket, the flag on a proper pole. | Unchanged, so look-only (gate, walls, wall walk, the human cannonball pad). | 8–12k |
| 3 | **Rope walkways, piers and boardwalks** (`ropeWalk()`; 2 on Islands, 5 on S&D) *(built: `walks_islands.glb` / `walks_islands_sd.glb`, see `walks_before_after.jpg`; the long pier is item 6)* | both (most of S&D's routes) | Flat brown deck boxes, box posts, a straight box "rope". | One model per map drawing every walkway: worn planks with gaps and a few missing; posts lashed with rope; handrail ropes that sag between posts; stilts down into the water with weed and barnacles; the S&D boardwalks as sturdier plank decks on piles. | Unchanged, so look-only. | 4–7k a map |
| 4 | ~~**Mount Kaboom, Islands' cone**~~ **done** (heightfield + `kaboom` dressing, see `kaboom_before_after.jpg`) | islands (the centre) | A dark faceted cone. From across the map it reads as a black lump: the crater, lava and smoke don't read. | A look pass on the dressing, not the ground: a proper crater lip with glowing lava in the throat, brighter lava rivers, a smoke plume, banded rock, jungle skirting the foot. Redone completely only if the dressing can't carry it. (The owner's 2026-11-11 "real sloped cone" ask went to S&D's volcano, item 1.) | The heightfield, throat and grapple spots are unchanged. | +3–6k |
| 5 | **The tiki village** (`tikiBar()`, `bigTiki()`, `hut()` ×2, `surfSchool()`) *(built: `tiki.glb` / `tiki_sd.glb`, see `tiki_before_after.jpg`)* | both (S&D: the tiki islet and the beach huts' islet) | Box counter, box thatch slabs, box hut walls, a box tiki face. | A bamboo tiki bar: lashed poles, a palm-thatch roof with a ragged fringe, a bar top with bottles and coconut cups, stools. The big tiki: a carved head with a grin, and his leaf hat. Bamboo-and-thatch beach huts on short stilts, with a hammock. Surfboards stuck in the sand by a sign. | Unchanged. | 6–9k all |
| 6 | **The pier and the bait shack** (Islands east, `baitShack()`) | islands | Box pier, box rails, a plank-box shack. | A timber pier on piles with bollards and tyre fenders. A ramshackle bait shack: plank walls, a hatch on a prop, a tin roof, nets, buoys and the sign. | Unchanged. | 3–5k |
| 7 | **The keeper's cottage** (`cottage()`) | both (S&D: site B cover) | Box walls, a two-slab pink roof. | A whitewashed stone cottage: a pitched pink roof with a chimney, a blue door, shuttered windows, a water butt, a washing line. | Unchanged. | 2–3k |
| 8 | **Cannons** (`cannon()`, 3 + 2) | both | A box barrel on a box carriage. | A cast-iron naval cannon (reinforce rings, a cascabel) on a wooden truck carriage with four wheels. A prop model (`cannon`), turned the way the code aims it. | Unchanged (the carriage box). | 1–1.5k |
| 9 | **Sun loungers and umbrellas** (`lounger()`) | both | Two boxes and a flat square. | A slatted wooden lounger with a striped towel, and a fringed beach umbrella in the four colours. A prop. | Unchanged. | 600–900 |
| 10 | **Sandbars** (`sandbar()`, 103 boxes on Islands) | both | 2 m stepped terraces sticking out of the shallows. | A smooth sand spit drawn over the steps, with wet edges, shells and a few starfish. | Unchanged (it stays a stepped wade). | 2–4k a map |
| 11 | **S&D small things**: the upturned rowboat, the tour group's beached boats, the site boards | islands_sd | Boxes. | A clinker rowboat (upturned, and two pulled up), and site boards on posts. | Unchanged. | 2–3k |

Order of work: 1, 2, 3, 4, then the village batch (5–7), then the props (8, 9) and the rest. One landmark or small batch per branch and draft PR, from the latest main. Each gets:
- the asset gate (0 errors)
- the tests, plus walk tests and bots wherever stairs or routes are touched
- `tools/arch/gamehash.mjs` showing it is look-only, unless the plan above says otherwise
- before/after pictures in Too HD plus one Potato
- a patch-notes line in the PR
