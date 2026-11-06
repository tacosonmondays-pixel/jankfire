# OVERDUE WP2: The Bottom, The Gut and the Commute strip

The vertical slice's districts, streamed by WP1's city tech (`docs/story/world/WP1.md`). 640 x 512 m, 80 chunks, all
behind the story flag. Look at them: `/storytest.html?city=slice&jank=3` (or in the game: `story_slice`).

## The plan (`shared/city/slice.js`)
| district | where | height | file |
|---|---|---|---|
| The Bottom | south-west, x -320..96, z 0..256 | nine 4 m terraces, y 0 - 32 | `shared/city/bottom.js` |
| The Gut Border | x -320..96, z -48..0 | y 36 | `shared/city/gut.js` (`border`) |
| The Gut | north-west, x -320..96, z -256..-48 | plateau y 40 | `shared/city/gut.js` |
| The Commute | east strip, x 96..320 | climbs 0 - 40 with the highway | `shared/city/commute.js` |
| round the edge | Greater Jankburg up the hill to Corp Hill and the ☺ Spire, ruined lowlands, the void | silhouettes | `shared/city/horizon.js` |
Shared pieces (cube houses, stairs, ramps, lines, bulbs, retaining walls, rubble, stalls): `shared/city/kit.js`.
Each district has its own sky, fog and light (blended over 40 m at the borders) and its own light pools.

