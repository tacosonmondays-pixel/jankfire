# ZOMBIES on Roblox

Started 19-20 Nov 2026 by weapons-port. Owner (via main): "A multi level multi section map, lets bring back zombies!!
We can used colored dummies for now!! It'll be a big highschool multiple floors courtyard basement classrooms
bathrooms etc!! Bring everything we got from jank fire!!"

This is the web game's ZOMBIES mode ported in full: co-op wave survival for a squad of 4 (bots fill the empty slots).
Rounds, window spawns, credits, doors, wall buys, the mystery crate, power, colas, the Warranty Voider, the Cheat
Machine, drops, boards, specials, crawlers and bosses. The web sources are in this repo: shared/zombies.js,
zmshop.js, zmlimbs.js, zmschool.js, zmhospital.js; server/zombies.js, zmextra.js, zmbots.js, zmboss.js;
public/js/zombies.js, zmextra.js, zmshop.js, zmlimbs.js, zmloadout.js, zmmats.js.

Who does what:
- **weapons-port**: the mode (server and client), the zombies, the bots, the HUD, the test map, and THIS CONTRACT.
- **maps** (local_ae134f7e): the school map, built to the contract below.
- **play-party** (local_3ee21416): the MODES tab entry and the queue into a zombies match.

Rules that hold everywhere in the mode:
- Zombies are COLOURED R15 DUMMIES for now (no skins, no gore, no blood). Limbs pop off as plain plastic parts.
- No voice sounds at all (no groans, moans, screams). Shuffles, steps, rattles, impacts: recordings only.
- No flavour text on screen. Item names (Jank Cola, Warranty Voider, Cheat Machine) are labels; descriptions say
  what a thing does, nothing more. Boss job titles are names, kept short.

---------------------------------------------------------------------------------------------------------------------

## 1. THE MAP CONTRACT (what a zombies map must carry)

Everything below mirrors the web map's `zm` block (shared/zmschool.js), in studs (1 web metre = 3 studs).

The map is one Model. Inside it, a **Folder named `ZM`** holds every marker. Markers are plain Parts: Anchored,
CanCollide **false**, CanQuery **false**, CanTouch false, Transparency 1. The mode only reads their CFrame, Size and
attributes. Where a marker has a front, its **LookVector points out of the wall, toward where the player stands**.

### 1.1 The `ZM` folder's own attributes
| attribute | type | meaning |
|---|---|---|
| `Label` | string | the map's name on screen, e.g. "Jankfield High" |
| `Start` | string | the area id the squad starts in (it is open from the start) |

### 1.2 `ZM/NavBounds` (one Part, required)
A box round everything zombies and players walk on INSIDE the building, every floor (basement to roof). The mode
lays its nav grid over the box's X/Z at 3-stud cells, and finds every floor in each cell by casting down from the
box's top. Window ledges outside need NOT be inside it (zombies climb in from there).

How the nav reads the building (so build to it):
- A floor is any **CanCollide, CanQuery** surface with at least **6.5 studs of head room** over it.
- Neighbouring cells link if their floors differ by **1.6 studs or less** (stairs: rise at most 1.6 per 3 studs of
  run; ramps any slope under that). Up to **4 floors stacked** in one column (basement, ground, upstairs, roof).
- Walls stop links: anything CanCollide and CanQuery between knee and chest height.
- Decoration that zombies should walk through (thin rails, posters, glass you see through but players also walk
  through) must be CanCollide false or CanQuery false. Props players must walk round (desks, lockers) stay solid:
  zombies walk round them too.
- Corridors and doorways at least 9 studs wide, so a crowd gets through.

### 1.3 `ZM/Areas` (Folder, required)
One Part per box of floor space. **Name = the area id** (lowercase, no spaces: `lobby`, `cafe`, `gym`, `basement`,
`courtyard`, `bath1`...). Several Parts may share a name (an L-shaped room, a balcony that belongs to the gym).
| attribute | type | meaning |
|---|---|---|
| `Label` | string | the name on screen ("Main Entrance") |

The box covers the room's floor and the height a player stands in on that floor (floor to ceiling). A point belongs
to an area if it's inside any of that area's boxes. Areas decide where zombies spawn (only at windows of OPEN areas)
and what you can buy (only in open areas). Outdoor areas (a courtyard) are areas like any other.

