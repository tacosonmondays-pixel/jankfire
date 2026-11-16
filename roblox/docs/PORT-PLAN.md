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

## 13. The hub is a bowling centre with rooms, 15 November 2026 (place version 206)

**The owner's direction for the whole Roblox game (15 November 2026): "This is serious compared to jankfire!" and "we're taking the wepaons and mechanics from jankfir ebut adding a serious roblox rivals touch to it, we really need to try on this".** So: JANKFIRE's weapons and mechanics, with a serious, restrained, Rivals-style finish. Inspired by, never copied. The same day they asked for the hub to be "less colorful". The web game's "jank, juice, comic" rule describes the web game, not the look of this place.

The overlook (section 11) was still one room. The research in the vault (`Research\Hub direction.md`) found that the lobby the owner admires gets its feel from several small, different rooms round a small round centre, each showing you the next through a framed opening. This is its option C, built the same day.

- **What it is.** You spawn in a round lobby (twelve sides, 48 across, its middle 84 south of the boards) on a stepped round platform under a ribbed dome, a big bowling ball turning over you. North: one opening 35 wide into the lanes hall, with all six boards in view from every spawn point. South, on the axis: an arch to a small brick lounge (sunk middle, a hologram ball you can see from the lanes through two doorways). East: a doorway and a step up to the snack bar and arcade. West: a low hatch and a ribbed passage to the training gate. A ring balcony runs round the lobby 13 up; its north side stands out into the hall as a bay you can look down the lanes from. Two jump pads go up; two gaps in the rail come down.
- **Switches in `HubLab`.** `L.LANES_STRUCTURE` is now `"centre"` (default), `"overlook"` or `"box"`. `L.LANES_PALETTE` is now `"calm"` (default) with `"retro"`, `"purple"`, `"sand"`, `"teal"` kept. **The hub as it was on the morning of 15 November is `L.LANES_STRUCTURE = "overlook"` with `L.LANES_PALETTE = "retro"`, then a rebuild.** Both older structures in the old paint still build to the part exactly what they built before (checked by sums of part count, positions, sizes, colours, lamps and text after every batch of edits, and by an independent tester).
- **How `centre` is built.** `L.LANES_BUILD.centre(H)` calls the overlook's builder with a second argument, which makes it leave the middle of its south wall open and skip what the lobby replaces (entrance roof, balcony, small lounge, jump pads, house ball, spawn, training door, arcade, snack bar), then builds the lobby and rooms with its own helpers (`at`, `side`, `seg`, `pier`, `ringSign`). The six boards are taller and higher in this structure, with the mode's name as the big line, because they are read from 85 studs away.
- **The `calm` palette is more than paint.** Off-white frame, grey walls and lid, grey carpet, pale wood, one dusty teal, pink as the only accent. Extra keys: `shell`, `pier`, `dome`, `cool` (the lobby is darker and heavier than the rooms it looks into, so every doorway frames a lit room), `remap` (repaints the loud dressing colours) and `sober` (takes out bunting, striped awnings, flower tubs and globe lamps, makes the house ball teal, swaps the joke lines on signs for plain ones from `L.LANES_WORDS`, and sets every label in Montserrat). Signs, boards and pads keep their colours.
- **`L.check()`** for this structure also tests, from every spawn point, a sight line to the name over each way out and to one thing inside each room (`L.LANES_SIGHTS.centre`). The pads themselves are behind the hall's parapet from the lobby, so their plates are counted, not required. Now: 25 zones, 0 problems, 0 leaks, 208 sight lines, 0 hidden.
- **Numbers.** `Hub.Lanes` 1,906 things, 1,463 parts, 126 lamps, 11 with shadows (the limit). No new meshes, no script outside `HubLab` changed. `HubLab` is 189,200 of Studio's 200,000 characters: the next big addition needs a second module.
- **Judged, not just checked.** An independent judge scored each main view on "would this hold up next to a Rivals lobby?", with a rework after each round. Round 1: 4.5 to 7, "closer to a tidy toy set". Round 2: 5 to 7.5, "the round lobby is now a serious room", the whole "progress, not finished". Round 3: 6.5 to 8, "first version, one pass short" (the lanes hall and the snack bar lowest); a short fourth pass followed (hall walls darker, floor arrows no longer glowing, bigger second line on the boards, pale-wood fins in the snack bar) and was not judged again. Write-ups: vault `Reviews\Bowling centre - judge round 1.md`, `... - judge round 2 and function test.md`, `... - judge round 3.md`, `... - final.md`.
- **Tested by an agent that did not build it (18 of 18):** names and attributes the server needs, spawn and arrival markers, lamps, nothing unanchored or near-black, its own sight and enclosure tests, both switches, fresh spawn, all five pads counting on both faces, the training gate both ways, both jump pads, the way down, real-key runs to every room, nobody trapped, falling out, things that turn, no script errors. After the last rework the pads, the gate and the jump pads were tested again by the builder.
- **Not tested:** a match from a pad (two players), mouse turning, phones and slow machines. One fling at a rail end happened once and did not repeat.
- **Still weak:** the lanes hall is the least reworked part (pale and bright next to the sober lobby); the snack bar is still narrow; the mode names on the boards are readable from the spawn but small. For another session: the on-screen hint says "training behind you" (`Arsenal`); training is on the left now.

## 14. The serious pass: HUD, menus, Rooftop, training hall, playground, 15 November 2026 (place version 208)

On 15 November the owner set the direction for the Roblox game: JANKFIRE's weapons and mechanics, a serious polished
finish in the class of Rivals, fewer colours ("This is serious compared to jankfire!"). Everything outside the hub and
the gun models had been built to the web game's comic look. This pass redraws it. Audit, before and after photos, three
independent judgings and the list of lines that read as jokes: `Reviews\Serious pass audit.md` in the vault. No
weapon, number or rule changed.

- **One look for every screen: `src/client/Theme.luau`.** Dark plates (`101216`), white and grey text, one amber
  accent (`ffc43d`), red (`eb4d4b`) only for danger, Builder Sans with Builder Extended for titles. Colour that
  carries information stays: team scores and names, a small chip in each weapon's colour, wrap swatches, rarities.
  **Build any new screen from it** (`T.plate`, `T.text`, `T.edge`, `T.key`, `T.scaled`), not from its own colours.
- **The HUD grows with the screen.** Plates are laid out for a 720-pixel-tall screen inside `T.scaled(gui)` and scale
  up (1.5x at 1080p, 2x from 1440p). The crosshair, hit marker, hurt rim, flash and scope stay pixel-exact.
- **Rebuilt on it:** `Hud` (speed, the announcer line on a soft dark band with its key word coloured, the controls
  line as a slim plate), `FightHud` (health with a red plate at 25 and under, ammo, a three-cell scoreboard in a
  match, kill feed, hit marker as four ticks, hit numbers, a soft hurt rim, the death band, the end screen as a table
  with the final score and a draining bar), `LoadoutUI` (flat cards, the weapon at rest in a three-quarter view, no
  junk on the podium), `JankSettings`, the Shredder's heat bar. Same functions, same arguments.
- **Where-you-are line:** low in the middle, just above the controls line, both centred under the crosshair (top
  centre and top left each covered one of the hub's hanging signs); the top centre is the match scoreboard's alone.
- **Low health:** at 25 and under the health plate turns red and the screen's rim glows faintly.
- **Words:** `Hud.callout` draws lower-case words in capitals ("dummy down" shows as DUMMY DOWN); the strings are
  unchanged. One line was corrected for the new lobby: the hub hint says "training on your left", not "behind you".
- **The grapple rope** is a pale steel cable (it was a pink-to-yellow beam), in `Move` and `Main`.
- **The repaint is a tool: `studio-tools/SeriousPass.luau`** (`PolishBackup.SeriousPass`): `S.training()`,
  `S.rooftop()`, `S.light()`, `S.all()`, and `S.restore()`, which puts back the paint kept in
  `PolishBackup.PreSeriousPass` (a ServerStorage backup, not exported). Paint, materials, sign type and the Rooftop's
  saved light only; no part moves. Safe to run again.
  - Training hall and playground: pink, purple, cyan and blue paint go neutral, coloured glow goes warm white, crates
    and ammo boxes are muted, the floor is darker, one amber safety colour is left; targets and the Plinker stay red.
    The playground's blocks are a dark slate (white and pale grey both read as a test level); its pads keep their cyan.
  - Rooftop: the box city loses its toy colours, neon strips become cool white / warm white / amber (a third dimmer
    out in the city), the penthouse is graphite and dark glass, the pool deck loses its magenta. The mesh templates in
    `JankfireMeshes` are repainted by piece name, so `MeshSwap` builds them calm.
  - Light (`S.LIGHT`): the same evening with a warm sun and cool shadows, a neutral haze, less bloom and saturation.
- **Lessons:** Roblox lights paint to about twice its value under lamps, so floors and wood are painted dark; a Neon
  part at pure white reads as an unlit bar; a dark roof goes black in evening shadow, a pale one turns the whole
  roof into one grey and plain asphalt reads as a bare slab (the floor is `868990` Pavement: the pavers give it scale); a `ScreenGui` made in code needs `ZIndexBehavior = Sibling`;
  `screen_capture` does not show BillboardGuis.
- **Left alone on purpose:** the hub (`Hub.Lanes`, `QueuePads`, `HubLab`, `HubLook`), weapon models and their paint,
  `Fx.luau` (tracers, sparks, blood), the dummies' colours (the yard's sign describes them by colour), UI sounds (they
  cannot be judged by ear from an agent session), and every other line of text.
