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
- Buying and reviving are ProximityPrompts on **F** (as on the web; E is our grapple, F only yanks while hooked to a
  person). Shutter 0.3 s, wall gun 0.3 s, revive 3 s.
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
