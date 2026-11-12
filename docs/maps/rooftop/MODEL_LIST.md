# Rooftop: what still needs modelling

Walk-through on 2026-11-12 (main at `d5dca9d`): Rooftop and Rooftop S&D in the real game at Too HD (jank 3), shots from
both spawns on each map, the S&D sites and mid, the penthouse inside and out, the bridges, the drop, the city and two
high overviews (`walk_sheet.jpg` next to this file: rows 1-4 Rooftop, rows 5-6 Rooftop S&D), plus
`tools/blender/inventory_maps.mjs`. Boxes still drawn as boxes: rooftop 3,537 look-only + 214 solid, rooftop_sd 4,075 +
172. Only the generic props are Blender models so far (AC units, water towers, billboards, crates, palms, the street's
lights, cars and trees). No arch model is placed on either map.

What reads worst: the **penthouse** in the middle of both maps is a blue grid box (glass-block texture with pixel
windows), the **machine rooms** at both spawns are bare grey blocks (the first thing you see on spawning), the towers
are single textured boxes 150 m tall with a noisy tar roof, the **stair-bridges** are concrete stairs of boxes over a
150 m drop, and the pool deck's DJ booth and speakers are tyre-textured blocks.

Ranked by what players see most: landmarks and objectives first, then buildings, then props and scenery.
**Collision** = whether the boxes you bump into change (default no: visual only; the boxes stay for physics, bots and
hits, checked with the map's gamehash).

| # | What | Maps | Now | Plan | Collision | Size |
|---|---|---|---|---|---|---|
| 1 | **The glass penthouse** (`penthouse()`): the bar downstairs, the lounge upstairs, the helipad roof | both (the middle; S&D its walls split the spawns) | glass-block boxes with pixel windows, box door gaps, a box parapet, neon strips | **new model** (arch): a two-storey steel and glass pavilion from real penthouse references: slim chrome mullions and transoms, tinted pink-violet glass with reflections, a deep white roof fascia with the neon in a channel, spandrel bands between floors, framed doors and a sliding glass door onto the pool, a glass balustrade on the roof with steel posts, the helipad's edge lights and windsock mast, the inside stairs as real stairs (wood treads, steel stringers) | no | 20 x 16 x 8.7 m, 6-9k |
| 2 | **Machine rooms** (lift motor houses), antennas, vents | both (2 at the spawns on Rooftop, 5 on S&D: both spawns, B site) | grey concrete blocks with a flat slab lid, a box door, a 6 m pole antenna | **new prop** (`liftroom`): a lift overrun from real references: board-marked concrete, louvred vents, a steel door with a WARNING plate, a cat ladder to the lid, a cable tray, a hooded vent, the lid's coping; the antenna as a lattice mast with an aircraft warning light | no | 6 x 4.8 x 10 m, 2-3k |
| 3 | **The tower bodies, parapets and roof skin** (`roofTop()`): the bank, the hotel, the party block; S&D's 7 tops | both | one textured box per tower down to the street, a 1 m box parapet, a noisy tar texture on the roofs | **new models** (arch, like Skyline's `tenement`): an office curtain-wall tower (the bank: `fac_office` with spandrels and a crown), a brick hotel (`tenement`-style with a neon HOTEL blade), the party block; parapets with metal coping, tar roofs with membrane seams, drains and walkway pads. **Shared with Skyline** (same `roofTop()`, its #4): build the facade kit once, whichever map session gets there first | no | 28 x 36 m x 150 m, x3 (x7 S&D) |
| 4 | **Stair-bridges** (`stairBridge()`) and the **sky-bridge** (`skyBridge()`) | both (4 + 1 on Rooftop, 12 + 2 on S&D) | concrete box steps solid down to the low end, plate rails; the sky-bridge a grid slab with box rails | **new model** (arch over the step boxes): steel stair bridges: deep side stringers or a truss under them, chequer-plate treads with yellow nosings, posts, handrail and mid-rail, lights underneath; the sky-bridge a Warren truss with neon along the chords. **Shared with Skyline** (its #5 and #9) | no | 4 m wide, 7-60 m long |
| 5 | **The roof signs**: JANK BANK, HOTEL 4 HOURS, the ☺ CORP flag | both (behind both spawns / sites) | a flat picture on two 6 m poles | **new prop** (`roofsign`): a real rooftop sign structure: a raked steel lattice frame braced back to the roof, a catwalk with a rail, floodlight arms, HOTEL 4 HOURS as neon tube letters on a raceway (the picture stays the map's) | no | 16 x 6.4 m, 2-3k |
| 6 | **The pool deck set**: the DJ booth, speakers, the light rig, four cabanas, loungers, the flamingo and the ring, string lights, palm planters, the pool coping | both (Rooftop's south half; S&D mid) | tyre-textured box booth and speaker stacks, post-and-slab cabanas, box loungers, a box flamingo | **new props** (small batch): a DJ booth (flight-case desk, two decks and a mixer, a laptop, a JANK banner), PA speaker stacks on stands, a box-truss light rig with moving heads, a cabana (frame, striped canvas roof with valance, tie-back curtains, a daybed), a slatted lounger with a towel, an inflatable flamingo and ring, planters | no | 6-9k for the set |
| 7 | **The hotel roof**: hot tub, towel hut, umbrellas | both (Rooftop east spawn; S&D A site) | tile boxes round a water box, a wood box hut with a pink slab, pole-and-square umbrellas | **new props**: an acrylic hot tub with a wood surround, steps and jets; a beach-hut towel kiosk (tongue-and-groove planks, pink roof, stacked towels, a TOWELS sign); a market umbrella | no | 3-4k |
| 8 | **The bank roof**: satellite dish, skylights, roof vents, the pipe run, the cold store, the generator, cable drums | both (Rooftop west spawn; S&D B site) | white box dish, glass slabs, box vents | **new props**: a VSAT dish on a non-penetrating mount, pyramid skylights, mushroom vents, a walk-in cold store with a condenser, a cable drum | no | 3-4k |
| 9 | **The penthouse inside**: the bar and back bar, stools, the jukebox, booths, tables, sofas, the pool table, the telly, plants, the disco ball | both | boxes | **new props** (or part of #1): a curved bar with a bottle wall and a BAR? neon, chrome stools, a jukebox, diner booths, a pool table, a sofa set, a mirror ball | no | 4-6k |
| 10 | **S&D cover kit**: HVAC boxes, planters, skylights, the privacy glass walls, A's rooftop bar, the day bed | rooftop_sd | metal boxes with a grid lid, stone box planters | **new props**: a packaged rooftop HVAC unit (fan grilles, panels, pipework), concrete planters with hedges, the privacy walls as frosted glass with neon caps | no | 3-5k |
| 11 | **Jump pads** | both | a glowing cyan box | **remodel**: a chrome launch pad with a glowing ring and chevrons (gameplay object: the box and its launch stay) | no | 300-600 |
| 12 | **The city below and beyond** (render only) | both | ~3,100 / 3,460 boxes (`streetLevel()`, `cityBeyond()`, far `tower()`s) | **new kit**: a few instanced far-building and shopfront types. **Shared with Skyline** (its #18): one kit for both city maps | no | far |

## Not Rooftop's own (for the coordinator)
- **Box clouds** and **cone mountains** over the city maps: the same as Skyline's note (global: `public/js/world.js`
  clouds, `public/js/scenery.js` city horizon).
- **Shared kits with Skyline**: tower bodies (#3), stair-bridges (#4) and the city backdrop (#12). Rooftop starts with
  its own pieces (#1, #2, #5, #6) so the two sessions don't build the same thing; whichever lands a shared kit, the
  other reuses it.

## Order of work
1 (the landmark both maps are built round), then 2 and 5 (what you see from every spawn), then 6, 7, 8 (props in small
batches), then 9 to 11. 3, 4 and 12 wait on the split with Skyline. One landmark, or a small batch of related props, per
branch `claude/map-rooftop-<thing>`.