- **Judged three times by independent agents.** Last round: death line, scoreboard, end screen and settings PASS; fight
  HUD, hub HUD and loadout CLOSE; training hall PASS; Rooftop CLOSE (it had failed); playground FAIL. A fourth round
  of fixes followed that judging and was not judged again.
- **Not tested:** a real match with two players (the scoreboard, end screen and death band were driven with test
  messages), phones and gamepads, the HUD over the bright Rooftop in play, the Shredder's heat bar in use, and clicking equip,
  wraps, wrap modes and rarity filters in the loadout after the restyle (their code is unchanged apart from looks).
- **What only new modelling would fix** (second judge): bare spawn decks on the Rooftop, the empty penthouse room and
  its block sofas, the plain box city, flat cabana curtains, the playground as a designed place, weapon icons.

## 15. The guns' calm paint and the first-person gloves, 15 November 2026 (place version 215)

The same direction as section 14, applied to the weapons: every one of the sixteen was repainted (a quiet body, one
muted furniture colour and one small accent per gun) and the bare first-person arms now wear a dark slate glove and
a near-black sleeve. No number, name, mechanic, gimmick or model shape changed. Full account, per-gun table, the judge's
scores and the pictures: `roblox/docs/GUN-PAINT.md` and `roblox/docs/gun-paint/`.

- **The paint is a switch.** `tools/roblox/weapon_paint.py` holds the calm table; `export_weapons.py --paint
  calm|web` and the paint tool write `roblox/studio-tools/WeaponPaint.luau` (both paints of every gun), which lives
  in the place as `PolishBackup.WeaponPaint`. In Studio `WeaponImport` has `W.use()`, `W.use("web")`, `W.load()`
  and `W.shredder()`. A colour change needs no upload. Recipe: `roblox/README.md`, "The paint is a switch".
- **Redline, Marble Shotgun and Katana** were re-exported through the current exporter and re-imported (they had
  been turned and painted by hand); the old templates are parked in `PolishBackup.OldWeaponTemplates`. All fifteen
  templates now carry `FileFrame` and `Paint`.
- **The Shredder** is a hand-imported Tool, so its paint is a table inside `WeaponImport` (`W.SHREDDER`); its old
  look is remembered on its parts.
- **Arms:** `AvatarArms.KIT`; `LOOK = "avatar"` or the module's `Look` attribute brings the bare arms back.
- **Judged twice** by an independent agent from in-hand photos: about 4 out of 10 on average in the web paint, about
  7 after the rework, nine guns at 7.5 or more, the Katana last at 4.5. The weakest (Katana, Marble Shotgun, Lawn
  Mower, Revolver, Sniper, the arms) were reworked between the rounds, and the second round's paint fixes went in
  afterwards without a third judging.
- **What only new work on the hold would fix:** the katana held edge-on with gloves over the hilt, the support hand
  beside the handguard, the blocky fingerless hands. That is the next job for the guns' look. Smaller: the HUD's
  colour chips for the Sniper and the Yeehaw still show their web colours (`color` in `Weapons`).
- **Not tested:** the guns in another player's hands, the Rooftop's daylight, the loadout screen's previews.

## 16. How the weapons are held, 15 November 2026 (place version 237)

The job section 15 left open. Every weapon's first-person hold was reworked; numbers, names, mechanics, gimmicks and
the paint are untouched. Full account, both judge rounds and the pictures: `roblox/docs/GUN-PAINT.md` ("The hold")
and `roblox/docs/gun-hold/`.

- **The hands are your own Roblox avatar's,** in the glove and sleeve colours. A modelled four-finger glove was built
  and taken out the same hour on the owner's word ("I just want the roblox ones"). Do not bring in a custom hand.
- **One table:** `tools/roblox/holds.json` -> `py tools/roblox/holds.py` -> `src/shared/Holds.luau`. A new weapon
  needs a row there or its hands are not drawn.
- **`AvatarArms.hold / aim / override`:** the hand grips at its own grip attachment and turns about the handle to
  face an elbow spot fixed in camera space; the forearm runs wrist to elbow every frame and is never glued to the
  gun. The Shredder's client uses the same calls.
- **The Katana** has a new rest and parry pose laid over the web game's clips (flat of the blade, guard and handle
  toward you); the cut is the web game's.
- **The off hand does the reload** instead of hiding: magazine, pump, the Redline's can, the marble bag, clear of
  the Yeehaw's spin.
