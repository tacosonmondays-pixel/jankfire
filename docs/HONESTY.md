# Server honesty

What the server checks before it believes a client's "I hit them", and what it still takes on trust. The checks live in
`server/honesty.js` (mixed into Room; it wraps `handle`, `onHit`, `onPush`, `onFire`, `sendLoadout`, `modeLoadout`,
`resetLife`). The test is `tests/honesty_ws.cjs` (every "refused" case in it lands on a server without this file).

Movement is the client's, so every check is lenient on purpose: it only refuses what no honest client at ~150 ms ping
could send. Bots and server-made shots never go through these checks (bots fire in `botFire`, not `onHit`). Story rooms
skip the hit checks (their referee judges hits on boss parts itself).

## Checked now

| What | Rule | Numbers |
| --- | --- | --- |
| Hitscan line of sight | a clear line (map boxes: walls, floors, glass; not deco or smoke, like the client's bullets) from the shooter's eye to any sample point on the target's hitboxes | eyes: 3 heights (1.6 / 1.3 / 0.98 m; a mech's cockpit + chase camera, the rig's, the ball's), at the newest position, one snapshot ahead (0.05 s at the speed the server saw), and the last 220 ms of positions. target: the newest position and the last 650 ms (every 100 ms; a shooter at ~540 ms ping still lands), hitboxes scaled up far away like the client draws them (x1 at 25 m to x1.8 at 85 m; x1.5 more in zombies), 9 points per box (middle, sides across the line of sight, top, bottom) |
| Revolver ricochets | no straight line: trace the shot back from the target along its last direction, mirroring off each wall (2 bounces); any wall spot the shooter can see counts | (a cheater can still bend a revolver shot off a wall they can see: see "left") |
| Weapon held | the hit's weapon is the one the snapshots say you hold, or the one you swapped away from < 400 ms ago. A hit with the gun you're swapping to (swap + click in one frame) waits up to 300 ms for the snapshot that says so, then runs the usual checks | dash hits: the scythe (or scythe rifle) in hand |
| Weapon in your loadout | Randomizer: exactly the rolled weapon for that slot (the server now keeps the roll, `p.roll`). Plain matches: one weapon per slot per life, from 6.5 s into the life (the client only switches loadouts in the first 5 s). Gun game, infection, chaos kits, zombies, royale, Plant & Defuse, board game night, training, co-op and lobbies keep their own rules (`allowed`, `chaosHit`, `zmArm`, `brHandle`, `econHitOk`) | a new loadout handed out (every spawn, gun game rungs) clears the lock |
| Melee cone | target within the weapon's cone + 0.45 rad + its body width of any look in the last 300 ms of snapshots, or within 2.2 m any way (the client takes 1.5 m). Plus line of sight. Off while the spinbot runs (its snapshots spin) | knife 0.75 rad, katana 0.7, bread 0.8 ... |
| Cigarette / Leaf Blower | the same cone check (0.42 rad + slack) and line of sight; held and in the loadout | |
| Taser / TV Remote | the mode allows them (`allowed`, zombies' buys, chaos kits), held (same 400 ms grace), in the loadout. The aim, range and wall checks were already there (`secTarget`) | |
| Chicken Strike / Giant Duck | the aim point within 300 m (+8 m, + your speed x 0.3) of one of your eyes, with nothing in the way before the last 1.2 m (the point itself is on a wall / the floor). Refused = back in your tray | zombie drops (`zmDeploy`) are server-made: not checked |
| Clubs shockwave | not through walls: a clear line from your middle to their head, middle or feet | |
| CPU | a full check that says "no" costs up to ~1000 rays (~5 us each). After 8 of those in a second, a player only gets the newest-positions version until it calms down | |

## Left (queued, with why)

- **Ammo, magazine, reload and spread on hitscan**: the client counts its own bullets (except the revolver, Plant &
  Defuse and royale). A server count needs the client's reloads and per-gun fire modes mirrored; spread needs the S&D
  style shared random seed everywhere. Bigger job.
- **Lag rewind**: the server judges against the last ~650 ms of positions it saw, not an exact rewind to the shooter's
  frame. Good enough to stop wall hacks; exact rewind would need timestamps on hits.
- **Revolver ricochet direction**: a cheater can claim a bounce off any wall they can see. A tighter check would replay
  the client's bounce from its aim (like `tacHitOk` does in Plant & Defuse), which needs the aim + spread seed.
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

- `tests/honesty_ws.cjs`: 45/45 on this branch. Against origin/main (`JF_ROOT=<old checkout>`) all 20 "refused" checks
  fail and all 21 "lands" checks pass, so the lenient side lands the same shots as before.
- Bots never go through these checks (they fire in `botFire`). Bots-only matches, 8 bots, all on the AR
  (`JF_BOT_GUNS=ar`), Warehouse, 120 s each, 3 runs, origin/main vs this branch side by side:
  FFA kills 48 / 46 / 43 vs 42 / 50 / 53, TDM kills 42 / 38 / 34 vs 30 / 38 / 32 (totals 251 vs 245: noise).
- Older ws tests whose fixtures swung at people behind them, through a Jankburg wall, or fired a sniper after a life
  holding an AR were changed to act like a real client (`island_meter_ws`, `island_squads_ws`, `mech_trolley_ws`,
  `mech_wrecking_ws`).
