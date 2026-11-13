# JANKFIRE modes: the Roblox porting spec

The owner asked: "can you explain the modes too!" This is the sister doc to WEAPONS.md. It explains every mode in
JANKFIRE so that any later session can build each one in Roblox from this doc alone.

**Where the facts come from.** Everything here is traced from the code on `claude/roblox-weapons-spec` (= latest
main). Names and memory were not used as sources. `file:line` points at the logic, so a porter can re-read it.
Anything the code doesn't settle is marked **unclear:**.

**Units.** The web game works in metres. The port uses **1 m = 3 studs**. Distances, radii, sizes and speeds are given
both ways, for example `1.9 m (5.7 studs)`. Times, HP, damage, counts, rates and multipliers do not scale. Gravity is
26 m/s², which is `Workspace.Gravity = 78`.

**Roblox ground rules** (decided in step 1, PR #503 / `claude/f-roblox`; see WEAPONS.md):
- **Movement:** the client owns its own character. The server catches teleports.
- **Knockback:** the server sends a velocity on a RemoteEvent, and that player's client applies it.
- **Remotes:** they live in `ReplicatedStorage.JankfireRemotes`. Every one is checked on the server: types,
  `Number.isFinite`, ranges, rate limits, alive.
- **Effects:** visual effects are Blender assets.
- **Sounds:** sounds stay as the `audio.js` functions named here, rendered to .ogg files.

---

## Modes at a glance

The **game modes** (`shared/modes.js` `GAMES`, plus `shared/royale.js:19`, `shared/island.js:40`):

| mode (id) | teams? | how you win |
|---|---|---|
| Deathmatch (`dm`) | no | everyone for themselves. first to 20 kills (15 with bots), or most kills when the 6 min clock runs out |
| Team Deathmatch (`tdm`) | RED vs BLUE | every kill is a point for your team. first team to 40 (30 with bots) |
| Tags (`tags`) | RED vs BLUE | kills drop dog tags. grab an enemy tag = +1 for your team, grab your own = they get nothing. first to 25 (20) |
| Plant & Defuse (`bomb`) | 5v5, attack / defend | attackers plant the bomb at A or B (hold F 3 s), defenders stop it or defuse it (5 s). first to 8 rounds, sides swap after 7. buy guns between rounds |
| Randomizer (`rand`) | no | deathmatch, but you get a random loadout every life. first to 20 (15) |
| Gun Game (`gun`) | no | one weapon at a time, 19 rungs. a kill with it moves you up, dying to melee knocks you down one. first kill with the spoon wins |
| Infection (`inf`) | survivors vs zombies | someone turns into a zombie 6 s in. whoever the zombies kill turns too. survivors win if anyone lasts 3 min |
| Zombies (`zm`) | co-op squad of 4 | endless rounds of zombies in a mall / school / hospital. buy doors, guns and colas. you lose when everyone is down |
| Spoons & Grapples (`spoons`) | no | spoons only, one hit kills, the grapple pulls harder, you run 1.6x. first to 20 (15) |
| Duck Rain (`duckrain`) | no | deathmatch, but rubber ducks rain from the sky and land as black holes. watch for the shadows. first to 20 (15) |
| Floor Is Lava (`lava`) | no | the ground floor burns and bounces you. stay on crates, roofs and walls. first to 20 (15) |
| One in the Chamber (`oitc`) | no | a revolver with one bullet (any hit kills) and a knife. kills give bullets. 3 lives, last one standing |
| Jank Royale (`br`) | no | blimp, umbrella, loot the floor, shrinking zone. last one standing. **phase 3** |
| Battle Island (`island`, BETA) | squads of 3 | the royale in squads. you go down instead of dying, and a squadmate can pick you up. last squad standing. **phase 3** |
| Board Game Night (`bgn`) | 4 seats | a party board game: roll the foam die, collect coupons, buy golden bread, and play a minigame every round. most bread wins. **phase 3** |

The **room types** (`shared/weapons.js:394` `MODES`). These are where you play, not what you play:

| room (id) | what it is |
|---|---|
| Online (`ffa`) | the one shared Online Quick Play room. real people only, no bots. the end-of-match vote picks the next mode |
| Bots (`bots`) | a room with bots. this covers OFFLINE matches, With Bots Quick Play and bots mode lobbies. bots fill the empty seats |
| Coop (`coop`) | one shared room: you and your friends vs endless waves of bots. no score limit |
| Training (`training`) | the Range: target dummies, infinite ammo, your 3 killstreaks always ready |
| Story: OVERDUE | hidden (`?story=1`), not in the menus. **phase 3+**, see the last section |

---

## How a match runs (the shared core)

### Rooms and how players get in
`roomFor(mode, ws, cfg)` decides which room you join (`server/room.js:4186`).
- **Online Quick Play:** one room with id `'ffa'`. Everyone online shares it.
  - It starts on `dm` on Islands (`room.js:365`).
  - It never gets bots, because `fillBots` is only called for `mode === 'bots'` (`room.js:543`).
- **With Bots Quick Play** (`cfg.lobby === 'qp'`):
  - You join a running public bots room that still has a bot you can replace.
  - If there is none, you get a new one on a random `dm` map (`room.js:4197-4203`).
- **Mode lobbies** (`cfg.lobby` = `bomb` / `br` / `zm` / `bgn`):
  - You join an open lobby room for that mode, or a new one is made (`room.js:4204-4210`, `server/lobby.js`).
- **OFFLINE (the hub):**
  - `cfg.priv` gives you a private bots room that nobody else drops into (`room.js:4224-4230`).
  - `cfg.hub` makes a single-mode match go back to that mode's lobby screen afterwards instead of voting
    (`server/hubback.js`).
- **Coop / Training:** Coop is one shared room `'coop'`. Training gets a room per join.
- **Room cap:** at most 300 rooms (`JF_MAX_ROOMS`). Past that, a join goes to the Online room.

The hub menu (`public/js/hubmenu.js:28-38`) shows these cards in this order: QUICK PLAY, PLANT & DEFUSE,
JANK ROYALE, ZOMBIES, BATTLE ISLAND (offline only: `lobby: null`), BOARD GAME NIGHT, TRAINING.
- ONLINE Quick Play has three choices: EVERYONE (the `ffa` room), + BOTS (the bots qp room) and CO-OP (the `coop` room).
- OFFLINE Quick Play lets you pick any of: `dm, tdm, tags, rand, gun, inf, spoons, duckrain, lava, oitc` (`hubmenu.js:81`).
  You also pick the map, whether bots are on, and a bot count of 1-12.

### Mode lobbies, the pre-game deck and READY (`shared/lobby.js`, `server/lobby.js`, `server/pregame.js`)
- `LOBBY = { wait: 60000, again: 10000, ready: 5000, respawn: 900, cap: { online: 16 } }`.
- Players needed for an Online lobby to start (`min`): bomb 2, br 2, zm 1, bgn 1.
- Zombies and BGN take 4 people at most (`cap: 4, squad: 4`).
- An Online Plant & Defuse lobby takes at most 10 people (`server/sdtune.js:53-56`).

**How a lobby runs:**
1. `lobbyInit(kind)` picks a random map the mode can be played on and starts the 60 s countdown
   (`server/lobby.js:22-30`).
2. While the countdown runs (`this.warm`), the room plays as `dm` on that map, with no score and no stats.
   - Warm-up deaths respawn after 0.9 s (`room.js:1526`).
   - `server/pregame.js` moves everyone onto a **deck** floating off the map's edge.
     - The deck is 26 x 18 m (78 x 54 studs). It sits 14 m (42 studs) above the highest spawn and at least 22 m
       (66 studs) past the play area (`shared/pregame.js:7-17`).
     - Nothing hurts there. Every combat message is dropped (`server/pregame.js` `BLOCK`).
     - FIRE does a harmless shove instead: 650 ms cooldown, 3.4 m (10.2 studs) reach, 12 m/s (36 studs/s) push,
       5 m/s (15 studs/s) lift.
     - Leave the deck and you're put back on it.
     - A big board shows the top 3 for this mode (`BOARD_STAT`).
3. READY (`{t:'ready'}`): once everyone has hit READY and there are enough people, the countdown jumps to 5 s
   (`lobby.js:102-106`).
4. When the countdown ends:
   - Nobody there: the room closes.
   - Online, not enough people: wait another 60 s ("waiting for players (n/min)").
   - Otherwise `startMatch()` runs. It sets `locked = true` (no new joiners), resets streaks, calls `startRound()` and
     fills bots (`lobby.js:118-128`).
5. After the match and its vote, the same room goes back to a 10 s lobby (`LOBBY.again`), so the group stays together.
- HUD: "PRE-GAME" callout, round line "pre-game · nothing hurts" (`public/js/main.js:2985`, `:2965`).

### The round (match) state, owned by the server
- `this.round = { target, ends, over, next, t0 }` (`room.js:369`, `startRound` at `room.js:3186`).
- The default length is `ROUND = { ffa: { kills: 20, time: 360 }, bots: { kills: 15, time: 300 } }` (`room.js:179`).
- The kill or point target comes from `TARGETS[roomType][game]` (`shared/modes.js:16, 94-95`). Modes then override it
  in `startModes` / `resetChaos` / `brRound`.

| game | target (ffa / bots) | clock |
|---|---|---|
| dm, rand, spoons, duckrain, lava | 20 / 15 kills | 360 s / 300 s |
| tdm | 40 / 30 team kills | 360 / 300 |
| tags | 25 / 20 confirms | 360 / 300 |
| gun | ladder length (19) | `GUNGAME.time` 600 s |
| inf | none (0) | `INFECT.time` 180 s |
| oitc | none (last one standing) | 360 / 300 |
| bomb | first to `BOMB.wins` 8 rounds | each round 110 s (map `roundTime` can override) + 15 s buy phase; match clock 1 h |
| br / island | none (last one / squad standing) | the zone plan + 90 s |
| zm | none | none (until everyone's down) |

`startRound()` (`room.js:3186-3208`) does this, in order:
1. Drop bots that are leaving.
2. Apply the vote (`resolveVote`).
3. Reset everyone's kills and deaths.
4. Set the new target and clock.
5. Reset the team scores, clear tags, reset zombies.
6. `startModes()` (gun game ladder, infection timer).
7. `assignTeams()`.
8. Set up the bomb (Plant & Defuse) or `resetWorld()` (everyone respawns).
9. Start Never Landed (`airStart`) and the royale (`brRound`).
10. Broadcast `{t:'round', start:1, ...roundInfo}`.

`tickRound()` runs every server tick (60 Hz, `server.js:202-203`). It checks, in this order (`room.js:3114-3132`):
1. A lobby countdown.
2. Board game night.
3. `over`: run the vote, then start the next round (or the next lobby).
4. Zombies (`zmRound`).
5. Plant & Defuse (`tickBomb`).
6. Gun game / infection (`tickModes`).
7. Team modes: `score >= target` for either team, or the clock ran out → `endRound`.
8. Lives (oitc), then the royale.
9. Otherwise FFA: the top killer reaches the target, or the clock runs out → `endRound`.

Snapshots go out at 20 Hz (`server.js:204`) and carry `round: roundInfo()` (`room.js:3096-3112`). That includes `left`
(ms), `target`, the team score `sc`, and the mode's own blocks (`inf`, `zm`, `bomb`, `warm`, `bg`).

### Teams
- `teamsOn()` is true in Online or Bots rooms when `GAMES[game].teams` is set (`room.js:384`).
- `TEAMS = { 1: RED #ff4f4f, 2: BLUE #4fa8ff }` (`modes.js:14`).
- `assignTeams()` (`room.js:387`):
  - Humans are sorted first, then players alternate between teams.
  - A party stays on one side (`server/partyteams.js`).
  - Your colour becomes the team colour.
  - It broadcasts `{t:'teams', game, list:[[id, team, color]]}`.
- A mid-match joiner goes to the smaller team, or joins their party's side (`joinTeam`, `room.js:425`).
- Client: the "YOU ARE RED" / "YOU ARE BLUE" callout (`main.js:1610-1622`).
- `friendly(a, b)` (`room.js:1350`) decides who can't hurt whom. Friendly damage is blocked in `hurt` / `hitBlocked`.
  - coop: bots vs humans.
  - zombies: everyone vs the zombies.
  - infection: same side.
  - battle island: same squad.
  - team modes: same team.

### Spawns and respawns
- `pickSpawn(forBot, who)` (`room.js:441-460`):
  - On Floor Is Lava, only safe spawns are used (`surfaces(map).spawns`).
  - In team modes on maps with `teamSpawns`, you use your side's spawns: Plant & Defuse picks by attack/defence, the
    other team modes use team 1 → `att` and team 2 → `def`.
    - Exception: maps flagged `teamSpawnsBomb` (Backrooms, Scary Forest) only use team spawns in Plant & Defuse.
  - For each spawn, the score = the distance to the nearest living enemy, + a random 0-15 m (0-45 studs).
  - On maps with `spawnSafe`, enemies in plain sight count at 0.3x distance, and the distance is capped at
    `spawnSafe` (so huge maps don't always pick the same corner).
  - The best score wins.
- **Respawn delay** (`room.js:1474`):
  - 2.5 s normally.
  - 4.5 s (`BOMB.respawn`) in Plant & Defuse with the economy off. With the economy on (the default) there is no
    respawn until the next round (`server/econ.js:269`).
  - 0.7 s for training dummies.
  - Killcam: a human with killcams on waits up to +9 s, unless they skip it with `{t:'respawn'}`. Skipping can never
    go below `minRespawnAt` (`room.js:1520`, `:3065-3069`).
- **Spawn protection:** 1.2 s after spawning, a human can't be hurt by others (`room.js:1362`).
- When the respawn time comes, `tick()` (`room.js:3930-3943`):
  - sets alive, HP 100, picks a new spawn;
  - calls `resetLife` (clears every status);
  - sends `{t:'spawn', p, q:seq}`, then `sendLoadout` (each mode's weapons).
  - The client teleports itself there. `seq` rejects old snapshots.

### Kills, scoring, streaks (`kill()`, `room.js:1465-1561`)
- **Who gets the kill:**
  - Void, cough, reset and car deaths go to whoever hit you in the last 10 s, with `via` = their weapon.
  - Sky ducks and lava go to whoever hit you in the last 6 s.
  - Otherwise nobody.
- **Team scoring:**
  - TDM: `score[killerTeam]++`.
  - Tags: `dropTag` (only enemy kills, only while the round is live).
- **Killstreaks:** a human's 3 picked streaks fill their tray (`{t:'streak', earned}`). Streaks are off in:
  - training, zombies, gun game, as a zombie, in a chaos kit with `noStreaks`, Plant & Defuse (`ECON.streaks:false`),
    the royale, and lobby warm-ups (`room.js:1504`).
- **Kill feed:** `{t:'kill', k, v, w, via, ...}` goes to everyone. The mode hooks run next: `chaosKill`, `modeKill`,
  `brKill`, `isleKilled`, `econOnKill`.

### End of match, scoreboard, the vote (`endRound`, `room.js:3133-3185`)
1. **End-screen order:** kills high to low, then deaths low to high. Each mode can re-sort (`modeSort`):
   - gun game by rung;
   - infection with the winning side on top;
   - oitc by lives left;
   - royale by placement.
2. **The winner:**
   - Team modes: the team with the higher score. A draw has no winner. In Plant & Defuse, round wins are the score.
   - FFA: the top player, but only with at least 1 kill or as the last one standing.
3. **The reward:** the winner gets a container roll + 50 xp if:
   - they have an account,
   - the room counts (Online needs 2+ humans; Bots needs 3+ bots),
   - they got at least 1 kill,
   - the match wasn't skipped.
4. Broadcast `{t:'round', over:1, winner, winTeam, sc, top, board, next}`, plus a personal `{t:'perf'}` report to
   each human.
5. The play of the round (`{t:'hl'}`) goes out 1.6 s later.
6. `startVote()` runs. Board game night and offline hub matches skip it (they use PLAY AGAIN / LOBBY instead,
   `hubback.js`).
7. **The vote** (`shared/vote.js`, `room.js:3261-3380`): `VOTE = { mode: 11000, map: 9000, reveal: 3000, cards: 4 }`.
   - **Stage 1, the mode:** 4 cards.
     - Only quick-play modes appear (`inQuickPlay`): no bomb, br, island or zm. bgn isn't in `GAME_ORDER` at all.
     - One card is always the **daily EVENT mode**. It rotates at midnight UTC through
       `['duckrain','spoons','lava','oitc','gun','inf','rand']`.
     - There is always a mix of team and FFA modes.
     - The mode you just played only shows up if there's nothing else.
     - A mode that was skipped with `/skip` doesn't show up at all.
   - **Stage 2, the map:** up to 4 maps from `mapsFor(game)`. The map you just played goes last in line.
   - **Who decides:** humans vote. Bots vote at a random moment (1.2-7 s), but they only break ties.
   - Once every human has voted, the stage closes after 2.5 s.
   - The next round starts `VOTE.mode + VOTE.map + VOTE.reveal` = 23 s after the end, and never before the
     highlight has finished.
   - In a one-mode lobby, only the map is voted on (`lobby.js:69-78`).
- **/skip:** typed in chat, it needs a majority of the humans within 30 s, then has a 60 s cooldown (`server/skip.js`).
  It ends the match at once, and the skipped match pays no container.
- **Never Landed:** a whole match without touching the ground, from a 3 s grace after each spawn.
  - The client reports `{t:'land'}`. The server also checks: feet on a box top for 2 snapshots in a row
    (`room.js:3209-3242`).
  - Off in lava, royale and warm-ups.
  - HUD: fail = "YOU TOUCHED GRASS" + `sfx.error`; success = `sfx.choir` flourish (`public/js/airborne.js`).

### Bots joining and filling (`room.js:599-626`)
- The room size is `cfg.bots` (0-12, default 5) + 1.
- Every human who joins takes a bot's seat. A bot that has to leave goes when it dies, or at the next round in round
  modes.
- When a human leaves, a bot comes back.
- Special sizes:
  - Plant & Defuse: 10 fighters (`sdtune.js:44-48`).
  - Royale: at least `BR.bots` = 15 (`JF_BR_BOTS`).
  - Battle Island: 3 x 6 - 1 = 17 bots.
  - Zombies: its own squad of 4 (`server/zmbots.js`).
  - Board game night: 4 seats.
- Online `ffa` never fills bots (except Online Plant & Defuse lobbies: `lobby.js:125`).
- The bot brain is `botThink` (`room.js:694`):
  - It picks the nearest visible target (non-visible ones count 2.5x farther).
  - It keeps a preferred range for its weapon. Melee bots run straight in.
  - It strafes and jumps, and grapples to chase or to save itself from the void.
  - It follows mode goals (`botGoal`, `room.js:922`): carry the bomb, defuse, grab tags.
  - It stays out of lava (`botLava`).

### Which maps each mode can use
`mapsFor(game)` (`shared/modes.js:73-77`) filters maps like this:
- WIP maps are hidden unless `JF_WIP_MAPS=1` / `?wip=1`.
- Zombie maps (`map.zm`) only go with zombies.
- `range` is never on the list.
- Royale-only maps only go with royale modes.
- Plant & Defuse needs `map.sites`. Every other mode skips the `_sd` versions.
- `GAMES[g].mapOk` can refuse a map (lava: `lavaOk`; royale: `map.royale`).
- `mapForGame` (`modes.js:79-83`) swaps a map for its `_sd` twin when you switch into or out of Plant & Defuse.

Computed today (`node` on `shared/map.js` + `mapsFor`):

| mode | maps |
|---|---|
| dm, tdm, tags, rand, gun, inf, spoons, duckrain, lava, oitc, bgn minigames | crate, platform, rooftop, suburb, warehouse, desert, bazaar, islands, skyline, backrooms, forest |
| bomb | platform_sd, rooftop_sd, suburb_sd, warehouse_sd, desert_sd, bazaar_sd, islands_sd, skyline_sd, backrooms (150 s rounds), forest (130 s rounds) |
| zm | deadmall (Dead Mall), school (Jankfield High), hospital (Second Opinion General) |
| br, island | jankburg (Jankburg) |

Lava's `lavaOk` passed for all 11 maps listed. **Unclear:** whether a future map would fail it. The rule is: at least
20% real floor, 100 m² of safe area and 4 safe spawns (`shared/lava.js:51`).

### What the server owns (every mode)
The server owns: HP and damage, who's on which team, kills and scores, the round clock and the win, respawn times and
spawn points, mode weapons (it refuses any `fire` / `hit` with a weapon you're not allowed: `allowed()`,
`room.js:3556`, `chaosHit` / `chaosFire`), objectives (tags, bomb, lives, ladder rung, infected list), the vote, and
bots.

The client owns its own movement only. It reports `{t:'s', p, v, y, x, w, g, f, q}` snapshots (`room.js:2908-2933`).
The server kills you if your feet go below `map.killY` (the void), and `OOB.secs` 3 s (+0.35 s grace) after you leave
`map.bounds`.

### Roblox notes for the core
- **One server Script owns the match:** a `MatchService` state machine `Lobby → Live → Over(vote) → Live`.
  - Keep its state in server tables. Mirror only what clients need, as attributes on `ReplicatedStorage.Match`:
    `Game`, `Map`, `Target`, `EndsAt` (use `workspace:GetServerTimeNow()`), `ScoreRed`, `ScoreBlue`, `Over`.
    Clients draw the clock from `EndsAt`. Don't send a countdown every tick.
- **Teams:** use the **Teams service** for tdm / tags / bomb. Make `Red` and `Blue` Team objects with
  `AutoAssignable = false`, and have the server set `player.Team`. In FFA modes, set `player.Neutral = true`.
  - Bots aren't Players. Keep a `team` field in the bot table and mirror it as a `Team` attribute on the bot model.
  - Run friendly fire through one `friendly(a, b)` function on the server, like the web code. Don't rely on
    Roblox's team-kill settings.
- **Spawns:** don't use auto-spawning `SpawnLocation`s (movement is client-owned). Put invisible anchored marker Parts
  in `Workspace.Map.Spawns` (with `TeamAtt` / `TeamDef` folders). Port `pickSpawn` on the server, then fire
  `JankfireRemotes.Spawn:FireClient(p, pos, seq)`. The client moves its own HumanoidRootPart. The server ignores
  snapshots with an old `seq` and treats the jump as allowed (no teleport flag).
- **Remotes to add:**
  - `Round` (server→all): start / over / scoreboard.
  - `Vote` (client→server `{i, stage}`): rate-limit 250 ms, check `i` is an integer in range.
  - `Ready`, `Respawn` (killcam skip).
  - `Use` (hold F, see Plant & Defuse).
  - `Teams`.
  - Keep the web message names as the payload `t` field, so the two codebases stay greppable.
- **Respawn timers on the server:** `os.clock()` is fine. Spawn protection is a server check in `hitBlocked`,
  not a ForceField.
- **Votes, `/skip`, Never Landed:** these are plain server logic and port 1:1. Use `TextChatService` to catch
  `/skip`.

---

## Free-for-all family

### Deathmatch (`dm`)
everyone for themselves. first to the kill limit.

**Rules**
1. Plain FFA. Everyone has their own loadout (primary, secondary, melee, item, 3 killstreaks).
2. The target is 20 kills (Online) / 15 (Bots), and the clock is 360 s / 300 s (`room.js:179`, `modes.js:16`).
3. You respawn 2.5 s after dying, with 1.2 s of spawn protection.
4. The match ends when anyone hits the target or the clock runs out (`room.js:3129-3131`). The winner is the most
   kills (ties go to fewer deaths), and needs at least 1 kill.
5. Killstreaks, items and grapple are all on.

**Bots:** they hunt the nearest target, keep their weapon's preferred range (sniper 25-60 m, shotgun 3-9 m, default
7-22 m: `room.js:719`), strafe, jump and grapple.

**HUD and sounds**
- Round line: "first to N · m:ss" (`main.js:2969`). Round start callout: "ROUND START".
- End: "YOU WIN" / "<name> wins".
- **Unclear:** the round-start sound for DM. `sfx.roundStart` is only used by zombies.

**Roblox notes:** this is the base every other mode extends. Build it fully on Rooftop first: target, clock, end
screen, vote, respawn, spawn picking. Everything below adds to it.

### Randomizer (`rand`)
everyone gets a random loadout every life. first to the kill limit.

**Rules**
1. Deathmatch rules and targets (20 / 15).
2. Every spawn, `randomLoadout()` (`room.js:405-410`) picks one random weapon per slot (`primary`, `secondary`,
   `melee`) from every weapon in that slot without `modeOnly`. You keep your own item.
3. The server sends `{t:'loadout', lo}` with `p.forced = true` (`room.js:421-423`). When the mode ends,
   `{t:'loadout', lo:null}` gives your own loadout back.
4. Bots pick a random gun from `BOT_GUNS` every life (`room.js:419`).

**Server checks:** **gap / unclear:** the server does not store the rolled loadout, so it can't check that a hit came
from it. `onHit` / `onFire` only check that the weapon is in a loadout slot (`room.js:2031`). The web game trusts the
client here.

**Roblox notes:** store the rolled loadout per player on the server and refuse `Fire` / `Hit` for anything else.
That's one table lookup.

### Spoons & Grapples (`spoons`)
spoons only (one hit kills) and the grapple pulls harder. swing in and bonk.

**Rules** (`modes.js:88`)
1. The kit is `{ slots: ['knife'], noItem, noStreaks, oneHit, speedMul: 1.6 }`. The knife wears the spoon look
   (`SPOON_LOOK = 'knife_spoon'`, `modes.js:101-102`).
2. Any knife hit kills: `dmg = max(dmg, target HP)` (`room.js:1451`).
3. You run 1.6x on top of the knife's own `speedMul 1.1` (`public/js/weapons.js:40`, `:1470`).
4. The grapple pull is x1.35 (`hookMul`). The client uses it in `classicRopeStep(..., G.hookMul)`
   (`public/js/player.js:162`), bots in `room.js:1065`.
5. Targets are 20 / 15 kills, with DM's clock.
6. The server refuses any weapon not in the kit (`chaosHit` / `chaosFire`, `room.js:3696-3712`). Items and streak
   deploys are refused too (`room.js:1127`, `:2981`).

**Bots** (`botChaosThink` / `botChaosFire`, `room.js:3833-3877`):
- They run straight in (melee strafe 0.3, speed = the weapon's `speedMul`).
- They grapple toward targets more than 12 m (36 studs) away, every 0.5 s.
- They swing when within knife range + 0.9 m.

**HUD and sounds:** intro "SPOONS & GRAPPLES" + `sfx.ting` (`public/js/chaos.js:269`). The streak tray is hidden
(`chaos-nostreaks` body class).

**Roblox notes:** the knife (WEAPONS.md) with a `oneHit` mode flag on the server; walk speed x1.6 on the client
(the server should also check its speed cap); the grapple multiplier is a replicated attribute that the client rope
code reads.

### One in the Chamber (`oitc`)
a revolver with one bullet (any hit kills) and a knife. kills give bullets. 3 lives, last one standing wins.

**Rules** (`modes.js:91`, `room.js:3679-3772`)
1. The kit is revolver + knife. Also: `noItem`, `noStreaks`, `noReload` (the client never reloads: `weapons.js:699`),
   and `noTbag` (the t-bag explosion is off: `room.js:2956`).
2. `lives: 3`, `bullets: [1, 3]`: you spawn with 1 bullet and can hold 3 at most.
3. **A revolver hit always kills:** 999 damage (`room.js:3704`). The knife does its normal damage.
4. **Bullet counting** (`oitcShot`, `room.js:3713-3724`):
   - A shot sends a `hit` (if it hit someone) and a `fire`, up to 250 ms apart. Both count as one bullet.
   - No bullets, or less than 300 ms since your last shot, means refused.
   - The server sends `{t:'oitc', b, l, out}` back each time.
5. **On a kill:** the victim loses a life and their bullets go to 0. The killer gets +1 bullet, capped at 3.
   Self deaths cost a life too.
6. **Out of lives:** you're out. `respawnAt = Infinity`, and your account (or your name, for guests) goes into
   `oitcOut`, so reconnecting doesn't give you new lives (`room.js:3726-3737`).
   - Chat line: "<name> is out of lives".
7. A late joiner gets as many lives as whoever has the fewest, at least 1.
8. **End:** the round ends when only one is left (once at least 2 were in it), or when the clock runs out (360 / 300 s)
   (`tickLives`, `room.js:3754`). End order: lives left, then kills.
9. RESET is off in oitc (`main.js:310`).

**Bots** (`room.js:3833-3877`):
- They use the knife when out of bullets or within 2.5 m (7.5 studs), otherwise the revolver.
- They only shoot within 26 m (78 studs), or 40 m (120 studs) on hard.
- They miss on purpose (easy ~70%, normal ~35%, hard ~14%), and a miss still costs the bullet.
- They hold fire for 2.5 s after their own spawn and 1.5 s after the target's spawn.

**HUD and sounds** (`public/js/chaos.js:183-260`):
- BULLETS pips and LIVES hearts (♥/♡).
- "+1 BULLET · n IN THE CHAMBER" + `sfx.chamber`.
- "OUT OF LIVES", then spectate: over-the-shoulder of a live player; click / Space / → for the next one, ← for the
  previous. The bar reads "OUT OF LIVES · watching X · ...".
- Round line "last one standing · N left · m:ss". Intro "ONE IN THE CHAMBER" + `sfx.chamber`.

**Roblox notes:**
- The server owns bullets and lives. Put `Bullets` and `Lives` attributes on the Player for the HUD.
- Keep the "hit + fire = one bullet" pairing, or better, send a single `Fire` remote that carries the hit claim.
- Spectating: set `workspace.CurrentCamera.CameraSubject` to the target's Humanoid with a scriptable offset camera.
- The "out" list is keyed by `UserId`.

### Duck Rain (`duckrain`)
deathmatch, but rubber ducks rain from the sky and land as black holes. watch for the shadows.

**Rules** (`modes.js:89`, `:99`, `room.js:3774-3806`, holes `room.js:2484-2546`)
1. Deathmatch with 20 / 15 kills and DM's clock. Normal loadouts and streaks.
2. **Drop timing:**
   - First drop 3 s after the round starts.
   - Then every `every` = lerp(2.4 s → 1.1 s, k).
   - k = max(share of the clock used, top kills / target).
3. **Drop size:**
   - Ducks per drop = round(lerp(1.5 → 3.5, k) x size + random ±0.5), at least 1.
   - size = clamp(√(total floor area / 9000 m²), 0.5, 1.8). Floor area comes from `shared/lava.js` `surfaces`.
4. **Where each duck lands:**
   - Half land 2-14 m (6-42 studs) from a random living fighter (`near: 0.5`).
   - The rest land on a random exposed top, weighted by area.
   - A ray from 20 m (60 studs) above the highest top finds where it lands. A roof keeps you dry.
5. **The fall:**
   - Spawned at landing y + 46 m (138 studs), capped below the ray start.
   - Falls straight down: starts at 6 m/s (18 studs/s), duck gravity 22 m/s² (66 studs/s²).
   - Sky ducks never home in.
   - The server broadcasts `{t:'skyduck', id, p:landing, ms:eta}` (`room.js:3804`).
6. **The black hole:** it lands, or after 8 s, and becomes a hole with `DUCKRAIN.hole`:
   - R 12 m (36 studs), pull 40, time 2.6 s.
   - Blast at the end: R 9 m (27 studs), kb 30 m/s (90 studs/s), 45 damage. These are the duck's own `blastR`,
     `blastKb`, `blastDmg` (`shared/weapons.js:247-255`).
   - If the duck lands on a player, it sticks to them and the hole rides them (they take 1 damage per 0.1 s).
   - Every 0.1 s, everyone within R gets pulled with s = (40·(1 − d/R) + 8)·0.1·min(1, d/1.5), + lift 1·min(1, d/1.5)
     (3 studs/s scale), and takes 3 damage if within 2 m (6 studs).
   - A sky duck's hole belongs to nobody, but it works on everyone. A shield bubble blocks it.
7. **Kill credit:** goes to whoever hurt you in the last 6 s, else nobody (`room.js:1484`). Kill feed: "got flattened
   by a sky duck" / "[weapon] X under a sky duck" (`main.js:1814-1815`).

**Bots:** the normal DM brain. **Unclear:** there's no special duck dodging that I found.

**HUD and sounds** (`chaos.js:149-180`):
- A black shadow disc + a blinking red ring at the landing spot. It grows over `ms`.
- `sfx.whistle(p, secs)` plays as each duck falls.
- "LOOK UP" if you're within 3.5 m (10.5 studs) horizontally and 4 m (12 studs) vertically of a landing spot.
- Intro "DUCK RAIN" + 3x `sfx.squeak`. Holes use the duck item's sounds (`sfx.hole`, `holePop`).

**Roblox notes:**
- Simulate each sky duck on the server: a falling point with gravity, raycast each step, or just schedule the landing
  at `eta`, since it falls straight down.
- Tell clients the landing point + eta with one remote. The client draws the shadow (a Blender decal/disc asset) and
  a falling duck mesh.
- The hole pull is a knockback stream: send it to each affected client every 0.1 s, like `kb`, or replicate the hole
  (pos, R, pull, until) and let each client pull itself. **Note:** if the client does the pull, the server must still
  do the damage.
- Cap live holes (Part count).

### Floor Is Lava (`lava`)
the ground floor burns. stay on crates, roofs and walls. bhop and grapple.

**Rules** (`modes.js:90`, `shared/lava.js`, `room.js:3808-3831`, client `chaos.js:40-115`)
1. Deathmatch with 20 / 15 kills and DM's clock. Only maps where `lavaOk(map)` is true (`mapOk`).
2. **Which surfaces are lava:** `surfaces(map)` works this out from the boxes alone, and caches it.
   - It samples every exposed box top on a 2.5 m grid.
   - The **ground floor** is the lowest height bin that holds at least half as much area as the biggest bin.
   - Lava = every box whose top is at most `base + 0.5 m`, plus all shaped terrain.
   - Everything higher is safe.
   - Safe spawns: each map spawn moves to the nearest safe spot (spots are 1.5 m apart, fully supported). It tops up
     to 6 spawns, picking the spots farthest apart.
3. **Touching the lava** (`LAVA = { dmg: 20, burn: 1.4, burnDmg: 4, every: 0.4, hop: 11.5 }`):
   - 20 damage.
   - A burn for 1.4 s, ticking 4 damage every 0.3 s.
   - A bounce straight up at 11.5 m/s (34.5 studs/s).
   - At most once per 0.4 s.
4. **Who detects it:**
   - The client sees its own feet on lava (`lavaStep`, `chaos.js:96`). It bounces itself and sends `{t:'lava'}`.
   - The server believes it only if there's lava within 6 m (18 studs) below your feet now, or 0.1 s ago
     (`room.js:3824`).
   - The server also checks snapshots on its own: feet on lava for more than 0.12 s → it applies the touch itself and
     sends `kb` (`room.js:3815-3816`).
   - Bots are checked on the server.
5. Lava deaths go to whoever hurt you in the last 6 s. Kill feed: "touched the floor" / "into the lava".
6. No Never Landed here.

**Bots** (`botLava`, `room.js:3878-3898`):
- They look 1.4 m ahead for lava under their next step and stop at the edge. 60% of the time they grapple toward
  their target (+4 m up).
- In lava, or falling toward it: they jump and grapple to the nearest safe spot within 45 m (135 studs).

**HUD and sounds** (`chaos.js:96-127`, `:268`):
- The lava floor mesh uses `liquidMaterial('lava')`, plus a lava glow and ember / bubble particles near the camera.
- On a touch: a random "HOT HOT HOT" / "OW OW OW" / "LAVA!" / "NOT THE FLOOR", `sfx.sizzle`, camera shake 0.35,
  a red flash and steam.
- Intro "THE FLOOR IS LAVA" + `sfx.rumble`, then `sfx.sizzle`.

**Roblox notes:**
- Precompute `surfaces` once per map on the server, port `shared/lava.js` as a ModuleScript. Or simpler: tag the
  ground-floor Parts with CollectionService `LavaFloor` in Studio, and give the lava look as a Blender mesh / texture
  laid over those Parts.
- The client checks its floor with a downward raycast (`FloorMaterial` isn't reliable on boxes). On lava it bounces
  itself and fires `Lava`.
- The server checks the claim with its own raycast down (6 m / 18 studs) and owns the damage and the burn. Don't use
  `Touched` (unreliable at speed).

---

## Team modes

### Team Deathmatch (`tdm`)
red vs blue. first team to the kill limit.

**Rules**
1. Teams split evenly (see the core). Team colours replace player colours.
2. Every kill on an enemy while the round is live: `score[killer.team]++` (`room.js:1486-1487`). Void kills credited
   through `via` count too.
3. The target is 40 (Online) / 30 (Bots) team kills. The clock is 360 / 300 s.
4. The end is `score >= target` or time out (`room.js:3126`). An equal score is a DRAW: no winner and no roll.
5. Normal loadouts, streaks and items.

**Bots:** the DM brain, skipping teammates (`botTarget`, `room.js:664`).

**HUD:**
- Team bar: "RED n | TEAM DEATHMATCH · to 40 · m:ss | n BLUE" (your side highlighted) (`public/js/objective.js:108-118`).
- Callout "YOU ARE RED/BLUE".
- End: "RED WINS 40 - 31 (YOU)" in the team colour, or "DRAW a - b" (`main.js:2996-2999`).

**Roblox notes:** Teams service with `Red` / `Blue` (BrickColor close to `#ff4f4f` / `#4fa8ff`). The score lives in
server variables, mirrored to `Match` attributes. On Rooftop, use its `teamSpawns` (`att` = team 1, `def` = team 2).

### Tags (`tags`)
kills drop tags. grab enemy tags to score, grab your own team's to deny them.

**Rules** (`room.js:3383-3412`)
1. A kill on an enemy during a live round drops a **tag**.
   - It lands on the floor under the body: a ray 60 m (180 studs) down from 1 m above the body.
   - Over the void, it lands under your last ground position, or else under the killer.
   - It is placed at floor + 0.9 m (2.7 studs) (`dropTag`).
   - `{t:'tag+', id, p, team}` tells everyone.
2. A tag lasts `TAG_LIFE` = 30 s, then `{t:'tagx'}` removes it.
3. Every tick: any living player whose centre (feet + 0.9 m) is within 1.9 m (5.7 studs) of a tag picks it up.
   - Enemy tag → **confirm**: +1 to your team, only while the round is live.
   - Your team's tag → **deny**: it's just gone.
   - `{t:'tagx', id, by, k:'confirm'|'deny'}`.
4. Kills alone score nothing. Target 25 (Online) / 20 (Bots). Clock 360 / 300 s. Draws are possible.

**Bots:** they walk to the nearest tag within 45 m (135 studs) when not fighting (`botGoal`, `room.js:952-956`).

**HUD and sounds:**
- The tag is a small team-coloured plate (0.34 x 0.5 x 0.05 m = 1.02 x 1.5 x 0.15 studs) in a white frame. It spins
  3 rad/s and bobs ±0.15 m (0.45 studs) (`objective.js:63-75`, `:105`).
- "KILL CONFIRMED +1" + `sfx.cash`, or "KILL DENIED" + `sfx.ting` (`main.js:1626-1629`).
- Objective line "grab enemy tags to score · grab your team's to deny".

**Roblox notes:**
- Each tag is an anchored, non-colliding, `CanQuery = false` Part or Model (a Blender dog tag asset). It is spawned by
  the server; the client spins and bobs it.
- Check pickups on the server with a distance check in `Heartbeat` (not `Touched`).
- Cap tags: they expire in 30 s anyway.

### Plant & Defuse (`bomb`)
5v5. attackers plant the bomb at A or B (hold F). defenders stop them or defuse it. buy guns between rounds.

This mode has two layers: the **bomb rules** (`room.js:3414-3530`) and the **economy / Search & Destroy layer**
(`server/econ.js`, `shared/econ.js`, `server/sdtune.js`, `shared/sdgun.js`, `shared/tactical.js`, bots in
`server/econai.js`). The economy is on by default (`JF_ECON=0` turns it off). Bomb numbers: `BOMB`,
`shared/modes.js:17-21`.

**The match**
1. **Rounds:** first team to `wins: 8` round wins.
   - Team 1 attacks first.
   - After round 7 (`swapAfter`), sides swap: "SIDES SWAPPED" / "HALF TIME". So there are at most 15 rounds.
2. **Round timing:** each round starts with a 15 s **buy phase** (`ECON.buyTime`).
   - Everyone is held inside a spawn **barrier zone**: the box around their side's team spawns, padded 4 m (12 studs),
     2 m below, 10 m above. The server puts you back if you go more than 0.75 m (2.25 studs) past it (`econHold`).
   - Then "GO GO GO": the round clock runs 110 s (`roundTime`; Backrooms 150 s, Scary Forest 130 s).
   - 5 s (`between`) after a round ends, the next one starts.
3. **The bomb is given** to a random living attacker, humans first (`giveBomb`). If nobody can take it, it's dropped
   at the attackers' spawn.
4. **Carrying the bomb:**
   - The carrier dies or leaves → the bomb drops at their feet (floor + 0.15 m). Over the void it goes to another
     attacker.
   - Any attacker within `pickup` 1.7 m (5.1 studs) picks it up.
   - A carrier standing still for 15 s (moving less than 1.5 m / 4.5 studs) drops it if a teammate is alive. They
     can't pick it back up for 8 s, and not until they've moved 2 m (6 studs).
   - A dropped bomb with no live human attacker goes to a bot after 20 s.
5. **Plant:**
   - The carrier inside a site box holds F. A site counts from 1 m below its floor to 4 m above its top (`siteAt`).
   - The client sends `{t:'use'}` about every 250 ms while F is held.
   - The plant takes 3 s (`BOMB.plant`).
   - It is cancelled if more than 600 ms passes without a `use`, if you move more than 1.6 m (4.8 studs) from where
     you started, if you die, or if you leave the site.
   - On success: the bomb sits at your feet + 0.1 m. `fuse` 35 s starts. The planter gets +10 xp.
6. **Defuse:**
   - Any defender in the defuse **cylinder** holds F (`canDefuse`, `modes.js:64-67`). The cylinder is 2.6 m
     (7.8 studs) flat distance, the bomb 1.6 m below to 4.6 m above your feet, +0.6 m slack while holding.
   - It takes 5 s (2.5 s with the Defuse Pliers kit). The same hold rules apply.
   - Success: the defenders win the round ("defused"). The defuser gets +15 xp.
7. **Explosion:** 18 m (54 studs) radius, 220 damage, kb 60 m/s (180 studs/s) (`room.js:3509-3512`). The attackers
   win ("exploded").
8. **Clock runs out** with no plant → the defenders win ("time").
9. **Elimination** (economy on): a side with nobody alive loses ("elim"). Once the bomb is planted, only the defenders
   running out ends it early (`econ.js:802-808`).
10. **Respawns:** none during a round. The dead come back at the next round (`econOnKill`: respawn = +1 day).
    - A mid-round joiner who arrives after the buy phase sits out.
    - With the economy off: 4.5 s respawns.
11. The match ends when a team reaches 8. A drawn match is impossible at 8; **unclear:** what happens if the 1 h match
    clock runs out (`room.js:3200`, it never does in practice).

**The economy** (`shared/econ.js`; the Search & Destroy overrides at `:173-219` win)
- **Credits:**
  - Start 800, max 9000.
  - The half: everyone back to 800, and the loss streaks reset.
  - Round win pays: elim / time 3000, defused / exploded 3300.
  - Loss ladder: 1400, 1900, 2400, 2900, 3400 for the 1st to 5th loss in a row.
  - The planter gets +300 when the plant completes. Every attacker gets +600 for a lost round in which the bomb was
    planted. The defuser gets +300.
  - Attackers who hide out the clock without planting get no loss bonus (`ECON.timeSurvivorBonus: false`).
- **Kill rewards** per weapon (cheap guns pay more): pistol 300, sawnoff 600, smg / redline 600, shotguns 900,
  AR / burst / lever / DMR / LMG 300, sniper 100, knife 1500.
- **The shop** (the tight S&D arsenal, `SD.cats`):

  | category | items and prices |
  |---|---|
  | SIDEARMS | pistol 200, sawnoff 300, akimbo 500, revolver 700 |
  | SMGS | smg 1250, redline 1600 |
  | SHOTGUNS | shotgun 1100, autoshot 2000 |
  | RIFLES | lever 1800, burst 2250, ar 2900 |
  | SNIPERS + LMG | dmr 2500, sniper 4700, lmg 3200 |
  | UTILITY | goggles flash 200 (2 max), smoke 300, frag 300 |
  | ARMOUR | vest 650, vest + bucket helmet 350 extra, Defuse Pliers 400 (defenders only) |

  - A refill is 25% of the price.
  - Default kit at each half and after dying: pistol + knife (free).
- **Armour:** 100 points. It takes 45% of body hits (head: 40% only with the helmet; blasts 35%), minus the weapon's
  `pen`.
- **Gear drops on death:** everything except the default knife lands on the floor. Pick-up 2.2 m (6.6 studs), auto
  pick-up 1.3 m (3.9 studs). At most 48 drops on the map.
- **Off in this mode:** no grapple (`hookOff`), no killstreaks.
- **Damage:** per-zone S&D damage with range falloff (`sdgun.js` `SDG`: head / body / legs). Spray patterns and
  moving spread are in `shared/tactical.js`. The weapon numbers belong in WEAPONS.md.

**Bots:**
- Without the economy (`botGoal`, `room.js:922-950`): the carrier walks a site lane (`map.nav`) and plants. Attackers
  head to a site, or guard a planted bomb. Defenders patrol a random site and rush a planted bomb to defuse it.
- With the economy (`server/econai.js`): buying (full buy / force buy lists, `econ.js:28-29`), executes, holds,
  rotations and retakes. Per-bot skill comes from `server/sdskill.js`.

**HUD and sounds** (`main.js:1630-1648`, `objective.js`, `public/js/econ.js`):
- Sites: a yellow "A" / "B" sprite visible through walls + a floor outline.
- The bomb model: a box + 3 red sticks + a blinking light that speeds up toward the end of the fuse. A "B" marker over
  the carrier, shown to attackers only.
- Callouts:
  - "YOU HAVE THE BOMB"
  - "ROUND n · ATTACK/DEFEND" (or the economy's own banner)
  - "BOMB PLANTED AT A" + `sfx.ting`
  - "BOMB DEFUSED" + `sfx.kill`
  - "RED WINS THE ROUND" + `sfx.kill` for the winning side
  - "GO GO GO" + `sfx.whoops` + `sfx.thunk` when the barriers drop
- Explosion: shake 1.
- Objective line: "BOMB PLANTED AT A · 0:21 · DEFUSE IT (hold F at the bomb)" etc. (`objective.js:121-131`).
- Team bar "ROUND n / 15 · ATTACK · first to 8".

**Roblox notes:**
- Build it in two steps.
  - **Step 1:** the bomb rules only (like `JF_ECON=0`), with 4.5 s respawns, on `rooftop_sd`.
  - **Step 2:** the economy (buy menu UI, credits, drops, armour, no respawn).
- **Hold F:** the client fires `JankfireRemotes.Use` every 0.25 s while F is held (no payload). The server keeps
  `useT`, start position and start time. Port `tryUse` / `tickBomb` as is. A `ProximityPrompt` with `HoldDuration` is
  tempting, but it can't express the cylinder, the "stay put" rule or the server-side timing. Use it only for the
  prompt look, if at all.
- **Sites:** invisible Parts named `SiteA` / `SiteB` in `Workspace.Map.Sites`. Check "inside" with the min/max box
  maths from `siteAt`, not `Touched`.
- **The bomb:** a server-owned anchored model, or welded to the carrier's back. Show the carrier marker to attackers
  only (a BillboardGui enabled per client).
- **Barrier zones:** the server clamps positions and fires `ezone`. The client must accept the server's correction.
- **Elim checks** run every tick on the server. Bots and players count the same.

---

## Ladder and infection

### Gun Game (`gun`)
one weapon at a time. a kill moves you up the ladder, a melee death knocks you back. first kill with the spoon wins.

**Rules** (`modes.js:24-49`, `room.js:3546-3641`)
1. **A new ladder every match** (`rollLadder`). It takes 10 random guns from `LADDER_POOL.guns`, then 5 from `silly`,
   then 3 from `melee`, then the `knife` (in its spoon look) last: 19 rungs.
   - Weapons that sat out the last match are picked first. Each group is shuffled.
   - The whole room (bots too) shares one ladder.
   - The fallback / old-client ladder is `LADDER` (`modes.js:28`).
   - The pools:
     - guns: ar, smg, redline, shotgun, minigun, shredder, revolver, marbles, sniper, burst, lmg, dmr, lever,
       autoshot, nailgun, pistol, akimbo, sawnoff, laser
     - silly: bow, chicken, bloodcross, banana, cards, bowling, tennis, cart, snowball, taser, slipper
     - melee: slapper, bread, scales, katana
2. Everyone starts on rung 0 (`JF_GG_START` for testers). Your only weapon is your rung's weapon (`modeWeapon`).
   - The server refuses any other weapon (`allowed`). Items and streak deploys are refused.
   - The server sends `{t:'modew', w}`. `{t:'gg', all, l}` gives everyone's rungs + the ladder.
3. **Moving up:** a kill **with your current rung's weapon** moves you up one (`kw` = `via || w`, so knocking someone
   into the void with it counts). You get the next weapon straight away.
   - `{t:'gg', id, n, k:'up'|'last'|'win'}`.
4. **Moving down:** dying to any `kind: 'melee'` weapon knocks **the victim** down one rung, never below 0
   (`k:'down'`, "HUMILIATED").
5. **Win:** the first kill with the last rung (the spoon) ends the match. The target is set to the ladder length.
   - Clock: `GUNGAME.time` 600 s. On time, the highest rung wins (ties go to kills).
6. A mid-match joiner starts at rung 0. Bots move up the ladder the same way.
7. No killstreaks.

**Bots:** they hold whatever their rung is (`modeLoadout`), and the brain adapts to it: melee rungs run in, bow /
cards / blood cross rungs have their own `botFire` branches (`room.js:1007-1024`). Bots move faster with a weapon
that has `speedMul` (`modeSpeed`).

**HUD and sounds** (`public/js/gungame.js`):
- Top bar "7/19 · <weapon name in its colour> · next: X" + a pip per rung + a leader marker.
- Callouts:
  - "<WEAPON> · n/19" + `sfx.rankUp`
  - "YOU HAVE THE SPOON · ONE KILL WINS" / "<NAME> HAS THE SPOON" (`sfx.rankUp` / `sfx.ting`)
  - "HUMILIATED" + `sfx.sad`
  - "NEW LADDER" + a chat line naming the first 4 rungs
- End rows show "rung n/19" or "SPOON KILL".

**Roblox notes:**
- Needs all 19+ pool weapons to be ported. Until then, ship a fixed ladder of whatever exists (the web has the same
  knob: `JF_GG_LADDER=cart,knife`).
- Server: a `Rung` attribute per player. Swap the equipped Tool on the server when the rung changes, and refuse any
  other Tool's `Fire` / `Hit`.

### Infection (`inf`)
someone starts infected. whoever the zombies kill turns into one. survive the timer.

**Rules** (`modes.js:50-52`, `room.js:3643-3677`)
1. `INFECT = { time: 180, delay: 6, two: 8, hp: 200, color: '#7dff4f' }`.
2. Everyone starts human with their own loadout. **6 s in**, patient zero turns. With 8 or more fighters, two do.
   - It waits until there are at least 2 fighters.
   - `{t:'infect', id, first:1}`.
3. **Zombies:**
   - Their only weapon is the **Zombie Claw**: melee, `cd 0.45`, range 2.6 m (7.8 studs), cone 0.85, 55 damage,
     kb 8 (24), kbUp 3 (9), `speedMul 1.3` (`shared/weapons.js:324-328`).
   - They have **200 HP** (`modeLoadout`). Overheal doesn't fade for them (`room.js:1422`).
   - Two swipes kill a survivor.
4. **Turning:** after patient zero turns, any survivor death (any cause) makes them a zombie (`modeKill` → `infect`).
   They respawn as one.
   - A survivor who dies before patient zero turns stays human.
   - A late joiner after the infection has started spawns as a zombie.
5. **Sides:** same-side hits don't land (`friendly`). Survivors keep streaks and items; zombies have none.
6. **End:**
   - No survivors left → **THE INFECTED WIN**.
   - The clock (180 s) runs out with anyone alive → **SURVIVORS WIN**.
   - If every zombie leaves, someone else turns at once.
   - End screen: the winning side on top. Its best player only takes the round if they got a kill.
7. One survivor left → `{t:'infect', last}`.

**Bots:**
- Zombies and survivors only target the other side.
- Zombie bots grapple at any target more than 6 m (18 studs) away (`b.inf ||` in the grapple check, `room.js:777`),
  and run in with the claw (melee pref range).

**HUD and sounds** (`public/js/infection.js`):
- When you turn: a green flash + huge wobbly "YOU ARE INFECTED" with a subtitle ("patient zero: infect them all" /
  "claw the survivors: two swipes each"), `sfx.infected` + `sfx.groan`, shake 0.8.
- "<NAME> IS PATIENT ZERO", "YOU ARE THE LAST SURVIVOR" + `sfx.ting`.
- Zombies are drawn as green-tinted mannequins that groan now and then within 45 m (`sfx.groan(pos)`).
- A green haze while you're a zombie.
- Bar:
  - before patient zero: "someone turns in N... spread out"
  - as a survivor: "SURVIVE m:ss · N survivors · M zombies"
  - as a zombie: "YOU ARE A ZOMBIE · N left to infect · m:ss"
  - plus a zombie-share meter.
- End title "THE INFECTED WIN" (green) / "SURVIVORS WIN".

**Roblox notes:**
- Don't use Teams (sides change mid-round). Use an `Infected` attribute per player and bot, set by the server. The
  client tints its rig green from the attribute.
- The claw is a server-validated melee Tool that's only given to the infected.
- Zombie max health 200: the server sets the HP. The client walk speed is x1.3, and the server checks its speed cap
  against it.

---

## Co-op and survival

### Zombies (`zm`), phase 2-3 (big)
co-op vs endless rounds of zombies. hits and kills earn credits: look at a door, wall gun or the crate and hold F to
buy. hold F on a downed friend to revive them.

The big pieces: `shared/zombies.js` (rules, numbers, `zmTarget` = what F does), `shared/zmshop.js`,
`shared/zmlimbs.js`, `server/zombies.js` (round loop, nav grid + flow fields, downs and revives),
`server/zmextra.js` (planks, drops, Cheat Machine, loadouts), `server/zmlimbs.js` (limbs + special zombies),
`server/zmboss.js`, `server/zmbots.js` (squad bots), `server/zmshop.js` (colas, Warranty Voider, grapple charges).
Client: `public/js/zombies.js`, `zm*.js`.

**Getting in and losing**
- A squad of 4: people + bots fill the empty slots (`SQUAD.size`, `zmbots.js`).
- Maps: Dead Mall, Jankfield High, Second Opinion General.
- The Online room hands 5+ people their own zombies lobby (`room.js:4237-4244`).
- Everyone is on team 1. No killstreaks (only drops set them off). No `respawn`. RESET is off.
- **Game over** when every squad member is down or dead → the end screen (`zmover`: kills, headshots, downs, revives,
  credits) and the vote (`zmGameOver`, `zombies.js:324`). There's no time limit.

**Rounds** (`zmRound`, `zombies.js:242-284`)
- 6 s before round 1, 10 s between rounds. "ROUND n" / "ROUND n SURVIVED" + `sfx.roundStart` / `sfx.roundEnd`.
- **Count** (`zmCount`):
  - Solo: 6, 9, 13, 18, 24, then +3 a round.
  - Each extra player adds 75%, up to 4 players.
- **HP** (`zmHp`): 40 + 22 per round up to round 9, then 216 x 1.09^(r−9).
- **Gait** (`zmGait`):
  - shamblers 2.6 m/s (7.8 studs/s)
  - runners 6.8 m/s (20.4) from round 4
  - sprinters 9.2 m/s (27.6) from round 9
- **Spawning:**
  - At most 14 + 6 per extra player alive (cap 24).
  - Spawn gap max(450, 2000 − 150·(r−1)) ms, x0.75 with more than one player.
  - Zombies only spawn at the windows of **open** areas.
- **Difficulty** (Bots room `cfg.diff`): easy hp x0.85, speed x0.9, damage x0.75; hard x1.2 / 1.12 / 1.3.
- **Claws:**
  - 15 damage in round 1, +1 a round, at most 34.
  - Swipe cd 1.1 s, windup 0.35 s.
  - Reach 1.5 m (4.5 studs), hit 2.2 m (6.6), up 2.6 m (7.8): you can't hide on a crate.
  - 0.45 s iframe after a claw lands.
- **Movement:** zombies walk a 1 m nav grid with a flow field per player (`buildNav`, `flow`). They tear planks off
  windows: 6 planks per window, 1.3 s each (0.85 s for runners).
- **Specials** (`shared/zmlimbs.js` `ZT`):
  - CHONK (from round 5, 3.5x HP, pops on death)
  - ANKLE BITERS (from round 3, packs of 3)
  - HARD HAT (from round 4, the hat eats headshots)
  - SCREAMER (from round 6, speeds up the zombies near it)
  - Share of specials: 7% per round past 2, capped at 40%.
- **Mini boss every 5 rounds:** THE FLOOR MANAGER (charges, calls a meeting), then THE MASCOT (jumps, floor ripple).
  16x / 20x HP. No hit takes more than 6% of its HP. Pays 1000 / 1250.
- **Limbs:** shot-off legs make a zombie crawl or hop; no arms means a weak headbutt (`ZLN`).

**You** (`ZM`, `zombies.js:6-16`)
- **Start:** 500 credits, your zombies loadout pistol (revolver / pistol / akimbo / sawnoff / water pistol) + knife +
  your item + one passive (`ZM_PASSIVES`). You carry 2 guns.
- **Credits:** +10 per hit (first 10 hits per zombie, at most one per 180 ms), +60 per kill, +100 for a headshot or
  melee kill. Boards: +10 each, up to 20 a round.
- **Regen:** 25 HP/s after 4 s without a hit.
- **Down, not dead:** while a friend is up, you go **down** with a 30 s bleed-out (60 s with Stubborn).
  - A friend holds F within 2.2 m (6.6 studs) for 3 s to revive you (1.5 s with Quick Hands). The bleed timer pauses
    while you're being revived.
  - Bled out = out until the next round, then back with the start kit.
  - Mid-round joiners sit out until the next round (`zbench`).
- **Hold F to buy** (`zmTarget` decides what you're looking at; hold 0.3 s):
  - doors / shutters: 750-1500 each (per map)
  - wall guns: e.g. Dead Mall revolver 300, smg 900, bread 600, banana 750, shotgun 1200, bow 1000, ar 1200,
    sniper 1500, katana 2000, burst 1300, lever 1100, autoshot 1400
  - ammo: half the gun's price
  - mystery crate: 950, spins 3.6 s, the weapon waits 8 s
  - power switch: hold 1 s
  - Jank Cola: 2500, needs the power. Zombies hit half as hard, regen x1.6.
  - more colas: LEG DAY 2000, DEEP POCKETS 3000, THIRD HAND 4000 (3 guns), GET UP JUICE 1500 (self-revive once).
    At most 3 colas; you lose them when you go down.
  - Warranty Voider: 2500 / 5000 / 9000. x1.6 / 2.4 / 3.4 damage, and a random side effect from tier 2.
  - Cheat Machine: 1250 + 500 per use this round, 15 s cooldown. A random 15-30 s modifier: ONE AND DONE, TAX FRAUD,
    BOTTOMLESS MAG, ZOOMIES, BRAIN FREEZE, BIG HEAD MODE, VAMPIRE TEETH, BOUNCY CASTLE.
  - nail a plank back: 0.6 s each
- **Drops:** a 4.5% chance per kill, at most 4 a round, they last 25 s. TIP JAR (+400 for everyone), RESTOCK,
  CLEAN-UP ON AISLE 5 (every zombie pops), or a killstreak that goes off at once.
- **Grapple:** runs on charges here: 2, each one back 8 s after the last (`BR.hook`, `server/zmshop.js`).
- **Containers:** every 5 rounds Online, every 10 in Bots rooms.

**Squad bots** (`server/zmbots.js`): they shoot, earn and spend (doors, guns, ammo, crate, cola), nail planks,
revive (humans first), grab drops, flip the power, and stay with the squad. Each has a personality kit.

**Roblox notes:**
- Phase 2-3. Port the shared modules as ModuleScripts first; they're pure data + maths.
- Use `PathfindingService` or port the flow field. The flow field scales better for 24 zombies: one BFS per player
  every ~0.3-1.5 s, then every zombie walks downhill.
- Zombies are server-owned NPC Models. Set network ownership to the server (`SetNetworkOwner(nil)`), or animate them
  with CFrame on the server and tween on the clients.
- Doors are Parts whose `CanCollide` is turned off on purchase. Hold F uses the same `Use` remote, and the server
  re-runs `zmTarget` with slack.
- Keep credits on the server, mirrored to a `Credits` attribute.

### Coop (room `coop`)
you and your friends against waves of bots.

**Rules** (`tickWaves`, `room.js:634-659`)
1. One shared room on Warehouse (`room.js:365`). Anyone can change the map and bot difficulty (`setCfg`, 1.5 s
   cooldown each).
2. Wave 1 starts 4 s after the room opens.
3. Wave n: spawn `min(30, 2 + 2n)` bots, at most `min(10, 3 + n)` alive at once.
4. When all are spawned and dead: a 6 s break, +10 + 5n xp each, and a container every 5 waves.
5. Coop bots never respawn (they're removed when they die: `room.js:1555`). Their hits on people do x0.6
   (`room.js:1374`).
6. Humans respawn normally (2.5 s).
7. No round, no win, no vote: it never ends. Waves only tick while a human is in the room.
8. HUD: the wave line from `{t:'wave', n, left, inter}` (`hud.wave`).

**Roblox notes:** a simple server loop. Bots are NPCs with the DM brain targeting players only. Good early test of
bot infrastructure.

### Training (room `training`)
dummies and infinite ammo. nobody is judging.

- **Map:** the Range (`range`). You can't change it.
- **Dummies:** grey "Dummy" bots at `map.dummies` (or at the spawns). Some slide side to side (`d.move`). They don't
  shoot. They respawn 0.7 s after dying.
- **Infinite ammo:** client `weapons.js:803` and server `room.js:1697`. Blood Cross HP comes back 2 s after your last
  shot (`room.js:2269`).
- **Streaks:** your 3 picked killstreaks are always in your tray. A used one comes back 3 s after it runs out
  (`trainingStreaks`, `room.js:3531`).
- **Spray range:** a zone that runs S&D gunplay for S&D guns (`public/js/sprayrange.js`).
- **Off:** no stats, no killcam, no highlights, no bot grapple.
- **Roblox notes:** the first room to port after Rooftop FFA: it's the weapon test bench.

---

## Big modes (summaries, phase 3)

### Jank Royale (`br`), phase 3
battle royale. jump out of the blimp, loot the floor, stay in the zone. last one standing wins.

Files: `shared/royale.js` (all numbers), `server/royale.js` (925 lines), `public/js/royale.js`, `docs/ROYALE.md`.
It only plays on **Jankburg** (`map.royale = { zone0: [0, 0, 300], blimpY: 195, loot: 380 }`).

**The drop**
- Everyone boards the **blimp** with a loaf (`BR.melee = 'bread'`), 100 HP and empty pockets.
- The blimp flies a straight line over the middle at 18.5 m/s (55.5 studs/s). It waits 2.5 s first and flies 400 m
  (1200 studs) in total.
- Jump whenever. Anyone still aboard at the end is thrown out.
- Free fall: up to 34 m/s (102 studs/s), steering 18 m/s (54).
- The umbrella opens by itself 42 m (126 studs) above the floor, or press Space (lowest 6 m / 18 studs). Glide:
  sink 7 m/s (21), steer 15 m/s (45).
- Late joiners get a seat if the blimp is less than 25 s in; otherwise they spectate.

**Loot**
- 60-380 spots: indoors first, at least 5.5 m (16.5 studs) apart, districts loot better or worse.
- 5 rarity tiers (Common → Legendary): damage x1 / 1.08 / 1.16 / 1.26 / 1.4.
- 2 gun slots + melee + a gadget.
- Pick-up reach 2.6 m (7.8 studs). Auto pick-up 1.4 m (4.2) for ammo, heals and armour.
- Ammo per gun: `ammoFor`.
- Heals: Jank Cola +25 (1.6 s, carry 8), Medkit +75 (3.5 s, carry 3).
- Armour: plate +25, vest +50, fridge 100. It absorbs 60% of hits, but not the zone.

**The rest**
- **Grapple charges:** 2, each back 8 s after the last.
- **The zone:** 6 circles `[wait, shrink, share of r0, dps]`:
  [55, 35, 0.62, 2], [35, 28, 0.4, 4], [28, 24, 0.24, 7], [22, 20, 0.12, 11], [18, 18, 0.04, 16], [14, 14, 0, 25].
  - Damage ticks every 0.5 s outside, with a shove back in of (4 + 1.5·phase) m/s.
  - Violet `#8a3cff`.
- **Twists** (`tickBRTwists`):
  - **RETURN TO SENDER:** your first death before circle 2 closes mails you back in a box 5 s later, somewhere in the
    next circle.
  - **The kill leader:** 2+ kills, everyone sees where they are. Their killer gets a Legendary.
  - **Supply crates:** at 75 s and 170 s.
  - **Loot goblins:** at 42 s and 150 s.
- **Win:** the last one standing, once at least 2 were in it. Or the time runs out. The end screen is ordered by
  placement.
- **Bots:** they drop, loot, rotate with the zone, heal, pick the gun for the range, and third-party hurt targets
  (`brBotScore`).
- **Roblox notes:** a project of its own. It needs the Jankburg map, a loot system with a server-side inventory, the
  blimp path (server-timed, client-drawn), umbrella glide physics on the client, and the zone as a server-timed plan
  that every client evaluates with `zoneAt` (port it).

### Battle Island (`island`, BETA), phase 3
squads of 3. drop in together, go down instead of dying, hold F on a downed squadmate to pick them up. last squad
standing wins.

Files: `shared/island.js`, `server/island.js`, `server/islemeter.js`, `server/isleparty.js`,
`docs/modes/BATTLE_ISLAND.md`. It's the royale with squads, offline only in the hub, and plays on Jankburg until the
island map lands (`shared/battleisland.js`).

- **Squads:** 6 squads of 3 (bots fill). The squads have names and colours: THE LOAVES, BIN LIDS, WET SOCKS...
- **Downed:**
  - Bleed-out 30 s. Every point of damage takes 0.25 s off it.
  - Crawl 1.7 m/s (5.1 studs/s).
  - No shooting, using, looting or healing.
- **Revive:** hold F for 4 s within 2.5 m (7.5 studs). You come back with 30 HP. A squad with nobody up is out.
- **MECH METER** (0-100):
  - Fills on its own in 90 s.
  - Energy cell +20, 0.1 per damage dealt, +25 per kill.
  - At 100, the streak key calls your hero mech (the mech drop killstreak's code).
  - After a mech breaks, the meter goes back to 25.
- **Zone:** its own 5 rings over about 12 min (`ISLE_ZONE`). The final ring is at least 20 m (60 studs).
- **Win:** the last squad standing. On time: the squad with the most people up.
- **Roblox notes:** build after the royale. It's a layer of hooks (`isleOn`) over it.

### Board Game Night (`bgn`), phase 3
roll the die, buy golden bread, minigames between turns.

Files: `shared/bgn.js` (every number and name), `shared/bgnboard.js` (the board graph), `server/bgn.js`,
`server/bgnbots.js`, `public/js/bgn*.js`, `docs/party/DESIGN.md`.

- **Where:** a private bots room parked on Crate. 4 seats (bots fill). Online via the `bgn` lobby too.
- **Length:** 5 / 10 / 15 rounds (default 10).
- **The board:** THE KITCHEN TABLE, a 36-space loop plus THE CREASE shortcut (7 spaces).
  - Spaces: COUPON +3, LATE FEE −3, JANK (a random wheel event), CORNER STORE (items), SODA SPILL (stuck: next roll
    halved), THE BAKERY, THE BOX LID.
  - Passing the BOX LID pays ALLOWANCE +5.
- **Golden bread:** costs 20 coupons at THE BAKERY, which moves between 6 plates.
- **Duels:** from round 4, landing on a pawn means a duel (fee 10).
- **Items:** peel, wet floor sign, shopping cart, fake bread, lasso. 3 in your bag at most.
- **Minigames:** every round ends with one of our own modes on a small map with a short clock (`BGN_MINIS`):
  CRATE BRAWL (dm), SPOON FIGHT (spoons), HOT FLOOR (lava), DUCK DODGE (duckrain), MYSTERY MEAT (rand),
  ONE-SHOT WONDER (oitc, 2 lives), SPEED LADDER (gun, 6 rungs), RED VS BLUE (tdm), TAG SALE (tags),
  EVERYONE VS THE LEADER (inf, the leader is patient zero).
  - Formats: 1v1v1v1, 2v2, 3v1.
  - Payouts in coupons (`BGN.pay`).
- **LAST CALL:** in the last 3 rounds, coupon spaces pay x2, and last place picks a house rule.
- **Win:** the most golden bread, then coupons. A tie is settled by a sudden-death spoon fight.
- **Server checks:** clients only send choices (`{t:'bg', k}`), checked against the seat whose turn it is, at most
  6 per second.
- **Roblox notes:** this mode only makes sense once the minigame modes it borrows (dm, spoons, lava, duckrain, rand,
  oitc, gun, tdm, tags, inf) are ported. The board itself is UI + server turn logic.

### Story mode: OVERDUE (hidden, phase 3+)
It isn't a match mode, and it isn't in the menus: it loads only with `?story=1` or `localStorage jfStory=1`, and never
on phones (`public/js/main.js:210-220`).

- Solo story runs the shared story sim in a browser web worker (`public/js/story/host.js`, `shared/story/*`).
- `server/story.js` only keeps save slots (`/api/story/*`). The co-op `StoryRoom` is an empty stub.
- Design: `docs/story/DESIGN.md`, `docs/story/TECH_PLAN.md`, `docs/story/ACT1_PLAYABLE.md`.
- **Unclear:** whether the owner wants it in the Roblox port at all. Ask before planning it.

---

## Test knobs (`JF_*`) worth knowing

These are set as env vars on the web server. Mirror the useful ones as server `Configuration` attributes in Roblox.

| knob | what it does |
|---|---|
| `JF_GAME=<id>` | the Online room starts in this mode (`room.js:363`) |
| `JF_TARGET=n` | every kill/point limit = n |
| `JF_ROUND_TIME=s` / `JF_ROUND_KILLS=n` | round length / default kill target |
| `JF_GG_START=n`, `JF_GG_LADDER=a,b,knife`, `JF_GG_TIME=s` | gun game: start rung, a fixed ladder, clock |
| `JF_INF_TIME`, `JF_INF_DELAY`, `JF_INF_HP` | infection clock, patient-zero delay, zombie HP |
| `JF_LIVES=n` | oitc lives |
| `JF_DUCKS=x` | duck rain amount multiplier |
| `JF_BOMB_WINS`, `JF_BOMB_FUSE`, `JF_BOMB_ROUND`, `JF_FFA_BOMB=n` | P&D: wins needed, fuse s, round s, start a Bazaar P&D in the Online room once n humans are in |
| `JF_ECON=0`, `JF_BUY_TIME`, `JF_START_MONEY`, `JF_ECON_MAX`, `JF_SD_SIZE` | P&D economy off / buy phase / credits / room size |
| `JF_LOBBY_WAIT`, `JF_LOBBY_AGAIN` (ms), `JF_LOBBY_MIN`, `JF_LOBBY_MAP` | mode lobbies |
| `JF_SKIP_WINDOW`, `JF_SKIP_COOL` | /skip vote timings |
| `JF_TRAIN_STREAKS=1` | your 3 killstreaks always ready, any mode |
| `JF_WIP_MAPS=1` | show maps still being built |
| `JF_ZM_ROUND`, `JF_ZM_CREDITS`, `JF_ZM_REST`, `JF_ZM_SWIPE=0`, `JF_ZM_MAP`, `JF_ZM_POWER`, `JF_ZM_OPEN`, `JF_ZM_BOSS`, `JF_ZM_TYPE`, `JF_ZM_BOTS=0` | zombies |
| `JF_BR_BOTS`, `JF_BR_ZONE=x` | royale crowd, zone speed |
| `JF_ISLE_SIZE`, `JF_ISLE_SQUADS`, `JF_ISLE_BLEED`, `JF_ISLE_REVIVE`, `JF_ISLE_METER`, `JF_ISLE_ZONE` | battle island |
| `JF_BGN_ROUNDS`, `JF_BGN_FAST`, `JF_BGN_DIE`, `JF_BGN_MG`, `JF_BGN_FMT`, `JF_BGN_SEED` ... | board game night (`server/bgn.js:19-34`) |
| `JF_MAX_ROOMS` | room cap (300) |

---

## Suggested porting order

**Step 0 (done in step 1):** free-for-all movement, grapple and shooting on Rooftop.

**Batch 1: the match core, on Rooftop.** Do this right after FFA works.
1. Deathmatch done properly: kill target (20 / 15), clock (360 / 300 s), spawn picking (`pickSpawn`), 2.5 s respawn +
   1.2 s spawn protection, the kill feed, the end screen with winner rules.
2. The end-of-match vote (mode then map, 4 cards, the daily event, bots break ties), `/skip`, and the next-round
   handover. Even with one map, the mode vote works.
3. Bots filling seats (`botWant` / `fillBots`) and the DM bot brain.
4. Training (the Range), because every later weapon needs a test bench.

**Batch 2: team modes on Rooftop** (it has `teamSpawns` and an `_sd` twin).
5. Team Deathmatch: the Teams service, `friendly()`, the team bar.
6. Tags: server-spawned tag Parts, distance pickups.
7. Plant & Defuse step 1 on `rooftop_sd`: bomb, sites, hold-F `Use` remote, rounds, side swap, 4.5 s respawns
   (economy off).

**Batch 3: cheap chaos modes.** These reuse DM, and each adds one rule.
8. Randomizer: needs most loadout weapons ported. The server stores the rolled loadout.
9. Spoons & Grapples: needs the knife and grapple only.
10. One in the Chamber: needs the revolver + knife; lives, bullets and spectating.
11. Infection: needs the claw; the `Infected` attribute, the 200 HP zombies.
12. Floor Is Lava: lava floor tagging, the bounce, server checks.
13. Duck Rain: needs the Rubber Duck item's black hole first.

**Batch 4: ladder and economy.**
14. Gun Game: start with a fixed ladder of ported weapons, then switch to the rotating 19-rung ladder once the pools
    are ported.
15. Plant & Defuse step 2: the economy (credits, buy menu, barrier zones, drops, armour, S&D damage, no respawns),
    then 5v5 bots (`econai.js`).
16. Mode lobbies + the pre-game deck (needed before any one-mode lobby goes online).
17. Coop waves (easy once bots exist).

**Batch 5: phase 3 projects** (each one is a project of its own).
18. Zombies: shared modules → nav and flow field → rounds, credits, doors → downs and revives → shop extras →
    specials and bosses → squad bots.
19. Jank Royale on Jankburg.
20. Battle Island on top of the royale (and the mech drop).
21. Board Game Night: last, since its minigames are the batch 1-4 modes.
22. Story (OVERDUE): only if the owner asks.

---

## Unclear (collected)
- **DM round-start sound:** there's no DM-specific one. Zombies uses `sfx.roundStart`; the generic round start only
  shows a callout (`main.js:2986`).
- **Randomizer:** the server doesn't check that hits come from the rolled loadout (`room.js:2031`), and the web game
  trusts the client. The port should check it.
- **Plant & Defuse:** if the 1 h match clock ever ran out, `endRound` would compare round wins. It never happens in
  practice (`room.js:3200`).
- **Duck Rain bots:** there's no special dodge logic in the bot brain.
- **Lava:** whether every future map passes `lavaOk` (today all 11 quick-play maps do).
- **Story mode:** it's hidden behind a flag. Whether it belongs in the Roblox port is the owner's call.