- **Bigger guns** (the owner, 16 Nov: "Can the weapons be a little larger, that way the arms dont look so long and
  lanky"): `_size` 1.25 in `holds.json` scales every first-person weapon and its hands; the one-handed guns have
  `scale` 0.8 on top. Third person and the loadout previews are untouched. The models themselves are being remade
  in the Rivals class by the gun-models session (owner: "recreate the weapons in the rivals style"); holds are in
  each weapon's file frame, so new models that keep the old spots need no hold work.
- **HUD chips:** Sniper `a2457c`, Yeehaw `a58640` (`Weapons` and `Roster`).
- **Matched to Rivals' layout** (16 Nov, place version 347; owner: "look at how all the weapons and stuff are held
  in rivals ... reference look and sizes"): every gun's muzzle just below and right of the crosshair, a quarter of
  the screen wide, pistols turned to show their side, the katana upright on the right, thicker forearms. Per-gun
  `shift`, `scale`, `tilt` in `holds.json`; `tools/roblox/hold_screen.py` prints where a gun lands (default FOV 80).
  Judge: before 2 to 5, after 4 to 9 (Katana 9, Assault Rifle 8); its three weakest fixed after, not judged again.
  Measurements in the vault (`Research/Rivals first-person holds.md`), sheets `gun-hold/rivals-1..4.jpg`, account
  in `GUN-PAINT.md`. Not tested: other bodies, the Shredder's thicker forearm, aim on every gun, third person.
- **Judged three times** from before and after pictures: the weapons' hold went from about 3.5 of 10 to about 5.5
  to 6; the Katana from 2 to 7 at best. Verdict each time: close, not at the bar. Weakest: the sidearms (reworked
  after round 3, not judged again), the Yeehaw, the reload props.
- **Not tested:** other avatar bodies, the bare-skin look, sights with every gun, the Rooftop's daylight. Open:
  the reload props are plain boxes, and the Shredder's first-person copy stays in the camera if its Tool is destroyed
  while held (an older fault, seen when a test deleted the tool).

## 17. The structure pass: what paint could not fix, 15 and 16 November 2026 (place version 238)

Section 14's judges said the rest of the Rooftop and the playground "cannot be fixed with paint". This pass builds
it: models, structure and light. Review note, before and after photos, both judgings and the sheets:
`Reviews\Structure pass.md` and `Reviews\structure-pass\` in the vault. No weapon, number, match rule or line of text
changed; the hub, the guns and the HUD were not touched.

- **The builder is a tool: `studio-tools/StructurePass.luau`** (`PolishBackup.StructurePass`). `S.import()` brings the
  kits in, `S.rooftop()`, `S.skyline()`, `S.lounge()`, `S.pooldeck()`, `S.cabanas()`, `S.small()`, `S.playground()` each
  rebuild their own part, `S.check()` proves the promises below, `S.clear(name)` takes a part away again, `S.all()` runs
  everything. Safe to run again. Run from a clone: `require(game.ServerStorage.PolishBackup.StructurePass:Clone())`.
- **Everything it adds lives in folders called `Dress`** (`Map.Rooftop.Dress`: `West`, `East`, `Lounge`, `Cabanas`,
  `Skyline`; `Hub.Playground.Dress`; `Hub.TrainingGround.Dress`). The map's own boxes are never moved or removed:
  where a model stands in for one, the box is hidden (attribute `DressHid`) and stays the collision. New solid boxes
  are invisible parts named `DressSolid` (CanCollide and CanQuery, so shots and line of sight respect them).
  `SeriousPass` skips `Dress` folders (and now holds three colour rules of this pass: the city's boxes grey, the
  playground boards' rims warm white, the penthouse ceiling panels warmer), so a repaint does not undo anything.
- **Kits** are Blender scripts in the chunky style, one .glb and one upload per kit: `tools/roblox/structkit.py`
  (shared helpers: several models in one file, mirrored twins `<name>M`, a Cycles preview) with `roofdress_models.py`
  (`rt_*`), `lounge_models.py` (`ph_*`, the cabana, the tent) and `playground_models.py` (`pg_*`). A piece is named
  `<model><n>__<kind>_<hex>` (kind: plastic, concrete, neon, glass, fabric, wood; fabric is drawn as SmoothPlastic,
  Roblox's Fabric weave is harsh); the importer paints from the name. The exporter turns the pieces first
  (`rbxglb.turn_for_roblox`), so a template's pivot is the kit's own origin (floor, middle) and its front is +Z.
- **Spawn roofs.** Laid out once for the west roof and mirrored onto the east one (x to -x, the mirrored model where a
  piece is not the same both ways round): a chiller north of the lift hut with a lane between, vents on the hut's
  south wall, a ridge skylight and a roof fan over two of the map's own low boxes, a stair head in the north-west
  corner, a duct run, a tank under the billboard, a barrel rooflight; after the first judging a kerbed plinth with a
  roof fan and three tall flues north of the spawns and a waist-high corner duct south of them. Coping and piers on
  every parapet (lamps only on corners and gate posts), lamps on the hut, a low raised apron for the walkways, amber
  thresholds and a muster box, a readable LIFT plate over the white-on-white one. East only: the wooden shed becomes
  a plant room and the three plain benches loungers (same boxes).
- **Skyline.** The eight towers round the arena and the three it stands on get facades made of parts, no pictures: a
  dark glass skin, floor bands, piers, and warm-white lit windows one grid cell each, mostly on one or two lit floors
  per tower.
  Four styles (grid, ribbon, fins, brick), a crown on each tall tower (set-backs and a mast, a chisel roof, a lit
  lantern, cooling drums, a glass vault on the south tower whose roof is level with yours), and a second row of plain
  towers further out. Look-only: nothing is solid. A few far roof slabs that floated in the haze are hidden.
- **Penthouse.** Sofas, bar, stools, standing tables, fridge, planter and pot plants stand over the map's own
  furniture boxes; rugs, hanging light rafts, a ring light and a warm cove strip round both ceilings are look-only
  and carry real lights.
  New and solid: a pool table on the map's centre line, a low table before each upstairs sofa, a sideboard and two tub
  chairs each side of the north door, two tub chairs at each standing table downstairs (all in mirrored pairs or on
  the centre line).
- **Cabanas.** The four old ones were baked into `arch_pooldeck`, so that model is replaced by one with them cut
  out (`tools/roblox/cut_cabanas.py`, then `export_models.py`; the old template is in `PolishBackup.StructureBackup`).
  Trap: MeshSwap reads a template's pieces in the frame of its bounding box, which follows the model's pivot, so an
  upload's half turn is fixed by turning `WorldPivot`, not the pieces. The new cabana has a canvas roof with a plain
  hanging band, a gathered drape at each post, two padded sides, a daybed and a lantern, on the map's own boxes.
- **Playground.** A floodlit yard at dusk: every block of the course is hidden behind a piece made for it (pylons
  with collars, decks with a lit amber edge, stepping stones, grapple pods hung by cables from eight light masts) over
  nothing but a slate haze. Pads, hooks, the finish board, the fall reset and the return door are what they
  were. Its light is the `playground` look in `HubLook` (the Rooftop's dusk with a slate haze; it was midday).
- **Training hall:** the two tents with the baked red rug are hidden behind a plain grey tent with a table under it.
- **Promises checked by `S.check()`** (all true at version 238): every new solid box on the west roof has its mirror
  image on the east roof (19 and 19); no new box within 3 studs of a spawn (38 spawns, each also mirrored); none in a
  jump pad's flight (10 flights).
- **Tested in Play (solo):** all 35 Rooftop spawn points stand clear; all six Rooftop pads and the four playground pads
  fly and land where they did; the playground's hooks still take a ray; a fall puts you back on the start; the return
  door takes you to training; walking works. **Not tested:** a real two-player match on the new cover.
- **Judged twice** by an independent agent from in-game photos. First round: spawn decks and penthouse CLOSE 6, tent
  CLOSE 5, the rest PASS 7 to 8 (all had been 2 or 3). Second round (version 231): spawn decks, skyline, cabanas and
  playground PASS 7.5, LIFT sign PASS 8, tent PASS 7, penthouse CLOSE 7 for its black ceilings ("Outdoors, mostly yes
  now: the spawn roofs, skyline, cabanas and playground read as a deliberate, built place"). A fourth round answered
  that (a cove strip of lights round both penthouse ceilings, no cloud floor, the far specks hidden, warm-white
  windows, the city's brick and the plant a step greyer, the corner ducts moved off the east hot tub), saved as version
  238 and photographed but **not judged**.
- **This Rooftop is v1 from here on.** On 16 November the owner asked for a separate Rooftop v2 built to the new design
  principles, with this one kept to compare ("Keep the current one rooftop v1 vs v2 and we'll compare"). Left in v1 by
  the last judging: bare paving in the lower half of each spawn view, all-white plant, the hut the only tall thing on a
  deck, a faint lattice floating in the haze north-east of the arena, a palm through a cabana roof.

## 18. The Rotunda is the hub again, reworked; the bowling centre is the spare, 15 and 16 November 2026 (place version 252)

**The owner's words (15 November 2026), about the bowling centre: "I like the aspect and design buyt bolowing doesnt make sense for the game you know, keep it as a hub we can use but lets rework the first rework like the map after the original one". Which hub: "it had a duck lounge, a big like circle thing in the center with the branching paths leading into the rivals like pads that I said were a bit too on the nose", then "C-G are what im talking about" (letters on the vault's `Research\our_hub_versions.jpg`), then "I like how it looked, I think with the new diesgn principles building somelike like it could be cool, less colorfuil, maybe keep some color obviously, idk tryh different thing".**

- **What it is.** The ground-floor lobby of the arena. You appear on a low stepped platform with a glowing ring in its top, in a fourteen-sided round room 56 across under a ribbed dome, with a ring balcony 14 up (two jump pads up, a gap in the rail over each as the way down). The game's own Redline turns slowly over the platform inside a lit ring, lit from a lens in the platform. Five of the room's sides open onto **the lift ring**: a curved walk, then five lift bays (1V1, 1V1V1, 2V2, 3V3, 4V4 left to right), each a tall shaft with the pad on the lift's deck and its board on the back wall under a lit cove. The bays fan out from the spot where you appear, so every lift is framed by its own two piers in the first look, and a floor line runs from the platform to each deck. No pad corridor, no runway, no blast door. South, behind you, a round arch leads to **the lounge** (small, low, warm, a sunk middle, the duck turning over its projector). East-south-east a pale portal leads to **the gym** (a padded ring under a light frame, bags, weights, a lit target on the far wall). West-south-west, on your left, a hatch with cut corners leads to **the armory** (the game's weapon models on boards over counters) and at the end of its aisle **the red gate to the training ground**. The training hall's door brings you back onto the round room's floor by that hatch.
- **Built by its own builder** (`HubLab` is full): `ServerStorage.PolishBackup.HubRotunda` (helpers, build, check, switch, palettes) with three part modules `HubRotundaCentre`, `HubRotundaLifts`, `HubRotundaRooms`. `R.build("live")` wipes and remakes the hub; what the server reads is built into the hub's own folders and marked `Built = "Rotunda"`: `QueuePads` (five pads; each board's `Status` and `Sub` labels face the room), `HubSpawns` (8), `Doors.HubArrive` (3), `Doors.RotundaToTraining`. Usage: `local R = require(game.ServerStorage.PolishBackup.HubRotunda:Clone()); print(R.build("live")); print(R.check())`; `R.status()` is one line on what stands.
- **The colour treatment is a switch** (`R.PALETTE`), because the owner asked to "try different thing": `glow` (default: the cosy rotunda E made sober; one soft aqua accent on the floor lines and the platform's ring, team colours only on the pads and boards), `arena` (calm slate and cream, one pink line, yellow words), `warm` (stone, brass and timber, one amber accent). `R.compare()` builds one staging copy of each side by side to photograph, `R.unstage()` removes them. The three side by side went to the owner (vault `Hubs\shots\rotunda\rotunda_three_colours.jpg`).
- **The bowling centre is one call away:** `R.switch("lanes")`, or `HubLab`'s own usage line (its build now also removes the Rotunda and anything marked `Built = "Rotunda"`). `R.switch("rotunda")` brings this hub back. Tried both ways twice (by the builder and by the tester): the bowling centre comes back exactly as it was, with its own check clean. The old round hub as it was parked is still in `PolishBackup.HubArchive.Rotunda`.
- **`R.check()`**: keep-clear zones round every spawn and arrival marker, pad and walk; leak rays from inside every room; sight lines from the eye over every spawn marker to the middle of every pad plate, three points across every board, the name and the word over every way out; from the middle of the platform to one thing inside each room; lamps with shadows (11 at most). `OverlapCheck.run()` hands over to it while the Rotunda stands. Now: 30 keep-clear zones, 0 problems, 0 leaks, 283 sight lines, 0 hidden.
- **Numbers.** `Hub.Rotunda` 1,751 things, 1,350 parts, 86 lamps, 9 with shadows. No new meshes (the kit's `hb_*`, `bc_*` pieces and the game's own weapon models). No game script changed; `HubLab` and `OverlapCheck` each learned one thing about the new hub (`R.install()` made those edits, and added the modules to `StudioExport`).
- **Judged, not just checked.** An independent agent, shown only pictures, the owner's words and the Rivals notes, scored it twice with a rework after each: round 1 **5/10** against the Rivals bar, 6/10 "fits an arena shooter" (weakest: the gym; colour leaking into the building; a placeholder centrepiece); round 2 **5.5/10**, 6/10 ("the plan is in Rivals' class; the finish is not": weakest the pad bays; flat light; teal as a second base colour). A third pass followed (lit coves in the bays, aqua only on the lines and the ring, calmer plates, the showpiece lowered) and was not judged. Write-ups: vault `Reviews\Rotunda rework - judge round 1.md` and `... - judge round 2.md`.
- **Tested by an agent that did not build it (all functions pass):** names and attributes the server reads, nothing unanchored, the switch both ways, a fresh spawn on the platform facing the lifts, all eleven team plates counting and lighting one place and resetting, the training gate both ways, both jump pads up and the gap down, real-key walks to every room and onto a lift, the duck and the showpiece turning, the loadout and its blur, the HUD hint ("training on your left": it is), no hub errors. Its catch (arriving back from training facing the armory's gun wall) was fixed: you now arrive in the round room by the hatch.
- **Not tested:** a match started from a pad (two players), phones and slow machines.
- **Still weak (the judges' list):** the light is even and shadowless (the hub look in `HubLook` and the place's Lighting are outside this builder); the walk past the lifts is plain; the gym's boxing theme; props stand singly rather than in groups; the five bays could be one band with one sign line. The displayed weapon models carry the kit's own dark details.

## 19. Rooftop v2: a second arena to the new principles, 16 November 2026 (place version 276)

The owner: "can we rebuild a new training area too with our new design principles as well as a version of rooftop that
follows our design principles? Keep the current one rooftop v1 vs v2 and we'll compare". **v1 (`Map.Rooftop`) is not
touched and is still what matches use.** Plan, build log and judge reports: vault `Hubs/Rooftop v2 plan.md`,
`Reviews/Rooftop v2 - judge round 1.md`, `... round 2.md`; RIVALS arena study: `Research/Rivals arenas - layout notes.md`.

- **What v2 is:** a fight across three rooftops (`workspace.Map.RooftopV2`, world origin (0, 0, 18000)), mirrored
  for the two teams. Each team starts in a spawn house (a coffered room over a podium, three framed doors, a baffle
  wall outside the front door: no spawn sees the other). Three lanes: the Gallery (high, +10, a lookout room in the
  middle), the Court (a sunken octagon round the Cistern, a drum with a dome standing in a pool you can swim in) and
  the Colonnade (covered, a vault, a small room on each half). Cover at chest and head height, heights from -4.5 to
  about +17, four jump pads, open gaps you can be knocked into ("into the smog"). Same size class as v1 (304 x 128).
- **Its look:** few big bevelled flat-colour shapes (warm stone, mid-grey floors, a slate coping on every edge, sage
  planting), colour only on pads, team signs and one amber accent; its own early-afternoon light
  (`HubLook.looks.rooftop_v2`, picked by `HubLife` in a match when the arena is v2); a city of instanced towers with a
  smog layer below.
- **The switch:** `workspace.Map` attribute `Arena` = `"Rooftop"` (v1, the default; also when missing),
  `"RooftopV2"` or `"RooftopV3"` (section 22). `ReplicatedStorage.Jankfire.Arena` answers for everyone: `Matches.teamSpawns`, `Fight.spawnPoints`,
  `Main` and `Dummies` (the fall line `KillY`), `HubLife` (the light). From Studio:
  `require(game.ServerStorage.PolishBackup.RooftopV2:Clone()).use("v2")` (or `"v1"`).
- **How it is built:** `tools/roblox/rooftop2_models.py` describes the arena once; one headless Blender run writes the
  meshes (`rooftop2.glb`, one Model asset, `R.ASSET` in the builder) and `studio-tools/RooftopV2Layout.luau` (hit boxes,
  spawn points, team spawns, pads, water, lights), and checks spawn sight lines, clear spawns, pad flights and the
  mirror. `PolishBackup.RooftopV2`: `R.import()`, `R.build()` (wipes and remakes the model), `R.check()`, `R.clear()`,
  `R.use(...)`. Photo sheets: `tools/roblox/compare_sheet.py`.
- **Tested** (solo Play tests, 16 Nov): both team spawns stand clean; all four pads throw you where meant; the pool is
  swimmable; walking (30 studs/s), a slide, the low cover, the gate; the grapple to the Cistern; a fall into a gap
  kills at the line. **Not tested:** a real two-player match on v2 (team spawns are read through the same code path
  as v1, checked by reading, not played), a 1v1v1 match, phones.
- **Judged:** round 1 middle PASS 7, the rest CLOSE 5 to 6, the defenders' spawn FAIL 4 (low sun on the spawn line);
  round 2 middle and covered lane PASS 7, spawns and gallery CLOSE 6, the spawn house's outside FAIL 4; round 3
  middle and covered lane PASS 7, the rest CLOSE 5 to 6 (a black band on the horizon: v1's navy fog reached v2 at
  distance, so v2's light now has a pale fog of its own); round 4 inside a spawn 6.5, outside 6; round 5 (place
  version 270) the middle PASS 7.5 (the bronze dome a landmark at last), covered lane PASS 7, inside a spawn CLOSE 7,
  the spawn exit, the gallery and the view from above CLOSE 6 to 6.5: "beats v1 on every principle; the middle and
  the covered lane hold up next to a RIVALS arena; the spawn exit, the gallery and the backdrop still read as a
  careful greybox"; round 6 (place version 272: the spawn exit's screen redrawn with the team's mark on it, calmer
  team colours, lockers in the spawn room, a darker gallery deck, a city floor of streets and blocks) the spawn room
  and the middle PASS 7.5, the spawn exit and the view from above CLOSE 7, the lanes CLOSE 6.5: "clearly better
  than v1 ... not yet beside a polished RIVALS arena: the backdrop gives it away"; round 7 (place version 276: no
  haze veils, low buildings and a far skyline round the city, the spawn exit washed by a warm light, the beams clear
  of the band) the spawn room PASS 8, the middle PASS 7.5, the rest CLOSE 7 to 7.5: "clean and consistent up close
  ... ahead of v1 everywhere except the backdrop". Write-ups: vault `Reviews/Rooftop v2 - judge round 1.md` to `7`.
- **Where it stopped (16 Nov):** after round 7 the work moved to the owner's pick (v1, v2 or v3; sheet
  `Reviews/sheet_rooftop_v1_v2_v3_final.jpg`). Left as known: the far skyline is paler than the sky at the horizon
  from the lanes; the lip under the spawn screen's cap pokes out at one end; the team mark outside reads rose against
  the band's mauve inside; fine stripes on the court's step faces from about 30 studs away, which tests in Studio put
  down to the engine (they stay with shadows, reflections, lamps, screen effects and haze off, and show on a plain
  Part too).
- **No coloured marks on the floors (place version 289).** The owner (16 Nov): "can you remove he colored marks on the
  floor for rooftop, inhub its okay but not on matches". v2 had five amber strips on its floors (the spawn's way out
  and its side doors, the two gates into the middle, the colonnade's doors). They are now sills in `SILL` (`66635e`,
  the paving a step darker) in `rooftop2_models.py`; `AMBER` is no longer used on any floor. Kit asset
  `jf_rooftop2_10` (71153063483666), rebuilt and checked (sight lines 0 open, spawns clear, pads land, the layout
  unchanged). Left on purpose: the jump pads' cyan faces, the court's warm floor lamps, the team signs and marks on
  walls. Nothing paints the floor during a match either: bullet holes are dark, water ripples white; the one coloured
  thing that can lie on a floor is the Marble Shotgun's patch of marbles (a weapon's hazard, not paint, left as is).
  Photo: `roblox/docs/rooftop-v2/v2_floor_marks_before_after.jpg`.

## 20. The guns rebuilt for Roblox, 15 and 16 November 2026 (place version 325)

After the calm paint the owner wrote "the gun textures look a little messed up?" and "would it be easier to recreate
them in roblox? you can look up other rivals weapons and skins!", then "can you reference the rivals weapons when
remodeling these please" and "im mostly discontent with the snipers". All sixteen weapons were remade as new
low-poly models built for Roblox; numbers, names, mechanics, gimmicks, spots and moving parts are untouched. After
round 5 the owner asked for no "bullets attached on top", a one-piece Sniper stock, no cross on Second Opinion, and
"a little blockier" like Rivals: round 6 did all four, round 7 made them chunkier (thicker barrels) and built a
signature back into the guns that lost one. Then "not completly block some rounded too ... a bix of the two
versions": round 8 (live, place version 281) mixes round 5's rounder look with round 7's blocks. Then "make the shapes
cohesive, reference an actual gun ... reference rivals heavily ... put them side by side and ill pick each one":
version C (a real gun each, built the way Rivals builds; `gunkit_c.py`, `gun_models_c*.py`). The owner picked per gun
(`gun-models/pick-1.jpg` to `-4.jpg`), with fixes and two mixed guns; the live set is built by `tools/roblox/gun_set.py`
(`gunkit.use_style` per gun). Full account, per-gun notes, every judge round and pictures:
`roblox/docs/GUN-MODELS.md` and `roblox/docs/gun-models/`.

- **Built from a kit,** in headless Blender: `tools/roblox/gunkit.py` (chamfered blocks, eight-sided barrels, panels,
  ribs, rivets, sights) and `tools/roblox/gun_models.py` (one builder per gun, plus skins). 8 to 31 big pieces a gun
  instead of 10 to 59 small ones; `SmoothPlastic` and flat colours, no pictures, no grainy materials. Since round 6
  the kit is blockier for every gun at once (`BEV_K`, `WTOP_K`, `SMOOTH_CYL` at the top of `gunkit.py`: half-width
  chamfers, straighter sides, flat-faceted barrels; `BARREL_K` since round 7: barrels 1.2 times as thick). Rivals' guns were studied for proportions (vault:
  `Research/Rivals weapons and skins - style notes.md`); every design is our own.
- **The models are a switch:** `PolishBackup.WeaponSets.{kit,web}`, `W.models()` / `W.models("web")` in
  `WeaponImport`. Each template carries its file bounds (`FileLo`, `FileHi`), which `WeaponModels.build` reads first.
- **Skins:** a skin is a kit model `w_<id>@<skin>` that recolours slots and swaps named pieces; `W.skin("ar",
  "cardboard")` shows the proof, Carl's Cardboard. Five ideas are in GUN-MODELS.md. Owning and picking skins is the
  cosmetics batch (ProfileStore first).
- **Wraps** go on and come off every kit model exactly (102 wraps x 3 modes x 17 models).
- **Judged every round** by an independent agent against "would this sit next to Rivals' guns?": 6.2, 6.6, 6.8,
  7.4, 7.3, 7.25, 7.5, 7.5 out of 10 (Rivals' own plain guns about 8 to 9). Round 6 answered the owner's four notes; its judge
  said the long guns are still slim for "blockier", three guns lost their signature with what was taken off, and
  every gun reads near-black in hand. Round 7 (7.5) made them chunkier and gave back signatures; its judge said the
  main limit is now the light on the held gun, not the models: a soft fill light that travels with the first-person
  gun was the next step, and is done (place version 280). Round 8 (7.5): the rounded mix; its judge said it was
  timid where the player looks, so round 8b rounded the tops, scopes and big masses. Then the owner's pick: 10 C, 3 A
  (Sniper and Redline with fixes, Shotgun), 1 B (Hat Trick), 2 mixed (Revolver A+C, Katana C+B), built by
  `tools/roblox/gun_set.py` and checked whole by `tools/roblox/gun_check.py` (every solid touches the gun, every moving
  node there). Live in place version 313 (with the wrap session's fixed UVs; the hub armory rebuilt, 0 problems);
  in hand: `gun-models/picked-hall.jpg`. Reload check done (every moving piece measured in a Play test): all pass
  after two fixes in place version 325, the held guns' fit (`WeaponModels.partsBox`: they were squashed up to 40%
  across) and the Revolver's cylinder (six-sided, on its axis).
- **The hub copies the templates:** after a gun change rebuild it (`R.build("live")` in `PolishBackup.HubRotunda`)
  so the armory racks and the showpiece show the new models (done for round 8b).
- **Not checked:** every gun firing (the Assault Rifle was), reload animations in motion on each new model, another
  player's view, the Rooftop's daylight.

## 21. Training v2: the training area rebuilt to the new principles, 16 November 2026 (place version 268)

**The owner (16 November 2026): "can we rebuild a new training area too with our new design principles as well as a version of rooftop that follows our design principles? Keep the current one rooftop v1 vs v2 and we'll compare". About the old hall (14 November): "rn its big with a lot of empty space yk".** The old hall is kept as v1, one switch away, so the owner can compare here too.

- **What v2 is.** At the old hall's site (`Hub.TrainingGround`, about x -90..82, z -8098..-8304, floor y 240), smaller rooms of different shapes instead of one big hall. You arrive through the hub's gate in a small **eight-sided muster room** (40 across) under a lantern drum, round a low dais with an amber ring; two lit bays, one band round the room, a warm bench bay (the place to stop) and a board saying where things are. Three framed ways out, one heavy word over each: **DUMMIES** ahead (a vaulted hall with ribs on piers; the strafing dummy's lane between walks with the two still dummies; cover on alternating sides; the far third a raised stage where the Plinker stands on a round two-step stand under a round light; the bullseye in a round frame in a canted niche), **RANGE** right (Cardboard Carl's: three booths under a canopy with the CHILL / NORMAL / SWEATY plates and their words on the counter; the board on arms on the west wall, clear of the line to the target; the lane open to the sky between piers, stepping up two terraces with rounded noses and lit strips; the Carls on three plinths at 15, 30 and 45 m; it ends on a full-width backstop with a cut top, the big target in a round recess with a lit rim, under a hood), **COURSE** left (the tallest room, on a darker floor: slate ledges 1, 2, 3 and a gallery stepping up the west and north walls, each with a rounded white nose, a lit edge and its number, jump pads between them; an eight-sided tower under a skylight drum with a pad up and a slate chute with white rails back down; a slide lane to a pit to slide-jump; flat amber grapple hoops under the coffered beams; piers on both long walls where the beams land; a lit framed bay on the far wall behind the tower and a framed TOP on the gallery's wall; the playground's secret bullseye high over ledge 3).
- **Built by its own builder:** `ServerStorage.PolishBackup.TrainingV2` (repo `roblox/studio-tools/TrainingV2.luau`). `T.build("live")` wipes and remakes `Hub.TrainingGround` and every marker the server reads (`TrainSpawns`, `DummySpots`, `TrainingZone`, `Barrier`, `Doors.ToHub`, `Doors.ToPlayground`, `Doors.TrainingArrive`; triggers marked `Built = "TrainingV2"`); `T.build("stage")` builds a copy 400 studs east to look at; `T.check()` checks the markers, the zone, the Plinker's view of the spawn points, every plate's view of every Carl, the gun sessions' test line and the arrival points. Usage: `local T = require(game.ServerStorage.PolishBackup.TrainingV2:Clone()); print(T.build("live")); print(T.check())`.
- **The switch:** `T.switch("v1")` puts the old hall and all its markers back exactly as they were (copies from `PolishBackup.TrainingV1`, parked whole the first time v2 went live); `T.switch("v2")` builds v2 again. Each switch also sets the attribute `TrainingLook` on `ReplicatedStorage.Jankfire.HubLook`, which picks the light: `looks.training_v1` (the old one) or `looks.training_v2` (early-afternoon daylight under the engine's plain sky, warm-neutral, little haze).
- **The kit:** `tools/roblox/training_models.py` (headless Blender, one .glb, Model asset `T.KIT`; `T.import()` brings it into `ServerStorage.JankfireMeshes`): cover wall and block, the Plinker's stand, the dais, the yard's rib and vault bay, two framed openings, light bar, booth wall, bench, the muster's crown and lantern, the eight-sided tower, the grapple hoop and ring, the target, the Plinker's pulpit, two framed openings. Flat `SmoothPlastic`, bevelled, one quiet family of greys and off-whites, amber the one accent, cyan only on pads, red on the gate.
- **Kept for others:** the gun sessions' test spot (stand at (-16, 243.2, -8150), `Stand1` at (-16, 240, -8170)) and `JankTest`; `PropCollision.RangeCounterBox` (the hub builders clone it); the door split with the hub (the hub owns `Doors.RotundaToTraining` and `Doors.HubArrive`). `SeriousPass.training()` now skips a `TrainingGround` marked `Version = "v2"`; `StudioExport` lists `TrainingV2`. No game script changed.
- **Tested in Play tests (all pass; the full one on place version 262, short ones on 265 and 268):** arriving through the hub's gate onto a `TrainSpawn` with Zone training; the four dummies alive at their spots; `JankTest` arming; a Carl run from the CHILL plate (shots through the game's own Fire remote, six down on the board); all four jump pads land on ledges 1, 2, 3 and the tower top; a 30-stud drop is harmless; dying respawns on a `TrainSpawn`; the secret bullseye to the playground and the way back onto the gallery; the server accepts the grapple at the bullseye and the rings; the gate back to the hub's `HubArrive`; on 268 again the gate, the dummies, the four pads, standing on the chute top and foot, the gate back. The check: the Plinker sees 0 of 6 spawn points, 0 of 45 plate-to-Carl lines blocked, nothing solid on any arrival point.
- **Not tested:** the Plinker firing at a player and a parry against it; a real slide-jump across the pit and a real grapple swing (both need live input); walking up every step and ramp with the game's movement; two players at once; phones.
- **Judged:** five rounds by fresh independent judges against the principles and "would this hold up next to RIVALS?" (vault `Reviews/Training v2 - judge round 1` to `5`), each followed by a rework. Round 1: the muster, the yard, the booths and the gallery CLOSE; the range's far end and the course's first view FAIL. Round 5 (after four reworks): the muster, the range from the booth and the gate with the bench bay PASS; the yard, the range's far end and the course entrance CLOSE; the course seen from the gallery still FAIL (a pale shaft with no end). Rework 5 then gave that view a lit framed bay on the far wall behind the tower, piers on the high west wall and a slate chute with white rails; it was not judged again. The judges' notes for the owner: the muster follows RIVALS' centre recipe in plan (the principles ask for it) and the matching yellow words over chamfered doors push it close; the yard's plan echoes RIVALS' duel hall; a pale range open to the sky on terraces is like RIVALS' range; "CARDBOARD CARL'S" and "he won't shoot back" read comic (the game's own words).
- **Numbers:** 1,039 things, 811 parts, 50 lamps (5 cast shadows); v1 parked is 2,516 things. Photos and both sheets in the vault (`Hubs/shots/training/`) and in `roblox/docs/training-v2/`; the build log in the vault's `Hubs/Training v2 plan.md`.

## 22. Rooftop v3: v1's layout, redressed to the new principles, 16 November 2026 (place version 273)

**The owner (16 November 2026): "rooftop v3 can it follow ther layout of v1 just updated with the new principles, loike the props but keep the layout the same yk what I mean I really like v2 too keep working on it".** So v3 plays exactly like v1 and looks like the new game. v1 (`Map.Rooftop`) and v2 (`Map.RooftopV2`) are not touched; v1 stays the default arena.

- **What v3 is:** `workspace.Map.RooftopV3` at world (0, 0, -30000), the same height as v1 (its KillY -484.8 holds). v1's three towers, the two spawn roofs with their lift huts, the stairs down to the middle roof, the pool deck with cabanas and trees, the two-storey penthouse with its roof terrace, the high bridge across the north, every box of cover, the six pads, the pool and the tub, all where they were. What a player sees is new: big flat tiles over dark joints with a darker band round each deck; slate copings; the lift huts as spawn houses (plinth, pilasters, a deep lit door reveal, the team's colour as a panel in the lintel with a slate chevron, a stripe in the floor from the door out through the team's apron, a thick beacon pylon); the penthouse as a stone frame (corner piers, mid-slate window frames, warm-grey glass, deep lintels, stone sills, a slate floor band and a deep slate cornice with PENTHOUSE in lit letters) with furnished floors (drop panels, rugs, a lit bar back, lit wall niches, a field on the upper floor); smooth stairs with one side wall per flight; the bridge with ribs, piers, lanterns and a lit gateway at each end; round chunky trees; the billboard says JANKFIRE; the towers' top two floors solid warm stone.
- **How the layout stays v1's:** the builder does not rebuild the collision, it copies it. `R.build()` clones every hit box of v1 (its 422 `Solid` boxes, the structure pass's 53 `DressSolid` cover boxes, the pads with their `Pad` attributes, the 14 team spawns, the pool and tub water with their `JankWater` tag; the 21 spawns as plain Parts) into v3, invisible. `R.check()` proves it: every v1 box has a copy within 0.01 stud with the same size, turn and flags (0 missing, 0 extra), no kit part collides or takes shots, and it prints each pad's flight.
- **How the look is made:** `tools/roblox/rooftop3_models.py` (headless Blender) reads `tools/roblox/rooftop3_v1.json` (v1's boxes, dumped from Studio) and dresses every box by kind: one .glb (154 meshes, about 235k triangles, kit `rooftop3`, models `r3_*`) and `roblox/studio-tools/RooftopV3Layout.luau` (origin, 69 lights). Look-only additions keep out of where a player stands (piers outside parapets, beams over heads, floor inlays flush). One v1 quirk kept: three crates float 12 studs over the north service roof in v1; v3 stands them on a look-only deck on legs.
- **Builder:** `ServerStorage.PolishBackup.RooftopV3` (`roblox/studio-tools/RooftopV3.luau`): `R.import()` (the kit into `JankfireMeshes`), `R.build()` (wipes and remakes the model; the city round it is v3's own copies of v2's tower designs, tinted cooler and darker, over a haze-blue smog layer and a pale horizon ring), `R.check()`, `R.clear()`, `R.use("v3" | "v2" | "v1")`. Usage: `local R = require(game.ServerStorage.PolishBackup.RooftopV3:Clone()); print(R.build()); print(R.check())`.
- **The switch and the light:** `workspace.Map` attribute `Arena` = `"RooftopV3"` (through `ReplicatedStorage.Jankfire.Arena`, read by Matches, Fight, Main, Dummies). `HubLife` picks `HubLook.looks.rooftop_v3` in a match on v3: the engine's sky, a sun about 31 degrees up from the south (latitude 78 at 13:30, measured: across the lanes, so neither team looks into it), a cooler, thicker haze, a pale fog (v1's saved navy fog drew a black band on the horizon).
- **Tested (solo Play test, 16 Nov):** all 14 team spawns stand clean; all six pads throw you where v1's do (the deck pads onto the spawn roofs, the roof pads onto the penthouse roof); the pool is water (Humanoid state Swimming); a fall into the gap kills at the line after 3.6 s. **Not tested:** a real two-player match on v3 (team spawns go through the same code as v1, read, not played), 1v1v1, phones and frame rate (v3 is 1,574 parts in the arena plus 857 in the city, against about 10,000 in v1).
- **Judged** four times by fresh independent judges (vault `Reviews/Rooftop v3 - judge round 1` to `4`), a rework after each of the first three. Round 1: every view CLOSE 5 to 6 (v1 4 to 5). Round 3: the bridge PASS 8, the spawns, the middle, the stairs and the view from above CLOSE 7, the penthouse floors 6 to 6.5; "v3 now clearly beats v1 on shape, calm and finish; v1 keeps only its dusk mood". Round 4 (the last rework: warm-grey glass, mid-slate frames, a deeper lit door reveal, a heavier billboard word): the upper floor up to 7, the rest held (the bridge PASS 8, everything else CLOSE 7, the ground floor 6.5): "close to the RIVALS bar but not there". **Left by the last judge:** the penthouse ground floor still reads sepia (a warm-grey floor, an off-white ceiling, mid-slate cove housings and stool bases), the spawn forecourts still read as empty plates (and the off-frame water tower throws a big shadow across the west spawn's view), the billboard's letters fuse from the bridge, the sky could be calmer.
- **Kept on purpose:** the team colours pink and cyan (the HUD's; matte, only the pads glow bright cyan), and the pool's surface (the game's own swimmable terrain water, shared with v1). Plan and build log: vault `Hubs/Rooftop v3 plan.md`; photos `Reviews/rooftop-v3/round1..4`, sheet `Reviews/rooftop-v3/sheet_v1_v2_v3.jpg`.
- **The pool's water is fixed (place version 277).** The owner, after seeing v3 (16 Nov 2026): "rooftop v3 is amazing, if you keep the pool, can you keep the amazing water look". The water is the game's terrain water (`ServerScriptService.JankWater` fills the `JankWater` part) under v3's light. Its settings were one global set on `workspace.Terrain`, so another arena's change could have changed v3's pool. They are now pinned in v3's own look: `HubLook.looks.rooftop_v3.Terrain` (WaterColor 28, 150, 178; WaterTransparency 0.55; WaterReflectance 0.75; WaterWaveSize 0.08; WaterWaveSpeed 8). `HubLook`'s `target()` now also accepts `"Terrain"`, and every other look gets the place's saved water back. Checked in Play: with the water set to red and big waves on purpose, v3's look put it back. The kit's pool (the stone coping, the pale lining, the lamp strips under the water and the light below) is marked KEEP AS IS in `rooftop3_models.py`. Photo: `roblox/docs/rooftop-v3/v3_pool.jpg`. **Rule for later rounds:** any rework of v3 keeps the pool and its water exactly as they are.
- **No coloured marks on v3's floors (place version 287).** The owner (16 Nov 2026): "can you remove he colored marks on the floor for rooftop, inhub its okay but not on matches". The only coloured paint on a walkable floor in v3 was the team stripe with its arrowhead on each spawn deck (`r3_deckW` pink b463a0, `r3_deckE` teal 45879a). It is gone from the kit (`rooftop3_models.py`, kit asset 109680564367482), so `R.build()` can't bring it back. Kept: the jump pads, the warm-white light strips (lamps), the neutral slate frames, the darker landing and the grey joints, and the team colour on the spawn houses' walls (lintel panel, beacon), which are not floors. A scan of every visible v3 part with a saturated colour now finds only the pads, the spawn houses' wall panels, planting, crates and tower glass. Nothing paints the floor during a match either: the runtime parts are bullet holes (dark), water ripples and the grapple rope. `R.check()` after the rebuild: 0 missing, 0 extra, every pad lands where it did. Photos: `roblox/docs/rooftop-v3/spawn_deck_before.jpg` and `spawn_deck_after.jpg`. **Rule:** no colour on any floor a player walks on in a match arena; mark things with the floor's own greys.

## 23. Matches take turns on Rooftop v2 and v3, 16 November 2026 (place version 283)

**The owner (16 November 2026), asked which Rooftop matches should use, v2 or v3: "Why not both XD".** So v2 and v3 are both in the rotation; v1 left it but stays in the place, one word away.

- **The rotation:** `workspace.Map` attribute `ArenaPool` = `"RooftopV2,RooftopV3"` (a comma list of arenas under `Map`; unbuilt names are skipped). `Matches.startMatch` picks the next arena just before anyone is moved in (`Arena.pick`: never the same one twice in a row; the first match after a server starts gets a random one) and sets `Map.Arena` to it, so team spawns, spawn points, the fall line and the match light all follow (they read `Map.Arena` live through `ReplicatedStorage.Jankfire.Arena`). No pool, or an empty one: `Map.Arena` stays as it is set (the old pin).
- **Why switching is safe:** `Matches` runs one match at a time (a full pad waits with "ARENA BUSY"), so the arena only changes when a match starts, never under a live one. Kept that way rather than running a match in each arena at once.
- **The banner:** the first round opens on the arena's name on the HUD's announcer line (the same white capitals over the amber rule), then "ROUND 1 · YOU'RE PINK", then "ROUND START". Names (`Arena.TITLES`, a model's own `Title` attribute wins): v3 **ROOFTOP** (v1's layout, the one players know), v2 **ROOFTOP: SKYLINE**, v1 **ROOFTOP: DUSK**.
- **The switch by hand:** `local R = require(game.ServerStorage.PolishBackup.RooftopV3:Clone())`, then `R.use("both")` (v2 and v3 take turns: the current setting), `R.use("all")` (adds v1), or `R.use("v1" | "v2" | "v3")` to pin one (the pool becomes just that one). `PolishBackup.RooftopV2`'s `R.use("v2")` also pins now. Or type `ArenaPool` on `workspace.Map` directly; then save and publish.
- **Tested (solo Play test, 16 Nov; a queue pad set to one side inside the test only, so one player could start a match):** four matches back to back went v2, v3, v2, v3. In each: the team-1 spawn of that arena (v2 at (-130, 3.7, 17993), v3 at (-162, 2.7, -29991)), the fall line read from that arena (-484.8 for both), the match light switched while the game ran (v2: clock 13.2, fog 450 to 2600; v3: clock 13.5, fog 400 to 2300), and the banner said "ROOFTOP: SKYLINE" on v2 and "ROOFTOP" on v3. Photo of v3's banner: `roblox/docs/rooftop-v2/rotation_v3_banner.jpg`. **Not tested:** a real two-player match, 1v1v1 (the third team uses `Spawns` named Spawn11, 18, 14, 12, 13: all three arenas have them), phones.

## 24. The back lot: a garage door off the dummy yard, an easter egg, and an open-air training ground behind it, 16 November 2026 (place version 340)

The owner, 16 Nov: "can you add a large garage door that leads outside to the big rivals style training grounds, you have to do like a little easter egg to get it or something".

**The door.** The dummy yard now ends on a 24 x 16.5 roll-up garage door, on the axis you look down when you arrive:
- a slate roller box across its head, and a lit transom in the lunette under the last rib
- warm daylight leaking under it, and amber beacons
- two deep panels: "KEEP CLEAR" over the door's hazard band, and "LOCKED" over three cardboard-man figures labelled BENCH / RANGE / COURSE, a timer line and the hint "ask the gold ones."

The yard's old end niche and bullseye are gone. The Plinker's stand moved off the axis, to (-15, -8246); it still sees none of the spawn points.

**The egg.** Three gold Carls (real fighters of kind "dummy", like Cardboard Carl's, so every weapon works on them):
- on the bench in the bench bay
- on the range's first beam, looking down the lane
- in the lit bay at the course's near end

Each hit tells the shooter "GOLD n OF 3 · m:ss" with a chime; the first one starts 90 s. All three:
- the door rolls up for 45 s, the panel's men light and the beacons turn
- everyone in training hears "THE GARAGE IS OPEN"
- its safety eye holds it open while anyone stands in the doorway
- anyone who has opened it can stand at it for 2 s to open it again ("THE GARAGE REMEMBERS YOU")

**The lot.** A loading bay, then a portal under a canopy onto an arrival terrace over an open-air ground (x -186..186, z -8304..-8734) in a valley:
- **the LONG LANE:** twelve Carls at 25/50/75/100 m between gate posts, rows stepping up, side walls, three baffle frames, and a 30-high slate backstop with a cardboard man on it
- **THE BLOCKS:** a container yard behind a container gateway; container walls 2 and 3 high; a raised pad under a three-storey house; a catwalk to a container tower; eight Carls
- **THE CLIMB:** one slate plinth carrying a pad onto a deck, an off-white slide, a cut gap, stepping drums, a summit, a walled canyon with two grapple masts, and a 64-stud finish tower; stages numbered 1 to 6
- **THE HILL:** three slate terraces with walled wedge ramps, and a lookout tower you are thrown up into through its core

A ridge of hills, made of smooth ellipsoids from the kit's `tl_ball`, hides the playground's towers. `L.horizon` checks it with rays: all 76 tall playground tops are hidden from all six eye points. You leave by the EXIT door (back on the muster's spawns) or the garage while it is up.

**Code.**
- `ServerScriptService.Jankfire.TheLot` (`roblox/src/server/TheLot.server.luau`, new): the door, the egg, the lot's Carls (they fold when shot and stand up 2.6 s later), and the player attribute `OnLot`. In Studio only, `ServerStorage.LotTest` drives it for play tests.
- `Dummies.luau`: the Plinker leaves `OnLot` players alone (he could see out through the open door). At the items session's request he also no longer sees through smoke (`Fight.smokeBlocks`, guarded).
- `HubLook.looks.lot` plus `HubLife`: the lot's own light while `OnLot`.

**Builders.**
- `PolishBackup.TrainingLot` (`roblox/studio-tools/TrainingLot.luau`, new) is called by `TrainingV2.build`, now push 13.
- The zone box takes the lot in. The hall's barrier stops at the façade, with a wall over it, and the lot has its own sides, back and lid.
- `LotExit` is one of the doors the build owns.
- `StudioExport` now lists `TrainingLot`.
- Kit: `tools/roblox/lot_models.py`, 18 models, asset 75809148325346 (kit 4 added `tl_cylinder`, a smooth 64-sided drum, and `tl_bank`, the hill's grass bank). Uploads are meshes in plain colours, no images.
- `T.check()` now also reports: the lot's markers, the ridge's ray check, rays from three eye points to the watchtower (12/12 each), and the long lane's counter-to-Carl lines (0 of 36 blocked).

**Tested in Play** (several tests across pushes):
- Real shots through the Fire remote put each gold Carl down in 3. The count, the per-hit toasts, the opening, the doorway hold, the close and the reopen all worked.
- The Plinker left a player in the bay alone with the door open.
- Every lot pad lands: the climb deck, the finish tower at 104 up, and the watchtower lift.
- Lot Carls come back; the EXIT lands on a muster spawn.

**Judged.** Four rounds, vault `Reviews/Back lot - judge round 1.md` to `round 4.md`:
- round 1: no PASS
- round 2: 1 PASS, 8 CLOSE, 2 FAIL
- round 3: 5 PASS, 6 CLOSE, 1 FAIL (the climb from the ground). No blocker in play.
- round 4: 9 PASS, 4 CLOSE, 0 FAIL. No blocker; "fine to show the owner now".

Pushes 7, 10 and 11 are the reworks. Push 11 did round 3's fix and quick wins: the direction board moved onto the terrace facing the portal (on the façade its left and right read mirrored), the door panels a step lighter with pale men and a warm spot on each, the ridge's lumps sunk and widened into hill caps, and a container wall on the yard's bare east side. The photo sheet is `roblox/docs/back-lot/back_lot.jpg`.

**Round 4** (lot pushes 12 and 13, TrainingV2 push 13, place version 340) fixed round 3's fail and close items:
- **The climb from the ground:** a pale course on its slate plinth, without the side piers that read as window slits on the deck and summit. The start is a raised rubber mat that meets the plinth, with a wedge lip, the pad set into it and THE CLIMB on the plinth's face (the sign on a post is gone). The stage plates are 6 studs. The two masts stand off the finish tower's line, with unlit amber faces east and west. The drums have slate bodies.
- **The hill:** the bottom tier is a walkable grass bank (`tl_bank`, 140 across, in the ground's green, over sixteen half-stud invisible steps), and it is the way up from the yard (the old first ramp is gone). The upper tiers are smooth kit cylinders over invisible solids. The ramp walls are the tiers' grey, with a rounded edge along their slope. The yard's kerb that the bank would have buried is gone.
- **The Blocks' east half:** a two-high container wall down the east edge in two runs, and a container bridge from it to the stack at (50, -8510), with parapets, a Carl on it, and a pad (63, -8496) with a chevron that throws you onto it. Barriers stand in two groups of three against container walls; the small crates, drums and tyres are gone. The gateway stacks are three high.
- **The door panels:** lighter (housing 9a9ea5), a warm spot on each from in front, the idle timer reads "1:30" (the rule), and the yard's end-wall base strip stops clear of them.
- **The façade:** window frames clear of the opening, sills the opening's width, mullions on the wide windows only; the EXIT is full size, with its sign higher.
- **The lane:** the backstop's middle rises to a crown, with a target man on it (legs, arms, a head and a ring on his chest). Its amber strip runs only between the lane's walls.
- **The ridge:** two saddle lumps between the three back hills; the playground's tops are still hidden (76 of 76 from all six eye points).
- The bay's crates are warm grey; the sign posts are 2.4 square.
- The Carl-spot check now uses a part probe (shape-exact), since the bank's round steps have square bounding boxes.

Tested in Play: the bridge pad lands on the bridge, the climb pad on the deck, the finish and watchtower pads as before; the bank steps up 0.5 at most and you stand anywhere on it. The Play photo sheet is `roblox/docs/back-lot/back_lot_play.jpg`.

**Left from round 4 (not done):**
- the climb still reads as closed pale boxes from the ground: open the deck and summit into platforms on slate legs, and make the slide a chute on trestles (the judge's "one change that would lift it most")
- the ridge is still a row of matched, mirrored domes: a bell-shaped hill mesh, different heights east and west, and an `L.ridgeCheck`
- the door panel's BENCH / RANGE / COURSE labels are too small at play distance (rows instead of columns), and the Plinker's stand still covers KEEP CLEAR
- the HUD's zone line on the lot still says "the dummies hit back in here"

## 25. Bumping into things flung you: fixed, 16 November 2026 (place version 348)

The owner: "at the smallest touch it'll launch you and ragdoll you". Reproduced in a solo Play test by plain sprinting
in the hub with no rope out: the body spun up to 3000°/s, dropped into the Humanoid's `FallingDown` state and was thrown
at 540 studs/s. Grapple Impacts (BONK, LEDGE LAUNCH) never fired: it was not the cause.

**The cause.** `Jankfire.Move` held your sideways speed with a `LinearVelocity` at `MaxForce` 1e7, because the
Humanoid's own ground controller (walk where the keys point at `WalkSpeed`) is very strong and fought every slide,
bhop landing and knockback. 1e7 pressed into a kerb, a sill, a dummy or another body made huge contact shoves and spin.
Worse, each step's maths starts from the body's measured velocity, so a one-step collision spike was read back in and
then held by the 1e7 force: brush something and it snowballed into a launch. Turning the force down alone was not
enough (at 2e4 the Humanoid's walk killed a 70 studs/s knockback down to 4.5).

**The fix** (all client, `Move`, `Body`, `GrappleImpacts`, `ShredderVictim`):
- **Steering:** after reading the keys, each step Move tells the Humanoid to walk exactly where the maths is taking you
  (`Humanoid:Move` along your velocity, `WalkSpeed` = your speed), so its controller agrees with the `LinearVelocity`
  instead of fighting it. The keys come from the control module's `moveFunction` (hooked); a frame without that call
  (controls off, the loadout screen) counts as no input. If the hook can't be made, Move warns and works as before.
- `JankMove.MaxForce` = max(2e4, mass × 3500), about 3500 studs/s² (was 1e7).
- **Fling guard:** a jump in speed none of our own moves made is put back: more than 18 studs/s sideways (6 m/s) or
  more than the slide jump's height + 12 studs/s upward over what Move asked for last step. Our own throws go through
  `Body.throw(v)` and pass for 0.15 s: `Body.push` (recoil, knockback), the marble slip, the ledge launch, the
  ragdoll, the Shredder's pull. `Body.throw` also sets the `LinearVelocity`'s target at once: a knock that arrives
  after Move has set this frame's target used to be braked by it. Pads, the rope and the items' `Body.onStep` are
  inside the maths and always pass.
- **No tumbling:** spin about any axis but the vertical is zeroed each step (vertical capped at 30 rad/s), except while
  `PlatformStand` (the slip, the BONK ragdoll, the Shredder).
- The Humanoid's `FallingDown` and `Ragdoll` states are off on your character.
- **Grapple Impacts** (a Roblox-only gag, not in the web game) kept but rare: only while really on the rope (Move's
  `OnRope` player attribute, instead of "any beam in Terrain fixed to you", which a lingering server rope could keep
  true), never in the 0.6 s after letting go. LEDGE LAUNCH from 55 studs/s (was 35); BONK from 90 studs/s and only in
  the air (was 50, or 80 on the ground); 3 s between them (was 1.2).

**Tested in Play** (solo; a sprint with strafes, a slide and a slide jump in the hub, on Rooftop v2 and on Rooftop v3;
a sprint straight into a training-yard dummy): no `FallingDown`, no launches, the body stayed upright, top speed
44–50 studs/s (sprint 43.5, plus the slide). Before the fix the same hub run spun the body at up to 3000°/s and threw
it at 540 studs/s. A server knockback of (70, 35) now carries 70 sideways and 34 up through the air; it had been braked
to 4.5 at 2e4 force, and reached only 52 sideways at 1e7. The marble slip (1.7 s on your back, then up), the hub pad
(58 up) and the grapple (hook, on the rope, grapple jump, let go) all still work. Swinging into the rotunda's wall gave
no BONK. Not tried: other players bumping you (a solo test), a real BONK or LEDGE LAUNCH at the new speeds.

**The feel check, old drive against new (place version 353).** Both drives were run back to back in one Play test on a
flat test floor, with a temporary switch for the old drive (taken out again). Expected numbers are from `Config`
(the web game's `player.js` × 3 studs):

| | expected | old drive (1e7) | new drive |
|---|---|---|---|
| run top speed | 30 | 30.0 | 30.4 |
| sprint top speed | 43.5 | 44.2 | 44.2 |
| slide from a sprint: start → end | 51 → 41.8 | 50.4 → 38.4 | 51.0 → 40.2 (50.9 → 38.6 on a rerun) |
| slide length | 0.8 s, about 37 studs | 0.80 s, 35.1 | 0.82 s, 36.8 (0.80 s, 36.0) |
| slide jump: leaves at / height | 59.9 / about 7 | 57 / +5.8 | 59 / +5.0 (+5.7) |
| bhop chain (W + Shift, Space held) | keeps speed | 43 every hop | 44 every hop |
| air strafe (A + turning, 2.5 s) | gains | 44 → 61.6 | 44 → 59.6 |
| grapple pull to the pillar | | 132 | 132.7 |

The old drive's grapple peaked at 184.9, but that was the fling itself: it hit the pillar at 132 and bounced back
off it. Heights are measured on the root, so they read below the maths' 4.9 / 7.0 on both drives alike.

**Two things moved, both brought back:**
- **Kerbs.** The web game steps straight up anything 0.6 m (1.8 studs) or lower (`shared/physics.js` `PH.step`).
  The Humanoid alone manages about 1 stud at a sprint: the old 1e7 drive bulldozed over higher lips, and the
  gentler drive caught on a 1.5-stud kerb (44 → 14). Move now lifts you onto any lip from 0.9 to 1.8 studs just
  ahead of your feet when you're on the floor (not onto other bodies). At a sprint: the 1.5 and 1.75 kerbs at 44
  without slowing, a 2.1 kerb (over 0.6 m) stops you as in the web game, stairs (0.8 risers) and an 18° ramp at 44.
- **Throttled drawing.** The keys are read when the control module runs, once per drawn frame. When drawing runs
  slower than physics (an unfocused or minimised window), some steps got no fresh keys and counted as none: run
  dropped to about 12 and sprint to about 28, jittering. The last real keys now carry over for 0.15 s.

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
