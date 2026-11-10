# Map box inventory (generated)

Made by `node tools/blender/inventory_maps.mjs` on `claude/blender-pipeline` (PR #71) after merging main, 2026-11-10.
It counts what each map would still draw as boxes once #71 is in. Vis 5 = you look at it all match, 1 = far away or tiny.
Groups: A props, B architecture, C terrain / natural, X boxes on purpose. Summary and plan: `INVENTORY.md`.

## A. Props and set pieces

#### Crate (`crate`): 57 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the whole CRATE map (crates, toys, the toy face) | shared/map.js:500 (section) | 1 | 57 | 3 | 550-1500 |

#### Platform (`platform`): 266 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| wellhead christmas trees | `xmasTree()` shared/map.js:725 | 1 | 84 | 3 | 850-2000 |
| pedestal cranes | `pedCrane()` shared/map.js:711 | 2 | 33 | 3 | 350-800 |
| separator vessels | `separator()` shared/map.js:579 | 1 | 30 | 3 | 300-700 |
| the cellar deck (-7.2): open grating, the wellbay slot (railed: the sea's down there), the christmas trees, th | shared/map.js:822 (section) | 1 | 24 | 3 | 250-600 |
| pipe racks | `pipeRack()` shared/map.js:591 | 1 | 24 | 3 | 250-600 |
| the laydown deck (south): containers (a crate up onto them), cargo baskets, gas bottles | shared/map.js:857 (section) | 1 | 16 | 3 | 150-400 |
| helicopters (parked) | `chopper()` shared/map.js:3510 | 1 | 15 | 3 | 150-350 |
| the flare boom (out west from the south-west corner): a catwalk up to the tip, the flare on fire | shared/map.js:865 (section) | 1 | 12 | 3 | 100-300 |
| the main deck (0): holes for the three stairs down, rails round its edge (open where the flare boom goes off) | shared/map.js:815 (section) | 1 | 24 (look only) | 2 | 250-600 |
| the sea, the far rigs, a tanker going by | shared/map.js:809 (section) | 1 | 4 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Platform (P&D) (`platform_sd`): 259 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| wellhead christmas trees | `xmasTree()` shared/map.js:725 | 1 | 84 | 3 | 850-2000 |
| the rig (north, x -36..36, z -70..-22): the main deck (holes for the stairs down), its cellar deck (the wellba | shared/map.js:926 (section) | 1 | 45 | 3 | 450-1000 |
| the riser platform (south, x -24..24, z 38..70): the raiders' spawn behind the riser module, a stair down each | shared/map.js:982 (section) | 1 | 31 | 3 | 300-750 |
| pipe racks | `pipeRack()` shared/map.js:591 | 1 | 24 | 3 | 250-600 |
| the bridge support platform (the middle, x -22..22, z 0..18): a deck at each level, a stair down each side, a | shared/map.js:967 (section) | 1 | 19 | 3 | 200-450 |
| pedestal cranes | `pedCrane()` shared/map.js:711 | 1 | 17 | 3 | 150-400 |
| helicopters (parked) | `chopper()` shared/map.js:3510 | 1 | 15 | 2 | 150-350 |
| separator vessels | `separator()` shared/map.js:579 | 1 | 15 | 2 | 150-350 |
| on the rig: the drilling side (A), the living quarters (the crew's spawn) and helideck, the pipe rack, a | shared/map.js:946 (section) | 1 | 5 | 2 | 50-100 |
| bomb site boards (A / B) | `siteBoard()` shared/map.js:2165 | 2 | 4 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Rooftop (`rooftop`): 214 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the pool deck (z [6, 28]): a pool to wade, loungers, four cabanas, the DJ, palms, party lights | shared/map.js:1166 (section) | 1 | 121 | 4 | 1000-3000 |
| the two towers: x [-58, -30] and [30, 58], z [-18, 18], roofs at 0. bridges land in the gaps on their inner si | shared/map.js:1121 (section) | 1 | 57 | 4 | 550-1500 |
| the party block: x [-22, 22], z [-28, 28], its roof at L0, the pool cut into it | shared/map.js:1146 (section) | 1 | 9 | 3 | 90-200 |
| neon crowns, facade ads, cables with hanging ads | `cityDress()` shared/map.js:320 | 1 | 21 (look only) | 2 | 200-500 |
| jump pads: tower -> the penthouse roof, the deck and the north end -> back up the towers | shared/map.js:1187 (section) | 1 | 6 | 2 | 60-150 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Rooftop (P&D) (`rooftop_sd`): 172 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the party block: the penthouse (no door upstairs, its north wall solid: the spawns stay out of each other's | shared/map.js:1253 (section) | 1 | 86 | 3 | 850-2000 |
| A, the hotel's roof: the towel hut in the middle, HOTEL 4 HOURS, a hot tub, loungers under umbrellas | shared/map.js:1282 (section) | 1 | 18 | 3 | 200-450 |
| HVAC units | `hvac()` shared/map.js:1309 | 4 | 16 | 3 | 150-400 |
| neon crowns, facade ads, cables with hanging ads | `cityDress()` shared/map.js:320 | 1 | 21 (look only) | 2 | 200-500 |
| planters | `planter()` shared/map.js:1310 | 2 | 12 | 2 | 100-300 |
| B, the bank's roof: its machine room in the middle (cover), the JANK BANK sign, the AC farm, a water tower | shared/map.js:1274 (section) | 1 | 10 | 2 | 100-250 |
| billboards (rooftop frames) | `billboard()` shared/map.js:194 | 2 | 5 | 2 | 50-100 |
| bomb site boards (A / B) | `siteBoard()` shared/map.js:2165 | 2 | 4 (look only) | 1 | 40-100 |

#### Suburb (`suburb`): 430 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the four corner lots (each past the end of a row of houses, between the street and the back lane) | shared/map.js:1840 (section) | 1 | 156 | 4 | 1500-3500 |
| the park: the playground (west), the founder's plaza (middle), the pond with a footbridge and the gazebo (east | shared/map.js:1782 (section) | 1 | 100 | 4 | 1000-2500 |
| outside the suburb: power poles, junk, tyre piles | `suburbOutside()` shared/map.js:1535 | 1 | 138 (look only) | 3 | 1500-3500 |
| the houses: five a side, all open (a trampoline in every yard throws you onto the roof) | shared/map.js:1762 (section) | 1 | 17 | 3 | 150-400 |
| west end (team 1): the corner store, its car park, the bus stop | shared/map.js:1814 (section) | 1 | 13 | 3 | 150-300 |
| pipe stacks | `pipeStack()` shared/map.js:2017 | 1 | 6 | 2 | 60-150 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Suburb (P&D) (`suburb_sd`): 245 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| outside the suburb: power poles, junk, tyre piles | `suburbOutside()` shared/map.js:1535 | 1 | 137 (look only) | 3 | 1500-3500 |
| B: the MEGA-MART EXPRESS (inside: aisles, the tills, the fridges, the stockroom), its car park | shared/map.js:1678 (section) | 1 | 39 | 3 | 400-950 |
| the main street (on west through the trees to nowhere), sidewalks, the cul-de-sac at the east end | shared/map.js:1591 (section) | 1 | 36 | 3 | 350-850 |
| NORTH: the back alley, A long | shared/map.js:1640 (section) | 1 | 14 | 2 | 150-350 |
| ATTACKERS' SPAWN: the bus stop at the entrance. the bus they came on screens the street | shared/map.js:1629 (section) | 1 | 9 | 2 | 90-200 |
| the house rows: north (facing south) and south (facing north). the middle north house and the east south house | shared/map.js:1615 (section) | 1 | 6 | 2 | 60-150 |
| bomb site boards (A / B) | `siteBoard()` shared/map.js:2165 | 2 | 4 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Warehouse (`warehouse`): 249 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the hall: doors on every side (the west and east ones off the same line), racking in a grid of aisles | shared/map.js:2057 (section) | 1 | 115 | 4 | 1000-3000 |
| warehouse racking | `rack()` shared/map.js:1912 | 3 | 24 | 3 | 250-600 |
| south: the truck dock. two semis backed up beside the dock doors, a row of trailers further out | shared/map.js:2104 (section) | 1 | 18 | 3 | 200-450 |
| the fence (the gate's shut), the world outside, light masts | shared/map.js:2050 (section) | 1 | 13 | 3 | 150-300 |
| cement mixer trucks | `mixerTruck()` shared/map.js:1996 | 1 | 28 (look only) | 2 | 300-650 |
| bulldozers | `bulldozer()` shared/map.js:1988 | 2 | 22 (look only) | 2 | 200-550 |
| road rollers | `roller()` shared/map.js:2003 | 1 | 11 (look only) | 2 | 100-250 |
| north: the container yard. stacks in two staggered rows (a little maze), a crane over the middle | shared/map.js:2092 (section) | 1 | 6 | 2 | 60-150 |
| pipe stacks | `pipeStack()` shared/map.js:2017 | 1 | 6 (look only) | 2 | 60-150 |
| east: the staff car park (team 2). the site office, cars | shared/map.js:2120 (section) | 1 | 3 | 2 | 40-100 |
| ad boards | `adBoard()` shared/map.js:1495 | 2 | 3 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 2 | 1 | |

#### Warehouse (P&D) (`warehouse_sd`): 244 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| MID: the hall | shared/map.js:2244 (section) | 1 | 100 | 3 | 1000-2500 |
| B: the parcel shed (inside, cyan) | shared/map.js:2308 (section) | 1 | 19 | 3 | 200-450 |
| cement mixer trucks | `mixerTruck()` shared/map.js:1996 | 1 | 28 (look only) | 2 | 300-650 |
| bulldozers | `bulldozer()` shared/map.js:1988 | 2 | 22 (look only) | 2 | 200-550 |
| the fence (the gate in the west side is shut behind the attackers' truck) | shared/map.js:2224 (section) | 1 | 15 | 2 | 150-350 |
| SOUTH: the trailer park, B long. three rows of trailers to weave through, the B yard at the end | shared/map.js:2325 (section) | 1 | 15 | 2 | 150-350 |
| A: the container dock (outside, red) | shared/map.js:2276 (section) | 1 | 11 | 2 | 100-250 |
| road rollers | `roller()` shared/map.js:2003 | 1 | 11 (look only) | 2 | 100-250 |
| warehouse racking | `rack()` shared/map.js:1912 | 1 | 10 | 2 | 100-250 |
| pipe stacks | `pipeStack()` shared/map.js:2017 | 1 | 6 (look only) | 1 | 60-150 |
| bomb site boards (A / B) | `siteBoard()` shared/map.js:2165 | 2 | 4 (look only) | 1 | 40-100 |
| ad boards | `adBoard()` shared/map.js:1495 | 2 | 3 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 2 | 1 | |

#### Desert (`desert`): 624 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the north back lots: the corral, the blacksmith, the outhouses, the mine's rail spur and its loading dock | shared/map.js:2660 (section) | 1 | 87 | 4 | 850-2000 |
| the mine: the mesa (a tunnel west to east into it, a side chamber with the shaft, the headframe on top) | shared/map.js:2727 (section) | 1 | 70 | 4 | 700-1500 |
| WEST BANK: Main Street, from the west gate to the stone bridge | shared/map.js:2623 (section) | 1 | 56 | 4 | 550-1500 |
| railway track | `rails()` shared/map.js:2476 | 1 | 166 (look only) | 3 | 1500-4000 |
| train wheels | `wheels()` shared/map.js:2477 | 5 | 50 (look only) | 3 | 500-1000 |
| the open ground between it all: the old fort (NW), the mission (SW), adobe huts, the canyon's rims | shared/map.js:2685 (section) | 1 | 49 | 3 | 500-1000 |
| windpumps | `windpump()` shared/map.js:2446 | 2 | 42 | 3 | 400-1000 |
| the train (engine, cars) | `train()` shared/map.js:2475 | 1 | 32 | 3 | 300-750 |
| water tanks on stilts | `waterTank()` shared/map.js:2456 | 2 | 26 | 3 | 250-600 |
| mine headframe | `headframe()` shared/map.js:2464 | 1 | 25 | 3 | 250-600 |
| EAST BANK: Mine Square (the assay office, the mine company's offices, the well, stalls, the founder's cart) | shared/map.js:2718 (section) | 1 | 13 | 3 | 150-300 |
| the depot: the railway north-south past the mesa, the train stopped at the platform, the station, a water tank | shared/map.js:2745 (section) | 1 | 5 | 2 | 50-100 |
| the desert round the town (render-only): dunes, rock formations, a caravan camped outside the east gate, more  | shared/map.js:2786 (section) | 1 | 3 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Desert (P&D) (`desert_sd`): 654 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| B: the depot. the payroll train stopped at the platform (its nose to the rope bridge), the station behind the | shared/map.js:2957 (section) | 1 | 94 | 3 | 950-2500 |
| A: the mine head. the mesa's the north edge: the mine's in it (in at the mouth, along the gallery behind the r | shared/map.js:2933 (section) | 1 | 90 | 3 | 900-2000 |
| railway track | `rails()` shared/map.js:2476 | 1 | 86 (look only) | 3 | 850-2000 |
| the north back lots: the corral, the blacksmith, the outhouses, the rail spur out to the trestle and its dock | shared/map.js:2867 (section) | 1 | 85 | 3 | 850-2000 |
| EAST BANK. Mine Square (mid): the well, the founder's cart; the assay office (north) and the mining company (s | shared/map.js:2909 (section) | 1 | 50 | 3 | 500-1000 |
| the south back lots: the church and its bell tower, the cemetery, a wagon that didn't make it | shared/map.js:2880 (section) | 1 | 46 | 3 | 450-1000 |
| water tanks on stilts | `waterTank()` shared/map.js:2456 | 3 | 39 | 3 | 400-950 |
| WEST BANK. the stage stop (the bandits' spawn) inside the shut gate; the stage office across the end of the st | shared/map.js:2839 (section) | 1 | 32 | 3 | 300-750 |
| the train (engine, cars) | `train()` shared/map.js:2475 | 1 | 32 | 3 | 300-750 |
| mine headframe | `headframe()` shared/map.js:2464 | 1 | 25 | 3 | 250-600 |
| windpumps | `windpump()` shared/map.js:2446 | 1 | 21 | 3 | 200-500 |
| train wheels | `wheels()` shared/map.js:2477 | 5 | 50 (look only) | 2 | 500-1000 |
| bomb site boards (A / B) | `siteBoard()` shared/map.js:2165 | 2 | 4 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Islands (`islands`): 301 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the ways off it: the rope bridge north (a rock to rest on halfway), the pier east (the bait shack halfway), | shared/map.js:3314 (section) | 1 | 109 | 4 | 1000-2500 |
| C, Volcano Island (x -28..28, z -24..24): Mount Kaboom, the tiki village on the south beach, jungle round the  | shared/map.js:3297 (section) | 1 | 49 | 3 | 500-1000 |
| the shipwreck (the Soggy Biscuit) | `wreck()` shared/map.js:3166 | 1 | 46 | 3 | 450-1000 |
| the tiki bar | `tikiBar()` shared/map.js:3132 | 1 | 28 | 3 | 300-650 |
| sun loungers | `lounger()` shared/map.js:3090 | 1 | 20 | 3 | 200-500 |
| the big tiki head | `bigTiki()` shared/map.js:3142 | 1 | 9 | 3 | 90-200 |
| cannons | `cannon()` shared/map.js:3073 | 3 | 35 | 2 | 350-850 |
| surf school boards and rack | `surfSchool()` shared/map.js:3150 | 1 | 5 (look only) | 2 | 50-100 |
| (1 more bits of 1-2 boxes) | | | 2 | 1 | |

#### Islands (P&D) (`islands_sd`): 152 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the shipwreck (the Soggy Biscuit) | `wreck()` shared/map.js:3166 | 1 | 46 | 3 | 450-1000 |
| the tiki bar | `tikiBar()` shared/map.js:3132 | 1 | 28 | 3 | 300-650 |
| sun loungers | `lounger()` shared/map.js:3090 | 2 | 16 | 3 | 150-400 |
| cannons | `cannon()` shared/map.js:3073 | 2 | 28 | 2 | 300-650 |
| the big tiki head | `bigTiki()` shared/map.js:3142 | 1 | 9 | 2 | 90-200 |
| C, Volcano Island (x -21..21, z -28..6): Mount Kaboom between the spawns | shared/map.js:3398 (section) | 1 | 6 | 2 | 60-150 |
| W, the tiki bar's islet (x -60..-36, z -36..-12); E, the beach huts' (x 36..60, z -36..-12) | shared/map.js:3414 (section) | 1 | 6 | 2 | 60-150 |
| S, Skull Rock (x -16..16, z 20..50): the tour group's beach, their boats pulled up on it | shared/map.js:3406 (section) | 1 | 4 | 2 | 40-100 |
| surf school boards and rack | `surfSchool()` shared/map.js:3150 | 1 | 5 (look only) | 1 | 50-100 |
| bomb site boards (A / B) | `siteBoard()` shared/map.js:2165 | 2 | 4 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 2 | 1 | |

#### Skyline (`skyline`): 354 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| neon crowns, facade ads, cables with hanging ads | `cityDress()` shared/map.js:320 | 1 | 103 (look only) | 3 | 1000-2500 |
| the rooftop greenhouse / pond | `skyGreen()` shared/map.js:3575 | 1 | 33 | 3 | 350-800 |
| helicopters (parked) | `chopper()` shared/map.js:3510 | 2 | 30 | 3 | 300-700 |
| the rooftop mini golf | `skyPutt()` shared/map.js:3553 | 1 | 30 | 3 | 300-700 |
| the giant cola can / sign rooftop | `skyCola()` shared/map.js:3520 | 1 | 26 | 3 | 250-600 |
| grapple bait: window washers' platforms on the towers' faces, gold blocks hanging over the gaps | shared/map.js:3655 (section) | 1 | 22 | 3 | 200-550 |
| the rooftop building site | `skyBuild()` shared/map.js:3565 | 1 | 20 | 3 | 200-500 |
| the news rooftop (van, dish, lights) | `skyNews()` shared/map.js:3542 | 1 | 19 | 3 | 200-450 |
| C, the Spire: the hub deck round its glass shaft (five floors of windows, stairs inside, a sniper's nest on to | shared/map.js:3638 (section) | 1 | 18 | 3 | 200-450 |
| the rooftop garden | `skyGarden()` shared/map.js:3531 | 1 | 18 | 3 | 200-450 |
| tower crane | `crane()` shared/map.js:3498 | 1 | 17 | 3 | 150-400 |
| the observatory roof | `skyObs()` shared/map.js:3588 | 1 | 8 | 3 | 80-200 |
| the helipad heli | `skyHeli()` shared/map.js:3598 | 1 | 7 | 3 | 70-150 |
| billboards (rooftop frames) | `billboard()` shared/map.js:194 | 2 | 3 | 2 | 40-100 |

#### Skyline (P&D) (`skyline_sd`): 264 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the set pieces | shared/map.js:3737 (section) | 1 | 47 | 3 | 450-1000 |
| the rooftop greenhouse / pond | `skyGreen()` shared/map.js:3575 | 1 | 33 | 3 | 350-800 |
| helicopters (parked) | `chopper()` shared/map.js:3510 | 2 | 30 | 3 | 300-700 |
| the rooftop mini golf | `skyPutt()` shared/map.js:3553 | 1 | 30 | 3 | 300-700 |
| the giant cola can / sign rooftop | `skyCola()` shared/map.js:3520 | 1 | 26 | 3 | 250-600 |
| the news rooftop (van, dish, lights) | `skyNews()` shared/map.js:3542 | 1 | 19 | 3 | 200-450 |
| the rooftop garden | `skyGarden()` shared/map.js:3531 | 1 | 18 | 3 | 200-450 |
| neon crowns, facade ads, cables with hanging ads | `cityDress()` shared/map.js:320 | 1 | 18 (look only) | 2 | 200-450 |
| the set pieces | shared/map.js:3731 (section) | 1 | 12 | 2 | 100-300 |
| the links | shared/map.js:3720 (section) | 1 | 8 | 2 | 80-200 |
| the observatory roof | `skyObs()` shared/map.js:3588 | 1 | 8 | 2 | 80-200 |
| the helipad heli | `skyHeli()` shared/map.js:3598 | 1 | 7 | 2 | 70-150 |
| billboards (rooftop frames) | `billboard()` shared/map.js:194 | 2 | 3 | 2 | 40-100 |
| bomb site boards (A / B) | `siteBoard()` shared/map.js:2165 | 4 | 5 (look only) | 1 | 50-100 |

#### Bazaar (`bazaar`): 431 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| THE GRAND BAZAAR: the covered hall in the middle | shared/map.js:3951 (section) | 1 | 308 | 4 | 3000-7500 |
| hanging rugs and lanterns on lines | `hanging()` shared/map.js:3866 | 2 | 36 | 3 | 350-850 |
| NW: the spice market (a square with a shop on each side, open at the corners), sacks, cones of spice, lanterns | shared/map.js:4019 (section) | 1 | 32 | 3 | 300-750 |
| SE: the potters (two kilns, stacks of pots, the pottery shop), houses | shared/map.js:4047 (section) | 1 | 15 | 3 | 150-350 |
| market stall leftovers (rugs, goods) | `stall()` shared/map.js:2361 | 1 | 11 | 3 | 100-250 |
| SW: the tea house (cushions on its roof terrace), houses, a garden, the canal behind | shared/map.js:4040 (section) | 1 | 7 | 3 | 70-150 |
| lamp towers | `lampTower()` shared/map.js:3849 | 1 | 16 | 2 | 150-400 |
| NE: the carpet yard (carpets drying on frames, rolls stacked, a plank bridge over it from roof to roof) | shared/map.js:4030 (section) | 1 | 6 | 2 | 60-150 |

#### Bazaar (P&D) (`bazaar_sd`): 194 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| MID: the Grand Hall (covered, its doors at opposite corners, three stall islands down the middle, side doors | shared/map.js:4126 (section) | 1 | 143 | 4 | 1500-3500 |
| lamp towers | `lampTower()` shared/map.js:3849 | 1 | 18 | 2 | 200-450 |
| WEST LANE: the spice alleys (north, a dog-leg east, north, a dog-leg west, north into B) | shared/map.js:4169 (section) | 1 | 12 | 2 | 100-300 |
| hanging rugs and lanterns on lines | `hanging()` shared/map.js:3866 | 2 | 12 | 2 | 100-300 |
| B: the carpet warehouse (its upstairs windows on the yard), the yard: rolls stacked, carpets drying on frames | shared/map.js:4190 (section) | 1 | 5 | 2 | 50-100 |
| bomb site boards (A / B) | `siteBoard()` shared/map.js:2165 | 2 | 4 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Training range (`range`): 166 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the rest of range() | shared/map.js:4490 (section) | 1 | 163 | 2 | 1500-4000 |
| ad boards | `adBoard()` shared/map.js:1495 | 1 | 3 (look only) | 1 | 40-100 |

#### Backrooms (`backrooms`): 28 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| office cubicles | `cube()` shared/map.js:4403 | 1 | 28 | 3 | 300-650 |
| (1 more bits of 1-2 boxes) | | | 2 | 1 | |

#### Scary Forest (`forest`): 573 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the radio mast yard (site B): a low chain-link fence, the mast blinking red, a shed full of radio, a generator | shared/map.js:4728 (section) | 1 | 150 | 4 | 1500-3500 |
| the road: fallen tree, power poles, the trailhead sign | shared/map.js:4759 (section) | 1 | 108 | 4 | 1000-2500 |
| property stakes | `stake()` shared/map.js:4786 | 2 | 92 | 4 | 900-2000 |
| the road: the broken-down car, a fallen tree across the lanes, power poles, a trailhead lot with a sign | shared/map.js:4770 (section) | 1 | 53 | 3 | 550-1500 |
| the cabin (site A): log walls, a porch, a door front and back, a stepped roof, a stone chimney | shared/map.js:4650 (section) | 1 | 40 | 3 | 400-950 |
| the woods: a jittered grid, thicker in the deep parts, some dead ones, some birches. outside the property | shared/map.js:4623 (section) | 1 | 38 | 3 | 400-900 |
| the campsite: a dead campfire in a ring of stones, log benches, two tents, a picnic table, the outhouse | shared/map.js:4688 (section) | 1 | 35 | 3 | 350-850 |
| trail and warning signs | `adSign()` shared/map.js:4826 | 5 | 28 | 3 | 300-650 |
| the broken-down car | `brokenCar()` shared/map.js:4571 | 1 | 19 | 3 | 200-450 |
| tents | `tent()` shared/map.js:4694 | 1 | 10 | 3 | 100-250 |

#### Dead Mall (`deadmall`): 66 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| ARCADE: three rows of back-to-back cabinets (gaps halfway down), screens glowing on both sides | shared/map.js:4924 (section) | 1 | 18 | 3 | 200-450 |
| FOOD COURT: tables in a 3x3 grid (lanes between them), a burger counter in the corner | shared/map.js:4910 (section) | 1 | 11 | 2 | 100-250 |
| ENTRANCE HALL (start): an info kiosk to run round, two pillars, benches under the boarded entrance | shared/map.js:4904 (section) | 1 | 8 | 2 | 80-200 |
| ARCADE: cabinets with glowing screens | shared/map.js:4913 (section) | 1 | 8 | 2 | 80-200 |
| ATRIUM: the elevator core in the middle (the big loop), planters, the mystery crate on the north stage | shared/map.js:4916 (section) | 1 | 8 | 2 | 80-200 |
| doors: roller shutters in the inside walls. they're not map boxes: the mode adds the closed ones to the room | shared/map.js:4882 (section) | 1 | 7 | 2 | 70-150 |
| LOADING DOCK: crates, pallets, a forklift, the power switch on the east wall | shared/map.js:4929 (section) | 1 | 3 | 2 | 40-100 |
| the Cheat Machine (server/zmextra.js): against the arcade's north wall, a random modifier once the power's on | shared/map.js:4933 (section) | 1 | 3 | 2 | 40-100 |

#### Jankburg (Royale) (`jankburg`): 449 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| over the streets: cables, hanging neon signs, washing lines; hazard bollards (the lights, vending machines, barrels and cars are round 4 models) | shared/jankburg.js:369 (section) | 1 | 213 | 4 | 2000-5000 |
| the giant toy-block letters | `word()` shared/jankburg.js:572 | 1 | 66 | 4 | 650-1500 |
| the park: benches, playground, fountain | `pronounPark()` shared/jankburg.js:583 | 1 | 53 | 3 | 550-1500 |
| the giant toy ball | `ball()` shared/jankburg.js:421 | 1 | 45 | 3 | 450-1000 |
| the fountain | `fountain()` shared/jankburg.js:428 | 1 | 32 | 3 | 300-750 |
| market stall leftovers (rugs, goods) | `stall()` shared/map.js:2361 | 2 | 21 | 3 | 200-500 |
| landmarks: the HQ statue, flags | shared/jankburg.js:302 (section) | 1 | 15 | 3 | 150-350 |
| ad boards | `adBoard()` shared/map.js:1495 | 1 | 4 | 2 | 40-100 |
## B. Architecture

#### Platform (`platform`): 1730 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| rig stairs (open grating flights) | `rigStair()` shared/map.js:562 | 12 | 661 | 5 | 4000-9500 |
| deck railings | `rail()` shared/map.js:544 | 10 | 576 | 4 | 3500-8000 |
| the living quarters block | `livingQuarters()` shared/map.js:605 | 1 | 153 | 4 | 900-2000 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 8 | 127 | 4 | 750-2000 |
| the drilling side: derrick, drill floor | `drillSide()` shared/map.js:672 | 1 | 101 | 4 | 600-1500 |
| the boat landing, bulwarks and stair up | `snackRun()` shared/map.js:735 | 1 | 58 | 4 | 350-800 |
| the rig jacket legs and braces | `jacket()` shared/map.js:778 | 1 | 43 (look only) | 3 | 250-600 |
| compressor house | `compressorHouse()` shared/map.js:765 | 1 | 11 | 3 | 70-150 |

#### Platform (P&D) (`platform_sd`): 2365 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| deck railings | `rail()` shared/map.js:544 | 10 | 1003 | 4 | 6000-14000 |
| rig stairs (open grating flights) | `rigStair()` shared/map.js:562 | 12 | 749 | 4 | 4500-10500 |
| the living quarters block | `livingQuarters()` shared/map.js:605 | 1 | 153 | 4 | 900-2000 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 8 | 127 | 4 | 750-2000 |
| the rig jacket legs and braces | `jacket()` shared/map.js:778 | 3 | 129 (look only) | 3 | 750-2000 |
| the drilling side: derrick, drill floor | `drillSide()` shared/map.js:672 | 1 | 101 | 3 | 600-1500 |
| the boat landing, bulwarks and stair up | `snackRun()` shared/map.js:735 | 1 | 58 | 3 | 350-800 |
| truss bridge | `trussBridge()` shared/map.js:895 | 1 | 18 | 3 | 100-250 |
| pipe bridge | `pipeBridge()` shared/map.js:905 | 1 | 16 | 3 | 100-200 |
| compressor house | `compressorHouse()` shared/map.js:765 | 1 | 11 | 2 | 70-150 |

#### Rooftop (`rooftop`): 3537 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the city beyond the map (render-only blocks, roofs, streets to the fog) | `cityBeyond()` shared/map.js:363 | 1 | 2408 (look only) | 5 | 14500-33500 |
| street level far below (render-only shopfronts, neon, windows) | `streetLevel()` shared/map.js:269 | 1 | 712 (look only) | 4 | 4500-10000 |
| stair bridges between the towers | `stairBridge()` shared/map.js:1040 | 1 | 108 | 4 | 650-1500 |
| the penthouse | `penthouse()` shared/map.js:1067 | 1 | 57 | 4 | 350-800 |
| office / tenement towers | `tower()` shared/map.js:201 | 1 | 130 (look only) | 3 | 800-2000 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 17 | 53 | 3 | 300-750 |
| sky bridges | `skyBridge()` shared/map.js:1051 | 1 | 25 | 3 | 150-350 |
| switchback stairs | `stairs()` shared/map.js:88 | 2 | 18 | 3 | 100-250 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 2 | 8 | 3 | 50-100 |
| the look (render-only): the towers round about, the street far below, the city to the fog | shared/map.js:1199 (section) | 1 | 14 (look only) | 2 | 80-200 |
| rooftop machine rooms and parapets | `roofTop()` shared/map.js:1029 | 1 | 4 | 2 | 40-100 |

#### Rooftop (P&D) (`rooftop_sd`): 4075 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the city beyond the map (render-only blocks, roofs, streets to the fog) | `cityBeyond()` shared/map.js:363 | 1 | 2484 (look only) | 4 | 15000-35000 |
| street level far below (render-only shopfronts, neon, windows) | `streetLevel()` shared/map.js:269 | 1 | 975 (look only) | 4 | 6000-13500 |
| stair bridges between the towers | `stairBridge()` shared/map.js:1040 | 6 | 225 | 4 | 1500-3000 |
| office / tenement towers | `tower()` shared/map.js:201 | 1 | 132 (look only) | 3 | 800-2000 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 14 | 83 | 3 | 500-1000 |
| the penthouse | `penthouse()` shared/map.js:1067 | 1 | 57 | 3 | 350-800 |
| the low roofs: AC, a skylight, vents, crates; the two towers: machine rooms, AC, the ☺ CORP flag, the billboar | shared/map.js:1291 (section) | 1 | 46 | 3 | 300-650 |
| switchback stairs | `stairs()` shared/map.js:88 | 2 | 18 | 3 | 100-250 |
| the look (render-only): the towers round about, the street far below, the city to the fog | shared/map.js:1330 (section) | 1 | 22 (look only) | 2 | 150-300 |
| rooftop machine rooms and parapets | `roofTop()` shared/map.js:1029 | 7 | 13 | 2 | 80-200 |
| sky bridges | `skyBridge()` shared/map.js:1051 | 1 | 12 | 2 | 70-150 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 2 | 8 | 2 | 50-100 |

#### Suburb (`suburb`): 1651 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 12 | 783 | 5 | 4500-11000 |
| the suburb houses | `home()` shared/map.js:1374 | 2 | 382 | 4 | 2500-5500 |
| wooden fences | `woodFence()` shared/map.js:1524 | 3 | 214 | 4 | 1500-3000 |
| switchback stairs | `stairs()` shared/map.js:88 | 4 | 109 | 4 | 650-1500 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 3 | 66 | 4 | 400-900 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 55 | 4 | 350-750 |
| east end (team 2): the building site: a frame going up, a scaffold, a digger, the site office | shared/map.js:1826 (section) | 1 | 42 | 3 | 250-600 |

#### Suburb (P&D) (`suburb_sd`): 633 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| facade houses | `facadeHouse()` shared/map.js:1508 | 2 | 170 | 4 | 1000-2500 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 16 | 162 | 4 | 950-2500 |
| wooden fences | `woodFence()` shared/map.js:1524 | 4 | 97 | 3 | 600-1500 |
| the suburb houses | `home()` shared/map.js:1374 | 2 | 68 | 3 | 400-950 |
| A: the building site (plywood hoarding, a frame going up, a scaffold, a digger, sand) | shared/map.js:1647 (section) | 1 | 53 | 3 | 300-750 |
| the turnaround is the defenders' side: the HOA clubhouse hides their spawn from the street | shared/map.js:1666 (section) | 1 | 36 | 3 | 200-500 |
| switchback stairs | `stairs()` shared/map.js:88 | 2 | 25 | 3 | 150-350 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 1 | 12 | 2 | 70-150 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 10 | 2 | 60-150 |

#### Warehouse (`warehouse`): 276 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 8 | 137 | 4 | 800-2000 |
| chain-link fences | `chainFence()` shared/map.js:2145 | 2 | 104 | 4 | 600-1500 |
| switchback stairs | `stairs()` shared/map.js:88 | 2 | 17 | 3 | 100-250 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 10 | 3 | 60-150 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 3 | 8 | 3 | 50-100 |

#### Warehouse (P&D) (`warehouse_sd`): 255 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| chain-link fences | `chainFence()` shared/map.js:2145 | 2 | 107 | 3 | 650-1500 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 12 | 105 | 3 | 650-1500 |
| the courtyard: the defenders' side, between the hall's east door and both sites | shared/map.js:2288 (section) | 1 | 37 | 2 | 200-500 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 3 | 3 | 2 | 40-100 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 3 | 2 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Desert (`desert`): 1871 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 4 | 780 | 5 | 4500-11000 |
| the town wall (gates east and west, a road through both, gate towers, corner towers, battlements) | shared/map.js:2611 (section) | 1 | 252 | 4 | 1500-3500 |
| switchback stairs | `stairs()` shared/map.js:88 | 5 | 225 | 4 | 1500-3000 |
| the frontier-town facades (false fronts, porches) | `frontier()` shared/map.js:2428 | 7 | 144 | 4 | 850-2000 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 98 | 4 | 600-1500 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 4 | 72 | 4 | 450-1000 |
| adobe huts | `adobeHut()` shared/map.js:2566 | 3 | 72 | 4 | 450-1000 |
| the rail trestle over the canyon | `trestle()` shared/map.js:2517 | 1 | 77 | 3 | 450-1000 |
| rope bridge | `ropeBridge()` shared/map.js:2530 | 1 | 55 | 3 | 350-750 |
| watchtower | `watchtower()` shared/map.js:2578 | 1 | 26 | 3 | 150-350 |
| canyon-lip fences | `lipFence()` shared/map.js:2586 | 1 | 24 | 3 | 150-350 |
| over the canyon | shared/map.js:2709 (section) | 1 | 20 | 3 | 100-300 |
| a ruin | `ruin()` shared/map.js:2573 | 1 | 13 | 3 | 80-200 |
| stone bridge | `stoneBridge()` shared/map.js:2524 | 1 | 13 | 3 | 80-200 |

#### Desert (P&D) (`desert_sd`): 1106 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 4 | 456 | 4 | 2500-6500 |
| the frontier-town facades (false fronts, porches) | `frontier()` shared/map.js:2428 | 8 | 134 | 4 | 800-2000 |
| the town wall (its top's over the ceiling): the west gate the stage came in by (shut behind it), north and sou | shared/map.js:2827 (section) | 1 | 151 | 3 | 900-2000 |
| switchback stairs | `stairs()` shared/map.js:88 | 2 | 93 | 3 | 550-1500 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 45 | 3 | 250-650 |
| canyon-lip fences | `lipFence()` shared/map.js:2586 | 2 | 43 | 3 | 250-600 |
| over the canyon: the trestle (north, the cart that jumped its rails), the stone bridge (its gateposts), the ro | shared/map.js:2900 (section) | 1 | 18 | 3 | 100-250 |
| the rail trestle over the canyon | `trestle()` shared/map.js:2517 | 1 | 77 | 2 | 450-1000 |
| rope bridge | `ropeBridge()` shared/map.js:2530 | 1 | 55 | 2 | 350-750 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 2 | 15 | 2 | 90-200 |
| stone bridge | `stoneBridge()` shared/map.js:2524 | 1 | 13 | 2 | 80-200 |
| walls (with their door / window cuts) | `wall()` shared/map.js:2829 | 2 | 6 | 2 | 40-100 |

#### Islands (`islands`): 693 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| stair flights | `flight()` shared/map.js:3021 | 16 | 203 | 4 | 1000-3000 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 18 | 116 | 4 | 700-1500 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 9 | 93 | 4 | 550-1500 |
| rope walkways and piers | `ropeWalk()` shared/map.js:3057 | 2 | 204 | 3 | 1000-3000 |
| the old fort | `fort()` shared/map.js:3239 | 1 | 53 | 3 | 300-750 |
| the lighthouse | `lighthouse()` shared/map.js:3212 | 1 | 17 | 3 | 100-250 |
| the keeper's cottage | `cottage()` shared/map.js:3228 | 1 | 4 | 2 | 40-100 |
| the bait shack | `baitShack()` shared/map.js:3156 | 1 | 3 | 2 | 40-100 |

#### Islands (P&D) (`islands_sd`): 612 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| rope walkways and piers | `ropeWalk()` shared/map.js:3057 | 5 | 263 | 3 | 1500-3500 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 16 | 109 | 3 | 650-1500 |
| stair flights | `flight()` shared/map.js:3021 | 10 | 103 | 3 | 600-1500 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 8 | 70 | 3 | 400-1000 |
| the old fort | `fort()` shared/map.js:3239 | 1 | 53 | 3 | 300-750 |
| the lighthouse | `lighthouse()` shared/map.js:3212 | 1 | 10 | 2 | 60-150 |
| the keeper's cottage | `cottage()` shared/map.js:3228 | 1 | 4 | 2 | 40-100 |

#### Skyline (`skyline`): 5993 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the city beyond the map (render-only blocks, roofs, streets to the fog) | `cityBeyond()` shared/map.js:363 | 1 | 3292 (look only) | 5 | 20000-46000 |
| stair bridges between the towers | `stairBridge()` shared/map.js:1040 | 2 | 600 | 5 | 3500-8500 |
| street level far below (render-only shopfronts, neon, windows) | `streetLevel()` shared/map.js:269 | 1 | 1440 (look only) | 4 | 8500-20000 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 8 | 203 | 4 | 1000-3000 |
| office / tenement towers | `tower()` shared/map.js:201 | 1 | 275 (look only) | 3 | 1500-4000 |
| switchback stairs | `stairs()` shared/map.js:88 | 2 | 51 | 3 | 300-700 |
| sky bridges | `skyBridge()` shared/map.js:1051 | 1 | 24 | 3 | 150-350 |
| the glass tube bridge | `tubeBridge()` shared/map.js:3488 | 1 | 22 | 3 | 150-300 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 20 | 3 | 100-300 |
| rooftop machine rooms and parapets | `roofTop()` shared/map.js:1029 | 1 | 18 | 3 | 100-250 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 1 | 9 | 3 | 50-150 |
| the look (render-only): the street far below, crowns and cables round the towers, the city to the fog | shared/map.js:3669 (section) | 1 | 34 (look only) | 2 | 200-500 |
| domes (bazaar roofs, skyline crowns) | `dome()` shared/map.js:3843 | 1 | 5 (look only) | 2 | 40-100 |

#### Skyline (P&D) (`skyline_sd`): 5644 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the city beyond the map (render-only blocks, roofs, streets to the fog) | `cityBeyond()` shared/map.js:363 | 1 | 3759 (look only) | 4 | 22500-52500 |
| street level far below (render-only shopfronts, neon, windows) | `streetLevel()` shared/map.js:269 | 1 | 1030 (look only) | 4 | 6000-14500 |
| stair bridges between the towers | `stairBridge()` shared/map.js:1040 | 6 | 414 | 4 | 2500-6000 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 8 | 176 | 4 | 1000-2500 |
| office / tenement towers | `tower()` shared/map.js:201 | 1 | 151 (look only) | 3 | 900-2000 |
| switchback stairs | `stairs()` shared/map.js:88 | 2 | 41 | 3 | 250-550 |
| rooftop machine rooms and parapets | `roofTop()` shared/map.js:1029 | 1 | 18 | 3 | 100-250 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 16 | 3 | 100-200 |
| outside: the city round about (render-only) | shared/map.js:3767 (section) | 1 | 26 (look only) | 2 | 150-350 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 1 | 8 | 2 | 50-100 |
| domes (bazaar roofs, skyline crowns) | `dome()` shared/map.js:3843 | 1 | 5 (look only) | 1 | 40-100 |

#### Bazaar (`bazaar`): 1686 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 14 | 752 | 5 | 4500-10500 |
| switchback stairs | `stairs()` shared/map.js:88 | 3 | 295 | 4 | 2000-4000 |
| souk arcades and shopfronts | `souk()` shared/map.js:3831 | 16 | 146 | 4 | 900-2000 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 4 | 140 | 4 | 850-2000 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 1 | 120 | 4 | 700-1500 |
| domes (bazaar roofs, skyline crowns) | `dome()` shared/map.js:3843 | 2 | 89 | 4 | 550-1000 |
| NORTH: the caravanserai (a courtyard inn: an arcade all round, a gallery over it, the yard in the middle) | shared/map.js:3992 (section) | 1 | 74 | 4 | 450-1000 |
| WEST and EAST: the gate plazas (the teams' spawns), a fountain each, the houses round them | shared/map.js:4054 (section) | 1 | 24 | 3 | 150-350 |
| SOUTH: the dye works, the canal (ankle deep, four bridges), the drying racks | shared/map.js:4009 (section) | 1 | 18 | 3 | 100-250 |
| outside the wall (render-only): dunes, rocks, a camp outside the west gate, an oasis, the next town over | shared/map.js:4076 (section) | 1 | 28 (look only) | 2 | 150-400 |

#### Bazaar (P&D) (`bazaar_sd`): 1897 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| facade dressing: shutters, window frames, balconies, sills | `dressFacades()` shared/map.js:3877 | 1 | 1449 (look only) | 4 | 8500-20500 |
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 14 | 215 | 4 | 1500-3000 |
| solid city blocks (facade + roof junk) | `block()` shared/map.js:4110 | 10 | 44 | 3 | 250-600 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 1 | 21 | 3 | 150-300 |
| souk arcades and shopfronts | `souk()` shared/map.js:3831 | 3 | 20 | 3 | 100-300 |
| EAST LANE: the canal (quays both sides, three bridges, boats moored, ankle-deep water to wade) | shared/map.js:4179 (section) | 1 | 19 | 3 | 100-250 |
| switchback stairs | `stairs()` shared/map.js:88 | 1 | 18 | 3 | 100-250 |
| domes (bazaar roofs, skyline crowns) | `dome()` shared/map.js:3843 | 2 | 70 (look only) | 2 | 400-1000 |
| outside the wall (render-only): dunes, rocks, the caravan's tail outside the south gate, the next town over | shared/map.js:4212 (section) | 1 | 25 (look only) | 2 | 150-350 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 11 | 2 | 70-150 |
| the palace (the guard's spawn): its forecourt, the passage south to mid, the alleys west to B and east to A | shared/map.js:4161 (section) | 1 | 5 | 2 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 2 | 1 | |

#### Backrooms (`backrooms`): 1735 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 8 | 1479 | 5 | 9000-20500 |
| pillar rooms | shared/map.js:4399 (section) | 1 | 119 | 3 | 700-1500 |
| the pool rooms: flooded, white tiles everywhere, under the west side of the map | shared/map.js:4421 (section) | 1 | 32 | 3 | 200-450 |
| switchback stairs | `stairs()` shared/map.js:88 | 1 | 30 | 3 | 200-400 |
| the big hall: sparse pillars, a few freestanding walls (one has a doorway to nowhere), low walls for cover | shared/map.js:4385 (section) | 1 | 17 | 3 | 100-250 |
| ceilings: a low drop ceiling everywhere, the hall's way up high. the light panels are part of the tile texture | shared/map.js:4374 (section) | 1 | 29 | 2 | 150-400 |
| stair flights | `flight()` shared/map.js:4354 | 3 | 9 | 2 | 50-150 |
| SITE B, the Wet Room: white tiles, the stairs up from the pools, tiled half walls, a couple of pillars, puddle | shared/map.js:4414 (section) | 1 | 8 | 2 | 50-100 |
| spawn lobbies: a row of pillars down the middle | shared/map.js:4418 (section) | 1 | 8 | 2 | 50-100 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 4 | 2 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Scary Forest (`forest`): 161 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 8 | 48 | 3 | 300-650 |
| chain-link fence | `fence()` shared/map.js:4730 | 1 | 40 | 3 | 250-550 |
| switchback stairs | `stairs()` shared/map.js:88 | 2 | 39 | 3 | 250-550 |
| the fire lookout tower: four legs, five flights of switchback stairs inside them, a glassless cab up top | shared/map.js:4708 (section) | 1 | 30 | 3 | 200-400 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 4 | 2 | 40-100 |

#### Dead Mall (`deadmall`): 231 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 9 | 123 | 3 | 750-1500 |
| windows: an opening in the outside wall (sill 0.9 m) onto a boarded-up back alley the zombies come from | shared/map.js:4852 (section) | 1 | 96 | 3 | 600-1500 |
| the rest of deadmall() | shared/map.js:4837 (section) | 1 | 12 | 2 | 70-150 |

#### Jankburg (Royale) (`jankburg`): 8830 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| walls (with their door / window cuts) | `wall()` shared/map.js:58 | 9 | 3668 | 5 | 22000-51500 |
| the outer ring: shanty walls, scaffold, junk barricades | `outerRing()` shared/jankburg.js:672 | 1 | 1118 | 5 | 6500-15500 |
| the city houses (shanty blocks, TVs, AC, junk) | `cityHouse()` shared/jankburg.js:135 | 1 | 998 | 5 | 6000-14000 |
| the city wall with its neon strip | `cityWall()` shared/jankburg.js:611 | 1 | 822 | 5 | 5000-11500 |
| the megacity out in the haze (render-only towers, the JankCorp megatower) | `skylineHaze()` shared/jankburg.js:715 | 1 | 444 (look only) | 4 | 2500-6000 |
| switchback stairs | `stairs()` shared/map.js:88 | 6 | 418 | 4 | 2500-6000 |
| upper facades of the city blocks (windows painted on) | `upper()` shared/jankburg.js:125 | 10 | 344 | 4 | 2000-5000 |
| building shells: floors, walls, stairs inside | `shell()` shared/map.js:112 | 17 | 308 | 4 | 2000-4500 |
| floor slabs (stairwell holes) | `slab()` shared/map.js:78 | 1 | 307 | 4 | 2000-4500 |
| the cathedral | `cathedral()` shared/jankburg.js:449 | 1 | 101 | 4 | 600-1500 |
| the Number Works factory | `numberWorks()` shared/jankburg.js:511 | 1 | 56 | 4 | 350-800 |
| solid city blocks (facade + roof junk) | `block()` shared/jankburg.js:554 | 1 | 54 | 4 | 300-750 |
| neon shop signs (shopfront: the buildings lane) | `sign()` shared/jankburg.js:137 | 7 | 69 (look only) | 3 | 400-950 |
| the slum tower | `slumTower()` shared/jankburg.js:534 | 1 | 30 | 3 | 200-400 |
| office / tenement towers | `tower()` shared/map.js:201 | 1 | 29 | 3 | 150-400 |
| the plaza building | `plaza()` shared/jankburg.js:439 | 1 | 22 | 3 | 150-300 |
| shop awnings (shopfront: the buildings lane) | `awning()` shared/jankburg.js:138 | 2 | 22 | 3 | 150-300 |
| the market hall | `marketHall()` shared/jankburg.js:485 | 1 | 15 | 3 | 90-200 |
| the arch | `liberalArch()` shared/jankburg.js:546 | 1 | 5 | 2 | 40-100 |
## C. Terrain and natural features

#### Platform (`platform`): 38 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 2 | 14 | 3 | 60-150 |
| far oil rigs (render-only) | `farRig()` shared/map.js:793 | 1 | 24 (look only) | 2 | 100-250 |

#### Platform (P&D) (`platform_sd`): 49 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 4 | 25 | 3 | 100-250 |
| far oil rigs (render-only) | `farRig()` shared/map.js:793 | 1 | 24 (look only) | 2 | 100-250 |

#### Rooftop (`rooftop`): 4 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 1 | 4 | 2 | 40-100 |

#### Rooftop (P&D) (`rooftop_sd`): 4 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 1 | 4 | 2 | 40-100 |

#### Suburb (`suburb`): 18 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the loop street (north and south run on out west through the trees: that's where the traffic comes from), kerb | shared/map.js:1752 (section) | 1 | 14 | 3 | 60-150 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Suburb (P&D) (`suburb_sd`): 21 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| SOUTH: the creek path, B long | shared/map.js:1699 (section) | 1 | 17 | 3 | 70-150 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 1 | 1 | |

#### Warehouse (`warehouse`): 52 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 3 | 16 | 3 | 60-150 |
| the ground (a hole for the shredder), asphalt where the trucks go, paint | shared/map.js:2042 (section) | 1 | 10 | 3 | 40-100 |
| gravel piles | `gravelPile()` shared/map.js:2021 | 2 | 16 (look only) | 2 | 60-150 |
| the road and verge outside the depot | `depotOutside()` shared/map.js:2172 | 1 | 6 | 2 | 40-100 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |

#### Warehouse (P&D) (`warehouse_sd`): 49 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| gravel piles | `gravelPile()` shared/map.js:2021 | 2 | 16 (look only) | 2 | 60-150 |
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 2 | 12 | 2 | 50-100 |
| the ground: one concrete slab, asphalt where the trucks go, paint | shared/map.js:2216 (section) | 1 | 11 | 2 | 40-100 |
| the road and verge outside the depot | `depotOutside()` shared/map.js:2172 | 1 | 6 | 2 | 40-100 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |

#### Desert (`desert`): 436 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the ground between it all (look only): dirt patches, sagebrush, the odd tumbleweed. never inside anything | shared/map.js:2769 (section) | 1 | 151 (look only) | 3 | 600-1500 |
| dunes | `dune()` shared/map.js:2413 | 1 | 132 (look only) | 3 | 550-1500 |
| rock formations | `rocks()` shared/map.js:2416 | 1 | 38 (look only) | 3 | 150-400 |
| boulders | `boulders()` shared/map.js:2590 | 1 | 35 | 3 | 150-350 |
| outside: sand all the way out (no cliff), the canyon running on as a ravine with a river at the bottom | shared/map.js:2776 (section) | 1 | 20 | 3 | 80-200 |
| the south back lots: the cemetery (picket fence, graves, a dead tree, a crypt), the stagecoach that didn't mak | shared/map.js:2675 (section) | 1 | 18 | 3 | 70-200 |
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 3 | 16 | 3 | 60-150 |
| the oasis: the pond (ankle deep), palms, a dock, the camp, rocks | shared/map.js:2757 (section) | 1 | 16 | 3 | 60-150 |
| the ground: sand both sides of the canyon (the east bank has a hole: the mine shaft), rock under it | shared/map.js:2606 (section) | 1 | 6 | 2 | 40-100 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |

#### Desert (P&D) (`desert_sd`): 319 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| dunes | `dune()` shared/map.js:2413 | 1 | 164 (look only) | 3 | 650-1500 |
| the ground between it all (look only): dirt patches, sagebrush, the odd tumbleweed. never inside anything | shared/map.js:2972 (section) | 1 | 91 (look only) | 3 | 350-900 |
| rock formations | `rocks()` shared/map.js:2416 | 1 | 42 (look only) | 2 | 150-400 |
| the ground, the canyon (x -7..7; its walls solid: fall in and grapple out), the river a long way down | shared/map.js:2822 (section) | 1 | 10 | 2 | 40-100 |
| boulders | `boulders()` shared/map.js:2590 | 1 | 8 | 2 | 40-100 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |

#### Islands (`islands`): 246 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| sandbars | `sandbar()` shared/map.js:3043 | 2 | 103 | 4 | 400-1000 |
| islets (surf rings) | `isle()` shared/map.js:3033 | 8 | 44 (look only) | 3 | 200-450 |
| Skull Rock | `skullRock()` shared/map.js:3264 | 1 | 33 | 3 | 150-350 |
| the volcano (Mount Kaboom) | `volcano()` shared/map.js:3109 | 1 | 28 | 3 | 100-300 |
| E, Lighthouse Point (x 62..92, z -18..18): the tower (a stair round it to the gallery), the keeper's cottage,  | shared/map.js:3336 (section) | 1 | 12 | 3 | 50-100 |
| the sandbars round the outside, each with a palm islet halfway | shared/map.js:3360 (section) | 1 | 12 | 3 | 50-100 |
| N, the Wreck (x -22..22, z -80..-58): the Soggy Biscuit on its reef, rocks, two palms, a rowboat | shared/map.js:3328 (section) | 1 | 5 | 2 | 40-100 |
| S, Skull Rock (x -18..18, z 58..80): the skull, palms, rocks, a rowboat | shared/map.js:3352 (section) | 1 | 5 | 2 | 40-100 |
| W, Fort Splinter (x -92..-62, z -18..18): the fort (the cannonball on its east wall), palms, rocks, a rowboat | shared/map.js:3344 (section) | 1 | 4 | 2 | 40-100 |

#### Islands (P&D) (`islands_sd`): 143 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| sandbars | `sandbar()` shared/map.js:3043 | 1 | 38 | 3 | 150-400 |
| Skull Rock | `skullRock()` shared/map.js:3264 | 1 | 33 | 3 | 150-350 |
| the volcano (Mount Kaboom) | `volcano()` shared/map.js:3109 | 1 | 28 | 3 | 100-300 |
| islets (surf rings) | `isle()` shared/map.js:3033 | 7 | 28 (look only) | 2 | 100-300 |
| reefs | `reef()` shared/map.js:3052 | 4 | 5 | 2 | 40-100 |
| B, Lighthouse Point (x -62..-34, z -82..-48): the tower's foot (no way up: the site's big cover), the cottage, | shared/map.js:3425 (section) | 1 | 4 | 2 | 40-100 |
| the links: mid (S to C), the sandbars (S to W / E), the boardwalks C to W / E, W to B, E to A, and the pirates | shared/map.js:3445 (section) | 1 | 4 | 2 | 40-100 |
| A, the Wreck (x 28..70, z -82..-50): the Soggy Biscuit on its reef, crates, rocks | shared/map.js:3436 (section) | 1 | 3 | 2 | 40-100 |
| (1 more bits of 1-2 boxes) | | | 2 | 1 | |

#### Skyline (`skyline`): 9 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the nine tops (half sizes): the Spire 13 x 13, the ring 15 x 13 (north/south) / 13 x 15 (east/west), the corne | shared/map.js:3618 (section) | 1 | 9 (look only) | 2 | 40-100 |

#### Skyline (P&D) (`skyline_sd`): 9 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the tops: [x, z, half x, half z, roof y]. middle column x [-14, 14]: the HQ z [-78, -50], the hub z [-40, 2], | shared/map.js:3706 (section) | 1 | 9 (look only) | 1 | 40-100 |

#### Bazaar (`bazaar`): 261 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| dunes | `dune()` shared/map.js:2413 | 1 | 160 (look only) | 3 | 650-1500 |
| rock formations | `rocks()` shared/map.js:2416 | 1 | 36 (look only) | 3 | 150-350 |
| the ground (the canal cut out of it), the city wall (its top's over the ceiling), corner towers, shut gates | shared/map.js:3941 (section) | 1 | 24 | 3 | 100-250 |
| the ground between it all (look only): sand patches, scrub, the odd tumbleweed, never inside anything | shared/map.js:4070 (section) | 1 | 33 (look only) | 2 | 150-350 |
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 1 | 4 | 2 | 40-100 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |

#### Bazaar (P&D) (`bazaar_sd`): 223 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| dunes | `dune()` shared/map.js:2413 | 1 | 160 (look only) | 3 | 650-1500 |
| rock formations | `rocks()` shared/map.js:2416 | 1 | 41 (look only) | 2 | 150-400 |
| the ground (the canal cut out of it), the wall round it all (its top's over the ceiling), the gates shut | shared/map.js:4111 (section) | 1 | 14 | 2 | 60-150 |
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 1 | 4 | 2 | 40-100 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |

#### Training range (`range`): 4 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |

#### Backrooms (`backrooms`): 59 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 4 | 59 | 3 | 250-600 |

#### Scary Forest (`forest`): 93 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| boulders | `boulder()` shared/map.js:4565 | 2 | 35 | 3 | 150-350 |
| the clearing: a ring of standing stones, one dead tree, and an office chair facing away from you | shared/map.js:4642 (section) | 1 | 15 | 3 | 60-150 |
| the ground: forest floor out a long way (past the lake shore it's mud under water), a dirt road | shared/map.js:4589 (section) | 1 | 11 | 3 | 40-100 |
| trails: drawn on the floor (render only, each a hair higher than the last so no two share a plane) | shared/map.js:4597 (section) | 1 | 28 (look only) | 2 | 100-300 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |

#### Jankburg (Royale) (`jankburg`): 169 boxes

| What | Built in | Copies | Boxes | Vis | Budget (tris) |
|---|---|---|---|---|---|
| paint: sidewalks, asphalt, the avenues' lane lines, the plaza | shared/jankburg.js:283 (section) | 1 | 154 (look only) | 3 | 600-1500 |
| ground slabs with holes (stairwells, canals) | `groundHoles()` shared/map.js:3813 | 2 | 8 | 3 | 40-100 |
| the ground: city paving inside the walls, dirt in the outer ring, the canal cut through both | shared/jankburg.js:271 (section) | 1 | 3 | 2 | 40-100 |
| the horizon floor out past the map | `horizon()` shared/map.js:494 | 1 | 4 (look only) | 1 | 40-100 |
## X. Boxes on purpose
- Suburb: livery pictures on the Blender box truck (`truckBoxes()` shared/map.js:1479, 2 boxes)
- Suburb: the shuttle bus's livery picture (`busBoxes()` shared/map.js:1455, 1 boxes)
- Suburb (P&D): livery pictures on the Blender box truck (`truckBoxes()` shared/map.js:1479, 2 boxes)
- Warehouse: livery pictures on the Blender trailers (`trailerBoxes()` shared/map.js:1944, 8 boxes)
- Warehouse: livery pictures on the Blender semis (`semiBoxes()` shared/map.js:1958, 6 boxes)
- Warehouse: gameplay side skirts under the trailers (no shooting under them) (`trailerS()` shared/map.js:2038, 4 boxes)
- Warehouse: gameplay side skirts under the semis (`semiS()` shared/map.js:2039, 3 boxes)
- Warehouse (P&D): livery pictures on the Blender trailers (`trailerBoxes()` shared/map.js:1944, 20 boxes)
- Warehouse (P&D): gameplay side skirts under the trailers (no shooting under them) (`trailerS()` shared/map.js:2212, 10 boxes)
- Warehouse (P&D): livery pictures on the Blender semis (`semiBoxes()` shared/map.js:1958, 6 boxes)
- Warehouse (P&D): gameplay side skirts under the semis (`semiS()` shared/map.js:2213, 3 boxes)
