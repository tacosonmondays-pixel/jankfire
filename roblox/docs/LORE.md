# The hidden NPCs, the Tall Guy From HR and the story cast (18 Nov 2026)

The owner: "Perhaps the hidden NPCs including guy from hr can be rehidden around hub areas? As well as the cast from
[the JANKFIRE] story?"

## What's where

| who | from the web | spot (`PolishBackup.LoreSpots.SPOTS`) |
|---|---|---|
| Gary, regional manager | `shared/secrets.js`, `public/js/lorenpcs.js` | back lot: the house's ground floor, at a desk |
| Dale, vending machine guy | same | back lot: behind the south-west container stack, at his machine |
| The Janitor | same | the basement boiler room, mopping |
| Mr. Smiles (retired mascot) | same | the playground: on the Hook pod, legs over the edge, balloons |
| Todd, intern (year 40) | same | training: on top of the course's far tower |
| Auntie Spreadsheet | `shared/story/content/cast_main.js`, `public/models/cast/c_auntie.glb` | training: the course's watch steps |
| Lumps | cast | the playground: a low west block, facing the sunset |
| Wee Gordo | cast | back lot: behind the south-east containers |
| Mina | cast | training: by the locked roll-up door in the course's egg corridor |
| Big Sauce Sharon | cast | back lot: the house's first floor |
| Dumpling | cast | the Rotunda: the gym, behind the tyres |
| Pallet Jack | cast | back lot: beside the garage |
| Employee of the Month | cast | back lot: on the finish tower |
| Mr. Overtime | cast | back lot: the far south-west corner by the fence |
| The Tall Guy From HR | `public/js/hrguy.js`, `shared/hr.js`, `server/hrguy.js` | rarely, on the back lot, to someone alone there |
| Biscuit (CFO, tabby, loaf) | `public/js/lorecats.js` | training: on the range canopy's roof over the gun shop |
| Beans (VP of sitting, tux) | cats | back lot: lying on top of the single container south of the house |
| Princess Gravy (chair of the board) | cats | the Rotunda lounge: sitting on top of the fridge |
| Meatloaf (head of synergy) | cats | the basement: flopped on his side by the boiler |
| Gremlin (head of legal) | cats | the Rotunda armory: in a cardboard box by the gun counter |

Left out (no gore): Dot and Mina grown into the flesh wall, Bev the meat mechanic, the Gut Choir, the Stomach Bishop.
Not yet: the Timekeeping Collector, the Unpaid Intern, Sister Agenda.

**The cats are parked** (owner, 18 Nov 2026: "No cats please"): `LoreData.CATS_ON = false`, so they are not built, don't count (LORE n / 15) and BOARD MEMBER is never granted (its row stays for anyone who has it; the profile hides an unowned secret). Everything below is kept so `CATS_ON = true` + `LoreSpots.build(LoreData.CATS)` brings them back.

The cats are ONE cohesive body each (the owner's rule for creatures, 18 Nov: no stacked primitives):
`tools/roblox/lore_cat_dump.mjs` (the web's `buildCat` in each cat's own pose, three moving pieces: body with legs,
head with ears, tail) + `blender -b -P tools/roblox/lore_cat_meshes.py` (each piece's solid parts voxel-remeshed and
smoothed into one skin, painted from the web's parts: stripes and patches win where they lie on the fur; eyes, nose,
crown, glasses, tie and lanyard kept on the surface). Pet them (their prompt): a purr, a slow blink, a headbutt, a
stretch, a roll, the odd swat. All five: the secret title BOARD MEMBER (`lore_cats`).

## How they're made (nothing redrawn)

1. `node --import ./tools/roblox/lore_register.mjs tools/roblox/lore_dump.mjs <dump>`: the web's own `lorenpcs.js`
   (with the real `models.js` and `clothes.js`) in Node. Every node the web's `update()` moves is a joint; every mesh
   goes into its joint's frame (studs, 3 per web metre). Canvas panels become their background colour (no text).
   Mr. Smiles' painted face and Todd's checker cube are made as shapes.
2. `tools/roblox/lore_hr_dump.mjs`: the web's `buildHR`, copied (its module pulls in the whole client).
3. `tools/roblox/lore_cast_dump.mjs` (the web's `buildLook` code skeleton and face rig) +
   `blender -b -P tools/roblox/lore_cast_meshes.py` (the cast's own `.glb` parts into the same joint frames; each face
   one colour: its picture sampled at the face's middle, softened toward the picture's average).
4. `blender -b -P tools/roblox/lore_meshes.py -- <dump> <out>`: one `.glb` per NPC, one mesh per joint, vertex colours
   (a step calmer), `rbxglb.turn_for_roblox`. Upload each as a Model (Open Cloud, from the approved folder).
5. `node tools/roblox/lore_rigs.mjs <dumps> <pieces.json> <assets.json> roblox/src/shared/LoreRigs.luau`.

## In the game

- `Shared.LoreData`: the book (names, titles, the web's lines trimmed, gifts, idle styles). `Shared.LoreRigs`: the rigs.
- `workspace.Map.Lore` (built by `PolishBackup.LoreSpots`: `L.build()`, `L.hr()`, `L.check()`), outside every hub
  builder. `ZonePiece = true` (ZoneCull drops it in matches). Bodies: no collisions, no queries (unshootable).
- `server/LoreNPCs.server.luau`: walking within reach of one finds it (once per player, own store `JankfireLore_v1`),
  gifts through `Loot.grant` (Dale a Spray Can, Todd a Crate, the Janitor the Plunger grapple and Smiles the Balloons
  kill effect, or a Duffel Bag when that can't be given), player attributes `LoreFound` / `LoreTotal` / `LoreList`,
  shown only on the profile card ("LORE n / N"). `ServerStorage.LoreTest`: state, find id, forget id?, near id.
- `client/LoreLife.client.luau`: the web's `update()` maths for the five, the web's `actors.js` standing pose and CLIPS
  for the cast, head turns, speech bubbles over their heads (the opening beat when you come near, the next on TALK).
- `server/HrGuy.server.luau` + `client/HrGuy.client.luau`: the HR stalk (moves only when nobody looks; staring fills
  your meter `HrStare`: static from plain frames, a washed-out shaking picture, a recorded hiss). Rare: back lot only,
  a lone player, 15% every 90 s after 60 s there, at most once in 20 min each. Never hurts: a catch is 1.2 s of static
  and a boom, then the spawn lounge (a `TeleportT` stamp first); it counts as finding him. `ServerStorage.HrTest`:
  state, come, leave, take.