### 1.4 `ZM/Doors` (Folder)
One **Model per door** (a roller shutter you buy open). Its attributes:
| attribute | type | meaning |
|---|---|---|
| `A`, `B` | string | the two area ids it joins (buying it opens both sides to each other) |
| `Price` | number | credits (web school: 750 to 1250; deeper = dearer) |
| `Label` | string | optional: what the prompt calls it (default: area B's Label) |

Children:
- `Shutter` (BasePart, required): the closed door, **CanCollide true, CanQuery true** (it blocks players, zombies and
  shots while closed). The mode rolls it up and turns its collision off when bought. Size: the opening, about
  12 wide x 9 tall x 1 thick.
- `Housing` (optional parts): the box over it; stays.
The nav finds every cell the Shutter's box covers and gates those links on the door being open.

### 1.5 `ZM/Windows` (Folder)
One **Model per window** (where zombies climb in). Attribute `Area` = the area id it opens into. Children:
- `Out` (Part): where a zombie appears, outside, ideally out of sight (a ledge, an alley, a fire escape). It walks
  from here to the window.
- `In` (Part): the floor point just inside where it lands (must be on the nav grid, in its `Area`).
- `Boards` (Part): the opening itself, about 6 wide x 6 tall, centred in the wall; **LookVector into the room** (the
  side a player stands on to nail planks back). The mode adds and removes the 6 planks.
Keep the opening a real hole in the wall (zombies climb through it) and the outside ledge closed in (players must not
be able to leave the building through it: the web put walls round each ledge).
Web school: 21 windows over 2 floors for 12 areas. Every area that zombies should come into needs at least one.

### 1.6 `ZM/WallBuys` (Folder)
One Part per chalk outline on a wall: about 4 wide x 2 tall, flat on the wall, LookVector out of the wall.
| attribute | type | meaning |
|---|---|---|
| `Weapon` | string | one of OUR weapon ids (Weapons.luau): `revolver`, `smg`, `shotgun`, `lever`, `ar`... |
| `Price` | number | credits. A refill costs half (rounded up to 10) |
The mode draws the outline and the gun on it. Web school prices: revolver 300, smg 900, banana 750, shotgun 1200,
lever 1100, autoshot 1400, ar 1200, bow 1000, burst 1300, sniper 1500, katana 2000.

### 1.7 `ZM/Crate` (Folder)
Parts named `Spot`: where the mystery crate can stand (the floor point under its middle; LookVector = the side you buy
from). One spot is enough; mark the first one with attribute `Start = true`. The mode brings the crate model.

### 1.8 The machines (single Parts directly in `ZM`; LookVector = the machine's front)
Each is the floor point under the machine's front middle. The mode brings the models. Leave about 4 x 3 studs of wall.
- `Power`: the power switch, on a wall (in a hard-to-reach area: the web put it in the boiler room). Its marker sits
  at hand height on the wall instead of on the floor.
- `CheatMachine`: the Cheat Machine (needs the power).
- `Voider`: the Warranty Voider (needs the power).
- `Colas` (Folder): one Part per cola machine, attribute `Cola` = `jank`, `getup`, `legday`, `pockets` or `thirdhand`.
  Web school: one per wing, Jank Cola by the gym.

### 1.9 Spawns
- `ZM/PlayerSpawns` (Folder): at least 4 Parts in the start area, on the floor, LookVector = facing.
- `ZM/BossSpawns` (Folder, optional): Parts outside, like a window's `Out`. Without them bosses use the windows.

### 1.10 Size and look
- The web school was 60 x 48 m on two floors (180 x 144 studs). A school with a basement, ground, upstairs and a
  courtyard can be bigger, but every area should be reachable through doors from the start.
- Every closed door leads somewhere worth buying. Two ways round (a loop through floors) lets a squad drag a crowd.
- The mode adds its own lights only for the power (it switches the map's `PowerLight` tagged lights on; untagged
  lights are always on). Optional: tag lights `PowerLight` with CollectionService for a dark-until-power look.

---------------------------------------------------------------------------------------------------------------------

## 2. THE MODE (the plan; filled in as stages land)

Server (roblox/src/server):
- `Zombies.luau`: the match: rounds, credits, doors, wall buys, downed / revive / bleed out, regen, game over.
- `ZombieNav.luau`: the nav grid and the flow fields (the web's buildNav / flow / downhill, on raycasts).
- `ZombieMobs.luau`: the zombies themselves: a pool of R15 dummies, gaits, the walk, the claws, limbs.
- `ZombieBots.luau`: the squad's bots.
- (stage 2) `ZombieExtra.luau`: crate, power, colas, Voider, Cheat Machine, drops, boards.
- (stage 3) `ZombieBoss.luau`: specials, crawlers, the Floor Manager and the Mascot.
Shared: `ZM.luau` (the numbers from shared/zombies.js, zmshop.js, zmlimbs.js, plain descriptions).
Client: `ZombiesClient.luau` (credits with +N, the round tally, F prompts, the downed screen), `ZombieFx.luau`.

How it plugs in (stage 1, place v1154):
- Zombies are Fighters of kind "zombie" in workspace.Dummies (every weapon hits them; their hits and deaths skip the
  feed, quests, kill effects and finishers: Fight.zombieHurt / zombieDied). Squad bots are kind "zbot", in the arena.
- Buying and reviving are ProximityPrompts on **Q** (F as on the web till 27 Nov 2026; F is the flashlight now, 4.11.
  E is our grapple, and Q's other jobs, the katana's wave and the Scythe's form, aren't in ZOMBIES). Shutter 0.3 s,
  wall gun 0.3 s, revive 3 s.
- A player in a game reads as Zone **"match"** (Matches.zoneHook), plus attribute ZmOn: every menu already hides and
  loadouts lock for a match.
- Spare rounds: Rules Ammo.res; the player's ZmRes_<weapon> attributes; Arsenal's reloads read them.
- The queue (play-party): Zombies.start(players, map, opts?) -> ("zm:N", info) | (nil, "busy"), Zombies.busy(),
  Zombies.maps(), Zombies.onEnd(id, players). One game per server for now; several per server land with stage 4
  (a map copy per game at (0, 600, 24000 + k x 3000), Zombies.MAX_GAMES from measured cost, all state per game).
- Studio test hook: ServerStorage.JankZombies ("start", "stop", "state", "round", "credits", "open", "max").

Stages (each with a report and a Play sheet or video):
1. This contract + the core loop on a test map: rounds, spawns, chase, claws, credits, doors, wall buys, downed and
   revive, squad bots.
2. The crate, power, colas, Voider, Cheat Machine, drops, boards.
3. Specials, crawlers, bosses.
4. On the school.

---------------------------------------------------------------------------------------------------------------------

## 3. THE 26 NOV FIX PASS (the owner: "Zombies is super buggy")

The owner, 25 Nov: "regular zombies are ookay but the pourple and red ones have too much hp! the bots follow you
instead of actually playing, let them shoot open doors buy guns etc.. doors dont have animations the ones you buy, the
ambiance isnt there yet, it should be darker, with fog, not all ceiling likes should work so the ones that do give a
better vibe, make sure props dont blick entrances unless entended, make sure propls dont clip into walls or other
objkects and props".

### HP (purple = the Chonk, red = the Floor Manager; the Mascot is the other boss)
- Chonk: 3.5 -> 2 times the round's zombie HP.
- Bosses: Floor Manager 16 -> 6, Mascot 20 -> 7 times the round's zombie HP. A boss used to count every squad member as a
  player (+50% each), so a solo player with 3 bots fought a 4-player boss. Now real players add 50% each and a bot 15%
  (`ZM.BOSS.perBot`, `ZM.bossHp`). No single hit still takes more than 6% of a boss.
- Regular zombies (and the red-orange sprinters, which have a regular zombie's HP) are unchanged.

| round | zombie | Chonk before (x3.5) | Chonk after (x2) | revolver hits before -> after | AR hits before -> after |
|---|---|---|---|---|---|
| 5 | 128 | 448 | 256 | 12 -> 7 | 41 -> 24 |
| 8 | 194 | 679 | 388 | 17 -> 10 | 62 -> 36 |
| 10 | 235 | 823 | 470 | 21 -> 12 | 75 -> 43 |
| 15 | 362 | 1267 | 724 | 32 -> 19 | 116 -> 66 |
| 20 | 557 | 1950 | 1114 | 49 -> 28 | 178 -> 102 |

| boss, round | squad | HP before | HP after | revolver hits before -> after |
|---|---|---|---|---|
| Floor Manager r5 | you + 3 bots | 5120 | 1114 | 128 -> 28 |
| Floor Manager r5 | 4 players | 5120 | 1920 | 128 -> 48 |
| Floor Manager r15 | you + 3 bots | 14480 | 3149 | 362 -> 79 |
| Mascot r10 | you + 3 bots | 11750 | 2385 | 294 -> 60 |
| Mascot r10 | 4 players | 11750 | 4113 | 294 -> 103 |
| Mascot r20 | you + 3 bots | 27850 | 5654 | 697 -> 142 |

(revolver: the zombies' 40 a body hit; AR 11. By round 10 a squad has wall guns and Voided ones: x1.6 to x3.4.)

### The bots (server/ZombieBots.luau, new)
Each bot steps through, in order: REVIVE a downed friend (people first); FIGHT the nearest zombie it can see, zombies at
windows too (bursts from an automatic, every pellet of a shotgun rolled, a person's reaction and aim); SHOP when no
zombie is within 30 studs (throws the power, buys a better wall gun, opens the cheapest door out of the open areas, one
a round each from round 2, the Warranty Voider on its gun, Jank Cola then Get Up Juice: your prices and checks, its own
credits); HOLD A POST: each bot takes a different window of the open areas within 80 studs of you on foot, stands
5.5 studs inside it facing it and nails the planks back between fights (no window near: a spot round you). Their rays
use the game's own map copy (Fight.castMap only knows workspace.Map, so before this a bot could "see" through a shut
door). Studio: `JankZombies "bots"` lists what each is doing.

### Doors
A bought shutter rolls up into its housing slat by slat in 2.6 s (`ZM.R.doorRoll`), drawn by each client
(`ZombiesClient.rollUp`), with a recorded rattle `zm_door` (Freesound CC0 383828). The server hides the real shutter
when the roll is done. Before, it slid up 9.5 studs and faded out in 0.9 s, which read as vanishing.
`JankZombies "door" n` opens one door (to watch the roll).

### Wall buys
They were bare markers: nothing on the wall until you stood close enough for the prompt. Each now has a chalk outline,
its gun hung inside it and a small lamp over it (`ZombiesClient.buildBuys`, client-side, once per game).

### Ambience (v2B, the live school)
- The look `HubLook.looks.school_v2b`: ambient about 40% lower, a thick cold haze (the Atmosphere is the fog: with one
  in Lighting, FogStart/FogEnd do nothing), less saturation, a readier bloom. The old values are in a comment there.
- The kit: about 4 in 10 ceiling fittings dead in every room but the gym (never all of a room's), the even room fill
  halved (`school_models.py` v2_plan / v2_lights, `DEAD_SHARE`). Shutter lamps and wall-buy lamps keep doors and buys
  readable.
- `SchoolLife.client`: four flicker groups dead for good, a recorded tube buzz `zm_flicker` (Freesound CC0 484157) as a
  group flickers, and a faint mist over the floor round you (one emitter box at your feet, moved twice a second, its
  puffs lit by the lamps they drift under).

### Props (school_layout.py + tools/roblox/school_clip.py, new)
`python tools/roblox/school_clip.py` checks every prop's box against walls, fences and landings, other props, the clear
space of every shutter and doorway (4 studs either side, floor to 7 up), every zombie window's way in and every stair
ramp. Before: 239 hits (12 entrances blocked, 6 window lanes, the rest props sunk into walls). After: 0.
- `F()` slides a prop out of any wall it was placed into (v2's piers are the wall's hit face, so a locker sunk 0.5 had
  the piers running through it). Pieces made to sit in or on a wall keep their place (`NO_NUDGE`).
- Moved: restroom sinks off the doorway wall's opening (3 restrooms x 2 floors + the basement one onto its west wall),
  the stalls in the west restrooms off the window landing, the basement storage shelves and the workshop bench beside
  their south doorways, the gym's ball rack off the weight room door, the lab skeleton off the hall door, the lab fume
  cupboard off a window, the locker rooms' lockers from under their windows, the upstairs lockers off the stair door,
  the courtyard bench off the lobby door.

### The play test (26 Nov, place versions 1370 / 1389; one solo game with 3 bots, Studio)
- Rounds 1-3 natural. The bots took windows 1 and 2 of the lobby and a spot of their own, out-killed the player (34 /
  23 / 18 kills to 0 by round 10) and opened doors by themselves from round 2: Cafeteria (Bot 3, before the player
  could), West Hall, Courtyard, Gym, Weight Room, Science Lab. By round 8 (credits set to 9000 to test shopping, the
  power thrown) Bots 2 and 3 walked to the gym wing and bought LMGs; all three dropped what they were doing to revive
  the player when they went down, twice, and they were back up each time. At round 10 all four were up.
- HP seen in the game: Chonk 388 at round 8 (2 x 194; was 679); THE FLOOR MANAGER 1688 at round 8 (was 7760); THE
  MASCOT 2385 at round 10 (was 11750). Server cost with 3 thinking bots: 2.2 ms a tick on average, 20 ms at worst.
- Found and fixed after it (push 4): no bot bought the lobby SMG. Scored on raw fire rate the starting revolver (2.5
  shots a second) outranked it; a gun is now scored on what it does in a bot's hands over a magazine and its reload, and
  the starting guns count 0.8 (revolver 32, SMG 42, AR 47, LMG 50, burst 71). Doors: one a round per bot opened 7 by
  round 8; now one a round for the bots together. A test round jump left the boss bar up (cleared now). In a real game
  the lit halls by the courtyard still read bright: the look's exposure -0.1 -> -0.35.
- The door prompt works on F; a test has to stand within 9 studs (my first "it doesn't fire" was a test standing too
  far off).
- Clip (training-v2's PolishBackup.Clip v2) on the school: each kit layer (sc_furn_G, sc_wall_G...) is one merged mesh,
  so its PROPS pass reads layer against layer (v2B 166, v2A 119 "sunk": walls in walls, not props) and can't count props
  here; school_clip.py on the layout's own boxes is the props count (239 -> 0). Its DOORWAYS pass (15 ground-floor
  doors): 2 flagged both before (v2A, the old layout) and after: the courtyard bench and a cafeteria table 4 studs off
  the door lines, with Clip's player box reaching 5. Not in the opening; left as they are.
- Frames: roblox/docs/zombies/7-fix-pass-before-after.jpg.

### Push 4 checked (27 Nov, place version 1521; one short solo game with 3 bots)
- Wall guns: with credits (botc 1500 in round 1) all three bots walked to the lobby SMG and bought it within 2 s, then
  went back to their windows (1, 2, 3).
- Doors: one for the squad a round. Round 2: Bot 3 opened the Cafeteria (Bot 2 had picked the Locker Hall and stood
  down). Round 5: the Locker Hall.
- Revives: when the player went down all three turned to them; once one was on it the other two went back to their
  windows within 2 s. Kills by round 5: 13 / 13 / 15 (the player stood still for the photos). Server cost 1.0 ms a
  tick on average, 8.7 ms at worst.
- The lobby in a real game now reads as night (exposure -0.35), the wall buys still lit. Frames:
  roblox/docs/zombies/8-bots-run-27nov.jpg.

## 4. EXTRACTION, REWARDS AND THE CINEMATICS (27 Nov; the owner: "cinematic for zombies mode please!!", "allow a way to extract!! If you extract at higher floors you can leave and gain rewards", "rewards CAN be bags sprays and crates but rarely chances increase significantly if you get to way higher rounds")

Main read "higher floors" as higher rounds. The plan, built in this order (numbers live in shared/ZM.luau: ZM.X for the
extraction, ZM.XR for the rewards).

### 4.1 Extraction (server/ZombieExtract.luau, new; installed by ZombiesServer after ZombieBots)
- **The offer.** The break after round 10, then after every 5th round (15, 20, 25...), offers an extraction. That break
  lasts 20 s instead of 10. Any player calls it: **Y**, or the EXTRACT button on a phone. The humans vote: more than half
  of them (solo: one press). Bots follow the humans. Nobody calls and the next round starts as usual.
- **The hold-out.** Calling it starts the next round at once, heavier: 50% more zombies at once (cap 36), spawning twice
  as fast, no end to the round. 90 s from the call to lift-off.
- **The way out.** The zone is the **roof**, the helipad between the HVAC units and the water tower (school local
  (10, 32, -70), 14 studs round): the lobby is at the front on the ground floor, so it's a run up two floors and across
  the school. The doors on the cheapest way from the open areas to the roof roll up for free when it's called.
- **The helicopter.** Chunky, unmarked, dark (tools/roblox/zm_heli_models.py, Blender; ReplicatedStorage.JankfireZmKit).
  Drawn on each client from the server's times (no server-side physics): in from the north-west at 55 s, over the pad
  at 62 s, settled at 66 s, rotor turning, a white searchlight, a red beacon. Its hover is a recorded loop on its body
  (zm_heli), so the approach and the leaving are distance.
- **The end.** At 90 s everyone standing in the zone (alive, not down, on the roof, within 14 studs of the pad's
  centre) extracts. If one human got out the squad's game ends with the extraction film; the ones left behind get the
  normal game over (XP only). A wipe during the hold-out is a normal game over.
- **The bots** run for the pad with the humans once it's called (ext.botGoal), fighting on the way.
- **HUD:** EXTRACTION · ROOF with the time to the helicopter, then to lift-off; an arrow and the distance to the pad at
  the screen's edge; the odds for this round's band on the offer.

### 4.2 Rewards (server/ZombieRewards.luau, new; server-only, once a player a match)
On the server's extraction event, for each extracted human who passes the checks: Brass through Quests.grant (its
300-a-day cap stands), XP through Stats.gift, containers through Loot.grant. Receipt ids are `zmx:<game guid>:<user
id>:<what>`, so a retry never pays twice. Each roll is its own; the band is the extraction round's.

| extraction round | Brass | XP | Spray Can | Duffel Bag | Crate | zombies wrap |
| --- | --- | --- | --- | --- | --- | --- |
| 10-14 | 25 | 300 | 2% | 1% | 0.5% | 3% |
| 15-19 | 35 | 450 | 4% | 2% | 1% | 6% |
| 20-24 | 50 | 650 | 8% | 4% | 2% | 10% |
| 25-29 | 65 | 850 | 13% | 7% | 4% | 17% |
| 30+ | 80 | 1100 | 20% | 10% | 6% | 25% |

- **Game over** (anyone who didn't make it, and every game that ends without one): 10 XP a round reached, 250 at most,
  through the same checks. Zombies gave no XP before.
- **Zombies-only wraps** (the wraps session's, 27 Nov; `Roster.EARNED.zombies`, each row `earned = "zombies"`, in no
  can, crate, bag, shop or bundle): Boarded Up `zboards` (Epic, from round 10, weight 5), Locker Rot `zpeel`
  (Legendary, from 20, weight 3), Ooze `zooze` (Exotic, living, from 30, weight 2). A wrap roll picks by weight among
  the ones open at that round that the player doesn't have yet, so at round 30+ the 25% splits 12.5 / 7.5 / 5%, and
  the screens show each wrap's own share. It goes on every gun, kept for guns added later (as a shop bundle's wrap:
  data.every.wrap). Loot.grant takes `zmwrap:<wrap>` only for a wrap marked earned = "zombies". A zombies-only skin
  later: a row with `kind = "skin"` in ZM.XR.wraps.
- **The odds are on screen:** on the offer and on the reward screen, for that band.
- **Anti-farming:** nothing (not even XP) unless the player is a human, did at least 15% of the squad's damage to
  zombies or 15% of its kills, was up (not down or out) for at least half the game, and was active (moving or hitting)
  for at least half of it. Bots get nothing. A Studio test switches the checks off with the hook's `xelig` op.

### 4.3 The cinematics (client/ZombieCine.client.luau, new; CineKit's bars, cuts, shake and kicks)
- **Intro, 7.5 s, skippable** (Space, Enter, or SKIP on a phone; the round waits: round 1 starts 1.5 s after it, or
  2.5 s after everyone skipped):
  1. 0-2.9 s: high over the school at night, in the fog, drifting from the back towards the front; a title card,
     JANKFIELD HIGH.
  2. 2.9-5.0 s: low by a boarded lobby window; a zombie lurches out of the fog into the boards; a hit (a short
     hit-stop and a kick, zm_board) and a plank falls (zm_planks).
  3. 5.0-7.5 s: the squad in the lobby, low and wide, a slow push in; the bars lift; the camera lands on your own view.
  The wind bed (zm_wind) under it all, the boom on the title.
- **Extraction out, ~8 s, then the reward screen:**
  1. 0-3.4 s: wide from a corner of the roof: the helicopter on the pad, the squad running into its open side, zombies
     spilling onto the roof behind them.
  2. 3.4-6.6 s: low under the tail: it lifts, tips its nose and pulls away over the school; zombies reach the empty pad.
  3. 6.6-8.2 s: high and far, the helicopter going into the fog; a fade; the reward screen (EXTRACTED · ROUND n, Brass,
     XP, each roll with its odds and what dropped).
- **Rules:** animation cycles and mocap only (the squad's own run cycles, the zombies' walk); recordings only (zm_wind,
  zm_board, zm_planks, zm_heli from Freesound CC0; the existing boom), no voices or crowds; the school's own muted night
  look; no text in the world, only the title cards.

### 4.4 The console line `rbxassetid://203785492 failed`
To pin down (likely Roblox's default Animate on the bot or zombie rigs); fixed only if it's ours.
- **Answer (27 Nov):** asset 203785492 is an audio upload, "Pop Close Sound" by Zyleak (not ours, not the owner's). It's
  in no script source, no saved instance on the server side, and nowhere in the repo. It fails 5-6 times as each game
  starts, on the client, loaded as the wrong asset type. Not ours, so not fixed (a client-side scan of StarterGui is
  still to do).

### 4.5 Built and checked (27 Nov, place version 1537, Studio; one Play, four short games)
- **Files:** shared/ZM.luau (ZM.X, ZM.XR, ZM.heliAt, ZM.padOf, ZM.xBand), server/ZombieExtract.luau and
  server/ZombieRewards.luau (new), Zombies.luau (hooks cleared / over / heavy, X.gameOver / saveBest / site, and the
  guard below), ZombieBots.luau (ext.botGoal), ZombiesServer (installs it), Loot.luau (the `zmwrap:` grant),
  client/ZombieExtract.client.luau and client/ZombieCine.client.luau (new), ZombiesClient (the HUD waits for a film:
  `ZmFilm`), studio-tools/ZmKit.luau (importHeli), tools/roblox/zm_heli_models.py (the helicopter), four Freesound CC0
  sounds (store.json, freesound-credits.md).
- **The helicopter:** asset 126355876947344 (11 pieces, 1538 faces; ReplicatedStorage.JankfireZmKit.Heli, pivot at the
  skids' feet under the rotor hub, nose -Z). LoadAsset centres an uploaded model, and with a PrimaryPart the model's
  pivot is that part's PivotOffset (WorldPivot alone does nothing): ZmKit sets both from the rotor and the searchlight.
- **Seen in the test:**
  - The intro plays and round 1 waits for it: live 9.0 s after the start. With Space at 1.5-2.5 s, live at 5.3 s.
  - The offer at round 10 shows the band's odds (SPRAY CAN 2%, DUFFEL BAG 1%, CRATE 0.5%, +25 BRASS, +300 XP; the wrap
    rows came after this test, with the wraps session's ids). Y called it through the real vote path.
  - The hold-out HUD: EXTRACTION · ROOFTOP, HELICOPTER 0:57, the pad marker on the screen's edge with its distance.
  - All three bots switched to "extract" and two were on the roof by 44 s, one holding the pad.
  - The helicopter came in over the pad at 59-62 s, searchlight on the roof.
  - Extraction (the player in the zone): the film plays, then EXTRACTED · ROUND 10 with Brass, XP and each roll with
    its odds, "STUDIO TEST · NOTHING WAS GRANTED" (Studio rolls and shows, grants nothing). The game ends 22 s after.
  - A loss (nobody human in the zone, or the solo player down at the end): the normal game over.
  - The anti-farming numbers did their job: the idle test player had 0 damage and act 0-19 of 99-114 s, so without the
    test switch (xelig) they'd have got nothing.
- **Found and fixed in the test:**
  - An extraction or a loss inside the extension's tick left a "break" past its time, and Zombies' tick started the
    next round on a finished game. Zombies' tick now returns after the extension's tick if the game is over.
  - The zombies HUD stayed on over the films: ZombiesClient re-enables its GUI every frame, and the newest handler runs
    first. Fix: the films set `ZmFilm` and ZombiesClient keeps its HUD off while it's set (a game-over panel isn't
    cleared).
  - The intro's first frame showed the hub's daylight; the film now sets the school's look itself.
  - The window shot put the lens inside the front desk; it now picks a lobby window with clear floor inside it
    (raycasts).
  - The hand-back went through your own head; your body only shows in the squad shot now.
  - The helicopter read as black on the night sky: lighter muted paint, a warm light in its open side, and a soft key
    light that rides with the film's camera.
- **Still open:**
  - zm_wind: the first upload (Freesound 117136) was REJECTED by Roblox moderation ("violations of Roblox Terms of Use";
    no warning on the account, the owner checked). The licensed library has no natural wind (synth drones only). The
    one retry: a 15.5 s loop of Freesound 521820 "Polar Wind" (asset 75933475633293). If that's rejected too, the films
    go without a wind bed (no third upload). The clips so far have no wind.
  - v1546: the outro's lift and away cameras are in (the lift from west of the tail, the water tower behind; the away
    shot a long lens from over the courtyard's edge).
  - Testing a downed player teleported to the roof left the bots trying to revive at the old spot (a test artifact
    or a real nav gap: to check).

### 4.6 Polish after main's look at the sheet (27 Nov)
- **The round HUD after the extraction:** out with the helicopter, the zombies HUD (the round, the boss bar, the credits)
  stays off from the film on (`ZmHudOff`, ZombieExtract.client; ZombiesClient reads it). While the reward card is up,
  every other HUD and the first-person gun are off too, each put back after.
- **The intro on a phone:** a cool moon fill while a film plays: the school's ambient lifted towards a cold blue, +0.55
  exposure, the haze 30% thinner, all eased back as the camera lands in your view (ZombieCine `moon`). The fly-over
  comes in closer (it was a black shape in the haze), and the squad shot's key light is stronger (40 studs, 1.6).
- **The boards:** six planks that tilted each way in turn read as a big "W". Now two long boards are crossed corner to
  corner (nailed first, torn off last), then four cross boards at uneven heights, tilts (up to 11°) and lengths, each
  a shade of its own. A seed per window, so every game's boards are the same (ZombieExtra).
- **The reward card (A PLATE, UiKit):** a centred bone card on a dimmed screen. EXTRACTED and the round. What dropped
  is called out big: a wrap's swatch in its own palette, or a flat glyph for the crate, bag or can, with its name, what
  it is and DROPPED with its odds, on the rarity's lip. Brass and XP as slit hero numbers, then every roll's odds
  small. The footer says whether it was a Studio test.

### 4.7 The helicopter, rebuilt from the web game's (27 Nov; the owner: "Can the helicopter be modeled a bit better? Like the jankfire helicopter?")
- **Source:** tools/blender/make_heli.py (the web game's JANK NEWS 7: lofted pod and boom, a see-through bubble with a
  real cabin, gasketed windows, a 3-blade rotor on its hub, mast and pitch links, a 2-blade tail rotor, swept fin,
  skids, the belly searchlight on its yoke, beacon and nav lights). tools/roblox/zm_heli2_models.py runs its build with
  the livery swapped and the pieces split for Roblox: zh_body, zh_glass, zh_cabin, zh_lamps, zh_beacon, zh_cam (still),
  zh_rotor, zh_tail, zh_search (they turn), x3 to studs (29 nose to tail, 9.5 tall), 12.3k triangles.
- **No writing:** JANK NEWS, the 7 badge, J-ANKY, WE SAW THAT, NO HUGS, HI MOM and NO STEP / OK STEP are gone. A door
  stripe, a boom stripe, a hazard band and plain panels take their places; the fin keeps its lightning bolt and the
  ventral fin its hazard bands. The instrument panel's two ring dials (they read as an "8" and a "0") are a plain gauge
  block. Every texture was looked at full size before the upload (the livery, the trim atlas, the glow atlas).
- **Two liveries:** A, the JANK scheme for night (dusty pink a8627f, mustard boom and nose b38a33, teal skids and
  accents 2f8a86), asset 139652899793298; B, a dark rescue scheme (charcoal 383d42, one jank-pink accent stripe
  c2508f, dark skids), asset 112118070212058. The trim atlas's cyan (the skids) is recoloured per livery.
- **In the game:** ReplicatedStorage.JankfireZmKit.HeliA / HeliB (ZmKit.importHeli; marker cubes give the hubs, the
  searchlight's pin and the nose, then go). ZM.X.heli picks which one flies (one line; the first one is still there as
  "Heli"). Its rotors turn about their own hubs (the model's HubMain / HubTail), the searchlight on zh_search, the warm
  cabin light in zh_cabin, the beacon blinks, the hover sound on the body. A test's side-by-side: the player attribute
  ZmHeli on the client overrides the switch. The film's boarding shot is tighter for the smaller body.
- **The sliding door:** the left rear door (Roblox -X, the boarding side; the front one is filled by the pilot's seat)
  comes out of the shell, the glass and the cabin's liner as zh_door, zh_doorglass and zh_doorliner (Blender, by the
  door's box from make_heli's shut lines), with a door marker (the model's DoorAt). The rebuilt assets: A 113544983542207,
  B 118547508099386 (the third upload: Roblox names each MeshPart after the glTF's mesh data, not its node, so the
  build sets every mesh's own name to zh_<piece>__<code> too; the second upload's parts came in as "glass.002" and the
  like and lost their paint codes).

### 4.8 The extraction film, first person (27 Nov; the owner: "she sort of just teleports into the helicopter! How about it's first person, helicopter door opens and there's a guy, he reaches out his hand, you take a step forward then shot its an away shot of the helicopter flying off then boom displays your round and then other small stats return to lobby?")
On each extracted player's own client (ZombieCine; the times in ZM.X.film, s into the film, which starts when the
hold-out ends):
1. 0-0.6 s: first person outside the helicopter's rear door at eye level, a short settle.
2. 0.6-1.5 s: the door pops out of the hull and slides back along the boom (ZombieExtract.client moves it, from the
   server's lift-off time), with the door sound.
3. 1.3 s: the crew member, a plain R15 in a muted olive flight suit (the server's HumanoidDescription; no text or
   logos) with a built helmet and dark visor, scaled to 0.85 to stand in the 4.7-stud cabin, lit by the warm cabin light
   and the film's key light, reaches out (mocap: the vault's Mixamo "Pointing Forward", frames 36-66, retargeted with
   tools/blender/mixamo_r15.py, Animation 110255422946477, held on its last frame).
4. 2.0 s: your own left hand comes up from the bottom of the frame (the same clip on your own body; nothing of your
   body is drawn before then, and then only that arm; the body starts 1.3 studs low and rises with the reach).
5. 2.6-3.6 s: one step forward with a small bob; the clasp sound and a little kick as the hands meet.
6. 3.7 s: a hard cut to the long lens as it lifts (4.2 s) and flies off; a fade at 8.4 s.
7. 9.0 s: the stats card (A PLATE): EXTRACTED and the round big, kills / revives / damage / time survived small, then
   the drop called out big, Brass and XP, the odds small; BACK TO LOBBY (or Enter) ends the game when every human who
   got out has pressed it, or the game ends on its own 13 s later.
Space skips to the card. Anyone left behind sees only the away shot, then the game over. The server hides the bodies
at the cut. The others who got out (the server's xout list: players and squad bots) sit in the cabin: a copy of each
body, scaled 0.85, on a plain bench along the far side, in Roblox's own R15 sit clip, their real bodies hidden on that
screen for the film. Traps from the tests: the crew member's clip loads only once he is in the world (an Animator
outside the game can't load one: his arms stayed down); his helmet and visor are loose anchored parts that follow his
head each frame (welded inside his model, the dome never drew in a game though it drew in Edit). Sheets: roblox/docs/zombies/10-heli-old-A-B-27nov.jpg
(the old helicopter against A and B, boarding and lift-off) and 11-extraction-film-first-person-27nov.jpg.

### 4.9 The intro as a news broadcast (27 Nov; the owner: "have a news broadcast actually for the intro a zombies, it'll be like breaking news", "Then it cuts to shot of the school", then "Can you do proper static for the transition from news .. also zombie is running into hedges can you do a shot of the school gate and multiple zombies piling up?")
ZombieCine; the times in ZM.X.news; 9.9 s, Space skips, round 1 waits for it.
- **Loading.** From the moment this client's party picks ZOMBIES (PlayUI.S.party.mode) or a game starts (ZmArena), an
  early CineKit.prewarm loads the school's, the films', the crowd's clips and the helicopters' assets in the background
  (keep = false: ZoneCull keeps the school put aside in the hub). The server starts the film 1.4 s after the game
  (ZombieExtract's LEAD): each client shows black and runs the intro's own prewarm under it (the shots' pieces kept, all
  of it preloaded); the news sting comes in 0.4 s before the feed. If that prewarm isn't in when the lead ends, the black
  holds up to 2 s more (the film's own clock waits at 0, the sting carrying it); round 1 allows for it (+1 s).
  (roblox/docs/PERFORMANCE.md, "Films: nothing pops in".)
1. 0-4.65 s, **the live feed:** the news helicopter's camera inside the grounds, up over the drive, at night: grain,
   scan lines and zoom brackets (live UI), focus breathing, a colder flatter grade, its searchlight from beside the
   lens, the moon fill held each frame. LIVE top left (a blinking dot), BREAKING NEWS slams in as a lower third (a
   warning-red box, A PLATE bone under it) with one headline: OUTBREAK · JANKFIELD HIGH. Nothing else is written.
   **Warning sirens, not a news sting** (the owner, 27 Nov: "Instead of like cheerful news could it be like warning
   sirens?"): an outdoor siren wailing over the town, zm_siren (PSE "Acme Whistle Wind Hurricane Siren 14",
   9113041454, library, no upload: a hand-cranked siren's wind-up, long wail and wind-down; Volume 2.0), far off and
   echoing (ZombieCine `farOff`: EqualizerSoundEffect highs -14 dB, ReverbSoundEffect 3.4 s), from under the lead's
   black (t -1.3); a low drone under it, zm_drone (PSE "Evil Drone Eerie 1", 9114353535, only its low end: highs -40,
   mids -14; Volume 0.9); the rotor wash (zm_heli). An outdoor siren only: no alert tones or broadcast-alert format.
   (The APM "Breaking News" sting, zm_news 86819169949071, stays in the library, unused.)
2. **The gate.** The school had a chain-link fence along the front of its grounds and no gate (the fence is the gate's
   stone and iron all round now: 4.10); studio-tools/ZmGate.luau
   added ZmFrontGate to Map.JankfieldHighV2B (so every game's copy has it): two chunky stone pillars and iron bar
   leaves in the fence line at the end of the drive (local x 28, z 171, between the street trees), a pavement and road
   outside, one sodium lamp; set dressing only (no collisions or queries, outside the play space). A crowd of 18
   (the mode's own shambler, cloned on this client) piles up against it: five pressing at the bars (Roblox's own zombie
   idle cycles, arms through the bars), six pushing behind (its walk cycle, slow), two going up on the others' backs
   (its climb cycle, leaning in), one walking up out of the street, four more along the fence either side; every one
   with its own speed, phase, sway and lean, leaning in harder as it builds. Each one dressed (main's readability note:
   they read as one bright flat green mass): muted skins, worn shirts in dull colours, dark trousers, now and then a
   torn sleeve; the searchlight eases to 1.9 once it sits on them, and a cool rim light from the street behind them
   outlines their heads and arms against the dark. The BREAKING NEWS lower third is a fifth bigger (phones). The leaves rattle and heave in on their hinges, then buckle at 4.6 s (a lurch, a
   kick). The lens zooms onto it from 3.0 to 4.0 s. Sounds, licensed recordings (PSE, no upload): the rattle bed
   zm_gaterattle ("Chain-Link Fence Impacts 16"), fists on the bars zm_gatebang ("Metal Shake Clunking Bursts Light
   Banging 3"), the heave zm_gateshake ("Metal Rattle Thick Shake 4"), the buckle zm_gateslam ("Metal Gate Slam 1"). No
   voices.
3. 4.65-5.2 s, **static:** full screen, HOUSE HUNT's approved noise frames (HuntConfig.INTRO.static, a new one every
   rendered frame, flipped at random, preloaded with the prewarm), one quick roll of the picture then a judder, tear
   bands, a brightness flutter and dark dropouts; the static burst (PSE "Television Static", zm_static, the same
   recording as HuntIntro's burst). The siren drops to a tenth under the burst; the drone, the rotor wash and the
   rattle cut. Then a hard cut:
4. 5.2-7.7 s, **the school,** our own lens: outside at night in the fog, the bars, a slow push, the wind (zm_wind); the
   siren fainter and further off (0.3, its highs -26 dB), winding down, faded out before the squad.
5. 7.7-9.3 s, **the squad** in the lobby; the bars lift; the camera lands in your view at 9.9 s.
The moon is held each frame up to the squad, and the film sets the player's Finishing attribute (CineKit's flag
"zmintro") so HubLife leaves the light alone (its zone switch ran the map room's black haze over the feed; the school's
own look took the moon back). Sheets: roblox/docs/zombies/12-news-intro-27nov.jpg (the window version),
13-film-and-intro-fixes-27nov.jpg.

### 4.10 The fence and the hedges (27 Nov; the owner: "Finish the fence it's just the gate!! Also can we make the shrubs better looking?", then "I heard if you take a leaf texture you can place it in different planes to create a shrub?")
- **The fence.** The chain-link round the grounds is gone (v2 schools: tools/roblox/school_models.py `railing_fence`):
  the gate's style all the way round, a stone pillar (1.8 wide, 9 tall, a wider cap) every 10 studs, a low stone plinth
  between them and an iron section on it (three rails, round bars every 0.95). v2B leaves the gate's span open (front,
  local x 18..38: ZmFrontGate stands there). Look only: the boundary is the layout's hit boxes, unchanged.
- **The hedges, two versions (the owner picks; the other is one call away).** The hedge hit boxes (school_layout's
  'hedge' cover) are unchanged; both sit in a low stone planter with dark soil (sc_ground) and share one body per hedge
  (tools/roblox/hedgekit.py: a metaball union of ellipsoids in three staggered rows, meshed and decimated: one rounded
  mass with lumps, not a row of balls).
  - **A, chunky** (`sc_hedgeA`, in the school's patch kit 81635365205124, W.PATCHES.JankfieldHighV2B, so a re-import
    keeps it): the body in one of four muted green sets plus a few lighter soft lumps on its skin. Flat colours.
    **Shown now** (place version 1613).
  - **B, leaf cards** (`sc_hedgeB`, tools/roblox/school_hedgeB.py, asset 127985213344563): the same body as a core in
    A's green ('506b3c': a gap between cards reads as foliage in shade, not a hole; r2's darker core rendered black at
    night) wrapped in 8,100 leaf cards (9 per stud of hedge + 16), quads tilted up to 55 degrees off the skin and spun,
    1-1.7 studs, each showing one cell of a 2 x 2 leaf atlas drawn in code (tools/roblox/leaf_atlas.py: clusters of
    pointed leaves on a clear ground, no text; Image 112495419517618). DoubleSided, no shadows. The atlas goes on as a
    SurfaceAppearance with AlphaMode Transparency: a .glb's own picture loses its alpha in the upload (black squares
    round the leaves). Waits in ServerStorage.ZmHedges.
  - **The switch** (Edit, then save):
    `require(game.ServerStorage.PolishBackup.ZmGate:Clone()).hedges(workspace.Map.JankfieldHighV2B, "A" | "B")`; the
    one not shown waits in ServerStorage.ZmHedges, and every game's copy of the school has the one shown. A whole
    W.import of the school lays the patch (A) back over it: run the switch again after one if B is picked.
  - **Measured** (Studio Edit, night look, this PC, 60 fps cap; two runs each, alternating), render CPU / GPU ms with
    A, B, and no hedges: establishing 4.64 / 4.61 / 4.64 and 3.57 / 3.48 / 3.31; the hedge line 4.20 / 4.27 / 4.29
    and 2.78 / 2.77 / 2.84; window close-up 4.40 / 4.42 / 4.39 and 2.85 / 2.91 / 2.86. Within noise of each other:
    neither costs anything measurable here. Sizes: A 103k triangles in 12 meshes; B 63k (core, 5 meshes) +
    16k (cards, 2 meshes). B's cards are see-through, so a phone's GPU pays for the layers it draws over each other
    (not measured on a phone).
- **Checks** (place version 1613). PolishBackup.ZFight on the school: nothing from the fence, planters, hedges or gate
  (223 hits in all, the old walls against door shutters; two sc_ground undersides at ground level, unseen). Clip: no
  hit on them (39 props sunk deeper than 0.15 elsewhere in the school, as before; no moving doors or doorways
  checked). The intro re-filmed with each (popscan: only the cuts, the banner and the zoom).
- Sheets: roblox/docs/zombies/16-fence-and-hedges-before-after-27nov.jpg, 17-hedges-A-vs-B-27nov.jpg (the three views at
  night and the intro's own school shot, the render ms).
- **The extraction film's first frames** (place version 1620, recorded in a fresh Play, popscan): the crew member and the
  seated copies are parked at the call (parkCast) and are in place from the film's first frame; the seated copies lose
  the TPRig tag and ThirdPerson's / the server's gun pieces at once; the film opens on 3 black frames (its key light and
  moon come in on its first frame). The visor is opaque now: a see-through Glass visor wasn't drawn behind the door's
  window, so it came on only as the door slid open, with a white glint. Test trap: at round 20 the zombies down the
  test player within ~9 s of xland (use round 2 and a ForceField).

### 4.11 Glowing eyes, flashlights and the dark areas (27 Nov; the owner: "Can you make zombies having glowing eyes, also some parts of the map you need a flashlight it'll be like most games f for flashlight?")
server/ZombieLight.luau (installed after ZombieExtract) and client/ZombieLight.client.luau; ZM.DARK, ZM.EYE.
- **The eyes.** Two small Neon pieces on every zombie's face (welded to the head; nothing queries or touches them, so
  shots still hit the rig), a sickly yellow-green (178, 236, 104: a paler one burnt to white). They go on the bodies
  every zombie is cloned from at the game's start, so the specials and the bosses have them too, scaled with them. No
  light per zombie (36 at a time); a boss gets a faint PointLight of the same colour on each client. The intro's gate
  crowd (ZombieCine `dress`): no face (it's the dynamic head's own picture: TextureID cleared) and eyes of their own,
  made on the client and half as big again (the server's can land a step after the film copies the body, and the
  game's size didn't read from the news lens under the searchlight).
- **The flashlight: F** (Binds "light", FLASHLIGHT (ZOMBIES) in Settings > KEYBINDS; a pad's D-pad up, otherwise
  unused; the phone's LIGHT button by RELOAD, lit while on). In a ZOMBIES game only, and not while your rope is on
  something (then F is the grapple's yank / reel, as before). The client asks the server ({ k = "light" } on the Zm
  remote); the player attribute ZmLight is the state, and every client draws every beam (ForestLife's pattern): a warm
  white SpotLight from the head (42 degrees, 48 studs). Yours rides your camera instead (the head doesn't tilt with
  your look), the only one with shadows. The click: zm_flashlight, PSE "Flashlight On Off Clicks 1" (9114479678,
  library, no upload; played from 0.3 s, where the click is).
- **The dark areas** (ZM.DARK: tunnels, the boiler room, the lockers hall, the gym wing). Before the power their 58
  lamps are off (tagged PowerLight at the start: ZombieExtra turns them on with the power), and while your camera is
  in one this client's light eases down to near-black over 0.6 s (Ambient 16,18,24, exposure -0.7: a faint fill, you
  can still move; you need the light to see them coming), and back as you leave or the power comes on. Films own the
  light (ZmFilm). The squad bots' flashlights come on in a dark area before the power (their body's ZmLight).
- **The lamps' panels go dark with them** (27 Nov, main: the glowing panels gave the unpowered areas away). The kit
  (tools/roblox/school_models.py, DARK_AREAS) puts the lenses of the fixtures in those four areas in a model of their
  own, sc_darklit (the rest stay in sc_fix_*; asset 87003238481034, in W.PATCHES.JankfieldHighV2B). ZombieLight's
  start hook turns it SmoothPlastic at its colour 55% to black until the arena's Power is on, then Neon again; the
  client's tube flicker (SchoolLife) holds those groups off and unlit until the power, then lights them.
  W.swap now removes a kit's overflow split (`<model>b`, `<model>c`...) when the patch brings the model but not the
  split (the old sc_fix_Ub drew the same lamps twice). Checked in Play (place version 1635): the tunnel lamp unlit
  before the power, glowing after.
- **Measured** (Studio, the boiler room, dark): four beams (yours with shadows + three bots') cost +0.07 ms render CPU
  (3.50 -> 3.57) and +0.23 ms GPU (3.40 -> 3.63).
- **Test traps.** `JankZombies open` opens every door AND turns the power on (no dark areas then): put the test player
  and the bots in a dark area by PivotTo instead. A held Scriptable camera is reset by the camera guard ("stuck,
  reset as V would") after a moment: hold it with a RenderStepped connection for photos.
- Sheet: roblox/docs/zombies/18-zombies-lights-27nov.jpg (dark without and with the light, the power on, the gate
  crowd's eyes). Place version 1631.

### 4.12 The sounds of a game (27 Nov; the owner: "Can we also have zombie sounds start of round sound effects that's like imposing like what cod has, find what needs sound effects in gameplay and add it no generated stuff")
client/ZombieSounds.client.luau (new); the picks and levels in roblox/assets/sounds/store.json (zm_*, written to Studio
by `node tools/roblox/store_sounds.mjs only=zm_`). All recordings: Pro Sound Effects from Roblox's licensed library (no
upload) and the CC0 takes already in JankfireSounds. The zombies' voices are the owner's exception to the no-voice rule,
ZOMBIES only: creature groans, snarls, shrieks, gurgles, roars; never words, never a crowd. Our own round sting: no
game's motif.
| Event | Sound | Source | Volume |
|---|---|---|---|
| Round starts | zm_round + zm_roundbell | PSE Boom Impact Deep Distant Thumping Hits (9125404320, 9125402735, 9125403433) + Church Bell Single Hits Double At Head 2 (9113804175) | 0.46, 0.58 |
| A boss round starts | zm_round + zm_roundboss, zm_gong 0.5 s on | Metal Tank Impact Deep Metallic Boom 1 (9116892160, from 0.65 s), Gong Chinese Style Single Hits (9125585534) | 0.33, 0.23 |
| A boss on the way | zm_bossroar, 1.6 s after the sting | Monster Vocals (9116967076, 9116967078, trimmed) | 0.46 x 0.85 |
| A round cleared | zm_roundend | Gong Hit Resonant Trail 1 (9114630316) | 0.26 |
| Zombies near you | zm_groan (6 takes) | Monster Vocals (9116966503, 9116968241, 9116966525, 9116966789, 9116967966, 9116967624) | 0.40, 10-90 studs, jitter 8% |
| One closes on you | zm_snarl (4) | Monster Vocals (9116965959, 9116966011, 9116965140, 9116965289) | 0.37 |
| Its attack | zm_shriek (3) | Monster Vocals (9116965782, 9116968466, 9116965514) | 0.65 |
| One dies | zm_zdie (2) | Monster Vocals (9116968247, 9116966797, trimmed) | 0.29 |
| A claw on you | zm_swipe + zm_claw (with the game's own hurt) | Whoosh Heavy Punches 1, 2 (9120728815, 9120728883); Punch Kit Beefy Hit 3, 4, 7 (9117969717, 9117969878, 9117970193) | 0.35, 0.06 |
| Someone goes down | zm_downed | Body Fall Heavy 3, Body Fall Thud 2 (9113470178, 9113480915) | 0.44 (x0.55 not you) |
| Someone's revived | heal (the game's) | | |
| A board torn off / nailed back | zm_planks / zm_board (CC0 takes already in the library, now wired) | Freesound CC0 (71149051809226, 91871213409913) | 0.7, 1.0 |
| Credits | zm_credit (at most ~8 a second) | Coin Throws 3 (9113849651, first 0.5 s) | 0.05 |
| A buy / a gun's ammo | zm_buy (+ zm_gunbuy) | Candy Machine Coin Drops Insert Vending 7 (9113704271), Ammo Magazine 1 (9113104176) | 1.3, 0.41 |
| A buy refused | empty (the game's dry click) | | |
| The power on | zm_power, then zm_flicker (the tubes' buzz) | Circuit Breaker 1 (9113808115) | 0.92 |
| A power-up | zm_roundbell x 0.45 | | |
| The extraction called | zm_gong x 0.8 | | |
| Lift-off's last 10 s | zm_tick each second | Mantle Clock 2 (9116466272) | 0.23 |
| Your HP under 30% | zm_heart, every 0.55 s near 0 to 1.1 s at the line, quieter as you heal | Freesound CC0 "Human Heartbeat (60 BPM)" by FenrirFangs (213181), one beat; upload 105380785242792 | 0.41 x (1 to 0.45) |
| A zombie walking near you | zm_step (4 drags), under 32 studs, while it moves faster than 1.5 studs/s, at most 4 a second in all | Freesound CC0 "Footstep Drag Indoors .wav" by abbahoot (221650), four drags as regions; upload 82254078949851 | 0.21, jitter 6%, roll-off 6-50 studs |
| You start a revive (holding the prompt) | zm_revive + zm_revpat | Freesound CC0 "Jacket/Cloth Rustle 9" by brandondelehoy (494797, 81612895656573); PSE Body Pats Cloth Hits 4 (9113532998) | 1.84, 0.92 |
| The mystery crate opens | zm_crate at the crate (its Spin attribute, so only the crate) | PSE Wood Groan Creak Opening Wood Chest Coffin 6 (9120881116) | 1.64 |
- **The voices' cap:** at most three zombie voices in any 1.6 s on a client, each zombie's next groan 5-12 s on (longer
  the more are near, longer still for a boss), a snarl once per approach (within 11 studs, reset past 18), a death
  gurgle 70% of the time, all positional (Sfx's roll-off) with pitch jitter.
- **Levels:** store.json targets (zm_round -20, roundboss -22, gong -24, groan -27, snarl / shriek -24, claw -29, swipe
  -30...). A recorded boss round clipped with everything at once (peak 1.0): the gong and the roar now follow the
  boom, and the recording peaks at 0.67 (place version 1634).
- **The gaps filled (27 Nov, place version 1635):** the heartbeat, the shuffle, the revive's start and the crate's creak
  (rows above). The two Freesound clips were uploaded once each. Logged in
  Play: at Hp 20 the heart beat every ~0.9 s, three walking zombies made ~2 steps a second, one crate buy one creak.
  The revive start isn't Play-tested yet (it needs a downed squadmate).

### 4.13 Dressed zombies and the phone check (27 Nov; main's small fixes)
- **The zombies dress like the gate crowd.** server/Zombies.luau `dress(m, kind)` on every plain zombie as it
  spawns: skin from DRESS_SKIN (muted grey-greens) leaned 12% to ZM.GAIT_COLOR, a worn dull shirt (DRESS_SHIRT), dark
  trousers (DRESS_PANTS), a torn sleeve 45% of the time (one arm skin), dark feet; the eyes stay. The specials and the
  bosses keep their own looks.
- **The phone check** (Studio, TouchForce on the player and TouchTest "fake:844x390"): the LIGHT button is in the
  touch cluster (by RELOAD); the buy and revive prompts are Roblox's own, which turn into tap buttons on a phone. Two
  overlaps found: the move stick sat over the round card and the spare rounds ran under the grapple and aim buttons.
  The fix moves them while TouchOn is set (ZombiesClient; checked in Studio, place version 1638): the round beside the credits
  (one line high), the spare rounds and the chips top right under the menu buttons. The dark areas' dimming is the
  same on any screen.


### 4.14 THE BRIEFING (27 Nov; the owner: "Can the cutscene static into like a green text pc code style menu? Thats where you select you weapons and passives and stuff? There will be a cool weapon graphic that's like a green grid hologram thing? It's like debrief after the news")
The plan (main's brief), then what was built under it.
- **Where it sits:** news -> gate -> static -> **BRIEFING** -> the school shot -> the squad -> round 1. The film
  (ZombieCine) holds its clock at the static's end (ZM.X.news.static[2], 5.2 s) while the briefing is up, and plays the
  school from BriefT1 on. A skip during the news lands you in the briefing (never past it); a skip after it ends the
  film as before.
- **The clock:** one shared timer, ZM.BRIEF.secs (18 s) from the moment it opens (BriefT0 = IntroT0 + 5.2, or sooner
  when every human skipped the news). READY: when every human is ready it closes at once. The bots pick at random (a
  passive; their gun is ZombieBots' own). Nobody can join a running game today; a member with no pick gets the
  defaults (the revolver, no passive).
- **The picks (the server checks and applies them; server/ZombieBrief.luau, new):**
  - a starting sidearm, one of four of the revolver's tier (ZM.BRIEF.sidearms): REVOLVER, PISTOL, SAWED-OFF,
    LEFTY & RIGHTY, with plain stats read from Weapons (damage, fire rate, magazine, reload, range, spare rounds). It is
    what you get back after being out (freshKit's m.startGun).
  - one passive (ZM.BRIEF.passives, our own names, plain words, never another game's perk names), for the whole game
    (going down doesn't lose it, unlike a cola):
    | Passive | What it does | Hook |
    |---|---|---|
    | BONUS PAY | +20% credits from everything you earn | creditMul |
    | HEAD MONEY | headshot kills pay 200, not 100 | creditMul (why "head") |
    | HOLD ON | down, you last 60 s, not 30 | bleedMul (new) |
    | MENDER | you start healing 2 s after a hit, not 4 | regenAfter (new) |
    | BOARD UP | boards go back twice as fast and pay 20 each, not 10 | boardTimeMul / boardPayMul (new, ZombieExtra) |
    | SCROUNGER | every kill puts 2 spare rounds back in the gun you hold | killed |
  - the Zm remote: { k = "bpick", w, p } (only while it's open), { k = "bready" }; arena attributes BriefT0, BriefEnd,
    BriefT1, BriefSquad (JSON: name, sidearm, passive, ready, bot).
- **The look (client/ZombieBrief.client.luau, new):** the static resolves into a CRT terminal: a switch-on line, a
  near-black green screen, scanlines, a faint flicker, green monospace text typed out with a block cursor; functional
  words only (LOADOUT, SIDEARM, PASSIVE, the stat names, READY, the timer, the squad's names and picks). The middle: the
  chosen sidearm as a hologram in a ViewportFrame: green see-through, an outline (Highlight), on a green grid with a
  ring, turning, a scan line sweeping up it. All four guns are built when the briefing opens and parked (only the
  picked one in view): nothing builds while you click.
- **Input:** mouse (click a row, READY), keyboard (W/S or arrows move, A/D or left/right change column, 1-4 the
  sidearm, Enter READY), a pad (PadNav: Roblox's selection moves between the rows, A picks, the bumpers change column;
  Pad.MENUS.zmbrief), touch (tap). MenuCursor "zmbrief" frees the mouse while it's up.
- **Sound:** recorded terminal sounds only (a switch-on, key ticks under the typing, a select blip, READY), from the
  licensed library.
- **Checks:** popscan on a recording of the static -> briefing -> school; a solo test and a test with 3 bots; a sheet and
  an MP4 to main.
- **Built and checked (27 Nov, place version 1638; one Play, three short games, solo + the 3 squad bots):**
  - Picks: 2 (keyboard) gave the pistol in hand with 72 spares; 3 the sawed-off (28 spares); the server's rows
    and the squad column agree; the bots showed random passives. Space in the news opened the briefing at once (its
    timer from the skip). READY with every human ready closed it as "ready" (BriefT1 = now + 0.35, the school shot from
    there, round 1 after the tail); left alone it closed on the timer.
  - The passive hooks through the whole chain (test op "bhooks"): BONUS PAY credit x1.2 (heads too), HEAD MONEY heads
    x2, HOLD ON bleed x2, MENDER regenAfter 2, BOARD UP board time x0.5 / pay x2, SCROUNGER 43 -> 45 spares on a kill.
  - The film: news -> static -> the switch-on (black, the line, the shutters part) -> the terminal -> the switch-off
    -> the school -> the squad -> round 1; the frames checked one by one at the cuts (popscan), nothing pops in. A late
    Enter meant for READY no longer skips the school: the film ignores skips for 1 s after the close.
  - The hologram: all four guns built at the open and parked; the outline (Highlight) is faint inside a ViewportFrame,
    the green see-through body and the grid carry it. At a phone's 844x390 everything fits; the squad's second lines
    and the stat names get small (~7 pt) but read.
  - Sounds (library, no uploads; store.json zm_term_*): zm_term_on (Switch Click On Or Off Toggle Button 2, 9119717523)
    + zm_term_hum (Electric Hum 15, 9114246115), zm_term_key (Relay Clicks 9, 9118138365) under the typing, zm_term_sel /
    zm_term_ready (Synth Chime Single Synth Tone 2, 9119802022, short / whole), zm_term_off (Switch Clicks Metallic Dull
    Pops 7, 9119717950). The library has no keyboard typing takes; the relay click stands in.
  - Sheet: side notes 20-zombies-briefing-27nov.jpg; clip zombies-briefing-27nov.mp4 (skip -> briefing -> round 1).

### 4.15 Dust in the light (27 Nov; the owner: "Can you add ambiance stuff like dust particles under light?")
client/ZombieDust.client.luau (new), built on HOUSE HUNT's client/HuntDust.luau, so its traps come with it (the VFX
library's soft glow at 0.11-0.13 studs and ~12% at their peak, lit by the scene; shafts of two plain bands with 12
segments and a faint emission; boxes pre-filled with :Emit so nothing fades up).
- Motes under the 8 nearest lit lamps (within 36 studs of the camera), a box from the lamp to the floor (the floor ray
  skips the fixture's own housing). A dark area's lamps are off till the power, so are its motes.
- A faint shaft under the 3 nearest lamps: its own pool, re-pointed each half second (a beam moves for nothing). The
  first take, warm at 0.9, read as a beige pillar under the school's cool tubes: now their own white (214, 226, 240)
  at 0.95.
- The 2 nearest zombie windows: a cool moonlit shaft in through the boards, motes in it.
- Your flashlight: motes in a box ahead of the beam, left hanging as you sweep; the scene lights them, so only the beam
  shows them. A dark area before the power: a few faint wisps round you.
- Switch: workspace attribute ZmDust = false. Cost (Studio, the lobby, 8 boxes + 3 shafts + a window): render CPU
  3.48 -> 3.50 ms, GPU 3.22 -> 3.29 ms (two runs, 3 s each). Place version 1640.
- Sheet: side notes 21-zombies-dust-27nov.jpg (before / after / the tunnel's beam / the rejected first shaft); clip
  zombies-dust-27nov.mp4.

### 4.16 No lag, no floating parts, cartoon dismemberment (27 Nov; the owner: "Make sure the zombies aren't laggy either make sure they can be dismembered and body parts aren't floating after they die!!")
- **Measured first** (Studio, round 21, 36 alive, solo + 3 bots, 10 s; the "cost" op now splits a tick by part):
  | | before | after |
  |---|---|---|
  | zombie AI tick (server, every 0.1 s) | avg 8.4 ms, max 16.8 | avg 2.8 ms, max 11.4 |
  | of it, the flow fields | ~3-4.4 ms a tick | 1.9 ms |
  | server heartbeat / worst frame | 2.2 ms / 49 ms | 1.2 ms / 20 ms |
  | server send | 35 kB/s | 37 kB/s (with ragdolls) |
  | client | 60 fps, render 3.9 ms | 60 fps, render 4.0 ms (worst frame varies 29-50 ms run to run) |
- **The fixes:** a flow field over the opened school costs 5-20 ms; several were rebuilt in the same tick (the spikes).
  Now one at a time, the stalest first, built 2.5 ms a tick (ZombieNav.flowBegin / flowStep) while the zombies walk
  the old one. A zombie's WalkSpeed and walk speed (both replicate) are written only when they change enough to see.
  The humanoid states a zombie never uses are off. Zombies were already server-owned (one owner, no flapping:
  Fight.track); corpses and loose pieces are server-owned too now.
- **No floating parts:** before, a death broke every joint (BreakJointsOnDeath) and flung the pieces apart one by
  one, gone at 2.5 s; a head shot off took no eyes and left the glowing eyes on the hidden head. Now a death is one
  ragdoll (Zombies.luau ragdoll: limited ball sockets, the root part gone so a zombie killed while climbing in falls
  too, hidden pieces gone, every piece collides with the map but not with zombies or players), it lies 3.2 s, fades on
  every client (ZmFade, client/ZombieBodies.client.luau) and goes; at most 10 corpses, the oldest first. A
  frame-by-frame floater check (a piece still and more than a stud above the floor) found nothing at the kill spot;
  4 flags elsewhere were likely bodies on desks and benches (the props can't be hit by rays); not checked by eye.
- **Dismemberment (cartoon, no blood):** ZombieSpecial's limbs, now picked by where the hit landed (Fight.hitAt: a
  shotgun at the legs takes the legs; no point known = the old dice), a limb comes off whole (its pieces welded), a
  frag counts as a blast (it isn't a Weapons row: before, grenades never took limbs), a head takes its eyes. The
  pieces keep the zombie's own colours, their ends are closed (nothing inside shows), a small grey dust puff and a dull
  thump where one comes off (zm_limb: PSE Body Slam Low End Thump 2, 9113535217). No legs: it crawls; one: it hops (as
  before). At most 24 loose pieces, faded with the corpses. Test op: JankZombies "zhurt" legs | head | blast | body, n.
- **Also:** the player's Hp attribute is written once the body's alive after a spawn (a fresh game after a down left
  it at 0). The school's hedges are B by the owner's pick ("B!!! A looks gross"): ZmGate.hedges sets the map's Hedges
  attribute and WebArena.swap re-applies it after a kit swap; A is one call away.
- Place versions 1644 (zombies) and 1645 (hedges B). Sheet: side notes 22-zombies-ragdoll-dismember-27nov.jpg; clip
  zombies-ragdoll-dismember-27nov.mp4.

### 4.17 The opening in the owner's order (27 Nov; the owner: "News static shot of the map computer terminal style menu when everyone ready shot of terminal closing and going into first person")
- **The order now:** the news feed (sirens, the gate crowd) -> static -> the school -> a push into the lobby terminal's
  screen until it fills the view -> the BRIEFING takes over (the same screen, full) -> when everyone's READY (or the
  timer ends) the picture hands back to the terminal, the CRT powers down in the world (a flash, the picture folds to
  a bright line, then a dot, then dark; the library's click and the hum pitched down as the whine) while the camera
  pulls back -> a push into your own first-person view at the desk, a footstep (step_hard) as you turn -> round 1.
  No squad shot. Times: ZM.X.news push 7.7-8.9 (ZM.BRIEF.at = 8.9), close 8.9-10.3, land 10.3-11.3; ZM.X.intro 11.3.
- **The terminal:** studio-tools/ZmGate.luau `terminal(map)`: an old beige CRT and keyboard on a dark security desk at
  the school's (0, 0, 55), in front of the spawns and facing them (built into workspace.Map.JankfieldHighV2B; every
  game's copy has it). Solid, CanQuery off (the nav grid doesn't see it). Its picture is each client's own
  (ZombieCine: a SurfaceGui on "Screen": the briefing's layout in small, its words fading as the push ends so the
  briefing comes in from plain green; the power-down on it at the close). How close fills the view comes from the
  window's own aspect.
- **The briefing's screen** (ZombieBrief.client) no longer switches itself on and off: it fades in over the
  terminal's picture and back to it (Veil); the film does the power-down in the world. A skip in the news still lands
  in the briefing.
- Checked in Play (place version 1647): the whole order recorded and read frame by frame. Left as polish: a short
  dark beat at the handoff into the briefing, and the very closest frame still shows the bezel at the sides in Studio's
  wide view. Sheet: side notes 23-zombies-intro-terminal-27nov.jpg; clip zombies-intro-terminal-27nov.mp4.

### 4.18 Plain names, moving dust, tubes that flicker and spark (27 Nov; the owner: "The dust particles look like they're not moving!! Can lights flicker too? Some electrical certain sounds etc?"; main: no jokes on screen, never CoD's power-up names)
- **Plain names** (ZM.luau, ids unchanged): every name on screen is a label of what it does. Colas ARMOR, SELF REVIVE,
  RUN SPEED, MORE AMMO, THIRD GUN; the machine UPGRADE (tiers UPGRADE 1-3, prompt "Upgrade"); its effects CHAIN SHOCK,
  BURN, FREEZE, LAUNCH, CREDITS PER HIT; modifiers ONE-HIT KILLS, DOUBLE CREDITS, NO RELOADS, RUN FASTER, SLOW ZOMBIES,
  BIG HEADS, HITS HEAL, HITS LAUNCH; drops +400 CREDITS, FULL AMMO, ALL ZOMBIES KILLED (ZombieExtra: BOOST MACHINE,
  RANDOM WEAPON; ZombiesClient: "<boss> summons more zombies"). Kept as names, flagged to main: the bosses and
  specials (THE FLOOR MANAGER, THE MASCOT, CHONK, ANKLE BITER, HARD HAT, SCREAMER).
- **Dust that moves** (ZombieDust.client `lively`): speed 0.4-1.0, drag 0.5, every direction, settling (-0.08),
  turning (+-120 deg/s), a size and transparency pulse over each mote's life (the twinkle), half again HOUSE HUNT's size
  and brightness; each box's sideways wander is re-drawn every 1.6-2.8 s; the flashlight's motes swirl away from the way
  the camera moves. A lamp lit in the last 4 s keeps its dust (a flicker doesn't hop the motes to another lamp); its
  shaft goes out and back with its light (shaftConn).
- **Fix, the window shafts:** ZombieDust took `-w.n` as inward, but a window's n points in, to the play side (Zombies
  spawns at `out` facing n), so the moon shafts slanted out of the building. Now they fall into the room.
- **Tubes that fail like fluorescents** (SchoolLife.client), each group on its own clock (3-12 s): blinks (45%), a
  struggling restart (20%), a dying stutter of at most 0.9 s into a dark spell, a spark 35% of the time (20%), a long
  dropout (15%). The fitting's glow, the group's lights and the fill light beside each fitting (an untagged light within
  6 studs) go out together: the room dims (18% in the test room). Seizure safety: the room's light changes at most 3
  times a second (ROOM_GAP 0.34 s; measured: room-wide changes 0.33 s or more apart); only the small fitting stutters
  faster; a spark flashes once. A dark area's tubes stay off till the power, then each restarts within 1.5 s. Dead for
  good: groups 3, 9, 15, 20.
- **Sparks:** 24-34 long hot streaks (the VFX library's vfx_spark, Squash 1.6, 9-18 studs/s, gravity 55), one 0.06 s
  flash (range 16), 6-12 more spat a beat later, the crackle.
- **Electrical sounds** (recordings from Roblox's licensed library, store.json): zm_tubehum looped on the two nearest
  lit tubes (within 30 studs, silent while out), zm_ballast as a tube catches (within 45 studs, at most every 0.08 s),
  zm_spark, and now and then (18-42 s) a distant zm_arc or zm_relay from a tube 30-90 studs off. They come from the
  group's fitting nearest you (a group spans floors).
- **Bots' path fields** are stepped jobs too (ZombieBots.fieldTo, BOT_FIELD_MS 2 a frame).
- **Test hook (Studio):** player attribute ZmFlickTest = "spark" | "restart" | "dying": the nearest lit tube does it.
- **Checked in Play (place version 1650):** a clip under a lit tube (a spark, a restart, a dying stutter) with its
  sounds; the dust's render cost is noise (CPU 3.64-3.76 ms on, 3.65 off; GPU 3.75 both; 60 fps); zombies on a client:
  walkers' per-frame tracks steady at 8-10 studs/s, no jumps (a legless crawler hops, as designed); 8 corpses all on
  the floor (lowest part within 0.1 stud). Sheet: side notes 24-zombies-flicker-dust-27nov.jpg; clip
  zombies-flicker-spark-27nov.mp4.
- **Trap, the recorder:** Studio's video_capture all but drops positional sound (a 2D spark records at -31 dB, the same
  spark 3 studs away in 3D at -78 dB). For a clip with sound, the test harness mirrored each zm_ sound flat at its
  Atten (Sfx sets it on every copy) and the hums at their distance gain. Not shipped.
