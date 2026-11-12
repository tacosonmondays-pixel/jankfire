# Jankburg: what still needs modelling

Walk-through on 2026-11-12 (main at `1f85a6d`): Jankburg in the real game (Jank Royale, Too HD = jank 3), shots from
four spawns, the plaza fountain, the cathedral, JankCorp HQ, the market hall, Number Works' smokestacks, the
THEY / YOU / WE letters, Liberal Lane, Overdraft Heights, Neon Market, a slum tower, the firewall (inside a gate,
outside, on top, a corner), the sprawl's shacks (street level and from above), the plastic orchard, the crashed blimp,
the farm, the highway stubs, the quay and two high overviews (`walkthrough.jpg` next to this file, labelled), plus
`tools/blender/inventory_maps.mjs`.

Jankburg has the most code boxes of any map: **9,448 still drawn as boxes** (8,830 architecture, 449 props, 1,732
ground and look-only paint + backdrop). Already Blender: the street props (streetlights, vending machines, cars, the
school buses, barrels, crates, jersey barriers, number balls, the forklift, pallets, lollipop / pine trees). **No arch
model is placed on the map yet.** A frame from the plaza draws ~1,800-2,700 calls at Too HD, the spawns up to ~4,000:
everything below has to instance (one model drawn many times) or merge, never add per-copy draw calls.

What reads worst: the **firewall** (a 360 m ring of plain grey slab with a pink strip: it frames every view and is
the first thing you see from the sprawl), the **city houses** (plank-textured boxes, a flat sign, box awnings: they
line every street), the **megacity in the haze** (170 textured boxes standing round the whole horizon), the
**plastic orchard** and the **sprawl's shacks** (hundreds of one-box trees and one-box huts), the **crashed blimp**
(a stack of pink boxes on its side: unreadable), and the landmarks (the fountain's ball is stacked boxes; the
cathedral, HQ, market hall and factory are plain shells).

