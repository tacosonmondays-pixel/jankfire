# What is still built from code (art lane inventory, 2026-11-10)

Goal from the owner: everything Blender-made. Buildings, props, real staircases, vehicles, natural rock instead of
blocky "Minecraft" terrain, characters, gear, the menu. **Look only:** collision stays boxes and the gameplay hash per
map (`tools/arch/gamehash.mjs`) must not change. Ground reshaping (hills, dips) is the terrain lane's job, not this one.

How this was counted:
- **Maps:** `node tools/blender/inventory_maps.mjs` on `claude/blender-pipeline` (PR #71) after merging main. It stamps
  every box with the function that added it and skips boxes a Blender prop already draws. Full per-map tables:
  [`INVENTORY_MAPS.md`](INVENTORY_MAPS.md). Vis 5 = in your face all match, 1 = far away or tiny.
- **Everything else** (characters, guns, gear, menus): a read through `public/js/` against the files in `public/models/`.

## Where we are

| | Blender today | Still code |
|---|---|---|
| Weapons | 42 base guns + 27 skins (`w_*.glb`, 95 files) | Blood Cross, 3 skins |
| Projectiles | 16 (`pj_*.glb`) | tennis ball, nails, marbles |
| Gear and streaks | 32 (`x_*.glb`) | grapple hooks, shield bubble, black hole, medkit pickups, supply crates |
| Map props | 45 kinds in PR #71 (not merged yet), 10 on main | ~6,400 boxes of one-off set pieces |
| Buildings | 3 look-test models in PR #115 (not merged, waiting on the look OK) | ~45,000 boxes |
| Natural terrain | none | ~2,200 boxes: rocks, dunes, sandbars, the volcano, Skull Rock |
| Characters | OVERDUE cast (11) and crowd | the player mannequin, all outfits, hats, hair, hands, zombies |
| Backdrops | none | mountains, cliffs, far city, sky, clouds |

Box totals on the 22 maps once #71 is in: props 6,410, architecture 44,985, terrain 2,210, on purpose 65.

## The ranking (most visible first)

### 1. Buildings and stairs: ~45,000 boxes. The biggest thing on screen in every map.
Waiting on the PS1 / Cruelty Squad look OK (PR #115) before mass conversion. Top groups:

| What | Builder | Maps | Boxes | Vis |
|---|---|---|---|---|
| walls with door / window cuts | `wall()` map.js:58 | 20 maps | 9,702 | 5 |
| rig stairs (open grating flights) | `rigStair()` map.js:562 | Platform, Platform P&D | 1,410 | 5 |
| stair bridges between towers | `stairBridge()` map.js:1040 | Rooftop, Skyline (+P&D) | 1,347 | 5 |
| Jankburg outer ring, city houses, city wall | jankburg.js:672 / 135 / 611 | Jankburg | 2,938 | 5 |
| switchback stairs | `stairs()` map.js:88 | 14 maps | 1,397 | 4 |
| stair flights | `flight()` map.js:3021 | Islands (+P&D) | 306 | 4 |
| deck railings | `rail()` map.js:544 | Platform (+P&D) | 1,579 | 4 |
| facade dressing (shutters, balconies) | `dressFacades()` map.js:3877 | Bazaar P&D | 1,449 | 4 |
| floor slabs and building shells | `slab()` / `shell()` map.js:78 / 112 | 17 maps | 1,544 | 4 |
| suburb houses, fences, facade houses | `home()` / `woodFence()` / `facadeHouse()` | Suburb (+P&D) | 931 | 4 |
| living quarters, drilling side, boat landing | map.js:605 / 672 / 735 | Platform (+P&D) | 624 | 4 |
| frontier town, town wall, adobe huts | map.js:2428 / 2611 / 2566 | Desert (+P&D) | 753 | 4 |
| souk arcades, domes, caravanserai | map.js:3831 / 3843 / 3992 | Bazaar, Skyline | 409 | 4 |
| penthouse, cathedral, Number Works | map.js:1067, jankburg.js:449 / 511 | Rooftop, Jankburg | 271 | 4 |
| office / tenement towers | `tower()` map.js:201 | Rooftop, Skyline, Jankburg | 717 | 3 |
| rope walkways, piers, rope bridge, trestle, fort | map.js:3057 / 2530 / 2517 / 3239 | Islands, Desert | 837 | 3 |
| far city below and beyond (render only) | `cityBeyond()` / `streetLevel()` map.js:363 / 269 | Rooftop, Skyline | 16,100 | 4-5 |
| megacity in the haze (render only) | `skylineHaze()` jankburg.js:715 | Jankburg | 444 | 4 |

**Stairs:** every staircase in the game comes from five builders (`stairs`, `rigStair`, `stairBridge`, `flight`, plus
the ones inside `shell()` / `home()`), 4,460+ boxes. One "real stairs" kit (treads, risers, stringers, rails sitting
exactly on the collision steps, as PR #115 already does inside the Suburb houses) covers all of them.

### 2. Natural terrain: ~2,200 boxes. The "Minecraft" look the owner called out.
No look decision needed beyond one test sheet: rock is rock. **This is where the art lane starts.**

| What | Builder | Maps | Boxes | Vis |
|---|---|---|---|---|
| sandbars | `sandbar()` map.js:3043 | Islands (+P&D) | 141 | 4 |
| dunes | `dune()` map.js:2413 | Desert, Bazaar (+P&D) | 616 | 3 |
| rock formations | `rocks()` map.js:2416 | Desert, Bazaar (+P&D) | 157 | 3 |
| boulders | `boulders()` map.js:2590, `boulder()` map.js:4565 | Desert, Forest | 78 | 3 |
| Skull Rock | `skullRock()` map.js:3264 | Islands (+P&D) | 66 | 3 |
| the volcano, Mount Kaboom | `volcano()` map.js:3109 | Islands (+P&D) | 56 | 3 |
| islets, reefs, loose rocks round the islands | `isle()` / `reef()` + sections | Islands (+P&D) | ~120 | 2-3 |
| the mesa, the canyon walls, the ravine, the oasis rocks | map.js:2727 / 2606 / 2776 / 2757 | Desert (+P&D) | ~130 | 3 |
| standing stones | map.js:4642 | Scary Forest | 15 | 3 |
| gravel piles | `gravelPile()` map.js:2021 | Warehouse (+P&D) | 32 | 2 |
| scrub, sagebrush, dirt patches (look only) | map.js:2769 / 2972 / 4070 | Desert, Bazaar | 275 | 2-3 |
| cliffs under each map's plateau | `scenery.js`:83 | most outdoor maps | dozens | 3 |

Note: the volcano itself is still stacked basalt boxes with a rock texture (three slab terraces, a rim, five box
boulders). Read "like on the volcano" as: every natural feature should look like a real formation; the volcano gets
the same treatment and becomes the showpiece.

Not this lane: the flat ground slabs, roads, trails and painted lines (`groundHoles()`, `horizon()`, floor sections).
Those are the terrain lane's hills-and-dips work.

### 3. Props and set pieces: ~6,400 boxes left after PR #71
PR #71 turns 45 repeated prop kinds into instanced Blender models. What is left is mostly one-offs:

| What | Builder | Maps | Boxes | Vis |
|---|---|---|---|---|
| the Grand Bazaar hall, the Grand Hall | map.js:3951 / 4126 | Bazaar (+P&D) | 451 | 4 |
| cables, hanging neon, washing lines | jankburg.js:369, `cityDress()` map.js:320 | Jankburg, Rooftop, Skyline | 376 | 3-4 |
| park, playground, corner lots, junk outside | map.js:1782 / 1840 / 1535 | Suburb (+P&D) | 531 | 3-4 |
| pool deck, cabanas, DJ | map.js:1166 | Rooftop | 121 | 4 |
| radio mast yard, road, property stakes | map.js:4728 / 4759 / 4786 | Scary Forest | 350 | 4 |
| warehouse hall insides | map.js:2057 / 2244 | Warehouse (+P&D) | 215 | 4 |
| back lots, mine, Main Street | map.js:2660 / 2727 / 2623 | Desert (+P&D) | 388 | 4 |
| giant toy-block letters, park | jankburg.js:572 / 583 | Jankburg | 119 | 3-4 |
| the whole CRATE map | map.js:500 | Crate | 57 | 3 |
| oil rig kit: christmas trees, cranes, separators, pipe racks | map.js:725 / 711 / 579 / 591 | Platform (+P&D) | ~330 | 3 |
| rooftop sets: greenhouse, mini golf, cola can | map.js:3575 / 3553 / 3520 | Skyline (+P&D) | 178 | 3 |
| tiki bar, shipwreck | map.js:3132 / 3166 | Islands (+P&D) | 148 | 3 |
| windpumps, water tanks, mine headframe | map.js:2446 / 2456 / 2464 | Desert (+P&D) | 178 | 3 |

### 4. Vehicles
| What | Where | Status |
|---|---|---|
| traffic cars, buses, trucks (8 types) | `cars.js`:354 | Blender in PR #71 |
| forklift, bus, cart, number balls | round 1 | Blender on main, no far LOD yet |
| the train: engine, cars, wheels, track | `train()` / `wheels()` / `rails()` map.js:2475 | code, 416 boxes, Desert |
| parked helicopters | `chopper()` map.js:3510 | code, 90 boxes, Platform + Skyline |
| the shipwreck, rowboats | `wreck()` map.js:3166 | code, Islands |
| royale drop blimp | `royale.js`:126 | code, ~19 parts |
| walk-in bus and box truck, `semi()` trucks | Suburb, Warehouse | code (known limit of #71) |
| OVERDUE sofa-car | `story/drive.js`:38 | code; `s_sofacar.glb` exists but isn't wired into driving |
| far tanker and far oil rigs (render only) | `farRig()` map.js:793 | code |

### 5. Backdrops and sky
| What | Where | Size |
|---|---|---|
| far mountain ring with snow caps | `scenery.js`:61 | 20-40 flat cones |
| theme dressing: hills, mesas, smokestacks, isles, pine ridges, city horizon | `scenery.js`:106-176 | hundreds of primitives, merged |
| sky dome, sun cube, clouds, floating void rocks | `world.js`:390 | ~50 |

The cone mountains show in almost every outdoor screenshot. Cheap to replace: a handful of far meshes per theme.

### 6. Characters
| What | Where | Status |
|---|---|---|
| the player / bot mannequin (body, egg head, limbs) | `models.js`:1724 `buildCharacter` | code, ~80 parts |
| hair, tops, bottoms, 23 accessories, cat wear, 10 gun hats | `models.js`:1444-1782, `catwear.js`, `skins.js`:169 | code |
| first-person hands | `hands.js`:74 | code, ~260 tris a hand |
| zombies | `remote.js`:72 | code: a recoloured mannequin, no zombie body of its own |
| P&D armour, helmet, defuse kit | `econ3d.js`:129-245 | code |
| lore NPCs, cats, the Tall Guy From HR, the Backrooms figure, the royale goblin | `lorenpcs.js`, `lorecats.js`, `hrguy.js`, `backrooms.js`, `royale.js`:803 | code |
| OVERDUE cast and crowd | `story/looks.js`, `city/crowd.js` | Blender (face rig stays code on purpose) |
| OVERDUE generic NPCs, implants | `story/looks.js`:274, `story/body.js`:191 | code |

The mannequin's built-in jank (the tilt, the wrong knee) is house style: a Blender version keeps it. The zombies and
gameplay lanes are changing bodies right now (dismemberment, body sliders), so characters wait until they land.

### 7. Weapons, gear and mode objects still in code
| What | Where | Note |
|---|---|---|
| Blood Cross finger gun (+ shadow skin) | `models.js`:1198 | a hand: goes with the hands work |
| skins: staple gun, ball machine, basket | `primmodels.js`:177-209 | |
| grapple hooks (8 looks) | `grapple.js`:204 | ropes stay code |
| shield bubble, black hole, medkit pickups | `main.js`:1453, `models.js`:1924, `econ3d.js`:306 | their `x_*.glb` exist but only draw the icons |
| royale supply crates, umbrella, loot (can, plate, vest, fridge, ammo bucket) | `royale.js`:177-225, 789 | |
| P&D bomb, Tags-mode tags | `objective.js`:48 / 63 | |
| zombies: power-up drops, mystery crate, power switch, cola machine, lamps, perk pictures | `zmextra.js`:161, `zombies.js`:159-205, `zmloadout.js`:83 | boards and the Cheat Machine are Blender already |
| jail cage, shredder pit drums, spray range wall | `secondaries.js`:112, `shredpit.js`:27, `sprayrange.js`:30 | |
| OVERDUE props with no model yet (13) | `city/propcode.js` | vendo, punch clock, till, gun rack, dentist chair... |

### 8. Menus and 3D UI
| What | Where | Status |
|---|---|---|
| home menu hero (your character + gun) | `preview.js`:120 | character code, gun Blender |
| containers (crate, duffel, box) and the opening burst | `crate3d.js`:12 | code, ~30 parts |
| mode pictures, medals, end-screen props | `modeart.js`:53-161 | code |
| home nav icons (trophy, cog, book, cat) | `navicons.js`:12 | code |
| locker plinth | `preview.js`:187 | code |

### 9. Stays code (effects, not models)
Muzzle flashes, tracers, shells, particles, explosions, kill effects, fireworks, beams, liquids, fire, the royale zone
wall, grapple ropes, lasso rope, soap bubbles, sprays, name tags, light pools. Also on purpose: livery pictures and the
gameplay side skirts on trucks (65 boxes, group X in the map tables).

## Work order
1. **Rock kit (now, no look decision needed):** boulders, rock formations, the volcano, Skull Rock, standing stones,
   islets and reefs, then dunes and sandbars as soft sand meshes. One test sheet first (Desert rocks + the volcano),
   owner OK, then the rest. Each mesh wraps its collision boxes so nothing you can stand on moves.
2. **Finish PR #71** (props round 4): remaining vehicle sheets, then ready for the owner.
3. **Backdrops:** real far mountains, mesas and ridges instead of cones.
4. **Real stairs kit** for the five stair builders: needs the look OK, since stairs belong to buildings.
5. **Buildings, map by map** after the look OK on PR #115: Suburb and Skyline first (already started), then Desert,
   Bazaar, Platform, Rooftop, Islands, Warehouse, Forest, Backrooms, Dead Mall, Jankburg last (the biggest).
6. **One-off set pieces and remaining vehicles** (train, helicopters, shipwreck, blimp) alongside each map.
7. **Leftover weapons and gear** (Shredder, Scales, grapple hooks, pickups, zombies objects, containers).
8. **Characters and hands** once the zombies and gameplay lanes' body changes have landed.

## Open questions for the owner
- The PS1 / Cruelty Squad look (PR #115 sheets in `docs/arch-look-test/`, PR #83): OK to use it for all buildings?
  And should the existing glossy props and guns be re-baked to match, or stay glossy?
