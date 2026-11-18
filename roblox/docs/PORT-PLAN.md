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
- **Three looks, combined live** (16 Nov, place version 358; owner: "combine the new angles with the closer look"):
  `holds.json` keeps before / after / combined per weapon and `use` picks one; combined = the closer, bigger before
  with the barrel pointed at the crosshair like after. Scopes like Rivals' (the Sniper's lens near the screen's
  height with a soft edge; the Second Opinion's a short scope with the world round it). Sheets `gun-hold/looks-1..3.jpg`.
  Open: third person on the owner's avatar holds the gun backward (older code).
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
- **The web game's weapon skins** (place version 379): the 26 skins the web game has for the sixteen live guns
  are kit models in look C, in `ReplicatedStorage.JankfireSkins`. The crate gives them (`LootTable.SKINS`), and the
  loadout's SKINS tab puts one on per weapon (the `Skins` attribute and save, `GunSkins.luau`,
  `WeaponModels.build(id, k, skin)`). Each keeps its gun's spots, moving parts and hold. The Wood Chipper is a
  Shredder Tool of its own. Details: `GUN-MODELS.md`, "The web game's skins".
- **The Marble Shotgun's jar** shows the ammo, fuller for longer (14 balls; one shot of two leaves 9). The reload flips
  the lid, pours the balls back in and snaps the lid shut (with the Gumball Machine's crank). It keeps the web game's
  1.9 s. Frame strip: `gun-models/marbles-reload.jpg`.
- **No z-fighting inside the guns** (place version 401): every gun and skin is built with flat-on faces of different
  looks pulled apart (`tools/roblox/gun_zfix.py`: 0.04 studs on its smallest display, 8 mm at most). The armory's
  12 display guns scan clean with `ZFight`. Details: `GUN-MODELS.md`, "No z-fighting inside a gun".

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
- **Why switching is safe:** `Matches` runs one match at a time (a full pad waits with "ARENA BUSY"), so the arena only changes when a match starts, never under a live one. Kept that way rather than running a match in each arena at once. **Replaced the same day by section 26:** matches now run side by side, each in its own arena or a copy, and each pad keeps its own rotation.
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

**A bhop needs a timed press, not a held key** (the owner, 16 Nov 2026: "make sure it counts an actual b hop though
and not just holding down space"). The web game's air movement is already Source-style and Roblox's `Movement`
matches it: in the air you accelerate toward the keys with the wish speed capped at 1.4 m/s (accel 90), so only
A/D plus turning the mouse the same way builds speed; W adds none. One JANKFIRE extra: W alone in the air turns your
momentum toward where you look (2.6 rad/s) and keeps all of it. **The one difference from the web game:** there a
held jump key bhops too; on Roblox it no longer does.
- A bhop (no ground friction on the landing tick, the combo goes up, "BHOP xN" from 3) needs a **fresh press**: a new
  key-down of Space, a gamepad's A or the phone's jump button (read from the control module's `touchJumpController`),
  at most 0.22 s before the jump (the web game's jump buffer) or within `Config.bhopTicks` (3) after landing. One
  press, one jump. A tap just before landing is buffered and jumps you in the very step you land (Move sets the
  upward speed itself; the Humanoid's own jump lags about 0.13 s out of its Landed state).
- A key held through the landing still hops (the Humanoid re-jumps), but each landing is a plain ground step:
  friction and the run's acceleration, and the combo goes back to 0 (`Movement.step`, `inp.fresh == false`).
- **Tested in Play** on a flat test floor, takeoff speeds in studs/s:
  - Timed taps, A held and turning 2.2 rad/s: 43.6 → 48.5 → 53.8. After a tap that the test tool's timing put
    0.25 s early, a new chain: 35.3 → 40.9 → 42.2.
  - W-only timed taps (Shift held): chained, 43.5 → 43.5 → 43.5 → 43.5, no gain.
  - Space held, A held and turning: 44.0 → 37.9 → 33.3 → 30.6 → 29.6 → 29.0, no BHOP callouts.
  - Not tried on a real gamepad or phone: Studio's input tool only sends keyboard keys.

## 26. Matches run side by side, each in its own arena, 16 November 2026 (place version 365)

**Why:** the owner, play-testing: "we also need more pads somewhere?". The hub session is adding a bank of pads (several 1v1, some 2v2, a 3v3). With one match at a time those pads would only have queued ("ARENA BUSY"), so matches now run at the same time, the way big Roblox duel games do it.

- **A site per match.** Every live match has its own "site": the rotation's pick itself (`workspace.Map.RooftopV2` / `RooftopV3`) when no other match is in it, else a copy of it in `workspace.Map.ArenaCopies` (`RooftopV2_copy1`, ...), 7,000 studs along x (`Arena.copyOffset`: +x, -x, +2x, -2x). The arenas' cities are 6,144 studs across, so copies never touch and each sits past the others' fog. The height stays, so a copy's fall line is its arena's; its `CentreX` attribute moves with it. A copy's pool fills itself (`JankWater` fills every tagged volume when it appears and empties it when it goes). v1 can't be copied (its Blender models live in `Map.Models`), so v1 would take one match at a time if it were put back in the pool.
- **When.** A pad takes its site when its countdown starts, so a copy has 3 s to reach every screen before anyone lands in it (this place has no streaming). The site goes back 3 s after the match's players are home (`Matches.CLEAR`), and a copy is then destroyed. A pad that stops being full keeps its site for 1.5 s, so a foot on the edge doesn't clear a copy and make it again.
- **Per match, not per server.** Team spawns come from the match's site (`teamSpawns(m, team)` in `Matches`). `Arena.killY(site)` and `Arena.centreX(site)` take the site; without one they answer for `Map.Arena`, which the training dummies still use. `Main`'s "into the smog" check asks `Matches.killY(player)`. A player in a match carries the attribute `Arena` (the arena's name, for a copy too), and `HubLife` picks the light from it, so two players in different arenas each see their own. Matches no longer change `Map.Arena`; it is now only the fallback when the pool is empty.
- **Rotation and banner kept.** Each pad has its own rotation: never the same map twice in a row on that pad, and the first pick after a server starts is random. The first banner still names the map.
- **The cap.** At most `Matches.MAX_LIVE` = 6 sites at once, counting live matches and counting-down pads (the two arenas themselves count). Past that, a full pad shows "ALL ARENAS BUSY · you're next" (or "· N ahead of you"), and the pad that filled first gets the next free site.
- **Pad data**, sent to the hub session: a pad is a Model directly in `Hub.QueuePads` with a unique name (its id). It has the attributes `Mode`, `Teams` and `Size`, the children `Side1..N`, `Slot` parts (`Team`, `Slot`, `Off`), and TextLabels `Status` / `Sub`. Any number of pads works, and a pad can start another match while its last one is still live.
- **Studio test hook:** `ServerStorage.JankMatchTest` (Studio only). `:Invoke("ghost", padName, arenaName?, secs)` starts a match with nobody in it that holds a site like a real one; `:Invoke("state")` reads the live matches, sites, copies and pads' countdowns. A `TestMaxLive` attribute on `Matches` lowers the cap inside a play test.
- **Tested** in one solo play test (16 Nov 16:01 UTC):
  - Four matches ran at once: three empty test matches on v2, on a v2 copy at (7000, 0, 18000) and on v3, plus a real match with me in it on pad 1v1. With both arenas busy, that one went to a v3 copy at x 7000.
  - Spawns: I landed exactly on v3's team-1 spawn moved by 7,000 (6838, 2.7, -29991). All 7 team-1 spawns of the v2 copy are v2's moved by 7,000.
  - Physics and water: a training dummy dropped into the v2 copy stood on its floor, and the copy's pool filled with water (128 cells, the same as v2's).
  - Light and banner: in the v3 copy, v3's light (clock 13.5, fog 400 to 2,300) and the "ROOFTOP" banner; on v2, v2's light and "ROOFTOP: SKYLINE"; back in the hub, the hub's light.
  - Rotation: pad 1v1's three matches went v3, v2, v3.
  - Fall line: with v3's own line set 40 studs under the spawn for the test, dropping 50 studs gave "INTO THE SMOG". The default arena's line (-484.8) wouldn't have caught that drop.
  - Cap: with the cap at 1 and one site held, the full pad read "ALL ARENAS BUSY · you're next".
  - Cleanup: afterwards `ArenaCopies` was empty, the copies' water was gone, no sites were held, nobody was still marked as in a match, and the workspace was back to its starting part count (25,226, plus the empty folder).
  - Cost: a v2 copy took 58 ms to make and added 4,613 instances. Studio's whole process (server and client together) grew by about 80 MB per copy.
  - Photo: `roblox/docs/rooftop-v2/side_by_side_pads.jpg` (three pads showing "match on" at once).
- **Not tested:** real players in two matches at once (a play test has one player), and phones. With no streaming, every copy is about 4,600 more parts on every screen; the cap of 6 is what bounds that.

## 26. Training: the owner's play-test notes, a sealed hall, live fire, three range lanes, the mirror, 16 November 2026 (place version 373)

The owner play-tested training and sent two lists. The first said:
- "the red dummy doesnt be able to shoot you from the center of the training hub"
- "when you go up to garage doors can they slide up"
- "when you get close you hear a click and the laser gate turns off?"
- "in course ... arrows leading to like a rectangular hole in the ground is that going to be something?"
- "some of the props dont look super like rivals ones!"
- "there is a roof in the dummy part of the training hub that lets you clip through it and get outside"

The second came with photos: a redundant arrow, two wall openings each with a lone gold dummy, the empty back of the range, the dummy hall's props and dummies, and "what is the slope to the cylinder thingy?".

**The hole.** The dummy yard's vault and the muster's crown are kit meshes that nothing touches. The yard's side walls also stopped at the vault's springing (y 258.6) while the roof sat at 270.5. So a grapple went through the vault, and you could walk out over the wall tops.
- The walls now go up to the roof.
- Thick unseen solids line the inside of the vault (16 arc segments, 4 thick) and of the crown (cove, ring, lantern drum and cap).
- Unseen lids now close the range lane (4 over its walls' tops) and the course's skylight drum, which were open to the sky too.
- `T.check` proves the hall is sealed, the same way the hub's leak test does. From 54 points inside every room, a ray each way (26) must meet something solid (CanCollide) within 300 studs. Where a ray ends on a skin under 2 studs thick with nothing behind it, that skin is listed. Result: 1404 rays, 0 leaks.
- In Play, launches at 300 studs/s from the game's own pads stopped at the yard's vault (y 265.8 against its 268 crown), in the yard's corner and inside the muster's lantern cap.

**Live fire, not the whole hall** (the owner: "an area where you can activate dummies that shoot back, that way they don't shoot into the main hub area"):
- The red dummies are off by default.
- The yard's stage end is the live-fire end, behind an amber-and-slate band, with LIVE FIRE on the floor. Two shooters ("Plinker", "Plinker2") stand at its far corners.
- Hold E at the console on the line and, for 90 s (or until the end has stood empty for 8 s), they fire at whoever is inside the end. The posts' lamps turn red.
- Their shots are cut off at the line, so nothing reaches the rest of the hall.
- `Hub.TrainingGround.LiveFire` holds the data (Zone, LiveButton with its Prompt, lamps, the attribute Line). Dummies.luau runs it; in Studio, `ServerStorage.LiveTest` answers "on", "off" and "state".
- Tested in Play: off, nothing. On, inside: HP 100 to 16 in 3.5 s. On, outside the line: nothing.

**The dummy yard:**
- Lines across the floor at 10, 20 and 30 m from the yard's mouth, with big numbers on the floor.
- The two standing dummies are on the 10 m line, the moving one strafes along the 20 m line, and the shooters are past 30 m.
- Dummies are cardboard-coloured with a ring on the chest; the shooters are slate with a red ring. No name tags.
- The cover pillars and low cover walls are remodelled.

**The range** (the owner: "keep in mind there will be multiple people in these hubs"):
- Three lanes, one per plate (CHILL, NORMAL, SWEATY), each with its own run at the same time. A Carl pops only on his lane's nine spots.
- The board has a row per lane and the last thing that happened.
- Low dividers run down the lane between the booths.
- The empty back of the deck now has a kit counter with a case and an ammo crate behind each lane, a slate rack with the lanes' names, a "best today" board and two benches.
- `RangeTest` runs them; the spots carry the attribute Lane.

**Doors:**
- The back lot's garage door and the muster's shutter (the gate home) roll up when you walk up, smoothly on each screen, with a motor's whirr, and roll down after you.
- The garage door keeps its egg. Locked, it jumps a hand's width, clatters and drops while LOCKED flashes. Once you have opened it (the gold Carls), it rolls up for you like the shutter. From the lot it always lets you back in.
- The server (TheLot) decides when it moves and whether the slats block. An unseen 4-thick DoorBlock stops anyone pushing through the thin slats. The new client script `TrainingDoors.client` moves the slats.

**The laser gates** aren't training's. The red gate into training is the hub's (HubRotundaRooms: LaserVoid, LaserField, LaserBar), and the playground's ReturnDoor.LaserVoid is the playground's. `TrainingDoors.client` already handles any model tagged `LaserGate`: its LaserBar and LaserField parts switch off with a click while someone is within Near (default 9) and come back on with a click after. The gate's owner only has to tag it.

**The two openings:**
- The arched bench bay is the mirror now. You stand there as a hologram in the hub's style: see-through, a soft fill and outline, turning slowly over a lens, holding what you hold.
- The course bay is just the lit end of the view again.
- The gold Carls now stand where targets belong: on the yard's 30 m line, on the range's first beam and on top of the course's tower. The panel's labels read YARD, RANGE, COURSE.

**The course:**
- The "hole" is a long-jump pit now: 1.5 deep, a line and number every 4 studs, JUMP before the amber line, a LONG JUMP sign. Land in it and the distance shows (FOUL if you crossed the line).
- The arrows to the first pad and down the slide lane are gone.
- The "slope to the cylinder" was the chute from the tower's top back to the start. From below it read as a ramp up, and the pad already does that, so it's gone.

**Tested in Play** (two tests):
- the seal (above) and live fire (above)
- the garage door rattling and then rolling up, and its DoorBlock letting go
- the shutter rolling up as you walk up (all 9 slats into the head)
- the mirror's hologram holding the Shredder
- a range run on one lane with its Carl in that lane, and the board's rows
- the long-jump readout ("LONG JUMP · 30.4")

The photo sheet is `roblox/docs/training/training_notes_play.jpg`.

**Props and flicker:**
- Kit 6 (131746416943530) remodels the cover, block, booth and bench (plinths, inset panels, slate guards, rounded caps). It also fixes the target's rings, the crown's drum, the frames' band and the tower's base.
- About 40 face pairs from the flicker list were lifted, inset or trimmed in the builders. The training hall went from 537 visible pairs to 342 by ZFight; most of what is left is underground bottoms. The flicker session is adding `T.dezfight` (run at the end of every build) to TrainingV2 for the rest.

**Left:**
- kit-internal flicker (tl_portal, the tower's trim cap), and the rest after T.dezfight
- the laser gates' tag (hub and playground)
- a judge pass on the new range back and the yard's props

## 27. The hub, round 2: holograms, the duel hall, duck trophies, new props, no floor lines, 16 November 2026 (place version 390)

**The owner's words (16 November 2026), relayed by the main session:**
- "in the hub can the center gun thingy cycle your loadout but hologram style? we also need holograms like in rivals with bundle sets that float and people can look at and interact with"
- After a play-test: "in the match pads theres random pots on the ground? some of the props dont look super like rivals ones!"
- "can you get rid of the lines leading to the pads, we also need more pads somewhere?"
- Of the gym: "the boxing ring and the backwall decor are off center from the entrance, is that intended what should we do? maybe make it a bit bigger"; of the lockers: "too close together and looks awkward"; of the armory shelf: "some props overlay each other make sure they dont"
- "can the trophy case, can they be ducky trophies?"

**What changed:**
- **Your loadout as a hologram.** The Redline showpiece in the ring over the platform is gone. In its place, each player sees their own loadout: primary, secondary, melee and utility in turn, each in its wrap with its hat.
  - It turns slowly; each piece stays 5 s, fades, and a scan line builds the next from the bottom.
  - The look: the real model 30% see-through, a Highlight in the palette's accent (glow: soft aqua), a faint beam from the lens, a small light. The slot, the name and the wrap and hat show under it.
  - It is drawn by `StarterPlayerScripts.Jankfire.HubHolo` (a LocalScript, `src/client/HubHolo.client.luau`), on each player's own screen.
- **Bundle holograms.** Three plinths in the showroom (the south wall: sides 6, 8 and 9).
  - Each shows a bundle from the shop's catalogue (`ReplicatedStorage.Jankfire.Shop`): today's featured bundle first, then the rest. Each piece is turned and built like the loadout's: the hero weapon in its wrap and hat, then each item on it.
  - Walk up and a card says what is in it: each item with a thin rarity mark, and the price ("FREE" while `Shop.free()`).
  - E (or a click on the prompt) opens the shop on that bundle: the prompt carries `ShopOpen = <bundle id>`, which the shop's own client acts on.
  - Until the catalogue is there, four stand-in sets show and say "coming to the shop".
- **The duck trophy case** (side 5, in the same frame as the plinths): a glass-fronted case on a podium, with the gold duck big in the middle and silver and bronze either side. Each duck is the new `rk_duckTrophy` (a slate base with a blank little plate, a stem, a dish, the duck), lit warm from inside. The plate on the board reads "THE DUCK CUP".
- **The duel hall** (side 4, where the gym was): 50 x 52, symmetric on the door's axis.
  - The gym's boxing ring is the centrepiece, bigger (20 across), under a light frame with the hall's one shadowed lamp over its middle.
  - The round target is in a lit recess on the far wall, on the axis.
  - Seven more pads stand round the walls facing the ring: 3v3 straight ahead with a 1v1 either side of it, a 2v2 on each side wall, a 1v1 either side of the door. Each pad has its board on the wall behind it and a light panel over it, with piers between.
  - That makes 12 pads in all. Pads carry `PadId` (unique, = the model's name) and `Bank` ("lifts" or "hall"); Matches runs them side by side (section 26), keyed by the pad's instance. At most 6 arenas run at once (`Matches.MAX_LIVE`), so a 7th full pad shows "ALL ARENAS BUSY · you're next".
  - The rotunda's door word is DUELS; the notice board says "MORE PADS · THE DUEL HALL, EAST".
- **No floor lines** to the lifts or the rooms. **No pots** by the outer lifts.
- **New props** (`tools/roblox/rotunda_props.py`, one upload, asset 94371006780646, imported by `R.importProps()`): a planter, punch bag, tyre stack, coffee table, locker bank, dumbbell rack, gym bench and the duck trophy. They are chunky: few big rounded shapes, flat matte colours.
  - The lounge's plants and coffee table and the armory's lockers use them.
  - The armory's lockers stand against the near wall with the bench in front of them and 3 studs to walk between.
  - The cases and ammo boxes that sat on the armory's counters (an SMG went through one, the katana through another) are gone.
- **Flicker:** every face the z-fight finder listed in the Rotunda has its own plane now. Dais and floor discs have their own sunk bottoms; the ring apron sits under the base; shaft walls sit under the lids; hall lids meet the rooms' walls; hall floors sit under the round floor.

**`R.check()` gained:**
- **OVERLAP:** every pair of kit models and display guns, part against part, shrunk 0.06 so touching passes; the structural kit set into walls (`R.STRUCTURE`) is left out.
- The hologram drums count as solid for the sight lines and keep-clear zones.
- The bundle holograms are looked for from the middle of the platform, and the target over the duel hall's 3v3 through its door.
- Pad count: 12.

Now (push 33): `R.check()` 37 keep-clear zones, 0 problems, 0 leaks, 286 sight lines, 0 hidden, 40 props, 0 overlaps, 89 lamps (9 with shadows), 12 pads.

**Flicker** (`ZFight`, minY 239.5): 431 visible pairs in the old hub, 162 after the first fixes, 16 now, none of them in these builders.
- 15 are inside the armory's display guns (the weapon kit) and 1 is inside the old `bc_fridge` kit model.
- The prop kit checks 0 offline (`zfight_glb.py ... alone=rk_`).
- Run the finder after every hub rebuild.

**The training gate** (the armory's red lasers) is a Model `TrainingLaserGate` tagged `LaserGate` (Center, Near = 9). `TrainingDoors.client` switches its LaserField and LaserBars off with a click as you come within 9 studs, and back on after (owner: "when you go to the laser gate, when you get close you hear a click and the laser gate turns off").

**Tested in Play** (place versions 383 to 390, by the builder):
- The loadout hologram cycles. Shown: the Frag Grenade with "UTILITY / FRAG GRENADE / 2 charges" under it.
- The three plinths read the live catalogue: Field Issue (today's featured), Night Shift, Tea House. Each prompt carries its ShopOpen, and E opened the shop on Field Issue. The card shows when you stand near and lists the items with rarity marks and "FREE".
- The bundles' guns lie flat. A first try stood them on end: their build orientation was kept instead of their own box's, which is what the loadout screen uses.
- The gate's lasers go off as you approach.
- No errors from the holograms in the console.
- Photos: vault `Hubs\shots\rotunda\hub2\`.
- Traps: `execute_luau` puts the camera back to Custom after every call, so Play photos need `screen_capture`'s own camera position; a billboard's StudsOffset follows the player's real camera, not that one.

**Not done / open:**
- The duel hall's pads have not been played in a real match from the hall: two players are needed.
- The holograms on phones and slow machines.
- The punch bags, tyres and dumbbells of the new kit are not used since the gym became the hall; they stay in the kit.

## 28. Training: a gun shop with the owner behind the counter, your own range targets, the mirror's podium, the owner's notes, 16 November 2026 (place versions 420 and up)

The owner asked for a gun shop behind the range ("with an npc me"), for every player on the range to get their own targets, and for the mirror hologram to show your name and stats. Notes on the hall and the back lot followed.

**The gun shop** (TrainingV2, at the back of the range deck):
- A slatwall let into the back wall with 12 of our guns on hooks, a glass counter with the sidearms and items under its glass, a low shelf of ammo boxes with headsets on hooks over it, and a tall lit glass case (Shredder, katana, duck).
- Props since the owner's "add more props": stacked hard cases, duffel bags, ammo cans, a box spilt across the floor and one on the counter's glass, and magazines, ammo boxes, a scope and loose rounds between the guns.
- No words, names or marks anywhere.
- The guns are made when the server starts (`ShopKeeper.server.luau`, from `WeaponModels` at hand size), at the Pegs in `Range.Shop`. Each Peg carries Gun, Len, High, Out and Hook attributes. They are always today's models.
- The place behind the counter is shut off (`ShopBox`, up to the canopy).

**The shopkeeper** is the owner's avatar, the same for every player (the owner: "I'll be the shop owner").
- `ShopKeeper.server` builds it with `CreateHumanoidModelFromUserId(2833796200)` each time a server starts. If Roblox won't give it, it uses the saved copy `ServerStorage.ShopKeeperCopy`.
- It is anchored and idles, takes no shots, and has a "Shop" prompt (`ShopOpen = "tab:featured"`). It waves when someone opens the shop.

**Range targets per player:**
- Each runner gets his own Carls. Any number of people can stand on one plate.
- A Carl carries the attribute `Owner` (his runner's UserId), and its fighter carries `onlyFor`. `Fight.hurt` drops any hit from anyone else.
- Every other client moves him out of its world (`TrainingDoors.client`), so he is not drawn, aimed at or outlined, and `Arsenal` throws no blood off him.
- A kill counts only from the runner, and not within 0.12 s of the Carl popping up.
- In Studio, `ServerStorage.RangeHook` runs a ghost runner: "ghost", "hold", "hit", "cross", "ghosthit", "state". The client attribute `ViewAs` shows another runner's view.
- Tested in Play with the ghost on NORMAL: each screen sees only its own Carl. Your shot at the ghost's Carl does 0; your own Carl and the ghost's both count (board: "Pompompoo 01 · Ghost 01").

**The mirror:**
- The hologram is always on while you are in training (the owner: "can your big hologram just be active always?").
- It stands on a two-step podium (the owner: "I was thinking more of like a podium thing"). The upper step's front shows your rank badge, name, @handle and level. The lower step's front is a strip of tiles: kills, K/D, wins, headshot %, best streak, most held.
- Each client fills these from its own card (Stats' Profile remote), so every player sees their own.

**The owner's notes:**
- The live-fire console is at the yard's door now: you switch it on as you come in.
- The long-jump pit is gone, with its lane, words, lines and numbers.
- The pad by the course tower is gone. The pads' arrows point the way they throw you: `bc_jumppad`'s arrows run along its -Z.
- Flavour text is cut:
  - the board's joke line and the MIRROR word
  - the Carl verdicts and "25 cardboard men incoming"
  - the back lot board's last line
  - the garage callouts (TheLot)
- The big figure on the long lane's backstop is gone. The "Back" bubble stays, as the owner asked.
- Trees: each stands upright where rays down at four sides of its trunk meet the berms or the ridge. The ridge is a faceted mesh that sits up to about 1.5 studs under its ellipsoid, which is why trees floated. Steep spots move a tree to flatter ground, and a ground-coloured foot hides the seam. `L.check` now counts trees with a gap or a buried side.
- The treeline is groves, not a scatter (the owner: "the trees were sort of just spammed"):
  - one kind of tree per grove
  - round trees along the berms round the lot, pines on the outer berms and on the near ridge's tops
  - a line of plain dark crowns along the tall ridge's crest
  - nothing on the steep faces

**Checks:**
- Place version 420: hall sealed (1404 rays, 0 leaks), 27 of 27 plate-to-Carl lines clear, ZFight 1 visible pair (a kit target).
- Place version 426 (podium, props, groves): the same results, and 79 trees with 0 gaps and 0 buried. The ridge still hides the playground (76/76 from every eye point).
- The near ridge's tops proved too steep for the pine groves (all left out), so the hill faces stay grass.
- Photo sheets: `roblox/docs/training/gun_shop_sheet.jpg` and `gun_shop_sheet2.jpg`.

**Round 2 (place version 432):**
- **The shop:** a rug in the middle (a dark field in a tan border).
- **The mirror:** the hologram stands empty-handed in Roblox's plain idle, in the game's shared hologram look (`ReplicatedStorage.Jankfire.Hologram`, the VFX session's). Your weapon leans against the podium's front corner and changes when you switch (the owner: "could you have whatever weapon you have equiped laying against it"). The hub's loadout hologram is left as it is: it already cycles your loadout, and it is the hub session's.
- **The back lot's fence** (the owner: "add a fence line ... where the trees are, so you can't see the ugly parts"):
  - It runs on the berms' outer slopes just behind the round-tree groves, in front of the near ridge's foot and behind the long lane's backstop, and closes on the façade's two ends.
  - Slate posts every 12 with pale caps; panels 16 high, with a dark foot band, a framed inset and a pale rail. Each panel's foot sits on the ground by rays.
  - An unseen wall up to y 760 runs along it and over the façade.
  - `L.check`'s ring test casts rays from the floor, the long lane and the climb's top, every way but north, flat and up 20 and 35 degrees. Result: 357 rays, 0 leaks.
  - 814 parts; 70 trees, all seated.
- Photos: `roblox/docs/training/back_lot_fence_sheet.jpg`.
- **The mirror made cheap** (place version 441, after the owner's lag report, 9 to 12 fps in training). It was a full 1.8x avatar clone with layered clothing, an Animator, 288 scanline textures and a new CFrame every frame. Now it is a still statue:
  - a plain copy: no layered clothing (WrapLayer and WrapTarget gone), nothing in its hands
  - posed for 0.35 s in Roblox's idle, then every part anchored and its Humanoid and joints destroyed
  - facing out of the bay; no spin
  - the shared hologram look with lines, glitch and flicker off, and see 0.84 (without scanlines the neon bloomed white)
  - made only when your character is (a spawn, CharacterAppearanceLoaded)
  - checked in Play: 51 parts, 0 textures, 0 Humanoids
  - the perf session's measurement after it (with the VFX session's Hologram at v447): training at 60 fps (Studio's cap), render CPU 6.2 ms, down from 40 ms and 12 fps. With every light off it was 6.0 ms, and shadows off changed nothing, so no lamp cuts are needed; keep shadow-casting lamps at 5 or fewer.
- **The podium weapon** is built fresh from `WeaponModels`; a copy of the hand's model was invisible.
- **Round 3 (place version 460):**
  - The podium is gone (the owner: "I dont like that podium ... maybe we dont need the stats or guns laying down"). The hologram stands on a plain round projector: a wide low drum, a slimmer slate drum with one soft cyan glow band, a pale trim ring, the lens. No words, no gun.
  - The back lot's trees are all outside the fence (the owner: "can you unclump the trees outside also dont let them be within the gate line!"):
    - They stand in bands on the berms beyond the fence (west, east, north; the south's ridge foot is too steep).
    - Each tree goes its crown plus the last one's plus a varied gap along its band, so crowns never meet. A spot too steep is passed by, not shifted.
    - They are big (scale 1.7 to 2.3 west and east) so they show over the 16-high fence from the lot's floor.
    - The steepness and depth allowances scale with a tree's size.
  - `L.check` now also checks the trees against the fence: each tree's whole box must clear `L.FENCE` by 2.5. Result: 27 trees, 0 over the line, nearest trunks 22.4 apart, 0 crowns touching, 0 gaps or buried.
  - Photos: `roblox/docs/training/trees_outside_sheet.jpg`.
- **Head room (push 18 of TrainingV2, place version 492)**, from the hold session: strafing into the yard's live-fire console put the camera 0.6 from its top, which filled a corner of the screen.
  - The console is 1.2 lower: its top's high edge was 4.8 over the floor, above the camera (4.17 on the owner's avatar, measured in Play); it is 3.58 now, a desk you look down on.
  - `T.HEAD.guard` names props that get an unseen box 0.8 past theirs each way, from 3 under to 8 over (`HeadGuard` in `Collision`; it stops bodies and shots like the hall's other solids). Now: `ConsoleTop`, and `ShelfTop` (the shop shelf, where you could stand with your head in the slatwall's headsets).
  - In Play, strafing right into it from the same spot: the camera stops 1.93 from the console top (was 0.6). Photo: `roblox/docs/training/console_head_room.jpg`.
  - `T.headRoom(stage, step)`, run by `T.check`: from every spot 0.5 apart on the hall's floors where a 1.2 x 3.2 x 1.2 body fits, what you can see within 1.0 of your eye at head height. Walls and posts from your waist to over your eye, thin signs flat on such a wall, and tops more than 0.4 under your eye do not count. A kit model counts whole. Result: 0 within 0.6 (8 between 0.6 and 1.0: the terrace's lip, wall sconces, the garage's crates and drums).
  - With the owner's eye height (4.2, `T.HEAD.eye` is 4.5) one spot remains: on top of the garage's crate stack (-20, -8268), next to the upper crate's top. Left as it is.
- **17 Nov: the shopkeeper talks deals and sways; the hub gate's shutter no longer sticks (place versions 576 and 590).**
  - The owner: "I give players 3 special discounts on random skins if you talk to me! I want a cute sway waiting at the cases."
    - Deals prompt (E, ButtonX) with `ShopOpen = "tab:deals"`: opens the shop on DEALS, the shop session's three picks. Shop moved to F, just under it.
    - Prompt style as the hub regulars': an attachment at chest height, no hold, 8 studs, no line of sight, clickable. "NAME · DEALS" floats over him.
    - He is built as R15 from his avatar's description, lifted until his lowest part is on the floor.
    - The sway is Studio's prompt-to-animation on his avatar, second take (132873393676097, 3.97 s): head about 0.25 left and right, hands clasped, feet planted. The first take barely moved.
  - **Animations the server plays don't reach the screen after ZoneCull.** In Play the server's track ran at weight 1, but the client had no tracks and a still head. So ShopKeeper.server only sets `Idle`, `Wave` and `WaveAt` (server time) on him, and TrainingDoors.client plays them: two copies crossfading at each end, restarted whenever he is back under workspace. The hub's regulars moved to the same pattern (hub push 52).
  - **The owner's door bug:** "the door is stuck halfway open until you get near it". Going home, ZoneCull took the training area out of the world mid-close; the 2 s rescan saw no area, forgot the shutter, then re-read it as shut without placing its slats.
    - Each shutter is now a state moved toward open or shut every frame, so a reversal carries on from where it is. It opens inside Near (13) and closes past Near + 2, after 0.8 s.
    - It is kept while the area is out of your world, and set straight to the right state, with no sound, when it is back.
    - Tested: frozen 8.81 up when the area left, every slat 0 on return; opens walking up from the east and the west, shuts walking away.
  - Photos: `roblox/docs/training/hub_gate_shutter_strip.jpg`, `shopkeeper_sway_strip.jpg` (four moments of the sway, a wave, the DEALS tab), `shopkeeper_deals.jpg`.
- **17 Nov: the shopkeeper's idles are Mixamo mocap (place version 599).** The owner approved Mixamo; the main session put the clips in the vault (`Assets/mixamo-17nov`, not in git).
  - `tools/blender/mixamo_r15.py` (shared) retargets a Mixamo .fbx to an R15 KeyframeSequence .rbxm in Blender headless; it is uploaded as an Animation.
  - Uploads: happy idle 1 = 105334089716706 (2.0 s, a side-to-side sway, arms relaxed) and happy idle 2 = 78877669663605 (2.9 s, hands clasped at the chest, a head tilt).
  - Side by side on his avatar against the generated sway (132873393676097), the mocap looked more natural. On the floor for all three: feet within 0.1.
  - `Idle` now takes a comma-separated list: the first plays most of the time, and after it one of the others about one loop in three (`SOMETIMES = 0.35`), then back. In Play: 105 > 788 > 105, crossfading.
  - Photo: `roblox/docs/training/shopkeeper_mocap_compare.jpg` (generated sway, idle 1, idle 2 at two moments, then him in the shop).
- **17 Nov: the back lot's EXIT leads down to a basement (place version 653).** The owner: the EXIT door "seemly leads no where, can it be like a basement section?"
  - `T.BASEMENT` (TrainingV2): the façade's door (x 52..64), the stairwell (`well`: x 52..78, z -8300..-8290, up to 252), the basement floor 226.4 and its room (x 40..78, z -8288..-8262, ceiling 234.9) under the range's far terrace.
  - range() cuts the well out of the Backstop, the RangeEnd wall (the door's hole) and Terrace2. `T.ZONE` now starts at y 220.
  - TrainingLot `basement()` builds the rest:
    - a landing behind the door, then 16 steps running down east, solid to the bottom, a handrail on each wall, two caged lamps
    - an opening at the foot into the room: pipes on brackets, a boiler with a flue, a tank, shelves of crates, a fuse box, three caged lamps
    - the way out: a door in a niche in the west wall, EXIT over it, with the LotExit trigger (back on the muster's spawns), replacing the old recess trigger
  - Below the hall's floors (236) it has walls of its own, all 2 thick.
  - Checks: the hall sealed (1482 rays from 57 points, now including the stairwell's foot and the basement; 0 leaks). Head room 0 within 0.6. The lot closed in (0 leaks). ZFight 1 visible pair (the old kit target).
  - Trap: a solid block's footprint is not the only thing in a hollow. The first build left Terrace2 (236..248) filling the stairwell; T.check's head-room line caught it ("Terrace2 within 1.0, floor 230.6").
  - Photos: `roblox/docs/training/basement_sheet.jpg` (the doorway from the lot, the stairs, the basement, the way out).
- **17 Nov, the lot round 4 (place version 662):**
  - The owner's bounce pad, matched by photo, was the finish tower's strong pad at (-98, 240, -8684); it is gone, so the climb is the way to the TOP. Photo: `bounce_pad_found.jpg`.
  - joxex21 (the owner: "can you add oxex21 @joxex21 down there"; user id 194032313, display name joxex21) sits on a crate in front of the basement's shelves, facing the way in.
    - A HubNPC Seat built by HubNPCs like the hub's regulars: their own avatar (fallback ServerStorage.JankfireNPCs.joxex21), name label, anchored, no shots.
    - Idle: the hub's Mixamo seated breathing (81991323034085), with a glance now and then (114005193645149). The clips and the living layer play on each screen.
    - In Play: nothing they touch but their crate; their track plays on the client.
  - The stairwell's south handrail (the owner: "the one that isnt is just floating") starts where it drops under the door's sill, so there is wall behind it all the way; brackets into the wall on both.
  - The hills' dark lumps (the owner: "get rid of the little dark green lumps on the hills") were the far ridge's FarTrees crowns: gone.
  - The fence (the owner: "raise the wall on the left side so its complete wall all at the same height"): one top all the way round, 16 over the highest ground any post stands on (rails at 277.7); each panel reaches down to its own ground.
  - The muster's gate home is on the hub session's corrected GateKit: the laser fence at the face, the roll-up door behind it, and behind that the doorway plate. That plate was amber (GatePortal) at first; since hub push 61 it is the old black plate again (GateBack), as the owner asked.
  - Checks: the hall sealed (0 leaks, 57 points), the lot closed in (0 leaks), head room 0 within 0.6, trees all outside the fence, ZFight 1 pair.
  - Photos: `lot_lumps_fence_before_after.jpg` (the owner's high angle), `lot_round4_sheet.jpg` (the rails, the gate home, joxex21).
- **17 Nov, the basement's real way out, the stair-foot hole, the gold dummies' door kit (place version 674):**
  - The way out (the owner: "can you make the exit actually connect to an exit because there should be no way for it to just tp you back into the main hub area"):
    - The EXIT door in the basement's west wall stands open onto a landing under the far terrace. Stairs climb south (flight A, under a 4-thick piece of the terrace), turn on a landing inside the backstop bank, and climb east (flight B) to a corridor at the far terrace's height (248).
    - A plain door in the bank's face, west of the big target, lets you out onto the far terrace. It has 24 risers of 0.9, handrails on brackets and four caged lamps, with EXIT over both doors.
    - The old `LotExit` teleport is gone. `OWNED_DOORS` still lists it, so a rebuild clears an old copy, and `T.check` no longer asks for it.
    - The door out is one-way (`WalkOutDoor`, tagged `OneWayDoor`, `TrainingDoors.client`). It swings open onto the terrace on the screen of whoever comes up the corridor (its `Inside` box), and stays open while they are within `Near` of it. Its leaf and `Block` let only them through.
    - From the hall it never opens, so nobody can reach the lot without the gold dummies this way. The anti-cheat skips it (`ACPass`).
    - Geometry: `T.BASEMENT.exit` (TrainingV2). `range()` splits Terrace2 and hollows the bank's west half (skins, the door hole, a ceiling at 257); TrainingLot `basement()` builds the rest.
  - The hole at the stairs' foot (the owner: "there's a hole in the ground once you go down the stairs"): a 6 x 2 strip between the foot and the basement's floor, where the south wall stops to let you in, had no floor. `WellThreshold` fills it.
  - `L.check` now probes the basement's floors: a ray straight down every stud over the room, the stairs' foot, the stairwell and the walk-out, skipping columns that are wall. 1488 probes, 0 holes. Head room on the walk-out is 9 at the least: the corridor, and the top of flight B.
  - The lot's `Area` is two boxes now: the loading bay, and everything past the façade. TheLot reads any number of them. The old single box ran from the garage door's line across the whole width, so the range's far end and the basement were `OnLot` and had the lot's open-air light. Now the switch happens in the doorways.
  - The gold dummies' door kit (`TrainingLot.eggDoor`, built where `T.EGG_DOOR` says; nil until the owner's screenshot shows the dead end):
    - A roll-up door with LOCKED over it and a dark doorway behind it, the corridor's sides filled.
    - Key holders (`LotKey`) see it roll up as they come, OPEN on the plate, and pass through. Everyone else sees it stay down, and it rattles and flashes LOCKED.
    - The trigger `Doors.EggPortal` (Land `PlaygroundArrive`, `NeedKey` `LotKey`) takes only key holders to the playground. LaserDoors now honours `NeedKey` on any Land door.
    - `L.check` checks the trigger and its landing, and casts 39 rays across the shut door for gaps.
  - Checks: the hall sealed (1560 rays from 60 points, 3 of them new in the stair hall; 0 leaks), the lot closed in (0 leaks), head room 0 within 0.6, ZFight 1 pair.
  - Photos: `basement_walkout_sheet.jpg` (the open EXIT door from the basement, flight A, the door out on the far terrace by the target, the stairs' foot with its floor closed).
  - Play test (no save): walked from the basement's floor up both flights to the corridor with nothing in the way (root 229.1 to 250.7). The door swung 90 degrees and stopped blocking. Out on the terrace, 8 studs away, it shut; pushing at it from the terrace stops you at its face, and it stays shut.
- **17 Nov, the gold dummies are everyone's own (place version 715):** the owner, from the friends' preview: "yellow dummies to enter outside once shot by someone dont appear for others". The three gold Carls were shared, so one player's shot took a dummy away from everyone.
  - Every player has their own three gold Carls, their own 90 s and their own count (TheLot's `hunts`). A gold Carl carries `Owner` (the player's UserId) and `f.onlyFor` (the player), the range's pattern: every other screen moves him out of its world (`TrainingDoors.client`'s Carl sort), and `Fight.hurt` drops anyone else's hit. The shot is still the server's to judge (Fire remote: eye, line of sight, aim).
  - Shooting all three of your own gives you, and only you, the saved key (`LotKey`, `JankfireLot_v1`). The door rolls up on your screen (the reveal), with the door's whirr. The old 45 s opening for everyone is gone, so nobody else's door moves.
  - A key holder has no gold Carls (found for good), and their panel shows all three lit and OPEN.
  - The panel over the garage door is painted on each screen from your own attributes, `LotGold` (bits 1, 2, 4) and `LotGoldBy` (server time your clock runs out). The ding, the chime where he stood and the buzz when your time is up play on your screen only. The server no longer touches the pips or the clock.
  - New `LotTest` ops: `ghost` (a stand-in hunter with its own UserId and three gold Carls, seen through the client's `ViewAs`), `ghostgold`, `ghostgone`, and `setkey` (put the saved key back exactly). `open` now finishes the first player's own hunt. Losing the key (`forget`, `setkey`) starts a fresh try with all three standing.
  - Play test with two hunters (you, plus the stand-in, UserId 7):
    - My real sniper shot at my gold 1 did 55, KO, "GOLD 1 OF 3". My screen then had my gold 2 and 3 only, while the stand-in still had all three.
    - My shot at the stand-in's gold 1 landed nothing, and it still stood.
    - The stand-in finished its three without touching my count. My clock ran out ("TOO SLOW", the buzz on my screen, all three of mine back, the panel idle at 1:30).
    - Then I shot my three again: "THE GARAGE IS OPEN", ding and whirr, the door rising on my screen while the server's door stayed shut, the panel OPEN, my save key true.
    - The Studio save was put back exactly afterwards (no key, eggAt 0).
  - Photos: `gold_dummies_per_player_sheet.jpg` (B's screen with B's gold 1 standing, A's screen from the same camera without A's, A's panel at 1 of 3 with A's clock).
- **18 Nov, a roomier yard and course, and the gold dummies' door (place version 746, TrainingV2 push 19, TrainingLot push 16):** a friend found the hub too cramped, and the owner added: "perhaps in the training hub too the dummies and course section I really like the shooting range trhough and me". The range, the mirror and the muster are as they were.
  - **The dummy yard:** the vaulted hall is unchanged (vault, piers, stage and live-fire end, console, garage door, 10/20/30 m lines, gold dummy 1). Its west wall opens on an arcade (its own piers stand free as columns, rounded white noses under every head) into a side hall 28 wide the yard's length, under a flat coffered ceiling with lit panels (`AISLE`, `aisle()`). Floor width 48 to 80. The side hall has its own three: `Stand3` at 10 m, `Stand4` on a round stand at 20 m, the second strafer `Dummy2` at 30 m (Dummies.luau: three more names, strafing by the `Dummy` prefix). The west walk's two cover walls moved into it, along its far wall; its end wall has the big target (head-guarded). The main lane's standing two are 18 apart, not 14. The arcade stops at the stage's pier: the live-fire end stays walled.
  - **The course:** an L, about twice the floor. The same short passage from the muster comes into an entry strip 102 wide (`STRIP`); the main hall runs north from it, 68 wide and 194 long, to the back lot's façade. Same height. Ledges 1-3 (about 60 long each) up the west wall, the gallery on the north wall, the tower under the skylight on the main hall's axis (x -98, gold dummy 3 on it: `T.COURSE`, read by TrainingLot), a far tower a fifth bigger, 7 grapple rings on beam crossings from the entrance to the gallery, the start bay, the bullseye and `TrainingArrive` over ledge 3. Two broad watch steps against the strip's north wall, the first thing you face coming in.
  - **The gold dummies' door** (the owner, 17 Nov: the dead end "should be the locked door connected to the dummies", "up the ramp on the left side", "a portal teleporter that takes you to the training area thats in the air"): coming into the course, on your left in the strip's south wall, the muster's frame opens onto a ramp up (4 in 16) and a corridor (warm walls, a dark skirting, the upper corners cut off, as in the owner's shot) that ends on TrainingLot's `eggDoor` (`T.EGG_DOOR`, from `EGGC`). LOCKED for everyone until their own three gold dummies are found; then it rolls up on their screen, OPEN, onto the dark doorway (`Doors.EggPortal`, NeedKey `LotKey`) to the playground.
  - The lot's façade runs 46 further west (to x -146, a pier and two windows more) so it still fronts the hall; the berm and the tree row beside it start past its end. The zone: x -140..86, z -8058..-8308.
  - Checks (`T.check`): the hall sealed (72 points, 1872 rays, 0 leaks; the 3 thin skins are the muster's old ones), head room 0 within 0.6, plate-to-Carl lines 0 of 27 blocked, 0 arrival points blocked, the egg door shut (39 rays, 0 gaps), the lot closed (0 leaks). ZFight: 548 pairs to 1.
  - Play test (one solo Play): all 9 dummies up, `Dummy2` strafing x -34 to -55; without the key, standing in the egg doorway did nothing; with the key the door rolled up (OPEN) and walking through landed me in the playground, 2.6 from its arrival; the Studio save put back (egg false, eggAt 0).
  - Photos: `training/roomier_training_sheet.jpg` (the arcade, the side hall, the course from the gallery and from the door, the egg door locked and open).
- **18 Nov, the practice lane (place version 766, TrainingV2 push 20):** the owner: "can the training hub be like the overwatch training one to an extent like the indoor part except for the shoot range that can stay as is". What that kind of range does, in our own look: bots that stand, move on set paths or shoot back; a high-health bot for damage; distances; heal packs; open room to move. The range, the mirror and everything from v746 are as they were.
  - **Rails:** a dummy's spot with `Span` (studs each way) and `Speed` (walk speed) runs on a rail (Dummies.luau; a dark bed with chunky stops under it, `rail()` in TrainingV2). The yard's own strafer keeps its 12 at 22 (no attributes, its 1.6 s flip).
  - **The practice lane** (the yard's side hall, `T.LANE`, spots `Lane = "practice"`): rails at 10 m (slow, 8), 20 m (14) and 30 m (20, up on the deck). Two consoles at its start, the live-fire console's kind (hold E): BEHAVIOUR cycles strafe, strafe and jump, shoot back, still; HEALTH cycles 100, 300, 50 (the dummies' tone goes lighter or darker; size stays, since hits are judged on one body size). Shoot back is the live-fire burst (3 shots), only at players inside the lane's `Practice.Zone`. The settings are the lane's, for everyone in it; the prompts show the current one.
  - **The deck:** the lane's far third raised 6 (a slate mass, white nose, lit edge), stairs up the arcade side, the 30 m dummy on it: shoot up at it, or climb and fight down the lane. The 20 m round stand went; the target sits over the deck.
  - **Your numbers:** the deck's face is a board, DAMAGE / DPS / TIME TO KILL, painted on each player's own screen by the new `PracticeBoard.client` from the server's `Dmg` events (your hits on any training dummy; a burst ends after 2 s without a hit).
  - **Heal pads:** a round pad with a green plus at the lane's start and one on the live-fire stage: +75 HP under full health, then dim for 10 s (Dummies.luau finds any Model with `Heal`/`Every`).
  - **The course:** a `Runner` on a long rail (18 each way at 14) between the towers, to shoot while you swing.
  - The lane's consoles are guarded for heads like the others, but their guards stop bodies only (`T.HEAD.bodiesOnly`): you shoot over them.
  - Test hook (Studio): `ServerStorage.PracticeTest` "mode" / "hp" / "state".
  - Checks: sealed (0 leaks), head room 0 within 0.6, Carl lines 0 of 27, the egg door shut. Play: two real sniper hits on the 10 m dummy (55, 55 KO) read DAMAGE 110, DPS 79, TIME TO KILL 1.40 s on the board; HEALTH 300 gave the lane 300/300; shoot back took me 100 to 32 in 4.8 s; the heal pad healed and went dim; the prompts read "Dummies: Still" and "Dummy health: 300"; back to strafe and 100.
  - Photos: `training/practice_lane_sheet.jpg`.
- **18 Nov, the hub egg (place version 819, HubEgg push 3):** the owner: "Can there be a secret Easter egg hidden somewhere in the hub a backfire manaqueen player?? With the exact crusty look" (backfire: JANKFIRE). The web game's player stands hidden in Hub v3 as a mannequin on its plinth. Touching it gives the OG title once.
  - **The look is the web's own code, not a redraw:**
    - `tools/roblox/hub_egg_dump.mjs` runs the web's `buildCharacter` (copied from `public/js/models.js`) and the real `clothes.js` in Node, with three 0.170.0 from a local copy (`hub_egg_hooks.mjs`, env `THREE_DIR`).
    - It uses the default look: Sash + Shorts, the default skin, the first player colour (pink), the locker mannequin's weight shift and the character screen's plinth (`preview.js`).
    - Every triangle and its colour goes to `roblox/assets/hub-egg/mannequin.json`. `tools/roblox/hub_egg_mannequin.py` makes the upload: 3 studs to the web metre, flat shaded, baked vertex colours.
    - Three pieces: the mannequin, the plinth, and the outline everyone else saw on a web player (`remote.js`: each piece 1.12x, inside out, in its colour; only its rim shows).
    - Nothing is cleaned up: six-sided limbs, 6 x 4 ball joints, the egg head with its mould seam, the price tag on the arm.
  - **Where:** the hub session's nook (HubRotunda `R.EGG_SIDE` / `R.EGG_NICHE`, kept in every rebuild), behind the dark gallery "window" over the west arch into the lounge (side 8).
    - It is a small closed room on the lounge's roof (floor 260.96; 8.6 wide, 8.1 deep, 8.4 tall).
    - From the round room's floor the balcony hides it. From the balcony it is a dark window with a faint warm glint.
    - You reach it by a jump pad to the balcony, then round to the south-west, then a 3.03-stud hop onto the sill.
    - `PolishBackup.HubEgg` (`E.build()`, `E.check()`, `E.NICHE` / `E.FACE` / `E.BACK`, asset 139602935358805) builds `workspace.Map.Hub.HubEgg` outside the Rotunda, so the hub's `R.build` leaves it. The plinth stands 1.3 back from the room's middle, facing out of the window, with a dim warm PointLight near the lid.
    - Checks: nothing in its box, flush on the lounge roof, 1 stud over its head.
  - **Finding it** (`server/HubEgg.server.luau`): walk into its unseen box round the plinth, or use its "Touch" prompt (phone and controller too).
    - The first time, `Loot.grant(p, "egg:title:og", "hubegg-<uid>")` gives the OG title, kept in your loot save, with one receipt per player.
    - A small line says "NEW TITLE · OG" (Hud's small kind). A slice of Pro Sound Effects' "Musical Toy Top 1" (1.3 to 3.0 s) plays in your own PlayerGui, so only you hear it.
    - After that, the prompt only plays the slice again.
  - **The secret rarity** (`CardStyles` rarity `"secret"`, pink) is never sold or rolled:
    - `forSale` leaves it out; `Shop.secret` keeps it out of singles and the day's six; LootTable rolls only the rarities it knows.
    - `Shop.offer("egg:<kind>:<id>")` is a pass, so the loot server's "buy" refuses it.
    - The card's picker shows a secret title only once it is yours.
  - **Play tests** (solo, v809 and v819):
    - "buy" of `title:og` gave "that isn't for sale"; of `egg:title:og`, "comes with VIP".
    - Stepping up to the plinth gave OG in 0.2 s. The line showed. The slice played (TimePosition 1.51 at 0.3 s, Interface group) and was gone after 2.2 s.
    - The hop: from the balcony, 3.5 studs out from the sill, walking at the window with the game's own movement (controls off, `Humanoid:Move` each frame) and one press of the pad's A through `PadTest`. The body rose 4.78 against the 3.03 sill and landed in the room, and the touch gave OG with the line and the sound.
    - The owner's Studio save was put back to its titles (vip) after leaving the box.
  - **Test hooks:** `ServerStorage.HubEggTest` "state" / "find". In Studio each find has a fresh receipt, so it can be found again.
  - **Traps:**
    - The game's controller ignores `Humanoid:MoveTo` from a test: disable the PlayerModule's controls and `Humanoid:Move` each frame, or step the body with `PivotTo` (and `TeleportT`).
    - Put the save back only after moving the body out of the touch box. A body left standing in it touched again and found OG again after the v809 restore.
  - Photos: `hub/hub_egg_sheet.jpg` (the mannequin in its nook, the first glimpse from the balcony, the round room's floor).
- **18 Nov, the gold dummies' door in the TOP frame, with a portal (place version 897, TrainingV2 push 21, TrainingLot push 17):** the owner sent a shot of the course's TOP frame on the gallery (its dark panel under the lit strip, the orange TOP word over it): "this door is still open bro this is what should lead to the teleporter". Their 17 Nov dead end ("should be the locked door connected to the dummies", "a portal teleporter that takes you to the training area thats in the air") was this frame all along. The v746 door was built in a new corridor off the strip instead, so the frame stayed a dead end.
  - **Where:** the TOP frame (`TOPD` in TrainingV2) stands 2.4 further out from the north wall. `TrainingLot.eggDoor` (`T.EGG_DOOR.room`) puts the locked roll-up door in its mouth, with LOCKED on a plate under the TOP word. The door is LOCKED for everyone, and rolls up only on the screen of a player with `LotKey`.
    - A dark sheet (`EggSheet`) rolls with the slats, so the lit room doesn't show through their gaps.
    - Behind the door, through the north wall, `topRoom` builds a 7-stud room in the frame's own look: warm lining, a dark skirting, the cut top corners carried on, a lit ceiling strip.
    - The collar between the frame and the wall is in the wall's colour. The frame's own depth is lined with unseen solids, since kit meshes have no collision.
  - **The teleporter** (`te_portal`, `tools/roblox/egg_portal_models.py`, Model asset 125041627506798, `L.PORTAL_KIT`; `L.import(L.PORTAL_KIT)` puts it in JankfireMeshes): an off-white ring 9.5 across with a black middle, one thin amber line round its inside, and three slate clamps, standing on a step (`EggPortalStep`).
    - There is no light column and nothing shines upward. The owner, earlier the same day: "I dont like the pillar of light from the teleporter". That was the hub jump pads' light column, already removed in v889 (7d0898c).
    - `Doors.EggPortal` is the ring's black middle, from 1.6 in front of the ring's plane back to the room's back wall. Walk up the step into it and LaserDoors takes key holders to `PlaygroundArrive`.
    - It runs back to the wall because LaserDoors looks every 0.1 s and a walking body crosses about 2 studs in that. The first trigger (1.9 deep) was crossed between two looks, and the body came to rest behind it.
  - **The strip's corridor from v746 is off** (`EGG_STRIP = false`; the code stays) and the strip's south wall is closed. The lore session moves Mina, who stood in it.
  - **The owner's live save holds the key** (`JankfireLot_v1`, egg true since 17 Nov 18:34 UTC, read only), so on their screen the door rolls up as they come.
  - **Checks** (`T.check`):
    - the hall sealed (1872 rays from 72 points, 2 of them in the new room, 0 leaks);
    - head room 0 within 0.6;
    - the egg door shut: 39 rays, 0 gaps;
    - the lot closed: 0 leaks;
    - ZFight: 1 pair.
  - **Play test** (one solo Play; the Studio save put back to egg false, eggAt 0):
    - Without the key: walking at the door stops you at it (root 0.1 behind its face). The slats only rattle (0.06) and LOCKED flashed red for 42 frames.
    - With the key (`LotTest` "setkey"): within 2.5 s the plate read OPEN, all 8 rolling parts were up and hidden, and `EggBlock` let you through.
    - Walking at the ring: the step lifts you 0.6. With the deeper trigger (the same size as in the build), you were taken in 0.12 s to the playground's arrival (0, 306.7, -9388).
  - Photos: `training/egg_top_door_sheet.jpg` (no key: LOCKED; with the key: OPEN onto the portal; the room and the ring).
- **18 Nov, the muster's passages finished (place version 905, TrainingV2 push 22):** the owner, from the course's side of the passage into the muster: "can you fix the back side of this to make it look presentable". The short splayed passages west (to the course) and east (to the range) were bare beige walls with a flat ceiling and one small light. `muster()` now gives them the house's finish on every face you see from inside:
  - a dark skirting that follows the ramp;
  - a framing strip at each end of each wall, with a pale panel between;
  - a cornice with its white nose;
  - a lit coffer (rim and panel) in the ceiling;
  - the room-side opening framed in white noses (both jambs and the head).
  - Checks: sealed (0 leaks), head room 0 within 0.6, the lot closed, the egg door shut.
  - Photo: `training/muster_passage_before_after.jpg`.
  - The same push carries the v3 rooms (`TrainingRooms.luau`, `T.ROOMS`), still switched off (`"v2"`) until they are judged.
- **18 Nov, the dummies room and the course redone (place version 917, TrainingV2 push 22, TrainingRooms):** the owner, of the muster with its COURSE and DUMMIES arches: "instead of an extension can you do a complete remodel the only thing I want to keep is the vip room and the shooting range area and the training hub but these two rooms can be redone entirely".
  - **Kept:** the muster (the training hub), the range, the basement, the back lot and its garage door. The old yard had grown a side hall through an arcade, and the course an entry strip; both read as add-ons.
  - **The owner's reference** (`practice_range_2.0`, a game's practice compound ripped to a .blend: rendered headless with auto-run off; nothing taken from it, no look or layout copied): a compact multi-level compound under a rock cliff, with building blocks whose roofs are decks, steel bridges between them, and things overhead everywhere. The main session added: vary the height, one centrepiece per room, a less tube-like course.
  - **One building, the same bones in every room** (`roblox/studio-tools/TrainingRooms.luau`, `PolishBackup.TrainingRooms`; `T.ROOMS = "v3"`, and `"v2"` brings back the old yard and course):
    - piers on a steady rhythm up the long walls, each with a dark base, a white cap, a haunch where its beam lands, and a sconce;
    - deep roof beams from wall to wall with rounded white noses, and a flat ceiling with lit panels in every bay;
    - a dark plinth and a pale band low on the walls, and a band of high pale panels with a lit cove (the clerestory) between the piers.
  - **The dummies hall** (x -64..24, z -8146..-8258): one hall 88 wide under one roof, with no arcade.
    - The main lane is on the muster's axis: the 10, 20 and 30 m lines, the strafer, the live-fire stage with its two shooters, and the garage door in the end wall.
    - The practice lane sits beside it: rails at 10 m and on the gantry, the deck at 30 m with its board, the big target over it.
    - A waist-high lane wall parts the two lanes.
    - The centrepiece is the **gantry**: a deep grey girder across the whole hall at the 20 m line, on three towers. It carries the room's one accent, a thin amber line, and a lit underside. The practice lane's 20 m dummy (Stand4) rides a rail on its deck, so you shoot up at it.
    - The **overlook**: a mezzanine across the front wall above the muster's arch (259) on chunky corbels, with a low parapet and one chunky stair up the east side. It looks down both lanes to the garage end.
  - **The course** is a low lobby off the muster's west passage (panelled, two benches, two beams), open on its far side into the course hall (x -132..-72, z -8102..-8296), the tallest room. Its piers and beams are 32 apart, a calmer rhythm (at 16 the hall read as "a corridor of piers"). In it:
    - broad watch steps up the south wall to the walk (2 high, to hop up and to sit on);
    - the west walk on brackets (254), with a gap to cross;
    - the core on its plinth under a skylight (the centrepiece), bridged from the walk;
    - a steel bridge across the hall from the walk to a new east block, with an amber line on its faces;
    - pads: the floor to the walk, the floor to the core's ledge, the ledge to its top, the walk's end and the block's end up to the gallery;
    - grapple rings on the beams;
    - the runner on its rail between the core and the bridge;
    - at the far end, the TOP gallery (270): a solid mass the hall's width with panels and pilasters. The gold dummies' door (TOP, x -102) and its portal room are in its back wall.
  - **Gold dummies:** gold 1 moved to the practice deck's far corner (`T.GOLD1`, TrainingLot's `L.GOLD[1]`), gold 3 to the core's top (`T.COURSE`); gold 2 is the range's.
  - **Checks** (`T.check`, live):
    - the hall sealed (2184 rays from 84 points, 0 leaks; 4 skins under 2: the 3 old ones and the walk's slab);
    - head room 0 within 0.6;
    - plate-to-Carl lines 0 of 27, the gun sessions' test line clear;
    - arrival points 0 blocked;
    - the lot closed (0 leaks), the watchtower in view 12/12 from the yard's steps;
    - the egg door shut (0 gaps);
    - ZFight: 1 pair.
  - **Play** (one solo Play; the Studio save put back to egg false, eggAt 0):
    - Real sniper shots: gold 1 from the practice lane's floor (71.7 studs) did 55, KO, "GOLD 1 OF 3"; gold 3 from the TOP gallery (87.6 studs) did 55, KO, "GOLD 2 OF 3". From behind the gantry's middle tower the server rightly refused the shot.
    - With the key, the TOP door read OPEN and walking in took me to the playground in 1.0 s.
  - **The lore session re-seats** Auntie and Todd, whose v2 spots (the watch steps, the far tower) are gone.
  - Photos: `training/v3_rooms_before_after.jpg`.

**Traps:**
- `ZoneCull` is on now: a server-side `PivotTo` into the hall drops the character through a floor its client has not drawn yet. In a Play test set `workspace:SetAttribute("ZoneCull", false)` on the server first.
- With ZoneCull on, hop into the hall with the root anchored for about 1.5 s (`HumanoidRootPart.Anchored = true`, `PivotTo`, wait, unanchor): the client brings the area back before the body falls. Don't park a photo camera in the hall while testing the trip home: ZoneCull keeps an area by the camera too.
- `Humanoid:MoveTo` from the client doesn't move the character in this game: drive it with `Humanoid:Move(direction)` every frame.
- From `execute_luau` on the client, the player's ControlModule writes `Move` every frame and wins: first `require(PlayerScripts.PlayerModule):GetControls():Disable()`, then call `Move` from `BindToRenderStep` at `Enum.RenderPriority.Character.Value + 5` (unbind after).
- `screen_capture` calls in parallel time out: take them one at a time.
- A copy of the character's `HeldWeapon` comes out invisible on its own player's screen: first person hides it there. Build a display gun fresh from `WeaponModels` (skin, wrap and hat from `GunSkins`, `WeaponModels.wrapFor` and `GunHats`).
- A commit swept in another session's unfinished Arsenal change (1fb2d29); a2d6e3c took it back. Before committing a shared file, check `git diff --cached` for other sessions' hunks, not just `--stat`.

## 29. The hub, round 3: a second floor of pads, a VIP room, the hologram at eye level, the gym for looks, true-size guns, four regulars, 16 November 2026 (place version 448)

**The owner's words (16 November 2026), relayed by the main session:**
- "I liked the old locker room with the boxing ring hmm, can the hub hologram that shows weapon still be a little lower?"
- "can you try to create a second floor of pads above the current one and add stairs or escalators up on both sides? ... we can move the how to play and notice board elsewhere and then we can recreate the boxing gym and put just for aesthetic", then "actually wait we dont need stairs or escalators, we already have the jump pads"
- Of the centre hologram: "can it be even lower? like I don't have to look up to see it? also can the sweep start lower, like at the base of the hologram cone?"
- Of the armory's display guns: they "look massive, at least scale them, because a revolver is not the size of a sniper". Of its workbench: "can we fix that crafting station or replace it with something else?"
- VIP, the game pass (the shop session's), "lets you enter the VIP room".
- "Can you put these two as NPCs somewhere?" (Looticus, Dune), then "This one too" (Frisk1636), then "Can you put this person inside the VIP room with the sliding doors?" (Trisangle)
- Of the VIP room's duck: "can you have it face the other way?"

(For one afternoon the extra pads were in a duel hall behind the gym, then on a second floor reached by escalators. Neither went live: the second floor reached by the jump pads replaced both.)

**The second floor** (`HubRotundaLifts`): a crescent hall over the five lifts, at the balcony's height (`R.UP_Y` = 14.04).
- Seven pads round its outer wall, left to right 1v1, 2v2, 1v1, 3v3, 1v1, 2v2, 1v1 (`R.UPPER`, 14.5 degrees apart seen from the focus). Each has its board on the wall behind it and a light panel over it, with piers between.
- Pads keep the contract: `PadId` = the model's name, `Bank` = "upper" (the lifts' are "lifts"). 12 pads in all; Matches runs at most 6 arenas at once.
- The way up: the jump pads (sides 3 and 11) throw you onto the balcony. Their outward push is now 6.2 (was 7.6), so you land mid-balcony, not against the wall.
- A doorway off the balcony over each of the four outer lifts (sides 12, 13, 1, 2: `R.UP_DOORS`) leads in, framed in pale cream. From where a jump pad lands you, the next doorway is right beside you.
- The way down: the balcony's gap over each jump pad, as before.
- HOW TO PLAY and the notice board stay behind the jump pads. The notice board's first line is "MORE PADS · UPSTAIRS".
- The lift bays under it were tall shafts lit from the top. They are 13 high now, with the second floor as their ceiling, and their lights and the cove over the boards moved under it.

**The hologram at a standing player's eye** (`HubRotundaCentre`): its middle is at 6 (was 8.2, first 13.9). It now sits on a low projector pedestal (the lens at 2.4) inside a ring rail of radius 4, so nobody walks into it.
- The eight spawn points moved to two rows just south of the rail (x -2.4 to 2.4, d -8.4 and -9.9), still looking north. From any further out, the side lifts' plates hide behind their piers.
- The build sweep (`HubHolo`) now starts at the lens, the foot of the light cone, and is visible from the first moment. It is as narrow as the cone there and widens with it, then builds the piece from its foot to its top in 1.5 s and fades.

**The VIP room**, behind the lounge, on the spawn's axis (`HubRotundaRooms`):
- **The door** is in the middle of the lounge's far wall, behind the duck: dark leaves in a brass frame, with "VIP" over it. Who may pass is the server's decision, by the shop's `Vip.isVip`; the player attribute `VIP` is only for looks.
  - `ServerScriptService.Jankfire.HubVip` (`src/server/HubVip.server.luau`) puts the leaves in collision group `VipDoor` and a VIP's character in `VipGuest`, which passes through them. It sets that on spawn, on every new part and on `Vip.changed`. Until `Vip.luau` loads, nobody is VIP.
  - `StarterPlayerScripts.Jankfire.HubVip` (`src/client/HubVip.client.luau`) only does the looks: it slides the leaves open on a VIP's own screen as they come near and hides the prompt.
  - Anyone else finds the door shut. Its prompt ("Get VIP", `ShopOpen = "vip"`) opens the shop on the VIP tile.
  - As a backstop, the same server script puts anyone who isn't VIP back out in front of the door, twice a second. The room is the part tagged `VipRoom`; its attributes `Out` and `OutLook` say where they go.
- **Inside**: a cosy, darker, warmer lounge with its floor level with the lounge's raised back.
  - Walnut panelling under a brass line, and a warm light hidden along the tops of the walls.
  - Plum sofas facing each other over a round rug, with a low table between them.
  - A gold duck on a dark plinth at the far end, under a ring of light, turned to look at the door (the model's own front is its back).
  - Two plinths by the door show the VIP pack turning: `HubHolo` with `Offer = "vip"` lists `Shop.vipItems()`, the pack's live skins on their own weapons, then its wrap and hat. They stay empty until the Ducky skins are in the place.

**The gym, for looks** (side 4): push 37's locker room. The ring is centred on the door's axis, 19 across, under its light frame. Lockers and benches by the door have room to walk; bags, weights, tyres and the sparring dummy stand round the walls. There are no pads in it and nothing behind it. The round target is in a lit recess at eye height.

**The armory**:
- Every display gun is at its true size, one scale for all (`GUN_K` = 3.5: the sniper 7.3 long, the AR 4.2, the revolver 1.5, the pistol 1.2). The long guns are on the top rows, the shorter ones and the sidearms under them. `B.gun` takes the shared scale as its last argument.
- The tool bench with the pegboard is now a gun maintenance bench (`GunBench`, built from parts): a heavy bench against the near wall, a rifle lying on a cleaning mat, a vice, rounds and a cleaning rod, two ammo cans on the shelf, and a warm lamp.

**Three regulars**, the owner's friends in their own avatars:
- Looticus (`roblox_user_4547551380`, id 4547551380) sits on the lounge's east sofa.
- Dune (`Doonamei`, id 56917496) stands in the gym off the south aisle, watching the ring.
- Frisk1636 (`BruhFrisk1636`, id 5028123368) stands on the balcony over the lifts, looking down at the platform.
- Trisangle (`Xxxglowingstarlightx`, id 2321239144) sits on a sofa in the VIP room, across from the door.
- How they work:
  - The builders leave a place for each (`B.npc`, data in `R.NPCS`): an invisible part tagged `HubNPC` with `Who`, `User`, `UserId` and `Pose` ("sit": a Seat on the cushion; "stand": a spot on the floor).
  - `ServerScriptService.Jankfire.HubNPCs` (`src/server/HubNPCs.server.luau`) builds them at server start from the user id (`Players:CreateHumanoidModelFromUserId`). If that fails it uses the saved copy in `ServerStorage.JankfireNPCs.<Who>`.
  - A standing regular is lifted until its lowest part is on the floor: a scaled R15 avatar's legs can be longer than its HipHeight says.
  - They can't be pushed (anchored, or seated on an anchored seat), shot (no queries, no touches) or killed. They play Roblox's own idle or sit animation and show one label: their name.
  - Any builder may add one: tag a part `HubNPC` with those attributes. The training session uses the same script for its owner NPC.

**Bundle holograms** list `Shop.shown(true)`, so a skin set shows once all its skins are in the place, and they draw the hero's weapon skin (`WeaponModels.build(weapon, 3, skin)`).

**`R.check()` gained a ROUTE test**: a body-sized box is swept from between the spawn rows to the front of every pad and onto it.
- To a lift: past the projector and straight out through its opening.
- To an upper pad: to the jump pad on its side, then the throw. The pad's `Pad` velocity is simulated under the place's gravity (78) with the whole body; a wall it meets stops it going sideways and it slides down. The throw must land on the balcony.
- From the landing it walks along the balcony to the doorway, through it, and along the upper walk onto the pad.
- Anything solid in the way, a throw that lands anywhere else, or a waypoint with no floor is a problem. The summary says "walked to N".
- A sight test checks that the doorway shows from where each jump pad lands you.
- New keep-clear zones: the upper walk in front of every upper pad. New leak points: in the second floor and the VIP room.

Now (push 45, place version 448): `R.check()` 46 keep-clear zones, 0 problems, 0 leaks, 288 sight lines, 0 hidden, 56 props, 0 overlaps, 105 lamps (9 with shadows), 12 pads, walked to 12.

**Flicker** (`ZFight`, minY 239.5): 6 visible hits, all under 0.2 sq studs:
- the old `bc_fridge` kit (0.15)
- two 0.06 slivers where the balcony's slab meets its floor at the doorways
- three inside the sawn-off's own kit model, which is smaller now at its true size

**Tested in Play** (place versions 431 and 448, by the builder):
- All four regulars built from their avatars: Looticus and Trisangle seated on their sofas with the sit animation, Dune (R6) on the gym floor, Frisk1636 on the balcony. Frisk's feet sank half a stud in v431; in v448 they are 0.07 off the floor.
- The VIP door's leaves are in `VipDoor`; the test player (VIP by the owner's Studio unlock) showed the door from the lounge and the room inside.
- The shop session tested the door in v437 with its `Vip.luau`: a character that wasn't VIP, put inside the room, was moved out within 1.7 s; a VIP stayed; the owner's dev "lock" moved them out again, and "unlock" made them VIP at once.
- The VIP pack's plinth showed a gold skin turning.
- Photos: `roblox/docs/hub/hub_round3_sheet.jpg` (both floors from the spawn, the hologram at a standing eye, the second floor, the VIP door and room, the gym, the armory and its bench, Looticus).

**Round 3, second pass (push 46, place version 455):**
- **The second floor got the rotunda's structure** (the main session, 16 Nov: the upper hall "reads plain next to the rotunda below it"). No new lamps and no floor marks.
  - Each pad stands in a bay: dark fins between the pads with a light strip on each nose, the bay's own pale back wall, cream guide rails either side of the board as in the lift bays, and a cream lintel across the bay's mouth.
  - The top of each bay's wall is cut at 45 degrees, with a hidden lit strip under the lip.
  - A cream rib runs from each fin across the ceiling to the round room's wall, with two cream beams across: coffers.
  - Along the round room's wall inside the hall: a dark foot and a cream hand rail, broken at each doorway, which has a pale frame on this side too.
- **An upper pad starts a match and brings you home.** Tested with Matches' Studio hook (`ServerStorage.JankMatchTest`, "ghost" with the player on team 1): 3v3_u1 started a match in RooftopV3. The player was in it 5 s later (zone "match") and back in the hub at time-up (zone "hub"), with no live matches left.
- **The VIP door passed both ways**, tested by the shop session in place v453 by walking into it. With VIP locked the character (collision group Default) stopped at the leaves; with VIP unlocked (VipGuest) it walked 18.6 studs into the room.
- **Lights:** the performance session measured them in Play. Lights and shadows cost next to nothing; the 12 fps in training was the old mirror. No light budget, but no more than the current 9 shadow casters. Its ZoneCull (far maps off the client) is in the place, switched off by the workspace attribute `ZoneCull = false` until it has tested teleports.
- `R.check()`: 0 problems, 0 leaks, 288 sight lines with none hidden, 0 overlaps, 105 lamps (9 with shadows), 12 pads, walked to 12. ZFight: the same 6 tiny hits. The fins and rails first shared a bottom face with the dark foot along the wall (14 more hits); their feet now go 0.04 into the floor.
- Photo: `roblox/docs/hub/hub_upper_bays.jpg`.

**Not done / open:**
- A match from an upper pad with two real players has not been played (the Studio hook stands one player in).
- Shadows: the performance session will send a budget (likely 4 shadowed lamps, now 9). Its ZoneCull takes the whole Rotunda out of the client while you are far from it, so the Rotunda must stay `Map.Hub.Rotunda`.
- Map.Hub was not exported to the repo this round: the hub is rebuilt from the builders (`R.build("live")`), which are in git.

## 30. Three more arenas from the web game: Crate, Platform, Bazaar, 17 November 2026 (place version 536)

**The owner (17 Nov 2026), passed on by the main session: "We do need more maps, we technically have really pretty rooftop maps v2 and v3!! We can bring over some of the other ones!!"** The brief was to pick three that suit Rivals-style duels (1v1 to 4v4), port them the Rooftop v3 way (the web's exact boxes, a new chunky kit), put them in the arena rotation, keep them cheap, and do one at a time, the small one first.

- **The picks, from the web layouts** (top-down plans of every map compared, size, sightlines, cover):
  - **Crate** (small, 30 x 30 m, 90 x 90 studs): a toy chest floating on a tower of giant toy blocks in a giant child's playroom. Corner crates, two long crates, the shape sorter in the middle (pads throw you onto its lid), four perches and a gold plate up high for the grapple. A 1v1 / 2v2 arena: `MaxTeam = 3`, so a 4v4 never lands on it.
  - **Platform** (mid, about 70 x 64 m): the oil rig. Main deck, cellar deck under it, the drill floor under the derrick, the living quarters (three floors) and helideck, the pipe rack walkway, separators, cranes, the supply boat below. Attackers start in the galley, defenders under the drill floor (the web's own team spawns).
  - **Bazaar** (bigger, 132 x 132 m): the walled market. The covered hall with its domes and lamp tower, the caravanserai, the dye works and canal, the corner markets, houses you can go into, the two gate plazas the teams start in.
  - Left out: Skyline (huge, long bridges are pure sightlines), Desert (200 m, a canyon splits it, 14,600 boxes), Warehouse (long open yards), Islands, Suburb, Forest (large and open), Backrooms, Dead Mall (zombies layouts).
- **How they are made** (the v3 way, generalised):
  - `node tools/roblox/webmap_dump.mjs <id>` writes `tools/roblox/arenas/<id>.json` from `shared/map.js` itself: boxes, deco, spawns, team spawns, the shaped ground's heightfield.
  - One headless Blender script per map (`tools/roblox/crate_models.py`, `platform_models.py`, `bazaar_models.py`, sharing `arenakit.py`) dresses the boxes and writes the kit `.glb` (one Model upload) and `roblox/studio-tools/<Name>Layout.luau`: the web's boxes x3 as hit boxes (with a material and colour for impacts), pads, spawns, team spawns (att, def and "mid" for a 1v1v1's third side), lights, backdrop.
  - `ServerStorage.PolishBackup.WebArena` builds them: `W.import(name)`, `W.build(name)`, `W.check(name)` (hit boxes vs layout, spawns on floors, team spawn sight lines, pad flights, kit parts that collide), `W.pool("add" | "remove" | "only" | "set", ...)`. Kit asset ids in `W.ASSETS`.
  - Sites: Crate (0, 0, 30000), Platform (0, 0, 42000), Bazaar (0, 0, 54000). Copies for side-by-side matches work (a Crate match ran on its copy at x +7000 with the whole room).
- **The look**: structure, quiet colours, nothing painted on a floor you fight on. Crate is natural wood and cream toys with one muted colour each, a giant playroom with one window (a low sun through it from the north). Platform is steel greys, off-white cabins, one muted safety yellow (rails, columns, cranes); every thin web rail is a chunky round rail on posts. Bazaar is one warm family of plasters and sandstone, muted awnings, one muted turquoise dome; the streets are the web's smooth ground (its heightfield drawn as one surface over the stepped hit boxes).
- **Code hooks** (commit f990910): `Arena.pool(teamSize)` and Matches' `nextArena` respect an arena's `MaxTeam`; Matches spawns a 1v1v1's third side on "mid" team spawns; HubLife lights a match through `HubLook.byArena` (looks `crate`, `platform`, `bazaar`); ZoneCull culls a small arena that says `ZonePiece`; titles come from the arena's `Title` attribute (CRATE, PLATFORM, BAZAAR).
- **The rotation**: `workspace.Map.ArenaPool` = `RooftopV2,RooftopV3,Crate,Platform,Bazaar` (v536). Pads, the Play queue and ranked all pick through `nextArena`.
- **Checks** (`W.check`, v536): every hit box built (Crate 19, Platform 895, Bazaar 4,109), every spawn and team spawn on a floor, no team spawn sees the other team's (Platform and Bazaar 0 of 98 lines open; Crate is a tiny open box, 16 of 32), Crate's pads land on the sorter's lid, no kit part collides or takes shots. Flicker check (ZFight) on Crate: 3 tiny contact spots, fixed in the kit. Duel Play tests on all three (1v1 Crate, 2v2 Platform, 2v2 Bazaar): spawned at the right end, the arena's own light on the client.
- **Cost**: Crate 105 parts, Platform 1,022 + 51 backdrop, Bazaar 4,346 + 83 backdrop (v1 is about 10,000). In a Bazaar match: 60 fps, 3.4 ms render CPU, every other arena put aside by ZoneCull.
- **Two traps met (in memory `roblox-web-arenas`)**:
  - Roblox shrinks a whole uploaded Model until its biggest extent fits 2,048 studs: Crate's 2,536-stud room drew its kit at 81%, Platform's 7,500-stud sea at 27% (hit boxes fine, the look tiny). Kits now stay inside +-1,000 studs (`arenakit.KIT_LIMIT`); anything bigger or farther becomes a backdrop box that WebArena builds as tiled Parts. The Blender log prints `KIT EXTENT`.
  - Studio caps a script's Source at 200,000 characters: the Bazaar layout was 304 KB. Layouts now list hit boxes as numbers with an index into a small `mats` table (152 KB).
- **Second pass (place version 546), after the main session's look at the first photos**:
  - **Spawn facing**: a round could open on a blank wall, because the camera kept its old heading through a respawn. Now Fight sends the spawn's heading with the Spawn remote, and Body turns the client's camera to it. A team spawn can also carry its own heading (attribute `Face`, from the layout's team entries). Crate's spawns face the middle of the lid, and Platform's galley spawns face their door. Checked in Play: a 2v2 on Platform opens facing the galley door with no camera help.
  - **Structure over colour**: Platform's cabins have steel panel ribs every 3.6 studs on both faces, beams under every floor, and a panelled compressor house. Crate's playroom has pilasters every 220 studs, a picture rail and raised panels.
  - **Bazaar's outskirts**: the web's dunes (four flat layers each) are drawn as smooth dunes. The ones at the kit's edge stay layered, in the backdrop.
  - **Sheets**: `roblox/docs/maps/sheet_crate.jpg`, `sheet_platform.jpg`, `sheet_bazaar.jpg`.
- **Not done / not tested**: a real 2-player match on any of them (stand-in ghost matches only), 4v4 on Platform and Bazaar, phones.

## 31. The hub's regulars: purposes, idles, moving about, 17 November 2026 (place version 571)

**The owner's words (17 November 2026), relayed by the main session:**
- "Can they have idle animations? Frisk looks around, Trisangle kicking her feet, Looticus will occasionally stretch and Dune will like breathe so his model looks more lively"
- "Dune is the quests guy, maybe Frisk does one. Maybe Looticus the shop? Idk.. I want to give them purposes"
- "Can Trisangle sometimes stand up and then sit back down on other seats? Maybe Looticus has a teleport ability but will always be in that room, Dune can walk around the gym and Frisk can move to different spots on the railing?"

**Purposes:** each regular has one prompt in one style: E, no hold, 8 studs, no line of sight, ObjectText = their name. Their label reads "NAME · PURPOSE".
- Dune · QUESTS: `QuestsOpen = true`, which the quests session's QuestClient opens on. An amber dot follows his name for a player whose `QuestNews` is true (`HubNPCs.client`). Tested by the quests session in place v563.
- Looticus · SHOP: `ShopOpen = "tab:containers"` (ShopClient).
- Frisk1636 · RANKED: `RankedBoard = "duels"`, which opens the ranked leaderboard (the play-party-ranked session, live in v551).
- Trisangle · DAILY REWARD: the shop session's `VipDailyPrompt` (its VipDaily module; her place carries `VipDaily = true`).
- Prompts ride on the regular's body: `HubNPCs` moves any prompt on their place onto an Attachment `PromptAt` on their root, including one another script adds later.

**Idles** come from Studio's prompt-to-animation tool (the owner's rule):
- Dune breathing (127219539482270), Frisk looking around (98265160247529), Trisangle kicking her feet (109986198247610).
- Looticus a calm seated idle (81632050089862), with a stretch every 15 to 30 s (71884246597796).
- One relaxed walk (135619112265836) for the three who walk.
- The seated clips lowered the hips 0.9 to 1.9 studs, which would have sunk them into the sofas. They were re-uploaded as Animation assets with the hips levelled, as Roblox's own sit has them. The walk call timed out at the bridge twice, so its clip was uploaded the same way.
- A generated clip loops with no pop: two tracks of it, the next fading in as the last runs out.
- Every regular is built as R15 from their avatar's description (Dune's avatar is R6), and the saved copies in `ServerStorage.JankfireNPCs` are R15 too.

**Moving about:** bodies are always anchored and moved in one Heartbeat loop. They walk only between points the builders lay (`B.npcPoint`, tag `NPCPoint`), clear of walls and furniture, and wait while a player stands in their way.
- Trisangle ("seats"): every 45 to 90 s she walks to another end of the two VIP sofas, by the aisle beside the table and across by the door.
- Looticus ("teleport"): every 60 to 120 s, a soft puff and he is on another sofa seat or standing by the arcade or the fridge.
- Dune ("loop"): walks round the gym ring, pausing at the weights, behind the ring, at the bags and by the door.
- Frisk1636 ("pingpong"): moves between four spots on the balcony rail.

**Tested in Play** (place version 571, by the builder): all four built, anchored, with their prompts on their bodies (the shop's VipDailyPrompt on Trisangle's).
- Within 13 s Trisangle had walked to another seat and sat, Frisk had moved along the rail, Dune was walking his loop, and Looticus had puffed to a standing spot.
- The seated clips keep them on the cushions.
- Photos: `roblox/docs/hub/hub_regulars_sheet.jpg`.

**Not done:** Looticus's and Frisk's prompts were not pressed in Play here (Dune's was, by the quests session).

## 32. The regulars get up and sit down, and move less stiffly; motion capture, 17 November 2026 (place versions 616 to 623)

The owner, on the regulars: "When they stand make sure they don't stand in their seats like clipped into it! Idk how you would do it but make them leaving their seat natural?", then "also the animations seem really stiff..", then "When you generate generate 4 at a time!". The owner then approved Mixamo motion capture for them (the FBX files stay in the vault, `Assets\mixamo-17nov`, never in git).

- **Getting up and sitting down** (HubNPCs.server):
  - A seated regular stands up onto the seat's `Stand` point, `R.NPC_STAND` (1.9) in front of it. The sofas reach 1.1 in front of their seat points and a body is 1.2 deep.
  - The body follows the hips' path from the motion-capture clip (the RISE / SETTLE tenths): a lean first, then forward over the feet and up.
  - They step out to the seat's `Approach` before turning, walk the aisles, stop on the next seat's `Stand` point, turn their back to it, and sit (down and back together).
  - Looticus stands up before he puffs away, lands standing in front of the next seat, then sits.
- **The clips play on each player's own screen** (HubNPCs.client).
  - The server only moves the bodies and sets attributes: Phase / PhaseAt / PhaseLen, WalkRate, ExtraAt, and the clip ids.
  - Why: a clip the server plays is lost on a screen once ZoneCull takes the Rotunda out of that player's world and brings it back (found by the training session).
  - The client stops everything when the body leaves workspace and re-enters the current phase when it is back.
- **Less stiff:**
  - Every clip change fades over 0.3 to 0.5 s.
  - Walks ease in and brake to a stop. They turn on the spot before walking off. The walk is each avatar's own (Trisangle has a walk pack; the others use Roblox's default), sped to their real speed by Roblox Animate's rule: full speed at 6.4 studs a second at HipHeight 2.
  - Each idle runs at its own speed (0.9 to 1.1) from its own start point.
  - One-shots play while they keep still: `Extra` (a seated regular's while seated), `ExtraStand` (a seated regular's while standing).
  - A living layer on the client: breathing in the waist, the head drifting between things to look at (now and then at you), shoulders swaying. It writes to the joints' C0, or to an AnimationConstraint's Attachment0.
- **Roblox's newer avatar joints:** the regulars' bodies (and the blank R15 rig) have `AnimationConstraint` joints, not Motor6Ds. Anything that poses joints by hand must handle both kinds.
- **The clips** (`MX` in HubRotunda):
  - All nine Mixamo clips were retargeted to R15 with my own Blender script. Each part takes its bone's world turn away from the T-pose rest, laid on R15's T-pose. A direction check matched every limb to within 4° (the spine within 7°).
  - They were uploaded as Animations. Seated loops have their hips levelled about the clip's middle. The transitions have no hips travel; their path became the server's tenths.
  - They were compared side by side with the live clips and the generated takes (four standing up, two sitting down; the generator lost two sit-down takes): `docs/hub/hub_regulars_takes.jpg`. The mocap was kept in every slot.
  - Two of the four generated stand-ups had a broken pose mid-way. The old generated seated stretch looked contorted, so Looticus's seated one-shot is now the mocap glance, and his standing one-shot is the mocap stretch.
- **R.check sweeps a body** (`R.NPC_BODY`: 5.2 tall, 1.2 deep, each regular's own width across their hands: Looticus 4, Dune 3.9, Trisangle 3.4, Frisk 3.2; its feet 0.35 over the floor):
  - It stands one on every point they stop at and sweeps it every 0.5 stud along every walk, the same walks HubNPCs uses.
  - It counts what can be seen. The invisible collision boxes round the kit (a sofa's, a rail's) are bigger than the things.
  - Clean since push 56 (place version 623): 14 ways, 636 body boxes, 0 problems.
  - To get there, an in-Studio probe tried candidate points:
    - Looticus's standing spots moved onto the lower floor in front of the arcade and the fridge.
    - Frisk walks 3 out from the rail, with a point between each two stops so he follows the curve.
    - Dune walks round three sides of the ring and back. On the door's side, the ring's corners and the benches leave less room than he is wide.
- **Checked in Play:**
  - Trisangle's whole seat change, slowed to a fifth (v616): `docs/hub/hub_trisangle_seat_change.jpg`.
  - The regulars' panels and frames (v620 to v623): `docs/hub/hub_regulars_panels.jpg`.
  - Both prompts are shown to a player 4 studs away (ProximityPromptService.PromptShown fired for ShopPrompt and RankedPrompt). Both are enabled, with range 8 and no line of sight needed.
  - The panels open from the prompts' own values: the shop on CONTAINERS (`ShopTest`), the leaderboard on DUELS (`PlayTest board:duels`).
- **Not done or not checkable here:**
  - The MCP cannot fire a prompt. `InputHoldBegin` and `user_keyboard_input` E both do nothing while Studio's window is not in front (rule 11 keeps it so). The press itself is the only step not seen.
  - The frame strips have 2 to 4 frames each, not 6. Captures run about 5 s apart, and in the last turn the viewport drew blank white (the window not drawn).

- **Test hook** `ServerStorage.JankNPCTest`:
  - `:Invoke("move", who, toIndex?, speed?)` makes that regular move now (0.2 = a fifth of normal speed, for photos).
  - `:Invoke("where", who)` returns their point, phase and position.

## 33. The hub/training gate on one kit, and queue pads that glow, 17 November 2026 (place versions 641 to 676)

The owner: "can the laser fence be on both side of the hub and same with the garage door because its weird to have the grid on one side and a garage door on the other", then "the garage door should be behind the laser, hello??", then "I like the old black entrances for doors idk if i like the gold..". On the pads: "can we try removing the circles on the pads and then make them glow?", then "pads should glow when you step on them!".

- **One gate kit for both sides** (`roblox/studio-tools/GateKit.luau`, `K.build(F, parent, { door, lasers })`):
  - The red laser fence is at the opening's face (Near 17). The roll-up garage door is just behind it (Near 13). Walking up, the lasers click off first, then the door rolls up. TrainingDoors.client does both on every screen.
  - The kit's hb_portal frame is in amber trim on slate (`K.FRAME`), with an amber light bar over the head and a warm lamp out in front (`K.LAMP`).
  - The hub's armory gate (HubRotundaRooms) and the training side's gate home (TrainingV2, the training session's) are both built with it.
- **The open doorway is black.** The dark plate behind the door is `GateBack`, `K.COL.back` "2b2d33".
  - The amber portal tried at v656 is gone: the swirl, the glow and the warm spill, along with GatePortal.client (676).
  - The owner preferred the old black opening.
- **Queue pads glow** (HubRotunda's `B.pad`, `roblox/src/client/PadGlow.client.luau`):
  - There are no circles. Each side has a thin neon `Glow` in its team's colour over a darker plate, with a soft PointLight in it.
  - An open side breathes quietly (see-through 0.78, light 0.12; v664).
  - When someone steps on a side, it flares (a flash toward white and a burst of light for 0.5 s), then holds clearly bright while they stay.
  - A side counts as taken when one of its `Slot` specks (buried in the plate) is shown.
- **Photos:**
  - `docs/hub/hub_gate_both_sides.jpg` (v649).
  - `docs/hub/hub_gate_and_pads_v656.jpg` (the order fixed; the amber portal; the pad flare).
  - `docs/hub/hub_queue_pads_open_dim_v664.jpg` (the open sides dimmer, from the spawn).
  - `docs/hub/hub_gate_black_676.jpg` (the open doorway black again).

## 34. THE GUT: a new arena round the heart tower, with a subway and the train boss passing by, 17 November 2026 (place versions 694 to 700)

The owner: "Can we have a map based on the gut district? We have this awesome heart tower build it would be a shame to not use it!! Maybe it can have a lower part that's a subway and the big train boss can pass by as an Easter egg".

**Content rules first.** The web Gut is body horror (flesh, organs, a bone stair with skulls, a train full of bodies), and the account already has one warning. So this keeps the district's feel and silhouettes and nothing else.
- Soft pinks, corals and creams. Rounded bubbly buildings with round windows. Smooth pale arches over the lanes (the rib arches as architecture). A soft covered tube street. A warm rose sky with a pink haze.
- No flesh, organs, blood, teeth, bone, bodies or eyes. No text, no logos, no coloured marks on any floor you fight on.

**The heart tower** (`tools/roblox/gut_heart.py`, numbers in `gut_heart_dims.py`): the web model's silhouette, made a clean sculpture.
- An ivory column with a pale spiral stair round it, with a rail and balusters. A lattice of rods.
- Four smooth legs holding a walkway balcony 21 studs up. You can climb to the balcony; above a gate the stair is look only.
- A rose-gold jewel-setting cradle holds the heart.
- Three takes on the heart (`docs/maps/gut_heart_takes.jpg`, `gut_takes.py`):
  - A candy: a puffy glossy coral heart with cream piping.
  - B gem: see-through faceted ruby glass with a neon heart inside.
  - C lantern: glowing seams and a rose-gold hoop.
- All three are in the kit (`gu_heartA/B/C`); the build keeps one (attribute `Heart`, A for now).
- `GutLife.client` makes it beat on one shared clock (0.72 beats a second: a lub and a dub, a 6% swell, its light flares) and turn once every 48 s.

**The layout** (`tools/roblox/gut_layout.py`; plan `docs/maps/gut_layout_plan.jpg`, drawn from the hit boxes by `gut_plan.py`). 300 x 208 studs, mirror-symmetric, site (0, 0, 66000).
- **Halls:** attackers spawn in the west hall, defenders in the east. Each hall has two doors with screens in front, so no line runs hall to hall.
- **Three lanes:** the covered Tube (north), the Approach (middle, a kiosk dome on the centre line), the open Avenue (south). Blocks with offset alleys split them.
- **The Plaza** holds the tower, with a dome pavilion in the north court and a gazebo in the south court.
- **The subway** at y -30 is one long platform under the south half. There are stairs up into each hall and two up to the Plaza.
- Everything that is not walkable is solid to y 150 (no roofs to stand on), with a lid over the arena.
- **Turned hit boxes:** WebArena and arenakit now take turned hit boxes (`solidR`: the spiral stair, the balcony, round posts). The flag "c" marks a box that stops you but takes no shots (rails).

**The train** (the Easter egg):
- **Its look:** the boss's ☺ station-sign mask: an off-white enamel disc, two dark oval eyes, a smile. Its hauling arms are plain dark cables. Behind it, three commuter wagons with dark windows.
- **Where it runs:** on its own track behind a full-height glass screen. It never collides or takes shots, so it can never decide a fight.
- **When:** `GutTrain.server` picks the times, first 12 to 30 s into a match, then every 58 to 103 s. It writes `TrainAt` and `TrainDir` on the arena (and on copies).
- **Each run on screen** (`GutLife.client`): 6 s of warning (the signals and the lamps along the glass flash red and amber, the lights flicker, a rumble grows), then it passes at 120 studs a second.
- **Sounds:** recordings, set as the arena's attributes `RumbleSound` (ProSoundEffects "Hollow Rumble 2", 9112795571) and `TrainSound` (5870203641, a subway express passing).
- **Its light:** `HubLook.looks.gut` with its own sky. HubLook can now give a look its own Sky (`H.ownSky`): `Lighting.SkyParked.GutSky`, three plain gradient faces from `gut_sky.py`. The first, redder take flooded the arena with red; the second is a dusty rose. The sun is low from the south (latitude 92, 21 degrees up), across the halls' line.

**Checks** (place version 696):
- `W.check("Gut")`: 639 hit boxes built, every spawn and team spawn on a floor, 0 of 128 team spawn lines open (the door screens and one spawn moved), no kit part solid.
- ZFight: one 20 sq stud contact on the platform's edge, fixed in the kit.
- In Play:
  - The train run measured on the client: it sets off on time, passes the station when `TrainAt` says, and parks. The signals flash, the lamps flicker, and the heart turns and swells.
  - A real 1v1 started on the Gut: the attacker spawned in the west hall facing east, and the client switched to GutSky and the gut light.
- **Cost:** 271k triangles in 105 meshes and 24 models; 822 parts with the hit boxes.
- **Photos:** `docs/maps/gut_heart_takes.jpg`, `gut_layout_plan.jpg`, `gut_studio_v696.jpg`.

**The heart, anatomical (place version 699).** After the first sheet the owner said "We can do an actual heart it's not like Roblox will say something against". So the Valentine takes are out of direction, and the heart is now a real one in the kit's clean style (`tools/roblox/gut_heart_anat.py`).
- **What it has:** the ventricles' cone, the atria and auricles, the aortic arch with three branches, the pulmonary trunk, the venae cavae, coronary arteries (pink-red) and veins (blue) in their grooves. Flat deep reds and pinks; no blood, drips or wet look.
- **Three takes** (`docs/maps/gut_heart_anatomical.jpg`):
  - A chunky: the main vessels only.
  - B vessels: the full coronary tree, forked branches, the pulmonary veins.
  - C grand: closest to the web model, with the arch and the vena cava as ropes and feelers.
- **Which is in:** B (`Heart` = "B"). The kit holds A, B, C and V (the first candy heart); the install keeps one.
- **The beat:** GutLife flushes the heart's colours a little brighter on each beat, as well as the swell and the light. The flush is checked in Studio but not seen in Play yet; the swell and turn were measured at v695.
- **Photo:** `docs/maps/gut_heart_anatomical_v699.jpg`.
- **Bigger, and firmer contrast (place version 700).** Main: "Make it bigger ... so it dominates the skyline from every lane", and keep the pink from washing out contrast.
  - The heart is 1.7 times the sheet's size, 64 x 116 studs, its top about 240 up. It rests on its apex (y 118) on the tower's axis, in a cradle 1.35 times bigger. It beats and turns round that point (the arena's `HeartPivotY`).
  - The windows' dark glass is deeper (3e2530) as the contrast anchors.
  - The gut look has less haze (Density 0.3, Haze 1.5) and more contrast (0.17).
  - Photo: `docs/maps/gut_big_heart_v700.jpg`.
- The district, the stair (no skulls) and the train (its mask only) stay as they were.

**The rotation:** `ArenaPool` = `RooftopV2,RooftopV3,Crate,Platform,Bazaar,Gut`.

**Not done / not tested:**
- A real 2-player match.
- The train sound's loudness in a live run (the passing sound is a Creator Store recording, not measured).
- Phones.
- The owner's pick of heart (A is in for now).

## 35. Three v2 maps: Bazaar v2, Desert v2, Suburb v2, each its own shape and its own tricks, 17 November 2026 (place versions 702 to 706)

The owner: "can you create an entirely new bazar desert, suburb, make the shape unique, give it like usnique properties, maybe bazar has an upper area or something", then "theyre all v2 versions".

Three new hand-made arenas on the Gut's pipeline. Each has:
- `tools/roblox/<map>2_layout.py`: plain Python with the hit boxes, turned boxes, pads, water and spawns.
- `<map>2_models.py`: a headless Blender kit that writes `roblox/studio-tools/<Name>V2Layout.luau`.
- A plan drawn from its boxes by the new generic `tools/roblox/arena_plan.py`, and offline spawn and sight-line checks (`tools/roblox/arena_check.py`).

Bazaar v2 was built here. Desert v2 and Suburb v2 were built by two parallel helpers that shared this session's context, then reviewed and installed here.

- **BAZAAR: ROOFTOPS** (`BazaarV2`, site z 78000; `docs/maps/bazaar2_layout_plan.jpg`)
  - **Shape:** an oval walled desert town, 330 x 250, round a square oasis pool, mirror-symmetric (gate courtyards west and east).
  - **The upper area:** every block's flat roof (y 18) is one network, joined by plank bridges over the streets. It has parapets and roof clutter (stair-houses, water tanks, cloth screens) for cover. You get up by outside stairs and by canvas springboards (pads) that throw you onto the roofs.
  - **Street level:** a covered souk with lanterns runs under the north roofs into a domed market hall you walk through (a raised fountain breaks the souk-to-souk line). The open spice market is south.
  - **The plaza:** the pool is swimmable, with a domed well house on its island that blocks the street-to-street line.
  - **The look:** whitewashed plaster, sand flagstones, beam ends, arched dark windows. Palms, clay pots, market stalls with cloth awnings. The muted teal (hall dome, pool tiles, springboards) is the one accent.
  - **Cost:** 190k triangles.
- **DESERT: CANYON** (`DesertV2`, site z 90000; `docs/maps/desert2_layout_plan.jpg`)
  - **Shape:** a W-shaped canyon between layered mesas. Each camp leads through a corridor, up a north leg, along under the north mesa and down a south leg into a shared basin. Every bend breaks the long lines.
  - **Mesa tops** (y 26) have rock spires, ruins and lips, reached by 10 stairs carved into the walls.
  - **The rope bridge** spans the basin from the north mesa's tongue to the south mesa.
  - **The sandstorm** (unique):
    - `DesertStorm.server` writes `StormAt` and `StormLen` (first 20-40 s in, then every 70-120 s, 18 s each).
    - `DesertStorm.client` eases Lighting's Atmosphere to a thick ochre wall and back, blows sand past the camera, and plays the arena's `WindSound` (81404060588532, "Howling Wind").
    - It stops at once if your match or arena changes.
  - **Cost:** 113k triangles.
- **SUBURB: CUL-DE-SAC** (`SuburbV2`, site z 102000; `docs/maps/suburb2_layout_plan.jpg`)
  - **Shape:** a dumbbell: a round cul-de-sac at each end (the spawns, behind the planted island and parked cars), the street between with a hedged village green in the middle.
  - **Houses you go through:** 8 of them, with front and back doors, a stair, and upstairs windows over the street and yards.
  - **Garage roofs** (y 11) lead in through an upstairs window.
  - **North yards:** two swimmable pools, a hot tub, a tree house (platform at 14).
  - **South yards:** trampolines (pads onto the garage roofs and the play fort), sheds, barbecues, a play fort with a slide.
  - **Cost:** 93k triangles.
- **Shared code:**
  - `HubLook.looks.bazaar2 / desert2 / suburb2`, each with a sun measured at 32-37 degrees from the south, across the teams' line.
  - `W.ASSETS` BazaarV2 131330198115223, DesertV2 127676315267642, SuburbV2 127392071390257.
  - **The rotation:** `ArenaPool` = `RooftopV2,RooftopV3,Crate,Platform,Bazaar,Gut,BazaarV2,DesertV2,SuburbV2`. The old Bazaar (the web port) stays in; removing it is the owner's call.
- **Checks** (`W.check` in Studio):
  - Every hit box built (480, 401, 527), every spawn and team spawn on a floor, 0 of 128 team spawn lines open on each map.
  - All pads land where they should (8 Bazaar springboards on roofs; 4 Suburb trampolines on garage roofs and the fort).
  - ZFight: 1 contact of 0.1 sq studs on the Bazaar, 0 on the others.
  - In Play, a real 1v1 started on each map, spawning the attacker at the west end, and the pools filled with water.
  - The desert storm starts on the client (haze up, sand blowing), but a one-player test can't hold a match long enough to watch it whole.
- **Photo:** `docs/maps/v2_maps_studio_v705.jpg`.
- **The cars came off the Suburb (place version 706).** The owner said "remove the cars on suburb". Each car (5.4 tall) became cover of the same footprint, so the lanes and lines didn't change:
  - in front of each cul-de-sac's spawns, a brick garden wall with a clipped hedge;
  - at the kerbs, a brick planter with a hedge, a mailbox cluster and two wheelie bins.
  - `W.check` still finds 539/539 hit boxes, 0 of 128 spawn lines open, the pads landing right, and ZFight 0.
  - Before/after photos: `docs/maps/suburb2_cars_removed_v706.jpg`.
- **Suburb v2 switched off until it's finished (17 Nov, commit 086915f).** The owner said "suburb can you take it out until its finished".
  - **The switch:** any arena's own attribute `Enabled`. When it is false, `Arena.pool` (`src/shared/Arena.luau`) skips the arena, so no pad, queue, mode, ranked game, party pick or map vote can land on it. `Arena.enabled(name)` asks the same question.
  - **Suburb's setting:** `workspace.Map.SuburbV2` has `Enabled = false`. It stays built and stays in `ArenaPool`.
  - **To bring it back:** `workspace.Map.SuburbV2:SetAttribute("Enabled", true)` (or clear the attribute), then save.
  - **Checked:**
    - Edit: Suburb is out of the pool for every team size, 0 picks in 2,000 draws, and flipping the switch puts it back.
    - Play: 21 pad picks landed on all 8 other arenas, never on Suburb.
  - The map selector and vote (Party.luau) read `Arena.pool`, so they follow the switch.
- **Not done / not tested:** real 2-player matches, a whole storm in a live match, phones.

## 36. The wall box: no sky lid, walls pushed out, a hologram grid where you hook them, 18 November 2026 (place versions 729, 730, 735 and 736)

The owner: "you can keep wall box but can you remove sky box? that way we can grapple properly? if you get close to wall box, should like a small like grid appear where you grapple? like almost a hologram shield type thing but not the entire box just in the section youre grappling to? can you also push back the wall box a bit on all maps to make them feel larger and give more swingability?"

- **What each arena's boundary was** (all in `workspace.Map`'s ArenaPool, plus v1):
  - **Rooftop v1, v2, v3, Platform:** no wall box and no lid. The roof or rig ends and you fall to the arena's KillY.
  - **Crate:** no wall box and no lid: the toy room's walls are look only; off the chest you fall.
  - **Bazaar (the web port):** no wall box and no lid. Its visible city wall (to 42) is solid; past it the desert hit boxes run out to 900.
  - **The Gut, Bazaar v2, Desert v2, Suburb v2** (the hand-made ones): invisible walls 10 thick round the edge, solid from under the floor to y 150 (the layouts' `LID`), a 5-thick lid on top, and everything not walkable solid up to the lid. Desert: the outer cliffs solid to the lid from the cliff lines out. Bazaar v2: 48 turned boxes on the town's ellipse. Suburb: the back and end hedges solid to the lid. All hit boxes take shots and grapples (CanQuery on), so a rope aimed at the sky hooked the invisible lid.
- **The rule, the same on all four walled arenas** (`tools/roblox/wallbox.py`):
  - **No lid.** A rope aimed at the sky finds nothing ("TOO FAR"), a rope over the old lid height reaches what's really there.
  - **The sky line** instead (`SkyY`, local 132): over it nothing lifts you higher; the climb eases off and stops 12 studs over (Move.client, any rope, pad or launch). So the old solid-to-the-lid columns, their tops at 150, can't be stood on. Measured in Play: a rope to the wall at y 230 topped out at 141.7. **Out of bounds** 60 over the line (Main.server kills, "OUT OF BOUNDS", only over the arena's site): only a client that skips Move.client gets there.
  - **The walls go 30 studs further out**, up to 260 (Mat `bound`): Gut 180 x 134, Desert 202 x 152, Bazaar v2 an ellipse 195 x 155, Suburb 206 x 142.
  - **The step:** from the old edge out to the new walls, solid up to the top of the scenery that stood right behind the old walls (Gut's edge buildings 60, Desert's outer cliffs 90, Bazaar v2's town wall 34, Suburb's hedges and the houses past them 32). Nothing walks into that scenery; above it is open air to swing in. Its top is a ledge (Mat `ledge`): land on it and you slide back in toward the middle (30 along, 18 up a hop; Move.client). Tested: dropped on the Desert's ledge, the body hopped inward off the cliff line onto the mesa.
  - The inner solid-to-the-lid columns (the Gut's blocks and halls, Bazaar v2's dead space, the desert spires, Suburb's houses) stay as they were: solid to 150, under the sky line out of reach.
  - Sites, kit limits: no kit changed (the kits never read the wall box), every hit box is within 216 of its origin.
- **The grid patch** (`src/client/WallGrid.client.luau`): a round hex grid 13 studs across in the game's hologram ice-blue (176, 226, 242), soft toward its rim, no text. It shows where your rope bites the wall box (a ring runs out from the bite; a far bite is drawn bigger, up to 30), where you come within 10 studs of it, and where a bullet hits it. On the step only above the scenery behind it (`EdgeSeen`). It fades out 0.6 s after you let go or leave. Four patches built once (a part, a SurfaceGui with the lines in a CanvasGroup), then only moved and faded; the near search is 9 rays ten times a second, only in a walled arena.
- **Bullets hit the wall box** on purpose: the walls must take ropes, and they are the same CanQuery. Fx.impact asks WallGrid (`WallGridHit`): on the wall box no chips fly off thin air, the grid flashes where the bullet stopped.
- **How it's wired:**
  - Layouts: each `<map>_layout.py` keeps SOLID and ROT as they were (the kits dress from them) and adds `HIT_SOLID`, `HIT_ROT`, `WALLBOX`; `<map>_models.py` writes those into `<Name>Layout.luau` (`skyY`, `edgeTop`, `edgeSeen`). `arena_plan.py`, `arena_check.py` and `gut_plan.py` read the hit lists.
  - `WebArena`: the arena's attributes `SkyY`, `EdgeTop`, `EdgeSeen` (world y); **`W.solid(name)` rebuilds just the hit boxes** (the kit, the lights and hand-set attributes like the Gut's heart and Suburb's Enabled stay); `W.check` counts extra boxes and reports the wall box.
  - `Main.server` puts `SkyY` and `ArenaAt` (your site's middle, a copy's own) on you twice a second while your `Arena` is a walled one. `Move.client` reads them; it also writes `HookAt` (where your rope bites) for WallGrid.
  - `tools/roblox/wallbox_plan.py <layout> <out.jpg>` draws the before/after.
- **Checks:** regenerating the four layouts before the change gave the committed files byte for byte. After: `W.check` 0 missing, 0 extra, no lid, every spawn on a floor, 0 of 128 team spawn lines open, pads landing as before; `arena_check.py` 0 problems on all four. ZFight reads visible parts only and nothing visible changed. The anti-cheat's checks don't involve a lid: on a rope you're "bound" (no fly checks), the sky line only takes upward speed away (a fall faster than gravity is never a fly or hover verdict), and the ledge's hop (18 up) is under a jump. With StudioOn it gave no verdicts for the teleport and the first rope; its state after the climb to the sky line wasn't read back.
- **Ray-blind over the roofs** (the main session's call, 18 Nov: "a rope or a bullet stopping in thin air over a roof reads as a bug, and passing through is what players expect"; `tools/roblox/roofs.py`). Every inner column that went to the old lid (the Gut's blocks, halls, Tube, kiosks, pavilion and gazebo; Bazaar v2's dead space; the desert spires; Suburb's houses) is measured against its own kit: a grid of rays every 2 studs down onto the kit's meshes in Blender (`<map>_models.py`, before it writes the layout). It becomes up to three layers that take ropes and shots, wrapping the real roof (the footprint to the eaves; the part above to the middle of what's there; the top: domes, lanterns, ridges), and one box from the eaves to 150 that stops bodies but takes nothing (flag "c"). So nobody walks over a building, but a rope or a bullet just over a roof goes on to whatever is really behind it. Measured eaves: Gut halls 34, blocks 27-33, kiosks 11, pavilion 15, gazebo 18; Bazaar v2 house backs 22-26; desert spires 33-36; Suburb houses 26-27. The wall box's own walls and step are left whole (bullets still stop there, with the grid flash).
  - **How "stops bodies, not rays" works:** CanQuery off does nothing on a part that collides (Roblox still lets rays hit it; found in the test). So WebArena puts every flag-"c" part into the collision group **`JFRayBlind`**, which doesn't collide with `Default` (every ray, rope and bullet is cast in Default) but does with the players' groups. Main.server sets the group up at run time too. For that, characters must never be in Default: **HubVip now puts non-VIP characters in `JFPlayers`** (the Shredder's group for a body) instead of Default; VIPs stay in `VipGuest`.
  - This also makes the Gut's rails (291, flag "c" since v696, "rails you can shoot through") really let shots and ropes through, as their layout meant; before, they stopped both.
  - Checked: `W.check` 0 missing / 0 extra on all four (Gut 726, Bazaar v2 577, Desert v2 420, Suburb v2 590 hit boxes), spawns on floors, 0 of 128 lines open, pads land. In Play (version 735): a box in the player's group rests on a column at y 151, a Default one falls through it; a rope from the Approach over the Gut's north block bit the outer wall at (-73, 124, -134), the server drew its rope to the same point and the grid showed there. Photo (place version 736): `docs/maps/wallbox_rope_over_block_v736.jpg`. That shot showed a far patch (195 studs) drawn too thin to read against the sky, so a far patch's lines now thicken with distance (WallGrid, once per hook, up to 10 px on its canvas).
- **Photos:** `docs/maps/wallbox_play_v730.jpg` (the grid on the Gut, Desert and Bazaar v2 walls, the overhead rope through where the lid was), `docs/maps/wallbox_plan_<map>.jpg` (before and after, solid at swing height, with the heights).
- **Not done / not sure:**
  - Hooking from a standstill on flat ground doesn't lift you until you jump (it was like that before).
  - The test shots have the hub's sky: the test body was put in the arenas outside a real match.
  - Not tested: a real 2-player match on each map, phones.

## 37. Grapple onto people, 18 November 2026 (place version 740)

The owner: "can you make it so you can grapple onto people". Ported from the web game (`public/js/player.js`: `tryHook`, `hookPoint`, `hookStep`, the person branch of `ballHookStep`).

- **The hook bites people.** The hook's ray already stops at whichever is nearer, the map or a body; now, when what it hit belongs to a living player or a training dummy (attribute `Dummy`), the rope ties onto that body instead of the point.
- **The rope follows them:** tied 1 stud over their root (their chest, `Config.hook.bodyUp`), on your own client (`Move.client`: the hook point follows them every step) and on the server's rope everyone sees (`Main.server`: its end is an Attachment in their root). The skin's head and tie follow too (`GrappleLook`: the bite is read again each frame). No max length: the classic rope only ever shortens, as on the web.
- **It reels you in** at the rope's full pull and **lets go `Config.hook.bodyLet` off them** (the web's 3.2 m = 9.6 studs; the brief said "about 3.2 studs", but the web's units are metres). Your momentum carries you into them.
- **It drops** when they die, respawn or leave, or once you've lost sight of them for `Config.hook.bodyBlind` (0.4 s, the client; the server's say-so is 0.8 s, for lag). No ropes through walls.
- **The server checks it** (`HookCheck.body`): a living Fighter (a player or a dummy), not you, in range to their chest with the usual slack, and seen from your head now or a moment ago (`Fight.sees`, the same lag allowance as shots). It costs a charge like any hook (`HookChargeServer`, ranked included), and the same rate limit applies.
- **Kill credit:** an enemy hooked is tagged like a knock (`Rules.tagged`, `wid = "grapple"`). A fall or a hazard within the game's 10 s tag window is the hooker's kill, shown "via" Grapple (a `slot = "none"` naming entry in `Weapons.list`, like the parry and the Shredder). A teammate, or anyone outside a live match, is never tagged (`Fight.allow`).
- **No text.** The sound and the rope skin are the usual ones.
- **Anti-cheat:** the server's rope is still `Rope_<id>` in Terrain, so the hooker counts as on a rope (no fly checks, a rope's throw allowed). A clean reel into a dummy raised no verdict with `StudioOn`.
- **Tested in solo Play** (training dummies as stand-ins):
  - the walking dummy hooked: the rope's end followed it within 1.5 studs (the skin's tie offset) while it walked; the server's rope was tied to its root;
  - reel-in: from 22.5 studs the rope let go by itself and momentum carried the hooker to 1.3 studs from it;
  - killed while hooked: the server's rope was gone within 0.05 s, the client's too;
  - a hooked dummy dropped below the fall line: the kill came back as `void`, `via = grapple`, credited to the hooker;
  - a wall hook: unchanged (a point, `HookAt` set, the rope's end in Terrain).
  - Not tested: two real players (a solo test can't). Photo: `docs/grapples/grapple_onto_people_v740.jpg`.

## 38. Hub v3: the Rotunda, roomier, 18 November 2026 (place version 743)

The owner: "can you do hub v3? its the current one just more spacious one of my friends said it felt too cramped".

- **One scale rule over the finished build** (`studio-tools/HubRotunda.luau`, `R.V3`, `R.applyWarp`): the same builder and the same contents, then the whole build warped before it goes into the place.
  - **The plan:** every place and every footprint is 1.35 times as far from the round room's middle.
  - **The heights:** a map of heights over the floor, `R.V3.H`. The bands people use keep their size (the ground floor up to 9.5, the second floor's first 9.5), and only the air over them grows.
- **Sizes (studs), Rotunda -> v3:**
  - round room 56 -> 75.6 across; the walk round the platform 14.6 -> 19.7; halls 10 -> 13.5 wide;
  - the middle to the lift decks 43.8 -> 59; lift decks 16 -> 21.6 wide;
  - lounge 28 x 22 -> 37.8 x 29.7; VIP 22 x 18 -> 29.7 x 24.3; gym 40 x 34 -> 54 x 45.9; armory 26 x 26 -> 35.1 x 35.1;
  - balcony and second floor 14 -> 18 up; wall top 27.5 -> 35; dome top 41 -> 53.
  - Plan: `docs/hub/hub_v3_plan.jpg`.
- **What keeps its size** (`R.WARP_MODE`):
  - **stretch** (wider, height by the map): structural kit and the jump pads.
  - **seat:** sofas, armchairs and benches get longer, not deeper or taller, so people sit as before.
  - **uniform:** planters grow 1.35x.
  - **rigid** (the default): props and display guns keep their size and move with their places.
  - The regulars' places and points, the spawn and arrival markers and the lamp spots just move; lamps reach 1.35x as far.
- **The world points held in attributes move too:** VIP `Out`/`Door`, the regulars' `Approach`/`Aisle`/`Stand`, the gate's `Center`/`Top`/`Lift` and each slat's `Shut`, and the VIP leaves' `Slide`.
  - The holograms' `Radius`/`Height`/`Base` follow the drums they fill.
  - Each jump pad's throw (`Pad`) is worked out again: as high over the new balcony and as far out in the new plan.
- **Switches:**
  - `R.VERSION = 3`: `R.build("live")` makes v3.
  - `R.switch("rotunda")` brings back the Rotunda exactly as it was (the spare, like the bowling centre); `R.switch("v3")` returns to v3.
  - The folder is still `Map.Hub.Rotunda` (ZoneCull, HubNPCs and HubVip find it there), with attribute `Version = 3`.
- **`R.check` uses the same warp** for its own places (walk zones, leak points, the route's waypoints, camera views).
  - While building v3 it found a flaw the Rotunda already had: a banner hung in front of each of the four doorways into the second floor. The old check missed it only because it skips each sight line's last stud. Those sides no longer get a banner (`HubRotundaCentre`).
- **Checks:**
  - A staging copy first, beside the live hub, then live. `R.check`: 0 problems, 0 leaks, 0 overlaps, 288 sight lines open, the route walked to all 12 pads, the regulars' 14 ways clear (839 body boxes).
  - ZFight: 9 hairline hits, none seen in play (two floor undersides, edge faces a few hundredths wide, and inside the fridge and a gun model).
  - In Play:
    - you spawn on the platform;
    - the four regulars stand and walk at their places;
    - the jump pad throws you onto the balcony (peak 29, landed 34.5 out at the balcony's height);
    - an upper pad and a lift pad each count you on their boards;
    - the training gate takes you to the training ground.
  - Photos: `docs/hub/hub_v3_photos_v743.jpg` (the entrance view, a pad bank, the upper floor, the VIP room).
- **Not tested:**
  - The VIP push-out: the owner counts as VIP in Studio. Its zone and its `Out` point moved with the build.
  - Two-player matches from the pads, phones.
  - No new decoration was added: the bigger room's own pieces (platform, ring, plinths, planters, the gym's ring) fill it.

## 38. A dead body's gun goes with it, 18 November 2026 (place version 753)

The owner: "after you kill someone their gun is still there".

- **The cause:** the server puts the gun a player holds into their body as `HeldWeapon`, welded to the right hand. Every client hides that one and draws its own copy sized to the avatar (`ThirdPerson.luau`). When a body died, `ThirdPerson` let the body go: it dropped its own copy and showed the server's gun again. Nothing removed the server's gun on a death, so it came apart with the body, was flung with it (`Fight.died` throws every part), and stayed for everyone until the body was replaced (the next round, in a round-based match).
- **The fix** (server, `Fight.luau`): `Fight.died` destroys the victim's `HeldWeapon` (and its hat with it) in the same step as the Health that tells the clients, and puts a Tool in the hand (the Shredder) back in the backpack. `Fight.showWeapon` never builds a gun on a dead fighter (a weapon switch, a zone change or the loadout window after death can't put one back).
- Replay and finisher copies already strip `HeldWeapon` and the client's gun, and the kill effects don't copy guns: nothing else was left behind.
- **Tested in Play:** the walking training dummy (katana), a Plinker (gun) and the player in the training room: each one's gun gone at the moment of death, and no gun piece visible on any dead body on the client.

## 39. The T-Bag explosion is back, 18 November 2026 (place version 753)

The owner: "bring back tbagging explosion". Ported from the web (`player.js` crouchTap, `room.js` case 'tbag').

- **The trigger** (`TBag.server.luau`): every crouch press goes to the server (`TBag` remote, `TBag.client`). The server counts them while you're alive: 14 within 4 s and your knees explode. At most 15 presses a second count, 3 s between two blasts, none while sealed in a bubble, in a pop quiz, in a cage, or before a match's round is live (the web's rules).
- **The warning:** from the 9th press `TBagHeat` (0..1) goes on the player, and every client draws a heat glow (a warm light), sparks and a haze round their legs, with the recorded `fuse_tick` as a looped sizzle, all growing with the heat and gone when it cools. No text.
- **The blast:** the frag's (Utility's explode(): damage 80 x (0.3 + 0.7 f), a 34 m/s shove + 10 up, out to 6 m, as the web's), mirrored in `TBag.server` because `Utility.luau` had another session's open work; the clients get the same "boom" and draw the frag's explosion, sound and close-up shake. It hurts only who you may hurt (`Fight.allow`: enemies in a live match, the training dummies), the knock through `Fight.knock`. Your own death is "T-Bag" with no killer (an earlier tagger gets no credit, as on the web). In the hub nobody else is touched; you still blow yourself up.
- **Kill feed:** `Weapons.list.tbag` (a naming-only row) shows "T-Bag".
- **Stats:** T-Bag kills, and falls after your grapple, now count as kills (count, streak, xp), not as a weapon row (`Stats.luau` only counted roster weapons, so both went uncounted). Coin and quest rewards follow the kills as they do for any kill.
- **Tested in Play:** 13 presses: the glow and sizzle on, still alive; the presses aged out and it cooled; 14 presses: the blast, a training dummy in range (30 HP left) died credited to the player via "tbag", and the player died, "tbag", no killer. Photo: `docs/tbag/tbag_warning_and_blast_v753.jpg`.

## 40. Balance pass: the Revolver's fan and the Redline's top speed, 18 November 2026 (place version 761)

The owner: "revolver needs to either do less damage or be less accurate the longer you hold it, redline damage at higher speeds needs to maybe be capped? its super strong". Commit 7b0fe84. The numbers, before and after, are in WEAPONS.md "Balance pass, 18 Nov 2026".

- **Revolver:** the tap is unchanged (40, 0.003 spread). Each fanned shot in a row is weaker and wilder: 24 x 0.88 each time (24, 21.1, 18.6, 16.4, 14.4), at spread 0.045 + 0.03 each time (up to 0.165). A 0.45 s pause or a tap starts a new string. A held cylinder still kills at 3 to 5 m. At 12 m it kills 49% of the time (was 93%), at 20 m 16% (was 53%).
- **The server fires fanned shots** (`Combat` `serverShot`): it rolls the spread itself and casts the bullet with both bounces against everyone's boxes where the shooter saw them, then echoes the path. The shooter's tracer comes from the echo (the `Arsenal` Shot handler).
- **Redline:** past 12 shots a second, only a quarter of the extra rate becomes damage (`over`, `Weapons.shotDmg`). DPS is 60 / 120 / 126 / 143 at 100 / 62 / 50 / 10 HP (was up to 204).

## 41. The remaining web weapons: audit and batch A, 18 November 2026

23 of the web game's 40 loadout weapons were still missing. The list, each one's gimmick and the batch order are in the shared notes, `weapons-port-audit.md`:

| batch | weapons |
|---|---|
| A | minigun, water, nailgun, bread, slapper |
| B | akimbo, taser, blower, cig (renamed), laser |
| C, a projectile engine | chicken, snowball, banana, tennis, bloodcross |
| D | bowling, slipper, scales, remote, bow |
| E | cart, lasso, cards |

**Batch A (in progress).**
- **Rows:** in `Weapons.luau`.
- **Gimmicks:**
  - Minigun: a spin-up held by the server (a `Spin` remote, `Rules.spin` / `spinLevel`, refused as "not spun up"). The barrels turn (`GunParts` `barrels`) and others see them through the `Spin` attribute. The recoil flight is the usual `Body.push`.
  - Water Pistol: a soak, `SoakUntil` in server time. `WeaponStates.client` sets `Body.wet` / `Body.grip`, and `Movement`'s friction is multiplied by `st.grip`. A wet screen edge, drips on soaked people, the stream instead of a tracer (`Fx.waterArc`), and the tank draining (`GunParts` `water`).
  - Nail Gun: 6 nails from one shooter in 1.2 s pin the victim to the wall behind them (`Combat` `nailHit` / `pinTo`). A player gets `PinAt` / `PinUntil` / `ACGrace`, and `Body.pin` pulls them in `Move`. A dummy is anchored. Nails stay in walls (`Fx.nailIn`), big nails go through the pinned person, and the shooter gets a `PINNED` callout.
  - Bread: a pogo off the map on a swing that hits nobody (`Arsenal` `resolveSwing`).
  - Hand Slapper: `radial` knockback and `slip` in the `MeleeHit` handler.
- **Clips:** `swing_bread`, `swing_bread2`, `swing_slapper`, `draw_heavy`, `draw_melee`, `draw_bread` (`anims.mjs` + `Anims.luau`).
- **Coming from other sessions:**
  - the kit models, from guns-remodel;
  - the hold rows and third-person poses, from hold-hands;
  - the recordings, from sounds;
  - the hat seats, from weapon-hats, once the models are in.
- The Roster rows stay `live = false` until the models and holds are in.

## 42. The grapple's yank, 18 November 2026 (place version 796)

The owner, about grappling onto people (section 37): "when you grapple someone maybe you can press a button to like pull them towards you?? Or reel you towards them??" Both are kept. Reeling you in stays what a hook on a person does; the yank is a second choice while the rope is on them.

- **The key:** GRAPPLE YANK in Settings > KEYBINDS (`Binds` id `yank`), rebindable like the rest.
  - Keyboard **F**: shared with QUICK JOIN, which only works in the hub, where the yank never does.
  - Controller **B**: shared with crouch. Crouching mid-rope only lowers your eye.
  - Phone: a **YANK** button (56, 244), shown only while your rope is on a person and the yank is ready.
- **What it does** (`Move.client` `tryYank` → `Main.server` `yank()`): one pull toward you through `Fight.knock`, so the anti-cheat knows the shove. The rope drops with it.
  - Aimed so they'd fly about 0.7 s and come down a fifth of the way short of you (`Config.hook.yankAir`).
  - Capped at 30 m/s sideways (`yankSpeed`; a point-blank frag shoves 34 m/s), plus 9 m/s up to lift them off their feet (`yankUp`). If you're above them, up to 10 more (`yankClimb`).
  - From the hook's full 90 m range it drags them about 20 m, not across the map.
  - A training dummy goes over for the pull (`Dummies.slip`, chest first toward you), or its legs would walk it off.
- **Who:** enemies in a live round and training dummies get the full yank and are tagged (`Rules.tagged`, `"grapple"`), so a fall within 10 s is your kill via Grapple.
  - Anyone you can't hurt (a teammate, another player in training) gets 45% of it (`yankMate`) and no tag: a rescue.
  - Not in the hub or a map room: weapons' zones only (`match`, `training`, `playground`).
  - Not before a round (`LoadoutWindow`), and not on someone held in a soap bubble, a cage or a pop quiz.
- **Cost:** one yank every 3 s (`yankCool`). The server stamps `YankT` (server time) on you; your client and the phone button read it. It ends the grapple, so the next yank needs a new hook, and that spends a ranked charge as usual. The yank itself takes no charge.
- **Look and sound** (`GrappleYank.client`, for everyone; the server sends `"yank"` on the Grapple remote):
  - the rope snaps dead straight and bright from the hand to their chest, then thins out over 0.22 s;
  - a crack: the recorded `ropesnap` (Pro Sound Effects, a towel crack), 2D for the yanker and positional on them for everyone else;
  - a short pale streak on them while they fly.
  - No text. A teammate's gentle pull draws thinner.
- **Test hook:** `YankFxHold` (seconds) on the local player holds the snap and the streak for photos.
- **Tested in solo Play** (the training yard's Plinker, on its block on the live-fire stage, 60 studs from the firing line):
  - hooked, then F 0.26 s later: the rope dropped, every client got the yank, the snap and the 2D crack played for the yanker;
  - the Plinker left its block at 68 studs/s toward the yanker and 25 up (peak 4 studs over the block), off the stage onto the yard floor;
  - dropped below the fall line 2.2 s later: a void kill credited to the yanker, `via = grapple`;
  - `YankT` stamped 3 s ahead;
  - the phone's YANK button (TouchForce): hidden unroped, shown roped and ready, hidden while cooling, back when ready, gone on letting go.
  - **Seen:** a dummy lands about where the yanker stands, then slides on (it lies flat for the slip). Over 2.5 s it went 88 studs, past the yanker. Since version 812 a landing brake cuts a yanked dummy's slide to 15% the moment it's down again (Main.server). It's not yet tested in Play.
  - Not tested: two real players (a yanked player's own movement friction stops them; a solo test can't show it) and the teammate pull.
  - Photo: `docs/grapples/grapple_yank_v796.jpg` (the taut rope to the Plinker in the air, its streak from the block).

## 43. Open roofs on the Gut and Suburb v2, 18 November 2026 (place versions 812 and 821)

The owner: "Suburb we should be able to get on roofs, gut map too!! There are weird ceiling blockers". The blockers were section 36's body-only columns: every building stood solid to the old lid at 150, and v735 made the part above its real roof ray-blind, but it still stopped bodies.

- **Open roofs** (`tools/roblox/roofs.py` `open_up`, run by `gut_models.py` and `suburb2_models.py` in place of `split`):
  - Every lid-high building's hit boxes now follow the kit's own roof, with nothing above it.
  - Rays straight down onto the kit every 1 stud (Suburb) or 1.5 studs (the Gut) give a height map. Heights go to the nearest 0.5 stud, and runs of cells within 1 stud of each other share a box, whose top is the highest cell.
  - Movement walks up any step of 1.8 studs or less, so pitched roofs and domes are walkable steps that stay within about a stud of the mesh.
  - A round building's turned twin squares are sampled once. Cells with nothing over them stay open where they reach the rim, so the hit boxes follow what you see.
- **Roofs over spawns shed you:** the Gut's two halls and Suburb's six houses round the turning circles.
  - Their boxes carry the flag `s`, and WebArena marks them `Slide`. Move.client treats them like the wall box's ledge: it slides you off toward the middle.
  - You can hook them, land and touch, but you can't camp over a spawn, and there's no ceiling.
- **Counts:** the Gut has 793 plain + 860 turned hit boxes (726 rows before); Suburb has 705 + 159 (590 before).
- **Sight lines** (`tools/roblox/roof_sight.py`: standing spots every 3 studs on every roof, eyes 4.6 up, to every team spawn at 2.5 and 4.6, through the built hit boxes; rails don't stop shots):
  - The Gut: 58 of 74 roof areas saw a team spawn, almost all through the halls' doors from 195-280 studs.
    - Screens as high as the doors now stand just inside each hall's two front doors and its north door: `cover`, 12 high, you go round either end.
    - That leaves 2 marginal lines: from a corner of each south block's roof through the hall's south door, at 52 studs, to the spawn just inside it.
  - Suburb: its spawns stand in the open at the turning circles, so nearly every roof sees one.
    - The rim houses, 44 studs over a spawn, now shed you.
    - The houses nearest each circle still see their own team's spawn from 64-80 studs, and every roof sees the far spawn down the street from 150-206 studs.
    - Parapet gables tried in the check only halved the near lines. A real fix needs cover over the spawns; it's left until Suburb comes back.
  - W.check's spawn-to-spawn lines: 0 of 128 on all four walled arenas (the Gut, Suburb v2, Bazaar v2, Desert v2), as before.
- **A way up besides the grapple** (`tools/roblox/pad_sim.py` flies the throws against the built hit boxes, as W.check does):
  - The Gut: a pad in each north yard throws you onto the Tube's flat roof (21.5 up), and one in each Avenue onto the small block by the south alley (32 up). New model `gu_pad`: an enamel plinth, a cream top, a soft pink glow ring.
  - Suburb: a trampoline on each north garage's roof (up the outside stair) throws you onto the house's roof (32 up), landing south of the ridge, clear of the chimney. None on the south garages: a free-for-all spawn stands there, and the yard trampoline lands there by the upstairs window (W.check caught a first try that put a trampoline on the spawn).
- **Patch kits:** `arenakit.py --only=<model>,...` exports just those models, and `W.swap(name, id)` swaps them into the kit library and the built arena's Shell, leaving everything else as it is (the Gut's installed heart).
  - Gut patch: asset 135539607644944 (`gu_cover`, `gu_pad`). Suburb patch: asset 92321963601111 (`sb_tramp`).
  - A later full W.import + W.build needs the kit uploaded whole.
- `W.solid` now rebuilds the pads too, and W.check reports `roofs: <body-only columns over 40>, <Slide boxes>`.
- Bazaar v2 and Desert v2 stay as they were.
  - Bazaar v2's lid-high boxes are the town's outer ring, round its roof network at y 18, which is already open.
  - Desert v2's are rock spires over the mesa tops, not roofs.
- **A raised roof box closes where the kit dips just under its foot.** A cell with nothing over a box that stands on something (base above y 1) gets a plate at the foot if the kit is within 8 studs under it (`roofs.UNDER`).
  - The v812 test fell twice through the side of the Gut's Tube roof: a barrel vault whose side meets the block's wall under the box's foot (y 18), looking closed.
  - Cells over the street stay open.
- **W.check:** every hit box built, no lid, Slide boxes 234 (Gut) and 42 (Suburb), no body-only columns over Suburb's roofs. The Gut's 27 "columns over 40" are the tower balcony's bars (y 21-41), not roofs. All spawns are on floors and every pad lands.
- **Tested in solo Play on the Gut** (version 812):
  - the west north-yard pad threw me onto the Tube's roof (peak 29, standing at 21.5);
  - walked 41 studs along it at roof height;
  - teleported onto the north block's roof and stood there (photo `docs/maps/gut_roof_v812.jpg`);
  - grappled from it down toward the kiosk dome (the pull flung me past it, as letting go does);
  - set on the west hall's roof, it shed me toward the middle and off its front edge, into the Approach, in 1.8 s.
  - **Found:** two grapples up from the Tube's roof to the block's dome dropped me through the slot at the Tube's side. Fixed above, in version 821: a floor at 19.5 there now, and W.check is still clean. Getting from the Tube's roof up onto the block's roof by grapple still needs the right swing: the block's edge is 12 higher.
  - Not tested: Suburb in Play (switched off), and two players.

## 43. Hub v3: the spawn lounge and the way upstairs, 18 November 2026 (place version 810)

The owner asked two things, both relayed by the main session:
- "Can the current lounge be turned into a part of a larger lounge where players will now spawn making the central [room] feel more spacious!!"
- "how do we make it more obvious that there are pads on second floor"

Plan picture: `roblox/docs/hub/hub_lounge_plan.jpg`. Photos from the Play test: `roblox/docs/hub/hub_lounge_photos_v810.jpg`.

**The lounge** (HubRotundaRooms, the lounge block):
- Today's lounge stays whole, with its numbers unchanged, as the middle bay of a big room. Its walls and hall are gone.
  - It moved `R.LOUNGE_S` = 8 further out (10.8 in Hub v3), with the VIP room behind it.
  - Its old ceiling is now a timber-edged canopy on two posts.
- The big room is 75.6 x 55 in Hub v3, as wide as the round room, with a 20-tall ceiling (`R.LOUNGE_X` = 28, `R.LOUNGE_H` = 16 before the warp).
  - It opens onto the round room through three round arches: sides 6, 7 and 8 (`R.OPEN` "arcade").
  - The ceiling's triangles in front of the side arches are WedgeParts laid flat (`LoungeLidCorner`), with their slope on the round room's wall.
- What's in it:
  - The spawn rug (an accent ring) on the front floor.
  - The showroom down the west wall: bundle plinths in slots 1, 2 and 4. Slot 3 stays on side 9; the trophy case stays on side 5.
  - Two seating groups down the east wall.
  - Timber beams and white panels in the ceiling, a wood dado and a cream cornice.
  - Looticus has a 7th spot by the showroom.
- The spawns: `R.SPAWNS`, 8 markers in two rows facing the arches, far enough back that the first look takes in all three. Everything that places you reads the same `Hub.HubSpawns` folder, so nothing else changed:
  - Matches' `spawnAt`, the map room's return, QuickJoin, `Fight.spawn`'s `TeleportT`.
  - `HubArrive` (training's way home) stays in the round room by the armory.

**Upstairs, obvious:**
- The jump pads: an accent ring (`JumpGlow`, with a light) round each pad. Their light column up past the balcony (`JumpColumn`) was taken out the same day (owner: "I dont like the pillar of light from the teleporter", place version 889). From the spawn the way up is the lit doorways (`R.FIRST_LOOK`); the rings and the UPSTAIRS boards are behind the piers from there.
  - Both breathe on your screen: `HubLife.client`'s new `HubBreathe` tag, with attributes `BreatheLo`, `BreatheHi` and `BreathePeriod`, and the light following.
- The UPSTAIRS boards (HubRotundaLifts, the end): on the gallery wall over each jump pad, in a banner's place. Each lists the pads that jump pad leads to (east: 7, 6, 5, 4; west: 1, 2, 3) with live counts.
  - Each row is a part named `Mirror` inside its pad's model, so `Matches.padSign` writes the count on it as on the pad's own board.
- The four doorways into the second floor: an accent line round each opening (`UpperGlow`, `UpperGlowHead`) and an accent light just inside.
- No floor strip: the owner had the floor lines taken out on 16 Nov.

**R.check:**
- The lifts, their boards and the words over the ways out are tested from `R.PLATFORM_LOOK`, the old spawn rows: where you come out onto the platform.
- From every spawn, `R.FIRST_LOOK` must show one each of: the name, a jump pad's column, a lit doorway upstairs, and the 2V2 lift's pad.
- The lounge's own things (the duck, bundles 1, 2 and 4) are tested from `R.LOUNGE_LOOK`, the front of the rug.
- The walk to all 12 pads starts at the middle of the spawns and goes out through the middle arch.
- New walks through the three arches, and new leak points in the lounge.

**The hub egg's nook** (training-v2 asked for a hidden spot that takes some exploring; main gave it the egg):
- The gallery window over the west arch (`R.EGG_SIDE` = 8) is a real opening, `R.EGG_NICHE` = { half width, sill, head }. It's dark, in the same frame as the others.
- Behind it is a small closed room on the lounge's roof: in Hub v3 about 8.6 wide, 8.1 deep and 8.4 tall, floor y 260.96.
- You reach it from the balcony with a hop of about 3 studs. training-v2 tested it in Play with real movement and one jump press: the body rose 4.78 over the 3.03 sill and landed inside. Their egg stands in it since place version 819 (commit 9384f5b).
- R.check keeps the room clear ("the hub egg's nook over the west arch" in `R.WALKS`).
- `R.KEEP` holds other sessions' spots in world numbers (Hub v3 only), so the builder can never put anything in them. The first entry is the lore NPCs session's Dumpling in the gym's south corner (`Map.Lore`).

**Flicker (ZFight, place version 846):** the first scan after the lounge build found 21 visible hits. The rebuilt lounge left 8, and those 8 were there before (the gym door's sill against its jambs, two balcony slivers, the fridge, the display sawn-off). The fixes:
- The lounge floor's top is at -0.05: it lies under the round room's floor disc, which was only 0.02 above.
- The bay's carpet underside sits off the VIP floor's.
- The canopy's end sits inside the far wall instead of on its face.
- The old lounge's piers stand 0.06 proud of the rail behind the sofas, whose backs no wall hides any more.
- The jump-pad ring's underside sits off the floor's ring line.

**Then the 8 older hits (place version 852): 0 visible hits left.** Only covered faces nobody can see remain.
- The gym door's jambs end just past the threshold paint, not on it.
- The balcony's floor finish stops 0.05 short of the slab's outer face.
- `B.unseam` (a kit part made thinner along its upright axis) fixes the two kit-model seams on show:
  - the fridge's dark part, top lowered off the red body's;
  - the display sawn-off's hinge, which lies 0.014 under and 0.017 over its frame in the kit model itself. The gun model still has that seam in hand.
- The egg is training-v2's, in `Map.Hub.HubEgg`, outside the Rotunda: no rebuild wipes it and R.check doesn't look at it. The room has its own leak point.

**Checks:**
- Live R.check: 0 problems, 0 leaks, 0 overlaps, 321 sight lines with none hidden, 12 pads walked to from the new spawn, the regulars' 14 ways clear.
- Solo Play:
  - You spawn on a spawn marker in the lounge, zone hub.
  - Standing on 2v2_u1's pink side turns its UPSTAIRS row from 0/2 to 1/2 together with the pad's own board, and back to 0/2 after stepping off.
  - On the client the column and ring breathe (column 0.84 to 0.90, ring 0.10 to 0.38 in 0.8 s).
- CROSS_SERVER stays false.

**Not tested:**
- The VIP push-out (the owner counts as VIP in Studio).
- Several players spawning at once.
- Phones (the arches and the board from a small screen).

**Traps:**
- The column first sat in the walks to the 1V1 and 4V4 lifts. A see-through part still counts in the keep-clear test, so the column was made narrower.
- From the rug's middle, the canopy's front post hid bundle 2. The lounge's sight point is the rug's front.
- A Mirror row lives in the round room but belongs to an upper pad's model. Anything that ever uses a pad's bounding box would see it stretch to the gallery wall. Nothing does today: Matches, QuickJoin and PadGlow only look for `Side*`, `Slot` and `Glow`.

## 44. More maps: Suburb v2's detail, the Spooky Forest and the Backrooms back from the web, ARCTIC CABIN, SKATEPARK and STATION, 18 November 2026 (place versions 818 and up)

The owner (18 Nov, about 04:30 UTC): "We need more map variety create our maps based off popular cod maps, make an artic cabin bring back spooky forest and back room!! Suburb needs a bit more detail but yeah".

**The rule kept:** no map copies another game's map, not even renamed or rebuilt. "Based off popular cod maps" was read as the design principles of classic shooter maps: three lanes, readable sightlines, power positions with counters, flanks, cover rhythm, a few seconds from spawn to the first fight. Every layout, theme and name here is our own. The owner's Nuketown wish is answered by SKATEPARK: two facing bases with a contested middle, small and fast, nothing taken from that map.

- **Suburb v2 detail pass** (`tools/roblox/suburb2_detail.py`; place version 818):
  - One item list drives both the hit boxes (`suburb2_layout.py` calls `add_hits`, kept as `L.DETAIL`) and the kit (`suburb2_models.py` calls `dress`), so they cannot drift apart.
  - Fronts: lap siding on the upper storey over a belt course, corner boards, plinths, sills, slatted shutters where there's room, window boxes, gutters and downpipes, porch decks with a step and a lantern (a real light).
  - The 8 houses you go through are furnished: a kitchen (counters, wall cupboards, a fridge), a living room (sofa, coffee table, rug, media unit, bookcase, floor lamp), a dining table; upstairs a bed, a wardrobe, a desk. Furniture is real cover (it stops you and takes shots). Skirting, curtains, ceiling lights, pictures (two flat colour fields, nothing written).
  - Yards and street: patios with a table and a parasol, a kennel, a washing line, a mower, mailboxes at every front path, shrubs at the house corners, hydrants, gates standing open. Garages: hoops, coach lamps, a workbench, storage tubs, bikes against the wall, an air-conditioning unit and a skylight on each flat roof (cover up there).
  - 124 new hit boxes; the open roofs (section 43), pads and everything else unchanged (checked hit box by hit box against the committed layout). A grid walk check passes in all 8 houses: front door to back door, to the stair's foot, upstairs from the stair's top to the spawn and every window.
  - Cost: about 180k triangles (from 97k).
- **Spooky Forest** (`Forest`, "SPOOKY FOREST", site z -42000): the web's Scary Forest cropped to its middle (web x -80..92 m, z -66..64 m, x3): the cabin, the campsite, the clearing's standing stones, the lookout tower, the mast yard, the dock, the lake (now deep enough to swim), the road with the broken-down car. The web's gags and every sign are gone (office chair, water cooler, memo board, TV, signs). Attackers start behind the campsite, defenders behind the lookout, the mast yard is the third side. `ForestLife.client`: flashlights on everyone in the Forest (a SpotLight on each head, this client only), the mast's red lights and the car's hazards blink (one write per change). Look `forest`: moonlit blue-grey, low cold haze.
- **Backrooms** (`Backrooms`, "BACKROOMS", site z -48000): the web's seeded rooms (a Python copy of its generator checked identical), cells 10 to 49 (480 x 480 studs), sealed by walls on the crop line; the hall, the office, the wet room, the pool rooms (ankle-deep, as on the web). Sealed indoors: no wall box, no SkyY. `BackroomsLife.client`: two groups of dying panels flicker on their own timers. Look `backrooms`: warm yellow-white, a haze close in.
- **ARCTIC CABIN** (`ArcticCabin`, site z -54000): new. A big two-storey log cabin you go through and onto (its roof's hit boxes follow the slope), a ridge with a knoll (the north lane), a frozen pond with boathouses, ice huts and drifts (the south lane), a sauna, a woodshed, a tool shed. The boathouse roofs are open (roofs.open_up) like the Gut's and Suburb's. `ArcticLife.client`: light snowfall (one emitter over the camera). Look `arctic`: a low winter sun from the south, bloom held back on the snow.
- **SKATEPARK** (`Skatepark`, site z -18000): new, small and fast. Two clubhouses (skate shops, roof decks behind parapets, an inside stair and a springboard) face each other across a sunken bowl crossed by a bridge; the bleachers lane (a perch at 9) and the shelter lane (quarter-pipe decks at 6, a shelter roof at 10). Doors offset so no door lines up with another; 0 of 128 spawn lines open. Look `skatepark`: late golden light from the south.
- **STATION** (`Station`, site z -24000): new, medium, a small-town terminus at golden hour with a train waiting. The middle lane is two platforms and the parked three-carriage train you go through (two doors a side per carriage, never facing each other), plank crossings between carriages and the open track bed; the waiting rooms (the bases) have upper floors that step out onto the platform canopies' flat tops; the north lane is the station hall (a terminus concourse with a gallery over the platforms), the south lane the goods yard (sheds you go through, crates, a dock, a gantry). The covered footbridge at 20 over the platforms is the power spot, countered by the upstairs windows, the gallery, the canopy tops and the train's roof. Built by `tools/roblox/station_arena_models.py` (kit `station_arena`, models `sa_*`: `station_models.py` is the 14 Nov show-hub lobby kit, left alone). About 4 s from spawn to the platforms.

**Checks** (W.check in Studio, then a Play test at version 830): every hit box built (Suburb 988, Forest 2,952, Backrooms 829, Arctic Cabin 791, Skatepark 205), every spawn on a floor, 0 of 128 team spawn lines open on each, pads landing where meant. In Play, a ghost match in each (`JankMatchTest("ghost", "1v1", <arena>, secs, player)`): Zone "match" and the arena's own look on the client, the Forest's flashlight on and off outside it, the Arctic's snowfall on and off elsewhere. The Forest's night was too dark on first sight and was lifted (ambient, exposure, a thinner haze); the Skatepark was washed out and got a lower exposure; its spawns faced the clubhouse's back wall and now face past its corners. Suburb v2 is back in the rotation (`Enabled = true`), with the four new ones (version 830). Station went in the same way at version 838 (487 hit boxes, every spawn on a floor, 0 of 128 lines open, a ghost match with its look): the rotation is 14 maps.

**How these were made:** the new-map pipeline (memory roblox-v2-maps): a plain-Python layout (`tools/roblox/maplayout.py` holds the shared helpers for new ones), `arena_plan.py` / `arena_check.py`, a headless Blender kit with arenakit, the wall box (wallbox.py), `roofs.open_up`, `W.import`, `W.build`, `W.check`, `W.pool("add")`. New arenas go into the pool with `Enabled = false` and are switched on after a Play check. The web ports read `tools/roblox/arenas/<id>.json` (webmap_dump.mjs).

**Map-vote cards** (`shared/MapCards.luau`): the new arenas' pictures are Cycles renders of their own kits (`tools/roblox/card_render.py` runs a map's builder with card cameras, 1280 x 720, denoised), uploaded as Images. No text in any.

## 45. Hub v3 quick pass: the arches from the lounge, the second floor's finish and its pad bays, 18 November 2026 (place version 903)

Three owner notes, fixed in Hub v3 ahead of the hotel-plaza rebuild (`roblox/docs/hub/hub_v3_quickpass_903.jpg`, before | after):

- **The arches from the lounge.** The owner: "can you fix the back side of this to make it look presentable".
  - **Cause:** the warp. The nine big stones were tilted boxes, and `R.applyWarp` stretches heights over 9.5 by 1.87, which turned them into pointed facets with holes beside them. The round room's piers showed their spiky backs.
  - **Fix:** in Hub v3 each arch is now made in world studs, with `B.rigid` (its place is warped, its parts keep their shape: marked `Warped`). It has:
    - 24 small stones in a true half circle as wide as the way through (the collision boxes' faces);
    - jambs under it, and the spandrels filled up to the lintel in slices that the stones hide;
    - on the lounge side, a cream hood, a keystone and imposts.
  - The lounge adds a clean pilaster over each of the round room's four piers there, an `ArchBand` over the arches, and its cornice carried across the three faces.
  - Hub v2 keeps the nine stones.
- **The second floor's finish.** The owner: "top floor is missing this, and its also missing moulding". It now has the ground floor's finish:
  - skirting with a cream cap that stops at the fins (no steps), plus a base round each fin's foot;
  - pilasters at the round room's corners inside the hall (they hide the trim's corners);
  - a cornice along the round room's wall and along the end walls;
  - on each end wall: skirting, a rail and a lit panel in a pale frame;
  - every doorway's sill lit in the accent, on the hall side and the balcony side.
- **The pads upstairs.** The owner: "the upstairs seems so empty", "like where the pads are!". Every upper pad now sits in a designed bay:
  - on a low deck (`DECK_H` 0.36: under the walks' keep-clear zones, which start 0.4 over the floor) with the accent along its lip (`UpperNosing`);
  - under a lit coffer its own size, in a cream frame;
  - with a lit panel over its board.
  - Between each two pads, clear of the walks: a solid waiting bench and a big planter.
- `R.FIRST_LOOK` groups can name several parts (`"A|B"`). The jump pads' light column went the same day (place version 889, commit 7d0898c).
- Checks: R.check 0 problems (50 zones, 0 leaks, 313 sight lines, walked to 12, 14 regulars' ways). Flicker finder 0 visible.
- Rule kept for the plaza: every level has the same finish (skirting, cornice, trim round openings, a finished lip on open edges); every pad has a designed bay; everything is finished on every side a player can see.

## 46. Hub v3: the hotel plaza in the lounge wing, 18 November 2026 (place version 940)

The owner asked for the lounge as "like a hotel plaza", because the add-ons looked like add-ons. A square plaza for the whole hub was planned, then the owner said: "keep the old circular look though for the hub, lounge free rein". So the round room stays the hub's heart, exactly as section 45 left it, and the hotel is the lounge wing south of the three arches. The builders are HubRotunda, HubRotundaCentre and HubRotundaRooms (`plaza()`). The square-plaza builders (HubPlaza*) were never committed; they are gone from PolishBackup too.

**Switch.** `R.LOUNGE_STYLE` comes from the module's `LoungeStyle` attribute and defaults to `"plaza"`. `R.switch("lounge")` builds section 43's spawn lounge live again; `R.switch("plaza")` builds this one. Both run from a copy of the module with the attribute set. `R.PLAZA` holds the plan, in the round room's own units, which the Hub v3 warp then scales.

**The plaza.** A courtyard under a pitched glass roof, entered through the three arches. Two storeys of hotel rooms in warm stone stand on three sides, over arcades.
- **North side.** The round room's three south faces.
  - They have a stone skin (`FaceSkin`), the band and string-course lines, and a cornice.
  - Over the middle arch is a balcony with doors and a window. Over each side arch is a bay window; the west one is still the hub egg's nook (`R.EGG_NICHE`, unchanged).
  - The arches are the world-stud arches of section 45. On the plaza side their spandrels get a stone skin (`ArchSkin`).
  - Clean world-stud pilasters stand over the round room's piers.
- **Facades.** Framed French windows with sills.
  - Some are balconies with balustrades; the rest have flower boxes.
  - Upper windows have bars, a head and jambs, and some have shutters.
  - About a quarter of the panes are lit warm from inside (`LIT`). The pattern is fixed by the bay count, so every build is the same.
  - The side facades' first bays carry only the pair away from the round room, because the bay windows' corners come close to the other pair.
- **Glass roof.** Two slopes of glass (`GlassRoof`) with a lit daylight field behind them, pale rafters, purlins, a ridge beam and stone gables. The flat lid stays over the strip by the arches, with its lit panel.
- **Arcades.** Every bay of the back walls has a framed front: pilasters, a fascia, a warm lit band and an awning.
  - `"shop"` is a glazed front with a door. `"window"` is glazed. `"frame"` is the frame only, with the fascia higher and no awning.
  - **West, the boutique:** three of the shop's bundles on plinths, in front of their boards.
  - **East, the lounge:** seats in the first and last bays, a bar in the middle bay (counter, stools, shelves with bottles, the fridge), and the arcade machine at the north end.
  - **South:** the reception desk (east), the VIP door (middle, the VIP room behind it unchanged) and the porter's door with two luggage carts (west).
- **Courtyard.** The spawn rug faces the middle arch. There is a fountain with the stone duck, big trees and two chunky chandeliers. Each chandelier has a big ring with candles and crystal drops, a smaller ring with candles, a lantern, and a warm light.
- **Lifts** (HubRotundaCentre). Each of the five lift openings has a pale frame against the piers, a head and a warm lit header.
- **Colour.** Warm quiet stone (`STONE`, `STONE2`, `TRIM`, `TRIM2`) and warm grey floors. The pads' colours and the one accent line stay the only strong colour.

**Kept working.** All 12 pads, HubSpawns, HubArrive, the holograms, the four regulars, the VIP door, the training gate, ZoneCull and the hub egg all still work. Looticus has new points: either sofa, behind the bar, the arcade machine, and the boutique.

**The code panel's corner.** The corner where the east and south arcades meet is left clear for the lore session's code panel. It has a warm light over it. Its floor point in the live hub is (-167.20, 239.95, -9899.42), facing -X; an 8 x 6 x 8 box over it was checked empty. The panel's old place, (-185, 240, -9946), is now inside a tree pot. Main was told to forward the move to the lore session.

**Checks.**
- Live `R.check` (place version 940): 0 problems, leaks 0, 313 sight lines, 12 of 12 pads walked to, the regulars' 14 ways clear.
- Flicker finder over `Map.Hub.Rotunda`: 21 small visible hits are left (from 61 on the first stage build). All are 2.2 sq studs or less, and most are bottoms at floor level.
- One solo Play: the player spawns in the courtyard facing the middle arch, all 12 pads are live, the regulars are out (Looticus in the boutique), and nothing from the hub shows in the console.
- Before and after: `roblox/docs/hub/hub_hotel_plaza_940.jpg`. The plan: `roblox/docs/hub/hub_hotel_plan.jpg`.

**Traps.**
- The plaza is built in the round room's units and warped (K = 1.35, heights by `R.V3.H`). People-sized things are built in world studs through `B.rigid`: the desk, the bar and the pilasters.
- Keep anything you add to the lift openings against the piers (x 4.85 or more). At x 4.35 it narrowed the ways from the platform to the outer lifts and hid two pads' sides.
- The side arches' ways are checked to 31 in the plaza (34 in the lounge). Past 31 they run into the plaza's first piers, where the courtyard is already open.
- Light: the hub's look (`HubLook` "hub") is lit by lamps, not by the sun. With pale stone, the first lamp values washed the photos out. Courtyard lamps sit about 0.45 to 0.8 bright; check photos in the hub's look after any lamp change.
- The kit pier's shaft, corbel and head share their back plane. In the plaza those backs show in the arcades, so they share one colour there (`PIERC`).
- Arches' world-stud stones and the round room's lintels stay the hall's own colours inside. The plaza side gets thin skins: `ArchSkin` in HubRotundaCentre and `FaceSkin` in Rooms.

## 47. Hub v3: the hotel plaza turned into an indoor lobby, 18 November 2026 (place version 953)

The owner on v940: "the lobby area looks like the outside of a hotel rather than the inside now!". Main relayed the rest of the brief: the bay boxes become part of the wall, no windows, a closed ceiling, exposure down, indoor plants, keep the rest. Same builder and footprint. The switch value is still `R.LOUNGE_STYLE = "plaza"`; the word over the middle arch now reads LOBBY.

**What changed** (all in `plaza()`, HubRotundaRooms):
- **Ceiling.** The glass roof, daylight field, rafters and gables are gone. One flat plaster ceiling (`PLASTER`) covers the whole wing. It is coffered by beams (`CX` along, `CD` across, laid out so a coffer is centred on each chandelier), with a warm downlight in every other coffer and a rose over each chandelier.
- **Walls over the arcades.**
  - No windows, shutters, balconies or flower boxes.
  - A **mezzanine gallery** runs round the west, east and south walls. It sits on the band's top, 2.6 out from the walls, with an edge, turned balusters and a rail; the side runs start at d 34, clear of the egg nook's box.
  - On the gallery wall: a wood dado and rail, a panelled wood door to each room (a double door over the VIP door), a moulded plaster panel over each door, and a sconce between each pair of doors.
- **The bay boxes over the side arches are part of the wall.** Each of sides 6 and 8 is built out to the box's old front, from over the arch to the ceiling (`FaceMass`). The same lines cross its front, with a framed wood panel where the window was. Side 8's mass is built round the hub egg's nook, whose walls and lid stay HubRotundaCentre's (their stone now matches). Side 7 keeps its balcony, now with a wood door and a plaster panel.
- **Arcades.** No awnings and no glass. The lounge bays are framed fronts, and the porter's door is a panelled wood door. The dado is the lobby's wood, no longer the hub's ochre.
- **Lobby floor.** Palms in pots (ringed trunk, two tiers of long leaves) replace the round trees. A seating group stands either side on a bordered rug: a sofa, two armchairs and a low wood table.
- **Exposure down.** The paint is a step darker (`STONE`, `TRIM` and the rest). The lamps are lower: courtyard 0.25, chandeliers 0.6, sconces 0.2, arcades 0.4.

**Checks.**
- Live `R.check`: 0 problems, leaks 0, 12 of 12 pads walked to, the regulars' ways clear.
- Flicker finder: the biggest visible hit left is 2.2 sq studs, a bottom face at floor level.
- One solo Play: the player spawns on the lobby floor, all 12 pads are live, the regulars are out, and nothing from the hub shows in the console.
- The lore code panel stands clear at its corner, (-167.2, 240.1, -9899.4).
- Sheet: `roblox/docs/hub/hub_hotel_lobby_953.jpg`.

**Traps.**
- Two stacked rugs need their tops at least 0.06 apart, or they flicker over their whole area.
- A full-width built-out wall must not also get the bay window's floor under it: their bottoms meet in one plane.
- Studio's id changed after the PC restart at 16:48 UTC (now `4c07f65f-…`). Use `list_roblox_studios` when a call says the Studio is gone.

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
