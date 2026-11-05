# JANKBURG: city map design brief

The big Battle Royale map (queued in HANDOFF.md). Plan it on paper first, then build a kit, then fill it in.
Build order follows the owner's steps: plan -> kit -> house variants -> districts -> landmarks.

## The vibe (applies to every map, not just this one)
JANKFIRE is **cyberpunk crossed with Nubby's Number Factory and Cruelty Squad**. We take the *feel*, never the content:
no names, logos, characters, textures, layouts or UI art from those games.
- **Cruelty Squad energy:** ugly on purpose. Clashing, noisy, over-saturated textures (acid green ceilings, magenta
  walls, leopard-camo floors), low-poly bodies with stretched textures, gore splats that stay, fleshy/biomech HUD frame
  around the screen, corporate-dystopia text in a deadpan voice ("Your organs have been leased.").
- **Nubby's energy:** shiny, rubbery, late-90s CG. Glossy balls and blobs with googly faces, chrome tubes, bubbly
  bevelled red title letters, puffy clouds, toy-like buttons that squish. Upbeat and a bit creepy.
- **Cyberpunk glue:** neon signs, ads everywhere, cables strung between buildings, rain-wet streets, a megacorp that
  owns the city. It's a cheap, cursed, corporate city, not a cool sleek one.
- **Readable through the jank:** player silhouettes, objectives, loot and the zone must always pop against the noise
  (outlines/rim light on players, loot glows, the zone wall is a single loud colour nobody else uses).

## 1. What the map is for (decide before drawing)
- Battle Royale: 16-24 players (humans + bots), about 8-12 minutes a match.
- Also reusable: Plant & Defuse sites inside two districts, and smaller "slices" of the city as regular arena maps later.
- Scale guide: Skyline spans about 260 m. The city is about **360 x 360 m inside the walls** plus an outer ring
  (sprawl, farms, slum) out to about 480 m where the first zone starts.

## 2. Master plan (draw this first, all numbers in metres, centre = 0,0)
```
                 N GATE (Data Gate)
   +---------------------||----------------------+
   |  STACKS        |  CORP HILL     |  NEON      |
   |  (slum towers, |  (HQ tower,    |  MARKET    |
   |   cables,      |   cathedral)   |  (stalls,  |
   |   verticality) |                |   arcades) |
W  |-------- ring road -----+------------ ring ----| E
GATE ===== main avenue === PLAZA === main avenue ===== GATE
   |                         (fountain)            |
   |  NUMBER WORKS  |  SUBURB POD    |  DOCKS /    |
   |  (factory,     |  (cul-de-sac,  |  WAREHOUSE  |
   |   tubes, vats) |   houses)      |  YARD       |
   +---------------------||----------------------+
                 S GATE (Freight Gate)       -> canal + waterfront park to the SE
```
- **City wall:** a 14 m tall corporate "firewall" ring, square with chamfered corners. Climbable only at
  broken sections (3-4 breaches) and via grapple. Towers every ~60 m (sniper perches, but exposed).
- **Gates (4):** N Data Gate, S Freight Gate, E and W Toll Gates. Each is a chokepoint with a booth, barrier arms and
  cover inside and out. The zone often forces fights through these, so give each gate a side passage.
- **Main roads:** one cross of wide avenues (20 m) from gate to gate through the plaza, plus a ring road ~90 m from
  centre. Streets off them are narrow (6-10 m) and crooked, like a real old downtown grid with a couple of diagonal
  cuts, so there are long sightlines on the avenues and close fights in the side streets.
- **Plaza:** 60 x 60 m in the centre. Fountain in the middle (cover + landmark), billboard screens on all sides,
  underpass/metro entrances to flank under it.
- **Districts (6):** each has its own colour, materials, loot tier and way of fighting:
  | District | Feel | Fights | Loot |
  |---|---|---|---|
  | Corp Hill (N) | glossy HQ tower, the cathedral, clean plazas | long range, high ground | high |
  | Neon Market (NE) | stalls, arcades, hanging signs, noodle bars | close, chaotic | medium, lots of items |
  | The Stacks (NW) | slum towers joined by cables and bridges | vertical, grapples | medium |
  | Number Works (SW) | toy factory: tubes, vats, conveyor belts, giant glossy number balls | mid range, hazards | high |
  | Suburb Pod (S) | a cul-de-sac of houses in a walled "model home" lot | house-to-house | low-medium |
  | Docks / Yard (SE) | warehouses, containers, forklifts, fenced yard, canal | mid range, cover hopping | medium |
