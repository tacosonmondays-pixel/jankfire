# Server honesty

What the server checks before it believes a client's "I hit them", and what it still takes on trust. The checks live in
`server/honesty.js` (mixed into Room; it wraps `handle`, `onHit`, `onPush`, `onFire`, `sendLoadout`, `modeLoadout`,
`resetLife`). The tests are `tests/honesty_ws.cjs` (every "refused" case in it lands on a server without this file) and
`tests/honesty.test.mjs` (in-process: bubbles, fast targets, launches, ricochets, the CPU budget). `JF_HON_LOG=1` prints
every refusal and why.

Movement is the client's, so every check is lenient on purpose: it only refuses what no honest client at ~150 ms ping
could send. Bots and server-made shots never go through these checks (bots fire in `botFire`, not `onHit`). Story rooms
skip the hit checks (their referee judges hits on boss parts itself).

## Checked now

| What | Rule | Numbers |
| --- | --- | --- |
| Hitscan line of sight | a clear line (map boxes: walls, floors, glass; not deco or smoke, like the client's bullets) from the shooter's eye to any sample point on the target's hitboxes | eyes: 3 heights (1.6 / 1.3 / 0.98 m; a mech's cockpit, the rig's, the ball's) at the newest position and one snapshot ahead (0.05 s at the speed the server believes: the claimed speed, no more than the 600 ms average it saw or, right after a launch, the last two snapshots x1.25, max 60 m/s). A hit always goes out after the snapshot before it, so older shooter positions aren't tried. target: its path over the last 650 ms (a shooter at ~540 ms ping still lands), tried every 0.6 m along the path (at most 16 spots, so a 40 m/s runner crossing a 1.5 m gap is still caught; one spot if they stood still); hitboxes as the client draws them (the soap bubble's ±1.1 m box when trapped, mech / rig / ball / knocked-flat bodies, scaled up far away: x1 at 25 m to x1.8 at 85 m, x1.5 more in zombies). Tried cheapest first: each spot's box middles, then 9 points per box (middle, sides across the line of sight, top, bottom), then the 8 corners of the newest 2 spots |
| Revolver ricochets | no straight line: trace the shot back from the target along its last direction, mirroring off each wall (2 bounces). A bounce spot counts if the shooter can see it AND a shot from their eye to it reflects (off that wall's face) within 0.12 rad + the target's size seen from the spot (max 0.35) of the leg the client claims | a "bounce" off a floor spot you can see that no shot from you makes is refused |
| Weapon held | the hit's weapon is the one the snapshots say you hold, or the one you swapped away from < 400 ms ago. A hit with the gun you're swapping to (swap + click in one frame) waits up to 300 ms for the snapshot that says so, then runs the usual checks | dash hits: the scythe (or scythe rifle) in hand |
| Weapon in your loadout | Randomizer: exactly the rolled weapon for that slot (the server now keeps the roll, `p.roll`). Plain matches: one weapon per slot per life, from 6.5 s after the life's first snapshot (the client only switches loadouts in the first 5 s; the clock starts when the client is really playing, so a slow map load or a laggy join can't eat it). Gun game, infection, chaos kits, zombies, royale, Plant & Defuse, board game night, training, co-op and lobbies keep their own rules (`allowed`, `chaosHit`, `zmArm`, `brHandle`, `econHitOk`) | a new loadout handed out (every spawn, gun game rungs) clears the lock |
| Melee cone | target within the weapon's cone + 0.45 rad + its body width of any look in the last 300 ms of snapshots, or within 2.2 m any way (the client takes 1.5 m). Plus line of sight. Off while the spinbot runs (its snapshots spin) | knife 0.75 rad, katana 0.7, bread 0.8 ... |
| Cigarette / Leaf Blower | the same cone check (0.42 rad + slack) and line of sight; held and in the loadout | |
| Taser / TV Remote | the mode allows them (`allowed`, zombies' buys, chaos kits), held (same 400 ms grace), in the loadout. The aim, range and wall checks were already there (`secTarget`) | |
| Chicken Strike / Giant Duck | the aim point within 300 m (+8 m, + your speed x 0.3) of one of your eyes, with nothing in the way before the last 1.2 m (the point itself is on a wall / the floor). Refused = back in your tray | zombie drops (`zmDeploy`) are server-made: not checked |
| Clubs shockwave | not through walls: a clear line from your middle to their head, middle or feet | |
| Zombies | hits on zombies skip the wall check (co-op vs the horde: limbs, crawlers, Chonks); held / loadout / melee cone still apply | |
| CPU | before any ray: the hit has to pass onHit's own rate and range gates (looked at, not touched: a hit onHit would drop costs nothing). A refused hit still uses up its rate slot (`p.pair`), like a landed one, so a flood at one target is dropped for free. Per hit: at most 2500 rays and 10 ms. Per player per second: 7500 rays and 20 ms, then that second's hits are refused | honest hits (moving shooter and target, 40-300 ms ping, 5 maps x 600): median 1 ray, p99 1-26, max 85; 0.01-0.03 ms median. a full refusal: avg 3-7 ms, worst ~10-13 ms (Jankburg rays cost ~14 us, open maps ~2 us). 300 blocked hits from one connection in one second: 2-7 ms (was 42-227 ms before the gates). an honest minigun / akimbo / marble shotgun at full rate on a strafing target: 1 ray a hit, under 1 % of the budget |

## Left (queued, with why)

- **Ammo, magazine, reload and spread on hitscan**: the client counts its own bullets (except the revolver, Plant &
  Defuse and royale). A server count needs the client's reloads and per-gun fire modes mirrored; spread needs the S&D
  style shared random seed everywhere. Bigger job.
- **Lag rewind**: the server judges against the last ~650 ms of positions it saw, not an exact rewind to the shooter's
  frame. Good enough to stop wall hacks; exact rewind would need timestamps on hits.
- **Revolver ricochet direction**: the bounce has to add up from the shooter's eye now (within ~0.12-0.35 rad), but the
  aim itself isn't replayed. Exact would replay the client's bounce from its aim (like `tacHitOk` in Plant & Defuse),
  which needs the aim + spread seed.
- **Second Opinion quick-scope**: still the shooter's word (snapshots don't carry aiming down sights); it only buys
  +10 damage once per 1.2 s.
