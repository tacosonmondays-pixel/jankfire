# The train set: the model

Dale's works train, the Under-Hill Loop's tunnel, the dead commuter train and the tunnel mouth, for `m06_tickets_please`
(TICKETS, PLEASE). This page is about the models: what is in the files, what the fight and later scenes can rely on,
how they are wired into the fight, and how to rebuild them. The design is [TRAIN.md](../TRAIN.md) §4 and §5, the fight
is [FIGHT.md](FIGHT.md), the boss that chases this train is [REVENUE_PROTECTION_MODEL.md](REVENUE_PROTECTION_MODEL.md).

| file | what | size |
|---|---|---|
| `public/models/story/rp_train.glb` | the four cars, the eight cover pieces, the flatbed's torn end, far versions | 2.03 MB |
| `public/models/story/rp_tunnel.glb` | the tunnel kit (pieces that tile along z) and the tunnel mouth | 405 KB |
| `public/models/story/rp_commuter.glb` | one carriage of the dead commuter train, its torn end, a far version | 394 KB |
| `public/models/story/rp_train.parts.json` | every part's box, the table it was built to, the markers | 12 KB |
| `public/js/story/trainset.js` | loads them and dresses the fight's stand-ins with them | |
| `tools/blender/make_rp_train.py` + `rptrain_cars.py`, `rptrain_tex.py`, `rptunnel.py`, `rpcommuter.py`, `trainkit.py` | the build (Blender 5.2) | |
| `tools/blender/rp_train_shots.cjs`, `rp_train_shots.html` | the sheets in the game's renderer, and the load check | |
| `tests/story/trainmodel.test.mjs` | the models measured against the size table | |

None of the `.glb` is in `public/models/story/index.json`: that list is the story props the city loads. `trainset.js`
fetches them with its own loader path when you are on the train, like the boss.

Everything is original: a works railway of no particular company, no real livery, logo or locomotive class. The real
kinds of thing it is built from are named at the top of each build script.

## The size table comes first
The room collides with boxes built from `shared/story/train.js` (`HW`, `CARS`, `COVER`). The models are only looks, so
they are built to that table and tested against it (`tests/story/trainmodel.test.mjs` reads the vertices out of the
`.glb`):

| | the table | the model |
|---|---|---|
| deck width | `HW` 2.1 (4.2 m) | every car's deck edge is at ±2.1; nothing reaches past ±2.16 (stake pockets) |
| rear wagon | z 0.2 – 9.2, deck 1.0, rail 0.75 | deck boards at 1.000, the rail's top at 1.750 on three sides, open to the flatbed |
| flatbed | z 9.8 – 19.8, deck 1.3 | boards at 1.300 from edge to edge |
| tool van | z 20.4 – 27.4, deck 1.3, roof 3.45 from z 22.8, 2.0 under it, 4 steps 1.1 wide | four steps of 0.5375 × 0.6 on the left, 1.1 wide, from the car's end; posts 0.14 square at the table's four spots; the roof's underside at 3.300, its top at 3.450 with a 45 mm lip at the edges |
| loco | z 28.0 – 33.0, body ±1.7 to 2.2, cab to 3.6 over z 28.3 – 30.6 | bonnet 2.2 high, cab roof 3.6 at its crown; running boards and handrails out to ±2.0 (inside `HW`) |
| cover | eight boxes | eight `cover_*` nodes, each inside its box (±3 cm) and filling at least 93% of it on every axis |
| the middle lane | clear | nothing above the deck within 0.5 m of the centre line; nothing under the van's roof more than 0.5 m in from the sides except the two cover pieces |

The buffers, couplings and lamps reach into the 0.6 m gaps between cars. Rails are at x = ±0.75 with their top at
y = 0.215 (the room's own rail boxes, 0.14 high, are inside the kit's rails); wheels stand on that.

Sizes that the table made awkward are under "Weak spots".

## Space
Metres, the arena's own space: x across, y up from the track bed, **z from the back of the train (0) to the loco**.
The bore's axis is at x = 0, y = 3.13 (`ARENA.cy`), its radius 4.6. Looking back at the boss (-z), +x is on your right.