Ranked by what players see most: landmarks and objectives first, then buildings, then props and scenery.
**Collision** = whether the boxes you bump into change (default no: visual only; the boxes stay for physics, bots and
hits, checked with the map's gameplay hash). **Kit** = one model reused on many copies (instanced).

| # | What | Now | Plan | Collision | Size |
|---|---|---|---|---|---|
| 1 | **The Smiling Fountain** (`fountain()`, plaza: the middle of the map, the zone's first centre) | a ball of 45 stacked yellow boxes with a face picture on each side, a box rim, box water arcs | **new model, in progress** (`p_jb_fountain`, PR after this one): a marble civic basin (bullnose coping, pink panels, corner piers with brass finials, a mosaic pool floor full of coins), a panelled pedestal with a brass SMILE: IT'S MANDATORY plaque and spouts, a brass cup holding a 12 m glossy toy-yellow smiley (bulging eyes, one pupil wandering off, a skeptical brow, anime blush, a toothy grin, a chrome nozzle spitting a jet into the pool), limescale and algae, PROPERTY OF JANKCORP stencilled on the side | no | 22 x 14.4 x 22 m, 16k / far 1k |
| 2 | **The firewall** (`cityWall()`): wall runs, the neon strip, merlons, 16 wall towers with their jump pads, 4 fat corner towers, the stepped chamfers, 3 breaches with rubble ramps | 822 boxes + the wall body: plain grey slabs, a pink strip, box merlons | **kit** (props, instanced): a 6 m precast wall module (panel joints, a recessed neon channel, crenel caps, cable trays, a FIREWALL stencil, grime streaks), the wall tower (a guard tower with a pink-lit crown, a ladder hatch, floodlights, the jump pad as a chrome launch plate), the corner tower, a chamfer block, breach rubble (broken panels, rebar). Fitted onto the existing boxes | no | 360 m ring; module 6 x 15 x 4 m 1-2k, tower 3-4k |
| 3 | **The four gates** (Data Gate, Freight Gate, East / West Toll): gatehouses, sign bridge, toll booths, barrier arms, jersey blocks | boxes, a picture on the sign bridge | **new model** (one gate, instanced x4): gatehouses with side passages, a steel sign gantry (the picture stays the map's), toll booths with windows and a ☺ CORP card reader, striped barrier arms on posts | no | 46 x 20 x 8 m, 6-8k |
| 4 | **JankCorp HQ** (`hq()`, Corp Hill): the 152 m glass tower, the 40 m logos, the gold stock arrow, the planters | a 4-tier glass box tower, gold box steps, marble boxes | **new model**: a stepped curtain-wall skyscraper (mullion grid, spandrels, a crown with a helipad and red aircraft lights), the logo banners in frames, a lobby with revolving doors, the gold arrow as a polished trophy sculpture (each step a bar of a bar chart), planters with benches | no | 24 x 152 x 24 m, 8-10k |
| 5 | **The Cathedral of Shareholder Value** (`cathedral()`): nave, ticker stained glass, pews, server-rack organ, bell tower (the town's best sniper spot) | 101 boxes: stone slabs, pictures for windows, box pews, a gold bar for a bell | **new model** (arch over the boxes): buttressed stone nave with pointed-arch window frames round the ticker glass, a rose window, a gilded portal, real pews, an organ of server racks with blinking LEDs and pipes, the bell tower with louvres, an open belfry, a real bell, a gold spire cap | no | 24 x 42 x 36 m, 8-12k |
| 6 | **The city houses** (`cityHouse()`: 12 kinds, capsule / noodle / bodega / walk-up / model home / container / squat / dorm / arcade / pastel / bio-lab / pawn) and their shells | ~1,000 house boxes + most of the 3,668 `wall()` boxes and 308 `shell()` boxes: plank-textured walls, flat signs, box awnings, box AC units | **kit + one decision** (see below): dressing pieces fitted to each house (window frames and sills, door frames, awnings with valances, the neon shop signs as real sign boxes with tubes, fire escapes, balconies, roller doors, roof parapets with coping, the AC unit prop that exists), plus Blender facades per kind | no (kit) / small gameplay change (option B) | 7-18 m lots, 1-3k a kind |
| 7 | **The megacity in the haze** (`skylineHaze()`, render only) and the JankCorp megatower | 170 textured boxes + neon bands + ad boards round the horizon, a 420 m glass slab | **new kit**: 5-6 far tower types (setbacks, crowns, antennae, emissive window grids, neon bands) as instanced lod-only models, the megatower as a proper spire. Cheap, and it's in every single view | no | far, ~300 tris a tower |
| 8 | **Number Works** (`numberWorks()`): the factory hall (sawtooth roof), the 3 smokestacks (seen from anywhere), the green vats, pipe racks, the yard fence | brick boxes with hazard bands, rust boxes, chrome slabs | **new models**: a brick chimney with banding, ladder cages and a soot-black crown (x3, instanced), a riveted vat with a lid and gauges glowing green, a pipe rack with elbows and valves, the sawtooth-roof factory with north lights, a chain-link fence kit | no | stack 5 x 63 m 2k, vat 1.5k, hall 4-6k |
| 9 | **The crashed blimp** (crash site, north-east outside the wall) | 14 stacked pink boxes, a face picture, a box gondola | **new model**: the last delivery blimp nose-down in the dirt: a fabric envelope crumpled at the nose, ribs showing through rips, fins, the gondola torn off and lying beside it, a smiley still on its side, trailing mooring ropes, a crater | no | 46 x 18 x 18 m, 6-8k |
| 10 | **THEY / YOU / WE** (`word()`, Pronoun Park) | 66 toy-coloured boxes making pixel letters | **new model**: giant wooden alphabet-block letters, chunky glossy painted plastic letters with bevels, scuffs and a few stickers; built over the pixel grid so every step you climb is still there | no | 3 words, 1-2k a letter |
| 11 | **Neon Market Hall** (`marketHall()`): the 44 m hall, the two-level gallery, stairs, light strips, the NOODLE sign; the stall square outside | a brick shell, grid slabs, box rails | **new model** (arch): a market hall from real references (a steel roof truss with clerestory glazing, a brick shell with tall arched windows, the gallery with a mesh rail, real stairs, neon tube strips hung on chains, the NOODLE sign as tube letters) | no | 44 x 13 x 44 m, 8-10k |
| 12 | **The plastic orchard** (outer ring south) | ~500 trees, each a trunk box and two candy-coloured slab boxes | **new prop** (instanced, 4-5 variants): moulded plastic fruit trees: a seam down the trunk, a blobby glossy crown, plastic apples, a price tag, some still on their display stands | no | 3.5 x 4.5 m, 600 tris |
| 13 | **The sprawl's shacks** (outer ring west) | ~400 single boxes of cardboard / plywood / rust with a tilted slab roof | **kit** (instanced, fitted per shack): a tin-and-plywood shack set (corrugated walls, a sagging tarp roof weighed down with tyres, a door curtain, a stovepipe), a cardboard-box hut, a container shack | no | 3.5-6.5 m, 800-1,500 tris |
| 14 | **Slum towers** (`slumTower()`, Overdraft Heights, 4) | a textured box shell, box balconies, a box hut on the roof | **kit pieces**: balconies with railings and laundry, the roof shack, the vertical neon sign as a real blade sign (with #6's kit) | no | 14 x 14 x 20-30 m |
| 15 | **Solid city blocks + upper facades** (`block()`, `upper()`) | textured boxes with painted windows, box roof junk | **kit**: a facade kit (window bays, cornices, parapets with coping, drainpipes) shared with Skyline / Rooftop's tower bodies (their #3 / #4: build it once) | no | many |
| 16 | **Overhead cables, hanging signs, washing lines** over the narrow streets | 213 thin boxes and neon slabs | **new props**: sagging cable bundles, hanging neon blade signs on brackets, washing lines with clothes | no | small |
| 17 | **The plaza's metro kiosks** (4) and ad boards | glass-block boxes with a teal slab | **new prop**: a closed metro entrance (glass canopy, steel frame, stairs down to a shutter, a CLOSED SINCE '09 sign) | no | 4 x 3.4 x 3 m, 2k |
| 18 | **Park set** (Pronoun Park + the fountain's ring): benches, the bandstand, hedges, the quay's crane and bollards | wood boxes, white posts with stepped pink slabs | **new props**: a park bench (cast-iron ends, slats), a bandstand (cast-iron columns, a pink pagoda roof with a finial), a quay crane, mooring bollards | no | 1-4k each |
| 19 | **The farm** (outer ring north): barn, silo, hay, crop rows | a brick shell, a concrete box silo, gold boxes | **new models**: a gambrel barn, a corrugated silo with a cone top and ladder; the hay already has a prop (`p_hay`) the boxes could use | no | 3-5k |
| 20 | **Highway stubs** (east and west): ramp, deck, pillars, rebar | asphalt boxes, concrete columns | **new model**: a concrete overpass with a box-girder deck, hammerhead piers, expansion joints, a guardrail, snapped-off rebar at the end | no | 60 x 9 x 18 m |
| 21 | **The Liberal Lane arch** (`liberalArch()`) | 5 white boxes and a picture | **new prop**: a white picket gateway arch with the sign in a frame and a neon strip | no | 1k |
| 22 | **Canal + quay** (steps, the bed, reeds) | concrete boxes | **later**: quay edge with coping and ladders, reeds as a prop | no | |

## Option for the city houses (#6): needs the coordinator's / owner's call
The building pipeline (`public/js/archfield.js`) puts one Blender model over many copies only when every copy has
**exactly the same boxes**. Jankburg's houses get a random width and depth per lot, so no two match. Two ways:
- **A, dressing kit (no gameplay change):** keep the box walls, add instanced Blender dressing fitted to each house
  (frames, sills, awnings, signs, fire escapes, parapets). Cheap and safe; the walls themselves stay textured boxes.
- **B, fixed lot sizes (small gameplay change):** snap each kind to 2-3 sizes, so each size gets a full Blender house
  (real walls, windows, roofs) over identical boxes. Streets get re-packed (the layout shifts a little; spawns, loot and
  bot routes are regenerated by the same code), so it needs a walk test and a bot check.
I'll start with A (it helps either way) and come back to B if the owner wants it.

## Not Jankburg's own (for the coordinator)
- The **facade kit** for tall blocks (#15) overlaps Skyline and Rooftop's tower bodies: whoever builds it first, the
  others reuse it.
- The **ground** (dirt humps, the canal bed) is the Terrain session's.
- The **box clouds** and **cone mountains** on the horizon are global (`public/js/world.js`, `public/js/scenery.js`).
