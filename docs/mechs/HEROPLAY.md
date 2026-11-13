# BATTLE ISLAND heroes: how they play (as built; the rigs are docs/mechs/HEROES.md)

The design is docs/mechs/ROSTER.md; this page is what got built, with every number. Each hero is a MECH DROP frame
(docs/mechs/PLAY.md: drop, climb in, armour, energy, eject all work the same) with its own kit. The numbers live in
`MECH.<id>` in `shared/mech.js`. Every hero has an **ULTIMATE** on Q that charges from the damage it deals (its
ultimate's own hits don't count) plus a slow trickle on its own; the charge, energy and cooldowns live on the mech, so
hopping out and back in doesn't reset them. They're picked in the battle island hero pick (`shared/heroes.js`) and in
the loadout's MECH DROP frame row.

How a hero is built (so the next ones are additive):

| part | file | registered in |
|---|---|---|
| numbers + pure rules | `shared/mech.js` (`MECH.<id>`, `FRAMES`, `speedCap`, `WEAPONS` kill-feed names) | |
| server judging | `server/mech_<id>.js` | `server/mech.js` `KIT` (hooks: enter, exit, flags, cap, budget, land, msg, tick, bot, shrug, soak, en) |
| client: keys, movement, effects, sounds, events | `public/js/mech_<id>.js` | `public/js/mech.js` `KITS` |
| code stand-in model + poses + clip names | `public/js/mechmodel_<id>.js` | `public/js/mechmodel.js` `MODELS` |
| tests | `tests/mech_<id>_ws.cjs`, `tests/mech_<id>_bots_ws.cjs` | |

The stand-ins use the mech art session's joint, marker and clip names, so `public/models/x_mech_<id>.glb` replaces
them when it lands (material prefix: wb_, vm_, tr_).