- **Status effects held by the victim's client**: snowball freeze, taser stun, nail-gun pin. A cheater can ignore them
  (the server pins the TV Remote's pause and the Speed Trap's jail). Pinning them means the server holding positions,
  like the remote does.
- **Grapple tug** (`push` with the hook): range and rate only, no line of sight. The hook is a projectile on the client;
  a server check needs its flight.
- **Mech Drop frames**: the server takes any of the 5 frames, the menu offers 2 (unclear if on purpose).
- **Client-only streak effects**: the scythe rifle's mag, dash fuel, the quiz speed boost, the popper's self-recoil,
  moon boots, spinbot and satellite.
- **Knockback through spawn protection** and **a void kill doesn't grow the katana**: current behaviour, a design call.
- **Snapshots themselves**: a client can still say it holds any gun in its snapshots and stand anywhere (movement is
  client-authoritative). The checks above bound what that buys: one gun per slot, only through clear lines.

## Verified (2026-11-13)

- `tests/honesty_ws.cjs`: 46/46 on this branch (the 46th: a ~550 ms-late hit on someone who ducked into cover still lands). Against origin/main (`JF_ROOT=<old checkout>`) all 20 "refused" checks
  fail and all 21 "lands" checks pass, so the lenient side lands the same shots as before.
- Bots never go through these checks (they fire in `botFire`), so a bots match doesn't test honesty itself: it only shows
  the pass changed nothing for bots (the Clubs wall check is the one rule they share). Bots-only matches, 8 bots, all on the AR
  (`JF_BOT_GUNS=ar`), Warehouse, 120 s each, 3 runs, origin/main vs this branch side by side:
  FFA kills 48 / 46 / 43 vs 42 / 50 / 53, TDM kills 42 / 38 / 34 vs 30 / 38 / 32 (totals 251 vs 245: noise).
- Older ws tests whose fixtures swung at people behind them, through a Jankburg wall, or fired a sniper after a life
  holding an AR were changed to act like a real client (`island_meter_ws`, `island_squads_ws`, `mech_trolley_ws`,
  `mech_wrecking_ws`).