## What's where (location ids are the writer's `LOCATIONS`; `node tools/city/places.mjs` checks them)
**The Bottom.** Stacked pastel cube houses (plaster and shipping containers) on every terrace, backed against the next
retaining wall so the top roofs are the terrace above's floor; a lane along every terrace lip with washing lines (ziplines),
festoon bulbs, cables, tarps, chairs, fridges, scooters, soup stacks and barrels out the front; graffiti on the walls.
- `bottom:lostfound` / `bottom:machine`: the Lost & Found, a ruined returns depot on terrace 2 with a hole in the roof;
  the Machine at the back (a tiny sim world behind its glass, the tray you're dispensed from), the salvaged-letter sign,
  the returns counter with a sleeping cat, lost-property heaps, the mezzanine bunks (bed, locker, vending-machine
  wardrobe), the sofa-car parked inside, chairs round a burning barrel.
- `bottom:long_stairs`: nine flights straight up the middle to the Gut border, tie-dye banners and bulbs over them.
- `bottom:soup_kitchen`: the market at the bottom: stalls, fire barrels, a canopy of bulbs, crowd spots.
- `bottom:gym`: Lumps' Gym, an open container shed where all the weights are fridges (`npc.lumps` mark).
- `bottom:down_escalator`: a dead mall escalator bridging two terraces. It only goes down (a conveyor).
- `bottom:rooftops`, `bottom:sunset_spot`, `bottom:dale_shed` (marked places).

**The Gut Border.** The Bottom's top houses half-swallowed by flesh blobs and skin, a tissue cliff up into the Gut with
bone steps at the avenues; `gut:stairs_top`: the gate at the top of the Long Stairs ("WELCOME TO THE GUT. DON'T PET
ANYTHING.": pastel pillars, a mouth with teeth in the arch, an eye in the keystone, intestine draped over).

**The Gut.** Gristle & Sons' campus on the plateau, grown over: office blocks with skin dripping down the walls, sphincter
doors, tongue doors, SUDS & SONS launderettes, the Gristle & Sons sign; tooth-cobble streets with real teeth, eyes in the
gutters, heart lamps, vein cables; intestines arcing out of the ground over the streets, veins across the floor, wet mounds
with staring eyes, bile puddles.
- `gut:border`: Clocking In, the first Mr. Overtime arena (WP9): a plaza under two rib arches on tooth paving, the old
  time office with its wall of punch clocks, four lung trampolines to bounce over his slams, low flesh walls
  (`boss.overtime.spawn` / `boss.overtime.entry` marks).
- the rib avenue north from the gate: rib arches every 18 m.
- `gut:peristalsis`: an intestine-tube street that carries you (a conveyor that surges on the heartbeat).
- `gut:big_stomach` / `gut:belly_button`: a stepped crater ringed with giant teeth, folds round the rim, a glowing acid lake
  that digests you, the belly-button door at the bottom.
- `gut:choir_lung`: a cathedral that breathes (a huge pulsing lung over a bone colonnade, windpipe organ pipes).
- `gut:tooth_market`: stalls, specimen jars, the Wisdom Tooth in the middle.
- `gut:campus` (marked).

**The Commute.** `commute:ring_road`: the old ring road climbing the hill's east side, jammed with the Final Quarter's rush
hour (rusted saloons, school buses, skeletons still in their lanyards, cones), a smooth deck over walkable steps;
`commute:smiles_hideout`: the collapsed span you have to jump (jersey barriers closing the lanes); the ☺ CORP district
clock stopped at 17:29; `commute:unpaid_camp`: Camp Onboarding under the highway (filing-cabinet barricades, Unpaid tents,
burning ☺buck barrels, tyre stacks, a bus war-rig, `enemy.unpaid` marks); `commute:digit_13`: the fallen 13, glowing in a
glassed hot zone; a wrecked ☺ CORP walker tank; ruined shopfronts with blast shadows, rubble heaps, paper drifts.

## Traversal gimmicks (`shared/city/gimmicks.js`, triggers from the generators)
- **Washing-line ziplines** (167 in the slice): grab with the use key, slide (downhill or the way you face), knock the
  socks off as you go, fling off the end ("ZIPLINE!", "SOCK RUN").
- **Peristalsis + the Down Escalator**: the floor carries you; slide in on the heartbeat for a surge ("RIDING THE BEAT").
- **Lung trampolines**: land on one and it throws you up, higher the further you fell ("LUNG!", "BIG BREATH").
- **Acid**: the Big Stomach's lake digests you ("YOU'RE BEING DIGESTED"). **Hot zones**, **paper storms**: triggers for the
  systems (Late Fees hiding, weather).

## Blender props (54, `public/models/story/s_<id>.glb`, sheets in `tools/blender/sheets/story/`)
Every model has a `*_lod1` copy (13-25% of the triangles) the city draws at mid distance; small repeated props stop
drawing past ~70 m (the houses' far boxes carry the look). Scripts: `tools/blender/make_story_{bottom,safehouse,gut,gut2,landmarks,ruins}.py`
(kits: `bottom_kit.py`, `gutkit.py`). Flesh materials (`*pulse*`, `lung*`, `*flesh*`) breathe in the game; `*paint*` takes a
per-instance colour.
- The Bottom (18): laundry x2, wok dish, plastic chair, sofa, fridge, scooter, AC unit, fallen ☺ sign, festoon bulbs, tie-dye
  tarp, scavenged door, shutter window, soup crate, bed, locker, vending-machine wardrobe, garage door.
- The Gut (15): rib arch, lung, molar, canine, gutter eye, sphincter, tongue, SUDS & SONS launderette, heart lamp, specimen
  jar, vein cable, Gristle & Sons sign, flesh blobs x2, windpipe organ pipe.
- Landmarks (7): the Machine, the LOST & FOUND sign, the returns counter, lost-property pile, the Gut gate, the sofa-car
  (wheels as nodes), the rush-hour wreck.
- Ruins and the Commute (14): filing cabinet, office chair, ☺buck fire barrel, Unpaid tent, rubble x2, blast-shadow
  shopfront, jersey barrier, cone, the 17:29 clock, the ☺ CORP walker tank, paper drift, tyre stack, lanyard skeleton.

## Numbers
Chunk build 4-9 ms each in Node (80 chunks in ~0.45 s); a Bottom chunk averages 8.7k triangles (hidden faces between
touching boxes are skipped). Too HD in the depot, the densest view: ~576k triangles including the shadow pass
(budget 600k). Server: the whole slice cached is ~10 MB; 8 story rooms: heap +16 MB (WP1.md).

## Not yet (later packages)
NPC and enemy characters (ART_BIBLE #8, #17, #25: the crowd spots, `npc.*` and `enemy.*` marks are placed), district music
beds, the paper-storm weather effect, real cars on the highway (WP7). The look-check sheets are in this folder.