## WRECKING BALL (dive tank, 1400 armour, 22 m/s rolling)
A 4 m hamster ball: steel side caps on the axle, a clear tread, a hazard-striped yoke that never rolls, a pail handle
with the chain's shackle, fold-out feet, and the pilot running in a wheel inside (spinning round with every roll: the
camera shakes with it). Frame id `wrecking` (`wreckingball` is the killstreak's armour pool).

| key | move | what it does |
|---|---|---|
| (rolling) | **ram** | the main weapon. rolling into people hurts by the speed the SERVER measured: 8 + 2.6 per m/s over 6, up to 70 (44 at top rolling speed, 70 from a launch or a swing), knockback with speed. once per target every 0.6 s |
| LMB (hold) | **rev** | spins up on the spot (feet out, sparks, a rising whine); let go to launch the way you look at 26-36 m/s (full charge at 0.8 s, the server times it). 20 energy |
| Shift | **chain** | throws the chain at whatever the crosshair's on: something solid, in plain sight, above you, within 42 m. swing on it (W pumps, A / D steer, jump or Shift lets go). 10 energy, 0.7 s cooldown, 7 s max |
| E | **ground slam** | in the air it dives straight down; on the floor it hops first. the slam's size is the height it really fell (1.5 m: 35 damage in 4 m; 22 m+: 130 in 9 m), it flings. 6 s cooldown |
| RMB (hold) | **brake** | stops hard (sparks) |
| Space | hop | |
| Q (ult) | **PILE DRIVER** | rockets 30 m straight up, hangs there up to 2.5 s while you aim (a red ring shows where it lands), then dives at 70 m/s onto the spot you pick (a floor within 55 m; none: straight down): 200 at the middle, down to 30 % at 9 m, everyone flung. everyone sees an INCOMING ring where it's coming down. ult: 650 damage dealt or 110 s |
| passive | | no knockback at all while it's rolling (or swinging, or diving) |

The server keeps it honest:
- **Rams:** the speed comes from where the server has it (claimed velocity counts for nothing).
- **Launch:** its speed allowance only lasts the launch, then it fades at 7 m/s per s (the client's drag is harder).
- **Chain:**
  - The anchor is where the server's own ray bites, not the client's point.
  - It pays for a climb to the anchor + 3 m, nothing more.
  - It snaps if the ball ends up 4 m past its length.
- **Slam:** sized by the height lost since it left the floor, measured from accepted snapshots.
- **PILE DRIVER:**
  - It pays for its 30 m rise once.
  - It fizzles if it never fell 10 m.
  - The 70 m/s dive only lasts the trip to its spot, and ends at once (with the movement bank cut back) if it heads anywhere else.
  - Its own hits don't recharge the ult.
- **Bots:** they roll at people, rev-launch from mid range, chain up to anyone above or far away, slam crowds and pile-drive whoever they can see.

Tests: `tests/mech_wrecking_ws.cjs` (46 checks incl. the exploits above), `tests/mech_wrecking_bots_ws.cjs`. Knobs:
`JF_MECH_FRAME=wrecking` (bots' frame), `JF_MECH_ULT=<x>` (ults charge x times faster), `JF_MECH_SLOW=<x>` (the pile driver's server windows x longer, for slow screenshot browsers).

## VENDING MACHINE (support, 1100 armour, 12 m/s waddling)
A 5 m vending machine (6.75 m at the 1.35x mech size) on stubby legs. It has a glowing front of drink cans, a coin slot for a face, a JANK COLA marquee, an OUT OF ORDER sign stowed on its back, and little jump jets in its heels. Frame id `vending`. The art session's skinned `x_mech_vending.glb` drops in; the kit only moves joints.

Lengths below are at size 1, with the 1.35x size in brackets (`sized`: the wall, the toss, the reaches, RESTOCK's range).

| key | move | what it does |
|---|---|---|
| LMB (hold) | **coin turret** | 9 a coin, 10 a second, 90 m. A server hitscan from the coin slot along your aim: an aim cone (cos 0.6) and a rate check. It hits players, mechs, empty parked mechs and enemy walls, but only the first thing in the way. |
| Shift | **DISPENSE** | A Jank Cola pops out of the flap onto the floor where you point: within 6 m (8.1), and the flap must see the spot. Otherwise it lands 2.4 m in front. 3 charges, one back every 8 s, 6 out per machine at most (the oldest goes flat), and each lasts 20 s. Allies and yourself (yours after 0.9 s) walk over it: +40 HP (or +40 armour in a mech) and a 3 s sugar rush. Someone at full health walks past it; enemies can't drink it. What it really heals charges the ult. |
| E | **OUT OF ORDER** | A 600 HP sign wall, 8 x 4.5 m (10.8 x 6.1), slammed down 3.5 m (4.7) in front, facing you. 10 s, 12 s cooldown, one at a time. Each half stops where a building is, so it never pokes into a room. See below for what it stops. |
| Q (ult) | **RESTOCK** | Every ally within 15 m (20.25), yourself too: up to 250 armour, as the battle island / royale vest (to its max) or, in modes with no armour, an overheal to 150. Allied mechs get armour back, full energy and every cooldown cleared (not the ult); a vending machine also gets its cans back. Ult: 800 dealt or healed, or 120 s. |
| passive | **STUCK!** | 10% of dispenses / walls come out twice: two cans, or a double-HP wall. |
| jank | **JAMMED** | 6% of dispenses / walls jam: nothing comes out (nothing is spent) and Shift / E / Q lock for up to 4 s. An ally on foot presses F within 4.5 m (6.1) to kick it: UNSTUCK, plus a free can. Allied bots do it too. |

What the OUT OF ORDER wall stops:
- Enemy gun shots. Judged along the shooter's own aim to where it meets the target, so the bit of you sticking out past the edge can still be hit.
- Mech hitscans.
- Projectiles. They stop on the sign's face:
  - a chicken rocket goes off there;
  - a banana slides down it into a peel;
  - grenades bounce off it.
- Missiles. They blow up on its face.
- Blasts. Explosions don't come through it to whoever's behind.
- The water pistol. A squirt it stops doesn't soak you.

Your own side shoots through it, and it isn't solid to walk through.

The server keeps it honest:
- **Colas:** only the server spawns, owns and hands them out, and there's a cap per machine.
- **The kick:** a validated, rate-limited on-foot message (`{t:'mech', k:'kick', to}`, `mechPoke` in server/mech.js). It needs a jammed allied machine, in reach. You can't kick it if you're down, and the pilot can't kick their own.
- **STUCK and JAMMED:** the server's dice.
- **RESTOCK:** needs a full ult, reaches allies in range only, and its own grants don't charge the ult.
- **Sugar rush:** the only extra speed it gives, and it ends with `fastUntil`.

Tests:
- `tests/mech_vending_ws.cjs`: three servers (no dice / every use jams / every use STUCK). Each exploit and every review repro fails on naive code.
- `tests/mech_vending.test.mjs`: the clipped wall.
- `tests/mech_vending_bots_ws.cjs`: TDM with bots.

Knobs:
- `JF_MECH_FRAME=vending`
- `JF_VM_JAM=<0..1>`
- `JF_VM_STUCK=<0..1>`
- `JF_VM_SLOW=<k>` (walls and cans last k x longer)

## TROLLEY (speed, 800 armour, 26 m/s)
A 4 m shopping trolley (5.4 m at the 1.35x mech size): a chrome wire basket made of real bars, a red push bar with your colour on the grips, a red child seat that folds down, a pound coin lock on a chain, a rubber bumper in your colour, four swivel casters (the front-left one bent, with gum on it), two little boosters behind, and a tiny pilot in a hi-vis vest pushing it from the footboard. Frame id `trolley`. Hitbox 1.3 m half-width, 2.6 m tall, cockpit band 1.7-2.6 m (the pilot at the handle).

Lengths below are at size 1, with the 1.35x size in brackets (`sized`: the push and scoop reaches, the ride reach, the can, the seat and basket spots, the muzzle).

It drives like a cart: quick off the mark (0 to 26 m/s in about 0.4 s), grippy (sideways speed fades at 7/s), a bit of slide, a 8 m/s hop. The fastest thing on the island.

| key | move | what it does |
|---|---|---|
| (driving) | **ram** | Driving into people hurts by the speed the SERVER measured: 6 + 1.4 per m/s over 9, up to 35 (27 at top speed), knockback 0.8 x speed. Once per target every 0.7 s. Empty parked enemy mechs too. |
| LMB (hold) | **TIN-CAN TOSS** | Lobbed cans from the handle, 3 a second, 26 m/s + 6 up. Each bounces off the floor and walls up to 3 times and BONKs the first enemy it touches for 22 (a small shove). An enemy OUT OF ORDER sign takes 22 and the can bounces back off it. Empty parked mechs take it. |
| Shift (hold) | **DRIFT** | The grip drops to 1.1/s and it slides; the casters swing out to 35 degrees, sparks and a squeal. Drifting faster than 12 m/s fills the **RAM CHARGE** from 0 to 1 in 1.5 s (from a standstill it starts counting once it's really travelled for ~0.5 s); it keeps 3 s after the drift. |
| E | **TROLLEY PUSH** | A 0.4 s lunge where it faces at 30 + 10 x charge m/s. Everyone on the bumper's path (1.7 m (2.3) either side) takes 30 + 50 x charge (up to 80) and a shove of 20 + 15 x charge, 6 up. Spends the charge. 4 s cooldown. Hit-stop and a red impact frame on a big one ("TROLLEY'D"). |
| RMB (hold) | **brake** | Stops hard (sparks). |
| Q (ult) | **CLEAN UP AISLE 5** | 6 s at 34 m/s, boosters on, a tannoy chime. Enemies it runs into (2.2 m (3.0) in front of the basket, it moving faster than 4 m/s) get SCOOPED into the basket, up to 3: they ride along at the basket's spots, can't move, shoot or use anything, and take 8/s. When the 6 s run out, or Q again, it DUMPS them: the basket tips and they fly forward 24 and up 14, for 35. A mech, a rig, a ball or someone on a rope is too big to scoop (rammed instead); so is the 4th. Ult: 550 damage dealt, or 100 s. |
| passive | **ONE WONKY WHEEL** | It always pulls a little left (0.07 rad/s at top speed, in your own driving) and the front-left caster wobbles. |
| jank | **THE POUND COIN LOCK** | An ally on foot presses F within 3 m (4.05) of its sides to ride in the child seat (one at a time). Riders keep their guns and shoot from it (a gunner), but can't grapple, use streaks or carts. F or jump hops them out over the side. If the trolley breaks they're flung out. Allied bots hop in now and then, and trolley bots drive over to pick allies up. |

The server keeps it honest:
- **Measured speed:** rams, the drift charge, the scoop, a can's carried speed and the dump's fling all use the speed the server measured (`mechMv`), cut down to the net travel over the last 0.5 s (wiggling back and forth in place reads as parked), clamped to what it may go right now (the kit's cap) and to no more than 12 m/s over the window before (a one-snapshot teleport counts as standing still). The generic PAPER PLANE / NIGHT SHIFT ram and WRECKING BALL's ram use `mechMv` too. Knockback directions are a unit vector of the raw velocity.
- **Drift charge:** the DRIFT flag only counts while the measured speed is over 12 m/s, and the charge builds on the server's own clock. The push's speed and damage come from that charge, not the client's.
- **Speed:** 26 m/s normally, the push's speed only inside its 0.4 s window, 34 m/s only in AISLE 5. Afterwards the cap comes down at 16 m/s per s (the client's own drag), and the extra movement bank the push / ult gave is cut back when they end.
- **The basket:** scooped and riding players are wherever the server's trolley puts them; their own positions are ignored, scooped ones can't fire, hit, use items, streaks or `unride`, and on Battle Island / Jank Royale can't revive, swap heroes, call a mech, loot, heal or kick (stopped before those modes' own handlers). Riders keep their guns and heals only. Getting scooped or climbing in drops a shopping cart you're riding and stops a revive you're doing; anyone on the blimp or gliding can't be scooped (rammed instead) or ride. They're let go on every path: the dump, the timer, Q, the trolley breaking (flung out), the pilot hopping out, dying or leaving, a round / map change, them dying, leaving, respawning, getting sealed in a soap bubble or caught on a lasso. A let-go spot is checked (no wall from the trolley's middle, not inside anything, not off the map; else the trolley's middle), and a rider hops out on a side with no wall (mechOutSpot). Carried off the edge, they fall into the void like the trolley.
- **Riding:** `{t:'mech', k:'ride', to}` / `{k:'unride'}` go through the on-foot poke route (`mechPoke` in server/mech.js, rate limited): allies only, from on foot, within reach, one rider.
- **Bots:** they race at the nearest enemy, drift round in an arc to build the charge, then push when they're lined up within 11 m; they toss cans at anyone in sight under 34 m, AISLE 5 when an enemy's within 25 m ahead, dump when the basket's full, and drive over to an ally on foot when there's no fight.

Tests:
- `tests/mech_trolley_ws.cjs`: TDM with 8 clients; every rule and each exploit above fails on naive code.
- `tests/mech_trolley_bots_ws.cjs`: TDM with bots.

Knobs: `JF_MECH_FRAME=trolley`, `JF_MECH_ULT=<x>`.
