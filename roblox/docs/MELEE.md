# Melee that can close the gap (26 November 2026)

The owner, 21 Nov: "How do we make the melee weapons better?" Then on 25 Nov: "Multiple people have pointed out melee
feels useless I can kinda gree! other than the sliper which is kinda op the rest of the melee weapons arent very
forgiving thats why I wanted to maybe try a better reel in or pull to help close gaps on players". And on the grapple:
"perhaps with grapple we have auto matic reel if we're attatched to something or someone, with have a bring in with f,
but its inconsistent when theyre zipping around, perhaps an actual reel in with f but f is an awkward button to press,
can we allow keybiinds to side mouse buttons, also perhaps we can have like on a timer like a lock on to player
attatchment system?"

Main's decisions: a held reel-in, a timed lock-on that holds longer with a melee weapon out, a lunge, a small run bonus,
forgiving swings, a first-swing bonus after a reel; rebindable keys on every device; check whether Roblox reads side
mouse buttons. The Slipper's numbers are left alone (to be measured against the others later).

## What a player gets

| Move | Keyboard | Controller | Phone | What it does |
| --- | --- | --- | --- | --- |
| Grapple | E (hold) | RB | HOOK | as before. aimed within a few degrees of a person, it snaps onto them (the lock-on) |
| Reel in | F (hold) | B (hold, on a rope) | REEL | pulls you along your rope at a steady speed to where its end is now |
| Yank | F (tap) | B (tap, on a rope) | YANK | as before: pulls them to you, the rope goes |
| Auto grapple | X | D-Right (in a round) | LOCK | as before (HookCharges.LOCK) |
| Lunge | Z; right click on Bread, Hand Slapper, Claw | RS (with the melee weapon out) | LUNGE | a short dash at the person under your crosshair |

