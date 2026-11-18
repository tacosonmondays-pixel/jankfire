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
| Todd, intern (year 40) | same | training: the dummies hall, on the west gantry tower's cap (since v3) |
| Auntie Spreadsheet | `shared/story/content/cast_main.js`, `public/models/cast/c_auntie.glb` | training: the course lobby's west bench (since v3) |
| Lumps | cast | the playground: a low west block, facing the sunset |
| Wee Gordo | cast | back lot: behind the south-east containers |
| Mina | cast | training: on the gallery beside the gold dummies' locked roll-up door at the course's TOP frame (since v898) |
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

## Hidden until its code: the code panel (18 Nov 2026)

The owner: "Can jankfire npc's be hidden unless you do a very specific thing", then "Its not very hidden, there should
be a control panel somewhere that you type in jank actually make codes and every code spawns in an NPC, ill give the
codes weekly by weekly at some point".

- **Not in the world until its code** (the owner, later the same day: "can you remove the jankfire npcs? when you type
  in the codes you'll get a cutscene where an npc walks in and then they'll appear somewhere!"). Every NPC's model and
  the hub egg's mannequin (`Lore_egg`) live in `ServerStorage.JankfireLore`: nothing stands in the map (LoreSpots
  builds them there; `L.migrate()` and LoreNPCs' own `migrate()` move any a builder leaves in `Map.Lore` or
  `Map.Hub.HubEgg`). Each player is given copies of only the NPCs THEY have revealed, in their own
  `PlayerGui.LoreDelivery` (a hidden ScreenGui: a PlayerGui reaches only its player), and their `LoreLife.client` puts
  each in `workspace.LoreLocal` at its spot. So nobody else sees it, and nothing unrevealed reaches a client at all.
  The HR guy never visits, and isn't drawn for, anyone whose `LoreSeen` lacks `hr`; `HubEgg.server` ignores touches and
  its prompt until `egg` is there.
- **The panel**: `workspace.Map.Lore.CodePanel`, a chunky terminal (plinth, cabinet with one trim band, a console
  leaning toward you with a dim screen and a row of keys). Built by `PolishBackup.LoreSpots.panel()` where `L.PANEL`
  says (data: `at`, `look`, `show`). Its prompt ("Code", E / X) opens `CodePanel.client`'s screen: CODE, a box,
  ENTER. Keyboard (the box takes the keys, Enter sends, Esc closes), controller (PadNav: the box is picked first, A
  types, B backs out) and phone (tap the box). Hub only (MenuGate `lorecode`); closes when you walk 16 studs off.
- **A right code** (`LoreNPCs.server`, remote `LoreCode` "try"): the NPC is revealed for you for good (saved in
  `JankfireLore_v1`: `seen`, and `codes` = when each was redeemed), its copy is delivered, and it counts as finding it:
  its gift and title as before (the mannequin's OG title through `ServerStorage.HubEggFind`, and the Mini Mannequin pet
  with it via PetSecrets). Then **the cutscene**, on your screen alone (`LoreLife.client` startCut, about 7.5 s): your
  controls and the HUD go, black bars, a soft chime, and the camera cuts to the panel. The NPC walks in (a procedural
  walk on its own leg joints; Gary, Todd and Mr. Smiles stand up from their seats for it) to the panel's `Show` spot,
  turns to you, greets you and says its first line and its gift line, then turns toward where it lives and walks off as
  it fades: the only hint, no text. The mannequin fades in on its plinth; the HR guy is a step closer at every cut and
  then simply gone. SKIP (Space, B, or the button) after the first 1.2 s; never in a match (it stops if a match takes
  you). Afterwards it's at its own spot for you to go and find. A code you already used plays it again with its
  "again" line, giving nothing new.
- **Reward codes** (book rows with `kind = "reward"`; what each gives: `REWARDS` in LoreNPCs): a code that gives items
  instead of an NPC, once per player (`Loot.grant` of shop-gui's `gift:<kind>:<id>` offers, one receipt per player and
  item; the save's `claims`). The screen shows what it gave (names from LootTable), or CLAIMED. First one:
  `ducky_classic`, the old Ducky trio (Bubble Bath LMG, Wish Duck revolver, Ribbon Duck katana), open from 18 Nov.
- **Codes**: `server/LoreCodeBook.luau` holds only salted, stretched SHA-256 hashes (`server/Sha256.luau`; the typed
  text made plain first: lower case, letters and digits only) and each code's opening day. **The plain codes are not in
  git or the game**: they're in the owner's vault, `JANKFIRE Vault/Codes.md`. A code before its day is just wrong.
  To move a week, change `opens` in the book (and the vault). Opening days (UTC):

  | opens | who |
  |---|---|
  | 18 Nov 2026 | the mannequin (`egg`) |
  | 23 Nov | Gary |
  | 30 Nov | Dale |
  | 7 Dec | the Janitor |
  | 14 Dec | Mr. Smiles |
  | 21 Dec | Todd |
  | 28 Dec | Auntie Spreadsheet |
  | 4 Jan 2027 | Lumps |
  | 11 Jan | Wee Gordo |
  | 18 Jan | Mina |
  | 25 Jan | Big Sauce Sharon |
  | 1 Feb | Dumpling |
  | 8 Feb | Pallet Jack |
  | 15 Feb | Employee of the Month |
  | 22 Feb | Mr. Overtime |
  | 1 Mar | the Tall Guy From HR |

- **Security**: the server checks every try (the code, its day, that you're within 24 studs of the panel and not in a
  match); 5 wrong tries, then a 60 s wait (saved, so rejoining doesn't skip it); half a second between tries; each
  redemption is logged (`[jankfire] lore code: <name> (<id>) -> <npc>` in the server log, and the save's `codes`).
- **Tests** (`ServerStorage.LoreTest`, Studio): `"code", text` (the real check as the first player, nearness
  skipped), `"clock", days` (the calendar runs that many days ahead), `"codes"` (which are open), `"unlock"` (clears
  the wait), `"hide", id?` (un-reveal and take the copy back; all with no id), `"reveal", id`, `"redeliver"` (what
  joining does), `"unclaim", id` (a reward's claim). From the client: `Remotes.LoreCode:InvokeServer("try", text)`.
  Photos of the cutscene: set the player attribute `LoreCutHold` = seconds (Studio only) and it holds at that moment
  (1.7 walk-in, 4.9 beat, 6.5 exit); clear it and it runs on. Check nobody else is pressing keys first: Space skips.
- **The parked first idea**: one secret action per NPC at its spot, judged by the server (`server/LoreTriggers.luau`,
  `TRIGGERS_ON = false` in LoreNPCs; written, never tested). Spoilers: Gary, salute facing his desk; Dale, shoot his
  machine 3 times in 8 s; the Janitor, stand still on the wet floor 8 s; Mr. Smiles, cheer on the Hook by his
  balloons; Todd, shoot the glitch cube 5 times; HR, wear REGIONAL MANAGER on the back lot 8 s; Auntie, shoot the tin
  on the watch steps 3 times; Lumps, face the sunset on his block 10 s; Wee Gordo, point on a chalk X; Mina, wait
  facing the roll-up door 12 s; Sharon, hook her red pot; Dumpling, dance by the tyres 5 s; Pallet Jack, hook his
  pallets; Employee of the Month, wear INTERN on the finish tower; Mr. Overtime, face his clock for a minute.

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
