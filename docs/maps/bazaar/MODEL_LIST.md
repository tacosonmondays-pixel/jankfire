# Bazaar (bazaar, bazaar_sd): what still needs modelling

**Status: PARKED** (2026-11-12, the coordinator moved this session to the hub/lobby job). The walk-through and the
ranking are done; no model work started. Pick up from item 1.

Walk-through: Too HD (jank 3), every spawn, the landmarks, both sites, two high overviews per map:
`walk_bazaar.jpg`, `walk_bazaar_sd.jpg` (next to this file). Box counts from `tools/blender/inventory_maps.mjs`:
bazaar 2580 code boxes left, bazaar_sd 2276.

What the pictures say: the Grand Bazaar hall (the centre of the main map) reads as a long brown wall with a stepped
teal box pyramid on top; inside it's grey square pillars, a flat dark-red ceiling and a striped floor. The souk shops
are painted *wooden siding* (they look like suburb houses, not plastered market buildings). The S&D version is mostly
blank adobe blocks with flat-box shutters. The props (stalls, tents, pots, dye vats, crates, barrels, hay, carts) are
already Blender models and read fine; the camel (stick legs) and the palm (thin, flat fronds) are the weak ones.

Route: the glossy prop pipeline (`tools/blender/make_market.py` style: painted atlas, clear-coat, lod0/lod1,
`meta.box`, `propOf()` in shared/map.js) for landmarks and props; the arch kit (`tools/blender/arch`) only where a
building repeats on a grid. Visual only unless marked.

| # | what | now | plan | collision change | size |
|---|---|---|---|---|---|
| 1 | **Lamp Tower** + the giant brass oil lamp on top (`lampTower()`, both maps: the tallest thing, seen from every spawn) | boxes (16 + 18) | new model: banded glazed-tile minaret shaft, muqarnas corbel under the balcony, lattice rail, arched lantern top, a real Aladdin-style brass lamp (lathe body, curled handle, long spout, flame), "RUB AT OWN RISK" | no | ~20 m tall, one prop, 2 placements |
| 2 | **The Grand Bazaar hall** (bazaar, centre): walls, four gates, roof + parapet, the big onion dome + four small domes, pillars, ceiling, floor, fountain, bunting, lamps, wall stalls | boxes (308 + its 4 `wall()`s, 89 `dome()` boxes) | new model: tiled iwan gate portals, mosaic frieze, stepped merlons, square drum + ribbed teal onion dome round the tower, blue domes, round columns with gold capitals and timber beams, painted coffered ceiling with glowing lattice skylights, zellige floor, octagonal marble fountain | no | 48 m square, one prop |
| 3 | **Hall stall islands** (8 in bazaar, 3 in the S&D Grand Hall) | boxes | one prop, tinted awning per copy: two counters, a goods rack, poles, scalloped awning, goods per island | no | 7 x 4.4 m, 11 copies |
| 4 | **Souk shops** (`souk()`: 16 in bazaar, 3 in S&D) | wooden-siding boxes | plastered shells with rounded parapets, carved doors, mashrabiya balconies, cloth awnings (arch kit `dress_shell` + paint per shop) | no | ~8 sizes |
| 5 | **The caravanserai** (bazaar north): courtyard inn, two-level arcade, gallery, well | boxes (74) | new model: pointed arches between the piers, gallery balustrade, timber gallery floor, roofed well | no | 40 x 26 m |
| 6 | **Town wall, corner towers, gatehouses** (both) | flat adobe slabs | crenellated rammed-earth wall, round corner towers, gatehouse arches with studded doors | no | the map edge |
| 7 | **S&D Grand Hall** (mid) + its 3 domes | boxes (143 + 70) | new model in the style of #2 (long hall, corner doors, side doors) | no | 18 x 44 m |
| 8 | **S&D facade dressing** (`dressFacades()`: shutters, windows, balconies, lanterns, cornices) | 1449 flat deco boxes | 5-6 small instanced props (door, barred window, shuttered window, balcony, lantern, cornice run) placed by the same picker | no | small, hundreds of copies |
| 9 | **Switchback stairs** (`stairs()`, 3 in bazaar) | boxes (295) | arch-kit stairs (treads on the step tops, rails) | no | |
| 10 | **Canal + bridges** (both) | stone boxes | stone quays with coping, humped bridges with parapets, moored boats | no | |
| 11 | Small props: kilns (beehive), gate-plaza fountains, spice tables + cones, carpet frames (`hanging()`), lanterns on strings, carpet rolls, the well | boxes | one small prop each | no | |
| 12 | Camel + palm (shared with Desert: check with that session first) | weak models | remodel | no | |
| 13 | S&D palace front (marble columns), site boards | boxes | small model | no | |
| 14 | Far scenery: the next town over, dunes (rocks are done) | look-only boxes | far LOD model | no | |
