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
