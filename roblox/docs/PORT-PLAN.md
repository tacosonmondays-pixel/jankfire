# JANKFIRE on Roblox: the port plan

Written 2026-11-14, updated the same day after the foundations pass. Place: "Jankfire.." (placeId 96891323589901), saved at version 77.
Counts come from the web game's own data (`shared/weapons.js`, `shared/modes.js`, `shared/map.js`) and from the open
Studio place, read the same day.

## 1. Where the port stands

| part | web game | in Roblox now | notes |
| --- | --- | --- | --- |
| Movement | run, sprint, slide, bhop, air strafe, grapple, jump pads | **all of it**, plus swimming | done |
| Loadout weapons | 40 (20 primary, 14 secondary, 6 melee) | **16**: Redline, Marble Shotgun, Katana, Shredder, and the twelve plain guns (Assault Rifle, SMG, Shotgun, Sniper, Hat Trick, Belt Sander, Second Opinion, Yeehaw, Lawn Mower, Revolver, Plan B, Half a Shotgun) | the Shredder is a one-off Tool, not in the normal weapon system. Batch 3: section 12 |
| Items (G) | 13 | 0 | |
| Killstreaks | 9 | 0 | |
| Game modes | 12 (Deathmatch, Team DM, Tags, Plant & Defuse, Randomizer, Gun Game, Infection, Zombies, Spoons, Duck Rain, Lava, One in the Chamber) | 0 of those | Roblox has its own thing instead: hub pads for 1v1, 2v2, 3v3, 4v4 and 1v1v1, first to 5 rounds |
| Maps | 11 (+ Plant & Defuse twins) | **1**: Rooftop | plus the hub and training hall, which only exist on Roblox |
| Bots | play every mode | 0 | training has two dummies |
| Loadout screen | yes | **yes**, with all 102 wraps, saved | 24 weapons show as "coming soon" |
| Accounts, levels, achievements | yes | only the loadout is saved | |
| Cosmetics, crates, shop | yes | wraps only | |
| Big modes | Zombies, Jank Royale, Battle Island, Board Game Night, OVERDUE story | none | |
| Sounds | made live in code | **43 uploaded and loading** (the game was silent until 2026-11-14: the 31 step-2 files had never been uploaded) | 44 of the 100 uploads per 30 days used by 2026-11-15 (2,000 if the account is ID verified); two more gun shots are rendered and waiting in `roblox/assets/sounds` (Minigun, Lefty & Righty) |
| Code | | about 10,200 lines of Luau | exported to `roblox/src` on branch `claude/f-roblox-studio` |

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
- [x] **Batch 3, plain guns (all 12, done 15 November: section 12):** Assault Rifle, SMG, Plan B, Revolver, Shotgun, Half a Shotgun, Sniper, Second Opinion, Hat Trick, Belt Sander, Lawn Mower, Yeehaw. Added scopes, shotgun jumps, sniper knockback, bursts, the quick-scope, the damage ramp, fanning and ricochets, and guns whose parts move.
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
3. Models from Blender (the web game's weapon models already exist; `tools/roblox/export_weapons.py` turns them and writes each piece's look into its name, and Studio's `WeaponImport` paints them and checks the facing: nothing is done by hand, see `roblox/README.md`). Hero models at extra-high effort, never max.
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
7. ~~Which of the five hubs becomes the real one~~ Decided on 15 November: Hub 3, The Lanes (section 11).

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

The owner asked for five different-looking hubs built on the same principles, checked by a reviewer against their reference pictures, so they can pick the best. **They picked Hub 3, The Lanes, on 15 November: section 11 is how things stand now, and the rest of this section is history.**

- **Hub 1, The Rotunda:** the live hub (`Map.Hub`), restyled with the `hb_*` kit by `PolishBackup.HubReskin`. Older meshes are in `PolishBackup.HubV5`; the pieces taken out in the fix pass are in `PolishBackup.HubV6`, each with a `From` attribute saying where it came from.
- **Hubs 2 to 5** (The Platform, The Lanes, The Food Court, The Depot): built by `PolishBackup.HubLab` (`L.build("Hub3_Lanes")`, `L.buildAll()`) under `Map.HubLab`, at x -600 / -200 / 200 / 600, z -10000. A build wipes and remakes its hub, so change the builder, never the built parts. Kits `st_*`, `bw_*`, `fc_*`, `dp_*` (`tools/roblox/station_models.py`, `lanes_models.py`, `foodcourt_models.py`, `depot_models.py`, `giantfood_models.py`; shared helpers in `chunky.py`), brought into the place by `PolishBackup.KitImport`.
- **Getting round:** four floor discs in the rotunda lead to the show hubs; each show hub has NEXT HUB and HUB 1 discs and a real training door. Any part in `Hub.Doors` with a `Land` attribute is a door (`LaserDoors`). A part in `Hub.LookZones` with a `Look` attribute sets the lighting for whoever stands in it (`HubLife`; looks `lab_platform`, `lab_lanes`, `lab_foodcourt`, `lab_depot` in `HubLook`). The server counts all five as "hub", so weapons stay holstered.
- **How they were judged:** each hub was tuned, photographed in a play test, reviewed, second-checked, fixed (about 80 fixes, plus shadows on the main lamps and tiles, carpet or concrete on the big floors), photographed again and ranked by three judges. Result out of 10: Lanes 7.0, Food Court 6.5, Rotunda 6.0, Platform 5.8, Depot 5.7. The reviews, photos and ranking live in the owner's local reference vault. That vault is not in git, because it also holds other games' screenshots.
- **Known weak spots:** the Lanes are very purple and the pads glare from the lane side; the Food Court's pads and stalls hide behind its fat columns; the Rotunda's pad corridor is dark and too close to one of the reference pictures; the Platform's arrival hall is the emptiest first view; the Depot is mostly grey. The shared `HubLab` helpers still paint pad bases, screen faces and the laser door's backing near-black.
- **After the pick:** move `QueuePads`, `HubSpawns` and the training door to the winner, update `OverlapCheck`'s zones, archive the rest. `Map.HubLab` then leaves the export by itself.
- **Export:** `StudioExport` now also covers `Map.HubLab`, the helper scripts `HubLab`, `KitImport` and `HubReskin`, the `MaterialService` variants and the sky's clouds. Left out on purpose: the backup folders in ServerStorage and Terrain's cells.
- **Animations:** Roblox Studio has a prompt-to-animation beta (standard R15 characters, announced 11 November 2026) that the Studio MCP can drive with `generate_animation`. It needs File > Beta Features > "Animation Generation in Assistant" ticked. Tried on four moves on 14 November (place version 149): fine as a quick draft maker for one-off gag moves (falls, flops, cheers, bot fidgets), no use for anything holding a weapon or for walking and running. Every clip comes out as a fixed 6 seconds, looped, with the real action in the first 1 to 3 seconds, so trim each one and turn looping off. Travel is baked into the LowerTorso joint, not the root. The four test clips are in `ServerStorage.RBX_ASSISTANT_ANIMGEN` and the test rig in `PolishBackup.AnimTrial`.

## 11. The Lanes is the real hub, 15 November 2026 (place version 165)

The owner picked **Hub 3, The Lanes** (a bowling alley). It was wired in as the real hub, repainted and tested the same day.

- **Where things are:** `Map.Hub` holds `Lanes` (Shell, Scenery, Collision), `QueuePads` (five real pads: 1v1, 1v1v1, 2v2, 3v3, 4v4), `HubSpawns`, `Doors` (`HubArrive`, `TrainingArrive`, `PlaygroundArrive`, `ToPlayground`, `ToHub`, `FromPlayground`, `LanesToTraining`), the training hall and the playground as before, `Barrier` (now round the training hall only) and an empty `LookZones`. `Hub`'s `Origin` attribute is (-200, 240, -10000): the hub stayed on its show site. `Map.HubLab` is gone.
- **The builder is the source:** `PolishBackup.HubLab` has a live mode (`L.LIVE = "Hub3_Lanes"`). `L.build("Hub3_Lanes")` wipes and remakes the room, the pads, the spawn and arrival markers and the training door trigger (everything marked `Built=HubLab`) straight into `Map.Hub`. Change the builder, never the built parts. `L.check()` tests 21 keep-clear zones (spawns, pads, walkways) and looks for leaks in the shell; `OverlapCheck.run()` hands over to it. The six modes' words are baked into the builder.
- **The pads are real:** each pad Model has its team plates `Side1..SideN` (in the server's team order: pink, cyan, yellow), a `Slot` light per place (attribute `Off` = the transparency of an empty place, which `Matches` honours) and the lane's hanging board as `Sign`, with live `Status` and `Sub` lines on both faces. `Matches.padSign` writes every label named `Status` or `Sub` inside the pad. Lane 6 (5v5) is closed: its pad is scenery (`Lanes.Scenery.ClosedPad_5v5`).
- **The look:** the judges' two faults were fixed. Paint comes from one palette table in the builder, `L.LANES_PALETTES`; the default is `retro` (sand walls, teal ceiling, cream frame, the carpet the only purple). The owner saw the before and after on 15 November and chose to keep `retro`. `L.LANES_PALETTE = "purple"` and a rebuild bring back the look the owner first picked, with its purple light (a build writes the attribute `HubTint` on `HubLook`, which chooses between a neutral and a purple tint for `looks.hub`; with no attribute the tint is neutral). The pad plates are flat SmoothPlastic in the team colours with a dim white glowing edge, so they no longer bloom. `looks.hub` is the Lanes' look; the rotunda's is kept as `looks.rotunda`.
- **The other hubs:** the rotunda (with its pads, spawns, doors, barrier and tour discs) and the Platform, Food Court and Depot are parked in `ServerStorage.PolishBackup.HubArchive`, each with a `From` attribute. That folder is not exported; the last export that holds them as files is commit `8e0668d` (`place/Workspace/Map.Hub.rbxm` and `Map.HubLab.rbxm`). `L.build(name, true)` rebuilds an archived show hub under `Map.HubLab`. The rotunda's edit tools `CozyKit` and `HubReskin` no longer have a rotunda to work on.
- **Tested in a solo play test:** spawn in the Lanes with zone "hub" and weapons holstered, every pad counts players on both faces of its board and lights its places, the training door and the hall's door back, the playground route, a fall puts you back, no ray escapes the room, no script errors. **Not tested:** a match starting from a pad (it needs two players), and walking through the doors on foot (the test moved the character into the triggers).
- **Structure pass, later the same day (place version 176):** the owner said the Lanes looked simple next to another game's lobby ("its not the color is the struicture"), and then that the first hub was cute. `HubLab` has a second switch beside the palette: `L.LANES_STRUCTURE` is `"overlook"` (the default) or `"box"` (the room as it was, 910 things). `overlook` is the same alley, paint, signs and pads in a shaped room: a raised concourse (spawn and shops, 3 studs up) with steps and two ramps down to the lanes, a fin and a canopy at every lane's pins, a beam-and-coffer ceiling with the light panels set into it, the six boards in a gantry across the hall, piers and bays down every wall, and a deep recess at each end of the cross walk (training door west, arcade east). On top of that it has what the rotunda had: a balcony over the entrance with a small lounge and the hologram duck, two jump pads up to it (parts with a `Pad` attribute, which `Move` already reads) and a marked gap to step back down, a giant turning bowling ball hung over the middle (tag `HubSpin`, which `HubLife` already turns), awnings, globe lamps and bunting. No script outside `HubLab` changed. `Hub.Lanes` is 1,512 things with 93 lamps, 11 of them casting shadows. `L.check()` now also tests 256 sight lines from the spawn points to every pad, every board and the name. A tester that did not build it passed 17 checks: spawn, sight lines, pads counting, the routes on foot, both doors, enclosure, nobody trapped, the jump pads, and the switch back to `box`. Not tested: a match from a pad, and how it runs on a phone. Still weak: it is one big room, and the first hub's charm was separate rooms seen through doorways.
- **Left for later (minor, from the judges):** from the spawn the floor arrows out-shine the pads; the two end boards touch the HIGH SCORES and TONIGHT boards under them; the giant pin is darker than the sand wall behind it; the strip under the ball returns and the wall behind the name are the darkest surfaces; the sign faces are still near-black; the training hall's wall round its hub door is near-black.

## 12. Batch 3: the eleven plain guns, 15 November 2026 (place version 190)

All twelve plain guns are in: selectable in the loadout screen, with their models, sounds, reloads and gimmicks.
The table of every gun against its web numbers, what was measured, what differs and what was not tested is
`roblox/docs/BATCH3-GUNS.md`.

Saved in place version 190 (the hub session's save of 15 November, 15:56 UTC; not published). The same document
ends with a verdict on each gun's look against the owner's "serious, Rivals-style, less colourful" bar: only the
SMG passes as it is; the rest need a calmer factory paint, which is a table in `WeaponImport`, not new models.

- **The exporter was fixed first.** One test upload settled it (`tools/roblox/rbxglb.py` holds the measurements):
  uploads arrive turned half way round their up axis and lose plain colours; pictures and vertex colours survive.
  `export_weapons.py` now turns every piece before export and writes its look into its name; `PolishBackup.WeaponImport`
  paints from the name and refuses a model whose box does not match the exporter's. The re-exported Assault Rifle
  matched the hand-fixed one piece for piece (position, size and inner shape to 0.00001 studs) and replaced it.
- **New code:** `GunParts.luau` (client: the pieces of a gun that move, driven by the web game's own keyframes),
  `TestHook.luau` (server, Studio only: `ServerStorage.JankTest`), about 120 lines in `Rules` and 100 in `Combat`
  for the gimmicks, the scope overlay in `FightHud`, run speed per gun in `Movement` / `Move`. A plain gun is still
  one row; the gimmicks are row fields the shared code acts on (`burst`, `ramp`, `quick`, `fan`, `ricochet`,
  `lethalHead`, `kb`, `speedMul`, `cycle`, `mdl.parts`).
- **Stricter than the web server:** ricochet paths are walked with the server's own rays, a headshot from a
  one-bullet gun has to cross the head box, the quick-scope claim has to fit the server's own clock for the scope,
  the Hat Trick is capped on shots, the Revolver's cylinder is the server's mag. Each was tried with faked messages.
- **Tools that came out of it:** `tools/roblox/push.mjs` (script files into Studio as one uploaded model),
  `weapon_import_call.mjs`, the wider `reloads.mjs` (rifle pack, sidearms, pump / bolt / lever clips, moving parts),
  `--sil` and `--orient-test` on the exporter.
- **Not ported:** the off hand and its props in reloads, the Sniper's no-scope show (overlay, fireworks, Royalty),
  inspect animations, per-gun reload noises (they reuse the clicks: 56 audio uploads left this month).
- **Not tested:** anything with two players (what others see, a real player launched off the map, parrying these
  guns), phones. The offline tests added to `tests/weapons.luau` were not run (no Lune on this PC).
- **Left alone on purpose:** the hub kits (`chunky.py` + `KitImport`) still turn and paint themselves on import; they
  can move to `rbxglb.py` when the hub is not being rebuilt.

## 13. The hub is a bowling centre with rooms, 15 November 2026 (place version 203)

**The owner's direction for the whole Roblox game (15 November 2026): "This is serious compared to jankfire!" and "we're taking the wepaons and mechanics from jankfir ebut adding a serious roblox rivals touch to it, we really need to try on this".** So: JANKFIRE's weapons and mechanics, with a serious, restrained, Rivals-style finish. Inspired by, never copied. The same day they asked for the hub to be "less colorful". The web game's "jank, juice, comic" rule describes the web game, not the look of this place.

The overlook (section 11) was still one room. The research in the vault (`Research\Hub direction.md`) found that the lobby the owner admires gets its feel from several small, different rooms round a small round centre, each showing you the next through a framed opening. This is its option C, built the same day.

- **What it is.** You spawn in a round lobby (twelve sides, 48 across, its middle 84 south of the boards) on a stepped round platform under a ribbed dome, a big bowling ball turning over you. North: one opening 35 wide into the lanes hall, with all six boards in view from every spawn point. South, on the axis: an arch to a small brick lounge (sunk middle, a hologram ball you can see from the lanes through two doorways). East: a doorway and a step up to the snack bar and arcade. West: a low hatch and a ribbed passage to the training gate. A ring balcony runs round the lobby 13 up; its north side stands out into the hall as a bay you can look down the lanes from. Two jump pads go up; two gaps in the rail come down.
- **Switches in `HubLab`.** `L.LANES_STRUCTURE` is now `"centre"` (default), `"overlook"` or `"box"`. `L.LANES_PALETTE` is now `"calm"` (default) with `"retro"`, `"purple"`, `"sand"`, `"teal"` kept. **The hub as it was on the morning of 15 November is `L.LANES_STRUCTURE = "overlook"` with `L.LANES_PALETTE = "retro"`, then a rebuild.** Both older structures in the old paint still build to the part exactly what they built before (checked by sums of part count, positions, sizes, colours, lamps and text after every batch of edits, and by an independent tester).
- **How `centre` is built.** `L.LANES_BUILD.centre(H)` calls the overlook's builder with a second argument, which makes it leave the middle of its south wall open and skip what the lobby replaces (entrance roof, balcony, small lounge, jump pads, house ball, spawn, training door, arcade, snack bar), then builds the lobby and rooms with its own helpers (`at`, `side`, `seg`, `pier`, `ringSign`). The six boards are taller and higher in this structure, with the mode's name as the big line, because they are read from 85 studs away.
- **The `calm` palette is more than paint.** Off-white frame, grey walls and lid, grey carpet, pale wood, one dusty teal, pink as the only accent. Extra keys: `shell`, `pier`, `dome`, `cool` (the lobby is darker and heavier than the rooms it looks into, so every doorway frames a lit room), `remap` (repaints the loud dressing colours) and `sober` (takes out bunting, striped awnings, flower tubs and globe lamps, makes the house ball teal, swaps the joke lines on signs for plain ones from `L.LANES_WORDS`, and sets every label in Montserrat). Signs, boards and pads keep their colours.
- **`L.check()`** for this structure also tests, from every spawn point, a sight line to the name over each way out and to one thing inside each room (`L.LANES_SIGHTS.centre`). The pads themselves are behind the hall's parapet from the lobby, so their plates are counted, not required. Now: 25 zones, 0 problems, 0 leaks, 208 sight lines, 0 hidden.
- **Numbers.** `Hub.Lanes` 1,906 things, 1,463 parts, 126 lamps, 11 with shadows (the limit). No new meshes, no script outside `HubLab` changed. `HubLab` is 188,800 of Studio's 200,000 characters: the next big addition needs a second module.
- **Judged, not just checked.** An independent judge scored each main view on "would this hold up next to a Rivals lobby?", with a rework after each round. Round 1: 4.5 to 7, "closer to a tidy toy set". Round 2: 5 to 7.5, "the round lobby is now a serious room", the whole "progress, not finished". Write-ups: vault `Reviews\Bowling centre - judge round 1.md`, `... - judge round 2 and function test.md`, `... - final.md`.
- **Tested by an agent that did not build it (18 of 18):** names and attributes the server needs, spawn and arrival markers, lamps, nothing unanchored or near-black, its own sight and enclosure tests, both switches, fresh spawn, all five pads counting on both faces, the training gate both ways, both jump pads, the way down, real-key runs to every room, nobody trapped, falling out, things that turn, no script errors. After the last rework the pads, the gate and the jump pads were tested again by the builder.
- **Not tested:** a match from a pad (two players), mouse turning, phones and slow machines. One fling at a rail end happened once and did not repeat.
- **Still weak:** the lanes hall is the least reworked part (pale and bright next to the sober lobby); the snack bar is still narrow; the mode names on the boards are readable from the spawn but small. For another session: the on-screen hint says "training behind you" (`Arsenal`); training is on the left now.

## For the next Claude session

- Recover state: memory `roblox-session-recovery`. Lighting: `roblox-zone-lighting`. Rules for the shared Studio: `studio-play-sharing`, `auto-save-place`.
- The local clone is stale and locked. Read the specs straight from GitHub:
  `https://raw.githubusercontent.com/tacosonmondays-pixel/jankfire/main/roblox/docs/WEAPONS.md` (398 KB; read "Core systems" once, then the weapon's own section) and `.../MODES.md`. Step 2's file map is in `roblox/README.md` on branch `claude/f-roblox-weapons`.
- Weapon stats live in `ReplicatedStorage.Jankfire.Weapons` (`list`), checks in `ServerScriptService.Jankfire.Rules` / `Combat`, the client in `StarterPlayerScripts.Jankfire.Arsenal` + `Viewmodel`.
- The spec's last section lists every place the web server trusts the client. The Roblox server must check those.
- Testing a weapon alone: `ServerStorage.JankTest` (Studio only) arms the test player with anything without touching the
  saved loadout; `roblox/README.md` ("Pushing code into Studio, and testing it") has the recipe. The Studio MCP's own
  `require` gets separate copies of the modules, and its key and mouse tool lags about 0.3 s per action.
- Someone else may be using the same play test (on 15 November real key presses arrived mid-test and switched the
  camera): check `UserInputService:GetKeysPressed()` and the camera mode before trusting a result.