- **Outer ring:** shanty sprawl, orchards of fake plastic trees, a crashed delivery blimp, highway stubs. Players drop
  here or inside; the first zone circle always contains at least part of the city.
- **Bots:** plan the bot walk graph with the roads. Every district needs 2+ entrances, every roof a way back down,
  and drop spots should be tagged (hot/medium/quiet) so bots spread out.

## 3. Modular kit (code, not Blender)
Maps are lists of axis-aligned boxes built in `shared/map.js`, the same data the server uses for physics and bots.
Blender isn't installed in the cloud session, and imported meshes would need hand-made box colliders, so the kit is
**JS builder functions**, the same way `house()`, `tower()`, `wall()`, `shell()` and `stairs()` already work.
- Kit pieces: `cityWall(segment)`, `wallTower()`, `gate(kind)`, `roofKit(type)` (flat, stepped, sawtooth, dome, antenna
  farm), `shopfront(sign)`, `stall(kind)` (noodle, arcade, junk, "organ leasing"), `cableSpan(a, b)`, `billboard()`,
  `neonSign()`, `container()`, `vat()`, `tubeRun()`, `numberBall(n)`, `streetFurniture()` (bins, hydrants, vending).
- Each piece takes a local frame (`B.local(ox, oz, rot)`), a seed and a palette, and returns where its doors and roof
  points are so streets and bots can connect to it.
- If a hero landmark ever needs a real mesh (the cathedral), model it in Blender on the owner's machine, load it as a
  visual-only glTF, and keep the gameplay version as boxes underneath. Not needed for the first version.

## 4. House variations (12 from one kit)
One `cityHouse(B, ox, oz, rot, variant, r)` with parts picked by variant: footprint (narrow, wide, L, corner),
floors (1-4), roof (flat with AC, stepped, pitched with antennas, dome, garden), facade material, door and window
layout, balcony, fire escape, shop on the ground floor or not, neon sign.
1. Capsule stack (stacked sleep pods, ladders) 2. Noodle shop + flat above 3. Corner bodega with roof garden
4. Narrow 4-floor walk-up with fire escape 5. Glossy "model home" (Nubby-shiny plastic) 6. Rusted container house
7. Tagged squat with a hole in the wall 8. Corporate dorm block 9. Arcade with a flat on top 10. Pastel suburb house
11. Bio-lab front (green glass, vats inside) 12. Pawn/repair shop with a garage door.
Every house is enterable, has at least 2 exits, and no two variants on the same street share a facade colour.

## 5. Populate the districts
- Fill blocks street by street from the plan, not randomly: houses face the street, backs make alleys.
- Gardens and orchards: plastic hedges, glossy toy trees, rooftop hydroponics.
- Market areas: stall rows with 2 m gaps, hanging cables and signs overhead (cover from the sky, not from bullets).
- Loot spots are part of the layout: every building gets 1-3 marked spots, districts follow the loot table above.
- Keep a box budget per district and test on the "Potato" and "Too HD" presets with 24 players before adding more.

## 6. Landmarks (placed exactly where the plan puts them)
- **The Cathedral of Shareholder Value** (Corp Hill, north of the plaza): a corporate megachurch with a stained-glass
  stock ticker, pews, an organ made of server racks, a bell tower you can grapple to. The best sniper spot, so it
  has no cover on its approach roof.
- **Plaza fountain:** a giant glossy smiling ball spitting water (Nubby-style), ring of benches.
- **Neon Market hall:** the covered marketplace at the NE corner of the ring road; a two-level gallery inside.
- **Number Works smokestacks:** visible from everywhere, so players can tell where they are.
- **HQ tower:** the tallest thing in the city; the final zone is never on its roof.
- Every landmark should be recognisable from the drop (helps callouts and the minimap).

## Done when
- The plan above is drawn as a top-down image and agreed with the owner before kit work starts.
- A full bots match runs: bots drop, loot, rotate with the zone and the match finishes in under 12 minutes.
- Frame rate holds on Potato with 24 players; no gaps or flickering faces (see the rule at the top of `shared/map.js`).
