# JANKFIRE on Roblox: the port plan

Written 2026-11-14, updated the same day after the foundations pass. Place: "Jankfire.." (placeId 96891323589901), saved at version 77.
Counts come from the web game's own data (`shared/weapons.js`, `shared/modes.js`, `shared/map.js`) and from the open
Studio place, read the same day.

## 1. Where the port stands

| part | web game | in Roblox now | notes |
| --- | --- | --- | --- |
| Movement | run, sprint, slide, bhop, air strafe, grapple, jump pads | **all of it**, plus swimming | done |
| Loadout weapons | 40 (20 primary, 14 secondary, 6 melee) | **5**: Redline, Marble Shotgun, Katana, Shredder, Assault Rifle | the Shredder is a one-off Tool, not in the normal weapon system |
| Items (G) | 13 | 0 | |
| Killstreaks | 9 | 0 | |
| Game modes | 12 (Deathmatch, Team DM, Tags, Plant & Defuse, Randomizer, Gun Game, Infection, Zombies, Spoons, Duck Rain, Lava, One in the Chamber) | 0 of those | Roblox has its own thing instead: hub pads for 1v1, 2v2, 3v3, 4v4 and 1v1v1, first to 5 rounds |
| Maps | 11 (+ Plant & Defuse twins) | **1**: Rooftop | plus the hub and training hall, which only exist on Roblox |
| Bots | play every mode | 0 | training has two dummies |
| Loadout screen | yes | **yes**, with all 102 wraps, saved | 36 weapons show as "coming soon" |
| Accounts, levels, achievements | yes | only the loadout is saved | |
| Cosmetics, crates, shop | yes | wraps only | |
| Big modes | Zombies, Jank Royale, Battle Island, Board Game Night, OVERDUE story | none | |
| Sounds | made live in code | **all 32 uploaded and loading** (the game was silent until 2026-11-14: the 31 step-2 files had never been uploaded) | 32 of the 100 uploads per 30 days used (2,000 if the account is ID verified); 12 more gun shots are rendered and waiting in `roblox/assets/sounds` |
| Code | | about 8,600 lines of Luau | exported to `roblox/src` on branch `claude/f-roblox-studio` |

## 2. Fix these first (before adding 36 more weapons)

Done on 2026-11-14: 1, 2 and 3, and the 31 missing sounds are uploaded. Still to do: 4.

1. **DONE. Get the Studio work into GitHub.** Exported with `StudioExport` (see `roblox/README.md`), rebuilt with `rojo build roblox/studio.project.json` as a check, pushed as `claude/f-roblox-studio`. Original note: the hub, matches, loadout screen and every fix since step 2 live only in the
   Studio place. If the place breaks, they're gone. Plan: save the place to a file and run `rojo syncback` (Rojo 7.7+),
   which writes every script back out as files. Needs a writable copy of the repo: `D:\Robloxd\jankfire` is locked.
2. **DONE. Make "a plain gun" cheap to add.** A plain gun is now one row in `Weapons.luau` (stats, `fx`, `snd`, `mdl`), a model from `export_weapons.py`, a sound from `render_guns.mjs` and a reload from `reloads.mjs`. The Assault Rifle went in this way with no code of its own. Original note: three weapons take 774 lines in `Arsenal` today. Before the next batch, plain
   guns should be one stats row + a model + sounds + a hand pose, with no new code per gun.
3. **DONE. Hit checking that forgives lag.** `Fight.path` / `Fight.sees` look back 0.6 s along the target's trail, and `Rules.aimed` refuses shots that never pointed at the target. Original note: the server should remember where everyone was for the last 0.2 s and check hits
   against that, so a fast player isn't "missed" on a laggy connection. Every gun shares this, so it goes in once, now.
4. **Safer save data** (ProfileStore) before levels, coins or cosmetics are saved. The loadout can stay as it is until then.

## 3. The order to port things

The repo already has the full spec for every weapon, item, killstreak and mode, traced from the web game's code:
`roblox/docs/WEAPONS.md` and `roblox/docs/MODES.md` (on GitHub `main`). Build from those, in their order:

- [x] Step 1: movement + Rooftop
- [x] Step 2: Redline, Marble Shotgun, Katana
- [x] Hub, pad matches, training hall, loadout screen (Roblox only)
- [ ] **Batch 3, plain guns (1 of 12 done: Assault Rifle):** SMG, Plan B, Revolver, Shotgun, Half a Shotgun, Sniper, Second Opinion, Hat Trick, Belt Sander, Lawn Mower, Yeehaw. Adds aiming down sights, shotgun jumps, sniper knockback.
- [ ] **Bots + a real Deathmatch** with the end-of-match vote. Bots also let one person test everything. Already written on branch `claude/f-roblox-core` (BotBrain, Bots, Vote, MatchUi, Modes, Maps), built from step 2: it needs merging with the Studio code, not rewriting.
- [ ] **Batch 4, things that fly (7):** Chicken Rocket, Peel Shooter, Bowling Ball Launcher, Tennis Ball Launcher, Nail Gun, Bow, Snowball. Adds server-run projectiles, explosions, bounces, peels on the floor, freezing.
- [ ] **More maps**, one at a time. The converter (`tools/roblox/convert.mjs`) already turns a web map into Roblox parts box for box. Suggested order: Crate, Warehouse, Platform, Suburb, Desert, Bazaar, Islands, Skyline, then Backrooms, Scary Forest, Dead Mall. A second arena also lets two matches run at once (today there is one arena, so matches queue).
- [ ] **Team modes:** Team Deathmatch, Tags, then Plant & Defuse without the shop.
- [ ] **Batch 5, melee and thrown (5):** Bread, Knife, Hand Slapper, Slipper, Scales of Justice.
- [ ] **Batch 6, sprays, beams and status (9):** Minigun, Big Laser Pointer, Cigarette, Leaf Blower, Water Pistol, Taser, TV Remote, Blood Cross, and the Shredder moved into the normal system.
- [ ] **Batch 7, the odd ones (4):** Lefty & Righty, Card Deck, Lasso, Shopping Cart Cannon.
- [ ] **Items (13), then killstreaks (9).** Overdrive Rig, Wrecking Ball and Mech Drop last.
- [ ] **Cheap chaos modes:** Randomizer, Spoons & Grapples, One in the Chamber, Infection, Floor Is Lava, Duck Rain, Gun Game.
- [ ] **Levels, cosmetics, crates, shop**, and Plant & Defuse's buy menu.
- [ ] **Big modes, each a project of its own:** Zombies, Jank Royale, Battle Island, Board Game Night. OVERDUE only if asked.

## 4. How each batch gets done

