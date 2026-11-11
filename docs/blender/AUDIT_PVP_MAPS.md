# What is still code-made boxes, per PvP map

Counted on main at af3c61d (after props round 4, the varied rocks and the volcano ground merged) with `tools/blender/inventory_maps.mjs`, skipping boxes a Blender prop, building or rock model draws and the shaped ground's hidden steps. "Boxes" = boxes still drawn as boxes. Vis 5 = in your face all match, 1 = far or tiny. Ranked by vis, then size. Top entries only; the full table is `AUDIT_PVP_MAPS_FULL.md`.

## islands: 1975 boxes left
- spawns: the fort's courtyard and beaches vs the lighthouse's point (TDM); everywhere for t (ground/rock, vis 4): 876 boxes. 
- stair flights (building, vis 4): 161 boxes, 10 copies. `flight()`
- walls (with their door / window cuts) (building, vis 4): 116 boxes, 18 copies. `wall()`
- the ways off it: the rope bridge north (a rock to rest on halfway), the pier east (the bai (prop, vis 4): 109 boxes. 
- sandbars (ground/rock, vis 4): 103 boxes, 2 copies. `sandbar()`
- floor slabs (stairwell holes) (building, vis 4): 55 boxes, 4 copies. `slab()`
- rope walkways and piers (building, vis 3): 204 boxes, 2 copies. `ropeWalk()`
- the old fort (building, vis 3): 53 boxes. `fort()`
- ...and 16 smaller groups (298 boxes)

## islands_sd: 898 boxes left
- rope walkways and piers (building, vis 3): 263 boxes, 5 copies. `ropeWalk()`
- walls (with their door / window cuts) (building, vis 3): 109 boxes, 16 copies. `wall()`
- stair flights (building, vis 3): 103 boxes, 10 copies. `flight()`
- floor slabs (stairwell holes) (building, vis 3): 70 boxes, 8 copies. `slab()`
- the old fort (building, vis 3): 53 boxes. `fort()`
- the shipwreck (the Soggy Biscuit) (prop, vis 3): 46 boxes. `wreck()`
- sandbars (ground/rock, vis 3): 38 boxes. `sandbar()`
- Skull Rock (ground/rock, vis 3): 33 boxes. `skullRock()`
- ...and 16 smaller groups (183 boxes)

## desert: 3032 boxes left
- walls (with their door / window cuts) (building, vis 5): 672 boxes, 4 copies. `wall()`
- the ground gets its shape last (shared/terrain.js): dunes, hollows and washes between the  (ground/rock, vis 4): 412 boxes. 
- the town wall (gates east and west, a road through both, gate towers, corner towers, battl (building, vis 4): 252 boxes. 
- switchback stairs (building, vis 4): 225 boxes, 5 copies. `stairs()`
- the frontier-town facades (false fronts, porches) (building, vis 4): 144 boxes, 7 copies. `frontier()`
- floor slabs (stairwell holes) (building, vis 4): 89 boxes. `slab()`
- the north back lots: the corral, the blacksmith, the outhouses, the mine's rail spur and i (prop, vis 4): 87 boxes. 
- the mine: the mesa (a tunnel west to east into it, a side chamber with the shaft, the head (prop, vis 4): 70 boxes. 
- ...and 28 smaller groups (1081 boxes)

## desert_sd: 2030 boxes left
- walls (with their door / window cuts) (building, vis 4): 456 boxes, 4 copies. `wall()`
- the frontier-town facades (false fronts, porches) (building, vis 4): 134 boxes, 8 copies. `frontier()`
- dunes (ground/rock, vis 3): 164 boxes. `dune()`
- the town wall (its top's over the ceiling): the west gate the stage came in by (shut behin (building, vis 3): 151 boxes. 
- B: the depot. the payroll train stopped at the platform (its nose to the rope bridge), the (prop, vis 3): 94 boxes. 
- switchback stairs (building, vis 3): 93 boxes, 2 copies. `stairs()`
- the ground between it all (look only): dirt patches, sagebrush, the odd tumbleweed. never  (ground/rock, vis 3): 91 boxes. 
- A: the mine head. the mesa's the north edge: the mine's in it (in at the mouth, along the  (prop, vis 3): 90 boxes. 
- ...and 22 smaller groups (757 boxes)

## bazaar: 2580 boxes left
- walls (with their door / window cuts) (building, vis 5): 752 boxes, 14 copies. `wall()`
- THE GRAND BAZAAR: the covered hall in the middle (prop, vis 4): 308 boxes. 
- switchback stairs (building, vis 4): 295 boxes, 3 copies. `stairs()`
- souk arcades and shopfronts (building, vis 4): 146 boxes, 16 copies. `souk()`
- floor slabs (stairwell holes) (building, vis 4): 140 boxes, 4 copies. `slab()`
- building shells: floors, walls, stairs inside (building, vis 4): 120 boxes. `shell()`
- domes (bazaar roofs, skyline crowns) (building, vis 4): 89 boxes, 2 copies. `dome()`
- NORTH: the caravanserai (a courtyard inn: an arcade all round, a gallery over it, the yard (building, vis 4): 74 boxes. 
- ...and 15 smaller groups (656 boxes)

## bazaar_sd: 2276 boxes left
- facade dressing: shutters, window frames, balconies, sills (building, vis 4): 1449 boxes. `dressFacades()`
- walls (with their door / window cuts) (building, vis 4): 215 boxes, 14 copies. `wall()`
- MID: the Grand Hall (covered, its doors at opposite corners, three stall islands down the  (prop, vis 4): 143 boxes. 
- dunes (ground/rock, vis 3): 160 boxes. `dune()`
- solid city blocks (facade + roof junk) (building, vis 3): 44 boxes, 10 copies. `block()`
- building shells: floors, walls, stairs inside (building, vis 3): 21 boxes. `shell()`
- souk arcades and shopfronts (building, vis 3): 20 boxes, 3 copies. `souk()`
- EAST LANE: the canal (quays both sides, three bridges, boats moored, ankle-deep water to w (building, vis 3): 19 boxes. 
- ...and 15 smaller groups (205 boxes)

## skyline: 6347 boxes left
- the city beyond the map (render-only blocks, roofs, streets to the fog) (building, vis 5): 3292 boxes. `cityBeyond()`
- stair bridges between the towers (building, vis 5): 600 boxes, 2 copies. `stairBridge()`
- street level far below (render-only shopfronts, neon, windows) (building, vis 4): 1440 boxes. `streetLevel()`
- walls (with their door / window cuts) (building, vis 4): 196 boxes, 8 copies. `wall()`
- office / tenement towers (building, vis 3): 275 boxes. `tower()`
- neon crowns, facade ads, cables with hanging ads (prop, vis 3): 103 boxes. `cityDress()`
- switchback stairs (building, vis 3): 51 boxes, 2 copies. `stairs()`
- the rooftop greenhouse / pond (prop, vis 3): 33 boxes. `skyGreen()`
- ...and 20 smaller groups (357 boxes)

## skyline_sd: 5917 boxes left
- the city beyond the map (render-only blocks, roofs, streets to the fog) (building, vis 4): 3759 boxes. `cityBeyond()`
- street level far below (render-only shopfronts, neon, windows) (building, vis 4): 1030 boxes. `streetLevel()`
- stair bridges between the towers (building, vis 4): 414 boxes, 6 copies. `stairBridge()`
- walls (with their door / window cuts) (building, vis 4): 176 boxes, 8 copies. `wall()`
- office / tenement towers (building, vis 3): 151 boxes. `tower()`
- the set pieces (prop, vis 3): 47 boxes. 
- switchback stairs (building, vis 3): 41 boxes, 2 copies. `stairs()`
- the rooftop greenhouse / pond (prop, vis 3): 33 boxes. `skyGreen()`
- ...and 18 smaller groups (266 boxes)

## rooftop: 3756 boxes left
- the city beyond the map (render-only blocks, roofs, streets to the fog) (building, vis 5): 2408 boxes. `cityBeyond()`
- street level far below (render-only shopfronts, neon, windows) (building, vis 4): 712 boxes. `streetLevel()`
- jump pads (prop, vis 4): 121 boxes. 
- stair bridges between the towers (building, vis 4): 108 boxes. `stairBridge()`
- the two towers: x [-58, -30] and [30, 58], z [-18, 18], roofs at 0. bridges land in the ga (prop, vis 4): 57 boxes. 
- the penthouse (building, vis 4): 57 boxes. `penthouse()`
- office / tenement towers (building, vis 3): 130 boxes. `tower()`
- walls (with their door / window cuts) (building, vis 3): 53 boxes, 17 copies. `wall()`
- ...and 10 smaller groups (110 boxes)

## rooftop_sd: 4251 boxes left
- the city beyond the map (render-only blocks, roofs, streets to the fog) (building, vis 4): 2484 boxes. `cityBeyond()`
- street level far below (render-only shopfronts, neon, windows) (building, vis 4): 975 boxes. `streetLevel()`
- stair bridges between the towers (building, vis 4): 225 boxes, 6 copies. `stairBridge()`
- office / tenement towers (building, vis 3): 132 boxes. `tower()`
- B, the bank's roof: machine room, JANK BANK sign, AC farm (prop, vis 3): 86 boxes. 
- walls (with their door / window cuts) (building, vis 3): 83 boxes, 14 copies. `wall()`
- the penthouse (building, vis 3): 57 boxes. `penthouse()`
- the low roofs: AC, a skylight, vents, crates; the two towers: machine rooms, AC, the ☺ COR (building, vis 3): 46 boxes. 
- ...and 13 smaller groups (163 boxes)

## suburb: 970 boxes left
- the suburb houses (building, vis 4): 222 boxes, 2 copies. `home()`
- wooden fences (building, vis 4): 214 boxes, 3 copies. `woodFence()`
- the four corner lots (each past the end of a row of houses, between the street and the bac (prop, vis 4): 156 boxes. 
- the park: the playground (west), the founder's plaza (middle), the pond with a footbridge  (prop, vis 4): 100 boxes. 
- outside the suburb: power poles, junk, tyre piles (prop, vis 3): 138 boxes. `suburbOutside()`
- east end (team 2): the building site: a frame going up, a scaffold, a digger, the site off (building, vis 3): 42 boxes. 
- switchback stairs (building, vis 3): 19 boxes, 3 copies. `stairs()`
- walls (with their door / window cuts) (building, vis 3): 18 boxes, 4 copies. `wall()`
- ...and 9 smaller groups (61 boxes)

## suburb_sd: 693 boxes left
- facade houses (building, vis 4): 170 boxes, 2 copies. `facadeHouse()`
- outside the suburb: power poles, junk, tyre piles (prop, vis 3): 137 boxes. `suburbOutside()`
- wooden fences (building, vis 3): 97 boxes, 4 copies. `woodFence()`
- A: the building site (plywood hoarding, a frame going up, a scaffold, a digger, sand) (building, vis 3): 53 boxes. 
- the suburb houses (building, vis 3): 44 boxes, 2 copies. `home()`
- B: the MEGA-MART EXPRESS (inside: aisles, the tills, the fridges, the stockroom), its car  (prop, vis 3): 39 boxes. 
- the main street (on west through the trees to nowhere), sidewalks, the cul-de-sac at the e (prop, vis 3): 36 boxes. 
- the turnaround is the defenders' side: the HOA clubhouse hides their spawn from the street (building, vis 3): 36 boxes. 
- ...and 10 smaller groups (81 boxes)

## platform: 2035 boxes left
- rig stairs (open grating flights) (building, vis 5): 661 boxes, 12 copies. `rigStair()`
- deck railings (building, vis 4): 576 boxes, 10 copies. `rail()`
- the living quarters block (building, vis 4): 153 boxes. `livingQuarters()`
- walls (with their door / window cuts) (building, vis 4): 127 boxes, 8 copies. `wall()`
- the drilling side: derrick, drill floor (building, vis 4): 101 boxes. `drillSide()`
- the boat landing, bulwarks and stair up (building, vis 4): 58 boxes. `snackRun()`
- wellhead christmas trees (prop, vis 3): 84 boxes. `xmasTree()`
- the rig jacket legs and braces (building, vis 3): 43 boxes. `jacket()`
- ...and 13 smaller groups (232 boxes)

## platform_sd: 2674 boxes left
- deck railings (building, vis 4): 1003 boxes, 10 copies. `rail()`
- rig stairs (open grating flights) (building, vis 4): 749 boxes, 12 copies. `rigStair()`
- the living quarters block (building, vis 4): 153 boxes. `livingQuarters()`
- walls (with their door / window cuts) (building, vis 4): 127 boxes, 8 copies. `wall()`
- the rig jacket legs and braces (building, vis 3): 129 boxes, 3 copies. `jacket()`
- the drilling side: derrick, drill floor (building, vis 3): 101 boxes. `drillSide()`
- wellhead christmas trees (prop, vis 3): 84 boxes. `xmasTree()`
- the boat landing, bulwarks and stair up (building, vis 3): 58 boxes. `snackRun()`
- ...and 15 smaller groups (270 boxes)

## warehouse: 579 boxes left
- walls (with their door / window cuts) (building, vis 4): 137 boxes, 8 copies. `wall()`
- the hall: doors on every side (the west and east ones off the same line), racking in a gri (prop, vis 4): 115 boxes. 
- chain-link fences (building, vis 4): 104 boxes, 2 copies. `chainFence()`
- warehouse racking (prop, vis 3): 24 boxes, 3 copies. `rack()`
- south: the truck dock. two semis backed up beside the dock doors, a row of trailers furthe (prop, vis 3): 18 boxes. 
- switchback stairs (building, vis 3): 17 boxes, 2 copies. `stairs()`
- ground slabs with holes (stairwells, canals) (ground/rock, vis 3): 16 boxes, 3 copies. `groundHoles()`
- the fence (the gate's shut), the world outside, light masts (prop, vis 3): 13 boxes. 
- ...and 14 smaller groups (135 boxes)

## warehouse_sd: 551 boxes left
- chain-link fences (building, vis 3): 107 boxes, 2 copies. `chainFence()`
- walls (with their door / window cuts) (building, vis 3): 105 boxes, 12 copies. `wall()`
- MID: the hall (prop, vis 3): 100 boxes. 
- B: the parcel shed (inside, cyan) (prop, vis 3): 19 boxes. 
- the courtyard: the defenders' side, between the hall's east door and both sites (building, vis 2): 37 boxes. 
- cement mixer trucks (prop, vis 2): 28 boxes. `mixerTruck()`
- bulldozers (prop, vis 2): 22 boxes, 2 copies. `bulldozer()`
- gravel piles (ground/rock, vis 2): 16 boxes, 2 copies. `gravelPile()`
- ...and 16 smaller groups (117 boxes)

## forest: 794 boxes left
- the radio mast yard (site B): a low chain-link fence, the mast blinking red, a shed full o (prop, vis 4): 150 boxes. 
- the lake edge: a dock, a rowboat tied to it, a canoe on the shore, reeds (prop, vis 4): 108 boxes. 
- property stakes (prop, vis 4): 92 boxes, 2 copies. `stake()`
- the road: the broken-down car, a fallen tree across the lanes, power poles, a trailhead lo (prop, vis 3): 53 boxes. 
- walls (with their door / window cuts) (building, vis 3): 48 boxes, 8 copies. `wall()`
- the cabin (site A): log walls, a porch, a door front and back, a stepped roof, a stone chi (prop, vis 3): 40 boxes. 
- chain-link fence (building, vis 3): 40 boxes. `fence()`
- switchback stairs (building, vis 3): 39 boxes, 2 copies. `stairs()`
- ...and 11 smaller groups (224 boxes)

## deadmall: 303 boxes left
- walls (with their door / window cuts) (building, vis 3): 123 boxes, 9 copies. `wall()`
- windows: an opening in the outside wall (sill 0.9 m) onto a boarded-up back alley the zomb (building, vis 3): 96 boxes. 
- ARCADE: three rows of back-to-back cabinets (gaps halfway down), screens glowing on both s (prop, vis 3): 18 boxes. 
- the rest of deadmall() (building, vis 2): 12 boxes. 
- FOOD COURT: tables in a 3x3 grid (lanes between them), a burger counter in the corner (prop, vis 2): 11 boxes. 
- ENTRANCE HALL (start): an info kiosk to run round, two pillars, benches under the boarded  (prop, vis 2): 8 boxes. 
- TOY STORE: three full-height shelves = three loops (prop, vis 2): 8 boxes. 
- ATRIUM: the elevator core in the middle (the big loop), planters, the mystery crate on the (prop, vis 2): 8 boxes. 
- ...and 4 smaller groups (19 boxes)

## backrooms: 1825 boxes left
- walls (with their door / window cuts) (building, vis 5): 1479 boxes, 8 copies. `wall()`
- pillar rooms (building, vis 3): 119 boxes. 
- ground slabs with holes (stairwells, canals) (ground/rock, vis 3): 59 boxes, 4 copies. `groundHoles()`
- the pool rooms: flooded, white tiles everywhere, under the west side of the map (building, vis 3): 32 boxes. 
- switchback stairs (building, vis 3): 30 boxes. `stairs()`
- office cubicles (prop, vis 3): 28 boxes. `cube()`
- the big hall: sparse pillars, a few freestanding walls (one has a doorway to nowhere), low (building, vis 3): 17 boxes. 
- ceilings: a low drop ceiling everywhere, the hall's way up high. the light panels are part (building, vis 2): 29 boxes. 
- ...and 6 smaller groups (32 boxes)

## jankburg: 9448 boxes left
- walls (with their door / window cuts) (building, vis 5): 3668 boxes, 9 copies. `wall()`
- the outer ring: shanty walls, scaffold, junk barricades (building, vis 5): 1118 boxes. `outerRing()`
- the city houses (shanty blocks, TVs, AC, junk) (building, vis 5): 998 boxes. `cityHouse()`
- the city wall with its neon strip (building, vis 5): 822 boxes. `cityWall()`
- the megacity out in the haze (render-only towers, the JankCorp megatower) (building, vis 4): 444 boxes. `skylineHaze()`
- switchback stairs (building, vis 4): 418 boxes, 6 copies. `stairs()`
- upper facades of the city blocks (windows painted on) (building, vis 4): 344 boxes, 10 copies. `upper()`
- building shells: floors, walls, stairs inside (building, vis 4): 308 boxes, 17 copies. `shell()`
- ...and 23 smaller groups (1328 boxes)

## crate: 57 boxes left
- the rest of crate() (prop, vis 3): 57 boxes. 

## range: 170 boxes left
- the rest of range() (prop, vis 2): 163 boxes. 
- the horizon floor out past the map (ground/rock, vis 1): 4 boxes. `horizon()`
- ad boards (prop, vis 1): 3 boxes. `adBoard()`
## How to read it
- The labels are the map code's own section comments and function names, so a few are loose (Islands' biggest "ground" entry is the islands' sand, shelves and shallows, filed under the section they are built in).
- Skyline, Rooftop and Jankburg are dominated by look-only city backdrop (`cityBeyond()`, `streetLevel()`): thousands of boxes, but far away. Rank by vis first.
- Counts are boxes, not triangles: one Blender model usually replaces 10 to 100 boxes.
- Mount Kaboom's ground is the heightfield now; its dressing model is `kaboom`. The shipwreck is a Blender model (`wreck`, `tools/blender/arch/make_wreck.py`). Skull Rock, the lighthouse and the fort are still boxes.
