# Platform and Platform P&D: what still needs modelling

The walk-through (2026-11-12) was played at Too HD from both TDM spawns, both P&D spawns, the P&D sites, the middle
and from high overhead, plus `tools/blender/inventory_maps.mjs`. Pictures: `walkthrough.jpg` (Platform, then Platform
P&D).

Platform is GLUG OIL's rig in the North Sea: the living quarters and helideck (east), the drill floor under the derrick
(west), the process deck between them, the cellar deck under it all, THE SNACK RUN tied up below. P&D puts the same rig
north, a bridge support platform in the middle and SLURP OIL's riser platform south.

**What's already a model:** the crates and the shipping containers (the shared `p_crate` / `p_container` props).
That's it. Everything
else is code boxes: 2,035 on Platform and 2,674 on P&D (`docs/blender/AUDIT_PVP_MAPS.md`). There is no landmark model
on either map yet.

**What reads badly today:**
- The derrick, the thing you see from every corner, is four stacked box legs with flat red "truss" panels between
  them. From the deck it looks like a red box chimney, not a lattice tower.
- The handrails and stairs are everywhere (1,237 boxes on Platform, 1,752 on P&D). They're square yellow sticks with
  posts every 2 m, and the stair treads are solid grey slabs.
- The living quarters are a white box with holes. The lifeboats are two orange bricks. The helideck is a flat slab
  with a code helicopter on it.
- The wellhead christmas trees (P&D site B) are red pillars with a crossbar and cubes for baubles.
- The jacket under the rig is square yellow columns, and the sea under it is flat.

The list is ranked by what players see most: landmarks and objectives first, then buildings, then props and scenery.
Columns:
- **now:** what's there today.
- **plan:** what the model will be.
- **collision:** what happens to the boxes you bump into.
- **size:** the triangle budget.

Every model covers its own boxes, like the Battle Island radio mast and the Islands lighthouse: the boxes are tagged
and hidden once the model loads, and drawn again if the file is missing. Collision stays boxes unless the row says
otherwise.

