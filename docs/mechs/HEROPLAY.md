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
`JF_MECH_FRAME=wrecking` (bots' frame), `JF_MECH_ULT=<x>` (ults charge x times faster).
