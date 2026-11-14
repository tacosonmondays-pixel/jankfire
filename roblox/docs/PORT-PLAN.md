# JANKFIRE on Roblox: the port plan

Written 2026-11-14, updated the same day after the foundations pass. Place: "Jankfire.." (placeId 96891323589901), saved at version 76.
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
| Sounds | made live in code | **1 of 32 uploaded** (the rifle). The other 31 are empty slots, so the game is silent | the files are ready in `roblox/assets/sounds`; limit is 100 uploads per 30 days, 2,000 if the account is ID verified |
| Code | | about 8,600 lines of Luau | exported to `roblox/src` on branch `claude/f-roblox-studio` |

## 2. Fix these first (before adding 36 more weapons)

Done on 2026-11-14: 1, 2 and 3. Still to do: 4, and uploading the 31 sounds.

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

## For the next Claude session

- Recover state: memory `roblox-session-recovery`. Lighting: `roblox-zone-lighting`. Rules for the shared Studio: `studio-play-sharing`, `auto-save-place`.
- The local clone is stale and locked. Read the specs straight from GitHub:
  `https://raw.githubusercontent.com/tacosonmondays-pixel/jankfire/main/roblox/docs/WEAPONS.md` (398 KB; read "Core systems" once, then the weapon's own section) and `.../MODES.md`. Step 2's file map is in `roblox/README.md` on branch `claude/f-roblox-weapons`.
- Weapon stats live in `ReplicatedStorage.Jankfire.Weapons` (`list`), checks in `ServerScriptService.Jankfire.Rules` / `Combat`, the client in `StarterPlayerScripts.Jankfire.Arsenal` + `Viewmodel`.
- The spec's last section lists every place the web server trusts the client. The Roblox server must check those.
