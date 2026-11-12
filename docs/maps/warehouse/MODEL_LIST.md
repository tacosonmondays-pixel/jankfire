# Warehouse and Warehouse S&D: what still needs modelling

The walk-through (2026-11-12) was played at Too HD (jank 3) from every spawn, the S&D sites, the hall inside and out and
overhead, plus `tools/blender/inventory_maps.mjs` (on main d5dca9d7: Warehouse 579 boxes still drawn as boxes, S&D 551).
The pictures are in `walkthrough.jpg`, 4 a row, in this order:
- rows 1–3: Warehouse S&D: attackers' spawn, courtyard, defenders' spawn (the staff block), hall; overview, site A (x2),
  site B; trailer park, container yard
- rows 3–7: Warehouse: car park spawn, crane, truck dock, fence; gate spawn, guard booth, hall aisle, hall door;
  foreman's office, outside, overview (x2); shredder, site office, trailers, container yard

Already Blender models, so not on this list: the racking, forklifts, pallets, loaded pallets, crates, cardboard boxes,
barrels, shipping containers, jersey barriers, cones, the semis and trailers (their livery pictures stay pictures), the
staff cars, the excavator, the generator tower, streetlights and the trees outside.

What the walk-through showed: the props inside the hall look good, but everything they stand in is still code. The
hall (the middle of both maps, seen from every spawn) is a flat grey box with a blue lid. Inside it has brown plank
"rafters" and a striped dark-blue ceiling. The gantry cranes are three orange sticks. The fence is a dithered noise
texture on a slab. S&D's defenders spawn facing a flat magenta wall with painted-on window squares. Site B is plain
blue walls round a grey box.

The list is ranked by what players see most. Columns:
- **now:** what's there today.
- **plan:** what the model will be.
- **collision:** what happens to the boxes you bump into.
- **size:** the triangle budget.

Every model covers its own boxes, like the fort and the lighthouse on Islands: the boxes are tagged and hidden once
the model loads, and drawn again if the file is missing.

| # | What | Maps | Now | Plan | Collision | Size |
|---|---|---|---|---|---|---|
| 1 | **The hall**, the big distribution shed in the middle (walls, roof, rafters, lamps, door frames) | both | A grey corrugated box with a blue roof slab. Plank rafters, box lamps, door holes with nothing round them. | Arch model, one per map (`hall`, `hall_sd`), the full building: a precast concrete plinth with corrugated cladding over it in two tones, plus a polycarbonate clerestory strip in the window cuts, a parapet with coping, gutters and downpipes, and the company name. The roller doors rolled up into their drum boxes. The south dock doors get black dock seals, dock lights on arms and DOCK 1–4 numbers. The roof gets skylight strips, turbine vents and an AC unit. Inside: steel portal columns, yellow open-web trusses over the rafter boxes, high-bay pendant lamps on chains, white liner panels over the plinth. | Unchanged, so look-only. | 10–16k a map |
| 2 | **The staff block**, the building the defenders spawn behind | warehouse_sd | One magenta box, with window squares as dark decals. | A two-storey office block: a ribbon of real windows with mullions and spandrel panels, a glass entrance with a canopy and a JANK LOGISTICS sign, a parapet with rooftop plant, downpipes and a smoking shelter. | Unchanged. | 3–5k |
| 3 | **The perimeter**: chain-link fence, the shut sliding gate, light masts | both | A dithered fence texture on a slab, box posts, two thin box wires on top. Light masts are a box pole with a box lamp. | One model per map: galvanised chain-link (an alpha mesh you can see through), line posts with caps, a top rail and a tension wire, barbed wire on 45° arms, and a cantilever sliding gate with a KEEP OUT sign. The light masts become tapered poles with a head frame of four floodlights and a ladder. | Unchanged. | 4–6k a map |
| 4 | **The gantry cranes** (over the container yard; over site A on S&D) | both | Two orange box legs, a box beam, a box hook block. | A rail-mounted gantry crane: A-frame legs on sill beams and bogies on rails, a box girder with a walkway and handrail, a trolley with a driver's cab, cables down to a container spreader, hazard stripes and warning lights. | Unchanged (the legs stay the boxes). | 3–5k each |
| 5 | **Site B, the parcel shed**: the shed, the sorting belt, the sorter, the parcel cages | warehouse_sd | Blue box walls, a teal floor, a box belt with box parcels, a grey box sorter, grid boxes. | Inside: an insulated panel shed with a roller door, translucent roof lights and a B sign. A powered roller conveyor on legs with side guards, plus a sorter machine with a hopper, chute and control panel. The parcel cages become wire roll cages on castors. | Unchanged. | 5–8k |
| 6 | **The foreman's office** (2 floors in the hall corner; 1 floor mid-hall on S&D) | both | A magenta shell, with box stairs up to the roof. | An in-plant modular office: a steel frame with glazed upper walls, a steel stair with handrails up to the roof deck (railed), plus blinds and a WORLD'S OKAYEST FOREMAN mug in the window. | Unchanged. | 3–5k each |
| 7 | **Small buildings**: the guard booth (both), the dispatch booth (S&D) and the site office (Warehouse) | both | Teal and blue boxes with a red roof slab. | A gatehouse kiosk with wrap-round windows, a hip roof, a barrier arm and a pass hatch. The site office becomes a stacked portable cabin: ribbed walls, a door with steps, an AC box. | Unchanged. | 1.5–3k each |
| 8 | **Yard props**: dumpsters, tyre stacks | both | A green box with a lid slab, stacks of flat boxes. | Real props: a front-load dumpster with lids, fork pockets and a bin-company sticker; a stack of truck tyres. | Unchanged. | 0.6–1k each |
| 9 | **The shredder pit's edge**: the hazard rails and the pit walls | warehouse | Hazard-striped boxes, rust slabs going down 47 m. | A steel guard rail with hazard paint, a grated lip, a warning sign on a post, and riveted rusty pit walls that fade into the dark. The drums stay the client's code. | Unchanged. | 1–2k |
| 10 | **Machinery outside the fence**: bulldozers, cement mixers, a road roller, a pipe stack, gravel piles | both (look-only) | Box machines. | Kit props like the excavator: a crawler dozer, a mixer truck with a striped drum, a twin-drum roller, a stack of concrete pipes, plus soft gravel and dirt mounds. | None (render-only). | 4–6k all |
| 11 | **S&D concrete walls**: site A's dock wall, the corner blocks, the bin store | warehouse_sd | Concrete and wood slabs. | Precast panels with lifting eyes and a stencilled bay number, and a timber-slatted bin store with wheelie bins inside. | Unchanged. | 1–2k |

Not on this list (other lanes): the ground, asphalt and painted lines (the terrain lane), the far mountains and city
(backdrops), the trailer liveries and the billboards (pictures on purpose).

Order of work: 1 (both halls, one PR), then 2, 3, 4, 5, then 6–7 together, then the props (8–11). One landmark or a
small batch per branch (`claude/map-warehouse-<thing>`) and draft PR, from the latest main. Each gets:
- the asset gate (0 errors)
- the tests
- `tools/arch/gamehash.mjs` showing it is look-only (Warehouse `bb66bb4f9792` / S&D `94051abab26e` boxes on main)
- before/after pictures in Too HD plus one Potato
- the frame-rate cost
- a patch-notes line in the PR
