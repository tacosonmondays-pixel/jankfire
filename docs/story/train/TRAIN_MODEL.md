# The train set: the model

Dale's works train, the Under-Hill Loop's tunnel, the dead commuter train and the tunnel mouth, for `m06_tickets_please`
(TICKETS, PLEASE). This page is about the models: what is in the files, what the fight and later scenes can rely on,
how they are wired into the fight, and how to rebuild them. The design is [TRAIN.md](../TRAIN.md) §4 and §5, the fight
is [FIGHT.md](FIGHT.md), the boss that chases this train is [REVENUE_PROTECTION_MODEL.md](REVENUE_PROTECTION_MODEL.md).

| file | what | size |
|---|---|---|
| `public/models/story/rp_train.glb` | the four cars, the eight cover pieces, the flatbed's torn end, far versions | SIZE_TRAIN |
| `public/models/story/rp_tunnel.glb` | the tunnel kit (pieces that tile along z) and the tunnel mouth | SIZE_TUNNEL |
| `public/models/story/rp_commuter.glb` | one carriage of the dead commuter train, its torn end, a far version | SIZE_COMMUTER |
| `public/models/story/rp_train.parts.json` | every part's box, the table it was built to, the markers | SIZE_PARTS |
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
TRI_TABLE

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
SHEETS

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
QA_TEXT

## Weak spots
WEAK
