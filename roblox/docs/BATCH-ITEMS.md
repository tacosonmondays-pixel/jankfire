# The utility slot and its items (G)

The owner, 16 Nov 2026: "So a lodout will consist of a primary, a secondary, a melee, and a utility". The web game
calls these items (key G, `ITEMS` in `shared/weapons.js`); the spec is `WEAPONS.md`, "Phase 2: ITEMS" and "Items
basics", plus one section per item. Every number below is the web game's, unchanged (distances x3 for studs).

## What's in

| | |
| --- | --- |
| The slot | `Roster.SLOTS` = primary, secondary, melee, **utility**. The 13 web items are rows in `Roster.luau` (slot `utility`); the live ones show on the loadout screen with their own model, the rest as "coming soon" crates. |
| The numbers | `src/shared/Items.luau`: charges and recharge (the final values after the web game's gadget override), each item's numbers, the charge clock, the dome and smoke tests, and the thrown items' flight (the web `stepProjectile`, run the same on the server and every client). |
| The server | `src/server/Utility.luau`: owns everything. The item you carry and when a new pick goes in (at once while you're dead or in the first 5 s of a life, else next life; charges used stay used), the charges and their clock, every throw, bounce, fuse and blast, the heal, the domes and every hit they stop (through `Fight.blocks`, asked first by `Fight.hurt`), the clouds (`Fight.smokeBlocks`). |
| The loadout | `Loadout.luau` picks, saves (`pick.utility` in the same DataStore entry) and checks it like the weapons; `LoadoutUI` has a fourth card (key G), item cards show charges and recharge, items take no paint and no hat. |
| Your client | `src/client/Utility.client.luau`: G, the HUD plate above the ammo (name, one pip per charge, the next one filling as it recharges), the item in your own avatar's left hand while it's used, and everything the server says happens in the world. |
| Models | `tools/roblox/item_models.py` (headless Blender, on the guns' kit `gunkit.py`): frag, smoke can, medkit case, shield puck. `tools/roblox/item_import.luau` puts the upload in `ReplicatedStorage.JankfireItems`. |
| Sounds | `tools/roblox/render_items.mjs` renders the web recipes (boom, heal, reverse, pop, blow) to .wav; ids in `roblox/assets/sounds/items.json`. |

## Batch 1: Frag Grenade, Medkit, Shield Bubble, Smoke Bomb

The core kinds: thrown with a blast (frag), thrown with an area (smoke), used on yourself (medkit), placed (shield).

![the four models](items/batch1-models.png)

### Tested against the web numbers (solo Play test, training hall, 16 Nov 2026)

Measured from the server's own events in Play (the client recorded `ItemFx`, `Dmg` and `Knock`; the server's numbers
through `ServerStorage.JankTest` `"item"`). The target was the training hall's still Stand (root at y 243.19, so its
middle, feet + 0.9 m, at y 242.89). Distances in studs.

| what | web game | expected in Roblox | measured | |
| --- | --- | --- | --- | --- |
| frag fuse | 2.2 s | 2.2 s | thrown at 5.16 s, went off at 7.36 s: **2.20 s** | ok |
| frag damage on the Stand, 10.28 from the blast | 105 x (0.3 + 0.7 f), f = 1 - d / 7.5 m | f = 0.543: **71.4** | **71** (the hit event rounds) | ok |
| frag shove on the thrower, 1.90 below the middle | 34 x (0.4 + 0.6 f) + 6 f up, m/s | 102 x 0.949 + 18 x 0.915 = **113.3 studs/s** up | **113.3** up (0.4 sideways) | ok |
| frag damage on the thrower | 0 | 0 | no damage event | ok |
| frag charges | 2, 18 s each | 2, then 1 with the clock running | 2 -> 1; the next one due 9.65 s later, 8.4 s after the throw | ok |
| frag bounce corrections | (the web game sends none while it rolls) | only on real bounces | 4 in a throw straight down (was 16 while rolling, fixed) | ok |
| medkit | +45 at 26 HP/s, never past 100 | 40 -> 85 | **40 -> 85** after 2 s | ok |
| medkit charges | 2, 20 s each | | 2 -> 1, the next one due 12.1 s later, 7.9 s after | ok |
| shield dome | 4.4 m radius, 1 m over your feet, 7 s | 13.2 studs, 3 over the feet, 7 s | r **13.2**, centre at y 243.2 for feet at 240.2, gone after **7.02 s** | ok |
| shield blocks a hit from outside | dropped (no damage, no shove) | | not measured yet: Studio closed (see below) | to do |
| a hit from inside the same dome | lands | | not measured yet (my first try came after the dome had gone) | to do |
| smoke | fuse 1.3 s, a 6.5 m cloud for 10 s | 19.5 studs, 10 s | not measured yet | to do |
| the loadout screen | four slots | a fourth card, G | pushed, not photographed yet | to do |

The Studio place was closed at 09:39 UTC (an account moderation warning about another session's uploaded image, not
these items); the place reopens from its 09:13 save, so this batch has to be pushed again before the rows marked "to do".

### Where the web server trusts the client, and what this port does instead

The web server takes the client's throw point within 4 m of its eye and the client's look. Here the throw point must
also be in clear sight of the server's own eye position (no throwing from the far side of a wall), the look must be a
real direction, and the velocity a throw inherits (35 % of yours) is held to 1.25 x the speed the server saw you move,
so a faked velocity can't fling a grenade across the map. Item use is refused in the hub (weapons-free) as well as when
dead, out of charges, too soon (0.4 s) or not your item; every refusal sends the real count back so the HUD can't
drift. Blast hits, heals and blocks are never reported by a client.

### Kept as the web game has it (on purpose)

- The frag's blast goes through walls (web `explodeAt` has no wall check), and the thrower takes the full shove but no damage.
- Thrown items slide along floors with no friction (web `stepProjectile`).
- The medkit keeps draining while you're at full health (it doesn't eat overheal).
- A dome protects everyone inside it from anyone outside, enemies included.