1. Read that batch's section of the spec.
2. Code it, with the server deciding hits, damage and ammo (Roblox cheaters can send anything).
3. Models from Blender (the web game's weapon models already exist; they need the Roblox export, then colours put back by hand, because uploads drop them). Hero models at extra-high effort, never max.
4. Sounds rendered to files and uploaded.
5. Play test, two players for anything that hits people. Console clean. Overlap check for anything placed.
6. Save the place, export to GitHub, update the notes.

One batch at a time. Usage is limited and a session can end at any moment, so every batch ends saved.

## 5. Roblox rules that change the game

- **The Cigarette can't ship as a cigarette.** Roblox bans showing tobacco and its gear, and it's the default secondary. It needs a Roblox-safe look and name with the same gimmick (hold to charge, let go to breathe fire).
- **Blood and gibs:** cartoon violence is fine if the experience's Maturity questionnaire is answered honestly (violence, blood). Realistic gore gets moderated whatever the label. The Shredder and Blood Cross are the ones to watch.
- **Phones:** most Roblox players are on phones. The game is keyboard and mouse only right now.
- **Performance:** aim for under about 500 to 1,000 draw calls. The hub now has around 100 lamps and 737 props, so it needs a check on a weak device before launch.
- **Server size** is set to 60 players. With one arena that should come down.

## 6. Tools and skills (researched 2026-11-14)

- **Keep:** the built-in Roblox Studio MCP (the community ones are archived or tiny), headless Blender 5.3, Rojo (already installed, plugin too).
- **Add when needed:** `rojo syncback` for the GitHub export; ProfileStore for save data; StyLua + Selene to check Luau outside Studio.
- **Maybe later:** Zap or Blink (faster networking) if bandwidth becomes a problem; FastCast2 as reference reading for projectiles.
- **Skip:** community "Claude skills for Roblox" packs (a handful of commits each; our own notes cover more), community Studio MCP servers, SimplePath for arena bots (can't do jumps or grapples).
- **No new Studio plugin is needed yet.**

## 7. Decisions for the owner

1. **Repo folder:** unlock `D:\Robloxd\jankfire`, or let Claude keep a fresh copy in a folder it can write to?
2. **Phones and controllers:** PC only for now, or plan for touch from the start?
3. **Web modes in the hub:** more pads (one per mode), or a mode board that picks for the whole server?
4. **The Cigarette:** what does it become on Roblox?
5. **Lobby menus like the reference screenshots** (shop, season pass, daily tasks, backpack, profile cards, weapon inspect): wanted, and before or after the weapons?
6. **Players per server.**
7. **Which of the five hubs becomes the real one** (section 10). The comparison pictures were sent on 14 November.

## 8. The training hall, 14 November 2026 (place version 84)

- **A warehouse now.** Kit `wh_*` (10 models, `tools/roblox/warehouse_models.py`): two lines of columns (x +-56), five roof girders with 40 light panels (the old thin trusses and pendants are in `PolishBackup.HallCeilingV1`), a mezzanine along the north-west wall (deck 14 up, stairs at x -42, rails, crates), eight bays of racking in the south-west, a pink van, a forklift, crate stacks, three roll-up doors (shut: the hub stays enclosed), floor paint, metal wall cladding. All in `TrainingGround.Scenery.Warehouse`; collision pieces are `PropCollision.WH_*`. Two containers were slid aside for columns (attributes `WHMoved`, `WHMoved2`).
- **Cardboard Carl's** (east strip): `ServerScriptService.Jankfire.RangeTest`. Stand on CHILL / NORMAL / SWEATY: 25 cardboard men, one at a time; the board counts. A Carl is a real "dummy" fighter, so every weapon works on him. While you run, the Plinker leaves you alone (player attribute `RangeRun`). Map data: `TrainingGround.Range` (Plates, Spots, Board); dressing in `Scenery.CarlsLane`. Models: `tools/roblox/range_models.py`.
- **The secret playground:** a block course in the open air at z -9400. Way in: the bullseye of the middle wall target in the hall, 14 studs up (`Hub.Doors.ToPlayground`). Zone "playground" (its own look in `HubLook`), a fall puts you back on its start, the cyan door leads back to training. Its tile comes from `tools/roblox/grid_tile.mjs`; the MaterialVariant `MaterialService.JankGrid` (SmoothPlastic, ColorMap `rbxassetid://93738886844159`, 8 studs per tile) is in the export since 14 November: `place/MaterialService/JankGrid.rbxm`.
- `OverlapCheck`: things named "Mezzanine..." are skipped (stuff stands under and on the deck by design); `Column` and `Girder` count as frames.

## 9. How things should look (owner, 14 November 2026)

The owner showed a duels lobby and said its models "are not complex but they look better", then asked for the training hall as a warehouse or garage because it was "big with a lot of empty space". For every new model and room:

- **Few big shapes, every sharp edge rounded off.** In Blender: a 2-step bevel on each primitive, smooth shading, a Weighted Normal modifier (`warehouse_models.py` does it in `_bevel` and `flush`). No sharp-edged boxes, no fiddly small parts.
- **Flat colours** (SmoothPlastic): a few greys plus the JANKFIRE accents. Mid values, not near-black: a dark colour under Roblox light is just black.
- **Light comes from plain white panels** in chunky housings, with a real light behind each.
- **Fill a big room with big things** (structure, a second level, vehicles, tall racking), not with more small props.
- Still to redo in this style: the older `bc_*` props, the Rooftop. The rotunda was restyled with the `hb_*` kit (section 10).

**Example bank** (pictures and two recordings the owner sent the same day; they show kinds of things, never looks to copy):

- Weapon skins that reshape the whole gun round a silly theme, with a small charm hanging off it, shown in an inspect view with the lobby blurred behind.
- Kill effects as things you collect; an equip screen where your character performs the weapon's moves on a turntable.
- A lobby that is a real place: pads in rows by team size, bundles on pedestals, stalls, a quick-play bar with mode tabs, party slots, a "join this duel" card, daily tasks, a currency counter.
- Fast, bright matches: big readable maps under a big sky, strong colours, speed.
- Characters and pets with name tags.

Order when it gets built: save data first (ProfileStore), then skins + charms + the inspect view, kill effects, the quick-play bar; pets and trading last.

## 10. Five hubs to choose from, 14 November 2026 (place version 149)

The owner asked for five different-looking hubs built on the same principles, checked by a reviewer against their reference pictures, so they can pick the best. **They have the comparison pictures and have not picked yet.**

- **Hub 1, The Rotunda:** the live hub (`Map.Hub`), restyled with the `hb_*` kit by `PolishBackup.HubReskin`. Older meshes are in `PolishBackup.HubV5`; the pieces taken out in the fix pass are in `PolishBackup.HubV6`, each with a `From` attribute saying where it came from.
- **Hubs 2 to 5** (The Platform, The Lanes, The Food Court, The Depot): built by `PolishBackup.HubLab` (`L.build("Hub3_Lanes")`, `L.buildAll()`) under `Map.HubLab`, at x -600 / -200 / 200 / 600, z -10000. A build wipes and remakes its hub, so change the builder, never the built parts. Kits `st_*`, `bw_*`, `fc_*`, `dp_*` (`tools/roblox/station_models.py`, `lanes_models.py`, `foodcourt_models.py`, `depot_models.py`, `giantfood_models.py`; shared helpers in `chunky.py`), brought into the place by `PolishBackup.KitImport`.
- **Getting round:** four floor discs in the rotunda lead to the show hubs; each show hub has NEXT HUB and HUB 1 discs and a real training door. Any part in `Hub.Doors` with a `Land` attribute is a door (`LaserDoors`). A part in `Hub.LookZones` with a `Look` attribute sets the lighting for whoever stands in it (`HubLife`; looks `lab_platform`, `lab_lanes`, `lab_foodcourt`, `lab_depot` in `HubLook`). The server counts all five as "hub", so weapons stay holstered.
- **How they were judged:** each hub was tuned, photographed in a play test, reviewed, second-checked, fixed (about 80 fixes, plus shadows on the main lamps and tiles, carpet or concrete on the big floors), photographed again and ranked by three judges. Result out of 10: Lanes 7.0, Food Court 6.5, Rotunda 6.0, Platform 5.8, Depot 5.7. The reviews, photos and ranking live in the owner's local reference vault. That vault is not in git, because it also holds other games' screenshots.
- **Known weak spots:** the Lanes are very purple and the pads glare from the lane side; the Food Court's pads and stalls hide behind its fat columns; the Rotunda's pad corridor is dark and too close to one of the reference pictures; the Platform's arrival hall is the emptiest first view; the Depot is mostly grey. The shared `HubLab` helpers still paint pad bases, screen faces and the laser door's backing near-black.
- **After the pick:** move `QueuePads`, `HubSpawns` and the training door to the winner, update `OverlapCheck`'s zones, archive the rest. `Map.HubLab` then leaves the export by itself.
- **Export:** `StudioExport` now also covers `Map.HubLab`, the helper scripts `HubLab`, `KitImport` and `HubReskin`, the `MaterialService` variants and the sky's clouds. Left out on purpose: the backup folders in ServerStorage and Terrain's cells.
- **Animations:** Roblox Studio has a prompt-to-animation beta (standard R15 characters, announced 11 November 2026) that the Studio MCP can drive with `generate_animation`. It needs File > Beta Features > "Animation Generation in Assistant" ticked. Tried on four moves on 14 November (place version 149): fine as a quick draft maker for one-off gag moves (falls, flops, cheers, bot fidgets), no use for anything holding a weapon or for walking and running. Every clip comes out as a fixed 6 seconds, looped, with the real action in the first 1 to 3 seconds, so trim each one and turn looping off. Travel is baked into the LowerTorso joint, not the root. The four test clips are in `ServerStorage.RBX_ASSISTANT_ANIMGEN` and the test rig in `PolishBackup.AnimTrial`.

## For the next Claude session

- Recover state: memory `roblox-session-recovery`. Lighting: `roblox-zone-lighting`. Rules for the shared Studio: `studio-play-sharing`, `auto-save-place`.
- The local clone is stale and locked. Read the specs straight from GitHub:
  `https://raw.githubusercontent.com/tacosonmondays-pixel/jankfire/main/roblox/docs/WEAPONS.md` (398 KB; read "Core systems" once, then the weapon's own section) and `.../MODES.md`. Step 2's file map is in `roblox/README.md` on branch `claude/f-roblox-weapons`.
- Weapon stats live in `ReplicatedStorage.Jankfire.Weapons` (`list`), checks in `ServerScriptService.Jankfire.Rules` / `Combat`, the client in `StarterPlayerScripts.Jankfire.Arsenal` + `Viewmodel`.
- The spec's last section lists every place the web server trusts the client. The Roblox server must check those.