## Parts (`rp_train.glb`)
```
rp_train
  car_wagon   wagon_body · wagon_tail · wagon_coupling · cover_wagon_0 · cover_wagon_1 · wagon_lod*
  car_flat    flat_body · flat_end · flat_end_bitten* · flat_van_coupling · cover_flat_0..3 · flat_lod*
  car_van     van_body · van_lamp · van_loco_coupling · cover_van_0 · cover_van_1 · van_lod*
  car_loco    loco_body · loco_glass · loco_headlamp · loco_cablamp · loco_lod*
```
`*` = hidden: visible in the file (glTF has no hidden flag), `jf_hidden: 1` in its extras, listed in the root's `jf`
(`hidden`) and marked `"hidden": true` in the parts file. Hide them on load.

| node | what | notes |
|---|---|---|
| `car_*` | an empty per car | move or hide it and the whole car goes, with what stands on it |
| `wagon_body` | the low open wagon: boards, three drop doors a side, **the rail** (one fat yellow tube round three sides on posts), a mid rail and a kick board at the back (MIND THE GAP, by hand), the tail lamp's case, rope, a shovel and a keying hammer in clips, a paraffin can | two axles on W-irons and leaf springs |
| `wagon_tail` | the tail lamp's lit lens | its own material (`tr_tail`) |
| `wagon_coupling` | the cranked bar to the flatbed, the fall plate you walk over, two safety chains | child of `car_wagon`: it goes with the wagon |
| `flat_body` | the flatbed: boards, stake pockets, lashing rings, the fridge's two chains with lever binders, chocks round the crates, a stack of spare boards, the yellow edge lines | truss rods underneath |
| `flat_end` | the flatbed's back, whole: headstock, coupler pocket with its pin, the ledge the fall plate lies on | hide when the wagon is bitten off |
| `flat_end_bitten` | the same end after the first lunge: the headstock in three folded pieces, the pocket torn open with the bar's stump in it, a chain down to the sleepers, the boards' ends chewed into splinters, the raves peeled out, two sets of four finger tracks dragged off the deck | hidden. Takes nothing of the deck away (the room still has all of it) |
| `van_body` | the tool van: four posts, a boarded roof under tarred canvas with a low lip in hazard stripes (so you can see its edge from up there), NO STANDING ON ROOF stencilled on its back beam for everyone on the flatbed to read while people stand on it, the steps (solid under them, as in the room: locker doors on the lane side), a tool board on the back of the steps, rolled side sheets under the roof's edges, a rack of long tools behind the bench, a ladder, fire buckets, the hand brake, lockers under the floor, the flood lamp's mast | |
| `van_lamp` | the flood's lit head and the hurricane lamp on the tool board | `tr_worklamp`. The fight's spot light is at this lamp (`markers.work_lamp`) |
| `van_loco_coupling` | the bar to the loco, chains, the low tray between them | the room has a floor there at 0.5 (you count as off the train on it) |
| `loco_body` | "more of a tractor, but it's on rails": outside frames, fly cranks and red coupling rods, sprung buffers and wasp-striped beams at both ends, a bonnet with louvred doors (one replaced with a plate in primer), a radiator, two head lamps (the left one's glass is broken), an exhaust stack with its flap, an air cleaner, handrails; the cab with a door at the back (a hand-painted 4), marker lamps, a low arc roof with a vent and twin horns; inside: Dale's seat with a folded rug, the desk, a pedestal brake valve with a brass handle, the throttle, three gauges, a tartan flask, a copper kettle on a primus, a mug, a fire extinguisher, his hi-vis on a hook | UNDER-HILL LOOP ENG DEPT in ghost lettering on the cab sides, TRACTOR and the 4 over it, CREW 2 corrected to 9 |
| `loco_glass` | the cab's panes | `tr_glass`, blended. One side sash is slid back and its neighbour boarded with a bit of crate |
| `loco_headlamp` | the lens of the head lamp that works | `tr_headlamp` |
| `loco_cablamp` | a bulkhead lamp in the cab roof, lit | `tr_worklamp` |
| `cover_<car>_<n>` | one per line of `COVER`, in the table's order within each car | **origin = the middle of its foot**: put it at that line's `(x, deck, z)`. Crates (boards on battens, rope handles, stencils; the tall one strapped), the fridge (`kind: "fridge"`: a fridge-freezer with its doors to the lane, a strap round it, a note that says JACK), the bench (`tool_chest`: red drawers to the lane, a vice, a tray of tools), a cable drum on a cradle (`cable_drum`) |
| `<car>_lod` | the car and what stands on it as a few boxes | 200 – 350 triangles each. Hide the body, the covers and the small parts with it |

Materials: `tr_atlas` (one 512 px atlas with a roughness / metal map: every painted, planked and steel thing),
`tr_glass`, and three that glow, each its own material so the game can drive it: `tr_headlamp`, `tr_tail`,
`tr_worklamp`. Vertex colours (COLOR_0) are baked AO times a tint. Every mesh node is one material: one draw call.

## The tunnel kit (`rp_tunnel.glb`)
Every piece is authored where it goes in the bore, starting at z = 0 and running toward +z: clone it and move it along z.

| node | length | what |
|---|---|---|
| `tk_lining` | 6 m | the brick barrel (9.2 m bore, down to the track bed) with one proud ring of headers at its start. Soot along the crown, damp and green low down, lime runs and rust stains in the vertex colours; both ends match, so it tiles |
| `tk_lining_b` | 6 m | the same with other stains, a cast drain pipe down the right wall and a 61 in whitewash |
| `tk_niche` | 6 m | the same with a refuge in the left wall: concrete sill and lintel, a lineside telephone, the notice ☺ CORP screwed up when they shut the line (LINE CLOSED / HAVE A NICE DAY), a lamp somebody left |
| `tk_track` | 6 m | ballast bed and shoulders, eight sleepers, the two rails on baseplates, cess paving out to the walls, concrete cable troughing down the left (one lid gone, one slid off), a drain |
| `tk_track_far` | 6 m | the same in 66 triangles for far down the tunnel |
| `tk_cables` | 6 m | two brackets on the right wall, three cables sagging between them |
| `tk_bulbs` | 12 m | the string: the wire on three insulators, one drop with an enamel shade. The bulb itself is not in it |
| `tk_bulb_lit`, `tk_bulb_dead` | | the bulb at that drop: `tk_bulb_on` (emissive) and `tk_bulb_off`. Same origin as `tk_bulbs`: draw one or the other |
| `tk_phone`, `tk_marker`, `tk_signal` | | on their own origins (the phone's back plate; the foot of the quarter-mile post; the foot of the signal's post). The signal is a dark two-aspect colour light with a ladder, looking back down the line |
| `tp_portal` | | the tunnel mouth for the ending: z = 0 is its face, the tunnel is behind it. A ring of headers in a stone face, pilasters, raking wing walls, a string course and coping, a date stone (UNDER HILL 1899), and the first 12 m of the viaduct's parapets and deck |

Materials: `tk_brick` (a 128 px tile, 1.5 m along the tunnel, 14 times round the barrel), `tk_atlas` (256 px, everything
else), `tk_bulb_on`, `tk_bulb_off`.

Look pass 2 (after seeing it in the fight): the first brick was a clean, bright red and the room lit it evenly, so dead
bulbs did not read and the pale mask sat on a wall of its own colour. The brick is now sixty years of steam: reds gone
to brown, about one in four a blue-black engineering brick, soot on the brick tops, dark joints, the whole upper half of
the barrel blacked (the crown most), far fewer lime specks and none of them white (white single pixels sparkle at a
distance with nearest filtering). In the game the kit takes a quarter of the studio reflection the train does, so the
bulbs' own lights make the pools.

**The second track.** TRAIN.md has "a second track swings in alongside" with the dead train on it. In the fight's bore
that cannot be: the floor is 6.7 m wide and the train is 4.2 m of it. `tk_track` is one line of track; a twin-track
length is two bores side by side (the kit laid twice, `tk_track` moved across), which is how the commuter sheet shows
it. So the dead train is not drawn in the fight: it belongs to the wider length of tunnel in `c6_mind_the_gap`.

## The dead commuter train (`rp_commuter.glb`)
One carriage in its own space: the origin on the track bed under its middle, 20 m from coupling to coupling along z,
2.84 m wide, rails at x = ±0.75.

| node | what |
|---|---|
| `cm_car` | the carriage: white, a cyan waist band, nine bays a side each with a hinged door standing open (a ☺ on every one, looking back down the line), quarter-lights, full-width benches facing each other in a bold check, luggage rails, coats on hooks, a briefcase, a newspaper, a hat, an umbrella, a child's shoe in a doorway, a flap table with a cup that is a mound of moss now, straps, two bogies |
| `cm_end` | its +z end wall, whole (the -z one is part of `cm_car`). A carriage = `cm_car` + `cm_end` + `cm_glass` |
| `cm_end_torn` | that end burst from inside: the wall in petals bent outward, bare metal on their backs, the headstock pushed out, a buffer hanging. Hidden. The last carriage = `cm_car` + `cm_end_torn` + `cm_glass` |
| `cm_glass` | every pane (`cm_glass`, blended). A few are missing |
| `cm_lod` | the carriage as 130 triangles: one painted cell a side, the doors still standing out of it. Hidden |

## The parts file
`rp_train.parts.json`, arena space, metres.

- `table`: `HW`, `cars`, `cover` as they were when it was built (the test fails if `shared/story/train.js` has moved
  on: rebuild), `rail_y`, `gauge`.
- `cars`: per car its nodes, z range and deck.
- `parts[]`: `name`, `centre`, `half`, `group` (its `car_*`), `tris`, `materials`, and where they apply `hidden`,
  `pivot`, `cover` (its line in `COVER`), `kind`, `box`.
- `states.bitten`: what to hide and show after the first lunge.
- `markers`: `crew` (the three spots from `CREW`), `back_rail` (the line along the top of the back rail, and its
  radius), `rail_sides`, `couplings` (three: the bar's two ends, **the pin** Lumps pulls, the node), `cab_seat`,
  `brake_handle`, `flask`, `kettle`, `cab_lamp`, `headlamp` (position and direction), `headlamp_dead`, `tail_lamp`,
  `work_lamp`, `van_lantern`, `fridge` (its node, where it stands, `lean`: where Jack goes down against it, `door`),
  `handtruck` (where `s_handtruck.glb` goes: leaning on the fridge's far side), `van_roof`, `van_steps`.
- `tunnel`: the kit's pieces and lengths, the niche, the bulb's place, the track's numbers, the portal's.
- `commuter`: the carriage's numbers and parts.

## Triangles and draw calls
Budgets were: the four cars 45 - 60k with far versions, a tunnel length under 1.5k, a carriage under 6k (600 far),
every file under about 4 MB, few materials. The three files are 2.81 MB together.

| | triangles | far version | draw calls (meshes shown) |
|---|---|---|---|
| rear wagon (with its 2 crates, coupling, tail lamp) | 8,336 | 304 | 5 |
| flatbed (with 4 cover pieces, both couplings) | 8,692 | 206 | 7 |
| tool van (with the bench and the cable drum) | 8,964 | 280 | 5 |
| loco | 9,482 | 354 | 4 |
| **the four cars** | **35,474** | 1,144 | 21 |
| of which the eight cover pieces | 3,470 | | |
| `flat_end_bitten` (hidden until the first lunge) | 1,194 | | (+0: it swaps with `flat_end`) |
| tunnel: `tk_lining` / `tk_lining_b` / `tk_niche` | 720 / 848 / 852 | | 1 / 2 / 2 (instanced) |
| tunnel: `tk_track` / `tk_track_far` / `tk_cables` | 590 / 62 / 426 | | 1 each (instanced) |
| tunnel: `tk_bulbs` + a bulb / `tk_phone` / `tk_marker` / `tk_signal` | 340 + 36 / 142 / 80 / 366 | | 1 each (instanced) |
| `tp_portal` (the mouth, the viaduct's first 12 m) | 1,522 | | 2 |
| dead carriage (`cm_car` + `cm_end` + `cm_glass`) | 5,882 | 130 (`cm_lod`) | 3 (1 far) |
| the last carriage (`cm_end_torn` in place of `cm_end`) | 6,346 | | 3 |

The cars come in under the 45 - 60k the brief allowed, and the headroom was left unspent on purpose: at play distance
they read (see the before / after pictures), and the room's frame is already about 220k triangles before the train
(the boss, its arms, the crew). The far versions are in the file but the
fight never needs them (the train is always within 35 m of you); they are for scenes that see the train from far off.

In the fight (headless Too HD, 1280 x 720, `renderer.info` summed over one frame, at the same staged moment with the models and with the old boxes switched back on):
from the rear wagon looking back, **412 draw calls and 257,651 triangles with the models, 429 and 219,331 with the
boxes**; from the van's roof, 549 and 307,653 against 564 and 249,251 (every render pass of one frame: the boss, its
arms, the crew, the viewmodel). So the models cost 38 - 58k triangles more and about 15 draw calls *fewer*: the old
bore drew each of its rings and bulbs on its own. The tunnel kit is instanced, so 30 lengths of tunnel cost the same
dozen draw calls as one. The bulbs' glows are one `Points`.

## How it is wired (`trainset.js`, `trainfight.js`)
- `trainfight.js` still builds the stand-in train and tunnel from the table's boxes (one group a car). When you are on
  the train it asks `trainset.js` for the files; when they land, each car's boxes are hidden and its `car_*` node goes
  into that car's group, so everything the fight already did to a group (the wagon thrown back into the dark when it is
  bitten off, its return on a retry) happens to the model. A file that never comes leaves the boxes.
- Cover pieces are placed from `COVER` as it is today, and each car is moved to its `z0` if the table has moved since
  the build.
- The tunnel kit is instanced along the bore (`InstancedMesh` per piece and material) and scrolled at the fight's
  speed. The layout repeats every 96 m: a refuge every fourth length, the drain-pipe length every fourth, a marker and
  a signal once each. Track detail and cables are only drawn within about 40 m of the train. The bulbs are the fight's
  own bulbs: where it has one lit the kit shows `tk_bulb_lit`, where the mask has passed, `tk_bulb_dead`. Two dark
  discs close the tunnel's ends (the room's end walls are brick).
- Each lit bulb also glows: one `Points` cloud with a soft halo for every bulb that is on, moved with the scroll and
  shortened as the mask puts them out (no light comes or goes, so no shader is rebuilt). The tail lamp, the work flood,
  the van's lantern and the working head lamp get a halo each.
- After the first lunge `flat_end` is swapped for `flat_end_bitten`; on a retry or when you leave, it is whole again.
- Pallet Jack's hand truck (`s_handtruck.glb`, the story prop) is fetched on the same path and stood behind the fridge at
  `markers.handtruck`, its toe plate toward it. It is optional: no file, no truck.
- Everything is built once and kept between visits. `?trainbox=1` keeps the boxes (for a before / after picture);
  `JF_TRAIN.model.show(false)` and `JF_TRAIN.set.kit.show(false)` switch back to them on the same frame.
- Nothing in the rules changed: no size, no server code, nothing about arms or the boss.

## Sheets
All in `docs/story/train/`. In the game's renderer (three.js, the treatment `trainset.js` gives the files), made by
`node tools/blender/rp_train_shots.cjs`:

| file | what |
|---|---|
| `rp_train_game_turn.jpg` | the train from behind (the boss's side) and the front, side and plan against the 9.2 m bore and a 1.8 m figure, the far versions, the bitten flatbed |
| `rp_train_game_detail.jpg` | each car close, the back rail and tail lamp, the chained fridge, under the van's roof, the roof, the cab, the head lamps, the tool board, the steps |
| `rp_train_game_tunnel.jpg` | 60 m of kit with the fight's own lights: all bulbs lit, bulbs going out, the refuge, the track, the train in it |
| `rp_train_game_commuter.jpg` | the dead carriage, inside, the coffee, the torn last carriage, eight far carriages, the tunnel mouth |

In the real fight (`?story=1&storytest=1&train=1&storydev=1`, staged with `bossdev`), **before** (main's box stand-ins
and the old bore, switched back on in the same frame) and **after** (the models), left and right:

| file | what |
|---|---|
| `train_ba_1_rear_wagon.jpg` | from the rear wagon looking back at the mask, THE GAP 18 m (the best one for the tunnel) |
| `train_ba_2_van_roof.jpg` | from the tool van's roof down the train |
| `train_ba_3_grabber.jpg` | a Grabber's hand over the wagon's back rail (left), Jack's stand-in at the rail, a LOOP STORES crate |
| `train_ba_4_bitten.jpg` | phase 3, after the first lunge: the wagon gone, the mask at the flatbed's back |
| `train_ba_5_bitten_end.jpg` | the flatbed's torn end after the bite (`flat_end_bitten`) |
| `train_ba_6_van_back.jpg` | the tool van from the flatbed: NO STANDING ON ROOF, the bench, the steps and their rail, the cab's back door (the best one for the train) |
| `train_ba_7_roof_forward.jpg` | from the van's roof forward over the loco: the lit bulbs ahead glow (main showed the room's brick end wall here) |
| `train_ba_8_hand_truck.jpg` | Jack's hand truck behind the chained fridge, Lumps hauling, the tall crate strapped |

The Blender turnaround is `tools/blender/sheets/rp_train_turnaround.jpg` (before look pass 2).

## Rebuild
```
blender52 -b -P tools/blender/make_rp_train.py                     # all three .glb, the parts file, the Blender sheets
blender52 -b -P tools/blender/make_rp_train.py -- --no-sheet       # the files only (about 20 s)
blender52 -b -P tools/blender/make_rp_train.py -- --no-sheet --no-export --no-ao --qa   # the asset-QA gate on every group
blender52 -b -P tools/blender/make_rp_train.py -- --only=train --no-ao --no-export --preview=/tmp/p --views=wagon,cab   # a quick look
node tools/blender/rp_train_shots.cjs                               # the sheets in the game's renderer; fails if a part is missing
node --test tests/story/trainmodel.test.mjs                         # the models against the table
```
Flags: `--only=train,tunnel,commuter`, `--sheet=turnaround,cars,...`, `--stats`, `--qa-warn`, `--zf=60` (how many
z-fight places to list). The size table is read out of `shared/story/train.js` with node at build time, so changing a
size there and rebuilding moves the model with it.

## QA
The asset-QA gate (`-- --qa`, the `blender-asset-qa` checks: z-fighting at 1 mm, floating parts, inside-out and
inconsistent normals, collapsed faces, n-gons) passes on all 23 groups after look pass 2: the four cars, their far
versions, the flatbed with its torn end, every tunnel piece, the portal, the carriage, the last carriage and the far
carriage. One accepted warning: the loco's working head lamp lens is inside its housing (`QA_ENCLOSED`), as meant.
Earlier fixes are in the geometry, not hidden: flanges under gussets, stake pockets on their flanges, posts and masts on
their feet, the racked tools standing on the deck.

`node --test tests/story/trainmodel.test.mjs` (10 tests) measures the export: every car inside `HW` and its z range,
the decks at the table's heights with the middle lane clear, the wagon's rail at the grip spots, the van's four steps,
four posts, 2 m headroom and flat roof, each cover piece inside and filling its `COVER` box with its origin at the
middle of its foot, the bitten end taking nothing of the deck, every part the parts file names a node in its `.glb`
(train, tunnel and commuter), the markers, the budgets. `rp_train_shots.cjs` fails if a named part is missing.

## Weak spots
- **The second track** is not a piece of its own: in the fight's 9.2 m bore there is no room for one, so a twin-track
  length is the kit laid twice (see above). The dead commuter train is therefore not in the fight; it is for
  `c6_mind_the_gap`, which needs its own wider set laid from these pieces.
- **The tunnel mouth at dusk** is modelled (portal, wing walls, the viaduct's first span) but has no sky, valley or
  lighting: that belongs to the ending's scene.
- **The last carriage** is 6.3k triangles with its torn end (the budget was 6k a carriage); there is one of it.
- **The deck shines at grazing angles** looking forward from the wagon: the fight's spot lamp on the van points back
  down the train, so the flatbed's boards catch it edge-on. It is the room's light, not the boards (they are 0.86 rough).
- **The front of the train is dark** from the van's roof looking forward: the room has three bulb lights, all kept near
  the back of the train where the fight is. The lit bulbs ahead glow, the walls there do not. A head lamp light would
  fix it at the cost of one more light on every surface.
- **Jack's hand truck** stands upright behind the fridge; it has no collision box (nor does anything that is not in
  `COVER`), so you can walk through it. The parts file's `lean` for it is for his idle pose and is not applied.
- **Not seen in motion at a real frame rate**: the headless browser draws a frame every few seconds. The scroll, the
  bulbs going out and the glows were checked frame by frame, not watched.
- **No co-op test**: the models are only looks, so another player sees the same files, but two people on the roof
  were not tried.