### Not yet

- The Plinker (the training hall's bot) should not see through smoke (web bots can't). `Fight.smokeBlocks` is there;
  the one line in `Dummies.luau` waits for the training session, which has that file open.
- Third person shows no throw pose on other players (the web game doesn't either); the item just leaves their hand.
- The other 9 items: Rubber Duck, Party Popper, Reverse Card (batch 2), then the gadgets (batch 3).

## Batch 2: Rubber Duck, Party Popper, Reverse Card (built, not live yet)

The code, the models and the sounds are in; `live` stays false (`Items.luau`, `Roster.luau`) until each is play-tested.

![the batch 2 models](items/batch2-models.png)

- **Party Popper.** The web client picks who is in its cone and the server re-checks with a wide slack; here the
  server picks them itself at the pop (`popperUse`): the cone from your eye along your look (0.6 rad, any angle within
  1.5 m), 9 m plus a speed allowance, against where each target is and was a moment ago (lag), in clear sight. Each gets
  50 m/s along you -> them (feet to feet) + 12 up, no damage, and is tagged (a fall is yours). Your own kick back
  (17 m/s back along your look + 5 up) is your client's, like the web game.
- **Reverse Card.** 3 s; `Fight.hurt` asks `Fight.reflects` after the dome check and swaps attacker and victim (the
  shove mirrored in x and z), so every hit that goes through `hurt` comes back: bullets, swings, blasts with a
  thrower, popper shoves, the duck's end blast. Ends on death.
- **Rubber Duck.** Homes (25 m, 60 degree cone, 3 rad/s, in sight, faster than 4 m/s), sticks to whoever it touches;
  the hole opens on them 0.3 s later and rides their middle; every 0.1 s it pulls everyone within 15 m (as `Knock`,
  not reflected: web rule), crushes the one it's on (1) and hurts anyone within 2 m (3), straight to HP (`Fight.hurt`'s
  new `plain`, like the web `damage()`); after 3 s it pops (9 m, 45 x f, the thrower: shove only). The momentum eater
  runs in your own movement step (`Body.onStep`, called by `Move.client.luau`); a rope within 6 m of the middle snaps.