| # | What | Maps | Now | Plan | Collision | Size |
|---|---|---|---|---|---|---|
| 1 | **The derrick** (`drillSide()`: the 30 m tower, crown, monkey board, top drive, racked pipe) | both (P&D: site A sits under it) | Stacked red box legs, flat `trussred` panels for the lattice, a red slab crown. Reads as a box chimney. | **New model, hero landmark.** A real land-rig derrick: four tapered tube legs, K-bracing and girts on every face, the V-door window on the east face, a crown block with its sheave cluster and a gin pole, the travelling block and top drive hanging on the drill line, the monkey board as a real fingerboard with racked stands of drill pipe, the GLUG OIL board, an obstruction beacon. Red and white candy paint, chrome sheaves, rust streaks. | Unchanged (look-only). The legs, the monkey board and its rails stay the boxes you grapple and stand on. | 8–12k |
| 2 | **The drill floor** (rest of `drillSide()`: the substructure, drawworks, doghouse, BOP, mud pumps and tanks, the V-door ramp) | both (P&D: site A) | Red box legs, a blue box doghouse, a box BOP, two box mud pumps, a flat plate deck with rails. | **New model** under the derrick: a box-girder substructure with diagonal braces, the drawworks with its drum and brake, the driller's doghouse (windows, A/C, chair inside), a stacked BOP (annular on top, rams with their hydraulics), triplex mud pumps, mud tanks with agitators, the rotary table, the catwalk and V-door ramp. | Unchanged (look-only). | 6–9k |
| 3 | **Rig stairs and handrails** (`rigStair()` ×12, `rail()` ×10: 1,237 boxes on Platform, 1,752 on P&D) | both (every deck, everywhere you walk) | Square yellow box rails with posts every 2.2 m. Stair treads are solid slabs. | **One model per map** drawing every rail and stair: round tube handrails with a knee rail and a toe board, posts every 1.5 m, real open grating treads with nosings, side stringers, landing gratings. Yellow safety paint, worn where hands go. | Unchanged (look-only). The top rail stays the physics. | 8–14k a map |
| 4 | **Wellhead christmas trees** (`xmasTree()` ×6 a map) | both (P&D: site B) | A red box pillar, a crossbar, cubes for baubles, flat tinsel strips. | **New prop**, instanced: a real production tree (master valves, the cross, wing valves with actuators, the swab valve and tree cap, the choke, gauges) dressed for christmas with round baubles, sagging tinsel, a star and fairy lights. | Unchanged (the pillar and crossbar boxes). | 1.2–1.8k each |
| 5 | **The living quarters and helideck** (`livingQuarters()` + its walls, the lifeboats, the helideck and its truss) | both (TDM attackers' spawn, P&D crew spawn) | A white box with window holes, a box stair tower, orange bricks for lifeboats, a flat helideck slab. | **New model** over the boxes: ribbed white cladding panels, framed windows, a GLUG OIL sign with lights, a real stair tower with landings, enclosed orange lifeboats (TEMPSC) in their davits, the helideck on its truss with a perimeter net and lights. Galley furniture stays the game's boxes. | Unchanged (look-only). | 10–14k |
| 6 | **The process deck**: separators (`separator()` ×2 / ×1) and the pipe rack (`pipeRack()`) | both (the middle of Platform TDM, cover everywhere) | Octagon box vessels, box saddles, pipes as long boxes, a box frame. | **New props:** a horizontal separator vessel (round shell, dished heads, saddles, nozzles with flanges, a manway with a davit, a level gauge, a ladder and platform); the pipe rack as real pipes (flanges, a valve now and then), steel frames and a cable tray. | Unchanged. | 2–3k each separator, 4–6k the rack |
| 7 | **The pedestal cranes** (`pedCrane()` ×2 / ×1) | both | A yellow box pedestal, a white box cab, a `truss` box boom, a box hook. | **New prop:** an offshore pedestal crane: round pedestal with its ladder, slew ring, cab with windows, A-frame and lattice boom with its pendants and wires, hook block. The walkable boom stays a box under it. | Unchanged. | 3–4k each |
| 8 | **THE SNACK RUN** (`snackRun()`: the supply boat, the boat landing and its stair) | both | A red box hull, a white box bridge, flat bulwarks. | **New model:** a platform supply vessel: flared bow, the bridge with wrap-round windows, the funnel and mast, the cargo rails, tyre fenders, mooring lines; the boat landing on the jacket. | Unchanged. | 6–9k |
| 9 | **The jacket and the sea under the rig** (`jacket()`, render only) | both (×1 on Platform, ×3 on P&D) | Square yellow columns, flat braces, `foam` squares at the waterline. | **New model:** tubular legs with K-braces, node cans, barnacles and weed at the waterline, the riser clamps and caissons, a ring of foam where the swell hits. | None (render only). | 3–5k a jacket |
| 10 | **The compressor house** (`compressorHouse()`) | both | Blue box walls with cuts, box compressors. | **New model:** a blue clad module with louvres, a roller shutter, a rooftop exhaust, two compressor skids inside. | Unchanged. | 2–3k |
| 11 | **The flare boom** | platform | A box stair, `truss` boxes, box flames. | **New model:** a lattice flare boom with its catwalk, the flare tip with a wind shield and pilot, the flame as a glowing shape. | Unchanged. | 2–3k |
| 12 | **P&D only: the bridges, the riser module, the junction hut, THE TOAD** (`trussBridge()`, `pipeBridge()`) | platform_sd | Box decks, `truss` panels, box valve boxes. | **New models:** a box-truss bridge with diagonal members and a roof frame, a pipe bridge with real pipes and supports, the riser module's clad box with risers down to the sea, THE TOAD as a real personnel basket (the rope cone, the rubber ring). | Unchanged. | 3–5k each bridge |
| 13 | **Small deck props**: pumps, the pig launcher, cargo baskets, the gas bottle quad, the drill-pipe stacks, the muster sign | both | Boxes. | **New props:** a pump skid, a pig launcher (a barrel with its door and valves), a cargo basket, a bottle quad, pipe stacks with end caps. | Unchanged. | 0.5–1.5k each |
| 14 | **The far rigs and the tanker** (`farRig()`, render only) | both | Boxes on the horizon. | A far-LOD rig and tanker silhouette, with the flare glowing. | None. | 1–2k each |

**Not on this list:** the parked helicopter (`chopper()`) is shared with Skyline's helipads and there's already a
Blender news helicopter (`p_heli`). Whoever wires `chopper()` to it does both maps at once, so it belongs to the Skyline
session (or a later shared pass), not here.

**Order of work:** 1 and 2 together (the derrick and its drill floor are one place), then 4 (the trees: small, and it's
a P&D site), then 3, 5, 6 and 7, then the rest. One landmark or small batch per branch and draft PR, from the latest
main. Each gets:
- the asset gate (0 errors)
- the tests (`node --test tests/*.test.mjs tests/story/*.test.mjs`)
- `tools/arch/gamehash.mjs` showing it is look-only, unless the plan above says otherwise
- before/after pictures in Too HD plus one Potato
- the frame-rate cost (draw calls and triangles, `tools/blender/perf_props.cjs`)
- a patch-notes line in the PR