All of them are on Settings > KEYBINDS (two keyboard columns and the controller column). F is shared by the yank and the
reel: a press shorter than `Config.hook.reelTap` (0.18 s) with the rope on a person is the yank, a longer one reels. Bind
them apart and each answers at once. The phone's REEL and YANK buttons press their own action only (`Keys.press(code,
down, act)`, `Binds` matches `io.Act`).

**Side mouse buttons:** Roblox reads only `MouseButton1`, `MouseButton2` and `MouseButton3` (checked in Studio 0.748:
`Enum.UserInputType` has no other mouse button, and `UserInputService:IsMouseButtonPressed` takes only those; the one
`KeyCode.MouseBackButton` is marked deprecated in the engine reference. A real side button could not be pressed in this
test, so "it never arrives" is not proven, only that the API has nothing for it). So the KEYBINDS tab says, under
MOVEMENT: set the side button to
a key in the mouse's own app (Logitech G HUB, Razer Synapse and the like), then bind that key here. Mapping a side button
to F gives the reel and the yank on the thumb.

## The numbers

`shared/Config.luau` (hook):
- reel: `reelSpeed` 40 m/s (120 studs/s; a sprint is 43.5 studs/s), reached in a few frames; ends `reelArrive` 4.5 studs
  off a wall point (the rope goes) or `reelBody` 6 studs off a person; `reelKeep` 0.45 of the speed carries on; at most
  `reelMax` 2.5 s; one every `reelCool` 2 s (ReelT, the server's).
- lock-on: a rope on a person holds `lockGun` 1.5 s with a gun out, `lockMelee` 3 s with a melee weapon out; the snap
  cone is `snapGun` 4 degrees, `snapMelee` 7 degrees, and never onto someone further off than what you aimed at (+6
  studs). With a gun the rope still lets go as you reach them (`bodyLet`, 9.6 studs); with a melee weapon it ties on
  there (the old TIE code: you walk, they can't get further than the rope, you're dragged after them) until the time is
  up. Jumping off the tie is a grapple jump, as on any rope.

`shared/Melee.luau`:
- `SPEED` 1.08: run speed with a loadout melee weapon out (on top of the weapon's own `speedMul`).
- `LUNGE`: range 22 studs (chest to chest), cone 12 degrees, 95 studs/s, at most 0.3 s, stops 4.5 studs off them (inside
  every swing's reach), at most 35 degrees up or down (never down into your own floor), keeps 0.4 of its speed, cooldown
  4 s. Nobody there: "NO TARGET", nothing spent. Already within 5 studs: nothing (just swing).
- `HIT`: a body is a column from the feet to 5.3 studs up, 1.2 studs wide each way. A swing reaches the column's nearest
  point (plus its radius) and the cone widens by the angle the radius takes; it also looks back along the swing, from the
  press (less 0.05 s) to the hit, for where they were.
- `REEL_HIT`: arriving on a person by the reel opens 0.8 s in which the next swing reaches 3 studs further and hits x1.2.
  One swing, hit or miss.

What the forgiving swing changes (old / new, `swingtable.py`; attacker standing, target standing unless said):

| case | katana | knife | bread | slapper | scythe | scales |
| --- | --- | --- | --- | --- | --- | --- |
| straight ahead, 8.5 studs | - / hit | - / hit | hit | - / - | hit | hit |
| straight ahead, 9.5 studs | - / hit | - / - | hit | - / - | hit | - / hit |
| 45 degrees off, 6 studs | - / hit | - / hit | - / hit | - / hit | hit | - / hit |
| one step (3 studs) below, 7.5 studs | - / hit | - / hit | hit | - / - | hit | hit |
| looking 25 degrees down, 8 studs | hit | - / hit | hit | - / - | hit | hit |

The Hand Slapper stays point blank (5.7 studs reach): its job is the shove.

## Where it lives

- Client: `client/MeleeLunge.luau` (the lunge, `speed`, `meleeOut`, the swing look-back history `hits`),
  `client/MeleeHud.client.luau` (the ring and the pip), hunks in `Move.client` (reel hold, tap/hold split, snap,
  lock-on clock, tie, lunge step), `Arsenal.client` (LUNGE key / right click, run bonus, `resolveSwing` through
  `MeleeX.hits`, the reel-hit swing), `Binds` (`reelin`, `lunge`), `Keys` (`act`), `TouchLayout` / `TouchControls` (REEL
  at 172,214 and LUNGE at 238,150, both `fixed`), `SettingsUI` (the side-button line).
- Server: `server/MeleeLunge.server.luau` (the lunge's say-so: weapon, zone, after GO, not held, cooldown `LungeT`,
  target in reach and sight; `ACGrace` for the anti-cheat; "no" back otherwise), hunks in `Main.server` (reel "reelno",
  the lock-on's clock and "time" cut, "reeled" -> the fighter's `reelHit`), `Combat.server` (the swing's look-back along
  `Fight.path` within `Latency.window` + the swing time, the reel-hit swing), `Rules.meleeHit` (`extra` reach).
- The HUD: a thin ring round the crosshair empties over the lock-on (white; the accent once a melee weapon has tied on;
  it pulses in the last half second). A wider accent ring fades over the reel-hit window. A small pip left of the
  crosshair fills over the lunge's cooldown (mirrors the AUTO GRAPPLE's pip on the right). No words.
- Test hook: `ServerStorage.JankMeleeTest` ("log" = the lunge asks and answers, "clear", "ready", p).

## The anti-cheat

The reel's say-so sets `ACGrace` for `reelMax` + 0.8 s; the lunge's for its time + 0.5 s (`roblox-anticheat` contract).
Both run at once on the client (no wait for the server), and the server's answer stops them if it says no.

## Tested (Studio, place version 1374, 26 Nov 2026 22:21-22:25 UTC)

One solo Play on the training range's dummies, real key and mouse input through the Studio MCP, the camera held on the
dummy by a RenderStep binding, every frame logged (distance, speed, rope/body/tie, timers). Sheet:
`docs/melee/melee_sheet_v1374.jpg`.

| test | result |
| --- | --- |
| lunge, katana out, Z, Stand 18 studs off | 18 -> 3.0 studs in 0.2 s at 95 studs/s; server said yes (`LungeT` 4.0 s, log "lunge 18") |
| lunge carry | 0.4 of its speed carried on 1.5 studs further into the dummy; `keep` is 0.15 since (not re-run) |
| snap: E aimed 4 degrees off a Stand 45 studs off, katana out | tied onto it, lock 3.0 s; pulled in 45 -> 4.4 studs in 0.93 s, then tied on (T) until E was let go |
| reel: E then F held on the strafing Dummy 50 studs off | 50 -> 3.2 studs in 0.78 s (steady 123 studs/s from 0.46 s, after the 0.18 s tap wait), `ReelHit` set at arrival, then tied on while it walked away |
| reel-hit swing | real click came after the 0.8 s window (the MCP's input lag), paid 48; by remotes (hook, reel, reeled, swing, hit): plain 48, after the reel 58 (x1.2) |
| anti-cheat (`StudioOn` true) through all of it | 0 catches, 0 points |
| KEYBINDS tab | MELEE LUNGE Z / RS, GRAPPLE REEL IN (HOLD) F / B, the side-button line under MOVEMENT |
| phone (TouchForce) | LUNGE shows with the katana out |

**Re-test with the shipped `keep` 0.15 (place version 1374, 26 Nov 23:27-23:30 UTC, same rig):**

| test | result |
| --- | --- |
| lunge at a still Stand, 18 studs | 18 -> 3.4 studs in 0.11 s at 95 studs/s; the carry left 24 studs/s (41 with 0.4) and it came to rest against the Stand's plinth at 1.3-1.7 studs, as before |
| lunge at the strafing Dummy, 18.7 studs | followed it as it walked: 18.7 -> 3.4 studs in 0.2 s, ended at 12 studs/s, no overshoot; server log "lunge 21.6" |
| lock-on with the SMG out, 45 studs, aimed 2 degrees off | snapped on, lock 1.5 s (`HookLockDur`), pulled in, let go on reaching them at 0.8 s, no tie (a gun's); the 1.5 s cut-off itself didn't come up (they were reached first) |
| anti-cheat (`StudioOn`) | 0 catches, 0 points |

Not tested: two real players (the Studio MCP runs solo Play only; the strafing dummy stood in for a moving target), a
real phone or controller, the gun-out lock-on's 1.5 s and its let-go on arrival (same code path as melee's, only the
number differs), a real side mouse button (no way to press one here).
