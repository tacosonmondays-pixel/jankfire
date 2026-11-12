# MECH DROP: how the mechs play

The owner's ask: a mech with the feel of the old mech-arena games (the Skylark / Arthur kind of frame): big, fast, readable,
far more detailed than anything else in the game. Two original frames: **PAPER PLANE** (nimble ~5 m flyer) and **NIGHT
SHIFT** (heavy ~6 m knight). The models and animation come from the mech model session (docs/mechs/MECHS.md); this page is
how they play. Every number below is a default the owner can change.

## Calling it in
- A new killstreak, **MECH DROP** (9 kills, between the Overdrive Rig at 8 and the top streaks). You pick your frame in the
  loadout next to the streak (PAPER PLANE or NIGHT SHIFT).
- Call it in and a red marker lands where your crosshair points (up to 60 m, on the floor under it). 2.5 s later the mech
  falls from the sky in a streak of smoke and lands with a **shockwave**: 60 damage at the middle, 6 m radius, big
  knockback up. Anyone standing on the marker gets squashed ("DROPPED A MECH ON THEM").
- It stands there, yours, with a glowing hatch. Walk up and press **F** to climb in (only you can; 30 s or it leaves).
  Bots call theirs in and climb in straight away.

## Inside
- **Third-person camera** behind the mech's shoulder, pulled back so you see the whole frame. Your crosshair still aims.
- **Armour bar** (the mech's own HP): PAPER PLANE 900, NIGHT SHIFT 1500. Your own HP is safe while you're inside; the
  mech takes every hit. Headshots on a mech hit the cockpit for 1.5x.
- **Energy meter** (100): the boost, hover and jet / dash moves spend it; it refills when you stop using it.
- Mechs can't grapple, use items or swap weapons: the mech's moves are your kit. Other killstreaks stay in your tray.
- Hitbox: one big box the size of the frame (it's easy to hit; it has a lot of armour).

### PAPER PLANE: the flyer (900 armour)
| key | move | what it does |
|---|---|---|
| LMB | **twin cannons** | fast, light shots (14 damage, 8 a second) |
| Space (hold) | **hover** | rises and hangs in the air while held; drains energy |
| Shift | **boost dash** | a fast burst the way you're moving; costs 25 energy; rams people it hits (30 + knockback) |
| RMB | **missile salvo** | 6 homing missiles at whatever is near the crosshair (rig missile code), 8 s cooldown |
| Q (big one) | **jet mode** | folds into a jet for 6 s: flies where you look at 45 m/s, can't shoot, rams for 60 and flings people; 20 s cooldown |

### NIGHT SHIFT: the knight (1500 armour)
| key | move | what it does |
|---|---|---|
| LMB | **sword combo** | three swings (40 / 40 / 70), a wide arc in front, big knockback on the third |
| RMB (hold) | **tower shield** | blocks 85% of hits from the front, walks slowly; release right after a hit to **shield bash** (30, shove) |
| Shift | **dash slash** | dashes 10 m and cuts everyone on the way (55); costs 35 energy |
| Q (big one) | **ground slam** | jumps up and smashes down: 120 at the middle, 8 m shockwave, everyone flung up; 18 s cooldown |

## Comedy
- **Stomp**: landing on someone (from a hover, a jump, a slam) squashes them: 50 + a flat "STOMPED" ragdoll.
- **Ram**: running into people at speed shoves them; faster = harder. Bots get bowled over.
- **Fling**: the slam, bash and jet ram send people flying with the game's usual knockback (into the void counts).
- Big callouts: "MECH DROP", "STOMPED", "EJECT! EJECT!".

## Ejecting
- At 0 armour the mech **ejects you**: you're flung up and back out of the cockpit, the mech flashes and blows up in a big
  jank pop (parts fly, 40 damage in 5 m, credited to whoever broke it, who gets a "MECH DOWN" kill-feed line).
- **F** inside hops you out early (no explosion). The empty mech stands there for 10 s, you can climb back in, then it
  leaves. Nobody else can use it.
- If you die some other way while inside (void, a train), the mech blows up too.

## Fairness (the server keeps it honest)
- Movement is client-side like the rig; the server checks speed caps per frame (hover / jet / dash), owns the armour,
  every hit, the drop marker (range + line of sight), the shockwave, stomps, rams and the explosion.
- Every new message is validated (types, finite numbers, ranges, cooldowns, energy, "are you in a mech") and rate limited.
- It reuses the Overdrive Rig's framework where it fits: the shield-takes-the-hit damage path, knockback shrug, missiles,
  landing shockwave, bot plan structure.

## Bots
- Bots that earn it call it in near the fight and climb in. In the mech: PAPER PLANE hovers at mid height, fires
  cannons, salvos when a target is in range and jets in to ram; NIGHT SHIFT walks at the nearest target, shields when it's
  being shot, dash-slashes to close the gap and slams when 2+ people are close.

## Build order
1. Code stand-ins in each frame's proportions (boxes and cylinders) so it plays now; the real models swap in when they land
   (file, bone and clip names from docs/mechs/MECHS.md).
2. Streak + drop + enter/exit + camera + armour/energy HUD.
3. The eight moves, stomps, rams, eject.
4. Bots. Tests: ws tests for every server rule, a bots walk/fight test, a Too HD clip.
