# HOUSE HUNT: one gunman, everyone else hides (the hunt mode)

Started 26 Nov 2026 by the hunt-mode session (`local_df23b97f`, the session in this file's commits). This is the plan.
Each stage adds its "as built" notes below the plan.

## 0. What was asked

The owner, 25 Nov (verbatim, trimmed to this mode):

> The new gamemode will start in a new lobby, we'll teleport you there since itll technically be a new game, but with
> the same like movement and stuff? That way don't have to change so much.
>
> Youll be in a house, with a backyard, there will be trampoline a garage tables outside for gamepasses with stuff.
> Itll be a bigish house so we can fit props inside, and people will spawn inisde and wait for a new game to start!
> They can ruyn around interact wsith stuff, punch push super push. Push is funny, if youy lay down look up and push
> youll send pepole flying. We need a stand, walk, run, crouhch, and laying down animations for player as well as a
> shove for push and a wind up punch! Hiders can also buy traps like a bear trap, some sort of spray, a tasaer, etc..
>
> The gunman will have a random gun from ar to sniper to shotgun etc..,. Hiders bodies can be "dismembertedd" but itll
> be l;ike blocky particles with some blood effects, headshots aalways kill instantly! If you hide for 2ish minutes you
> will be given a chance to fight back, you'll have the chance to find and search for weapons around the house like a
> kitchen knife golf club etc! well depending on the mpa, it needs to be large enough that people can hide for 2
> minutes you know?
>
> For now make the new game an extnesion in the current studio maybe? can we allow teleport to toher games? it wont
> have any grappling!

The friend's idea he pasted: "A gamemode where there is one killer, and everyone is a hider. Killer has a gun and must
search for people! Crouching, running, pushing super pushing punching are survivor kits, killer gets a gun and various
passives!"

Main's decisions (not re-asked): a far area of the one place, ready to become its own place in the same experience;
the main game's movement with no grapple; the house lobby with a real trampoline, a garage and outdoor tables that
show only the existing store items (VIP, coin packs, cases; THE ROBUX RULE, no new products); mocap animations on R15
and R6; a random gunman with a random main-game gun plus passives; traps bought with in-round points; headshots always
kill; fight-back weapons after about 2 minutes; deaths as blocky cubes in the avatar's own colours with a few
pink cubes (the owner, 27 Nov: "can the blood actually be pink instead?"); the house judged against the ring hub by two blind judges; chunky, structured, quiet colours, no
flavour text, recordings only, anti-AI critic on the UI; not named or styled after any existing game.

**The name.** HOUSE HUNT (the mode), THE HOUSE (its lobby). Plain words, no other game's name or look. Code files are
`Hunt*` so they sort together. The on-screen name is one constant, `HuntConfig.TITLE` (the lobby's is `HOUSE_TITLE`),
so a rename is a one-line change. The mode was called HOLDOUT until 27 Nov, when the owner picked HOUSE HUNT.

## 1. Where it lives (now, and as its own place later)

| what | where |
|---|---|
| the lobby, THE HOUSE | `workspace.Map.HuntHouse`, origin **(0, 300, -90000)** |
| the round maps (sources) | `workspace.Map.<Name>` (an existing map) plus a marker set `ServerStorage.HuntMaps.<Name>` |
| a round's copy of its map | **(7000·k, 300, -96000)**, k = 0, 1, 2 (destroyed after the round) |

- Why there: every map in the place sits on the x = 0 line between z -78000 (the newest school) and +102000 (Suburb v2),
  and match copies go out along x at ±7000 from their own arena's z. Nothing is at z < -84000 (scanned 26 Nov).
- Why y 300: outside a match, Matches voids anyone 60 studs under the hub's Origin (y 240), so the lobby must stand over
  y 180.
- Every uploaded kit stays inside ±1,000 studs of its own origin (the 2,048-stud upload shrink, memory
  `roblox-web-arenas`). The house and both yards are about 330 x 260 studs, the trees and back gardens round it reach
  about ±600.

**Getting there and back.**
- From the hub: a HOUSE HUNT card on the PLAY screen's MODES tab (play-party's `ModesTab`; one card, one remote op), and
  any part tagged `HuntPortal` gets a GO TO THE HOUSE prompt. Hub builders can drop a portal frame into their hubs
  later, and the card works from day one.
- Back: the house's front door (BACK TO HUB). PLAY from the house works as it does anywhere in the hub.
- `server/HuntTravel.luau` is the only code that moves people between the hub and the house: `go(p)`, `back(p)`.
  Today it's a server PivotTo with `TeleportT` stamped (the anti-cheat contract).

**Ready to be its own place.** Everything the mode needs is in its own files (`Hunt*`), its own maps and its own
markers, and it reaches the rest of the game only through the hooks listed in section 3. To split it off:
1. The owner adds a second place to this experience (Creator Hub, the experience's Places, Add Place) and publishes
   this place file into it once. Publishing is the owner's.
2. Set `HuntConfig.PLACE_ID` to that place's id (nil today = in this place).
3. `HuntTravel.go` then calls `TeleportService:TeleportAsync(PLACE_ID, { p }, options)` with teleport data
   `{ from = "hub" }`, and `back` teleports to the start place. In the hunt place, `workspace` attribute
   `PlaceRole = "hunt"` makes new players spawn in the house instead of a hub.
4. Nothing else changes. DataStores, MemoryStores, the VIP pass, developer products and badges belong to the
   experience (the universe), not the place, so coins, skins, loadouts, ranks and VIP carry over by themselves.

**The owner's question: can we teleport to other games?** Yes, technically, with limits:
- **Inside one experience** (what this plan uses): teleports carry the player, and every place shares the
  experience's DataStores, passes and products. Nothing to copy.
- **To another experience** (a different universe): possible with Game Settings → Security → **Allow Third Party
  Teleports** on the experience you leave from. What travels is only the player and a small teleport-data table
  that the client can read and tamper with. That other experience has its own DataStores, its own passes and its own
  products: coins, skins, VIP and ranks don't carry, and teleport data can't be trusted for them. The only way to
  share a save across experiences is an outside web server through HttpService, which is a backend to build and run.
- So: a second place in this experience, not a new game.

## 2. The lobby: THE HOUSE

A big two-storey family house with a front yard, a back garden and an attached garage. Everyone in the mode spawns
inside and waits there between rounds. It is the mode's hub, so it gets the hub's quality bar (section 9).

**The plan (studs; floors 16 apart: 15 clear, a 1-stud slab; outside walls 2 thick, inside 1):**
- Footprint: the house about 128 x 88, the garage 44 x 44 on its east side, the back garden about 170 x 110, the front
  yard and driveway about 40 deep.
- **Ground floor:** an entry hall with the main stairs (a straight flight to a landing, then a turn), a living room
  (sofas, TV wall, fireplace, rug), an open kitchen with an island and a dining table, a downstairs bathroom, a
  laundry/mudroom through to the garage, and glass sliding doors from the living room to the patio.
- **Upper floor:** a landing hall looking down over the entry (a gallery), the main bedroom with its own bathroom, two
  more bedrooms (one with a bunk bed), a study, a family bathroom, and a balcony over the patio.
- **Garage:** a roll-up door to the driveway (a wall button opens it), a car, a workbench, shelving, bikes, a chest
  freezer.
- **Back garden:** the patio with the three store tables, a lawn with the TRAMPOLINE, a tree, a fence round it all, a
  shed and a gate back to the driveway. **Front:** the driveway, a basketball hoop on the garage, the path, a mailbox.
- Doors are real doors (they swing open as you walk into them, and shut behind you a few seconds later).
- Headroom for lying down: beds and the dining table stand 3.5 studs clear, so a hider lying down can roll under them.

**The look:** the chunky kit rules (`chunky-model-style`): few big rounded shapes, bevelled, flat mid-value colours,
white light panels in real housings with real lights behind them. Structure first (`structure-over-colour`): thick
walls with framed openings, skirting and cornices, a coffered or beamed living-room ceiling, the stair as a real
built piece with a newel post and a solid balustrade, window bays, a porch with posts. Subtle texture on big surfaces
(oak floor, tiled kitchen and bathrooms, carpeted bedrooms, painted plaster, brick and siding outside, paving, lawn).
A quiet palette (`less-colourful-look`): warm whites, greys and wood; colour only on the store tables and the
trampoline's pad. No floor marks in the round maps (`no-floor-marks-in-matches`); the house may have rugs.

**Built the proven way** (the Jankfield High pipeline, memory `roblox-jankfield-high`):
- `tools/roblox/hunt_house_layout.py`, plain Python, one source:
  - the rooms per floor;
  - the walls worked out from the rooms;
  - doors and windows cut by position;
  - stairs as collision ramps under drawn steps;
  - furniture with hit boxes;
  - the markers: spawns, interactables, shop tables, the trampoline, lights.
- `tools/roblox/hunt_house_models.py` (headless Blender) builds the kit: one `.glb`, split under 10k triangles a mesh.
- It also writes `roblox/studio-tools/HuntHouseLayout.luau`.
- `WebArena` builds it like any arena: `W.import("HuntHouse")`, `W.build("HuntHouse")`. It then gets `Enabled = false`
  (never in the PvP pool), its own Look (`HubLook.looks.hunt_house`, a soft afternoon) and ZonePiece (ZoneCull culls it).
- `studio-tools/HuntBuild.luau` then adds what WebArena doesn't know: the `Hunt` folder of markers, the doors, the
  interactables and the zone box `HuntZone`.
- Plan note in the vault `Hubs\The House (HOUSE HUNT lobby) plan.md`. Judge rounds go in vault `Reviews\`.

**What you can do in the house:**
- Run, slide and crouch as in the main game. No grapple anywhere in the mode, no weapons in the house.
- Punch, push and super push other players. In the house these knock people around but do no damage.
- Lie down. Lying on your back looking up, a push throws people straight up.
- The trampoline bounces you higher each jump timed on landing, up to a cap, and anyone landing on it bounces.
- Interact with props: lights on every room switch, the TV, taps, the fridge, the garage door button, the
  basketball (a real ball you can throw at the hoop), beds you can bounce on, every chair and sofa (`HubSeat`).
- Shop at the three patio tables: VIP, COINS and CASES. Each opens the existing SHOP at its own tab, through the
  `ShopOpen` prompt attribute. No new products.
- A board on the living-room wall shows the next round: players in the house, the countdown, the map. That is
  information, not flavour.

## 3. How it plugs into the game (the code)

New files (all ours):
| file | what |
|---|---|
| `shared/HuntConfig.luau` | every number in this doc, the gun pool, passives, traps, the fight-back weapons, `PLACE_ID` |
| `server/Hunt.luau` | the lobby queue, the round loop, roles, points, traps, search spots, deaths, the Fight hooks |
| `server/HuntMoves.luau` | punch, push, super push, lie down: the server's checks and the knock |
| `server/HuntTravel.luau` | the hub ↔ house moves (and the teleports once it is its own place) |
| `server/HuntServer.server.luau` | start-up, the remote `JankfireRemotes.Hunt`, the Studio test hook `ServerStorage.JankHuntTest` |
| `client/HuntClient.client.luau` | the HUD, the trap menu, prompts, the gunman's passives on screen |
| `client/HuntMoves.client.luau` | the move keys, aim of a push, the wind-up |
| `client/HuntAnims.luau` | the hider animation set (stand, walk, run, crouch, lie down, shove, wind-up punch) on R15 and R6 |
| `client/HuntFx.luau` | the cube break-up, trap effects, the spray blur |
| `studio-tools/HuntBuild.luau`, `HuntHouseLayout.luau` | the house's builder and layout |

Hooks into shared code, each chained (the previous function is kept and called), never replacing anyone's:
- `Fight.allow`: in a round, gunman ↔ hider hits count, hider ↔ hider never. In the house nothing hurts.
- `Fight.modDamage`: a headshot on a hider is a kill, plus the passives.
- `Fight.holdRespawn` and `Fight.spawnAt`: the dead watch till the round ends, then spawn in the house.
- `Fight.noItems`: no main-game gadgets in the mode.
- `Fight.onKill`: the break-up and the points.
- `Matches.zoneHook`: a player in a round reads as Zone `"match"`, as in a zombies game, so the hub menus hide and
  the fall line is the map's. The house stays Zone `"hub"`, so weapons are holstered and nothing hurts. Zombies sets
  this hook without chaining, so Hunt re-wraps whatever is there every tick instead of trusting its first wrap.
- `Rules` forced kits (`f.forced`, the classic modes' way): the gunman gets `{ gun }`, with spare rounds kept full.
- **One-line hunks in other sessions' files** (each owner told before it goes in):
  - `Unarmed` player attribute (server-set): `Fight.holstered`, Arsenal's `inHub()` and HubHolster treat it like the
    hub. Hiders carry nothing in a round.
  - `NoGrapple` player attribute (server-set): Move.client's tryHook / tryYank / tryLock and Main.server's hook
    handler refuse. Set on everyone in the house and in a round.
  - CrouchPoses stands down for a body whose `HuntAnim` attribute is set (the hider set has its own crouch and
    lie-down).
  - ModesTab: the HOUSE HUNT card.

## 4. Moves (hiders always; everyone in the house)

| move | key (pad / phone) | what it does | numbers |
|---|---|---|---|
| punch | click (RT / PUNCH) | tap = a jab; hold = the wind-up, let go = the haymaker | jab 6 dmg; haymaker after a 0.5 s hold, 18 dmg + a 35 shove; reach 6, cone 50°; 0.45 s between |
| push | E (RB / PUSH) | a two-handed shove along your look | 45 shove sideways + 12 up; reach 7; 1.2 s cooldown |
| super push | hold E 0.8 s | a big shove | 105 + 40 up; 8 s cooldown |
| lie down | X, the auto grapple's key (D-Right; no phone button yet) | on your back; slow scoot; fits under beds | 2.4 studs tall, 6 studs/s |
| launch | push while lying | the push goes along your whole look, up included | x1.4, the up part uncapped |
| crouch, slide, sprint | the main game's | unchanged | Config |

- Damage only lands on the gunman, and only in a round.
- The server judges reach and cone from its own copy of the bodies, as boxing does, or it's a whiff.
- Knocks go through `Fight.knock`, which the anti-cheat already knows.
- The gunman can be shoved too. With FIRM STANCE he moves half as far.

## 5. The round

**Flow:**
1. **Lobby.** A round needs 2 or more players in the house. The board counts down 20 s; anyone who walks in
   before it ends is in.
2. **Hide, 20 s.** Everyone goes to the map's copy. Hiders spawn spread out; the gunman waits in a sealed room with
   his screen dark. The HUD says HIDE and the time.
3. **Hunt, 4:00.** The gunman is let out.
4. **Fight back, at 2:00 into the hunt.** The map's search spots open. Hold F at a drawer, cupboard, golf bag or
   toolbox for 1.5 s; some hold a weapon, the rest are empty. Each spot gives one weapon and is then done.
5. **The end.** The gunman wins when every hider is dead. The hiders win when the clock runs out with one alive, or
   when they kill the gunman. A 6 s results card, then everyone back to the house.

**The gunman:**
- Picked at random. The last round's gunman sits out the pick unless they're the only player.
- 250 HP; hiders have 100.
- One gun at random from the main game's real guns: `ar, smg, shotgun, sniper, burst, lmg, dmr, lever, autoshot`.
  Spare rounds never run out. Wraps, hats and skins show as the player owns them.
- **Headshots always kill a hider**, whatever the gun.
- **Two passives** drawn at random each round, named on his HUD and on the hiders' HUD in small type:

| passive | what it does |
|---|---|
| PULSE | every 25 s, hiders within 60 studs show through walls for 1.5 s, to him only |
| TRACKS | a hider who sprinted or slid in the last 3 s leaves faint footprints he can see |
| QUIET STEPS | his footsteps make no sound |
| THICK SKIN | +100 HP |
| FIRM STANCE | pushes and punches move him half as far |
| QUICK HANDS | reloads and the draw are 40% faster |

**Hiders:**
- Unarmed, no gadgets, no grapple.
- Points: they start with 10 and earn 1 every 3 s alive in the hunt, 5 a punch landed on the gunman, 8 a push
  landed on the gunman, and 20 when one of their traps catches him.
- **Traps** (B opens the menu, two carried at once, keys 1 / 2 to use):

| trap | cost | what it does |
|---|---|---|
| BEAR TRAP | 30 | placed on the floor; the gunman steps in: held 3 s, 20 dmg |
| PEPPER SPRAY | 25 | 3 puffs, a 12-stud cone: his view goes white and blurred for 3 s |
| TASER | 40 | one shot, 18 studs: he can't move or shoot for 2 s |
| SMOKE BOMB | 20 | a 14-stud cloud for 8 s that hides everyone in it |
| MARBLES | 15 | a spill; whoever runs over it slips, as the Marble Shotgun's marbles do |
| DECOY | 20 | footsteps that walk from where you drop it, for 10 s |

- **Fight-back weapons** (search spots, after 2:00):

| weapon | damage | swing |
|---|---|---|
| KITCHEN KNIFE | 35 | 0.45 s |
| FRYING PAN | 40 | 0.7 s, a big knock |
| GOLF CLUB | 45 | 0.8 s, long reach |
| BASEBALL BAT | 50 | 0.9 s |

  Each map lists which weapons hide where (a kitchen for the knife and pan, a garage or golf bag for the club, a gym
  for the bat).

**Maps.** A map must hold a 2-minute hide: several floors, many rooms, loops and hiding spots.
- **No schools (main, 27 Nov, not negotiable).** A lone gunman hunting unarmed people through a school is a
  school-shooting scenario: against Roblox's rules on real-world violent events, and a reason to moderate the whole
  experience. So no schools, churches, malls or offices full of desks, nothing that reads as a real-world attack site,
  for any map, now or later. Homes, mansions, backrooms, parks, warehouses and the like are fine. Jankfield High was in
  the first map list and is out for good.
- The round loop runs on **THE HOUSE** (a copy of the lobby, its doors, exit and tables stripped), **the Backrooms**
  and **Suburb v2**, then the manor once it is built.
- Stage 4 adds a purpose-built **manor**: three floors and a basement, a garden and a pool house.
- Stage 4 also converts maps we already have where they work for hiding: the Backrooms, the Arctic Cabin and Suburb
  v2, each with a marker set only. (The Station is off this list since 27 Nov: a station reads as a real-world attack
  site, by the no-schools rule above.)
- **The marker contract:** `ServerStorage.HuntMaps.<Name>` (a Model placed in the map's own space):
  - `HiderSpawns`;
  - `GunmanPen` (the sealed room and its door);
  - `GunmanSpawn`;
  - `SearchSpots` (attribute `Weapon`, or `Weapon = ""` for empty);
  - `Bounds` (the box you must stay in);
  - attributes `Title` and `Look`.

## 6. Deaths: the cube break-up

When a hider dies, every client hides the body and puts small cubes where it was.
- Each body part is split into a few cubes in that part's own colour, from the avatar's own BodyColors and the
  clothing's average.
- The cubes fly with the hit, bounce and fade out over 4 s.
- About a dozen smaller pink cubes come with them, fading out in 1.5 s: a soft sakura pink (255, 176, 204), never
  red (the owner, 27 Nov).
- Plain Parts made on the client: nothing is uploaded, no textures, no body parts and no realistic blood. The gunman
  breaks up the same way if the hiders kill him.

**The maturity questionnaire** (Roblox's Content Maturity page, read 26 Nov 2026; the owner fills the questionnaire):
- **Violence:** stays "unrealistic". Roblox counts bodies that "disappear the moment their health reaches zero" as
  mild, and lists "characters falling apart before respawning" among its unrealistic examples. Cubes in the avatar's
  colours, with no limbs or body parts coming off, are not "dismemberment", which Roblox puts under Restricted only
  when it looks realistic. Frequency "repeated" (a shooter), which is already the case.
- **Blood:** the answer changes from "no" to "yes, unrealistic" ("a different color or shape": pink cubes). Blood in
  a clearly unreal colour is the questionnaire's "unrealistic blood" answer. Whether it is
  "infrequent and/or fleeting" decides the level:
  - yes (a second or two, now and then) → light unrealistic blood → Minimal;
  - no → heavy unrealistic blood → Mild.

  Answer it as the most a player can see: a hider death every round, so "no", which is **Mild**.
- **Net:** the experience's label becomes at least **Mild**. Repeated mild violence alone already makes a shooter Mild,
  so the label most likely doesn't move at all. The risk is anything that looks like a real body part or real blood
  at any moment, which would push it to Moderate or Restricted. So: cubes only, no limb shapes, no red texture, no
  pools on the floor.

## 7. Animations (the hider set)

All mocap from the owner's Mixamo account (memory `roblox-ai-animation`, `poses-from-references`), retargeted with
`tools/blender/mixamo_r15.py` and a new R6 sibling, `tools/blender/mixamo_r6.py`. The R6 retarget maps each R6 part
onto its bone's chain: the Torso follows the spine, each limb follows its upper bone. Each clip is uploaded as an
Animation under the owner, with ids in `HuntConfig.ANIMS`.

| move | source | loop |
|---|---|---|
| stand | vault `mixamo-17nov/05_dune_breathing_idle` (or 16_idle_male) | yes |
| walk | Mixamo "Walking" (new download) | yes |
| run | vault `mixamo-19nov/02_sprint_standard` | yes |
| crouch (still / moving) | Mixamo "Crouch Idle" + "Crouched Walking" (new) | yes |
| lie down / lying | Mixamo "Lying Down" + "Laying Idle" (new) | the idle loops |
| shove | Mixamo "Push" (new) | no |
| wind-up punch | vault `mixamo-18nov-boxing/30_knockdown_punch` (the haymaker): the hold freezes at the wind-up, the release plays the rest | no |

- `HuntAnims` plays these from the walk speed and the move state on the local body. The Animate script stands down
  while the body has `HuntAnim`, and Roblox replicates the tracks to everyone.
- The gunman keeps the main game's own animations and gun poses.
- The FBX files stay in the vault, never in git.

## 8. Sound and UI

- **Sound:** recordings only, from Roblox's licensed Pro Sound Effects library first. Footsteps, trampoline springs,
  doors, the shove (cloth plus a body thud), the punch, the bear trap snap, the spray hiss, the taser crackle, the
  garage door motor, the TV and the taps. No voices, no crowd, no screams.
- **UI:**
  - The round timer and phase, top centre.
  - The role, then the gunman's two passives in small type.
  - The points and the two trap slots, bottom right.
  - The trap menu (B): 6 tiles, price and one plain line each.
  - The results card: who won, the gunman's kills, the survivors.
  - The style follows the ui-mocks direction once the owner picks one, and is judged by the anti-AI player critic
    until every element reads real (8+).
  - No flavour text anywhere; HIDE, FIGHT BACK and the trap names are labels.

## 9. Stages and checks

Each stage ends with a frame sheet sent to main, a commit on `claude/f-roblox-studio`, and a save.

| stage | what | done when |
|---|---|---|
| 1 | THE HOUSE, both yards, movement (no grapple), the moves, the animations, the interactables, the shop tables, the way in and out | two blind judges, averaged, put it at or above the ring hub overall and on chunkiness, with no copy flag; a function test with Studio test players: walk every room, punch, push, super push, the launch, the trampoline, each prop, each table, the hub ↔ house moves, R15 and R6 |
| 2 | the round loop on THE HOUSE, the Backrooms and Suburb v2 (copies) | a round with Studio test players: roles, the gun, headshots, the break-up, timers, win and lose both ways, back to the house |
| 3 | the traps and the fight-back weapons | each trap and each weapon used on the gunman in a test |
| 4 | the manor and the converted maps | each map: a 2-minute hide checked with test players, the marker check, ZFight |

**Tests** use Studio's Test → Server + 2 or more clients for the moves and the round, plus `ServerStorage.JankHuntTest`
(`state`, `start`, `role`, `points`, `trap`, `end`) for one-player checks. The Studio lock and queue rules apply
(`side-session-notes/STUDIO-TURNS.md`).

## 10. Decided, so not asked

- The lobby is Zone "hub" (holstered, no damage), a round is "match". So there are no zone-name changes in other code.
- Stage 2 runs on THE HOUSE, the Backrooms and Suburb v2 until the manor is built (no schools: section 5).
- In-round points are per round, not saved. The only saved things are the usual XP, coins and quests (a round counts
  as a match for them: a win, a kill).
- Rated? No. HOUSE HUNT is unranked.
- Players per round: 2 to 12. The pick is 1 gunman for up to 8 players, and 2 gunmen from 9 (stage 2 builds 1; 2 is
  a switch, `HuntConfig.TWO_AT`).

---------------------------------------------------------------------------------------------------------------------

## 11. The gunman's intro (owner, 27 Nov)

The owner: when you're the gunman, a cinematic fills the hiders' head start. A person in a dark room, cinematic angles,
they start to go crazy, then "boom!": an angle from above as they look up, a cut outside, they look down, the angle
swings round behind them, the bars lift, and you're looking at the outside of the map.

**The beats** (the gunman's client only; the hiders get the head start as now, at most a short sound cue at its end).
The intro lasts exactly the hide time, so both are one number, `HuntConfig.ROUND.hide` (16 s to start):
1. **The room** (0 to 5.5 s): the gunman stands in the middle of a dark room, letterbox on. Three slow shots: a low
   wide, a slow push, a profile. The only light is the screen's.
2. **The build** (5.5 to 10.4 s): they start to lose it. Twitches, the head jerking, shoulders heaving; the screen's
   flicker and the camera shake grow, the cuts get shorter.
3. **The snap** (10.4 to 11.4 s): a hard hit cut to straight above as the head snaps up into the lens.
4. **Outside** (11.4 to 13.4 s): a cut to the gunman standing outside the round's map, looking up at it.
5. **The turn** (13.4 to 16 s): they look down; the camera swings round behind them, the bars lift, and control is
   theirs. The last camera frame is the gameplay camera's first, so nothing pops.

The gunman can't move during it. It ends on the hiders' clock even on a phone or a slow load (each beat is skipped
to, never waited for).

**Two rooms, the same beats** (the owner: "we can try both"), as swappable sets: the props in one model, the light
source one part with its light:
- **A, their bedroom:** the only light is a PC screen, a cool flickering blue-white on the face and the walls.
- **B, an attic:** the only light is an old TV showing static.

**Guardrails** (a fictional horror villain, never a real-world attack's build-up):
- No gun anywhere in the intro: no loading, cocking or weapon close-ups.
- No mask (the owner, 27 Nov: "No mask for the killer!"): the gunman is his own avatar, in the intro and in play.
- The screens show nothing readable: glow, colour and noise only. No text, chat or pages.
- Plain props only: nothing on the walls that reads as a real-world symbol, poster or message.
- Motion is mocap only (no hand-posing). Sounds are recordings with no voices (the owner's order, 27 Nov): the
  room's hum (PC fans, a fridge; B adds its TV's static) and a heartbeat that gets louder and faster up to the
  snap (one looped APM beat, PlaybackSpeed 0.85 to 1.85 with a PitchShift holding its pitch, the hum ducking under
  it), the hit on the snap, then peace: birds outside, carrying on past the hand-back and fading out. The ids and
  levels are in `HuntConfig.INTRO.sounds` (levels from Studio's AudioAnalyzer, place v1460). No breathing, no screams.
- The owner's liminal grade (27 Nov): a washed-out grey (`HuntConfig.INTRO.grade`: a ColorCorrection and a soft blur
  on the camera) over the whole film, lifting into the game's own colour with the bars. Clips: side-session-notes
  `holdout/intro_A_v5_grey` / `intro_B_v5_grey` (`_small` copies), sheet `intro_AB_sheet_v1460_grey.jpg`.

**Where the gunman comes in:** each map gets an `outside` spot (x, y, z, facing) just outside it, facing in. The
gunman is released there, not inside.

**Tech:** `client/CineKit.luau`, the one shared cinematic piece (letterbox, a shot list stepped against a clock, the
finishers' handheld shake and hit kick, the hand-back onto the gameplay camera). The finishers and the victory scene
move onto it with their next scenes. `client/HuntIntro.client.luau` plays the intro; `shared/HuntIntroData.luau` (made
by the intro script) holds the rooms' screens. The mocap: `HuntConfig.INTRO.anims` (vault clips; the Mixamo list for
better takes is with main). While it plays every HUD is off (the hide shade covered the first recordings, v1415).

**Played in Studio (v1415 to v1442):** both rooms on their beats, no HUD while it plays, the hand-back onto the
game's own camera with no pop (CineKit's `warm` lets the game's camera take the type back for the last 0.6 s while the
shot still places it, and points it at the current body: the round re-makes the gunman's body). The owner's sheet:
side-session-notes `holdout/intro_AB_sheet_v1435.jpg` and the clips `intro_A_v3` / `intro_B_v3` (`_small` copies).

## 12. The win films (owner, 27 Nov)

The owner: "If you win as killer start the walk with destroyed place and then zoom out with static to imply it was you
still at your desk and it was just a game you were playing?? Same with survivors? But instead it's the attick me a group
of friend (survivors)". Everyone in the round sees the winners' film (`HuntConfig.OUTRO.len`, 11 s), then the results
card; HuntRound.finish sends Remote `outro` { win, who, map, mapId, origin, len, t0 } and holds the card. `HuntOutro.client`.

- **The gunman wins:** a slow walk through the house (`MAPS[].outroWalk`: a path and where to look; else from where he
  stands, forward), cushions knocked to the floor and the last pink cubes fading. No blood, no bodies. A hit-stop (the
  house holds its last frame while the lens kicks), full-screen static, then the lens pulls back out of the monitor in
  room A, which shows the house as the lens last saw it (a ViewportFrame of the map's pieces near it). His own avatar sits
  at the desk, lit by the screen; on the reveal he leans back and stretches.
- **The hiders win:** the survivors together in the house (`MAPS[].outroGroup`), out of breath, then the same static
  and the pull back out of the attic TV in room B. The same avatars as friends: two on the couch, one in the sheeted
  armchair, the rest standing behind, each with a pad in hand, cheering, clapping and fist-pumping.
- **Rules:** both rooms are canon (A the gunman's bedroom, B the friends' attic). Screens show only the game's own view,
  glow and static; nothing readable. Mocap only: the vault stand-ins (seated breathing, seated arm stretch, upper-body
  clapping, cheering and fist pump; ids in `HuntConfig.OUTRO.anims`) until the Mixamo list (Sitting, Typing, Sitting
  Clap, High Five) lands. The intro's muted grade, CineKit's bars and kick, frills fading between the lens and a face.
- **Sound** (recordings, no voices): birds through the walls in the house, a static burst, then the PC's hum (A) or
  the TV's hiss (B), keys, pad clicks, a sofa creak and single hand claps, each at one friend (never a crowd).
- **Kit:** the intro's kit (`hunt_intro_models.py`, hunt_intro3 = 123000465026529): the office chair is its own piece
  (`hiA_chair`: pushed back in the intro, at the desk in the film), `hiB_couch`, `hiB_pad`, `hiW_cushion`; the spots
  are in `HuntIntroData.spots`.
- **Test:** a round, then `JankHuntTest("win", p, "gunman" | "hiders")` (a round with `role = "hider",
  standinRole = "gunman"` for the hiders' film).

## 13. The survivors' role card (owner, 27 Nov), and the hiders' intro (parked)

The owner, after the hiders' intro was built: "Actuall scratch that no cinematic for survivor!! When you load in, it'll
tell you survivor!! Hunter you get the cinematic?". So `HuntConfig.ROLE_CARD`: as a survivor lands in the round,
SURVIVOR in A's hero type hits in with the game's impact, holds 1.7 s and fades; it never stops them moving. On screen
the roles are HUNTER and SURVIVOR everywhere (role line, hide shade, results card, modes card, passives); internal
ids stay `gunman` / `hider`. The hiders' intro below is parked behind `HIDER_INTRO.on = false`.

### The hiders' intro (parked)

The owner: "if you get survivor you get a small cinematic of your character walking scared in the map?.. and then it
says survive!! You can skip it!! It'll be short regardless". `HuntHiderIntro.client`, `HuntConfig.HIDER_INTRO`.

- **What it is:** 5 s on each hider's own screen as the round starts. A copy of their own avatar walks scared up to
  their spot from a few studs behind it (Roblox's walk slowed, the gunman intro's upper-body look round), the lens in
  front of them and low; then SURVIVE in A's hero type hits in with the game's own impact, and the lens glides onto
  the game's camera as the word fades. Bars and the gunman intro's muted grade; a heartbeat under it.
- **Skip:** Space, B on a pad, or a tap: straight back to the game.
- **No hiding time lost:** HuntRound adds `HIDER_INTRO.len` to the hide and sends Remote `hintro` { len, t0, at } to
  each hider; the gunman's intro starts that much later (his hide shade covers him until then), so it still ends as
  the hunt starts. A test round can pass `hiderIntro = false`.
- **While it plays:** the real body is anchored and hidden locally (after the game's camera each frame), every other
  HUD is off and put back after, and `HuntIntro = "hider"` is set so HuntClient stands back.

## 14. Ragdoll, the three moves and the item tables (owner, 27 Nov)

The owner: "Outside by the garage I want tables with a medkit, bandages, beat mace, taser , bear trap, and a special prop
gun?.. You can pick one before the hunter gets there maybe? Medkit taser and prop gun cost money!! Then there's push super
push and punch!! ... we need ragdoll mechanic and a button to unragdoll!! Cooldown shouldn't be crazy long but also not
short enough where you can chain all three".

- **Ragdoll (server/HuntRagdoll):** a landed move stands the body's Motor6Ds down (all but the root's) and holds the limbs
  with limited ball sockets (R15 and R6), then puts the joints back on the get-up. A player's own client runs their
  body's physics (it goes limp on Remote `rag`); a stand-in is the server's. While down: the anti-cheat's ACGrace,
  StunUntil (the game's own stun, so a downed hunter can't shoot), HuntRag / HuntRagMin for the client's GET UP key.
- **The moves (HC.MOVES):** PUSH down 1 s (up after 0.5), cd 3 s; SUPER PUSH (hold) down 2 s (up after 1), cd 10 s;
  PUNCH (tap or wound up) down 3 s with a 2.5 s stun, cd 6 s when it lands (1.2 s on a miss). After any move every move
  waits 1 s, and someone just up can't be downed again for 2 s. FIRM STANCE halves the hunter's time down. They work
  on the hunter and on other survivors, in a round (hide and hunt) and in the house. A weapon's swing stays a knock.
- **GET UP:** Space / pad A / the phone's jump, once the move's minimum time has passed (a key cap bottom middle, dim
  until then); the vault's Mixamo Getting Up plays (HC.RAGDOLL.getUp), no moving till it's done.
- **The item tables (HC.PICKS):** two store tables (copied from the patio's) on the driveway in front of the garage
  (THE HOUSE's `tables`; a map without them: its first hider spot). Every survivor starts in a row in front of them and
  takes ONE in the hide (F): BANDAGES (+25 a use, 3), BASEBALL BAT, PEPPER SPRAY, BEAR TRAP free; MEDKIT (full over 2.5 s),
  TASER, PROP GUN for $40 of the round's cash (POINTS.start = 40: exactly one; never coins, never Robux). The prompts go
  when you've taken one, and close when the hunter is let out. The trap menu (G, the hunt) sells the rest; the taser and
  the medkit are the tables' only.
- **The prop gun:** aim at a piece of furniture (slot key) and become a copy of it, your body hidden. Moving faster than
  9 studs/s, attacking, being hit or being downed breaks it; one charge.
- **CASH:** the round's points are shown as $.
- **Test (Studio):** JankHuntTest ("pick", p, id), ("use", p, slot, look), ("cash", p, n), ("rag", p, who, dur, min),
  ("getup", p).

## Built so far (26 Nov 2026, hunt-mode session)

### The house's kit and layout (stage 1)
- `tools/roblox/hunt_house_layout.py` holds the single layout. Run it and it checks spawns, door swings, the way
  through every doorway (`DOORWAYS BLOCKED`: 1 to 3 studs out on both sides, added 27 Nov after Clip found the pantry
  in the garage doorway) and that every room is reached. It currently passes, with one false flag at the WC door,
  whose leaf stops 0.1 stud short of the toilet.
- `hunt_house_models.py` builds the kit (247k triangles). One whole upload came back "Unknown Error" from Open Cloud,
  so the kit goes up in two halves:
  - architecture, `--only=hh_`: `HuntBuild.B.ARCH` (round 8, 27 Nov: hunt_arch10 = 133158939004700);
  - furniture plus the moving pieces (`hx_*` templates), `--only=hp_,hx_`: `B.FURN` (round 8: hunt_furn11 =
    98904903893193).
  - the gunman's intro rooms, `tools/roblox/hunt_intro_models.py`: `B.INTRO` (hunt_intro2 = 106007849260783),
    imported by `B.importIntro()` into `ReplicatedStorage.JankfireHuntIntro`.
  - Each judge round rebuilds both halves (`--name=hunt_archN` / `hunt_furnN`) and re-uploads them; the ids above
    are the latest. Judge rounds and their fixes: vault `Reviews\The House - judge rounds.md`.

  HuntBuild `B.importExtra(FURN)` adds the second half without clearing the first.
- New textures: siding 127661606333401, shingles 135435899461861, lawn2 118128219477802 (round 4: calmer; the first
  lawn was 82912196276517), fence boards 136590475412292, asphalt 72215822270952, oak planks 123980610531995, kitchen
  tile 101846364880605, plaster 87623840105825. The rest are the school's pictures. `hunt_house_textures.py` makes
  them; `TEXS` in hunt_house_models.py maps each textured colour to its picture (the picture's own colour wins).
- In Studio, in this order:
  1. `W.import("HuntHouse", B.ARCH)`
  2. `B.importExtra()`
  3. `W.build("HuntHouse")`
  4. `B.build()`, then `B.check()`
- **Live in Studio since place v1382 (26 Nov); round 8 rebuilt at v1452 (27 Nov, 04:06 UTC):** 27 kit models, 474
  hit boxes, 16 spawns, 33 lights; 19 doors, the roll-up with 2 buttons, 18 switches, 3 TVs, 6 taps, the fridge, 3
  toilets, the ball, 3 store tables, 48 seats, 5 bouncy parts (the trampoline). The back terrace is level with the
  house's floor (`DECK`), with broad steps down to the garden path. The look is `HubLook.looks.hunt_house`, given by the LookZone
  `Map.Hub.LookZones.HuntHouseLook`.
- The one-line hooks in shared files are in (commit 2df0027): `Unarmed` in Fight.holstered, Arsenal's inHub and
  HubHolster; `NoGrapple` in Move.client (tryHook, tryYank, tryLock) and Main.server's hook handler; `Body.sink` taken
  off HipHeight in Move.client; the HOUSE HUNT card in ModesTab; the look in HubLook.
- 27 Nov (commit 092e0cb): FlairServer's onKill returns early when the killer has `Hunt` set, so a gunman's worn kill
  effect never plays on a hider (round re-test v1407: a shell of limb shapes showed with the cubes, against section 6).
- Round test verified in Play (v1407): the gunman's spawn grace (HuntRound `grace`, 6 s) keeps the round going, a
  headshot breaks a stand-in into cubes, the last kill gives GUNMAN WINS, the house comes back with the lobby
  attributes, and X lies down (HipHeight 0.05, `HuntLie`) and gets up again.

### Animations (mocap, the vault's Mixamo clips)
- Uploaded for R15 and R6 (ids in `HuntConfig.ANIMS`): idle, run, the haymaker (a rear hook that holds at its
  wind-up), the jab, lying down (the fall onto the back, hips flat via `mixamo_r15.py --no-rise`), lying, and the shove
  (a hands-forward push sped up to 0.22 s).
- Waiting on the owner's Mixamo sign-in (signed out on 26 Nov): walk, crouch idle, crouch walk, and a real shove. Until
  then the avatar's own walk and CrouchPoses' crouch stay.

### Sounds (recordings only)
- `hunt_*` in store.json: door open and shut, light switch, tap, trampoline, punch hit, shove, fridge (all Freesound
  CC0) and the toilet flush (a licensed library take). The garage door reuses `zm_door`.
- The traps reuse library sounds: `taser_fire`, `taser_arc`, `gas_hiss`, `marble`, `ropesnap`, `step_hard`,
  `skin_smoke_censer_cloud`.

### Stages 2-4 in code
- `HuntRound` runs the round, `HuntItems` the traps, points and FIGHT BACK weapons.
- The fight-back weapons are held props swung with the punch, judged by the server.
- `HuntConfig.MAPS` has three maps (27 Nov: Jankfield High taken out, no schools):
  - THE HOUSE: a copy of the lobby with its `Hunt` folder stripped (doors, the exit, the tables); spots from
    `hunt_spots.py hunt_house_layout house HuntHouse "THE HOUSE" 24 --y=-2,13.5`, the weapons placed by hand;
  - the Backrooms;
  - Suburb v2.

  Each has spots picked by `tools/roblox/hunt_spots.py` from its own layout.
- Studio test hooks on `ServerStorage.JankHuntTest`:
  - `round {role, standins, gun, hide, hunt}` starts a round with stand-in bodies;
  - `rstate` reads its state, `stop` ends it;
  - `hurt who dmg head` gives a round member a hit from the tester (the break-up test).
